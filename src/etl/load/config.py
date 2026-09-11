"""Configuração do banco de ingestão local em DuckDB."""

from __future__ import annotations

import math
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

ENVIRONMENT_VARIABLES = {
    "database_path": "ETL_DUCKDB_PATH",
    "threads": "ETL_DUCKDB_THREADS",
    "memory_limit": "ETL_DUCKDB_MEMORY_LIMIT",
    "write_lock_timeout_seconds": "ETL_DUCKDB_WRITE_LOCK_TIMEOUT_SECONDS",
}

DEFAULT_DATABASE_PATH = "data/duckdb/ingestao.duckdb"

# threads e memory_limit ficam sem padrão: ausente significa não tocar no que
# o DuckDB já usa por conta própria, não impor um valor arbitrário.
DEFAULT_WRITE_LOCK_TIMEOUT_SECONDS = 300.0

DEFAULT_VALUES: dict[str, str] = {
    "database_path": DEFAULT_DATABASE_PATH,
    "write_lock_timeout_seconds": str(DEFAULT_WRITE_LOCK_TIMEOUT_SECONDS),
}

IN_MEMORY_ALIASES = frozenset({":memory:", "memory"})

# As mensagens nomeiam a configuração, não a variável: o mesmo valor pode
# chegar por ETL_DUCKDB_PATH ou pelo parâmetro do comando de carga.
PATH_MUST_BE_A_FILE = "o caminho do banco de ingestão deve apontar para um arquivo"


class ConfigurationError(ValueError):
    """Indica configuração ausente ou inválida do banco de ingestão."""


ParameterValue: TypeAlias = str | Path | None


@dataclass(frozen=True, slots=True)
class DuckDBSettings:
    """Configurações validadas do arquivo local usado na carga.

    O DuckDB é embutido no processo: não há host, porta nem credencial a
    configurar. O que identifica o ambiente é o caminho do arquivo.
    """

    database_path: Path
    threads: int | None = None
    memory_limit: str | None = None
    write_lock_timeout_seconds: float = DEFAULT_WRITE_LOCK_TIMEOUT_SECONDS


def _validate_database_path(value: ParameterValue) -> Path:
    if isinstance(value, bool) or not isinstance(value, (str, Path)):
        raise ConfigurationError(PATH_MUST_BE_A_FILE)

    text = str(value).strip()
    if not text:
        raise ConfigurationError(PATH_MUST_BE_A_FILE)
    if text.lower() in IN_MEMORY_ALIASES:
        raise ConfigurationError(
            "o caminho do banco de ingestão exige um arquivo persistente; "
            "um banco em memória não sobrevive ao fim da execução"
        )

    path = Path(text).expanduser()
    if text.endswith(("/", os.sep)) or path.is_dir():
        raise ConfigurationError(
            "o caminho do banco de ingestão deve apontar para um arquivo, não para um diretório"
        )
    if ".." in path.parts:
        raise ConfigurationError("o caminho do banco de ingestão não pode conter '..'")
    return Path(os.path.abspath(path))


def _validate_threads(value: ParameterValue) -> int | None:
    """Ausente é válido: significa deixar o DuckDB decidir sozinho."""

    if value is None:
        return None
    if isinstance(value, bool):
        raise ConfigurationError("o número de threads do DuckDB deve ser inteiro positivo")
    if isinstance(value, int):
        threads = value
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if not re.fullmatch(r"[1-9][0-9]*", text):
            raise ConfigurationError("o número de threads do DuckDB deve ser inteiro positivo")
        threads = int(text)
    else:
        raise ConfigurationError("o número de threads do DuckDB deve ser inteiro positivo")
    if threads <= 0:
        raise ConfigurationError("o número de threads do DuckDB deve ser inteiro positivo")
    return threads


def _validate_memory_limit(value: ParameterValue) -> str | None:
    """A gramática do valor (`'2GB'`, `'80%'`, ...) é validada pelo próprio DuckDB.

    Reimplementar essa gramática aqui duplicaria uma checagem que o `SET
    memory_limit=?` já faz com um erro claro; aqui só garante que o valor
    configurado é texto não vazio antes de chegar à conexão.
    """

    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, str):
        raise ConfigurationError("o limite de memória do DuckDB deve ser texto")
    text = value.strip()
    return text or None


def _validate_write_lock_timeout(value: ParameterValue) -> float:
    """Maior que zero: um timeout nulo ou negativo tornaria a espera pelo lock inútil."""

    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ConfigurationError(
            "o timeout do lock de escrita do DuckDB deve ser numérico e maior que zero"
        )
    try:
        timeout = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            "o timeout do lock de escrita do DuckDB deve ser numérico e maior que zero"
        ) from exc
    if not math.isfinite(timeout) or timeout <= 0:
        raise ConfigurationError(
            "o timeout do lock de escrita do DuckDB deve ser numérico e maior que zero"
        )
    return timeout


def _configured_value(
    field_name: str,
    parameters: Mapping[str, ParameterValue],
    environ: Mapping[str, str],
) -> ParameterValue:
    explicit = parameters.get(field_name)
    if explicit is not None:
        return explicit

    # Variável presente e em branco vale como não configurada: o .env do time
    # lista todas as chaves, inclusive as que ficam com o padrão.
    environment_value = environ.get(ENVIRONMENT_VARIABLES[field_name])
    if environment_value is not None and environment_value.strip():
        return environment_value

    return DEFAULT_VALUES.get(field_name)


def load_duckdb_settings(
    parameters: Mapping[str, ParameterValue] | None = None,
    environ: Mapping[str, str] | None = None,
) -> DuckDBSettings:
    """Carrega parâmetros explícitos antes das variáveis de ambiente.

    Os nomes aceitos em ``parameters`` são os campos de :class:`DuckDBSettings`.
    Caminhos relativos são resolvidos a partir do diretório de execução, por
    isso os comandos documentados partem da raiz do repositório.
    """

    supplied_parameters = dict(parameters or {})
    unknown = sorted(set(supplied_parameters) - set(ENVIRONMENT_VARIABLES))
    if unknown:
        raise ConfigurationError("parâmetros de configuração desconhecidos: " + ", ".join(unknown))
    supplied_environment = os.environ if environ is None else environ

    return DuckDBSettings(
        database_path=_validate_database_path(
            _configured_value("database_path", supplied_parameters, supplied_environment)
        ),
        threads=_validate_threads(
            _configured_value("threads", supplied_parameters, supplied_environment)
        ),
        memory_limit=_validate_memory_limit(
            _configured_value("memory_limit", supplied_parameters, supplied_environment)
        ),
        write_lock_timeout_seconds=_validate_write_lock_timeout(
            _configured_value(
                "write_lock_timeout_seconds", supplied_parameters, supplied_environment
            )
        ),
    )
