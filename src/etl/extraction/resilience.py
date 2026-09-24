"""Retry limitado para operações de acesso às fontes."""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, TypeVar

from .failures import (
    FailureNature,
    FailureRecorder,
    PermanentSourceError,
    RetryLimitExceededError,
    SourceFailure,
    StandardFailureRecorder,
    classify_source_failure,
)

if TYPE_CHECKING:
    from .config import ExtractionSettings


Result = TypeVar("Result")


class Sleep(Protocol):
    def __call__(self, seconds: float) -> None: ...


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Limites e espera exponencial das tentativas de uma operação."""

    max_attempts: int = 3
    initial_delay_seconds: float = 0.5
    backoff_multiplier: float = 2.0
    max_delay_seconds: float = 5.0

    def __post_init__(self) -> None:
        if (
            isinstance(self.max_attempts, bool)
            or not isinstance(self.max_attempts, int)
            or self.max_attempts < 1
        ):
            raise ValueError("max_attempts deve ser um inteiro positivo")

        numeric_values = (
            self.initial_delay_seconds,
            self.backoff_multiplier,
            self.max_delay_seconds,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            for value in numeric_values
        ):
            raise ValueError("os valores de espera devem ser numéricos")
        if not all(math.isfinite(value) for value in numeric_values):
            raise ValueError("os valores de espera devem ser finitos")
        if self.initial_delay_seconds < 0 or self.max_delay_seconds < 0:
            raise ValueError("os tempos de espera não podem ser negativos")
        if self.backoff_multiplier < 1:
            raise ValueError("backoff_multiplier deve ser maior ou igual a um")
        if self.max_delay_seconds < self.initial_delay_seconds:
            raise ValueError("max_delay_seconds deve comportar a espera inicial")

    def delay_after(self, failed_attempt: int) -> float:
        """Calcula a espera limitada antes da próxima tentativa."""

        try:
            delay = self.initial_delay_seconds * (self.backoff_multiplier ** (failed_attempt - 1))
        except OverflowError:
            return self.max_delay_seconds
        return min(delay, self.max_delay_seconds)


class RetryExecutor:
    """Executa operações de fonte segundo uma política e registra cada falha."""

    def __init__(
        self,
        *,
        policy: RetryPolicy | None = None,
        recorder: FailureRecorder | None = None,
        sleep: Sleep = time.sleep,
    ) -> None:
        self._policy = policy or RetryPolicy()
        self._recorder = recorder or StandardFailureRecorder()
        self._sleep = sleep

    @classmethod
    def from_settings(
        cls,
        settings: ExtractionSettings,
        *,
        recorder: FailureRecorder | None = None,
        sleep: Sleep = time.sleep,
    ) -> RetryExecutor:
        """Monta a política usando somente configurações já validadas."""

        return cls(
            policy=RetryPolicy(
                max_attempts=settings.max_attempts,
                initial_delay_seconds=settings.retry_initial_delay_seconds,
                max_delay_seconds=settings.retry_max_delay_seconds,
            ),
            recorder=recorder,
            sleep=sleep,
        )

    def execute(
        self,
        operation: Callable[[], Result],
        *,
        source: str,
        operation_name: str,
    ) -> Result:
        for attempt in range(1, self._policy.max_attempts + 1):
            started = time.monotonic()
            try:
                return operation()
            except Exception as exception:
                failure = self._handle_failed_attempt(
                    exception,
                    source=source,
                    operation_name=operation_name,
                    attempt=attempt,
                    duration_ms=round((time.monotonic() - started) * 1000, 3),
                )
                if failure.nature is FailureNature.PERMANENT:
                    raise PermanentSourceError(
                        failure,
                        f"falha permanente de acesso à fonte {source} ({failure.category.value})",
                    ) from exception
                if not failure.retry_scheduled:
                    raise RetryLimitExceededError(
                        failure,
                        "limite de tentativas atingido para a fonte "
                        f"{source} ({failure.category.value})",
                    ) from exception
                self._sleep(failure.next_delay_seconds)

        raise AssertionError("a política de retry deve executar ao menos uma tentativa")

    def _handle_failed_attempt(
        self,
        exception: BaseException,
        *,
        source: str,
        operation_name: str,
        attempt: int,
        duration_ms: float,
    ) -> SourceFailure:
        classification = classify_source_failure(exception)
        retry_scheduled = classification.retryable and attempt < self._policy.max_attempts
        delay = self._policy.delay_after(attempt) if retry_scheduled else 0.0
        failure = SourceFailure(
            source=source,
            operation=operation_name,
            category=classification.category,
            nature=classification.nature,
            attempt=attempt,
            max_attempts=self._policy.max_attempts,
            exception_type=type(exception).__name__,
            retry_scheduled=retry_scheduled,
            next_delay_seconds=delay,
            duration_ms=duration_ms,
        )
        self._recorder.record(failure)
        return failure

    def record_failure(
        self,
        exception: BaseException,
        *,
        source: str,
        operation_name: str,
        duration_ms: float = 0.0,
    ) -> SourceFailure:
        """Registra uma falha ocorrida fora de uma operação com retry."""

        classification = classify_source_failure(exception)
        failure = SourceFailure(
            source=source,
            operation=operation_name,
            category=classification.category,
            nature=classification.nature,
            attempt=1,
            max_attempts=1,
            exception_type=type(exception).__name__,
            retry_scheduled=False,
            next_delay_seconds=0.0,
            duration_ms=duration_ms,
        )
        self._recorder.record(failure)
        return failure
