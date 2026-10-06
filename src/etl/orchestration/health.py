"""Health check do orquestrador (Prefect) e do banco de ingestão (OB-09).

Duas checagens independentes, combinadas num só relatório: a orquestração só
está saudável se o servidor Prefect configurado responde e o banco de
ingestão aceita conexão/consulta/persistência (``etl.load.environment``,
já usado pelo health check da carga). O resultado é publicado como um evento
técnico único, no mesmo formato das demais camadas (ADR 0001), para aparecer
no mesmo índice que alimenta o painel operacional (OB-08) e as regras de
alerta mínimas.
"""

from __future__ import annotations

import http.client
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

import duckdb

from etl.load.config import ConfigurationError, DuckDBSettings
from etl.load.environment import DatabaseEnvironmentError, HealthCheck, run_health_check

HEALTH_CHECK_EVENT = "orchestration.health_check.emitted"
HEALTH_CHECK_STAGE = "orchestration"
PREFECT_HEALTH_TIMEOUT_SECONDS = 5.0

HttpGet = Callable[[str, float], int]


def _default_http_get(url: str, timeout: float) -> int:
    """GET simples devolvendo só o status HTTP; sem retry (a checagem é o próprio sinal)."""
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        return response.status


@dataclass(frozen=True, slots=True)
class DatabaseHealthCheck(HealthCheck):
    """Lock de outro processo é contenção; a disponibilidade ainda é desconhecida."""

    busy: bool = False


@dataclass(frozen=True, slots=True)
class OrchestrationHealthReport:
    """Resultado combinado das duas checagens de uma execução do health check."""

    prefect: HealthCheck
    database: HealthCheck
    duration_ms: float

    @property
    def passed(self) -> bool:
        return self.prefect.passed and self.database.passed

    @property
    def status(self) -> str:
        if self.prefect.passed and getattr(self.database, "busy", False):
            return "busy"
        return "ok" if self.passed else "degraded"

    def as_dict(self) -> dict[str, str | float | bool | None]:
        busy = getattr(self.database, "busy", False)
        return {
            "event": HEALTH_CHECK_EVENT,
            "stage": HEALTH_CHECK_STAGE,
            "status": self.status,
            "prefect_available": self.prefect.passed,
            "prefect_detail": self.prefect.detail,
            "database_available": None if busy else self.database.passed,
            "database_status": "busy"
            if busy
            else ("available" if self.database.passed else "unavailable"),
            "database_detail": self.database.detail,
            "duration_ms": self.duration_ms,
        }


def check_prefect_health(
    api_url: str | None, *, http_get: HttpGet = _default_http_get
) -> HealthCheck:
    """Verifica se o servidor Prefect em ``api_url`` responde em ``/health``.

    ``api_url`` é o mesmo ``PREFECT_API_URL`` que o próprio Prefect já lê
    (OQ-03 publica os flows nele); sem valor configurado não há orquestrador
    remoto para checar — reportar isso como falha explícita é melhor do que
    supor um endpoint default que pode nem existir neste ambiente.
    """
    if not api_url:
        return HealthCheck(
            name="prefect_api", passed=False, detail="PREFECT_API_URL não configurado"
        )

    url = f"{api_url.rstrip('/')}/health"
    try:
        status = http_get(url, PREFECT_HEALTH_TIMEOUT_SECONDS)
    except (urllib.error.URLError, http.client.HTTPException, OSError) as error:
        # http.client.HTTPException não é OSError: cobre o caso de
        # PREFECT_API_URL apontar para uma porta que responde, mas não fala
        # HTTP (resposta corrompida) — sem isso, esse erro escaparia do health
        # check inteiro em vez de virar uma falha relatada como as demais.
        return HealthCheck(name="prefect_api", passed=False, detail=f"{url} inacessível: {error}")

    if status != 200:
        return HealthCheck(
            name="prefect_api", passed=False, detail=f"{url} respondeu HTTP {status}"
        )
    return HealthCheck(name="prefect_api", passed=True, detail=f"{url} respondeu HTTP 200")


def check_database_health(settings: DuckDBSettings) -> HealthCheck:
    """Reaproveita o health check da carga (``etl.load.environment``) como uma única checagem.

    ``run_health_check`` abre a conexão direto, sem o retry com espera de
    ``duckdb_repository._connect_with_retry`` usado pela carga real: rodar
    este health check durante uma carga em andamento pode reportar uma falha
    transitória de lock de escrita que a carga em si teria esperado passar.
    O erro de lock externo do DuckDB é classificado como busy, sem afirmar
    indisponibilidade nem executar uma escrita concorrente.
    """
    try:
        report = run_health_check(settings)
    except (ConfigurationError, DatabaseEnvironmentError) as error:
        cause = error.__cause__
        while cause is not None:
            if isinstance(cause, duckdb.IOException) and "could not set lock" in str(cause).lower():
                return DatabaseHealthCheck(
                    name="duckdb", passed=False, detail=str(error), busy=True
                )
            cause = cause.__cause__
        return HealthCheck(name="duckdb", passed=False, detail=str(error))

    if not report.passed:
        falhas = "; ".join(check.detail for check in report.checks if not check.passed)
        return HealthCheck(name="duckdb", passed=False, detail=falhas)
    return HealthCheck(
        name="duckdb",
        passed=True,
        detail=f"DuckDB {report.duckdb_version} em {report.database_path}",
    )


def run_orchestration_health_check(
    *,
    api_url: str | None,
    settings: DuckDBSettings,
    http_get: HttpGet = _default_http_get,
) -> OrchestrationHealthReport:
    started = time.monotonic()
    prefect = check_prefect_health(api_url, http_get=http_get)
    database = check_database_health(settings)
    return OrchestrationHealthReport(
        prefect=prefect,
        database=database,
        duration_ms=round((time.monotonic() - started) * 1000, 3),
    )


def log_health_check(
    report: OrchestrationHealthReport, logger: logging.Logger | None = None
) -> None:
    """Publica o resultado combinado como um único evento (ADR 0001)."""
    target_logger = logger or logging.getLogger("etl.orchestration")
    target_logger.info(HEALTH_CHECK_EVENT, extra=report.as_dict())
