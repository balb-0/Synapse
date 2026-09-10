"""Configuração do banco de ingestão local em DuckDB."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias


ENVIRONMENT_VARIABLES = {
    "database_path": "ETL_DUCKDB_PATH",
}

DEFAULT_DATABASE_PATH = "data/duckdb/ingestao.duckdb"

DEFAULT_VALUES: dict[str, str] = {
    "database_path": DEFAULT_DATABASE_PATH,
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
            "o caminho do banco de ingestão deve apontar para um arquivo, "
            "não para um diretório"
        )
    if ".." in path.parts:
        raise ConfigurationError(
            "o caminho do banco de ingestão não pode conter '..'"
        )
    return Path(os.path.abspath(path))


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
        raise ConfigurationError(
            "parâmetros de configuração desconhecidos: " + ", ".join(unknown)
        )
    supplied_environment = os.environ if environ is None else environ

    return DuckDBSettings(
        database_path=_validate_database_path(
            _configured_value("database_path", supplied_parameters, supplied_environment)
        )
    )
