"""Observa os arquivos entregues a um consumidor sem banco de origem."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import duckdb

from etl.analytics.publish import PUBLICATIONS, publish_cubes


class PublishCubesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.database = root / "private.duckdb"
        self.output = root / "published"
        connection = duckdb.connect(str(self.database))
        for statement in (
            "CREATE TABLE DIM_AREA (sk_area VARCHAR, area VARCHAR)",
            "CREATE TABLE DIM_STATUS_PESQUISA (sk_status VARCHAR, status VARCHAR)",
            "CREATE TABLE DIM_TIPO_PESQUISA (sk_tipo VARCHAR, tipo VARCHAR)",
            "CREATE TABLE DIM_TEMPO (sk_tempo VARCHAR, data DATE)",
            "CREATE TABLE DIM_PERFIL_PESQUISA (sk_perfil VARCHAR, complexidade VARCHAR, tipo_resposta VARCHAR)",
            "CREATE TABLE DIM_PERGUNTA (sk_pergunta VARCHAR, tipo VARCHAR, enunciado VARCHAR)",
            "CREATE TABLE FATO_CICLO_PESQUISA (sk_pesquisa VARCHAR, sk_area VARCHAR, sk_status VARCHAR, sk_tipo VARCHAR, dias_corridos_validacao BIGINT, dias_corridos_coleta BIGINT, dias_corridos_tabulacao BIGINT, dias_corridos_ciclo_total BIGINT)",
            "CREATE TABLE FATO_PARTICIPACAO (sk_pesquisa VARCHAR, sk_data_resposta VARCHAR, minutos_preenchimento BIGINT, source_checksum VARCHAR, source_offset BIGINT)",
            "CREATE TABLE FATO_PIPELINE_MENSAL (data_fim_mes DATE, sk_status VARCHAR, sk_area VARCHAR, sk_tipo VARCHAR, sk_perfil VARCHAR, qtd_pesquisas_no_status BIGINT, qtd_entradas_no_mes BIGINT, qtd_saidas_no_mes BIGINT)",
            "CREATE TABLE FATO_PESQUISA_PERGUNTA (sk_pesquisa VARCHAR, sk_pergunta VARCHAR)",
            "CREATE TABLE ingestao_private (email VARCHAR)",
            """
            CREATE TABLE ingestao_pesquisas_atual AS
            SELECT * FROM (VALUES
                ('p1', 'Pesquisa 1', 'Ativa', 'Mercado', 'Saúde', 10, 0.5,
                 '2026-01-01', NULL, '2026-01-05', '2026-02-01', NULL,
                 '2026-02-10', 5, 'Alta', 'Múltipla', 3.5, 'Objetivo', 'Seg',
                 10, 4, 9),
                ('p1', 'Pesquisa 1 (reprocessada)', 'Ativa', 'Mercado', 'Saúde',
                 10, 0.5, '2026-01-01', NULL, '2026-01-05', '2026-02-01', NULL,
                 '2026-02-10', 5, 'Alta', 'Múltipla', 3.5, 'Objetivo', 'Seg',
                 10, 4, 9),
                ('p2', 'Pesquisa 2', 'Encerrada', 'Satisfação', 'Educação', 4,
                 0.2, '2026-03-01', '2026-03-04', '2026-03-06', '2026-04-01',
                 NULL, '2026-04-05', 3, 'Baixa', 'Única', 2.0, 'Objetivo 2',
                 'Ter', 6, 5, 4)
            ) AS t(pesquisa_id, titulo, status, tipo, area, participantes,
                   part_mercado, data_solicitacao, data_aprov, data_divulgacao,
                   data_limite, prorrogada_ate, data_entrega,
                   dias_uteis_para_entrega, complexidade, tipo_resposta,
                   tempo_preenchimento, objetivos, dia_semana_lancamento,
                   dias_uteis_aberta, dias_solicitacao_divulgacao,
                   dias_tabulacao)
            """,
            """
            CREATE TABLE ingestao_empresas_atual AS
            SELECT * FROM (VALUES
                ('e1', 'Empresa 1', 0.5, 'Nacional', true, 'Efetivo', 'SP', 'SP', 'Brasil'),
                ('e2', 'Empresa 2', NULL, 'Estrangeira', false, NULL, 'RJ', 'RJ', 'Brasil')
            ) AS t(empresa_id, nome_fantasia, part_mercado, nacionalidade,
                   associado, tipo_associado, cidade, estado, pais)
            """,
            """
            CREATE TABLE ingestao_clientes_atual AS
            SELECT * FROM (VALUES
                ('c1', 'e1', 'Analista', 'Compras', 'c1@example.invalid'),
                ('c2', 'e9', 'Gerente', NULL, 'c2@example.invalid')
            ) AS t(cliente_id, empresa_id, cargo, departamento, email)
            """,
            """
            CREATE TABLE ingestao_respondentes AS
            SELECT * FROM (VALUES
                ('p1', '2026-01-10 09:00', '2026-01-10 09:20', 'e1', 0.5, 'c1'),
                ('p9', '2026-01-11 09:00', NULL, 'e1', NULL, NULL)
            ) AS t(pesquisa_id, hora_inicio, hora_termino, empresa_id,
                   market_share, cliente_id)
            """,
            """
            CREATE TABLE ingestao_questoes_atual AS
            SELECT * FROM (VALUES
                ('q1', 'p1', 'Pesquisa 1', 'Enunciado privado', 'única', 4,
                 NULL, NULL, NULL, NULL, NULL, NULL, NULL),
                ('q2', 'p9', 'Pesquisa 9', 'Enunciado privado 2', 'múltipla', 3,
                 NULL, NULL, NULL, NULL, NULL, NULL, NULL)
            ) AS t(pergunta_id, pesquisa_id, pesquisa_titulo, enunciado, tipo,
                   qtd_alternativas, alternativas, linhas_matriz,
                   colunas_matriz, confianca, formato_arquivo, col_origem,
                   observacoes)
            """,
            """
            CREATE TABLE ingestao_respostas_atual AS
            SELECT * FROM (VALUES
                ('r1', 'p1', 'q1', 'resp1', 'e1', 'Sim', NULL, NULL, NULL),
                ('r2', 'p9', 'q9', 'resp2', 'e9', NULL, NULL, NULL, NULL)
            ) AS t(resposta_id, pesquisa_id, pergunta_id, respondent_id,
                   empresa_id, alternativa, linha_matriz, coluna_matriz, valor)
            """,
            "CREATE TABLE ingestao_pesquisas AS SELECT pesquisa_id FROM ingestao_pesquisas_atual",
            "CREATE TABLE ingestao_empresas AS SELECT empresa_id FROM ingestao_empresas_atual",
            "CREATE TABLE ingestao_clientes AS SELECT cliente_id FROM ingestao_clientes_atual",
            "CREATE TABLE ingestao_questoes AS SELECT pesquisa_id, pergunta_id FROM ingestao_questoes_atual",
            "CREATE TABLE ingestao_respostas AS SELECT pesquisa_id, resposta_id FROM ingestao_respostas_atual",
            "INSERT INTO DIM_AREA VALUES ('area1', 'Saúde')",
            "INSERT INTO DIM_STATUS_PESQUISA VALUES ('status1', 'Ativa')",
            "INSERT INTO DIM_TIPO_PESQUISA VALUES ('tipo1', 'Mercado')",
            "INSERT INTO DIM_TEMPO VALUES ('tempo1', DATE '2026-09-03')",
            "INSERT INTO DIM_PERFIL_PESQUISA VALUES ('perfil1', NULL, NULL)",
            "INSERT INTO DIM_PERGUNTA VALUES ('pergunta1', 'única', 'texto livre privado')",
            "INSERT INTO FATO_CICLO_PESQUISA VALUES ('pesquisa1','area1','status1','tipo1',NULL,3,NULL,7)",
            "INSERT INTO FATO_PARTICIPACAO VALUES ('pesquisa1','tempo1',NULL,'checksum privado',1)",
            "INSERT INTO FATO_PIPELINE_MENSAL VALUES (DATE '2026-09-30','status1','area1','tipo1','perfil1',1,NULL,NULL)",
            "INSERT INTO FATO_PESQUISA_PERGUNTA VALUES ('pesquisa1','pergunta1')",
            "INSERT INTO ingestao_private VALUES ('segredo@example.invalid')",
        ):
            connection.execute(statement)
        connection.close()

    def test_publishes_only_seven_curated_files_with_nulls(self):
        manifest = publish_cubes(self.database, self.output, load_reference="synthetic-run-test-1")
        current = json.loads((self.output / "current.json").read_text())
        generation = self.output / current["generation"]
        self.assertEqual(manifest["load_reference"], "synthetic-run-test-1")
        self.assertEqual(
            manifest["tables"]["PUB_C03_PIPELINE_MENSAL"]["observation_state"], "unverified"
        )
        self.assertNotIn("observed_months", manifest["tables"]["PUB_C03_PIPELINE_MENSAL"])
        self.assertEqual(set(manifest["tables"]), set(PUBLICATIONS))
        self.assertEqual(
            {item.name for item in generation.iterdir()},
            {"manifest.json", *(name + ".parquet" for name in PUBLICATIONS)},
        )

        # Este leitor recebe apenas a publicação; não conhece o caminho do banco.
        reader = duckdb.connect(":memory:")
        try:
            for name, entry in manifest["tables"].items():
                path = generation / entry["file"]
                self.assertEqual(
                    entry["rows"],
                    reader.execute("SELECT COUNT(*) FROM read_parquet(?)", [str(path)]).fetchone()[
                        0
                    ],
                )
                self.assertNotIn("sk_pessoa", entry["columns"])
                self.assertNotIn("source_checksum", entry["columns"])
                self.assertNotIn("enunciado", entry["columns"])
                self.assertNotIn("email", entry["columns"])
                self.assertEqual(len(entry["sha256"]), 64)
            c01 = generation / "PUB_C01_CICLO.parquet"
            self.assertEqual(
                reader.execute(
                    "SELECT soma_dias_validacao, qtd_validacao_disponivel, soma_dias_coleta FROM read_parquet(?)",
                    [str(c01)],
                ).fetchone(),
                (None, 0, 3),
            )
            c03 = generation / "PUB_C03_PIPELINE_MENSAL.parquet"
            self.assertEqual(
                reader.execute(
                    "SELECT qtd_entradas_no_mes, qtd_saidas_no_mes FROM read_parquet(?)",
                    [str(c03)],
                ).fetchone(),
                (None, None),
            )
            with self.assertRaises(duckdb.CatalogException):
                reader.execute("SELECT * FROM ingestao_private")
        finally:
            reader.close()

    def test_publishes_physical_completion_integrity_and_duplicates(self):
        manifest = publish_cubes(self.database, self.output, load_reference="synthetic-run-test-1")
        current = json.loads((self.output / "current.json").read_text())
        generation = self.output / current["generation"]
        reader = duckdb.connect(":memory:")
        try:
            campo = generation / "PUB_QUALIDADE_CAMPO.parquet"
            data_aprov = reader.execute(
                "SELECT qtd_linhas, qtd_preenchidas FROM read_parquet(?)"
                " WHERE tabela = 'pesquisas' AND campo = 'data_aprov'",
                [str(campo)],
            ).fetchone()
            self.assertEqual(data_aprov, (3, 1))

            relacao = generation / "PUB_QUALIDADE_RELACAO.parquet"
            clientes_empresa = reader.execute(
                "SELECT qtd_chaves_informadas, qtd_chaves_correspondentes"
                " FROM read_parquet(?) WHERE relacao = 'clientes.empresa_id'",
                [str(relacao)],
            ).fetchone()
            self.assertEqual(clientes_empresa, (2, 1))

            duplicidade = generation / "PUB_QUALIDADE_DUPLICIDADE.parquet"
            pesquisas_dup = reader.execute(
                "SELECT qtd_linhas, qtd_chaves_distintas FROM read_parquet(?)"
                " WHERE tabela = 'pesquisas'",
                [str(duplicidade)],
            ).fetchone()
            self.assertEqual(pesquisas_dup, (3, 2))

            for entry_name in ("PUB_QUALIDADE_CAMPO", "PUB_QUALIDADE_RELACAO"):
                columns = manifest["tables"][entry_name]["columns"]
                self.assertNotIn("email", columns)
                self.assertNotIn("enunciado", columns)
        finally:
            reader.close()

    def test_physical_completion_counts_cells_without_applicability_filter(self):
        first = publish_cubes(self.database, self.output, load_reference="synthetic-physical-completion")
        reader = duckdb.connect(":memory:")
        self.addCleanup(reader.close)
        publication = self.output / first["generation"] / "PUB_QUALIDADE_CAMPO.parquet"
        # Both questions are non-matrix. Their matrix fields still have a
        # physical denominator; no mandatory-field/conditional rule is inferred.
        self.assertEqual(
            reader.execute(
                "SELECT SUM(qtd_linhas), SUM(qtd_preenchidas) FROM read_parquet(?)"
                " WHERE tabela = 'questoes' AND campo IN ('linhas_matriz', 'colunas_matriz')",
                [str(publication)],
            ).fetchone(),
            (4, 0),
        )
        # Each selected field contributes one cell per row. SQL COUNT counts
        # a non-null empty string; it does not validate semantic content.
        writer = duckdb.connect(str(self.database))
        try:
            writer.execute("UPDATE ingestao_clientes_atual SET departamento = ''")
        finally:
            writer.close()
        second = publish_cubes(self.database, self.output, load_reference="synthetic-non-null-cell")
        self.assertEqual(
            reader.execute(
                "SELECT qtd_linhas, qtd_preenchidas FROM read_parquet(?)"
                " WHERE tabela = 'clientes' AND campo = 'departamento'",
                [str(self.output / second["generation"] / "PUB_QUALIDADE_CAMPO.parquet")],
            ).fetchone(),
            (2, 2),
        )

    def test_physical_completion_empty_source_publishes_zero_base(self):
        writer = duckdb.connect(str(self.database))
        try:
            writer.execute("DELETE FROM ingestao_questoes_atual")
        finally:
            writer.close()
        manifest = publish_cubes(self.database, self.output, load_reference="synthetic-empty-source")
        reader = duckdb.connect(":memory:")
        self.addCleanup(reader.close)
        self.assertEqual(
            reader.execute(
                "SELECT qtd_linhas, qtd_preenchidas FROM read_parquet(?)"
                " WHERE tabela = 'questoes' AND campo = 'linhas_matriz'",
                [str(self.output / manifest["generation"] / "PUB_QUALIDADE_CAMPO.parquet")],
            ).fetchone(),
            (0, 0),
        )

    def test_failure_keeps_previous_generation_current(self):
        first = publish_cubes(self.database, self.output, load_reference="synthetic-run-test-1")
        with patch("etl.analytics.publish._digest", side_effect=RuntimeError("falha injetada")):
            with self.assertRaisesRegex(RuntimeError, "falha injetada"):
                publish_cubes(self.database, self.output, load_reference="synthetic-run-test-2")
        self.assertEqual(
            json.loads((self.output / "current.json").read_text())["generation"],
            first["generation"],
        )
        self.assertFalse(list(self.output.glob(".pending-*")))

    def test_second_publication_is_complete_and_switches_pointer(self):
        first = publish_cubes(self.database, self.output, load_reference="synthetic-run-test-1")
        second = publish_cubes(self.database, self.output, load_reference="synthetic-run-test-2")
        self.assertNotEqual(first["generation"], second["generation"])
        self.assertEqual(
            json.loads((self.output / "current.json").read_text())["generation"],
            second["generation"],
        )
        self.assertTrue((self.output / first["generation"] / "manifest.json").exists())
        self.assertEqual(
            {name: table["rows"] for name, table in first["tables"].items()},
            {name: table["rows"] for name, table in second["tables"].items()},
        )

    def test_rejects_output_inside_git_or_secret_like_reference(self):
        with self.assertRaisesRegex(ValueError, "identificador simples"):
            publish_cubes(self.database, self.output, load_reference="token=123")
        inside_repo = Path(__file__).resolve().parents[2] / "data" / "publication"
        with self.assertRaisesRegex(ValueError, "fora do repositório"):
            publish_cubes(self.database, inside_repo, load_reference="synthetic-run-test-1")
        self.assertFalse(inside_repo.exists())

    def test_source_without_controls_requires_explicit_synthetic_reference(self):
        with self.assertRaisesRegex(ValueError, "synthetic-"):
            publish_cubes(self.database, self.output, load_reference="run-without-control")
        self.assertFalse((self.output / "current.json").exists())
        self.assertFalse(list(self.output.glob(".pending-*")))

    def test_question_relation_uses_research_and_question_without_multiplying_children(self):
        with duckdb.connect(str(self.database)) as connection:
            connection.execute(
                "INSERT INTO ingestao_questoes_atual "
                "SELECT * REPLACE('other-research' AS pesquisa_id) "
                "FROM ingestao_questoes_atual WHERE pergunta_id='q1'"
            )
        manifest = publish_cubes(self.database, self.output, load_reference="synthetic-composite")
        path = self.output / manifest["generation"] / "PUB_QUALIDADE_RELACAO.parquet"
        with duckdb.connect() as reader:
            result = reader.execute(
                "SELECT qtd_chaves_informadas, qtd_chaves_correspondentes "
                "FROM read_parquet(?) WHERE relacao='respostas.pergunta_id'",
                [str(path)],
            ).fetchone()
        self.assertEqual(result, (2, 1))

    def test_question_id_from_another_research_does_not_match(self):
        with duckdb.connect(str(self.database)) as connection:
            connection.execute(
                "UPDATE ingestao_respostas_atual SET pesquisa_id='other-research' "
                "WHERE pergunta_id='q1'"
            )
        manifest = publish_cubes(self.database, self.output, load_reference="synthetic-orphan")
        path = self.output / manifest["generation"] / "PUB_QUALIDADE_RELACAO.parquet"
        with duckdb.connect() as reader:
            result = reader.execute(
                "SELECT qtd_chaves_informadas, qtd_chaves_correspondentes "
                "FROM read_parquet(?) WHERE relacao='respostas.pergunta_id'",
                [str(path)],
            ).fetchone()
        self.assertEqual(result, (2, 0))


if __name__ == "__main__":
    unittest.main()
