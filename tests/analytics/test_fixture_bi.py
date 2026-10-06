"""Contrato do pacote sintético usado no ensaio de importação BI-02."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import duckdb

from etl.analytics.publish import PUBLICATIONS
from scripts.analytics.gerar_fixture_bi import generate


class FixtureBITests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name) / "publication"
        self.manifest = generate(self.output)
        self.generation = self.output / self.manifest["generation"]
        self.reader = duckdb.connect(":memory:")
        self.addCleanup(self.reader.close)

    def rows(self, name, where=""):
        return self.reader.execute(
            f"SELECT * FROM read_parquet(?) {where}",
            [str(self.generation / f"{name}.parquet")],
        ).fetchall()

    def test_seven_files_match_manifest_hashes_counts_and_tmdl_columns(self):
        self.assertEqual(self.manifest["load_reference"], "synthetic-bi02-fixture")
        self.assertEqual(set(self.manifest["tables"]), set(PUBLICATIONS))
        self.assertEqual(
            {path.name for path in self.generation.iterdir()},
            {"manifest.json", *(f"{name}.parquet" for name in PUBLICATIONS)},
        )
        self.assertEqual(
            json.loads((self.output / "current.json").read_text())["generation"],
            self.manifest["generation"],
        )
        self.assertEqual(json.loads((self.generation / "manifest.json").read_text()), self.manifest)
        expected = {
            "PUB_C01_CICLO": 2,
            "PUB_C02_PARTICIPACAO": 3,
            "PUB_C03_PIPELINE_MENSAL": 4,
            "PUB_C04_INSTRUMENTO": 2,
            "PUB_QUALIDADE_CAMPO": 64,
            "PUB_QUALIDADE_RELACAO": 8,
            "PUB_QUALIDADE_DUPLICIDADE": 5,
        }
        model = (
            Path(__file__).resolve().parents[2]
            / "powerbi/CentralPesquisasBI.SemanticModel/definition/tables"
        )
        for name, entry in self.manifest["tables"].items():
            path = self.generation / entry["file"]
            self.assertEqual(entry["rows"], expected[name])
            self.assertEqual(entry["rows"], len(self.rows(name)))
            self.assertEqual(entry["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(
                entry["columns"],
                [
                    column[0]
                    for column in self.reader.execute(
                        "SELECT * FROM read_parquet(?) LIMIT 0", [str(path)]
                    ).description
                ],
            )
            tmdl = (model / f"{name}.tmdl").read_text()
            self.assertIn(f"\\{name}.parquet", tmdl)
            for column in entry["columns"]:
                self.assertIn(f"\tcolumn {column}\n", tmdl)
            for forbidden in (
                "source_checksum",
                "email",
                "enunciado",
                "respondent_id",
                "pesquisa_id",
            ):
                self.assertNotIn(forbidden, entry["columns"])

    def test_weighted_means_missing_dates_month_end_profiles_and_quality(self):
        c01 = self.rows("PUB_C01_CICLO", "WHERE area = 'Saúde'")[0]
        self.assertEqual(c01[3:6], (3, 10, 2))  # média ponderada: 10/2, não média de grupos
        self.assertEqual(c01[6:8], (10, 2))
        c01_empty = self.rows("PUB_C01_CICLO", "WHERE area = 'Educação'")[0]
        self.assertEqual(c01_empty[4:6], (None, 0))
        c02 = self.rows("PUB_C02_PARTICIPACAO", "ORDER BY mes_resposta NULLS LAST")
        self.assertEqual(
            [row[2].isoformat() if row[2] else None for row in c02],
            ["2026-01-01", "2026-03-01", None],
        )
        self.assertEqual(c02[0][3:], (2, 20, 2))
        self.assertEqual(c02[1][3:], (1, None, 0))
        self.assertEqual(c02[2][3:], (1, None, 0))
        c03 = self.rows("PUB_C03_PIPELINE_MENSAL", "ORDER BY data_fim_mes, area")
        self.assertEqual({row[0].isoformat() for row in c03}, {"2026-01-31", "2026-02-28"})
        self.assertEqual({row[6] for row in c03}, {1, 2, 3})
        self.assertTrue(all(row[7:] == (None, None) for row in c03))
        self.assertTrue(any(row[4] is None and row[5] == "Única" for row in c03))
        self.assertIn(("pesquisas", "data_aprov", 2, 1), self.rows("PUB_QUALIDADE_CAMPO"))
        self.assertIn(("clientes.empresa_id", 2, 1), self.rows("PUB_QUALIDADE_RELACAO"))
        self.assertIn(("pesquisas", 3, 2), self.rows("PUB_QUALIDADE_DUPLICIDADE"))

    def test_output_stays_outside_git_and_only_publication_is_delivered(self):
        inside = Path(__file__).resolve().parents[2] / "fixture-output"
        with self.assertRaisesRegex(ValueError, "fora de qualquer repositório Git"):
            generate(inside)
        self.assertFalse(inside.exists())
        self.assertFalse(any(path.suffix == ".duckdb" for path in self.output.rglob("*")))
        with self.assertRaises(duckdb.CatalogException):
            self.reader.execute("SELECT * FROM ingestao_pesquisas")

    def test_same_source_produces_identical_rows(self):
        second = generate(Path(self.temporary.name) / "second")
        for name in PUBLICATIONS:
            path = Path(self.temporary.name) / "second" / second["generation"] / f"{name}.parquet"
            other = self.reader.execute("SELECT * FROM read_parquet(?)", [str(path)]).fetchall()
            self.assertCountEqual(self.rows(name), other)


if __name__ == "__main__":
    unittest.main()
