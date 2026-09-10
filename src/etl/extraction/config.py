"""Configuração segura da etapa de extração."""

from __future__ import annotations

import math
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import TypeAlias
from urllib.parse import urlsplit


REDACTED = "********"

ENVIRONMENT_VARIABLES = {
    "source_dir": "ETL_SOURCE_DIR",
    "nifi_api_url": "ETL_NIFI_API_URL",
    "nifi_input_dir": "ETL_NIFI_INPUT_DIR",
    "minio_endpoint": "ETL_MINIO_ENDPOINT",
    "minio_bucket": "ETL_MINIO_BUCKET",
    "minio_access_key": "ETL_MINIO_ACCESS_KEY",
    "minio_secret_key": "ETL_MINIO_SECRET_KEY",
    "request_timeout_seconds": "ETL_REQUEST_TIMEOUT_SECONDS",
}

DEFAULT_VALUES: dict[str, str] = {
    "nifi_input_dir": "/opt/nifi/input",
    "request_timeout_seconds": "30",
}


class ConfigurationError(ValueError):
    """Indica configuração ausente ou inválida sem revelar seu conteúdo."""


@dataclass(frozen=True, slots=True, repr=False)
class SecretValue:
    """Mantém uma credencial oculta em ``str`` e ``repr``."""

    _value: str = field(repr=False)

    def __post_init__(self) -> None:
        if not self._value or not self._value.strip():
            raise ConfigurationError("credencial obrigatória ausente")

    def get_secret_value(self) -> str:
        """Retorna a credencial somente para o adaptador que fará a conexão."""

        return self._value

    def __str__(self) -> str:
        return REDACTED

    def __repr__(self) -> str:
        return f"SecretValue('{REDACTED}')"


ParameterValue: TypeAlias = str | int | float | Path | SecretValue | None


def _validate_endpoint(value: str, field_name: str) -> str:
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
    except ValueError:
        raise ConfigurationError(f"endpoint inválido em {field_name}") from None

    if parsed.scheme not in {"http", "https"} or not hostname:
        raise ConfigurationError(f"endpoint inválido em {field_name}")
    if parsed.username is not None or parsed.password is not None:
        raise ConfigurationError(
            f"{field_name} não pode conter credenciais; use as variáveis específicas"
        )
    if parsed.query or parsed.fragment:
        raise ConfigurationError(f"{field_name} não pode conter query ou fragmento")
    return value.rstrip("/")


def _validate_source_dir(value: ParameterValue) -> Path:
    if not isinstance(value, (str, Path)):
        raise ConfigurationError(
            "ETL_SOURCE_DIR deve apontar para um caminho válido"
        )

    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise ConfigurationError("diretório configurado em ETL_SOURCE_DIR não existe")
    if not path.is_dir():
        raise ConfigurationError("ETL_SOURCE_DIR deve apontar para um diretório")
    return path


