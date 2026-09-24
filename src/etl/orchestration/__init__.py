"""Plano de controle do ETL — orquestração com Prefect.

O flow amarra extração, transformação e carga como tarefas separadas. Uma falha
em uma etapa impede a execução das dependentes. O código de domínio permanece
sem dependência do Prefect: a orquestração apenas coordena as etapas já
implementadas em `extraction/`, `transformation/` e `load/`.
"""

from .flow import backfill, ingest_object
from .logging_config import configure_json_logging

__all__ = ["backfill", "configure_json_logging", "ingest_object"]
