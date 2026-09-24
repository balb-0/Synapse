-- Dimensoes analiticas v1. Gerado de src/etl/analytics/dimensions_ddl.py.
-- Confira com PYTHONPATH=src python -m etl.analytics.dimensions_ddl --check.
-- A carga fornece natural_key via canonical_key; o banco confere o SHA-256.
-- is_unknown reserva uma linha por dimensao para vinculos orfaos.

CREATE TABLE IF NOT EXISTS "DIM_TEMPO" (
    "sk_tempo" VARCHAR PRIMARY KEY,
    "natural_key" VARCHAR UNIQUE,
    "is_unknown" BOOLEAN NOT NULL DEFAULT FALSE,
    "data" DATE,
    "ano" INTEGER,
    "trimestre" INTEGER,
    "mes" INTEGER,
    "dia" INTEGER,
    "dia_semana" INTEGER,
    "fim_mes" BOOLEAN,
    CHECK ("is_unknown" = ("sk_tempo" = 'e65c0f359f7b8950941ba138f0248eaf216f828478cbd6920055c3deac2b87b9')),
    CHECK ("is_unknown" = ("natural_key" IS NULL)),
    CHECK ("is_unknown" OR "sk_tempo" = sha256('v1|DIM_TEMPO|K|' || "natural_key")),
    CHECK ("is_unknown" OR "data" IS NOT NULL),
    CHECK (NOT "is_unknown" OR "data" IS NULL),
    CHECK ("is_unknown" OR ("ano" IS NOT NULL AND "ano" = (year("data")))),
    CHECK (NOT "is_unknown" OR "ano" IS NULL),
    CHECK ("is_unknown" OR ("trimestre" IS NOT NULL AND "trimestre" = (quarter("data")))),
    CHECK (NOT "is_unknown" OR "trimestre" IS NULL),
    CHECK ("is_unknown" OR ("mes" IS NOT NULL AND "mes" = (month("data")))),
    CHECK (NOT "is_unknown" OR "mes" IS NULL),
    CHECK ("is_unknown" OR ("dia" IS NOT NULL AND "dia" = (day("data")))),
    CHECK (NOT "is_unknown" OR "dia" IS NULL),
    CHECK ("is_unknown" OR ("dia_semana" IS NOT NULL AND "dia_semana" = (isodow("data")))),
    CHECK (NOT "is_unknown" OR "dia_semana" IS NULL),
    CHECK ("is_unknown" OR ("fim_mes" IS NOT NULL AND "fim_mes" = ("data" = last_day("data")))),
    CHECK (NOT "is_unknown" OR "fim_mes" IS NULL),
    UNIQUE ("data")
);

INSERT INTO "DIM_TEMPO" ("sk_tempo", "natural_key", "is_unknown") VALUES ('e65c0f359f7b8950941ba138f0248eaf216f828478cbd6920055c3deac2b87b9', NULL, TRUE) ON CONFLICT ("sk_tempo") DO NOTHING;

CREATE TABLE IF NOT EXISTS "DIM_PESQUISA" (
    "sk_pesquisa" VARCHAR PRIMARY KEY,
    "natural_key" VARCHAR UNIQUE,
    "is_unknown" BOOLEAN NOT NULL DEFAULT FALSE,
    "pesquisa_id" VARCHAR,
    "titulo" VARCHAR,
    "objetivos" VARCHAR,
    CHECK ("is_unknown" = ("sk_pesquisa" = '28d61d4b6a9c57493f0424e34934c028d7d3865f655bfeaf2d11a471d0ed8da3')),
    CHECK ("is_unknown" = ("natural_key" IS NULL)),
    CHECK ("is_unknown" OR "sk_pesquisa" = sha256('v1|DIM_PESQUISA|K|' || "natural_key")),
    CHECK ("is_unknown" OR "pesquisa_id" IS NOT NULL),
    CHECK (NOT "is_unknown" OR "pesquisa_id" IS NULL),
    UNIQUE ("pesquisa_id")
);

INSERT INTO "DIM_PESQUISA" ("sk_pesquisa", "natural_key", "is_unknown") VALUES ('28d61d4b6a9c57493f0424e34934c028d7d3865f655bfeaf2d11a471d0ed8da3', NULL, TRUE) ON CONFLICT ("sk_pesquisa") DO NOTHING;

