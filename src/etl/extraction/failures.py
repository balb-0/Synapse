"""Classificação segura das falhas encontradas nas fontes."""

from __future__ import annotations

import errno
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

RETRY_EVENT = "extraction.retry.emitted"
RETRY_STAGE = "extraction"


class FailureNature(str, Enum):
    """Define se uma operação pode ser repetida automaticamente."""

    TRANSIENT = "transient"
    PERMANENT = "permanent"


class FailureCategory(str, Enum):
    """Categorias estáveis e sem conteúdo sensível para falhas das fontes."""

    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"
    AUTHENTICATION = "authentication"
    NOT_FOUND = "not_found"
    MALFORMED = "malformed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class FailureClassification:
    """Resultado da classificação de uma exceção da fonte."""

    category: FailureCategory
    nature: FailureNature

    @property
    def retryable(self) -> bool:
        return self.nature is FailureNature.TRANSIENT


@dataclass(frozen=True, slots=True)
class SourceFailure:
    """Registro técnico de uma tentativa, sem mensagem ou payload da fonte."""

    source: str
    operation: str
    category: FailureCategory
    nature: FailureNature
    attempt: int
    max_attempts: int
    exception_type: str
    retry_scheduled: bool
    next_delay_seconds: float
    duration_ms: float

    @property
    def retryable(self) -> bool:
        return self.nature is FailureNature.TRANSIENT

    def as_dict(self) -> dict[str, str | int | float | bool]:
        """Expõe somente atributos apropriados para logs e métricas."""

        return {
            "source": self.source,
            "operation": self.operation,
            "category": self.category.value,
            "nature": self.nature.value,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "exception_type": self.exception_type,
            "retryable": self.retryable,
            "retry_scheduled": self.retry_scheduled,
            "next_delay_seconds": self.next_delay_seconds,
            "duration_ms": self.duration_ms,
        }


@runtime_checkable
class FailureRecorder(Protocol):
    """Recebe falhas classificadas sem conhecer os dados extraídos."""

    def record(self, failure: SourceFailure) -> None:
        """Registra uma tentativa para observabilidade posterior."""

        ...