def _validate_nifi_input_dir(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if not path.is_absolute() or ".." in path.parts:
        raise ConfigurationError(
            "ETL_NIFI_INPUT_DIR deve ser um caminho absoluto sem '..'"
        )
    return path


def _validate_bucket(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", value):
        raise ConfigurationError("ETL_MINIO_BUCKET possui nome inválido")
    return value


def _validate_timeout(value: ParameterValue) -> float:
    if isinstance(value, (bool, Path, SecretValue)) or value is None:
        raise ConfigurationError(
            "ETL_REQUEST_TIMEOUT_SECONDS deve ser numérico"
        )

    try:
        timeout = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            "ETL_REQUEST_TIMEOUT_SECONDS deve ser numérico"
        ) from exc
    if not math.isfinite(timeout) or timeout <= 0:
        raise ConfigurationError(
            "ETL_REQUEST_TIMEOUT_SECONDS deve ser maior que zero"
        )
    return timeout


@dataclass(frozen=True, slots=True)
class ExtractionSettings:
    """Configurações validadas para NiFi, entrada local e MinIO."""

    source_dir: Path
    nifi_api_url: str
    nifi_input_dir: PurePosixPath
    minio_endpoint: str
    minio_bucket: str
    minio_access_key: SecretValue = field(repr=False)
    minio_secret_key: SecretValue = field(repr=False)
    request_timeout_seconds: float = 30.0

    def safe_summary(self) -> dict[str, str | float]:
        """Retorna dados apropriados para diagnóstico e logs."""

        return {
            "source_dir": str(self.source_dir),
            "nifi_api_url": self.nifi_api_url,
            "nifi_input_dir": str(self.nifi_input_dir),
            "minio_endpoint": self.minio_endpoint,
            "minio_bucket": self.minio_bucket,
            "minio_access_key": REDACTED,
            "minio_secret_key": REDACTED,
            "request_timeout_seconds": self.request_timeout_seconds,
        }


def _configured_value(
    field_name: str,
    parameters: Mapping[str, ParameterValue],
    environ: Mapping[str, str],
) -> ParameterValue:
    explicit = parameters.get(field_name)
    if explicit is not None:
        return explicit

    environment_value = environ.get(ENVIRONMENT_VARIABLES[field_name])
    if environment_value is not None:
        return environment_value

    return DEFAULT_VALUES.get(field_name)


def _required_value(
    field_name: str,
    parameters: Mapping[str, ParameterValue],
    environ: Mapping[str, str],
) -> ParameterValue:
    value = _configured_value(field_name, parameters, environ)
    if value is None or (isinstance(value, str) and not value.strip()):
        variable = ENVIRONMENT_VARIABLES[field_name]
        raise ConfigurationError(
            f"configuração obrigatória ausente: {field_name} ({variable})"
        )
    return value


def _secret(value: ParameterValue, field_name: str) -> SecretValue:
    if isinstance(value, SecretValue):
        return value
    if not isinstance(value, str) or not value.strip():
        variable = ENVIRONMENT_VARIABLES[field_name]
        raise ConfigurationError(
            f"credencial obrigatória ausente: {field_name} ({variable})"
        )
    return SecretValue(value)


def load_extraction_settings(
    parameters: Mapping[str, ParameterValue] | None = None,
    environ: Mapping[str, str] | None = None,
) -> ExtractionSettings:
    """Carrega parâmetros explícitos antes das variáveis de ambiente.

    Os nomes aceitos em ``parameters`` são os campos de
    :class:`ExtractionSettings`. Credenciais nunca são incluídas em mensagens
    de erro ou no resumo seguro retornado pela configuração.
    """

    supplied_parameters = dict(parameters or {})
    unknown = sorted(set(supplied_parameters) - set(ENVIRONMENT_VARIABLES))
    if unknown:
        raise ConfigurationError(
            "parâmetros de configuração desconhecidos: " + ", ".join(unknown)
        )
    supplied_environment = os.environ if environ is None else environ

    source_dir = _required_value(
        "source_dir", supplied_parameters, supplied_environment
    )
    nifi_api_url = _required_value(
        "nifi_api_url", supplied_parameters, supplied_environment
    )
    nifi_input_dir = _required_value(
        "nifi_input_dir", supplied_parameters, supplied_environment
    )
    minio_endpoint = _required_value(
        "minio_endpoint", supplied_parameters, supplied_environment
    )
    minio_bucket = _required_value(
        "minio_bucket", supplied_parameters, supplied_environment
    )
    minio_access_key = _required_value(
        "minio_access_key", supplied_parameters, supplied_environment
    )
    minio_secret_key = _required_value(
        "minio_secret_key", supplied_parameters, supplied_environment
    )
    timeout = _required_value(
        "request_timeout_seconds", supplied_parameters, supplied_environment
    )

    return ExtractionSettings(
        source_dir=_validate_source_dir(source_dir),
        nifi_api_url=_validate_endpoint(str(nifi_api_url), "ETL_NIFI_API_URL"),
        nifi_input_dir=_validate_nifi_input_dir(str(nifi_input_dir)),
        minio_endpoint=_validate_endpoint(
            str(minio_endpoint), "ETL_MINIO_ENDPOINT"
        ),
        minio_bucket=_validate_bucket(str(minio_bucket)),
        minio_access_key=_secret(minio_access_key, "minio_access_key"),
        minio_secret_key=_secret(minio_secret_key, "minio_secret_key"),
        request_timeout_seconds=_validate_timeout(timeout),
    )
