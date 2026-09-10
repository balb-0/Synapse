"""Plano de controle do ETL — orquestração com Prefect.

O flow amarra extração, transformação e carga como tarefas separadas. Uma falha
em uma etapa impede a execução das dependentes. O código de domínio permanece
sem dependência do Prefect: a orquestração apenas coordena as etapas já
implementadas em `extraction/`, `transformation/` e `load/`.
"""

from .flow import ingest_object

__all__ = ["ingest_object"]
