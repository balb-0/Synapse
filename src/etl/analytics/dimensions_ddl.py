"""DDL v1 das dimensões dos quatro cubos.

Execute ``dimension_statements()`` depois do DDL de ingestão e antes dos
fatos. A carga das dimensões será uma etapa própria: este módulo cria as
estruturas e as linhas sentinela, sem inferir atributos de fonte ausentes.
"""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from pathlib import Path

VERSION = "v1"
SQL_PATH = Path(__file__).resolve().parents[3] / "sql/duckdb/002_dimensoes.sql"


@dataclass(frozen=True)
class Dimension:
    name: str
    sk: str
    columns: tuple[str, ...]
    identity_columns: tuple[str, ...]
    required_identity: tuple[str, ...] = ()


DIMENSIONS = (
    Dimension(
        "DIM_TEMPO",
        "sk_tempo",
        (
            "data DATE",
            "ano INTEGER",
            "trimestre INTEGER",
            "mes INTEGER",
            "dia INTEGER",
            "dia_semana INTEGER",
            "fim_mes BOOLEAN",
        ),
        ("data",),
        ("data",),
    ),
    Dimension(
        "DIM_PESQUISA",
        "sk_pesquisa",
        (
            "pesquisa_id VARCHAR",
            "titulo VARCHAR",
            "objetivos VARCHAR",
        ),
        ("pesquisa_id",),
        ("pesquisa_id",),
    ),
    Dimension(
        "DIM_STATUS_PESQUISA",
        "sk_status",
        (
            "status VARCHAR",
            "flag_em_aberto BOOLEAN",
            "flag_conta_como_a_finalizar BOOLEAN",
            "flag_terminal BOOLEAN",
        ),
        ("status",),
        ("status",),
    ),
    Dimension("DIM_AREA", "sk_area", ("area VARCHAR",), ("area",), ("area",)),
    Dimension("DIM_TIPO_PESQUISA", "sk_tipo", ("tipo VARCHAR",), ("tipo",), ("tipo",)),
    Dimension(
        "DIM_PERFIL_PESQUISA",
        "sk_perfil",
        (
            "complexidade VARCHAR",
            "tipo_resposta VARCHAR",
        ),
        ("complexidade", "tipo_resposta"),
        (),
    ),
    Dimension(
        "DIM_EMPRESA",
        "sk_empresa",
        (
            "empresa_id VARCHAR",
            "nome_fantasia VARCHAR",
            "part_mercado DECIMAL(18, 6)",
            "nacionalidade VARCHAR",
            "associado BOOLEAN",
            "tipo_associado VARCHAR",
            "cidade VARCHAR",
            "estado VARCHAR",
            "pais VARCHAR",
        ),
        ("empresa_id",),
        ("empresa_id",),
    ),
    Dimension(
        "DIM_PESSOA",
        "sk_pessoa",
        (
            "cliente_id VARCHAR",
            "empresa_id VARCHAR",
            "cargo VARCHAR",
            "departamento VARCHAR",
            "nivel_hierarquico VARCHAR",
            "agrupamento_departamento VARCHAR",
        ),
        ("cliente_id",),
        ("cliente_id",),
    ),
    Dimension(
        "DIM_PERGUNTA",
        "sk_pergunta",
        (
            "pesquisa_id VARCHAR",
            "pergunta_id VARCHAR",
            "enunciado VARCHAR",
            "tipo VARCHAR",
            "qtd_alternativas BIGINT",
            "alternativas VARCHAR",
            "linhas_matriz VARCHAR",
            "colunas_matriz VARCHAR",
            "confianca VARCHAR",
            "formato_arquivo VARCHAR",
            "col_origem VARCHAR",
            "observacoes VARCHAR",
        ),
        ("pesquisa_id", "pergunta_id"),
        ("pesquisa_id", "pergunta_id"),
    ),
    Dimension(
        "DIM_FAMILIA_PESQUISA",
        "sk_familia",
        (
            "titulo_normalizado VARCHAR",
            "estado_homologacao VARCHAR",
        ),
        ("titulo_normalizado",),
        ("titulo_normalizado",),
    ),
    Dimension("DIM_FONTE_DADO", "sk_fonte", ("source VARCHAR",), ("source",), ("source",)),
    Dimension(
        "DIM_EXECUCAO_CARGA",
        "sk_carga",
        (
            "source VARCHAR",
            "run_id VARCHAR",
            "concluded_at TIMESTAMP",
            "source_checksum VARCHAR",
        ),
        ("source", "run_id"),
        ("source", "run_id"),
    ),
)


def canonical_key(*parts: str | None) -> str:
    """Codificação sem ambiguidades, inclusive para NULL e separadores no texto.

    O comprimento usa caracteres Unicode (``length`` no DuckDB), não bytes.
    Partes de IDs devem vir normalizadas pelo schema da transformação; categorias
    devem ser normalizadas pela carga antes de chamar esta função.
    """
    if not parts:
        raise ValueError("a chave natural precisa de ao menos uma parte")
    if any(part is not None and not isinstance(part, str) for part in parts):
        raise TypeError("partes da chave natural devem ser strings ou None")
    return "".join("-1:" if part is None else f"{len(part)}:{part}" for part in parts)


