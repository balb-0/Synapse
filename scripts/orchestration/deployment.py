"""Serve a agenda fonte → ingestão → DW → Parquet com histórico no Prefect.

    python scripts/orchestration/deployment.py
    prefect deployment run 'pipeline-completo/agendado-dw'

Cada execução confirma as seis fontes antes de publicar; arquivo ausente ou
reconciliação inválida falha o flow e conserva a geração anterior. A data de
observação C03 é um parâmetro explícito, sem valor fabricado pela agenda.
"""

import os

from etl.orchestration import configure_json_logging
from etl.orchestration.analytics import SOURCE_ORDER
from etl.orchestration.pipeline import run_pipeline


def scheduled_parameters() -> dict:
    """Parâmetros públicos; credenciais vêm da configuração validada do ETL."""
    return {
        "sources": list(SOURCE_ORDER),
        "publish_dir": os.environ.get("ETL_PUBLISH_DIR", "/data/publicacao"),
    }


if __name__ == "__main__":
    configure_json_logging()
    run_pipeline.serve(
        name="agendado-dw",
        cron="0 3 * * *",
        parameters=scheduled_parameters(),
        tags=["etl", "backfill", "analytics"],
    )
