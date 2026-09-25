-- Fatos C01 e C02 v1. Gerado de src/etl/analytics/facts_cycle_participation.py.
-- Confira com PYTHONPATH=src python -m etl.analytics.facts_cycle_participation --check.
-- Executar apos 002_dimensoes.sql. C01: uma linha corrente por pesquisa_id
-- via sk_pesquisa; origem ingestao_pesquisas_atual. Datas opcionais
-- correspondem, na ordem, a data_solicitacao, data_aprov,
-- data_divulgacao, data_limite, prorrogada_ate e data_entrega.
-- C02: uma linha por ocorrencia do snapshot conciliado de
-- ingestao_respondentes; identidade (source_checksum, source_offset).
-- sk_data_pesquisa e sk_data_resposta sao papeis opcionais.
-- NULL nas duracoes e contagens significa medida indisponivel.

CREATE TABLE IF NOT EXISTS "FATO_CICLO_PESQUISA" (
    "sk_pesquisa" VARCHAR PRIMARY KEY REFERENCES "DIM_PESQUISA" ("sk_pesquisa"),
    "sk_data_solicitacao" VARCHAR REFERENCES "DIM_TEMPO" ("sk_tempo"),
    "sk_data_aprovacao" VARCHAR REFERENCES "DIM_TEMPO" ("sk_tempo"),
    "sk_data_divulgacao" VARCHAR REFERENCES "DIM_TEMPO" ("sk_tempo"),
    "sk_data_limite_coleta" VARCHAR REFERENCES "DIM_TEMPO" ("sk_tempo"),
    "sk_data_prorrogacao" VARCHAR REFERENCES "DIM_TEMPO" ("sk_tempo"),
    "sk_data_entrega" VARCHAR REFERENCES "DIM_TEMPO" ("sk_tempo"),
    "sk_area" VARCHAR REFERENCES "DIM_AREA" ("sk_area"),
    "sk_status" VARCHAR REFERENCES "DIM_STATUS_PESQUISA" ("sk_status"),
    "sk_tipo" VARCHAR REFERENCES "DIM_TIPO_PESQUISA" ("sk_tipo"),
    "sk_perfil" VARCHAR REFERENCES "DIM_PERFIL_PESQUISA" ("sk_perfil"),
    "sk_familia" VARCHAR REFERENCES "DIM_FAMILIA_PESQUISA" ("sk_familia"),
    "sk_fonte" VARCHAR NOT NULL REFERENCES "DIM_FONTE_DADO" ("sk_fonte"),
    "sk_carga" VARCHAR NOT NULL REFERENCES "DIM_EXECUCAO_CARGA" ("sk_carga"),
    "dias_corridos_validacao" BIGINT,
    "dias_corridos_coleta" BIGINT,
    "dias_corridos_tabulacao" BIGINT,
    "dias_corridos_ciclo_total" BIGINT,
    "qtd_empresas_na_pesquisa" BIGINT,
    "flag_prorrogada" BOOLEAN NOT NULL,
    CHECK ("flag_prorrogada" = ("sk_data_prorrogacao" IS NOT NULL)),
    CHECK ("dias_corridos_validacao" IS NULL OR "dias_corridos_validacao" >= 0),
    CHECK ("dias_corridos_coleta" IS NULL OR "dias_corridos_coleta" >= 0),
    CHECK ("dias_corridos_tabulacao" IS NULL OR "dias_corridos_tabulacao" >= 0),
    CHECK ("dias_corridos_ciclo_total" IS NULL OR "dias_corridos_ciclo_total" >= 0),
    CHECK ("qtd_empresas_na_pesquisa" IS NULL OR "qtd_empresas_na_pesquisa" >= 0)
);

CREATE TABLE IF NOT EXISTS "FATO_PARTICIPACAO" (
    "source_checksum" VARCHAR NOT NULL,
    "source_offset" UBIGINT NOT NULL,
    "sk_pesquisa" VARCHAR NOT NULL REFERENCES "DIM_PESQUISA" ("sk_pesquisa"),
    "sk_empresa" VARCHAR NOT NULL REFERENCES "DIM_EMPRESA" ("sk_empresa"),
    "sk_pessoa" VARCHAR REFERENCES "DIM_PESSOA" ("sk_pessoa"),
    "sk_data_pesquisa" VARCHAR REFERENCES "DIM_TEMPO" ("sk_tempo"),
    "sk_data_resposta" VARCHAR REFERENCES "DIM_TEMPO" ("sk_tempo"),
    "qtd_participacao" INTEGER NOT NULL DEFAULT 1,
    "seq_ocorrencia" BIGINT,
    "minutos_preenchimento" BIGINT,
    "motivo_minutos_indisponivel" VARCHAR,
    "pct_mercado_na_participacao" DECIMAL(18, 6),
    PRIMARY KEY ("source_checksum", "source_offset"),
    UNIQUE ("sk_pesquisa", "sk_pessoa", "seq_ocorrencia"),
    CHECK (length("source_checksum") > 0),
    CHECK ("qtd_participacao" = 1),
    CHECK ("seq_ocorrencia" IS NULL OR "seq_ocorrencia" > 0),
    CHECK ("minutos_preenchimento" IS NULL OR "minutos_preenchimento" >= 0),
    CHECK (("minutos_preenchimento" IS NULL) = ("motivo_minutos_indisponivel" IS NOT NULL)),
    CHECK ("motivo_minutos_indisponivel" IS NULL OR length("motivo_minutos_indisponivel") > 0),
    CHECK ("sk_pessoa" IS NOT NULL OR "seq_ocorrencia" IS NULL),
    CHECK ("pct_mercado_na_participacao" IS NULL OR
           "pct_mercado_na_participacao" BETWEEN 0 AND 100)
);
