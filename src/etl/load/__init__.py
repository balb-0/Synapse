"""Adaptador de carga do ETL — persiste os lotes tratados no DuckDB.

Não é uma etapa de transformação: recebe o resultado já tratado
(`TransformationResult`) e o grava, mantendo as tabelas de controle técnico
(idempotência por objeto, identidades carregadas para deduplicação e
checkpoints). O código de domínio permanece independente do driver: o
repositório é acessado por uma interface e pode ser trocado sem alterar o flow.

O repositório é resolvido sob demanda porque o ``__init__`` de um pacote roda
antes de qualquer submódulo: importá-lo aqui tornaria o driver do DuckDB
obrigatório até para ler ``etl.load.config``, e é a ausência dessa exigência
que permite exercitar a configuração do ambiente em quem só instala as
dependências de outra frente.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .duckdb_repository import DuckDbLoadRepository, LoadResult

__all__ = ["DuckDbLoadRepository", "LoadResult"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from . import duckdb_repository

        return getattr(duckdb_repository, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
