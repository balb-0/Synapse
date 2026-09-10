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
    "minio_endpoint": "ETL_MINIO_ENDPOINT",
    "minio_bucket": "ETL_MINIO_BUCKET",
    "minio_input_prefix": "ETL_MINIO_INPUT_PREFIX",
    "minio_access_key": "ETL_MINIO_ACCESS_KEY",
    "minio_secret_key": "ETL_MINIO_SECRET_KEY",
    "request_timeout_seconds": "ETL_REQUEST_TIMEOUT_SECONDS",
    "batch_size": "ETL_EXTRACTION_BATCH_SIZE",
    "max_attempts": "ETL_EXTRACTION_MAX_ATTEMPTS",
    "retry_initial_delay_seconds": "ETL_EXTRACTION_RETRY_INITIAL_DELAY_SECONDS",
    "retry_max_delay_seconds": "ETL_EXTRACTION_RETRY_MAX_DELAY_SECONDS",
}

DEFAULT_VALUES: dict[str, str] = {
    "minio_input_prefix": "landing",
    "request_timeout_seconds": "30",
    "batch_size": "1000",
    "max_attempts": "3",
    "retry_initial_delay_seconds": "0.5",
    "retry_max_delay_seconds": "5",
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


def _validate_source_dir(value: ParameterValue) -> Path | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
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


def _validate_object_prefix(value: str) -> str:
    normalized = value.strip().strip("/")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise ConfigurationError(
            "ETL_MINIO_INPUT_PREFIX deve ser um prefixo relativo sem '..'"
        )
    return normalized


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


def _validate_batch_size(value: ParameterValue) -> int:
    if isinstance(value, bool):
        raise ConfigurationError("ETL_EXTRACTION_BATCH_SIZE deve ser inteiro positivo")
    if isinstance(value, int):
        batch_size = value
    elif isinstance(value, str) and re.fullmatch(r"[1-9][0-9]*", value.strip()):
        batch_size = int(value)
    else:
        raise ConfigurationError("ETL_EXTRACTION_BATCH_SIZE deve ser inteiro positivo")

    if batch_size <= 0:
        raise ConfigurationError("ETL_EXTRACTION_BATCH_SIZE deve ser inteiro positivo")
    return batch_size


def _validate_max_attempts(value: ParameterValue) -> int:
    if isinstance(value, bool):
        raise ConfigurationError(
            "ETL_EXTRACTION_MAX_ATTEMPTS deve ser inteiro positivo"
        )
    if isinstance(value, int):
        max_attempts = value
    elif isinstance(value, str) and re.fullmatch(r"[1-9][0-9]*", value.strip()):
        max_attempts = int(value)
    else:
        raise ConfigurationError(
            "ETL_EXTRACTION_MAX_ATTEMPTS deve ser inteiro positivo"
        )

    if max_attempts <= 0:
        raise ConfigurationError(
            "ETL_EXTRACTION_MAX_ATTEMPTS deve ser inteiro positivo"
        )
    return max_attempts


def _validate_retry_delay(value: ParameterValue, variable: str) -> float:
    if isinstance(value, (bool, Path, SecretValue)) or value is None:
        raise ConfigurationError(f"{variable} deve ser numérico e não negativo")
    try:
        delay = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            f"{variable} deve ser numérico e não negativo"
        ) from exc
    if not math.isfinite(delay) or delay < 0:
        raise ConfigurationError(f"{variable} deve ser numérico e não negativo")
    return delay


@dataclass(frozen=True, slots=True)
class ExtractionSettings:
    """Configurações validadas para leitura de objetos no MinIO."""

    minio_endpoint: str
    minio_bucket: str
    minio_access_key: SecretValue = field(repr=False)
    minio_secret_key: SecretValue = field(repr=False)
    minio_input_prefix: str = "landing"
    request_timeout_seconds: float = 30.0
    batch_size: int = 1000
    max_attempts: int = 3
    retry_initial_delay_seconds: float = 0.5
    retry_max_delay_seconds: float = 5.0
    source_dir: Path | None = None

    def safe_summary(self) -> dict[str, str | int | float | None]:
        """Retorna dados apropriados para diagnóstico e logs."""

        return {
            "minio_endpoint": self.minio_endpoint,
            "minio_bucket": self.minio_bucket,
            "minio_input_prefix": self.minio_input_prefix,
            "minio_access_key": REDACTED,
            "minio_secret_key": REDACTED,
            "request_timeout_seconds": self.request_timeout_seconds,
            "batch_size": self.batch_size,
            "max_attempts": self.max_attempts,
            "retry_initial_delay_seconds": self.retry_initial_delay_seconds,
            "retry_max_delay_seconds": self.retry_max_delay_seconds,
            "source_dir": str(self.source_dir) if self.source_dir else None,
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

    source_dir = _configured_value(
        "source_dir", supplied_parameters, supplied_environment
    )
    minio_endpoint = _required_value(
        "minio_endpoint", supplied_parameters, supplied_environment
    )
    minio_bucket = _required_value(
        "minio_bucket", supplied_parameters, supplied_environment
    )
    minio_input_prefix = _required_value(
        "minio_input_prefix", supplied_parameters, supplied_environment
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
    batch_size = _required_value(
        "batch_size", supplied_parameters, supplied_environment
    )
    max_attempts = _required_value(
        "max_attempts", supplied_parameters, supplied_environment
    )
    retry_initial_delay = _required_value(
        "retry_initial_delay_seconds", supplied_parameters, supplied_environment
    )
    retry_max_delay = _required_value(
        "retry_max_delay_seconds", supplied_parameters, supplied_environment
    )

    validated_retry_initial_delay = _validate_retry_delay(
        retry_initial_delay,
        "ETL_EXTRACTION_RETRY_INITIAL_DELAY_SECONDS",
    )
    validated_retry_max_delay = _validate_retry_delay(
        retry_max_delay,
        "ETL_EXTRACTION_RETRY_MAX_DELAY_SECONDS",
    )
    if validated_retry_max_delay < validated_retry_initial_delay:
        raise ConfigurationError(
            "ETL_EXTRACTION_RETRY_MAX_DELAY_SECONDS deve ser maior ou igual "
            "a ETL_EXTRACTION_RETRY_INITIAL_DELAY_SECONDS"
        )

    return ExtractionSettings(
        minio_endpoint=_validate_endpoint(
            str(minio_endpoint), "ETL_MINIO_ENDPOINT"
        ),
        minio_bucket=_validate_bucket(str(minio_bucket)),
        minio_access_key=_secret(minio_access_key, "minio_access_key"),
        minio_secret_key=_secret(minio_secret_key, "minio_secret_key"),
        minio_input_prefix=_validate_object_prefix(str(minio_input_prefix)),
        request_timeout_seconds=_validate_timeout(timeout),
        batch_size=_validate_batch_size(batch_size),
        max_attempts=_validate_max_attempts(max_attempts),
        retry_initial_delay_seconds=validated_retry_initial_delay,
        retry_max_delay_seconds=validated_retry_max_delay,
        source_dir=_validate_source_dir(source_dir),
    )