def surrogate_key(namespace: str, *parts: str | None) -> str:
    """SHA-256 v1 com domínio por dimensão e identidade natural canônica."""
    if namespace not in {dim.name for dim in DIMENSIONS}:
        raise ValueError(f"dimensão desconhecida: {namespace}")
    material = f"{VERSION}|{namespace}|K|{canonical_key(*parts)}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def unknown_key(namespace: str) -> str:
    """Chave reservada para vínculo órfão, sem inventar entidade de origem."""
    if namespace not in {dim.name for dim in DIMENSIONS}:
        raise ValueError(f"dimensão desconhecida: {namespace}")
    return hashlib.sha256(f"{VERSION}|{namespace}|U".encode("utf-8")).hexdigest()


def _identity_sql(dim: Dimension) -> str:
    """Reproduz canonical_key com os atributos gravados na própria dimensão."""
    parts = []
    for column in dim.identity_columns:
        value = f'CAST("{column}" AS VARCHAR)'
        parts.append(
            f"(CASE WHEN \"{column}\" IS NULL THEN '-1:' "
            f"ELSE CAST(length({value}) AS VARCHAR) || ':' || {value} END)"
        )
    return " || ".join(parts)


def dimension_statements() -> tuple[str, ...]:
    statements = []
    for dim in DIMENSIONS:
        unknown = unknown_key(dim.name)
        definitions = [
            f'    "{dim.sk}" VARCHAR PRIMARY KEY',
            '    "natural_key" VARCHAR UNIQUE',
            '    "is_unknown" BOOLEAN NOT NULL DEFAULT FALSE',
            *(
                f'    "{column.split(" ", 1)[0]}" {column.split(" ", 1)[1]}'
                for column in dim.columns
            ),
            f'    CHECK ("is_unknown" = ("{dim.sk}" = \'{unknown}\'))',
            '    CHECK ("is_unknown" = ("natural_key" IS NULL))',
            f'    CHECK ("is_unknown" OR "{dim.sk}" = sha256(\'{VERSION}|{dim.name}|K|\' || "natural_key"))',
            f'    CHECK ("is_unknown" OR "natural_key" = ({_identity_sql(dim)}))',
        ]
        for column in dim.required_identity:
            definitions.append(f'    CHECK ("is_unknown" OR "{column}" IS NOT NULL)')
        for column in dim.identity_columns:
            definitions.append(f'    CHECK (NOT "is_unknown" OR "{column}" IS NULL)')
        if dim.name == "DIM_PERFIL_PESQUISA":
            definitions.append(
                '    CHECK ("is_unknown" = ("complexidade" IS NULL AND "tipo_resposta" IS NULL))'
            )
        if dim.name == "DIM_TEMPO":
            calendar = (
                ("ano", 'year("data")'),
                ("trimestre", 'quarter("data")'),
                ("mes", 'month("data")'),
                ("dia", 'day("data")'),
                ("dia_semana", 'isodow("data")'),
                ("fim_mes", '"data" = last_day("data")'),
            )
            for column, derived in calendar:
                definitions.append(
                    f'    CHECK ("is_unknown" OR '
                    f'("{column}" IS NOT NULL AND "{column}" = ({derived})))'
                )
                definitions.append(f'    CHECK (NOT "is_unknown" OR "{column}" IS NULL)')
        if dim.identity_columns:
            quoted = ", ".join(f'"{column}"' for column in dim.identity_columns)
            definitions.append(f"    UNIQUE ({quoted})")
        statements.append(
            f'CREATE TABLE IF NOT EXISTS "{dim.name}" (\n' + ",\n".join(definitions) + "\n)"
        )
        statements.append(
            f'INSERT INTO "{dim.name}" ("{dim.sk}", "natural_key", "is_unknown") '
            f"VALUES ('{unknown}', NULL, TRUE) ON CONFLICT (\"{dim.sk}\") DO NOTHING"
        )
    return tuple(statements)


def render_ddl() -> str:
    header = (
        "-- Dimensoes analiticas v1. Gerado de src/etl/analytics/dimensions_ddl.py.\n"
        "-- Confira com PYTHONPATH=src python -m etl.analytics.dimensions_ddl --check.\n"
        "-- O banco confere natural_key contra a identidade e recalcula o SHA-256.\n"
        "-- is_unknown reserva uma linha por dimensao para vinculos orfaos.\n\n"
    )
    return header + ";\n\n".join(dimension_statements()) + ";\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    document = render_ddl()
    if args.check:
        if not SQL_PATH.exists() or SQL_PATH.read_text(encoding="utf-8") != document:
            parser.exit(1, f"DDL_DESATUALIZADA: {SQL_PATH}\n")
    else:
        SQL_PATH.parent.mkdir(parents=True, exist_ok=True)
        SQL_PATH.write_text(document, encoding="utf-8")


if __name__ == "__main__":
    main()
