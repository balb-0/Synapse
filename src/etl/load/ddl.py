"""Contrato físico das tabelas de ingestão tratada no DuckDB.

Este módulo é a fonte única do DDL da camada de carga. Ele acrescenta ao
contrato canônico da transformação o que só existe no banco de destino: nome
físico da tabela, tradução de tipo para o DuckDB, constraints e as views de
estado atual.

Uma linha da tabela de ingestão corresponde a uma linha da fonte, e o mesmo
registro pode aparecer em mais de uma linha quando o parceiro reexporta o
arquivo com conteúdo corrigido. Por isso a chave primária é a identidade de
idempotência (chave de negócio + conteúdo) e não a chave de negócio: a
correção convive com a versão anterior, e cada linha carrega a proveniência
que permite reconstruir o estado em qualquer momento.

O arquivo versionado em ``sql/duckdb/`` é a forma revisável deste mesmo
contrato; ``scripts/load/render_ddl.py --check`` impede que os dois divirjam.
"""

from __future__ import annotations

import re

from etl.transformation.schema import KEYS, SCHEMAS, destination_columns


TABLE_PREFIX = "ingestao_"
CURRENT_VIEW_SUFFIX = "_atual"

# Identidade de idempotência: chave de negócio combinada ao conteúdo. É a
# unidade de uma linha da tabela de ingestão.
IDENTITY_COLUMN = "idempotency_key"

# Participação não tem chave natural confirmada: a identidade é a ocorrência
# física na fonte. Registrado no inventário de contratos dimensionais.
POSITIONAL_KEY = ("source_checksum", "source_offset")

# Colunas técnicas que o contrato de lote garante preenchidas.
# ``source_checksum`` fica de fora porque o adaptador local de
# desenvolvimento pode não informá-lo.
TECHNICAL_NOT_NULL = (
    "source",
    "run_id",
    "task_id",
    "batch_id",
    "source_offset",
    "content_checksum",
    "record_identity",
    "idempotency_key",
    "ingested_at",
    "schema_version",
)

_BASE_TYPES = {
    "String": "VARCHAR",
    "Int64": "BIGINT",
    "UInt64": "UBIGINT",
    "Bool": "BOOLEAN",
    "Date32": "DATE",
}

# Tabelas de controle técnico. Mantidas como a carga já as usa; a formalização
# de execução, rejeição e reconciliação pertence à etapa seguinte.
CONTROL_STATEMENTS = (
    'CREATE TABLE IF NOT EXISTS "rejected" (\n'
    "    source VARCHAR NOT NULL,\n"
    "    source_checksum VARCHAR,\n"
    "    source_offset UBIGINT NOT NULL,\n"
    "    run_id VARCHAR NOT NULL,\n"
    "    batch_id VARCHAR NOT NULL,\n"
    "    ingested_at TIMESTAMP NOT NULL,\n"
    "    reasons VARCHAR NOT NULL\n"
    ")",
    'CREATE TABLE IF NOT EXISTS "_control_object" (\n'
    "    source VARCHAR NOT NULL,\n"
    "    source_checksum VARCHAR PRIMARY KEY,\n"
    "    run_id VARCHAR NOT NULL,\n"
    "    concluded_at TIMESTAMP NOT NULL\n"
    ")",
    'CREATE TABLE IF NOT EXISTS "_loaded_identity" (\n'
    "    source VARCHAR NOT NULL,\n"
    "    record_identity VARCHAR PRIMARY KEY,\n"
    "    content_checksum VARCHAR NOT NULL\n"
    ")",
    'CREATE TABLE IF NOT EXISTS "_checkpoint" (\n'
    "    source VARCHAR PRIMARY KEY,\n"
    "    position VARCHAR,\n"
    "    sequence BIGINT,\n"
    "    source_version VARCHAR\n"
    ")",
    'CREATE TABLE IF NOT EXISTS "_batch_metadata" (\n'
    "    source VARCHAR NOT NULL,\n"
    "    run_id VARCHAR NOT NULL,\n"
    "    task_id VARCHAR NOT NULL,\n"
    "    batch_id VARCHAR NOT NULL,\n"
    "    record_count BIGINT NOT NULL,\n"
    "    byte_count BIGINT NOT NULL,\n"
    "    schema_version VARCHAR NOT NULL,\n"
    "    source_checksum VARCHAR,\n"
    "    started_at TIMESTAMP NOT NULL,\n"
    "    finished_at TIMESTAMP NOT NULL\n"
    ")",
)


def quote(identifier: str) -> str:
    """Cita um identificador conhecido, recusando qualquer coisa inesperada."""

    if not re.fullmatch(r"[A-Za-z0-9_]+", identifier):
        raise ValueError(f"identificador inválido: {identifier!r}")
    return f'"{identifier}"'


