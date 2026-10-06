"""Comando único do pipeline (PL-01..PL-03): backfill, carga, reconciliação e publicação.

Encadeia as rotinas existentes sobre o mesmo arquivo DuckDB: o caminho é
resolvido uma única vez (`ETL_DUCKDB_PATH`) e passado a todas as etapas,
eliminando a chance de ingestão e cubos apontarem para bancos distintos. A
carga analítica só começa depois que todas as fontes configuradas concluíram a
ingestão — status `loaded` ou `ignored`; qualquer outro resultado aborta o
encadeamento antes de tocar nos cubos.

Depois da carga, o relatório de reconciliação decide a publicação: os sete
Parquet só são gravados quando `reconciled=true`, e o manifesto aponta o
`load_id` efetivo da carga reconciliada. `reconciled=false` não publica nada.

A saída registra os identificadores e o status de cada etapa: o status por
fonte do backfill, o `load_id` da geração analítica, o veredito da
reconciliação e a geração publicada. Toda falha sobe como
:class:`PipelineStageError` com a etapa identificada e a causa encadeada;
reexecutar o comando após uma falha é seguro — a ingestão é idempotente e a
carga analítica substitui os fatos em vez de acumular.
"""

from __future__ import annotations

import calendar
import time
from datetime import datetime
from pathlib import Path

from prefect import flow, get_run_logger

from etl.extraction import load_extraction_settings
from etl.load.config import load_duckdb_settings
from etl.orchestration.analytics import (
    SOURCE_ORDER,
    load_warehouse,
    publish_warehouse,
    reconcile_warehouse,
)
from etl.orchestration.flow import EXTRACTORS, _log_event, backfill
from etl.orchestration.lock import database_lock

PIPELINE_EVENT = "orchestration.pipeline.emitted"

# Ordem compatível com os relacionamentos de consistência (RELATIONS): pais
# antes dos filhos — respostas por último, que valida contra pesquisas,
# questões e empresas.
DEFAULT_SOURCES = SOURCE_ORDER

# Uma fonte `ignored` já está íntegra no banco (idempotência por objeto); para
# efeito da carga analítica ela conta como concluída tanto quanto `loaded`.
COMPLETED_STATUSES = frozenset({"loaded", "ignored"})


class PipelineStageError(RuntimeError):
    """Falha do pipeline com a etapa identificada (PL-03).

    ``stage`` nomeia onde o encadeamento parou (``backfill``,
    ``load_analytics``, ``reconciliation`` ou ``publication``); a causa
    original fica encadeada em ``__cause__``. As garantias de estado são das
    próprias etapas: a publicação é atômica e não troca o ``current.json``
    anterior em caso de falha, e a reexecução não duplica fatos — a ingestão é
    idempotente por objeto e a carga analítica substitui os fatos na mesma
    transação em vez de acumular.
    """

    def __init__(self, stage: str, message: str) -> None:
        super().__init__(f"[{stage}] {message}")
        self.stage = stage


class PipelineAbortedError(PipelineStageError):
    """O backfill não concluiu todas as fontes; a carga analítica não executa."""

    def __init__(self, message: str) -> None:
        super().__init__("backfill", message)


class ReconciliationFailedError(PipelineStageError):
    """O relatório analítico não reconciliou; nada é publicado."""

    def __init__(self, message: str) -> None:
        super().__init__("reconciliation", message)


