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

    def test_publishes_only_four_curated_files_with_nulls(self):
        manifest = publish_cubes(self.database, self.output, load_reference="run-test-1")
        current = json.loads((self.output / "current.json").read_text())
        generation = self.output / current["generation"]
        self.assertEqual(manifest["load_reference"], "run-test-1")
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

    def test_failure_keeps_previous_generation_current(self):
        first = publish_cubes(self.database, self.output, load_reference="run-test-1")
        with patch("etl.analytics.publish._digest", side_effect=RuntimeError("falha injetada")):
            with self.assertRaisesRegex(RuntimeError, "falha injetada"):
                publish_cubes(self.database, self.output, load_reference="run-test-2")
        self.assertEqual(
            json.loads((self.output / "current.json").read_text())["generation"],
            first["generation"],
        )
        self.assertFalse(list(self.output.glob(".pending-*")))

    def test_second_publication_is_complete_and_switches_pointer(self):
        first = publish_cubes(self.database, self.output, load_reference="run-test-1")
        second = publish_cubes(self.database, self.output, load_reference="run-test-2")
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
            publish_cubes(self.database, inside_repo, load_reference="run-test-1")
        self.assertFalse(inside_repo.exists())


if __name__ == "__main__":
    unittest.main()
