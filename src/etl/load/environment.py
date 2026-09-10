"""Criação e verificação do arquivo local do DuckDB usado na ingestão."""

from __future__ import annotations

import uuid
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

from .config import DuckDBSettings


HEALTH_CHECK_SCHEMA = "health_check"
HEALTH_CHECK_TABLE = f"{HEALTH_CHECK_SCHEMA}.smoke_test"
SMOKE_QUERY_VALUE = 42
LEFTOVER_NOTICE = (
    f"a tabela {HEALTH_CHECK_TABLE} permaneceu no arquivo; "
    "a próxima execução a remove"
)


class DatabaseEnvironmentError(RuntimeError):
    """Falha ao criar ou verificar o arquivo local do banco de ingestão."""


@dataclass(frozen=True, slots=True)
class HealthCheck:
    """Resultado de uma verificação isolada do ambiente."""

    name: str
    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class HealthCheckReport:
    """Relatório completo de uma execução do health check."""

    database_path: Path
    duckdb_version: str
    database_created: bool
    checks: tuple[HealthCheck, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)


def _first_line(error: Exception) -> str:
    message = str(error).strip()
    return message.splitlines()[0] if message else type(error).__name__


@contextmanager
def open_connection(settings: DuckDBSettings) -> Iterator[duckdb.DuckDBPyConnection]:
    """Abre e fecha uma conexão com o arquivo configurado.

    O arquivo aceita um único escritor por vez, porque o controle de acesso
    fica no processo e não em um servidor. Uma tentativa de abrir o arquivo já
    bloqueado falha com :class:`DatabaseEnvironmentError` informando o motivo
    devolvido pelo DuckDB.
    """

    try:
        connection = duckdb.connect(str(settings.database_path))
    except duckdb.Error as error:
        raise DatabaseEnvironmentError(
            f"não foi possível abrir {settings.database_path}: {_first_line(error)}"
        ) from error

    try:
        yield connection
    finally:
        connection.close()


def _execute(
    connection: duckdb.DuckDBPyConnection,
    statement: str,
    parameters: Sequence[Any] = (),
) -> duckdb.DuckDBPyConnection:
    try:
        return connection.execute(statement, list(parameters))
    except duckdb.Error as error:
        raise DatabaseEnvironmentError(
            f"comando recusado pelo banco de ingestão: {_first_line(error)}"
        ) from error


def _scalar(
    connection: duckdb.DuckDBPyConnection,
    statement: str,
    parameters: Sequence[Any] = (),
) -> Any:
    row = _execute(connection, statement, parameters).fetchone()
    if row is None:
        raise DatabaseEnvironmentError(
            "o banco de ingestão não devolveu resultado para uma consulta obrigatória"
        )
    return row[0]


def prepare_database(settings: DuckDBSettings) -> bool:
    """Garante o diretório e o arquivo do banco e informa se acabou de criá-lo.

    A operação é idempotente: repetir o comando não recria o arquivo nem apaga
    o conteúdo já carregado.
    """

    path = settings.database_path
    already_existed = path.exists()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise DatabaseEnvironmentError(
            f"não foi possível criar {path.parent}: {error.strerror}"
        ) from error

    if not already_existed:
        # Conectar cria o arquivo em disco; o DuckDB não tem processo a subir.
        with open_connection(settings) as connection:
            _execute(connection, "SELECT 1")
    return not already_existed


def _file_check(path: Path) -> HealthCheck:
    if not path.is_file():
        return HealthCheck("arquivo_local", False, f"{path} não existe depois da criação")
    return HealthCheck("arquivo_local", True, f"{path} com {path.stat().st_size} bytes")


def _smoke_query_check(connection: duckdb.DuckDBPyConnection) -> HealthCheck:
    value = _scalar(connection, f"SELECT {SMOKE_QUERY_VALUE}")
    if value == SMOKE_QUERY_VALUE:
        return HealthCheck("consulta_smoke", True, f"consulta devolveu {value}")
    return HealthCheck(
        "consulta_smoke",
        False,
        f"consulta devolveu {value!r}; esperado {SMOKE_QUERY_VALUE}",
    )


def _write_marker(connection: duckdb.DuckDBPyConnection, marker: str) -> None:
    _execute(connection, f"CREATE SCHEMA IF NOT EXISTS {HEALTH_CHECK_SCHEMA}")
    _execute(
        connection,
        f"CREATE OR REPLACE TABLE {HEALTH_CHECK_TABLE} "
        "(marcador VARCHAR, verificado_em TIMESTAMPTZ)",
    )
    _execute(connection, f"INSERT INTO {HEALTH_CHECK_TABLE} VALUES (?, now())", [marker])


def _persistence_check(connection: duckdb.DuckDBPyConnection, marker: str) -> HealthCheck:
    found = _scalar(
        connection,
        f"SELECT count(*) FROM {HEALTH_CHECK_TABLE} WHERE marcador = ?",
        [marker],
    )
    if found == 1:
        return HealthCheck(
            "escrita_persistida",
            True,
            "linha gravada em uma conexão e relida depois de reabrir o arquivo",
        )
    return HealthCheck(
        "escrita_persistida",
        False,
        f"{found} linha(s) encontradas para o marcador desta execução; esperado 1",
    )


def _drop_marker(connection: duckdb.DuckDBPyConnection) -> None:
    _execute(connection, f"DROP TABLE IF EXISTS {HEALTH_CHECK_TABLE}")
    _execute(connection, f"DROP SCHEMA IF EXISTS {HEALTH_CHECK_SCHEMA}")


def _discard_marker(settings: DuckDBSettings) -> bool:
    """Tenta remover a tabela do marcador e informa se conseguiu.

    A limpeza precisa abrir o arquivo outra vez, e é justamente o lock de
    escritor único que tende a falhar aqui. Um resíduo não impede a execução
    seguinte: ela recria a tabela do marcador antes de usá-la.
    """

    try:
        with open_connection(settings) as connection:
            _drop_marker(connection)
    except DatabaseEnvironmentError:
        return False
    return True


def run_health_check(settings: DuckDBSettings) -> HealthCheckReport:
    """Cria o ambiente, se necessário, e verifica consulta e persistência.

    A verificação de persistência grava uma linha, fecha a conexão, reabre o
    arquivo e relê a linha antes de remover a tabela usada. As tabelas de
    ingestão são definidas pelas DDLs versionadas da carga, não por esta
    verificação: uma execução concluída não deixa objeto no banco. Uma
    execução interrompida tenta remover o marcador e, quando nem isso é
    possível, informa o resíduo no erro.
    """

    created = prepare_database(settings)
    marker = f"health-check-{uuid.uuid4()}"
    marker_pending = False

    try:
        with open_connection(settings) as connection:
            version = str(_scalar(connection, "SELECT version()"))
            smoke_query = _smoke_query_check(connection)
            _write_marker(connection, marker)
            marker_pending = True

        with open_connection(settings) as connection:
            persistence = _persistence_check(connection, marker)
            _drop_marker(connection)
            marker_pending = False
    except BaseException as error:
        # Inclui Ctrl+C e falha de lock: o marcador não fica para trás calado.
        leftover = marker_pending and not _discard_marker(settings)
        if leftover and isinstance(error, DatabaseEnvironmentError):
            raise DatabaseEnvironmentError(f"{error}; {LEFTOVER_NOTICE}") from error
        raise

    return HealthCheckReport(
        database_path=settings.database_path,
        duckdb_version=version,
        database_created=created,
        checks=(
            _file_check(settings.database_path),
            smoke_query,
            persistence,
        ),
    )
