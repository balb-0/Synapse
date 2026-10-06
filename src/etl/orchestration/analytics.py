"""Trecho DW e publicação após a confirmação de um conjunto completo."""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from prefect import get_run_logger, task
from prefect.cache_policies import NO_CACHE
from prefect.runtime import flow_run, task_run

from etl.analytics.load import load_analytics
from etl.analytics.publish import PUBLICATIONS, publish_cubes
from etl.analytics.reconcile import reconcile_analytics
from etl.load.config import load_duckdb_settings
from etl.load.connection import connect_with_retry
from etl.orchestration.flow import _log_event, _should_retry

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
            raise ValueError("relatório analítico não reconciliou com a ingestão atual")
        _event("analytics_reconcile", started, "success", load_reference=load_reference)
        return report.as_dict()
    except Exception as error:
        _event("analytics_reconcile", started, "failed", error_type=type(error).__name__)
        raise


def _published_for_load(connection, output: Path, load_reference: str) -> dict | None:
    """Reutiliza só a geração íntegra cujo conteúdo coincide com a origem atual.

    Isto cobre a repetição após a troca atômica de current.json. Contagens
    iguais sozinhas não bastam: a comparação EXCEPT ALL preserva multiplicidade.
    """
    try:
        if (output / "current.json").is_symlink():
            return None
        pointer = json.loads((output / "current.json").read_text())
        generation = pointer["generation"]
        if not isinstance(generation, str) or not re.fullmatch(r"[a-f0-9]{32}", generation):
            return None
        directory = output / generation
        if directory.is_symlink():
            return None
        if (directory / "manifest.json").is_symlink():
            return None
        if {path.name for path in directory.iterdir()} != {
            "manifest.json",
            *(f"{name}.parquet" for name in PUBLICATIONS),
        }:
            return None
        manifest = json.loads((directory / "manifest.json").read_text())
        if (
            manifest["generation"] != generation
            or manifest["load_reference"] != load_reference
            or type(manifest["version"]) is not int
            or manifest["version"] != 1
            or set(manifest["tables"]) != set(PUBLICATIONS)
        ):
            return None
        for name, query in PUBLICATIONS.items():
            metadata = manifest["tables"][name]
            path = directory / f"{name}.parquet"
            if (
                metadata["file"] != path.name
                or path.is_symlink()
                or type(metadata["rows"]) is not int
                or metadata["rows"] < 0
                or not isinstance(metadata["columns"], list)
                or not all(isinstance(column, str) for column in metadata["columns"])
                or not isinstance(metadata["sha256"], str)
                or not re.fullmatch(r"[a-f0-9]{64}", metadata["sha256"])
            ):
                return None
            if hashlib.sha256(path.read_bytes()).hexdigest() != metadata["sha256"]:
                return None
            parquet = str(path).replace("'", "''")
            file_query = f"SELECT * FROM read_parquet('{parquet}')"
            columns = [item[0] for item in connection.execute(file_query + " LIMIT 0").description]
            expected_columns = [
                item[0] for item in connection.execute(query + " LIMIT 0").description
            ]
            if columns != metadata["columns"] or columns != expected_columns:
                return None
            count = connection.execute(f"SELECT count(*) FROM ({file_query})").fetchone()[0]
            if count != metadata["rows"]:
                return None
            difference = connection.execute(
                f"SELECT count(*) FROM (({query}) EXCEPT ALL ({file_query}))"
            ).fetchone()[0]
            reverse = connection.execute(
                f"SELECT count(*) FROM (({file_query}) EXCEPT ALL ({query}))"
            ).fetchone()[0]
            if difference or reverse:
                return None
        return manifest
    except (OSError, ValueError, KeyError, TypeError):
        return None


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
        destination = Path(output)
        if destination.is_symlink():
            raise ValueError("diretório de publicação simbólico não é permitido")
        destination = destination.resolve()
        if any((parent / ".git").exists() for parent in (destination, *destination.parents)):
            raise ValueError("a publicação deve ficar fora do repositório")
        with connect_with_retry(
            settings.database_path, settings.write_lock_timeout_seconds, read_only=True
        ) as connection:
            connection.execute("BEGIN TRANSACTION")
            report = reconcile_analytics(connection)
            if not report.reconciled or report.load_id != load_reference:
                raise ValueError("a origem mudou ou não reconciliou antes da publicação")
            manifest = _published_for_load(connection, destination, load_reference)
            connection.execute("COMMIT")
        reused = manifest is not None
        if manifest is None:
            manifest = publish_cubes(
                settings.database_path, destination, load_reference=load_reference
            )
        _event(
            "analytics_publish",
            started,
            "success",
            load_reference=load_reference,
            generation=manifest["generation"],
            reused=reused,
        )
        return manifest
    except Exception as error:
        _event("analytics_publish", started, "failed", error_type=type(error).__name__)
        raise
