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

Além das tabelas de ingestão, o módulo declara as estruturas de controle da
carga: o registro por lote (status e contagens), a rejeição e seus motivos, e
as views que agregam a execução e provam a equação de contagem. Agregado é
view, não tabela: assim não existe um segundo escritor capaz de divergir do
que a carga gravou lote a lote.

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

# Status de um lote de carga. `falha` não é derivável das contagens — um lote
# revertido grava zero em todas elas, igual a um lote vazio bem-sucedido — por
# isso o status é gravado, não calculado.
BATCH_STATUS_LOADED = "carregado"
BATCH_STATUS_LOADED_WITH_REJECTIONS = "carregado_com_rejeicoes"
BATCH_STATUS_FAILED = "falha"

# Agregados por execução. São views: não existe segundo escritor, e o total
# não pode divergir do que a carga gravou lote a lote.
EXECUTION_VIEW = "execucao"
RECONCILIATION_VIEW = "reconciliacao_execucao"

REJECTED_TABLE = "rejected"
REJECTED_REASON_TABLE = "rejected_reason"
BATCH_METADATA_TABLE = "_batch_metadata"

# Colunas das tabelas que a carga escreve, na ordem do DDL. O insert é nomeado
# a partir destas tuplas: acrescentar coluna aqui não desloca valor de um
# insert posicional em silêncio.
REJECTED_COLUMNS = (
    "rejection_id",
    "source",
    "source_checksum",
    "source_offset",
    "run_id",
    "batch_id",
    "ingested_at",
)

REJECTED_REASON_COLUMNS = ("rejection_id", "code", "field")

BATCH_METADATA_COLUMNS = (
    "source",
    "run_id",
    "task_id",
    "batch_id",
    "status",
    "record_count",
    "accepted_count",
    "rejected_count",
    "duplicated_count",
    "byte_count",
    "schema_version",
    "source_checksum",
    "started_at",
    "finished_at",
)

# Tabelas de controle técnico da carga: execução (por lote), rejeição e o
# motivo de cada rejeição. Rejeitado é gravado à parte do aceito — nenhuma
# tabela de ingestão carrega motivo.
CONTROL_STATEMENTS = (
    # `rejection_id` identifica a ocorrência mais o conjunto de motivos e já é
    # calculado pela quarentena da transformação (`RejectedRecord`). Ele não
    # carrega a execução: a chave inclui o lote para que a rejeição vista por
    # duas execuções não colapse numa linha só — senão a listagem de rejeições
    # de uma execução passada mudaria a cada reprocessamento. É a mesma chave
    # do ledger durável em `QuarantineStore`.
    'CREATE TABLE IF NOT EXISTS "rejected" (\n'
    "    rejection_id VARCHAR NOT NULL,\n"
    "    source VARCHAR NOT NULL,\n"
    "    source_checksum VARCHAR,\n"
    "    source_offset UBIGINT NOT NULL,\n"
    "    run_id VARCHAR NOT NULL,\n"
    "    batch_id VARCHAR NOT NULL,\n"
    "    ingested_at TIMESTAMP NOT NULL,\n"
    "    PRIMARY KEY (rejection_id, run_id, batch_id)\n"
    ")",
    # Um motivo por linha, em vez de uma lista JSON opaca: contar rejeição por
    # código ou por campo passa a ser consulta, não leitura de documento. A
    # execução fica fora da chave de propósito: `rejection_id` já determina o
    # conjunto de motivos, então repetir a rejeição não repete os motivos.
    'CREATE TABLE IF NOT EXISTS "rejected_reason" (\n'
    "    rejection_id VARCHAR NOT NULL,\n"
    "    code VARCHAR NOT NULL,\n"
    "    field VARCHAR NOT NULL,\n"
    "    PRIMARY KEY (rejection_id, code, field)\n"
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
    # `batch_id` é sequencial por fonte (`pesquisas-000001`) e repete em toda
    # execução: a identidade do lote é o par com a execução que o produziu.
    'CREATE TABLE IF NOT EXISTS "_batch_metadata" (\n'
    "    source VARCHAR NOT NULL,\n"
    "    run_id VARCHAR NOT NULL,\n"
    "    task_id VARCHAR NOT NULL,\n"
    "    batch_id VARCHAR NOT NULL,\n"
    "    status VARCHAR NOT NULL,\n"
    "    record_count BIGINT NOT NULL,\n"
    "    accepted_count BIGINT NOT NULL,\n"
    "    rejected_count BIGINT NOT NULL,\n"
    "    duplicated_count BIGINT NOT NULL,\n"
    "    byte_count BIGINT NOT NULL,\n"
    "    schema_version VARCHAR NOT NULL,\n"
    "    source_checksum VARCHAR,\n"
    "    started_at TIMESTAMP NOT NULL,\n"
    "    finished_at TIMESTAMP NOT NULL,\n"
    "    PRIMARY KEY (run_id, batch_id)\n"
    ")",
)


# Colunas que as tabelas de controle ganharam nesta versão. Um banco criado
# antes dela mantém a tabela antiga, porque `CREATE TABLE IF NOT EXISTS` não
# altera o que já existe: sem alinhar, as views de execução não conseguem nem
# ser criadas, e a carga falha ao nomear uma coluna ausente. Acrescentar coluna
# é reversível e não reescreve linha; refazer chave primária exige reconstruir
# a tabela, que é assunto da rotina de migração.
CONTROL_COLUMNS_ADDED = (
    ("_batch_metadata", "status", "VARCHAR"),
    ("_batch_metadata", "accepted_count", "BIGINT DEFAULT 0"),
    ("_batch_metadata", "rejected_count", "BIGINT DEFAULT 0"),
    ("_batch_metadata", "duplicated_count", "BIGINT DEFAULT 0"),
    ("rejected", "rejection_id", "VARCHAR"),
)

