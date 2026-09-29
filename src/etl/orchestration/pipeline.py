"""Comando único do pipeline (PL-01): backfill seguido de carga analítica.

Encadeia o flow `backfill` e a rotina `load_analytics` sobre o mesmo arquivo
DuckDB: o caminho é resolvido uma única vez (`ETL_DUCKDB_PATH`) e passado às
duas etapas, eliminando a chance de ingestão e cubos apontarem para bancos
distintos. A carga analítica só começa depois que todas as fontes configuradas
concluíram a ingestão — status `loaded` ou `ignored`; qualquer outro resultado
aborta o encadeamento antes de tocar nos cubos.

A saída registra os identificadores e o status de cada etapa: o status por
fonte reportado pelo backfill e o `load_id` da geração analítica.
"""

from __future__ import annotations

import time
from datetime import datetime

import duckdb
from prefect import flow, get_run_logger

from etl.analytics.load import load_analytics
from etl.extraction import load_extraction_settings
from etl.load.config import load_duckdb_settings
from etl.orchestration.flow import EXTRACTORS, _log_event, backfill

PIPELINE_EVENT = "orchestration.pipeline.emitted"

# Ordem compatível com os relacionamentos de consistência (RELATIONS): pais
# antes dos filhos — respostas por último, que valida contra pesquisas,
# questões e empresas.
DEFAULT_SOURCES = (
    "pesquisas",
    "empresas",
    "clientes",
    "questoes",
    "respondentes",
    "respostas",
)

# Uma fonte `ignored` já está íntegra no banco (idempotência por objeto); para
# efeito da carga analítica ela conta como concluída tanto quanto `loaded`.
COMPLETED_STATUSES = frozenset({"loaded", "ignored"})


class PipelineAbortedError(RuntimeError):
    """O backfill não concluiu todas as fontes; a carga analítica não executa."""


@flow(name="pipeline-completo")
def run_pipeline(
    sources: list[str] | None = None,
    *,
    reprocess: bool = False,
    db_path: str | None = None,
    observed_at: datetime | None = None,
) -> dict:
    """Backfill das fontes configuradas seguido da carga analítica dos cubos.

    ``sources`` ausente usa as seis fontes na ordem de dependência; bucket e
    prefixo vêm da configuração de extração (`ETL_MINIO_BUCKET`,
    `ETL_MINIO_INPUT_PREFIX`). ``observed_at`` repassa à carga analítica o
    fechamento observado do C03 (precisa ser fim de mês, validado lá).
    """
    logger = get_run_logger()
    started = time.monotonic()

    selected = list(sources) if sources else list(DEFAULT_SOURCES)
    unknown = sorted(set(selected) - set(EXTRACTORS))
    if unknown:
        raise ValueError(f"fontes desconhecidas: {', '.join(unknown)}")

    settings = load_extraction_settings()
    db_path = db_path or str(load_duckdb_settings().database_path)

    _log_event(
        logger,
        PIPELINE_EVENT,
        status="started",
        sources=selected,
        db_path=db_path,
        reprocess=reprocess,
    )

    backfill_report = backfill(
        sources=selected,
        bucket=settings.minio_bucket,
        prefix=settings.minio_input_prefix,
        reprocess=reprocess,
        db_path=db_path,
    )

    pending = [
        result["source"]
        for result in backfill_report["results"]
        if result["status"] not in COMPLETED_STATUSES
    ]
    if pending:
        _log_event(
            logger,
            PIPELINE_EVENT,
            status="aborted",
            sources=selected,
            pending=pending,
            duration_ms=round((time.monotonic() - started) * 1000, 3),
        )
        raise PipelineAbortedError("fontes sem conclusão no backfill: " + ", ".join(pending))

    with duckdb.connect(db_path) as con:
        analytics = load_analytics(con, observed_at=observed_at)

    _log_event(
        logger,
        PIPELINE_EVENT,
        status="completed",
        sources=selected,
        load_id=analytics.load_id,
        duration_ms=round((time.monotonic() - started) * 1000, 3),
    )
    return {
        "status": "completed",
        "db_path": db_path,
        "backfill": backfill_report,
        "analytics": {
            "load_id": analytics.load_id,
            "pesquisas": analytics.pesquisas,
            "participacoes": analytics.participacoes,
            "perguntas": analytics.perguntas,
            "orfaos": analytics.orfaos,
            "fechamento": str(analytics.fechamento) if analytics.fechamento else None,
        },
    }