def duckdb_type(canonical_type: str) -> str:
    """Traduz o tipo declarado pelo contrato da transformação para o DuckDB.

    O contrato nomeia os tipos na convenção do ClickHouse, destino anterior à
    ADR 0001. A tradução acontece aqui, uma vez, em vez de em cada consulta.
    """

    inner = canonical_type
    if inner.startswith("Nullable(") and inner.endswith(")"):
        inner = inner[len("Nullable(") : -1]
    if inner.startswith("FixedString"):
        return "VARCHAR"
    if inner.startswith("Decimal"):
        return "DECIMAL(18, 6)"
    if inner.startswith("DateTime64"):
        return "TIMESTAMP"
    if inner.startswith("Array"):
        return "VARCHAR"  # lista serializada como JSON
    return _BASE_TYPES.get(inner, "VARCHAR")


def table_name(source: str) -> str:
    """Nome físico da tabela de ingestão da fonte."""

    return f"{TABLE_PREFIX}{source}"


def current_view_name(source: str) -> str:
    """Nome da view de estado atual da fonte."""

    return f"{table_name(source)}{CURRENT_VIEW_SUFFIX}"


def business_key(source: str) -> tuple[str, ...]:
    """Chave de negócio da fonte, ou a ocorrência física quando não há uma."""

    return KEYS.get(source, POSITIONAL_KEY)


def has_business_key(source: str) -> bool:
    """A fonte tem chave de negócio declarada no contrato?"""

    return source in KEYS


def required_columns(source: str) -> tuple[str, ...]:
    """Campos que o contrato da transformação recusa quando ausentes."""

    return tuple(field.name for field in SCHEMAS[source] if field.required)


def _column_definition(source: str, column: str, canonical_type: str) -> str:
    not_null = column in TECHNICAL_NOT_NULL or column in required_columns(source)
    suffix = " NOT NULL" if not_null else ""
    return f"    {quote(column)} {duckdb_type(canonical_type)}{suffix}"


def create_table(source: str) -> str:
    """DDL da tabela de ingestão da fonte, com tipos e constraints."""

    lines = [
        _column_definition(source, column, canonical_type)
        for column, canonical_type in destination_columns(source).items()
    ]
    lines.append(f"    PRIMARY KEY ({quote(IDENTITY_COLUMN)})")
    unique = business_key(source)
    if has_business_key(source):
        unique = (*unique, "content_checksum")
    lines.append(f"    UNIQUE ({', '.join(quote(column) for column in unique)})")
    body = ",\n".join(lines)
    return f"CREATE TABLE IF NOT EXISTS {quote(table_name(source))} (\n{body}\n)"


def create_current_view(source: str) -> str | None:
    """View com a versão mais recente de cada chave de negócio.

    Devolve ``None`` para a fonte sem chave natural: sem chave não existe
    noção de versão mais recente, e cada linha é uma ocorrência distinta.
    """

    if not has_business_key(source):
        return None
    partition = ", ".join(quote(column) for column in business_key(source))
    return (
        f"CREATE OR REPLACE VIEW {quote(current_view_name(source))} AS\n"
        "SELECT * EXCLUDE (_versao) FROM (\n"
        "    SELECT *, row_number() OVER (\n"
        f"        PARTITION BY {partition}\n"
        '        ORDER BY "ingested_at" DESC, "source_offset" DESC\n'
        "    ) AS _versao\n"
        f"    FROM {quote(table_name(source))}\n"
        ") WHERE _versao = 1"
    )


def create_legacy_view(source: str) -> str:
    """View de compatibilidade com o nome que a tabela tinha antes do prefixo.

    Transitória: existe para que leitores escritos antes do prefixo continuem
    funcionando sem alteração. ``IF NOT EXISTS`` mantém o comando seguro em
    banco antigo, onde o nome ainda pertence a uma tabela. A remoção depende
    de nenhum leitor usar mais o nome sem prefixo; ver a ADR 0002.
    """

    return (
        f"CREATE VIEW IF NOT EXISTS {quote(source)} AS\n"
        f"SELECT * FROM {quote(table_name(source))}"
    )


def statements() -> tuple[str, ...]:
    """Todos os comandos do contrato, na ordem de aplicação."""

    tables = [create_table(source) for source in SCHEMAS]
    current = [view for view in (create_current_view(source) for source in SCHEMAS) if view]
    legacy = [create_legacy_view(source) for source in SCHEMAS]
    return (*tables, *CONTROL_STATEMENTS, *current, *legacy)


def render_ddl() -> str:
    """Renderiza o arquivo versionado do contrato físico."""

    header = (
        "-- Contrato físico das tabelas de ingestão tratada no DuckDB.\n"
        "-- Gerado de src/etl/load/ddl.py; valide com\n"
        "-- `PYTHONPATH=src python scripts/load/render_ddl.py --check`.\n"
        "--\n"
        "-- Uma linha corresponde a uma linha da fonte. O mesmo registro pode\n"
        "-- aparecer em mais de uma linha quando o arquivo é reexportado com\n"
        "-- conteúdo corrigido: a chave primária é a identidade de idempotência\n"
        "-- (chave de negócio + conteúdo). As views `_atual` devolvem a versão\n"
        "-- mais recente de cada chave de negócio. As views sem prefixo são\n"
        "-- compatibilidade transitória com leitores anteriores ao prefixo.\n"
    )
    body = ";\n\n".join(statements())
    return f"{header}\n{body};\n"
