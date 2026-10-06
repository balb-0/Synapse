"""A publicação conserva fechamento vazio sem inventar grupos ou observações."""

import json
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

import duckdb

from etl.analytics.load import load_analytics
from etl.analytics.publish import publish_cubes
from etl.analytics.reconcile import reconcile_analytics
from etl.load.ddl import table_statements, view_statements


class PublishedMonthlyClosuresTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.database = root / "private.duckdb"
        self.output = root / "published"
        with duckdb.connect(str(self.database)) as con:
            for statement in (*table_statements(), *view_statements()):
                con.execute(statement)
            # Um snapshot de respondentes vazio e conciliado é diferente de uma
            # fonte ausente. Nenhum registro individual é necessário neste teste.
            con.execute("""INSERT INTO _batch_metadata VALUES
                ('respondentes','r1','t1','b1','carregado',0,0,0,0,0,'1.0',
                 'empty-file',TIMESTAMP '2026-09-01',TIMESTAMP '2026-09-01')""")
            con.execute("""INSERT INTO _control_object VALUES
                ('respondentes','empty-file','r1',TIMESTAMP '2026-09-01')""")

    def insert_research(self, identity, **attributes):
        values = {
            "pesquisa_id": identity,
            **attributes,
            "source": "pesquisas",
            "run_id": "r1",
            "task_id": "t1",
            "batch_id": "research-batch",
            "source_checksum": "research-file",
            "source_offset": int(identity[-1]),
            "content_checksum": identity,
            "record_identity": identity,
            "idempotency_key": identity,
            "ingested_at": datetime(2026, 9, 1),
            "schema_version": "1.0",
        }
        columns = ", ".join(f'"{name}"' for name in values)
        with duckdb.connect(str(self.database)) as con:
            con.execute(
                f"INSERT INTO ingestao_pesquisas ({columns}) "
                f"VALUES ({', '.join('?' for _ in values)})",
                list(values.values()),
            )

    def load(self, observed_at=None):
        with duckdb.connect(str(self.database)) as con:
            result = load_analytics(con, observed_at=observed_at)
            report = reconcile_analytics(con)
            self.assertTrue(report.reconciled, report.as_dict())
        return result, report

    def publish(self, load_id):
        manifest = publish_cubes(self.database, self.output, load_reference=load_id)
        generation = self.output / manifest["generation"]
        self.assertEqual(len(list(generation.glob("*.parquet"))), 7)
        self.assertEqual(json.loads((generation / "manifest.json").read_text()), manifest)
        with duckdb.connect() as con:
            rows = con.execute(
                "SELECT * FROM read_parquet(?) ORDER BY data_fim_mes, area NULLS FIRST",
                [str(generation / "PUB_C03_PIPELINE_MENSAL.parquet")],
            ).fetchall()
        return manifest["tables"]["PUB_C03_PIPELINE_MENSAL"], rows

    def test_no_observation_is_unavailable_even_with_current_research(self):
        self.insert_research("p1", status="Aberta")
        result, report = self.load()
        table, rows = self.publish(result.load_id)
        self.assertEqual(report.cubes[2].status, "not_observed")
        self.assertEqual(rows, [])
        self.assertEqual(table["observation_state"], "not_observed")
        self.assertEqual(table["observed_months"], [])
        self.assertEqual(
            (table["fact_rows"], table["empty_closure_rows"], table["rows"]), (0, 0, 0)
        )

    def test_observed_empty_month_has_one_zero_marker_and_no_fact_group(self):
        at = datetime(2026, 9, 30, 23)
        result, report = self.load(at)
        table, rows = self.publish(result.load_id)
        self.assertEqual(rows, [(date(2026, 9, 30), None, None, None, None, None, 0, None, None)])
        self.assertEqual(table["observation_state"], "observed")
        self.assertEqual(
            (table["fact_rows"], table["empty_closure_rows"], table["rows"]), (0, 1, 1)
        )
        self.assertEqual(
            table["observed_months"],
            [
                {
                    "month": "2026-09-30",
                    "observed_at": "2026-09-30 23:00:00",
                    "groups": 0,
                    "stock": 0,
                    "state": "observed_zero",
                }
            ],
        )
        self.assertEqual((report.cubes[2].eligible, report.cubes[2].loaded), (0, 0))
        self.assertEqual(
            table["columns"],
            [
                "data_fim_mes",
                "status",
                "area",
                "tipo",
                "complexidade",
                "tipo_resposta",
                "qtd_pesquisas_no_status",
                "qtd_entradas_no_mes",
                "qtd_saidas_no_mes",
            ],
        )

    def test_unknown_positive_group_is_not_an_empty_closure(self):
        self.insert_research("p1")
        self.insert_research("p2")
        result, report = self.load(datetime(2026, 9, 30, 23))
        table, rows = self.publish(result.load_id)
        self.assertEqual(rows, [(date(2026, 9, 30), None, None, None, None, None, 2, None, None)])
        self.assertEqual((table["fact_rows"], table["empty_closure_rows"]), (1, 0))
        self.assertEqual(table["observed_months"][0]["state"], "observed_positive")
        self.assertEqual((report.cubes[2].eligible, report.cubes[2].loaded), (2, 2))

    def test_same_observation_reload_preserves_zero_and_newer_observation_replaces_it(self):
        at = datetime(2026, 9, 30, 22)
        first, _ = self.load(at)
        initial_table, initial_rows = self.publish(first.load_id)
        self.insert_research("p1", area="Saúde", status="Aberta", tipo="Mercado")
        same, _ = self.load(at)
        same_table, same_rows = self.publish(same.load_id)
        self.assertEqual(same_rows, initial_rows)
        self.assertEqual(same_table["observed_months"], initial_table["observed_months"])
        newer, _ = self.load(datetime(2026, 9, 30, 23))
        table, rows = self.publish(newer.load_id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1:4], ("aberta", "saúde", "mercado"))
        self.assertEqual(rows[0][6], 1)
        self.assertEqual((table["fact_rows"], table["empty_closure_rows"]), (1, 0))

    def test_global_month_sum_distinguishes_zero_positive_and_missing_month(self):
        self.load(datetime(2026, 9, 30, 23))
        self.insert_research("p1", area="Saúde", status="Aberta")
        result, _ = self.load(datetime(2026, 10, 31, 23))
        table, _ = self.publish(result.load_id)
        parquet = (
            self.output
            / json.loads((self.output / "current.json").read_text())["generation"]
            / table["file"]
        )
        with duckdb.connect() as con:
            stocks = [
                con.execute(
                    "SELECT sum(qtd_pesquisas_no_status) FROM read_parquet(?) WHERE data_fim_mes=?",
                    [str(parquet), month],
                ).fetchone()[0]
                for month in ("2026-09-30", "2026-10-31", "2026-11-30")
            ]
            filtered_zero = con.execute(
                "SELECT sum(qtd_pesquisas_no_status) FROM read_parquet(?) "
                "WHERE data_fim_mes=DATE '2026-09-30' AND area='saúde'",
                [str(parquet)],
            ).fetchone()[0]
            filtered_positive = con.execute(
                "SELECT sum(qtd_pesquisas_no_status) FROM read_parquet(?) "
                "WHERE data_fim_mes=DATE '2026-10-31' AND area='saúde'",
                [str(parquet)],
            ).fetchone()[0]
        self.assertEqual(stocks, [0, 1, None])
        self.assertIsNone(filtered_zero)  # O marcador global não cria recortes de grupo.
        self.assertEqual(filtered_positive, 1)
        self.assertEqual(
            (table["fact_rows"], table["empty_closure_rows"], table["rows"]), (1, 1, 2)
        )

    def test_unreconciled_closure_does_not_publish_zero_or_switch_pointer(self):
        result, _ = self.load(datetime(2026, 9, 30, 23))
        self.publish(result.load_id)
        pointer_before = (self.output / "current.json").read_text()
        with duckdb.connect(str(self.database)) as con:
            con.execute("DELETE FROM analytics_pipeline_closure")
        with self.assertRaisesRegex(ValueError, "não reconciliou"):
            publish_cubes(self.database, self.output, load_reference=result.load_id)
        self.assertEqual((self.output / "current.json").read_text(), pointer_before)
        self.assertFalse(list(self.output.glob(".pending-*")))


if __name__ == "__main__":
    unittest.main()
