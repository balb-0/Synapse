"""Gera uma publicação sintética para ensaio de importação no Power BI Desktop."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import duckdb

from etl.analytics.publish import publish_cubes

STATEMENTS = (
    "CREATE TABLE DIM_AREA (sk_area INTEGER, area VARCHAR)",
    "CREATE TABLE DIM_STATUS_PESQUISA (sk_status INTEGER, status VARCHAR)",
    "CREATE TABLE DIM_TIPO_PESQUISA (sk_tipo INTEGER, tipo VARCHAR)",
    "CREATE TABLE DIM_TEMPO (sk_tempo INTEGER, data DATE)",
    "CREATE TABLE DIM_PERFIL_PESQUISA (sk_perfil INTEGER, complexidade VARCHAR, tipo_resposta VARCHAR)",
    "CREATE TABLE DIM_PERGUNTA (sk_pergunta INTEGER, tipo VARCHAR)",
    "CREATE TABLE FATO_CICLO_PESQUISA (sk_pesquisa INTEGER, sk_area INTEGER, sk_status INTEGER, sk_tipo INTEGER, dias_corridos_validacao BIGINT, dias_corridos_coleta BIGINT, dias_corridos_tabulacao BIGINT, dias_corridos_ciclo_total BIGINT)",
    "CREATE TABLE FATO_PARTICIPACAO (sk_pesquisa INTEGER, sk_data_resposta INTEGER, minutos_preenchimento BIGINT)",
    "CREATE TABLE FATO_PIPELINE_MENSAL (data_fim_mes DATE, sk_status INTEGER, sk_area INTEGER, sk_tipo INTEGER, sk_perfil INTEGER, qtd_pesquisas_no_status BIGINT, qtd_entradas_no_mes BIGINT, qtd_saidas_no_mes BIGINT)",
    "CREATE TABLE FATO_PESQUISA_PERGUNTA (sk_pesquisa INTEGER, sk_pergunta INTEGER)",
    "INSERT INTO DIM_AREA VALUES (1, 'Saúde'), (2, 'Educação')",
    "INSERT INTO DIM_STATUS_PESQUISA VALUES (1, 'Ativa'), (2, 'Concluída')",
    "INSERT INTO DIM_TIPO_PESQUISA VALUES (1, 'Mercado'), (2, 'Satisfação')",
    "INSERT INTO DIM_TEMPO VALUES (1, DATE '2026-01-01'), (2, DATE '2026-01-15'), (3, DATE '2026-03-20')",
    "INSERT INTO DIM_PERFIL_PESQUISA VALUES (1, 'Alta', 'Múltipla'), (2, NULL, 'Única')",
    "INSERT INTO DIM_PERGUNTA VALUES (1, 'única'), (2, 'múltipla')",
    "INSERT INTO FATO_CICLO_PESQUISA VALUES (1,1,1,1,2,4,NULL,10), (2,1,1,1,8,NULL,3,20), (3,1,1,1,NULL,6,5,NULL), (4,2,2,2,NULL,NULL,NULL,NULL)",
    "INSERT INTO FATO_PARTICIPACAO VALUES (1,1,5), (2,2,15), (3,3,NULL), (4,NULL,NULL)",
    "INSERT INTO FATO_PIPELINE_MENSAL VALUES (DATE '2026-01-31',1,1,1,1,2,NULL,NULL), (DATE '2026-01-31',2,2,2,2,1,NULL,NULL), (DATE '2026-02-28',1,1,1,1,3,NULL,NULL), (DATE '2026-02-28',2,2,2,2,1,NULL,NULL)",
    "INSERT INTO FATO_PESQUISA_PERGUNTA VALUES (1,1), (2,1), (4,2)",
    "CREATE TABLE ingestao_pesquisas_atual AS SELECT * FROM (VALUES ('p1','Pesquisa sintética 1','Ativa','Mercado','Saúde',2,0.5,'2026-01-01','2026-01-02','2026-01-03','2026-01-31',NULL,'2026-01-30',4,'Alta','Múltipla',5.0,'Teste','Qui',10,2,3), ('p2','Pesquisa sintética 2','Concluída','Satisfação','Educação',NULL,NULL,'2026-02-01',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL)) AS t(pesquisa_id,titulo,status,tipo,area,participantes,part_mercado,data_solicitacao,data_aprov,data_divulgacao,data_limite,prorrogada_ate,data_entrega,dias_uteis_para_entrega,complexidade,tipo_resposta,tempo_preenchimento,objetivos,dia_semana_lancamento,dias_uteis_aberta,dias_solicitacao_divulgacao,dias_tabulacao)",
    "CREATE TABLE ingestao_empresas_atual AS SELECT * FROM (VALUES ('e1','Empresa sintética',0.5,'Nacional',true,'Efetivo','São Paulo','SP','Brasil')) AS t(empresa_id,nome_fantasia,part_mercado,nacionalidade,associado,tipo_associado,cidade,estado,pais)",
    "CREATE TABLE ingestao_clientes_atual AS SELECT * FROM (VALUES ('c1','e1','Analista','Pesquisa','fixture@example.invalid'), ('c2','ausente',NULL,NULL,NULL)) AS t(cliente_id,empresa_id,cargo,departamento,email)",
    "CREATE TABLE ingestao_respondentes AS SELECT * FROM (VALUES ('p1','2026-01-01 09:00','2026-01-01 09:05','e1',0.5,'c1'), ('p2',NULL,NULL,NULL,NULL,NULL)) AS t(pesquisa_id,hora_inicio,hora_termino,empresa_id,market_share,cliente_id)",
    "CREATE TABLE ingestao_questoes_atual AS SELECT * FROM (VALUES ('q1','p1','Pesquisa sintética 1','Texto reservado','única',2,NULL,NULL,NULL,NULL,NULL,NULL,NULL)) AS t(pergunta_id,pesquisa_id,pesquisa_titulo,enunciado,tipo,qtd_alternativas,alternativas,linhas_matriz,colunas_matriz,confianca,formato_arquivo,col_origem,observacoes)",
    "CREATE TABLE ingestao_respostas_atual AS SELECT * FROM (VALUES ('r1','p1','q1','resp1','e1','Sim',NULL,NULL,NULL), ('r2','p2','q1','resp2','ausente',NULL,NULL,NULL,NULL)) AS t(resposta_id,pesquisa_id,pergunta_id,respondent_id,empresa_id,alternativa,linha_matriz,coluna_matriz,valor)",
    "CREATE TABLE ingestao_pesquisas AS SELECT pesquisa_id FROM ingestao_pesquisas_atual UNION ALL SELECT 'p1'",
    "CREATE TABLE ingestao_empresas AS SELECT empresa_id FROM ingestao_empresas_atual",
    "CREATE TABLE ingestao_clientes AS SELECT cliente_id FROM ingestao_clientes_atual",
    "CREATE TABLE ingestao_questoes AS SELECT pesquisa_id, pergunta_id FROM ingestao_questoes_atual",
    "CREATE TABLE ingestao_respostas AS SELECT pesquisa_id, resposta_id FROM ingestao_respostas_atual",
)


def create_database(path: Path) -> None:
    connection = duckdb.connect(str(path))
    try:
        for statement in STATEMENTS:
            connection.execute(statement)
    finally:
        connection.close()


def generate(output: Path) -> dict:
    output = output.expanduser()
    if any((parent / ".git").exists() for parent in (output.resolve(), *output.resolve().parents)):
        raise ValueError("a saída deve ficar fora de qualquer repositório Git")
    with tempfile.TemporaryDirectory(prefix="fixture-bi02-") as temporary:
        database = Path(temporary) / "synthetic.duckdb"
        create_database(database)
        return publish_cubes(database, output, load_reference="synthetic-bi02-fixture")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="diretório privado fora do Git")
    args = parser.parse_args()
    manifest = generate(args.output)
    print(json.dumps({"generation": manifest["generation"], "load_reference": manifest["load_reference"], "rows": {name: entry["rows"] for name, entry in manifest["tables"].items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
