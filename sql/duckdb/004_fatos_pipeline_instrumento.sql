-- Fatos analiticos v1. Gerado de src/etl/analytics/facts_pipeline_instrument.py.
-- Confira com PYTHONPATH=src python -m etl.analytics.facts_pipeline_instrument --check.
-- Execute apos 002_dimensoes.sql. As chaves de dimensao sao SHA-256 VARCHAR.
-- Pipeline: estoque semiaditivo apenas para fechamento observado; nao some meses.
-- Entradas e saidas sem historico de transicoes permanecem NULL, nunca zero presumido.
-- data_fim_mes corresponde a chave deterministica de DIM_TEMPO.
-- Instrumento: SK da pergunta deriva do par de IDs de origem.
-- Vinculo por titulo unico exige prova na carga e registro na reconciliacao.
-- COUNT(*) deriva a quantidade de perguntas; alternativas sao da dimensao.

CREATE TABLE IF NOT EXISTS "FATO_PIPELINE_MENSAL" (
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
    CHECK ("sk_data_fim_mes" = sha256('v1|DIM_TEMPO|K|10:' || CAST("data_fim_mes" AS VARCHAR))),
    CHECK (CAST("observed_at" AS DATE) >= "data_fim_mes"),
    CHECK ("qtd_pesquisas_no_status" >= 0),
    CHECK ("qtd_entradas_no_mes" IS NULL OR "qtd_entradas_no_mes" >= 0),
    CHECK ("qtd_saidas_no_mes" IS NULL OR "qtd_saidas_no_mes" >= 0)
);

CREATE TABLE IF NOT EXISTS "FATO_PESQUISA_PERGUNTA" (
    "sk_pesquisa" VARCHAR NOT NULL REFERENCES "DIM_PESQUISA"("sk_pesquisa"),
    "sk_pergunta" VARCHAR NOT NULL REFERENCES "DIM_PERGUNTA"("sk_pergunta"),
    "sk_data_pesquisa" VARCHAR REFERENCES "DIM_TEMPO"("sk_tempo"),
    "pesquisa_id_origem" VARCHAR NOT NULL,
    "pergunta_id_origem" VARCHAR NOT NULL,
    "metodo_vinculo" VARCHAR NOT NULL,
    PRIMARY KEY ("sk_pesquisa", "sk_pergunta"),
    UNIQUE ("sk_pergunta"),
    CHECK ("sk_pergunta" = sha256('v1|DIM_PERGUNTA|K|' ||
        CAST(length("pesquisa_id_origem") AS VARCHAR) || ':' || "pesquisa_id_origem" ||
        CAST(length("pergunta_id_origem") AS VARCHAR) || ':' || "pergunta_id_origem")),
    CHECK (
        ("metodo_vinculo" = 'id' AND "sk_pesquisa" = sha256('v1|DIM_PESQUISA|K|' ||
            CAST(length("pesquisa_id_origem") AS VARCHAR) || ':' || "pesquisa_id_origem"))
        OR ("metodo_vinculo" = 'desconhecido' AND "sk_pesquisa" = '28d61d4b6a9c57493f0424e34934c028d7d3865f655bfeaf2d11a471d0ed8da3')
        OR ("metodo_vinculo" = 'titulo_unico' AND "sk_pesquisa" <> '28d61d4b6a9c57493f0424e34934c028d7d3865f655bfeaf2d11a471d0ed8da3'
            AND "sk_pesquisa" <> sha256('v1|DIM_PESQUISA|K|' ||
                CAST(length("pesquisa_id_origem") AS VARCHAR) || ':' || "pesquisa_id_origem"))
    )
);
