"""Regressões do verificador com DDL versionado e ingestão sintética."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

import duckdb

from etl.analytics.load import load_analytics
from etl.load.ddl import table_statements, view_statements
from scripts.analytics.verificar_metricas_cubos import main, verificar


class CubeMetricsVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / "fixture.duckdb"
        self.con = duckdb.connect(str(self.database))
        for statement in (*table_statements(), *view_statements()):
            self.con.execute(statement)
        self._insert_sources()
        self._select_respondents()

    def tearDown(self) -> None:
        if self.con is not None:
            self.con.close()

    def _insert(self, source: str, identity: str, offset: int, **business) -> None:
        values = {
            **business,
            "source": source,
            "run_id": "run-fixture",
            "task_id": "task-fixture",
            "batch_id": "batch-fixture",
            "source_checksum": "synthetic-file",
            "source_offset": offset,
            "content_checksum": f"content-{identity}",
            "record_identity": identity,
            "idempotency_key": identity,
            "ingested_at": datetime(2026, 9, 30, 12),
            "schema_version": "1.0",
        }
        columns = ", ".join(f'"{name}"' for name in values)
        marks = ", ".join("?" for _ in values)
        self.con.execute(
            f'INSERT INTO "ingestao_{source}" ({columns}) VALUES ({marks})',
            list(values.values()),
        )

    def _insert_sources(self) -> None:
        self._insert(
            "pesquisas",
            "research-one",
            1,
            pesquisa_id="p1",
            titulo="Pesquisa 1",
            status="Aberta",
            area="Área A",
            tipo="Tipo 1",
            complexidade="Alta",
            tipo_resposta="Aberta",
            data_solicitacao="2026-09-01",
            data_aprov="2026-09-03",
            data_divulgacao="2026-09-05",
            data_limite="2026-09-10",
            prorrogada_ate="2026-09-12",
            data_entrega="2026-09-15",
            participantes=3,
        )
        self._insert(
            "pesquisas",
            "research-two",
            2,
            pesquisa_id="p2",
            titulo="Pesquisa 2",
            status="Fechada",
        )
        self._insert("empresas", "company-one", 1, empresa_id="e1")
        self._insert("clientes", "person-one", 1, cliente_id="c1", empresa_id="e1")
        self._insert(
            "respondentes",
            "participation-one",
            1,
            pesquisa_id="p1",
            empresa_id="e1",
            cliente_id="c1",
            hora_inicio="2026-09-01 10:00:00.900000",
            hora_termino="2026-09-01 10:01:00.100000",
            market_share=12.5,
        )
        self._insert(
            "respondentes",
            "participation-two",
            2,
            pesquisa_id="p2",
            empresa_id="e1",
        )
        self._insert(
            "respondentes",
            "participation-three",
            3,
            pesquisa_id="p1",
            empresa_id="e1",
            cliente_id="c1",
            hora_inicio="2026-09-02 10:00:00",
            hora_termino="2026-09-02 10:05:00",
        )
        self._insert(
            "questoes",
            "question-one",
            1,
            pesquisa_id="p1",
            pergunta_id="q1",
            tipo="multipla",
            qtd_alternativas=3,
        )
        self._insert(
            "questoes",
            "question-two",
            2,
            pesquisa_id="p2",
            pergunta_id="q2",
            tipo="aberta",
        )

    def _select_respondents(self) -> None:
        finished = datetime(2026, 9, 30, 12)
        self.con.execute(
            """INSERT INTO _batch_metadata VALUES
            ('respondentes', 'run-fixture', 'task-fixture', 'batch-fixture',
             'carregado', 3, 3, 0, 0, 10, '1.0', 'synthetic-file', ?, ?)""",
            (finished, finished),
        )
        self.con.execute(
            "INSERT INTO _control_object VALUES (?, ?, ?, ?)",
            ("respondentes", "synthetic-file", "run-fixture", finished),
        )

    def _load(self, *, observed: bool = True) -> None:
        at = datetime(2026, 9, 30, 23) if observed else None
        load_analytics(self.con, observed_at=at)

    def test_synthetic_metrics_denominators_and_nulls_match(self) -> None:
        self._load()
        report = verificar(self.con)

        self.assertTrue(report["ok"])
        self.assertEqual(
            {cube: row["status"] for cube, row in report["cubes"].items()},
            {
                "C01": "ok",
                "C02": "ok",
                "C03": "ok",
                "C04": "ok",
            },
        )
        self.assertEqual(
            report["cubes"]["C01"]["metrics"]["dias_corridos_validacao"]["source"],
            {"sum": 2, "denominator": 1},
        )
        self.assertEqual(
            report["cubes"]["C02"]["metrics"]["minutos_preenchimento"]["source"],
            {"sum": 5, "denominator": 2},
        )
        self.assertEqual(
            report["cubes"]["C03"]["months"][0]["stock"],
            {
                "source": 2,
                "fact": 2,
            },
        )
        self.assertIsNone(report["cubes"]["C03"]["months"][0]["entries"])
        self.assertEqual(
            report["cubes"]["C04"]["metrics"]["qtd_perguntas"],
            {
                "source": 2,
                "fact": 2,
            },
        )
        self.assertNotIn('"p1"', json.dumps(report))

    def test_changes_in_cycle_and_participation_measures_fail(self) -> None:
        self._load()
        self.con.execute("UPDATE FATO_CICLO_PESQUISA SET dias_corridos_validacao = 99")
        self.con.execute("""UPDATE FATO_PARTICIPACAO SET minutos_preenchimento = 6
            WHERE source_offset = 3""")
        report = verificar(self.con)

        self.assertFalse(report["ok"])
        self.assertEqual(report["cubes"]["C01"]["status"], "mismatch")
        self.assertGreater(report["cubes"]["C01"]["field_mismatches"]["dias_corridos_validacao"], 0)
        self.assertEqual(report["cubes"]["C02"]["status"], "mismatch")
        self.assertEqual(
            report["cubes"]["C02"]["metrics"]["minutos_preenchimento"]["fact"],
            {"sum": 6, "denominator": 2},
        )
        self.con.close()
        self.con = None
        with redirect_stdout(io.StringIO()) as output:
            exit_code = main([str(self.database)])
        self.assertEqual(exit_code, 1)
        self.assertFalse(json.loads(output.getvalue())["ok"])

    def test_wrong_pipeline_stock_and_missing_question_fail(self) -> None:
        self._load()
        self.con.execute("UPDATE FATO_PIPELINE_MENSAL SET qtd_pesquisas_no_status = 5")
        self.con.execute("UPDATE FATO_PIPELINE_MENSAL SET qtd_entradas_no_mes = 1")
        self.con.execute("DELETE FROM FATO_PESQUISA_PERGUNTA WHERE pergunta_id_origem = 'q2'")
        report = verificar(self.con)

        self.assertFalse(report["ok"])
        self.assertEqual(report["cubes"]["C03"]["months"][0]["status"], "mismatch")
        self.assertGreater(report["cubes"]["C03"]["months"][0]["stock_mismatches"], 0)
        self.assertGreater(report["cubes"]["C03"]["months"][0]["flows_without_source"], 0)
        self.assertEqual(report["cubes"]["C04"]["missing_grains"], 1)

    def test_unobserved_month_is_null_and_new_source_invalidates_closure(self) -> None:
        self._load(observed=False)
        report = verificar(self.con)
        self.assertTrue(report["ok"])
        self.assertEqual(report["cubes"]["C03"]["status"], "not_observed")
        self.assertIsNone(report["cubes"]["C03"]["stock"])

        self._load()
        self._insert("pesquisas", "research-three", 3, pesquisa_id="p3")
        stale = verificar(self.con)
        self.assertFalse(stale["ok"])
        self.assertEqual(
            stale["cubes"]["C03"]["months"][0]["status"],
            "source_snapshot_unavailable",
        )

    def test_observed_empty_month_has_zero_stock_and_null_sums(self) -> None:
        self.con.close()
        self.con = duckdb.connect(str(self.database))
        for table in (
            "ingestao_pesquisas",
            "ingestao_empresas",
            "ingestao_clientes",
            "ingestao_respondentes",
            "ingestao_questoes",
        ):
            self.con.execute(f"DELETE FROM {table}")
        self.con.execute("DELETE FROM _batch_metadata")
        self.con.execute("DELETE FROM _control_object")
        self.con.execute("""INSERT INTO _batch_metadata VALUES
            ('respondentes', 'empty-run', 'task', 'batch', 'carregado',
             0, 0, 0, 0, 10, '1.0', 'empty-file',
             '2026-09-30 12:00:00', '2026-09-30 12:00:00')""")
        self.con.execute("""INSERT INTO _control_object VALUES
            ('respondentes', 'empty-file', 'empty-run', '2026-09-30 12:00:00')""")
        self._load()
        report = verificar(self.con)

        self.assertTrue(report["ok"])
        self.assertEqual(report["cubes"]["C03"]["status"], "ok")
        self.assertEqual(
            report["cubes"]["C03"]["months"][0]["stock"],
            {
                "source": 0,
                "fact": 0,
            },
        )
        self.assertEqual(
            report["cubes"]["C01"]["metrics"]["dias_corridos_validacao"]["source"],
            {"sum": None, "denominator": 0},
        )
        self.assertEqual(
            report["cubes"]["C02"]["metrics"]["minutos_preenchimento"]["source"],
            {"sum": None, "denominator": 0},
        )

    def test_missing_respondent_snapshot_blocks_and_cli_exits_one(self) -> None:
        self.con.execute("DELETE FROM _control_object")
        self._load(observed=False)
        report = verificar(self.con)
        self.assertFalse(report["ok"])
        self.assertEqual(report["cubes"]["C02"]["status"], "source_unavailable")

        self.con.close()
        self.con = None
        output = io.StringIO()
        with redirect_stdout(output):
            code = main([str(self.database)])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(output.getvalue())["ok"])

    def test_observed_load_without_closure_marker_is_not_unobserved(self) -> None:
        self._load(observed=False)
        self.con.execute("""UPDATE analytics_load_run SET observed_at = '2026-09-30 23:00:00'""")
        report = verificar(self.con)
        self.assertFalse(report["ok"])
        self.assertEqual(report["cubes"]["C03"]["status"], "mismatch")
        self.assertEqual(report["cubes"]["C03"]["missing_closure_markers"], 1)


if __name__ == "__main__":
    unittest.main()
