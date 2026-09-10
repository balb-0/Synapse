"""Contrato canônico explícito, independente do extrator e do driver de carga."""

from dataclasses import dataclass

SCHEMA_VERSION = "1.0"

TECHNICAL_COLUMNS = {
    "source": "String",
    "run_id": "String",
    "task_id": "String",
    "batch_id": "String",
    "source_checksum": "FixedString(64)",
    "source_offset": "UInt64",
    "content_checksum": "FixedString(64)",
    "record_identity": "FixedString(64)",
    "idempotency_key": "FixedString(64)",
    "ingested_at": "DateTime64(6, 'UTC')",
    "schema_version": "String",
}


def destination_columns(source):
    return {**{f.name: f.clickhouse_type for f in SCHEMAS[source]}, **TECHNICAL_COLUMNS}


@dataclass(frozen=True)
class Field:
    origin: str
    name: str
    kind: str = "text"
    required: bool = False
    sentinels: tuple[str, ...] = ()

    @property
    def clickhouse_type(self) -> str:
        base = {
            "text": "String",
            "id": "String",
            "integer": "Int64",
            "decimal": "Decimal(18, 6)",
            "percent": "Decimal(18, 6)",
            "date": "Date32",
            "datetime": "DateTime64(6, 'UTC')",
            "boolean": "Bool",
            "list": "Array(String)",
        }[self.kind]
        # Nullable(Array) is not a ClickHouse type: absent lists become [].
        return base if self.required or self.kind == "list" else f"Nullable({base})"


def field(origin, name=None, kind="text", required=False, sentinels=()):
    return Field(origin, name or origin, kind, required, sentinels)


SCHEMAS = {
    "pesquisas": (
        field("id", "pesquisa_id", "id", True),
        field("titulo"),
        field("status"),
        field("tipo"),
        field("area"),
        field("participantes", kind="integer"),
        field("part_mercado", kind="percent"),
        *(
            field(name, kind="date")
            for name in (
                "data_solicitacao",
                "data_aprov",
                "data_divulgacao",
                "data_limite",
                "prorrogada_ate",
                "data_entrega",
            )
        ),
        field("dias_uteis_para_entrega", kind="integer"),
        field("complexidade"),
        field("tipo de resposta", "tipo_resposta"),
        field("tempo_preenchimento", kind="decimal"),
        field("objetivos"),
        field("dia da semana de lançamento", "dia_semana_lancamento"),
        field("dias úteis aberta", "dias_uteis_aberta", "integer"),
        field("dias entre a solicitação e a divulgação", "dias_solicitacao_divulgacao", "integer"),
        field("dias para tabulação", "dias_tabulacao", "integer"),
    ),
    "empresas": (
        field("ID", "empresa_id", "id", True),
        field("Nome Fantasia", "nome_fantasia"),
        field("% de mercado", "part_mercado", "percent"),
        field("Nacionalidade", "nacionalidade"),
        field("Associado", "associado", "boolean", sentinels=("-",)),
        field("Tipo de Associado", "tipo_associado"),
        field("Cidade", "cidade"),
        field("Estado", "estado"),
        field("País", "pais"),
    ),
    "clientes": (
        field("id_cliente", "cliente_id", "id", True, ("s/i",)),
        field("id_empresa", "empresa_id", "id", True),
        field("cargo"),
        field("departamento"),
        field("e-mail", "email"),
    ),
    "respondentes": (
        field("id_pesq", "pesquisa_id", "id", True),
        field("hora_inicio", kind="datetime"),
        field("hora_termino", kind="datetime"),
        field("id_empresa", "empresa_id", "id", True),
        field("market_share", kind="percent", sentinels=("na", "n/a")),
        field("id_cliente", "cliente_id", "id", sentinels=("s/i",)),
    ),
    "questoes": (
        field("id_pergunta", "pergunta_id", "id", True),
        field("pesquisa_id", kind="id", required=True),
        field("pesquisa_titulo"),
        field("enunciado"),
        field("tipo", required=True),
        field("qtd_alternativas", kind="integer"),
        field("alternativas", kind="list"),
        field("linhas_matriz", kind="list"),
        field("colunas_matriz", kind="list"),
        field("confianca"),
        field("formato_arquivo"),
        field("col_origem"),
        field("observacoes"),
    ),
    "respostas": (
        field("id_resposta", "resposta_id", "id", True),
        field("pesquisa_id", kind="id", required=True),
        field("id_pergunta", "pergunta_id", "id", True),
        field("respondent_id", kind="id", required=True),
        field("id_empresa", "empresa_id", "id"),
        field("alternativa"),
        field("linha_matriz"),
        field("coluna_matriz"),
        field("valor", sentinels=("na", "n/a")),
    ),
}

KEYS = {
    "pesquisas": ("pesquisa_id",),
    "empresas": ("empresa_id",),
    "clientes": ("cliente_id",),
    "questoes": ("pesquisa_id", "pergunta_id"),
    "respostas": ("pesquisa_id", "resposta_id"),
}

QUESTION_TYPES = frozenset(
    ("multipla_escolha", "caixas_de_selecao", "matriz_avaliacao", "numerica", "aberta")
)