CREATE TABLE IF NOT EXISTS "DIM_STATUS_PESQUISA" (
    "sk_status" VARCHAR PRIMARY KEY,
    "natural_key" VARCHAR UNIQUE,
    "is_unknown" BOOLEAN NOT NULL DEFAULT FALSE,
    "status" VARCHAR,
    "flag_em_aberto" BOOLEAN,
    "flag_conta_como_a_finalizar" BOOLEAN,
    "flag_terminal" BOOLEAN,
    CHECK ("is_unknown" = ("sk_status" = '843cdd81627069c60e170fb410d81667c4684d157b3bd09688d7d8d480505dd9')),
    CHECK ("is_unknown" = ("natural_key" IS NULL)),
    CHECK ("is_unknown" OR "sk_status" = sha256('v1|DIM_STATUS_PESQUISA|K|' || "natural_key")),
    CHECK ("is_unknown" OR "status" IS NOT NULL),
    CHECK (NOT "is_unknown" OR "status" IS NULL),
    UNIQUE ("status")
);

INSERT INTO "DIM_STATUS_PESQUISA" ("sk_status", "natural_key", "is_unknown") VALUES ('843cdd81627069c60e170fb410d81667c4684d157b3bd09688d7d8d480505dd9', NULL, TRUE) ON CONFLICT ("sk_status") DO NOTHING;

CREATE TABLE IF NOT EXISTS "DIM_AREA" (
    "sk_area" VARCHAR PRIMARY KEY,
    "natural_key" VARCHAR UNIQUE,
    "is_unknown" BOOLEAN NOT NULL DEFAULT FALSE,
    "area" VARCHAR,
    CHECK ("is_unknown" = ("sk_area" = '0c6e3d4fca3079a7d67204b539f383131b9169784c2dbe9cbcefbb571fde5ac5')),
    CHECK ("is_unknown" = ("natural_key" IS NULL)),
    CHECK ("is_unknown" OR "sk_area" = sha256('v1|DIM_AREA|K|' || "natural_key")),
    CHECK ("is_unknown" OR "area" IS NOT NULL),
    CHECK (NOT "is_unknown" OR "area" IS NULL),
    UNIQUE ("area")
);

INSERT INTO "DIM_AREA" ("sk_area", "natural_key", "is_unknown") VALUES ('0c6e3d4fca3079a7d67204b539f383131b9169784c2dbe9cbcefbb571fde5ac5', NULL, TRUE) ON CONFLICT ("sk_area") DO NOTHING;

CREATE TABLE IF NOT EXISTS "DIM_TIPO_PESQUISA" (
    "sk_tipo" VARCHAR PRIMARY KEY,
    "natural_key" VARCHAR UNIQUE,
    "is_unknown" BOOLEAN NOT NULL DEFAULT FALSE,
    "tipo" VARCHAR,
    CHECK ("is_unknown" = ("sk_tipo" = '7fd33fd52a0029d989e3fb27db2caca1ff04359d846b830e89799312344d4db6')),
    CHECK ("is_unknown" = ("natural_key" IS NULL)),
    CHECK ("is_unknown" OR "sk_tipo" = sha256('v1|DIM_TIPO_PESQUISA|K|' || "natural_key")),
    CHECK ("is_unknown" OR "tipo" IS NOT NULL),
    CHECK (NOT "is_unknown" OR "tipo" IS NULL),
    UNIQUE ("tipo")
);

INSERT INTO "DIM_TIPO_PESQUISA" ("sk_tipo", "natural_key", "is_unknown") VALUES ('7fd33fd52a0029d989e3fb27db2caca1ff04359d846b830e89799312344d4db6', NULL, TRUE) ON CONFLICT ("sk_tipo") DO NOTHING;

CREATE TABLE IF NOT EXISTS "DIM_PERFIL_PESQUISA" (
    "sk_perfil" VARCHAR PRIMARY KEY,
    "natural_key" VARCHAR UNIQUE,
    "is_unknown" BOOLEAN NOT NULL DEFAULT FALSE,
    "complexidade" VARCHAR,
    "tipo_resposta" VARCHAR,
    CHECK ("is_unknown" = ("sk_perfil" = 'e70c48afed032784d97267e356fd623530b4e7e070246778bcb993a7429eaaa9')),
    CHECK ("is_unknown" = ("natural_key" IS NULL)),
    CHECK ("is_unknown" OR "sk_perfil" = sha256('v1|DIM_PERFIL_PESQUISA|K|' || "natural_key")),
    CHECK ("is_unknown" = ("complexidade" IS NULL AND "tipo_resposta" IS NULL))
);

