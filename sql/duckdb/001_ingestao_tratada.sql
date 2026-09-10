-- Contrato físico das tabelas de ingestão tratada no DuckDB.
-- Gerado de src/etl/load/ddl.py; valide com
-- `PYTHONPATH=src python scripts/load/render_ddl.py --check`.
--
-- Uma linha corresponde a uma linha da fonte. O mesmo registro pode
-- aparecer em mais de uma linha quando o arquivo é reexportado com
-- conteúdo corrigido: a chave primária é a identidade de idempotência
-- (chave de negócio + conteúdo). As views `_atual` devolvem a versão
-- mais recente de cada chave de negócio. As views sem prefixo são
-- compatibilidade transitória com leitores anteriores ao prefixo.
--
-- A carga registra cada lote em `_batch_metadata` com status e as três
-- contagens, e cada rejeição em `rejected` com um motivo por linha em
-- `rejected_reason`. As views `execucao` e `reconciliacao_execucao`
-- agregam por execução e provam a equação de contagem.

CREATE TABLE IF NOT EXISTS "ingestao_pesquisas" (
    "pesquisa_id" VARCHAR NOT NULL,
    "titulo" VARCHAR,
    "status" VARCHAR,
    "tipo" VARCHAR,
    "area" VARCHAR,
    "participantes" BIGINT,
    "part_mercado" DECIMAL(18, 6),
    "data_solicitacao" DATE,
    "data_aprov" DATE,
    "data_divulgacao" DATE,
    "data_limite" DATE,
    "prorrogada_ate" DATE,
    "data_entrega" DATE,
    "dias_uteis_para_entrega" BIGINT,
    "complexidade" VARCHAR,
    "tipo_resposta" VARCHAR,
    "tempo_preenchimento" DECIMAL(18, 6),
    "objetivos" VARCHAR,
    "dia_semana_lancamento" VARCHAR,
    "dias_uteis_aberta" BIGINT,
    "dias_solicitacao_divulgacao" BIGINT,
    "dias_tabulacao" BIGINT,
    "source" VARCHAR NOT NULL,
    "run_id" VARCHAR NOT NULL,
    "task_id" VARCHAR NOT NULL,
    "batch_id" VARCHAR NOT NULL,
    "source_checksum" VARCHAR,
    "source_offset" UBIGINT NOT NULL,
    "content_checksum" VARCHAR NOT NULL,
    "record_identity" VARCHAR NOT NULL,
    "idempotency_key" VARCHAR NOT NULL,
    "ingested_at" TIMESTAMP NOT NULL,
    "schema_version" VARCHAR NOT NULL,
    PRIMARY KEY ("idempotency_key"),
    UNIQUE ("pesquisa_id", "content_checksum")
);

CREATE TABLE IF NOT EXISTS "ingestao_empresas" (
    "empresa_id" VARCHAR NOT NULL,
    "nome_fantasia" VARCHAR,
    "part_mercado" DECIMAL(18, 6),
    "nacionalidade" VARCHAR,
    "associado" BOOLEAN,
    "tipo_associado" VARCHAR,
    "cidade" VARCHAR,
    "estado" VARCHAR,
    "pais" VARCHAR,
    "source" VARCHAR NOT NULL,
    "run_id" VARCHAR NOT NULL,
    "task_id" VARCHAR NOT NULL,
    "batch_id" VARCHAR NOT NULL,
    "source_checksum" VARCHAR,
    "source_offset" UBIGINT NOT NULL,
    "content_checksum" VARCHAR NOT NULL,
    "record_identity" VARCHAR NOT NULL,
    "idempotency_key" VARCHAR NOT NULL,
    "ingested_at" TIMESTAMP NOT NULL,
    "schema_version" VARCHAR NOT NULL,
    PRIMARY KEY ("idempotency_key"),
    UNIQUE ("empresa_id", "content_checksum")
);

CREATE TABLE IF NOT EXISTS "ingestao_clientes" (
    "cliente_id" VARCHAR NOT NULL,
    "empresa_id" VARCHAR NOT NULL,
    "cargo" VARCHAR,
    "departamento" VARCHAR,
    "email" VARCHAR,
    "source" VARCHAR NOT NULL,
    "run_id" VARCHAR NOT NULL,
    "task_id" VARCHAR NOT NULL,
    "batch_id" VARCHAR NOT NULL,
    "source_checksum" VARCHAR,
    "source_offset" UBIGINT NOT NULL,
    "content_checksum" VARCHAR NOT NULL,
    "record_identity" VARCHAR NOT NULL,
    "idempotency_key" VARCHAR NOT NULL,
    "ingested_at" TIMESTAMP NOT NULL,
    "schema_version" VARCHAR NOT NULL,
    PRIMARY KEY ("idempotency_key"),
    UNIQUE ("cliente_id", "content_checksum")
);

