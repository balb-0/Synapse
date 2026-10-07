-- Consultas de referência das sessões de usabilidade S1–S4.
--
-- Calculam, direto sobre os Parquet da geração usada nas sessões, o valor que
-- cada tarefa deve exibir no recorte combinado. São independentes do modelo
-- semântico: não usam DAX, relacionamentos nem medidas do Power BI.
--
-- Uso (DuckDB >= 1.1), a partir da raiz do repositório:
--   duckdb -c "SET VARIABLE geracao = 'C:/caminho/privado/<generation>';" \
--          -c ".read docs/usabilidade/evidencias/consultas-referencia.sql"
-- Em Python:
--   con = duckdb.connect()
--   con.execute("SET VARIABLE geracao = 'C:/caminho/privado/<generation>'")
--   remova as linhas de comentário e execute cada instrução separada por ";"
--
-- A geração fica fora do Git; somente os resultados agregados são
-- registrados em valores-referencia-v3.md.

CREATE OR REPLACE VIEW c01 AS
SELECT * FROM read_parquet(getvariable('geracao') || '/PUB_C01_CICLO.parquet');
CREATE OR REPLACE VIEW c02 AS
SELECT * FROM read_parquet(getvariable('geracao') || '/PUB_C02_PARTICIPACAO.parquet');
CREATE OR REPLACE VIEW c03 AS
SELECT * FROM read_parquet(getvariable('geracao') || '/PUB_C03_PIPELINE_MENSAL.parquet');
CREATE OR REPLACE VIEW c04 AS
SELECT * FROM read_parquet(getvariable('geracao') || '/PUB_C04_INSTRUMENTO.parquet');
CREATE OR REPLACE VIEW q_campo AS
SELECT * FROM read_parquet(getvariable('geracao') || '/PUB_QUALIDADE_CAMPO.parquet');

-- R-NAV-01: total do portfólio e cartão "Indicadores principais"
SELECT 'R-NAV-01' AS recorte,
       SUM(qtd_pesquisas) AS pesquisas,
       SUM(qtd_ciclo_total_disponivel) AS base_valida_ciclo_total,
       ROUND(SUM(soma_dias_ciclo_total) / NULLIF(SUM(qtd_ciclo_total_disponivel), 0), 1) AS media_dias_ciclo_total,
       ROUND(SUM(soma_dias_coleta) / NULLIF(SUM(qtd_coleta_disponivel), 0), 1) AS media_dias_coleta
FROM c01;

-- R-NAV-01 / R-DET-01: distribuição por status
SELECT 'R-DET-01 status' AS recorte, status, SUM(qtd_pesquisas) AS pesquisas,
       SUM(qtd_ciclo_total_disponivel) AS base_valida_ciclo_total,
       ROUND(SUM(soma_dias_ciclo_total) / NULLIF(SUM(qtd_ciclo_total_disponivel), 0), 1) AS media_dias_ciclo_total
FROM c01 GROUP BY status ORDER BY pesquisas DESC;

-- R-DET-01: tipo dentro do maior status (finalizada)
SELECT 'R-DET-01 tipo' AS recorte, tipo, SUM(qtd_pesquisas) AS pesquisas
FROM c01 WHERE status = 'finalizada' GROUP BY tipo ORDER BY pesquisas DESC;

-- R-FIL-01: área assuntos regulatórios (sem período: C01 não publica data)
SELECT 'R-FIL-01' AS recorte, SUM(qtd_pesquisas) AS pesquisas
FROM c01 WHERE area = 'assuntos regulatórios';

-- R-FIL-02: pesquisa fixa anual, status diferentes de finalizada
SELECT 'R-FIL-02' AS recorte, status, SUM(qtd_pesquisas) AS pesquisas
FROM c01 WHERE tipo = 'pesquisa fixa anual' AND status <> 'finalizada'
GROUP BY ROLLUP (status) ORDER BY status NULLS LAST;

-- R-FIL-04: inovação × pesquisa fixa anual (recorte vazio esperado)
SELECT 'R-FIL-04' AS recorte, COUNT(*) AS linhas, SUM(qtd_pesquisas) AS pesquisas
FROM c01 WHERE area = 'inovação' AND tipo = 'pesquisa fixa anual';

-- R-DET-05: linha da tabela "Acompanhamento das Pesquisas"
SELECT 'R-DET-05' AS recorte, area, status, tipo, qtd_pesquisas,
       ROUND(soma_dias_ciclo_total / NULLIF(qtd_ciclo_total_disponivel, 0), 1) AS media_dias_ciclo_total
FROM c01
WHERE area = 'assuntos regulatórios' AND status = 'finalizada' AND tipo = 'solicitação de associado';