@flow(name="pipeline-completo")
def run_pipeline(
    sources: list[str] | None = None,
    *,
    publish_dir: str | Path,
    reprocess: bool = False,
    db_path: str | None = None,
    observed_at: datetime | None = None,
) -> dict:
    """Backfill, carga analítica, reconciliação e publicação encadeados.

    ``sources`` ausente usa as seis fontes na ordem de dependência; bucket e
    prefixo vêm da configuração de extração (`ETL_MINIO_BUCKET`,
    `ETL_MINIO_INPUT_PREFIX`). ``observed_at`` repassa à carga analítica o
    fechamento observado do C03 (precisa ser fim de mês, validado lá).
    ``publish_dir`` é o destino dos sete Parquet — fora do checkout, validado
    por ``publish_cubes``; a publicação só acontece com ``reconciled=true``.
    """
    logger = get_run_logger()
    started = time.monotonic()

    if observed_at is not None:
        if not isinstance(observed_at, datetime):
            raise ValueError("observed_at deve ser datetime")
        if observed_at.day != calendar.monthrange(observed_at.year, observed_at.month)[1]:
            raise ValueError("observed_at deve ocorrer no último dia do mês")

    selected = list(DEFAULT_SOURCES) if sources is None else list(sources)
    unknown = sorted(set(selected) - set(EXTRACTORS))
    if unknown:
        raise ValueError(f"fontes desconhecidas: {', '.join(unknown)}")

    if len(selected) != len(DEFAULT_SOURCES) or set(selected) != set(DEFAULT_SOURCES):
        raise ValueError("o pipeline completo exige as seis fontes, sem repetição")
    selected = list(DEFAULT_SOURCES)
    destination = Path(publish_dir)
    if destination.is_symlink():
        raise ValueError("diretório de publicação simbólico não é permitido")
    destination = destination.resolve()
    if any((parent / ".git").exists() for parent in (destination, *destination.parents)):
        raise ValueError("a publicação deve ficar fora do repositório")

    settings = load_extraction_settings()
    database_settings = load_duckdb_settings({"database_path": db_path})
    db_path = str(database_settings.database_path)

    _log_event(
        logger,
        PIPELINE_EVENT,
        status="started",
        sources=selected,
        db_path=db_path,
        reprocess=reprocess,
    )

    def failed(stage: str, error: Exception) -> PipelineStageError:
        """Marco de falha com a etapa identificada; a causa segue encadeada."""
        _log_event(
            logger,
            PIPELINE_EVENT,
            status="failed",
            failed_stage=stage,
            sources=selected,
            error=type(error).__name__,
            duration_ms=round((time.monotonic() - started) * 1000, 3),
        )
        return PipelineStageError(stage, str(error))

    try:
        backfill_report = backfill(
            sources=selected,
            bucket=settings.minio_bucket,
            prefix=settings.minio_input_prefix,
            reprocess=reprocess,
            db_path=db_path,
        )
    except Exception as error:
        raise failed("backfill", error) from error

    results = backfill_report.get("results", [])
    if len(results) != len(selected) or {result.get("source") for result in results} != set(
        selected
    ):
        _log_event(
            logger,
            PIPELINE_EVENT,
            status="aborted",
            failed_stage="backfill",
            duration_ms=round((time.monotonic() - started) * 1000, 3),
        )
        raise PipelineAbortedError("o backfill não confirmou uma ocorrência de cada fonte")
    pending = [
        result["source"] for result in results if result.get("status") not in COMPLETED_STATUSES
    ]
    if pending:
        _log_event(
            logger,
            PIPELINE_EVENT,
            status="aborted",
            failed_stage="backfill",
            sources=selected,
            pending=pending,
            duration_ms=round((time.monotonic() - started) * 1000, 3),
        )
        raise PipelineAbortedError("fontes sem conclusão no backfill: " + ", ".join(pending))

    # O mesmo lock de ingest_object exclui escritores orquestrados enquanto
    # as três tasks executam. Cada task fecha sua conexão antes da próxima.
    try:
        with database_lock(
            database_settings.database_path, database_settings.write_lock_timeout_seconds
        ):
            try:
                analytics = load_warehouse(db_path, observed_at)
            except Exception as error:
                raise failed("load_analytics", error) from error
            try:
                report = reconcile_warehouse(db_path, analytics["load_id"])
            except ValueError as error:
                _log_event(
                    logger,
                    PIPELINE_EVENT,
                    status="reconciliation_failed",
                    failed_stage="reconciliation",
                    error=type(error).__name__,
                )
                raise ReconciliationFailedError(str(error)) from error
            except Exception as error:
                raise failed("reconciliation", error) from error
            if not report["reconciled"] or report["load_id"] != analytics["load_id"]:
                raise ReconciliationFailedError(
                    "relatório analítico não reconciliou com esta carga"
                )
            try:
                manifest = publish_warehouse(db_path, str(destination), analytics["load_id"])
            except Exception as error:
                raise failed("publication", error) from error

    except PipelineStageError:
        raise
    except Exception as error:
        raise failed("load_analytics", error) from error

    _log_event(
        logger,
        PIPELINE_EVENT,
        status="completed",
        sources=selected,
        load_id=analytics["load_id"],
        generation=manifest["generation"],
        duration_ms=round((time.monotonic() - started) * 1000, 3),
    )
    return {
        "status": "completed",
        "db_path": db_path,
        "backfill": backfill_report,
        "analytics": analytics,
        "reconciliation": report,
        "publication": {
            "generation": manifest["generation"],
            "load_reference": manifest["load_reference"],
            "tables": {name: table["rows"] for name, table in manifest["tables"].items()},
        },
    }
