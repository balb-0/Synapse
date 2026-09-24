"""Reconciliation checks against persisted DuckDB facts and source views."""

import unittest
from datetime import datetime

import duckdb
from etl.analytics.load import load_analytics

from etl.analytics.reconcile import reconcile_analytics
from etl.load.ddl import table_statements, view_statements


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.con = duckdb.connect()
        for statement in (*table_statements(), *view_statements()):
            self.con.execute(statement)

    def tearDown(self):
        self.con.close()

    def insert(self, source, identity, offset, *, checksum="file1", run="r1", **business):
        values = {
            **business,
            "source": source,
            "run_id": run,
            "task_id": "t1",
            "batch_id": "b1",
            "source_checksum": checksum,
            "source_offset": offset,
            "content_checksum": f"c{identity}",
            "record_identity": identity,
            "idempotency_key": identity,
            "ingested_at": datetime(2026, 9, 1),
            "schema_version": "1.0",
        }
        columns = ", ".join(f'"{name}"' for name in values)
        self.con.execute(
            f'INSERT INTO "ingestao_{source}" ({columns}) '
            f"VALUES ({', '.join('?' for _ in values)})",
            list(values.values()),
        )

    def select_respondents(self, checksum="file1", run="r1", finished=None):
        finished = finished or datetime(2026, 9, 1)
        count = self.con.execute(
            """SELECT count(*) FROM "ingestao_respondentes"
            WHERE source_checksum = ?""",
            (checksum,),
        ).fetchone()[0]
        self.con.execute(
            """INSERT INTO "_batch_metadata" VALUES
            ('respondentes', ?, 'task', ?, 'carregado', ?, ?, 0, 0, 10,
             '1.0', ?, ?, ?)""",
            (run, f"{run}-batch", count, count, checksum, finished, finished),
        )
        self.con.execute(
            'INSERT INTO "_control_object" VALUES (?, ?, ?, ?)',
            ("respondentes", checksum, run, finished),
        )

    def test_four_cubes_and_orphan_log(self):
        self.insert("pesquisas", "p1", 1, pesquisa_id="p1", titulo="Pesquisa")
        self.insert("empresas", "e1", 1, empresa_id="e1")
        self.insert("respondentes", "r1", 1, pesquisa_id="p1", empresa_id="ausente")
        self.insert("questoes", "q1", 1, pesquisa_id="sem-vinculo", pergunta_id="q1", tipo="aberta")
        self.select_respondents()
        load_analytics(self.con, observed_at=datetime(2026, 9, 30, 23))

        report = reconcile_analytics(self.con)
        self.assertTrue(report.reconciled)
        self.assertEqual(
            [(c.cube, c.eligible, c.loaded, c.difference) for c in report.cubes],
            [("C01", 1, 1, 0), ("C02", 1, 1, 0), ("C03", 1, 1, 0), ("C04", 1, 1, 0)],
        )
        self.assertEqual(report.monthly_closures[0]["stock"], 1)
        self.assertEqual(
            {row["reason"] for row in report.orphan_reasons},
            {"empresa_id_ausente", "pesquisa_nao_encontrada"},
        )
        self.assertTrue(all(row["expected"] == row["logged"] for row in report.orphan_audit))
        self.assertEqual(report, reconcile_analytics(self.con))

        self.con.execute("""DELETE FROM "analytics_reconciliation"
            WHERE reason = 'empresa_id_ausente' """)
        damaged = reconcile_analytics(self.con)
        self.assertFalse(damaged.reconciled)
        self.assertEqual(damaged.orphan_audit[1]["expected"], 1)
        self.assertEqual(damaged.orphan_audit[1]["logged"], 0)

    def test_equal_count_with_wrong_member_is_mismatch(self):
        self.insert("pesquisas", "p1", 1, pesquisa_id="p1")
        load_analytics(self.con)
        self.con.execute('DELETE FROM "ingestao_pesquisas" WHERE pesquisa_id = ?', ("p1",))
        self.insert("pesquisas", "p2", 2, pesquisa_id="p2")
        report = reconcile_analytics(self.con)
        self.assertFalse(report.reconciled)
        self.assertEqual(report.cubes[0].missing_keys, 1)
        self.assertEqual(report.cubes[0].unexpected_keys, 1)
        self.assertEqual(report.cubes[0].difference, 0)

    def test_manifest_catches_changed_content_at_the_same_grain(self):
        self.insert("pesquisas", "p1-a", 1, pesquisa_id="p1", titulo="Anterior")
        load_analytics(self.con)
        self.insert("pesquisas", "p1-b", 2, pesquisa_id="p1", titulo="Corrigido")
        report = reconcile_analytics(self.con)
        self.assertEqual(report.cubes[0].difference, 0)
        self.assertFalse(report.source_digests_match)
        self.assertFalse(report.reconciled)
        load_analytics(self.con)
        self.assertTrue(reconcile_analytics(self.con).source_digests_match)

    def test_old_snapshot_is_not_counted_as_current_participation(self):
        self.insert("pesquisas", "p1", 1, pesquisa_id="p1")
        self.insert("empresas", "e1", 1, empresa_id="e1")
        self.insert("respondentes", "old", 1, pesquisa_id="p1", empresa_id="e1")
        self.select_respondents()
        load_analytics(self.con)
        self.insert(
            "respondentes", "new", 1, checksum="file2", run="r2", pesquisa_id="p1", empresa_id="e1"
        )
        self.select_respondents("file2", "r2", datetime(2026, 9, 2))
        stale = reconcile_analytics(self.con)
        self.assertFalse(stale.reconciled)
        self.assertEqual(stale.cubes[1].unexpected_keys, 1)
        self.assertEqual(stale.cubes[1].missing_keys, 1)
        load_analytics(self.con)
        self.assertTrue(reconcile_analytics(self.con).reconciled)

    def test_no_reconciled_respondent_snapshot_is_unavailable(self):
        self.insert("pesquisas", "p1", 1, pesquisa_id="p1")
        load_analytics(self.con)
        report = reconcile_analytics(self.con)
        self.assertEqual(report.cubes[1].status, "source_unavailable")
        self.assertIsNone(report.cubes[1].eligible)
        self.assertEqual(report.cubes[2].status, "not_observed")
        self.assertIsNone(report.cubes[2].eligible)
        self.assertFalse(report.reconciled)

    def test_failed_reload_leaves_detectable_current_source_difference(self):
        self.insert("pesquisas", "p1", 1, pesquisa_id="p1", titulo="Primeira")
        load_analytics(self.con)
        self.insert("pesquisas", "p2", 2, pesquisa_id="p2", titulo="Nova")
        with self.assertRaisesRegex(RuntimeError, "injected"):
            load_analytics(self.con, fail_after="facts")
        report = reconcile_analytics(self.con)
        self.assertFalse(report.reconciled)
        self.assertEqual(report.cubes[0].difference, 1)
        self.assertEqual(report.cubes[0].missing_keys, 1)

    def test_monthly_history_survives_current_source_change_and_detects_tampering(self):
        self.insert("pesquisas", "p1", 1, pesquisa_id="p1", status="Aberta")
        self.insert("empresas", "e1", 1, empresa_id="e1")
        self.insert("respondentes", "r1", 1, pesquisa_id="p1", empresa_id="e1")
        self.select_respondents()
        load_analytics(self.con, observed_at=datetime(2026, 9, 30, 23))
        self.insert("pesquisas", "p2", 2, pesquisa_id="p2", status="Fechada")
        load_analytics(self.con)
        report = reconcile_analytics(self.con)
        self.assertEqual(report.cubes[2].eligible, 1)
        self.assertEqual(report.cubes[2].loaded, 1)
        self.assertTrue(report.reconciled)

        self.con.execute("""UPDATE "FATO_PIPELINE_MENSAL"
            SET qtd_pesquisas_no_status = 2""")
        damaged = reconcile_analytics(self.con)
        self.assertFalse(damaged.reconciled)
        self.assertEqual(damaged.cubes[2].difference, -1)


if __name__ == "__main__":
    unittest.main()