-- R-ETAPA: "Tempo por Etapa e Tipo" com a base de cada média
SELECT 'R-ETAPA' AS recorte, tipo,
       ROUND(SUM(soma_dias_validacao) / NULLIF(SUM(qtd_validacao_disponivel), 0), 1) AS media_validacao,
       SUM(qtd_validacao_disponivel) AS base_validacao,
       ROUND(SUM(soma_dias_coleta) / NULLIF(SUM(qtd_coleta_disponivel), 0), 1) AS media_coleta,
       SUM(qtd_coleta_disponivel) AS base_coleta,
       ROUND(SUM(soma_dias_tabulacao) / NULLIF(SUM(qtd_tabulacao_disponivel), 0), 1) AS media_tabulacao,
       SUM(qtd_tabulacao_disponivel) AS base_tabulacao
FROM c01 GROUP BY tipo ORDER BY tipo;

-- R-SEG-01: sindical trabalhista e rh × pesquisa fixa anual
SELECT 'R-SEG-01' AS recorte, SUM(qtd_pesquisas) AS pesquisas
FROM c01 WHERE area = 'sindical trabalhista e rh' AND tipo = 'pesquisa fixa anual';

-- R-SEG-02 (parte C01): assuntos regulatórios × solicitação de associado × finalizada
SELECT 'R-SEG-02 c01' AS recorte, SUM(qtd_pesquisas) AS pesquisas
FROM c01
WHERE area = 'assuntos regulatórios' AND tipo = 'solicitação de associado' AND status = 'finalizada';

-- R-SEG-03: pilha que zera e retorno ao remover o status
SELECT 'R-SEG-03 com status' AS recorte, COUNT(*) AS linhas, SUM(qtd_pesquisas) AS pesquisas
FROM c01 WHERE area = 'sindical trabalhista e rh' AND tipo = 'pesquisa fixa anual' AND status = 'em tabulação';
SELECT 'R-SEG-03 sem status' AS recorte, COUNT(*) AS linhas, SUM(qtd_pesquisas) AS pesquisas
FROM c01 WHERE area = 'sindical trabalhista e rh' AND tipo = 'pesquisa fixa anual';

-- R-DET-02: participações observadas, total e por área
SELECT 'R-DET-02 total' AS recorte, SUM(qtd_participacoes) AS participacoes,
       SUM(qtd_preenchimento_disponivel) AS base_preenchimento,
       ROUND(SUM(soma_minutos_preenchimento) / NULLIF(SUM(qtd_preenchimento_disponivel), 0), 1) AS media_minutos
FROM c02;
SELECT 'R-DET-02 area' AS recorte, area, SUM(qtd_participacoes) AS participacoes
FROM c02 GROUP BY area ORDER BY participacoes DESC;

-- R-CMP-01 / R-CMP-02: anos e meses de resposta observados
SELECT 'R-CMP' AS recorte, YEAR(mes_resposta) AS ano, mes_resposta,
       COUNT(*) AS linhas, SUM(qtd_participacoes) AS participacoes
FROM c02 GROUP BY ALL ORDER BY mes_resposta NULLS FIRST;

-- R-DET-03 / R-SEG-02 (parte C04): perguntas por tipo na área e no total
SELECT 'R-DET-03 area' AS recorte, tipo_pergunta, SUM(qtd_perguntas) AS associacoes
FROM c04 WHERE area = 'assuntos regulatórios' GROUP BY tipo_pergunta ORDER BY associacoes DESC;
SELECT 'R-DET-03 total' AS recorte, tipo_pergunta, SUM(qtd_perguntas) AS associacoes
FROM c04 GROUP BY ROLLUP (tipo_pergunta) ORDER BY associacoes DESC;

-- R-DET-04: completude global e campos abaixo de 100%
SELECT 'R-DET-04 global' AS recorte, SUM(qtd_preenchidas) AS preenchidas, SUM(qtd_linhas) AS linhas,
       ROUND(100.0 * SUM(qtd_preenchidas) / NULLIF(SUM(qtd_linhas), 0), 1) AS completude_pct
FROM q_campo;
SELECT 'R-DET-04 campo' AS recorte, tabela, campo, qtd_linhas, qtd_preenchidas,
       qtd_linhas - qtd_preenchidas AS afetados,
       ROUND(100.0 * qtd_preenchidas / NULLIF(qtd_linhas, 0), 1) AS completude_pct
FROM q_campo
WHERE tabela = 'pesquisas' AND qtd_preenchidas < qtd_linhas
ORDER BY completude_pct;

-- R-ESTOQUE: fechamentos mensais observados em C03
SELECT 'R-ESTOQUE' AS recorte, COUNT(*) AS linhas, MAX(data_fim_mes) AS ultimo_fechamento,
       SUM(qtd_pesquisas_no_status) AS estoque
FROM c03;