CREATE TABLE IF NOT EXISTS "ingestao_respondentes" (
    "pesquisa_id" VARCHAR NOT NULL,
    "hora_inicio" TIMESTAMP,
    "hora_termino" TIMESTAMP,
    "empresa_id" VARCHAR NOT NULL,
    "market_share" DECIMAL(18, 6),
    "cliente_id" VARCHAR,
    "source" VARCHAR NOT NULL,
    "run_id" VARCHAR NOT NULL,
    "task_id" VARCHAR NOT NULL,
    "batch_id" VARCHAR NOT NULL,
    "source_checksum" VARCHAR,
    "source_offset" UBIGINT NOT NULL,
    "content_checksum" VARCHAR NOT NULL,
    "record_identity" VARCHAR NOT NULL,
    "idempotency_key" VARCHAR NOT NULL,
    "ingested_at" TIMESTAMP NOT NULL,
    "schema_version" VARCHAR NOT NULL,
    PRIMARY KEY ("idempotency_key"),
    UNIQUE ("source_checksum", "source_offset")
);

CREATE TABLE IF NOT EXISTS "ingestao_questoes" (
    "pergunta_id" VARCHAR NOT NULL,
    "pesquisa_id" VARCHAR NOT NULL,
    "pesquisa_titulo" VARCHAR,
    "enunciado" VARCHAR,
    "tipo" VARCHAR NOT NULL,
    "qtd_alternativas" BIGINT,
    "alternativas" VARCHAR,
    "linhas_matriz" VARCHAR,
    "colunas_matriz" VARCHAR,
    "confianca" VARCHAR,
    "formato_arquivo" VARCHAR,
    "col_origem" VARCHAR,
    "observacoes" VARCHAR,
    "source" VARCHAR NOT NULL,
    "run_id" VARCHAR NOT NULL,
    "task_id" VARCHAR NOT NULL,
    "batch_id" VARCHAR NOT NULL,
    "source_checksum" VARCHAR,
    "source_offset" UBIGINT NOT NULL,
    "content_checksum" VARCHAR NOT NULL,
    "record_identity" VARCHAR NOT NULL,
    "idempotency_key" VARCHAR NOT NULL,
    "ingested_at" TIMESTAMP NOT NULL,
    "schema_version" VARCHAR NOT NULL,
    PRIMARY KEY ("idempotency_key"),
    UNIQUE ("pesquisa_id", "pergunta_id", "content_checksum")
);

CREATE TABLE IF NOT EXISTS "ingestao_respostas" (
    "resposta_id" VARCHAR NOT NULL,
    "pesquisa_id" VARCHAR NOT NULL,
    "pergunta_id" VARCHAR NOT NULL,
    "respondent_id" VARCHAR NOT NULL,
    "empresa_id" VARCHAR,
    "alternativa" VARCHAR,
    "linha_matriz" VARCHAR,
    "coluna_matriz" VARCHAR,
    "valor" VARCHAR,
    "source" VARCHAR NOT NULL,
    "run_id" VARCHAR NOT NULL,
    "task_id" VARCHAR NOT NULL,
    "batch_id" VARCHAR NOT NULL,
    "source_checksum" VARCHAR,
    "source_offset" UBIGINT NOT NULL,
    "content_checksum" VARCHAR NOT NULL,
    "record_identity" VARCHAR NOT NULL,
    "idempotency_key" VARCHAR NOT NULL,
    "ingested_at" TIMESTAMP NOT NULL,
    "schema_version" VARCHAR NOT NULL,
    PRIMARY KEY ("idempotency_key"),
    UNIQUE ("pesquisa_id", "resposta_id", "content_checksum")
);

CREATE TABLE IF NOT EXISTS "rejected" (
    rejection_id VARCHAR NOT NULL,
    source VARCHAR NOT NULL,
    source_checksum VARCHAR,
    source_offset UBIGINT NOT NULL,
    run_id VARCHAR NOT NULL,
    batch_id VARCHAR NOT NULL,
    ingested_at TIMESTAMP NOT NULL,
    PRIMARY KEY (rejection_id, run_id, batch_id)
);

CREATE TABLE IF NOT EXISTS "rejected_reason" (
    rejection_id VARCHAR NOT NULL,
    code VARCHAR NOT NULL,
    field VARCHAR NOT NULL,
    PRIMARY KEY (rejection_id, code, field)
);

