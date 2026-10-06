"""Reuso de geração C03 verifica marcador, observação e tipos do manifesto."""

import copy
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

import duckdb

from etl.analytics.load import load_analytics
from etl.analytics.publish import publish_cubes
from etl.load.ddl import table_statements, view_statements
from etl.orchestration import analytics as analytics_module


class PublishedC03RetryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.database = root / "private.duckdb"
        self.output = root / "published"
        with duckdb.connect(str(self.database)) as con:
            for statement in (*table_statements(), *view_statements()):
                con.execute(statement)
            con.execute("""INSERT INTO _batch_metadata VALUES
                ('respondentes','r1','t1','b1','carregado',0,0,0,0,0,'1.0',
                 'empty-file',TIMESTAMP '2026-09-01',TIMESTAMP '2026-09-01')""")
            con.execute("""INSERT INTO _control_object VALUES
                ('respondentes','empty-file','r1',TIMESTAMP '2026-09-01')""")
            self.load_id = load_analytics(con, observed_at=datetime(2026, 9, 30, 23)).load_id
        event = mock.patch.object(analytics_module, "_event")
        self.event = event.start()
        self.addCleanup(event.stop)

    def run_task(self, output=None):
        return analytics_module.publish_warehouse.fn(
            str(self.database), str(output or self.output), self.load_id
        )

    def test_retry_after_empty_closure_pointer_switch_reuses_exact_generation(self):
        published = []

        def fail_after_publish(*args, **kwargs):
            published.append(publish_cubes(*args, **kwargs))
            raise RuntimeError("falha transitória depois da troca do ponteiro")

        with mock.patch.object(analytics_module, "publish_cubes", side_effect=fail_after_publish):
            with self.assertRaisesRegex(RuntimeError, "troca do ponteiro"):
                self.run_task()
        self.assertEqual(published[0]["tables"]["PUB_C03_PIPELINE_MENSAL"]["rows"], 1)
        with mock.patch.object(analytics_module, "publish_cubes") as publisher:
            reused = self.run_task()
        publisher.assert_not_called()
        self.assertEqual(reused, published[0])
        self.assertTrue(self.event.call_args.kwargs["reused"])
        self.assertEqual(len([path for path in self.output.iterdir() if path.is_dir()]), 1)

    def test_every_c03_semantic_field_is_verified_before_reuse(self):
        cases = {
            "observation_state": "not_observed",
            "fact_rows": 1,
            "empty_closure_rows": 0,
            "empty_closure_row_rule": "sem regra",
            "observed_months": [],
            "fact_rows_boolean": False,
            "empty_closure_rows_boolean": True,
            "month": "2026-10-31",
            "observed_at": "2026-09-30 22:00:00",
            "groups": 1,
            "stock": 1,
            "stock_boolean": False,
            "state": "observed_positive",
            "extra_month_field": "extra",
            "missing_field": None,
            "metadata_list": [],
        }
        for field, bad_value in cases.items():
            with self.subTest(field=field):
                output = self.output / field
                first = self.run_task(output)
                manifest_path = output / first["generation"] / "manifest.json"
                tampered = copy.deepcopy(first)
                c03 = tampered["tables"]["PUB_C03_PIPELINE_MENSAL"]
                if field in {"month", "observed_at", "groups", "stock", "state"}:
                    c03["observed_months"][0][field] = bad_value
                elif field == "stock_boolean":
                    c03["observed_months"][0]["stock"] = bad_value
                elif field == "extra_month_field":
                    c03["observed_months"][0]["extra"] = bad_value
                elif field == "missing_field":
                    del c03["observation_state"]
                elif field == "metadata_list":
                    tampered["tables"]["PUB_C03_PIPELINE_MENSAL"] = bad_value
                else:
                    c03[field.removesuffix("_boolean")] = bad_value
                manifest_path.write_text(json.dumps(tampered))
                repaired = self.run_task(output)
                self.assertNotEqual(first["generation"], repaired["generation"])
                self.assertFalse(self.event.call_args.kwargs["reused"])
                self.assertEqual(
                    repaired["tables"]["PUB_C03_PIPELINE_MENSAL"],
                    first["tables"]["PUB_C03_PIPELINE_MENSAL"],
                )


if __name__ == "__main__":
    unittest.main()
