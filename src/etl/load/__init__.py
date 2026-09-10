"""Adaptador de carga do ETL — persiste os lotes tratados no DuckDB.

Não é uma etapa de transformação: recebe o resultado já tratado
(`TransformationResult`) e o grava, mantendo as tabelas de controle técnico
(idempotência por objeto, identidades carregadas para deduplicação e
checkpoints). O código de domínio permanece independente do driver: o
repositório é acessado por uma interface e pode ser trocado sem alterar o flow.
"""

from .duckdb_repository import DuckDbLoadRepository, LoadResult

__all__ = ["DuckDbLoadRepository", "LoadResult"]