CREATE TABLE IF NOT EXISTS "_control_object" (
    source VARCHAR NOT NULL,
    source_checksum VARCHAR PRIMARY KEY,
    run_id VARCHAR NOT NULL,
    concluded_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS "_loaded_identity" (
    source VARCHAR NOT NULL,
    record_identity VARCHAR PRIMARY KEY,
    content_checksum VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS "_checkpoint" (
    source VARCHAR PRIMARY KEY,
    position VARCHAR,
    sequence BIGINT,
    source_version VARCHAR
);

CREATE TABLE IF NOT EXISTS "_batch_metadata" (
    source VARCHAR NOT NULL,
    run_id VARCHAR NOT NULL,
    task_id VARCHAR NOT NULL,
    batch_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    record_count BIGINT NOT NULL,
    accepted_count BIGINT NOT NULL,
    rejected_count BIGINT NOT NULL,
    duplicated_count BIGINT NOT NULL,
    byte_count BIGINT NOT NULL,
    schema_version VARCHAR NOT NULL,
    source_checksum VARCHAR,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP NOT NULL,
    PRIMARY KEY (run_id, batch_id)
);

CREATE OR REPLACE VIEW "ingestao_pesquisas_atual" AS
SELECT * EXCLUDE (_versao) FROM (
    SELECT *, row_number() OVER (
        PARTITION BY "pesquisa_id"
        ORDER BY "ingested_at" DESC, "source_offset" DESC
    ) AS _versao
    FROM "ingestao_pesquisas"
) WHERE _versao = 1;

CREATE OR REPLACE VIEW "ingestao_empresas_atual" AS
SELECT * EXCLUDE (_versao) FROM (
    SELECT *, row_number() OVER (
        PARTITION BY "empresa_id"
        ORDER BY "ingested_at" DESC, "source_offset" DESC
    ) AS _versao
    FROM "ingestao_empresas"
) WHERE _versao = 1;

CREATE OR REPLACE VIEW "ingestao_clientes_atual" AS
SELECT * EXCLUDE (_versao) FROM (
    SELECT *, row_number() OVER (
        PARTITION BY "cliente_id"
        ORDER BY "ingested_at" DESC, "source_offset" DESC
    ) AS _versao
    FROM "ingestao_clientes"
) WHERE _versao = 1;

CREATE OR REPLACE VIEW "ingestao_questoes_atual" AS
SELECT * EXCLUDE (_versao) FROM (
    SELECT *, row_number() OVER (
        PARTITION BY "pesquisa_id", "pergunta_id"
        ORDER BY "ingested_at" DESC, "source_offset" DESC
    ) AS _versao
    FROM "ingestao_questoes"
) WHERE _versao = 1;

CREATE OR REPLACE VIEW "ingestao_respostas_atual" AS
SELECT * EXCLUDE (_versao) FROM (
    SELECT *, row_number() OVER (
        PARTITION BY "pesquisa_id", "resposta_id"
        ORDER BY "ingested_at" DESC, "source_offset" DESC
    ) AS _versao
    FROM "ingestao_respostas"
) WHERE _versao = 1;

CREATE VIEW IF NOT EXISTS "pesquisas" AS
SELECT * FROM "ingestao_pesquisas";

CREATE VIEW IF NOT EXISTS "empresas" AS
SELECT * FROM "ingestao_empresas";

CREATE VIEW IF NOT EXISTS "clientes" AS
SELECT * FROM "ingestao_clientes";

CREATE VIEW IF NOT EXISTS "respondentes" AS
SELECT * FROM "ingestao_respondentes";

CREATE VIEW IF NOT EXISTS "questoes" AS
SELECT * FROM "ingestao_questoes";

CREATE VIEW IF NOT EXISTS "respostas" AS
SELECT * FROM "ingestao_respostas";

CREATE OR REPLACE VIEW "execucao" AS
SELECT
    run_id,
    string_agg(DISTINCT source, ', ' ORDER BY source) AS fontes,
    CASE
        WHEN count(*) FILTER (WHERE status = 'falha') > 0
            THEN 'falha'
        WHEN sum(rejected_count) > 0 THEN 'carregado_com_rejeicoes'
        ELSE 'carregado'
    END AS status,
    count(*) AS lotes,
    sum(record_count) AS extraidos,
    sum(accepted_count) AS carregados,
    sum(rejected_count) AS rejeitados,
    sum(duplicated_count) AS duplicados,
    sum(byte_count) AS bytes,
    min(started_at) AS iniciado_em,
    max(finished_at) AS concluido_em
FROM "_batch_metadata"
GROUP BY run_id;

CREATE OR REPLACE VIEW "reconciliacao_execucao" AS
SELECT
    execucao.run_id,
    execucao.fontes,
    execucao.status,
    execucao.lotes,
    extraidos,
    carregados,
    rejeitados,
    duplicados,
    coalesce(registro.rejeitados_registrados, 0) AS rejeitados_registrados,
    carregados + rejeitados + duplicados AS contabilizados,
    extraidos - (carregados + rejeitados + duplicados) AS diferenca,
    extraidos = (carregados + rejeitados + duplicados) AND rejeitados = coalesce(registro.rejeitados_registrados, 0) AS conciliado
FROM "execucao" AS execucao
LEFT JOIN (
    SELECT run_id, count(*) AS rejeitados_registrados
    FROM "rejected"
    GROUP BY run_id
) AS registro ON registro.run_id = execucao.run_id;
