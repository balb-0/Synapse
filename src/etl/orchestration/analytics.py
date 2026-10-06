"""Trecho DW e publicação após a confirmação de um conjunto completo."""

from __future__ import annotations

import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE
from prefect.runtime import flow_run, task_run

from etl.analytics.load import load_analytics
from etl.analytics.publish import publish_cubes
from etl.analytics.reconcile import reconcile_analytics
from etl.load.config import load_duckdb_settings
from etl.load.connection import connect_with_retry
from etl.orchestration.flow import _log_event, _should_retry
from etl.orchestration.lock import database_lock

SOURCE_ORDER = ("pesquisas", "empresas", "clientes", "questoes", "respondentes", "respostas")


def _event(stage: str, started: float, status: str, **attributes: object) -> None:
    _log_event(
        get_run_logger(),
        f"orchestration.{stage}.emitted",
        run_id=flow_run.id,
        attempts=task_run.run_count or 1,
        status=status,
        duration_ms=round((time.monotonic() - started) * 1000, 3),
        **attributes,
    )


@task(
    retries=2,
    retry_delay_seconds=1,
    retry_condition_fn=_should_retry,
    timeout_seconds=3600,
    cache_policy=NO_CACHE,
)
def load_warehouse(db_path: str, observed_at: datetime | None = None) -> dict:
    """A carga de fatos mantém sua transação; nenhuma data de observação é inventada."""
    started = time.monotonic()
    settings = load_duckdb_settings({"database_path": db_path})
    try:
        with connect_with_retry(
            settings.database_path, settings.write_lock_timeout_seconds
        ) as connection:
            result = load_analytics(connection, observed_at=observed_at)
        output = asdict(result)
        if output["fechamento"] is not None:
            output["fechamento"] = output["fechamento"].isoformat()
        _event("analytics_load", started, "success", load_reference=result.load_id)
        return output
    except Exception as error:
        _event("analytics_load", started, "failed", error_type=type(error).__name__)
        raise


@task(
    retries=2,
    retry_delay_seconds=1,
    retry_condition_fn=_should_retry,
    timeout_seconds=3600,
    cache_policy=NO_CACHE,
)
def reconcile_warehouse(db_path: str, load_reference: str) -> dict:
    """Uma carga desbalanceada ou substituída impede a publicação."""
    started = time.monotonic()
    settings = load_duckdb_settings({"database_path": db_path})
    try:
        with connect_with_retry(
            settings.database_path, settings.write_lock_timeout_seconds, read_only=True
        ) as connection:
            report = reconcile_analytics(connection)
        if not report.reconciled or report.load_id != load_reference:
            raise ValueError("a carga analítica não reconciliou com a ingestão atual")
        _event("analytics_reconcile", started, "success", load_reference=load_reference)
        return report.as_dict()
    except Exception as error:
        _event("analytics_reconcile", started, "failed", error_type=type(error).__name__)
        raise


@task(
    retries=2,
    retry_delay_seconds=1,
    retry_condition_fn=_should_retry,
    timeout_seconds=3600,
    cache_policy=NO_CACHE,
)
def publish_warehouse(db_path: str, output: str, load_reference: str) -> dict:
    """Publica os sete Parquet somente após reconciliação no mesmo run."""
    started = time.monotonic()
    settings = load_duckdb_settings({"database_path": db_path})
    try:
        manifest = publish_cubes(
            settings.database_path, Path(output), load_reference=load_reference
        )
        _event(
            "analytics_publish",
            started,
            "success",
            load_reference=load_reference,
            generation=manifest["generation"],
        )
        return manifest
    except Exception as error:
        _event("analytics_publish", started, "failed", error_type=type(error).__name__)
        raise


@flow(name="complete-warehouse")
def complete_warehouse(
    *, db_path: str | None, output: str, observed_at: datetime | None = None
) -> dict:
    """Mantém writers orquestrados fora do DW até concluir publicação ou falhar."""
    settings = load_duckdb_settings({"database_path": db_path})
    with database_lock(settings.database_path, settings.write_lock_timeout_seconds):
        loaded = load_warehouse(str(settings.database_path), observed_at)
        report = reconcile_warehouse(str(settings.database_path), loaded["load_id"])
        manifest = publish_warehouse(str(settings.database_path), output, loaded["load_id"])
    return {"load": loaded, "reconciliation": report, "manifest": manifest}
