"""Comando único do pipeline (PL-01/PL-02): backfill, carga, reconciliação e publicação.

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
reconciliação e a geração publicada.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

import duckdb
from prefect import flow, get_run_logger

from etl.analytics.load import load_analytics
from etl.analytics.publish import publish_cubes
from etl.analytics.reconcile import reconcile_analytics
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


class ReconciliationFailedError(RuntimeError):
    """O relatório analítico não reconciliou; nada é publicado."""


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

    # Conexão de escrita fechada antes de reabrir: a reconciliação lê em
    # read_only e a publicação abre a própria conexão read_only sobre o arquivo.
    with duckdb.connect(db_path, read_only=True) as con:
        report = reconcile_analytics(con)

    if not report.reconciled:
        _log_event(
            logger,
            PIPELINE_EVENT,
            status="reconciliation_failed",
            sources=selected,
            load_id=analytics.load_id,
            duration_ms=round((time.monotonic() - started) * 1000, 3),
        )
        raise ReconciliationFailedError(
            f"relatório analítico não reconciliou (load_id={analytics.load_id}); nada foi publicado"
        )
    if report.load_id != analytics.load_id:
        # O relatório reconcilia sempre a carga corrente; divergência aqui
        # significa outra carga concluída entre as duas etapas — publicar
        # atribuiria os Parquet a um load_id que não é o verificado.
        raise ReconciliationFailedError(
            f"a reconciliação aponta load_id={report.load_id}, mas esta execução "
            f"carregou load_id={analytics.load_id}; nada foi publicado"
        )

    manifest = publish_cubes(Path(db_path), Path(publish_dir), load_reference=report.load_id)

    _log_event(
        logger,
        PIPELINE_EVENT,
        status="completed",
        sources=selected,
        load_id=analytics.load_id,
        generation=manifest["generation"],
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
        "reconciliation": {
            "reconciled": True,
            "load_id": report.load_id,
        },
        "publication": {
            "generation": manifest["generation"],
            "load_reference": manifest["load_reference"],
            "tables": {name: table["rows"] for name, table in manifest["tables"].items()},
        },
    }
