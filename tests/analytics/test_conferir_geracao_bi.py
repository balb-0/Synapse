"""Conferência independente da geração BI e do recibo do Desktop."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import duckdb

from etl.analytics.publish import publish_cubes
from scripts.analytics.conferir_geracao_bi import conferir
from scripts.analytics.gerar_fixture_bi import create_database


class ConferirGeracaoBITest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="bi05-")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.database = root / "fonte.duckdb"
        create_database(self.database)
        self.manifest = publish_cubes(
            self.database, root / "publicacao", load_reference="synthetic-bi02-fixture"
        )
        self.generation = root / "publicacao" / self.manifest["generation"]

    def _write_manifest(self) -> None:
        (self.generation / "manifest.json").write_text(json.dumps(self.manifest))

    def _receipt(self) -> Path:
        report = conferir(self.generation, self.database, sintetico=True)
        receipt = {
            "generation": self.generation.name,
            "tables": report["preparation"]["tables"],
            "aggregate": {"table": "PUB_C01_CICLO", "column": "qtd_pesquisas", "value": 4},
        }
        target = Path(self.temp.name) / "desktop.json"
        target.write_text(json.dumps(receipt))
        return target

    def test_synthetic_must_be_explicit_and_never_final(self) -> None:
        with self.assertRaisesRegex(ValueError, "--sintetico"):
            conferir(self.generation, self.database)
        result = conferir(self.generation, self.database, self._receipt(), sintetico=True)
        self.assertEqual(result["preparation"]["status"], "ok")
        self.assertEqual(result["desktop"]["status"], "recibo_confere")
        self.assertEqual(result["final_acceptance"], "pendente")
        self.assertTrue(result["synthetic"])

    def test_wrong_hash_and_count(self) -> None:
        self.manifest["tables"]["PUB_C01_CICLO"]["sha256"] = "0" * 64
        self._write_manifest()
        with self.assertRaisesRegex(ValueError, "SHA256 divergente"):
            conferir(self.generation, self.database, sintetico=True)
        self.manifest["tables"]["PUB_C01_CICLO"]["sha256"] = self._original_hash()
        self.manifest["tables"]["PUB_C01_CICLO"]["rows"] += 1
        self._write_manifest()
        with self.assertRaisesRegex(ValueError, "contagem Parquet/manifesto"):
            conferir(self.generation, self.database, sintetico=True)

    def _original_hash(self) -> str:
        return hashlib.sha256((self.generation / "PUB_C01_CICLO.parquet").read_bytes()).hexdigest()

    def test_cube_aggregate_detects_rehashed_bad_values(self) -> None:
        path = self.generation / "PUB_C01_CICLO.parquet"
        changed = Path(self.temp.name) / "changed.parquet"
        con = duckdb.connect(":memory:")
        source = "'" + str(path).replace("'", "''") + "'"
        target = "'" + str(changed).replace("'", "''") + "'"
        con.execute(
            "COPY (SELECT * REPLACE (qtd_pesquisas + 1 AS qtd_pesquisas) "
            f"FROM read_parquet({source})) TO {target} (FORMAT PARQUET)",
        )
        con.close()
        path.write_bytes(changed.read_bytes())
        self.manifest["tables"]["PUB_C01_CICLO"]["sha256"] = self._original_hash()
        self._write_manifest()
        with self.assertRaisesRegex(ValueError, "agregado diverge"):
            conferir(self.generation, self.database, sintetico=True)

    def test_different_generation_and_bad_desktop_aggregate(self) -> None:
        receipt = self._receipt()
        data = json.loads(receipt.read_text())
        data["generation"] = "outra-geracao"
        receipt.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "geração diferente"):
            conferir(self.generation, self.database, receipt, sintetico=True)
        data["generation"] = self.generation.name
        data["aggregate"]["value"] = 5
        receipt.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "agregado divergente"):
            conferir(self.generation, self.database, receipt, sintetico=True)

    def test_c03_compares_each_month_without_summing_stock(self) -> None:
        result = conferir(self.generation, self.database, sintetico=True)
        self.assertEqual(
            result["preparation"]["c03_stock_by_month"],
            [
                {"month_end": "2026-01-31", "stock": 3},
                {"month_end": "2026-02-28", "stock": 4},
            ],
        )
        self.assertNotIn("PUB_C03_PIPELINE_MENSAL", result["preparation"]["aggregates"])

    def test_empty_stock_means_no_observed_close(self) -> None:
        con = duckdb.connect(str(self.database))
        con.execute("DELETE FROM FATO_PIPELINE_MENSAL")
        con.close()
        root = Path(self.temp.name)
        manifest = publish_cubes(self.database, root / "empty", load_reference="synthetic-empty")
        result = conferir(root / "empty" / manifest["generation"], self.database, sintetico=True)
        self.assertEqual(result["preparation"]["c03_stock_by_month"], [])
        self.assertEqual(
            result["preparation"]["c03_observation"], "sem_fechamento_observado_na_publicacao"
        )


if __name__ == "__main__":
    unittest.main()