INSERT INTO "DIM_PERFIL_PESQUISA" ("sk_perfil", "natural_key", "is_unknown") VALUES ('e70c48afed032784d97267e356fd623530b4e7e070246778bcb993a7429eaaa9', NULL, TRUE) ON CONFLICT ("sk_perfil") DO NOTHING;

CREATE TABLE IF NOT EXISTS "DIM_EMPRESA" (
    "sk_empresa" VARCHAR PRIMARY KEY,
    "natural_key" VARCHAR UNIQUE,
    "is_unknown" BOOLEAN NOT NULL DEFAULT FALSE,
    "empresa_id" VARCHAR,
    "nome_fantasia" VARCHAR,
    "part_mercado" DECIMAL(18, 6),
    "nacionalidade" VARCHAR,
    "associado" BOOLEAN,
    "tipo_associado" VARCHAR,
    "cidade" VARCHAR,
    "estado" VARCHAR,
    "pais" VARCHAR,
    CHECK ("is_unknown" = ("sk_empresa" = '42863741238d53a0f676593060a13668a8f8ac5c8d153eaf67583049eb4813af')),
    CHECK ("is_unknown" = ("natural_key" IS NULL)),
    CHECK ("is_unknown" OR "sk_empresa" = sha256('v1|DIM_EMPRESA|K|' || "natural_key")),
    CHECK ("is_unknown" OR "empresa_id" IS NOT NULL),
    CHECK (NOT "is_unknown" OR "empresa_id" IS NULL),
    UNIQUE ("empresa_id")
);

INSERT INTO "DIM_EMPRESA" ("sk_empresa", "natural_key", "is_unknown") VALUES ('42863741238d53a0f676593060a13668a8f8ac5c8d153eaf67583049eb4813af', NULL, TRUE) ON CONFLICT ("sk_empresa") DO NOTHING;

CREATE TABLE IF NOT EXISTS "DIM_PESSOA" (
    "sk_pessoa" VARCHAR PRIMARY KEY,
    "natural_key" VARCHAR UNIQUE,
    "is_unknown" BOOLEAN NOT NULL DEFAULT FALSE,
    "cliente_id" VARCHAR,
    "empresa_id" VARCHAR,
    "cargo" VARCHAR,
    "departamento" VARCHAR,
    "nivel_hierarquico" VARCHAR,
    "agrupamento_departamento" VARCHAR,
    CHECK ("is_unknown" = ("sk_pessoa" = 'a4fdb4acc2bbec798dbb7cc016f6ae3ed04bad5d7317b4388258d5b6174ad64f')),
    CHECK ("is_unknown" = ("natural_key" IS NULL)),
    CHECK ("is_unknown" OR "sk_pessoa" = sha256('v1|DIM_PESSOA|K|' || "natural_key")),
    CHECK ("is_unknown" OR "cliente_id" IS NOT NULL),
    CHECK (NOT "is_unknown" OR "cliente_id" IS NULL),
    UNIQUE ("cliente_id")
);

INSERT INTO "DIM_PESSOA" ("sk_pessoa", "natural_key", "is_unknown") VALUES ('a4fdb4acc2bbec798dbb7cc016f6ae3ed04bad5d7317b4388258d5b6174ad64f', NULL, TRUE) ON CONFLICT ("sk_pessoa") DO NOTHING;

CREATE TABLE IF NOT EXISTS "DIM_PERGUNTA" (
    "sk_pergunta" VARCHAR PRIMARY KEY,
    "natural_key" VARCHAR UNIQUE,
    "is_unknown" BOOLEAN NOT NULL DEFAULT FALSE,
    "pesquisa_id" VARCHAR,
    "pergunta_id" VARCHAR,
    "enunciado" VARCHAR,
    "tipo" VARCHAR,
    "qtd_alternativas" BIGINT,
    "alternativas" VARCHAR,
    "linhas_matriz" VARCHAR,
    "colunas_matriz" VARCHAR,
    "confianca" VARCHAR,
    "formato_arquivo" VARCHAR,
    "col_origem" VARCHAR,
    "observacoes" VARCHAR,
    CHECK ("is_unknown" = ("sk_pergunta" = 'ee6147b1a5fef4f50dd667eaee37d5196717055722dee71c6335dc3c888a0f42')),
    CHECK ("is_unknown" = ("natural_key" IS NULL)),
    CHECK ("is_unknown" OR "sk_pergunta" = sha256('v1|DIM_PERGUNTA|K|' || "natural_key")),
    CHECK ("is_unknown" OR "pesquisa_id" IS NOT NULL),
    CHECK ("is_unknown" OR "pergunta_id" IS NOT NULL),
    CHECK (NOT "is_unknown" OR "pesquisa_id" IS NULL),
    CHECK (NOT "is_unknown" OR "pergunta_id" IS NULL),
    UNIQUE ("pesquisa_id", "pergunta_id")
);

