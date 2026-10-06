"""Conferência independente da geração BI e do recibo do Desktop."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import duckdb

from etl.analytics.load import current_source_digests
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
            "load_reference": self.manifest["load_reference"],
            "tables": report["preparation"]["tables"],
            "aggregates": {
                "PUB_C01_CICLO": {"column": "qtd_pesquisas", "value": 4},
                "PUB_C02_PARTICIPACAO": {"column": "qtd_participacoes", "value": 4},
                "PUB_C03_PIPELINE_MENSAL": {
                    "column": "qtd_pesquisas_no_status",
                    "month_end": "2026-02-28",
                    "value": 4,
                },
                "PUB_C04_INSTRUMENTO": {"column": "qtd_perguntas", "value": 3},
            },
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

    def test_desktop_reference_binds_receipt_to_load(self) -> None:
        receipt = self._receipt()
        data = json.loads(receipt.read_text())
        for reference in ("different-load", None):
            with self.subTest(load_reference=reference):
                data["load_reference"] = reference
                receipt.write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, "Desktop: load_reference"):
                    conferir(self.generation, self.database, receipt, sintetico=True)
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
        data["aggregates"]["PUB_C02_PARTICIPACAO"]["value"] = 5
        receipt.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "agregado PUB_C02_PARTICIPACAO divergente"):
            conferir(self.generation, self.database, receipt, sintetico=True)

    def test_desktop_requires_four_aggregates_and_numeric_counts(self) -> None:
        receipt = self._receipt()
        data = json.loads(receipt.read_text())
        del data["aggregates"]["PUB_C04_INSTRUMENTO"]
        receipt.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "agregado por cubo"):
            conferir(self.generation, self.database, receipt, sintetico=True)
        data["aggregates"]["PUB_C04_INSTRUMENTO"] = {"column": "qtd_perguntas", "value": 3}
        data["tables"]["PUB_C01_CICLO"] = True
        receipt.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "contagens divergentes"):
            conferir(self.generation, self.database, receipt, sintetico=True)

    def test_c03_receipt_uses_one_observed_month(self) -> None:
        receipt = self._receipt()
        data = json.loads(receipt.read_text())
        data["aggregates"]["PUB_C03_PIPELINE_MENSAL"]["value"] = 7
        receipt.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "PUB_C03_PIPELINE_MENSAL divergente"):
            conferir(self.generation, self.database, receipt, sintetico=True)
        data["aggregates"]["PUB_C03_PIPELINE_MENSAL"]["month_end"] = "2026-03-31"
        receipt.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "fechamento C03 não observado"):
            conferir(self.generation, self.database, receipt, sintetico=True)

    def test_real_source_control_binds_reference_and_current_digests(self) -> None:
        con = duckdb.connect(str(self.database))
        for source, key in (
            ("pesquisas", "pesquisa_id"),
            ("empresas", "empresa_id"),
            ("clientes", "cliente_id"),
            ("questoes", "pergunta_id"),
        ):
            con.execute(f"ALTER TABLE ingestao_{source}_atual ADD COLUMN idempotency_key VARCHAR")
            con.execute(f"UPDATE ingestao_{source}_atual SET idempotency_key = {key}")
        digests = current_source_digests(con)
        con.execute(
            "CREATE TABLE _control_object (source VARCHAR, source_checksum VARCHAR, run_id VARCHAR, concluded_at TIMESTAMP)"
        )
        con.execute(
            "CREATE TABLE reconciliacao_execucao (run_id VARCHAR, conciliado BOOLEAN, status VARCHAR)"
        )
        con.execute("CREATE TABLE _batch_metadata (run_id VARCHAR, source VARCHAR, status VARCHAR)")
        con.execute(
            "CREATE TABLE analytics_load_run (load_id VARCHAR, loaded_at TIMESTAMP, pesquisas_digest VARCHAR, empresas_digest VARCHAR, clientes_digest VARCHAR, questoes_digest VARCHAR, respondentes_checksum VARCHAR)"
        )
        con.execute(
            "INSERT INTO analytics_load_run VALUES ('synthetic-bi02-fixture', now(), ?, ?, ?, ?, NULL)",
            [digests[source] for source in ("pesquisas", "empresas", "clientes", "questoes")],
        )
        con.close()
        report = conferir(self.generation, self.database, sintetico=True)
        self.assertEqual(report["preparation"]["source_control"]["status"], "confere")
        con = duckdb.connect(str(self.database))
        con.execute("UPDATE analytics_load_run SET load_id = 'another-load'")
        con.close()
        with self.assertRaisesRegex(ValueError, "load_reference diverge"):
            conferir(self.generation, self.database, sintetico=True)
        con = duckdb.connect(str(self.database))
        con.execute("UPDATE analytics_load_run SET load_id = 'synthetic-bi02-fixture'")
        con.execute("UPDATE analytics_load_run SET pesquisas_digest = 'bad'")
        con.close()
        with self.assertRaisesRegex(ValueError, "fonte pesquisas diverge"):
            conferir(self.generation, self.database, sintetico=True)

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
        receipt = self._receipt()
        original = json.loads(receipt.read_text())
        con = duckdb.connect(str(self.database))
        con.execute("DELETE FROM FATO_PIPELINE_MENSAL")
        con.close()
        root = Path(self.temp.name)
        manifest = publish_cubes(self.database, root / "empty", load_reference="synthetic-empty")
        generation = root / "empty" / manifest["generation"]
        result = conferir(generation, self.database, sintetico=True)
        self.assertEqual(result["preparation"]["c03_stock_by_month"], [])
        self.assertEqual(
            result["preparation"]["c03_observation"], "sem_fechamento_observado_na_publicacao"
        )
        original["generation"] = generation.name
        original["load_reference"] = manifest["load_reference"]
        original["tables"] = result["preparation"]["tables"]
        original["aggregates"]["PUB_C03_PIPELINE_MENSAL"] = {
            "column": "qtd_pesquisas_no_status",
            "state": "sem_fechamento_observado",
            "value": None,
        }
        receipt.write_text(json.dumps(original))
        self.assertEqual(
            conferir(generation, self.database, receipt, sintetico=True)["desktop"]["status"],
            "recibo_confere",
        )
        original["aggregates"]["PUB_C03_PIPELINE_MENSAL"]["value"] = 0
        receipt.write_text(json.dumps(original))
        with self.assertRaisesRegex(ValueError, "estado indisponível e valor nulo"):
            conferir(generation, self.database, receipt, sintetico=True)


if __name__ == "__main__":
    unittest.main()
