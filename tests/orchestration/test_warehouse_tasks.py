"""Regressões DW: retry real, publicação íntegra e preservação de checkpoints."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

import duckdb
from prefect import flow

from etl.orchestration import analytics as analytics_module
from etl.orchestration import flow as flow_module
from etl.orchestration.lock import database_lock
from etl.orchestration.pipeline import PipelineAbortedError, ReconciliationFailedError, run_pipeline
from tests import fixtures
from tests.orchestration.test_orchestration_logs import AMBIENTE_FICTICIO, LeitorEmMemoria


class WarehouseTasksTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.database = self.root / "warehouse.duckdb"
        self.output = self.root / "published"
        reader = LeitorEmMemoria(
            {source: fixtures.payload(source) for source in fixtures.ORDEM_CARGA}
        )
        for patcher in (
            mock.patch.dict(os.environ, AMBIENTE_FICTICIO),
            mock.patch.object(flow_module, "MinioObjectReader", lambda client: reader),
            mock.patch.object(flow_module, "get_run_logger", return_value=mock.Mock()),
            mock.patch.object(flow_module, "_current_task_id", return_value="synthetic-task"),
            mock.patch.object(analytics_module, "get_run_logger", return_value=mock.Mock()),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def prepare_ingestion(self) -> None:
        # Sem rede/servidor Prefect neste preparo, mas extratores, validação,
        # reconciliação, commits e checkpoints usam a implementação e DuckDB.
        with (
            mock.patch.object(flow_module, "extract", flow_module.extract.fn),
            mock.patch.object(flow_module, "transform", flow_module.transform.fn),
            mock.patch.object(flow_module, "load", flow_module.load.fn),
        ):
            for source in fixtures.ORDEM_CARGA:
                flow_module.ingest_object.fn(
                    source, "landing-test", f"landing/{source}.csv", db_path=str(self.database)
                )

    def prepare_analytics(self) -> str:
        self.prepare_ingestion()
        loaded = analytics_module.load_warehouse.fn(str(self.database))
        return loaded["load_id"]

    def test_task_retry_after_atomic_pointer_switch_reuses_one_generation(self) -> None:
        load_id = self.prepare_analytics()
        actual = analytics_module.publish_cubes
        calls = 0

        def fail_after_publish(*args, **kwargs):
            nonlocal calls
            calls += 1
            actual(*args, **kwargs)
            raise RuntimeError("falha transitória depois da publicação")

        @flow
        def attempt():
            return analytics_module.publish_warehouse(str(self.database), str(self.output), load_id)

        with mock.patch.object(analytics_module, "publish_cubes", side_effect=fail_after_publish):
            result = attempt()
        self.assertEqual(calls, 1)
        self.assertEqual(result["load_reference"], load_id)
        self.assertEqual(len([path for path in self.output.iterdir() if path.is_dir()]), 1)
        self.assertEqual(
            json.loads((self.output / "current.json").read_text())["generation"],
            result["generation"],
        )

    def test_equal_counts_with_changed_values_do_not_reuse_generation(self) -> None:
        load_id = self.prepare_analytics()
        first = analytics_module.publish_warehouse.fn(str(self.database), str(self.output), load_id)
        with duckdb.connect(str(self.database)) as connection:
            connection.execute('UPDATE "FATO_CICLO_PESQUISA" SET dias_corridos_ciclo_total=999')
        second = analytics_module.publish_warehouse.fn(
            str(self.database), str(self.output), load_id
        )
        self.assertNotEqual(first["generation"], second["generation"])

    def test_modified_parquet_hash_prevents_reuse(self) -> None:
        load_id = self.prepare_analytics()
        first = analytics_module.publish_warehouse.fn(str(self.database), str(self.output), load_id)
        table = next(iter(first["tables"]))
        target = self.output / first["generation"] / first["tables"][table]["file"]
        target.write_bytes(target.read_bytes() + b"corruption")
        second = analytics_module.publish_warehouse.fn(
            str(self.database), str(self.output), load_id
        )
        self.assertNotEqual(first["generation"], second["generation"])
        repaired = self.output / second["generation"] / second["tables"][table]["file"]
        self.assertEqual(
            hashlib.sha256(repaired.read_bytes()).hexdigest(), second["tables"][table]["sha256"]
        )

    def test_reconciliation_failure_does_not_publish_and_ingestion_remains_complete(self) -> None:
        load_id = self.prepare_analytics()
        with duckdb.connect(str(self.database)) as connection:
            connection.execute('DELETE FROM "FATO_CICLO_PESQUISA"')
        with self.assertRaises(ValueError):
            analytics_module.reconcile_warehouse.fn(str(self.database), load_id)
        with self.assertRaises(ValueError):
            analytics_module.publish_warehouse.fn(str(self.database), str(self.output), load_id)
        self.assertFalse(self.output.exists())
        with duckdb.connect(str(self.database), read_only=True) as connection:
            self.assertEqual(
                connection.execute("SELECT count(*) FROM _control_object").fetchone()[0], 6
            )
        repaired = analytics_module.load_warehouse.fn(str(self.database))
        report = analytics_module.reconcile_warehouse.fn(str(self.database), repaired["load_id"])
        self.assertTrue(report["reconciled"])

    def test_partial_empty_duplicate_and_unknown_source_sets_fail_before_ingestion(self) -> None:
        from etl.orchestration import pipeline as pipeline_module

        with (
            mock.patch.object(pipeline_module, "get_run_logger", return_value=mock.Mock()),
            mock.patch.object(pipeline_module, "backfill") as backfill,
        ):
            for sources in ([], ["empresas"], [*fixtures.ORDEM_CARGA, "empresas"], ["unknown"]):
                with self.subTest(sources=sources), self.assertRaises(ValueError):
                    run_pipeline.fn(sources, publish_dir=self.output, db_path=str(self.database))
            backfill.assert_not_called()

    def test_missing_backfill_result_fails_before_analytics(self) -> None:
        from etl.orchestration import pipeline as pipeline_module

        with (
            mock.patch.object(pipeline_module, "get_run_logger", return_value=mock.Mock()),
            mock.patch.object(pipeline_module, "backfill", return_value={"results": []}),
            mock.patch.object(pipeline_module, "load_warehouse") as loader,
        ):
            with self.assertRaises(PipelineAbortedError):
                run_pipeline.fn(publish_dir=self.output, db_path=str(self.database))
            loader.assert_not_called()

    def test_retry_policy_rejects_permanent_duckdb_errors_and_permissions(self) -> None:
        for error in (
            duckdb.CatalogException("missing table"),
            PermissionError("denied"),
            FileExistsError("output is a file"),
            TypeError("invalid parameter"),
        ):
            state = mock.Mock()
            state.result.side_effect = error
            self.assertFalse(flow_module._should_retry(None, None, state))
        for task in (
            analytics_module.load_warehouse,
            analytics_module.reconcile_warehouse,
            analytics_module.publish_warehouse,
        ):
            self.assertEqual(task.retries, 2)
            self.assertIs(task.retry_condition_fn, flow_module._should_retry)
            self.assertEqual(task.timeout_seconds, 3600)

    def test_invalid_report_gate_logs_failure_without_overwriting_stage(self) -> None:
        from etl.orchestration import pipeline as pipeline_module

        completed = [{"source": source, "status": "loaded"} for source in fixtures.ORDEM_CARGA]
        for report in (
            {"reconciled": False, "load_id": "this-load"},
            {"reconciled": True, "load_id": "another-load"},
        ):
            with (
                self.subTest(report=report),
                mock.patch.object(pipeline_module, "get_run_logger", return_value=mock.Mock()),
                mock.patch.object(pipeline_module, "backfill", return_value={"results": completed}),
                mock.patch.object(
                    pipeline_module, "load_warehouse", return_value={"load_id": "this-load"}
                ),
                mock.patch.object(pipeline_module, "reconcile_warehouse", return_value=report),
                mock.patch.object(pipeline_module, "publish_warehouse") as publisher,
                mock.patch.object(pipeline_module, "_log_event") as event,
                self.assertRaises(ReconciliationFailedError),
            ):
                run_pipeline.fn(publish_dir=self.output, db_path=str(self.database))
            publisher.assert_not_called()
            self.assertEqual(event.call_args.kwargs["status"], "reconciliation_failed")
            self.assertEqual(event.call_args.kwargs["failed_stage"], "reconciliation")
            self.assertNotIn("stage", event.call_args.kwargs)

    def test_lock_wait_is_bounded_between_threads_and_released_on_failure(self) -> None:
        outcomes = []

        def contender():
            try:
                with database_lock(self.database, 0.01):
                    outcomes.append("acquired")
            except TimeoutError:
                outcomes.append("timed_out")

        with self.assertRaisesRegex(RuntimeError, "failure"):
            with database_lock(self.database, 1):
                other = threading.Thread(target=contender)
                other.start()
                other.join(timeout=1)
                self.assertFalse(other.is_alive())
                self.assertEqual(outcomes, ["timed_out"])
                raise RuntimeError("failure")
        with database_lock(self.database, 0.01):
            outcomes.append("acquired")
        self.assertEqual(outcomes, ["timed_out", "acquired"])


if __name__ == "__main__":
    unittest.main()
