"""DDL v1 dos fatos de pipeline mensal e instrumento de pesquisa.

Execute ``fact_statements()`` depois de ``dimension_statements()``. Este
módulo cria estruturas: não reconstrói fechamentos ou transições históricas.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

VERSION = "v1"
SQL_PATH = Path(__file__).resolve().parents[3] / "sql/duckdb/004_fatos_pipeline_instrumento.sql"
UNKNOWN_PESQUISA_KEY = hashlib.sha256(f"{VERSION}|DIM_PESQUISA|U".encode("utf-8")).hexdigest()


def fact_statements() -> tuple[str, ...]:
    """Tabelas com grão e referências conformadas verificáveis no DuckDB."""
    return (
        """CREATE TABLE IF NOT EXISTS "FATO_PIPELINE_MENSAL" (
    "sk_data_fim_mes" VARCHAR NOT NULL REFERENCES "DIM_TEMPO"("sk_tempo"),
    "data_fim_mes" DATE NOT NULL,
    "observed_at" TIMESTAMP NOT NULL,
    "sk_status" VARCHAR NOT NULL REFERENCES "DIM_STATUS_PESQUISA"("sk_status"),
    "sk_area" VARCHAR NOT NULL REFERENCES "DIM_AREA"("sk_area"),
    "sk_tipo" VARCHAR NOT NULL REFERENCES "DIM_TIPO_PESQUISA"("sk_tipo"),
    "sk_perfil" VARCHAR NOT NULL REFERENCES "DIM_PERFIL_PESQUISA"("sk_perfil"),
    "qtd_pesquisas_no_status" BIGINT NOT NULL,
    "qtd_entradas_no_mes" BIGINT,
    "qtd_saidas_no_mes" BIGINT,
    PRIMARY KEY ("sk_data_fim_mes", "sk_status", "sk_area", "sk_tipo", "sk_perfil"),
    CHECK ("data_fim_mes" = last_day("data_fim_mes")),
    CHECK ("sk_data_fim_mes" = sha256('{version}|DIM_TEMPO|K|10:' || CAST("data_fim_mes" AS VARCHAR))),
    CHECK (CAST("observed_at" AS DATE) >= "data_fim_mes"),
    CHECK ("qtd_pesquisas_no_status" >= 0),
    CHECK ("qtd_entradas_no_mes" IS NULL OR "qtd_entradas_no_mes" >= 0),
    CHECK ("qtd_saidas_no_mes" IS NULL OR "qtd_saidas_no_mes" >= 0)
)""".replace("{version}", VERSION),
        """CREATE TABLE IF NOT EXISTS "FATO_PESQUISA_PERGUNTA" (
    "sk_pesquisa" VARCHAR NOT NULL REFERENCES "DIM_PESQUISA"("sk_pesquisa"),
    "sk_pergunta" VARCHAR NOT NULL REFERENCES "DIM_PERGUNTA"("sk_pergunta"),
    "sk_data_pesquisa" VARCHAR REFERENCES "DIM_TEMPO"("sk_tempo"),
    "pesquisa_id_origem" VARCHAR NOT NULL,
    "pergunta_id_origem" VARCHAR NOT NULL,
    "metodo_vinculo" VARCHAR NOT NULL,
    PRIMARY KEY ("sk_pesquisa", "sk_pergunta"),
    UNIQUE ("sk_pergunta"),
    CHECK ("sk_pergunta" = sha256('{version}|DIM_PERGUNTA|K|' ||
        CAST(length("pesquisa_id_origem") AS VARCHAR) || ':' || "pesquisa_id_origem" ||
        CAST(length("pergunta_id_origem") AS VARCHAR) || ':' || "pergunta_id_origem")),
    CHECK (
        ("metodo_vinculo" = 'id' AND "sk_pesquisa" = sha256('{version}|DIM_PESQUISA|K|' ||
            CAST(length("pesquisa_id_origem") AS VARCHAR) || ':' || "pesquisa_id_origem"))
        OR ("metodo_vinculo" = 'desconhecido' AND "sk_pesquisa" = '{unknown_pesquisa_key}')
        OR ("metodo_vinculo" = 'titulo_unico' AND "sk_pesquisa" <> '{unknown_pesquisa_key}'
            AND "sk_pesquisa" <> sha256('{version}|DIM_PESQUISA|K|' ||
                CAST(length("pesquisa_id_origem") AS VARCHAR) || ':' || "pesquisa_id_origem"))
    )
)""".replace("{version}", VERSION).replace("{unknown_pesquisa_key}", UNKNOWN_PESQUISA_KEY),
    )


def render_ddl() -> str:
    header = (
        "-- Fatos analiticos v1. Gerado de src/etl/analytics/facts_pipeline_instrument.py.\n"
        "-- Confira com PYTHONPATH=src python -m etl.analytics.facts_pipeline_instrument --check.\n"
        "-- Execute apos 002_dimensoes.sql. As chaves de dimensao sao SHA-256 VARCHAR.\n"
        "-- Pipeline: estoque semiaditivo apenas para fechamento observado; nao some meses.\n"
        "-- Entradas e saidas sem historico de transicoes permanecem NULL, nunca zero presumido.\n"
        "-- data_fim_mes corresponde a chave deterministica de DIM_TEMPO.\n"
        "-- Instrumento: SK da pergunta deriva do par de IDs de origem.\n"
        "-- Vinculo por titulo unico exige prova na carga e registro na reconciliacao.\n"
        "-- COUNT(*) deriva a quantidade de perguntas; alternativas sao da dimensao.\n\n"
    )
    return header + ";\n\n".join(fact_statements()) + ";\n"


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
