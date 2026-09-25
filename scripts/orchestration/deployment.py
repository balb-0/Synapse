"""Deployment agendado do ETL (OV-03).

Registra o flow `ingest-object` como um deployment do Prefect com **agendamento
cron** e parâmetros padrão. Servir este deployment habilita tanto a execução
agendada quanto a execução manual (UI/CLI) com os mesmos parâmetros — e o
histórico do Prefect registra os parâmetros de cada run.

    # serve o deployment (worker local com o schedule ativo):
    python scripts/orchestration/deployment.py

    # execução manual com parâmetros explícitos (backfill controlado):
    prefect deployment run 'ingest-object/agendado' -p source=empresas \
        -p bucket=sindusfarma -p key=landing/empresas.csv -p reprocess=true
"""

import os

from etl.orchestration.flow import ingest_object

if __name__ == "__main__":
    ingest_object.serve(
        name="agendado",
        cron="0 3 * * *",  # diariamente às 03:00 (janela de baixa carga)
        parameters={
            "source": "empresas",
            "bucket": os.environ.get("ETL_MINIO_BUCKET", "sindusfarma"),
            "key": "landing/empresas.csv",
        },
        tags=["etl", "ingest"],
    )