INSERT INTO "DIM_PERGUNTA" ("sk_pergunta", "natural_key", "is_unknown") VALUES ('ee6147b1a5fef4f50dd667eaee37d5196717055722dee71c6335dc3c888a0f42', NULL, TRUE) ON CONFLICT ("sk_pergunta") DO NOTHING;

CREATE TABLE IF NOT EXISTS "DIM_FAMILIA_PESQUISA" (
    "sk_familia" VARCHAR PRIMARY KEY,
    "natural_key" VARCHAR UNIQUE,
    "is_unknown" BOOLEAN NOT NULL DEFAULT FALSE,
    "titulo_normalizado" VARCHAR,
    "estado_homologacao" VARCHAR,
    CHECK ("is_unknown" = ("sk_familia" = 'de83de21770f2237f4a34e24fc1a60db070e875c321169010eacabf820668bf8')),
    CHECK ("is_unknown" = ("natural_key" IS NULL)),
    CHECK ("is_unknown" OR "sk_familia" = sha256('v1|DIM_FAMILIA_PESQUISA|K|' || "natural_key")),
    CHECK ("is_unknown" OR "titulo_normalizado" IS NOT NULL),
    CHECK (NOT "is_unknown" OR "titulo_normalizado" IS NULL),
    UNIQUE ("titulo_normalizado")
);

INSERT INTO "DIM_FAMILIA_PESQUISA" ("sk_familia", "natural_key", "is_unknown") VALUES ('de83de21770f2237f4a34e24fc1a60db070e875c321169010eacabf820668bf8', NULL, TRUE) ON CONFLICT ("sk_familia") DO NOTHING;

CREATE TABLE IF NOT EXISTS "DIM_FONTE_DADO" (
    "sk_fonte" VARCHAR PRIMARY KEY,
    "natural_key" VARCHAR UNIQUE,
    "is_unknown" BOOLEAN NOT NULL DEFAULT FALSE,
    "source" VARCHAR,
    CHECK ("is_unknown" = ("sk_fonte" = 'ce6f988ab46f22f90db12e52f06273e68e61cf8d010fab7665f3b346c43aa0aa')),
    CHECK ("is_unknown" = ("natural_key" IS NULL)),
    CHECK ("is_unknown" OR "sk_fonte" = sha256('v1|DIM_FONTE_DADO|K|' || "natural_key")),
    CHECK ("is_unknown" OR "source" IS NOT NULL),
    CHECK (NOT "is_unknown" OR "source" IS NULL),
    UNIQUE ("source")
);

INSERT INTO "DIM_FONTE_DADO" ("sk_fonte", "natural_key", "is_unknown") VALUES ('ce6f988ab46f22f90db12e52f06273e68e61cf8d010fab7665f3b346c43aa0aa', NULL, TRUE) ON CONFLICT ("sk_fonte") DO NOTHING;

CREATE TABLE IF NOT EXISTS "DIM_EXECUCAO_CARGA" (
    "sk_carga" VARCHAR PRIMARY KEY,
    "natural_key" VARCHAR UNIQUE,
    "is_unknown" BOOLEAN NOT NULL DEFAULT FALSE,
    "source" VARCHAR,
    "run_id" VARCHAR,
    "concluded_at" TIMESTAMP,
    "source_checksum" VARCHAR,
    CHECK ("is_unknown" = ("sk_carga" = '2c21ccdca460bee3065df8dbfc07a4c98d8b17b081309dfded8f9d1909142182')),
    CHECK ("is_unknown" = ("natural_key" IS NULL)),
    CHECK ("is_unknown" OR "sk_carga" = sha256('v1|DIM_EXECUCAO_CARGA|K|' || "natural_key")),
    CHECK ("is_unknown" OR "source" IS NOT NULL),
    CHECK ("is_unknown" OR "run_id" IS NOT NULL),
    CHECK (NOT "is_unknown" OR "source" IS NULL),
    CHECK (NOT "is_unknown" OR "run_id" IS NULL),
    UNIQUE ("source", "run_id")
);

INSERT INTO "DIM_EXECUCAO_CARGA" ("sk_carga", "natural_key", "is_unknown") VALUES ('2c21ccdca460bee3065df8dbfc07a4c98d8b17b081309dfded8f9d1909142182', NULL, TRUE) ON CONFLICT ("sk_carga") DO NOTHING;