class StandardFailureRecorder:
    """Publica cada tentativa retried como evento estruturado (OB-06, ADR 0001).

    Antes do OB-06, o padrão era ``RetryExecutor`` descartar toda tentativa
    (``_NullFailureRecorder``) quando nenhum recorder era injetado — cada
    repetição era classificada e depois jogada fora. Este é o recorder
    padrão agora: mesmo formato técnico (evento como mensagem, atributos em
    ``extra``) das outras etapas, com rótulos limitados por construção
    (``SourceFailure.as_dict()`` já não carrega mensagem de exceção).
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("etl.extraction")

    def record(self, failure: SourceFailure) -> None:
        attributes = failure.as_dict()
        attributes["event"] = RETRY_EVENT
        attributes["stage"] = RETRY_STAGE
        self._logger.info(RETRY_EVENT, extra=attributes)


class SourceAccessError(RuntimeError):
    """Falha sanitizada de acesso a uma fonte."""

    def __init__(self, failure: SourceFailure, message: str) -> None:
        self.failure = failure
        super().__init__(message)


class PermanentSourceError(SourceAccessError):
    """Falha que não deve receber retry automático."""


class RetryLimitExceededError(SourceAccessError):
    """Falha transitória que consumiu todas as tentativas permitidas."""


TRANSIENT_STATUS_CATEGORIES = {
    408: FailureCategory.TIMEOUT,
    425: FailureCategory.UNAVAILABLE,
    429: FailureCategory.RATE_LIMITED,
    500: FailureCategory.UNAVAILABLE,
    502: FailureCategory.UNAVAILABLE,
    503: FailureCategory.UNAVAILABLE,
    504: FailureCategory.UNAVAILABLE,
}
PERMANENT_STATUS_CATEGORIES = {
    401: FailureCategory.AUTHENTICATION,
    403: FailureCategory.AUTHENTICATION,
    404: FailureCategory.NOT_FOUND,
}
TRANSIENT_SOURCE_CATEGORIES = {
    "InternalError": FailureCategory.UNAVAILABLE,
    "RequestTimeout": FailureCategory.TIMEOUT,
    "RequestTimeoutException": FailureCategory.TIMEOUT,
    "ServiceUnavailable": FailureCategory.UNAVAILABLE,
    "SlowDown": FailureCategory.RATE_LIMITED,
}
PERMANENT_SOURCE_CATEGORIES = {
    "AccessDenied": FailureCategory.AUTHENTICATION,
    "ExpiredToken": FailureCategory.AUTHENTICATION,
    "InvalidAccessKeyId": FailureCategory.AUTHENTICATION,
    "SignatureDoesNotMatch": FailureCategory.AUTHENTICATION,
    "NoSuchBucket": FailureCategory.NOT_FOUND,
    "NoSuchKey": FailureCategory.NOT_FOUND,
    "NoSuchObject": FailureCategory.NOT_FOUND,
}
TRANSIENT_EXCEPTION_CATEGORIES = {
    "ConnectTimeoutError": FailureCategory.TIMEOUT,
    "MaxRetryError": FailureCategory.UNAVAILABLE,
    "NewConnectionError": FailureCategory.UNAVAILABLE,
    "ProtocolError": FailureCategory.UNAVAILABLE,
    "ReadTimeoutError": FailureCategory.TIMEOUT,
}
TRANSIENT_ERRNOS = frozenset(
    {
        errno.ECONNABORTED,
        errno.ECONNREFUSED,
        errno.ECONNRESET,
        errno.EHOSTUNREACH,
        errno.ENETDOWN,
        errno.ENETUNREACH,
        errno.ETIMEDOUT,
    }
)


def _classification(
    category: FailureCategory,
    nature: FailureNature,
) -> FailureClassification:
    return FailureClassification(category=category, nature=nature)


def _status_code(exception: BaseException) -> int | None:
    direct_status = getattr(exception, "status", None)
    if isinstance(direct_status, int):
        return direct_status

    response = getattr(exception, "response", None)
    response_status = getattr(response, "status", None)
    return response_status if isinstance(response_status, int) else None


def _classify_builtin_exception(
    exception: BaseException,
) -> FailureClassification | None:
    declared_category = getattr(exception, "failure_category", None)
    if isinstance(declared_category, FailureCategory):
        return _classification(declared_category, FailureNature.PERMANENT)

    if isinstance(exception, TimeoutError):
        return _classification(FailureCategory.TIMEOUT, FailureNature.TRANSIENT)
    if isinstance(exception, ConnectionError):
        return _classification(FailureCategory.UNAVAILABLE, FailureNature.TRANSIENT)
    if isinstance(exception, OSError) and exception.errno in TRANSIENT_ERRNOS:
        return _classification(FailureCategory.UNAVAILABLE, FailureNature.TRANSIENT)
    return None


def _classify_source_code(exception: BaseException) -> FailureClassification | None:
    source_code = getattr(exception, "code", None)
    if not isinstance(source_code, str):
        return None
    transient_category = TRANSIENT_SOURCE_CATEGORIES.get(source_code)
    if transient_category is not None:
        return _classification(transient_category, FailureNature.TRANSIENT)

    permanent_category = PERMANENT_SOURCE_CATEGORIES.get(source_code)
    if permanent_category is not None:
        return _classification(permanent_category, FailureNature.PERMANENT)
    return None


def _classify_http_status(exception: BaseException) -> FailureClassification | None:
    status_code = _status_code(exception)
    transient_category = TRANSIENT_STATUS_CATEGORIES.get(status_code)
    if transient_category is not None:
        return _classification(transient_category, FailureNature.TRANSIENT)

    permanent_category = PERMANENT_STATUS_CATEGORIES.get(status_code)
    if permanent_category is not None:
        return _classification(permanent_category, FailureNature.PERMANENT)
    return None


def _classify_exception_name(
    exception: BaseException,
) -> FailureClassification | None:
    category = TRANSIENT_EXCEPTION_CATEGORIES.get(type(exception).__name__)
    return _classification(category, FailureNature.TRANSIENT) if category is not None else None


def _classify_single_exception(exception: BaseException) -> FailureClassification:
    classifiers = (
        _classify_builtin_exception,
        _classify_source_code,
        _classify_http_status,
        _classify_exception_name,
    )
    for classifier in classifiers:
        classification = classifier(exception)
        if classification is not None:
            return classification
    return _classification(FailureCategory.UNKNOWN, FailureNature.PERMANENT)


def classify_source_failure(exception: BaseException) -> FailureClassification:
    """Classifica uma exceção sem usar sua mensagem potencialmente sensível."""

    pending: list[BaseException] = [exception]
    visited: set[int] = set()
    while pending:
        current = pending.pop(0)
        if id(current) in visited:
            continue
        visited.add(id(current))

        classification = _classify_single_exception(current)
        if classification.category is not FailureCategory.UNKNOWN:
            return classification

        related = (
            current.__cause__,
            current.__context__,
            getattr(current, "reason", None),
        )
        pending.extend(item for item in related if isinstance(item, BaseException))

    return _classification(FailureCategory.UNKNOWN, FailureNature.PERMANENT)