# Colunas que deixaram de ser preenchidas: o motivo saiu do JSON para
# `rejected_reason`. A obrigatoriedade tem de cair, senão a carga é recusada
# por uma coluna que ninguém mais escreve.
CONTROL_COLUMNS_RELAXED = (("rejected", "reasons"),)


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


def create_execution_view() -> str:
    """Estado e contagens de cada execução, agregados dos lotes gravados.

    Uma execução falha se qualquer lote seu falhou: um lote perdido não é
    compensado pelos que deram certo.
    """

    return (
        f"CREATE OR REPLACE VIEW {quote(EXECUTION_VIEW)} AS\n"
        "SELECT\n"
        "    run_id,\n"
        "    string_agg(DISTINCT source, ', ' ORDER BY source) AS fontes,\n"
        "    CASE\n"
        f"        WHEN count(*) FILTER (WHERE status = '{BATCH_STATUS_FAILED}') > 0\n"
        f"            THEN '{BATCH_STATUS_FAILED}'\n"
        f"        WHEN sum(rejected_count) > 0 THEN '{BATCH_STATUS_LOADED_WITH_REJECTIONS}'\n"
        f"        ELSE '{BATCH_STATUS_LOADED}'\n"
        "    END AS status,\n"
        "    count(*) AS lotes,\n"
        "    sum(record_count) AS extraidos,\n"
        "    sum(accepted_count) AS carregados,\n"
        "    sum(rejected_count) AS rejeitados,\n"
        "    sum(duplicated_count) AS duplicados,\n"
        "    sum(byte_count) AS bytes,\n"
        "    min(started_at) AS iniciado_em,\n"
        "    max(finished_at) AS concluido_em\n"
        'FROM "_batch_metadata"\n'
        "GROUP BY run_id"
    )


def create_reconciliation_view() -> str:
    """A equação de contagem por execução, e o confronto das duas gravações.

    `extraidos - contabilizados` acusa o lote perdido: o lote revertido grava
    zero nas contagens e a diferença sobra. Já `rejeitados` contra
    `rejeitados_registrados` confronta dois caminhos de gravação distintos — o
    contador do lote, gravado uma vez, contra a lista de rejeições, gravada uma
    linha por ocorrência. Uma execução só está conciliada se as duas fecharem.
    """

    accounted = "carregados + rejeitados + duplicados"
    registered = "coalesce(registro.rejeitados_registrados, 0)"
    return (
        f"CREATE OR REPLACE VIEW {quote(RECONCILIATION_VIEW)} AS\n"
        "SELECT\n"
        "    execucao.run_id,\n"
        "    execucao.fontes,\n"
        "    execucao.status,\n"
        "    execucao.lotes,\n"
        "    extraidos,\n"
        "    carregados,\n"
        "    rejeitados,\n"
        "    duplicados,\n"
        f"    {registered} AS rejeitados_registrados,\n"
        f"    {accounted} AS contabilizados,\n"
        f"    extraidos - ({accounted}) AS diferenca,\n"
        f"    extraidos = ({accounted}) AND rejeitados = {registered} AS conciliado\n"
        f"FROM {quote(EXECUTION_VIEW)} AS execucao\n"
        "LEFT JOIN (\n"
        "    SELECT run_id, count(*) AS rejeitados_registrados\n"
        f"    FROM {quote(REJECTED_TABLE)}\n"
        "    GROUP BY run_id\n"
        ") AS registro ON registro.run_id = execucao.run_id"
    )


def create_legacy_view(source: str) -> str:
    """View de compatibilidade com o nome que a tabela tinha antes do prefixo.

    Transitória: existe para que leitores escritos antes do prefixo continuem
    funcionando sem alteração. ``IF NOT EXISTS`` mantém o comando seguro em
    banco antigo, onde o nome ainda pertence a uma tabela. A remoção depende
    de nenhum leitor usar mais o nome sem prefixo; ver a ADR 0002.
    """

    return (
        f"CREATE VIEW IF NOT EXISTS {quote(source)} AS\nSELECT * FROM {quote(table_name(source))}"
    )


def table_statements() -> tuple[str, ...]:
    """Tabelas: uma de ingestão por fonte, mais as de controle da carga."""

    return (*[create_table(source) for source in SCHEMAS], *CONTROL_STATEMENTS)


def view_statements() -> tuple[str, ...]:
    """Views, que só podem ser criadas depois das tabelas que elas leem."""

    current = [view for view in (create_current_view(source) for source in SCHEMAS) if view]
    legacy = [create_legacy_view(source) for source in SCHEMAS]
    return (*current, *legacy, create_execution_view(), create_reconciliation_view())


def statements() -> tuple[str, ...]:
    """Todos os comandos do contrato, na ordem de aplicação."""

    return (*table_statements(), *view_statements())


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
        "--\n"
        "-- A carga registra cada lote em `_batch_metadata` com status e as três\n"
        "-- contagens, e cada rejeição em `rejected` com um motivo por linha em\n"
        "-- `rejected_reason`. As views `execucao` e `reconciliacao_execucao`\n"
        "-- agregam por execução e provam a equação de contagem.\n"
    )
    body = ";\n\n".join(statements())
    return f"{header}\n{body};\n"
