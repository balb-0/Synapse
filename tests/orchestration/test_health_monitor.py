"""Sinal de saúde periódico: limite de execução, falha explícita e retomada."""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
SPEC = importlib.util.spec_from_file_location(
    "health_monitor", ROOT / "scripts/orchestration/health_monitor.py"
)
assert SPEC is not None and SPEC.loader is not None
health_monitor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(health_monitor)


class PeriodicHealthMonitorTests(unittest.TestCase):
    def test_forwards_one_report_and_accepts_degraded_exit_without_duplicating(self) -> None:
        for status, exit_code in (("ok", 0), ("degraded", 1), ("busy", 2)):
            with self.subTest(status=status):
                payload = {"event": health_monitor.HEALTH_CHECK_EVENT, "status": status}
                result = subprocess.CompletedProcess([], exit_code, json.dumps(payload) + "\n", "")
                stream = io.StringIO()
                with (
                    mock.patch.object(health_monitor.subprocess, "run", return_value=result) as run,
                    redirect_stdout(stream),
                ):
                    health_monitor.check_once(30)
                self.assertEqual(
                    [json.loads(line) for line in stream.getvalue().splitlines()], [payload]
                )
                self.assertEqual(run.call_args.kwargs["timeout"], 30)
                self.assertIn("--json-only", run.call_args.args[0])

    def test_timeout_is_an_explicit_degraded_event(self) -> None:
        with (
            mock.patch.object(
                health_monitor.subprocess,
                "run",
                side_effect=subprocess.TimeoutExpired("health", 30),
            ),
            self.assertLogs("etl.orchestration", level="ERROR") as records,
        ):
            health_monitor.check_once(30)
        event = records.records[0]
        self.assertEqual(event.event, health_monitor.HEALTH_CHECK_EVENT)
        self.assertEqual(event.status, "degraded")
        self.assertIn("30 segundos", event.monitor_detail)
        self.assertGreaterEqual(event.duration_ms, 0)
        # Sem resultado do subprocess, não afirmar disponibilidade de API/banco.
        self.assertFalse(hasattr(event, "prefect_available"))

    def test_missing_corrupted_or_inconsistent_reports_fail_closed(self) -> None:
        for output, code in (
            ("", 0),
            ("{invalid}", 1),
            (json.dumps({"event": health_monitor.HEALTH_CHECK_EVENT, "status": "ok"}), 1),
            (json.dumps({"event": health_monitor.HEALTH_CHECK_EVENT, "status": "unknown"}), 0),
        ):
            with self.subTest(output=output, code=code):
                result = subprocess.CompletedProcess([], code, output, "error")
                with (
                    mock.patch.object(health_monitor.subprocess, "run", return_value=result),
                    self.assertLogs("etl.orchestration", level="ERROR") as records,
                ):
                    health_monitor.check_once(30)
                self.assertEqual(records.records[0].status, "degraded")

    def test_cannot_start_process_produces_degraded_report(self) -> None:
        with (
            mock.patch.object(health_monitor.subprocess, "run", side_effect=OSError("sem memória")),
            self.assertLogs("etl.orchestration", level="ERROR") as records,
        ):
            health_monitor.check_once(30)
        self.assertIn("sem memória", records.records[0].monitor_detail)

    def test_monitor_starts_immediately_and_runs_again_after_degraded_check(self) -> None:
        stopped = threading.Event()
        waits = []

        def wait(seconds):
            waits.append(seconds)
            if len(waits) == 2:
                stopped.set()

        with (
            mock.patch.object(health_monitor, "check_once") as check,
            mock.patch.object(stopped, "wait", side_effect=wait),
            mock.patch.object(health_monitor.time, "monotonic", side_effect=[0, 2, 60, 90]),
        ):
            health_monitor.monitor(60, 30, stopped)
        self.assertEqual(check.call_count, 2)
        self.assertEqual(waits, [58, 30])

    def test_real_child_emits_json_only_and_preserves_database_when_api_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            environment = dict(os.environ)
            environment.pop("PREFECT_API_URL", None)
            environment["PYTHONPATH"] = str(ROOT / "src")
            environment["ETL_DUCKDB_PATH"] = str(Path(directory) / "health.duckdb")
            completed = subprocess.run(
                [sys.executable, str(health_monitor.HEALTH_CHECK_SCRIPT), "--json-only"],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
                env=environment,
            )
        self.assertEqual(completed.returncode, 1, completed.stderr)
        lines = completed.stdout.splitlines()
        self.assertEqual(len(lines), 1)
        report = json.loads(lines[0])
        self.assertEqual(report["status"], "degraded")
        self.assertFalse(report["prefect_available"])
        self.assertTrue(report["database_available"])

    def test_manual_invalid_configuration_emits_one_sanitized_degraded_event(self) -> None:
        for override in (
            {"ETL_DUCKDB_PATH": ":memory:"},
            {"ETL_DUCKDB_MEMORY_LIMIT": "secret-user-token@private.example/private/path"},
        ):
            with self.subTest(override=override), tempfile.TemporaryDirectory() as directory:
                environment = dict(os.environ)
                environment["PYTHONPATH"] = str(ROOT / "src")
                environment["ETL_DUCKDB_PATH"] = str(Path(directory) / "private-warehouse.duckdb")
                environment["PREFECT_API_URL"] = "http://user:password-token@private.example/api"
                environment.update(override)
                completed = subprocess.run(
                    [sys.executable, str(health_monitor.HEALTH_CHECK_SCRIPT), "--json-only"],
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                    env=environment,
                )
                self.assertFalse((Path(directory) / "private-warehouse.duckdb").exists())
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertEqual(completed.stderr, "")
            lines = completed.stdout.splitlines()
            self.assertEqual(len(lines), 1)
            report = json.loads(lines[0])
            self.assertEqual(report["event"], health_monitor.HEALTH_CHECK_EVENT)
            self.assertEqual(report["stage"], "orchestration")
            self.assertEqual(report["status"], "degraded")
            self.assertEqual(report["error_type"], "ConfigurationError")
            self.assertFalse(report["database_available"])
            self.assertIsNone(report["prefect_available"])
            for sensitive in (directory, "private.example", "password-token", "secret-user-token"):
                self.assertNotIn(sensitive, completed.stdout)
            self.assertNotIn("Traceback", completed.stdout)

    def test_intervals_must_be_positive_and_finite(self) -> None:
        for value in ("0", "-1", "nan", "inf"):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                health_monitor.positive_seconds(value)
        self.assertEqual(health_monitor.positive_seconds("0.5"), 0.5)


class CanonicalVolumeQueryTests(unittest.TestCase):
    def test_old_flow_summaries_cannot_double_count_loaded_rows(self) -> None:
        import re

        objects = [
            json.loads(line)
            for line in (ROOT / "observability/kibana/painel-operacional.ndjson")
            .read_text()
            .splitlines()
        ]
        panel = next(obj for obj in objects if obj.get("id") == "etl-viz-volumes")
        source = json.loads(panel["attributes"]["kibanaSavedObjectMeta"]["searchSourceJSON"])
        query = source["query"]["query"]
        self.assertTrue(query.startswith("event.keyword: ("))
        allowed = set(re.findall(r'"([^"]+)"', query))
        self.assertEqual(
            allowed,
            {
                "extraction.batch.emitted",
                "transformation.batch.emitted",
                "load.batch.emitted",
                "orchestration.load.emitted",
            },
        )
        historical_events = [
            {"event": "orchestration.load.emitted", "loaded_count": 3},
            {"event": "orchestration.ingest_object.emitted", "loaded_count": 3},
        ]
        self.assertEqual(
            sum(e["loaded_count"] for e in historical_events if e["event"] in allowed), 3
        )

    def test_queue_alert_requires_completed_pipeline_not_monitor_heartbeats(self) -> None:
        import re

        runbook = (ROOT / "docs/runbook-execucao.md").read_text()
        rules = [json.loads(body) for body in re.findall(r"-d '(\{.*?\})'", runbook, re.DOTALL)]
        rule = next(rule for rule in rules if rule.get("name") == "ETL - fila parada")
        query = json.loads(rule["params"]["esQuery"])
        self.assertEqual(
            query["query"]["bool"]["filter"],
            [
                {"term": {"event.keyword": "orchestration.pipeline.emitted"}},
                {"term": {"status.keyword": "completed"}},
            ],
        )

    def test_failure_alert_matches_structured_errors_but_not_writer_contention(self) -> None:
        import re

        runbook = (ROOT / "docs/runbook-execucao.md").read_text()
        rules = [json.loads(body) for body in re.findall(r"-d '(\{.*?\})'", runbook, re.DOTALL)]
        rule = next(rule for rule in rules if rule.get("name") == "ETL - falha de execução")
        query = json.loads(rule["params"]["esQuery"])["query"]

        def matches(clause, record):
            if "bool" in clause:
                boolean = clause["bool"]
                return all(matches(item, record) for item in boolean.get("filter", [])) and sum(
                    matches(item, record) for item in boolean.get("should", [])
                ) >= boolean.get("minimum_should_match", 0)
            operator = next(iter(clause))
            field, expected = next(iter(clause[operator].items()))
            value = record.get(field.removesuffix(".keyword"))
            if operator == "terms":
                return value in expected
            return expected in value if isinstance(value, list) else value == expected

        for record in (
            {"event": "orchestration.pipeline.emitted", "status": "failed", "level": "INFO"},
            {"status": "failed", "failed_stage": "publication"},  # JSON da CLI sem event/level
            {"event": "orchestration.pipeline.emitted", "status": "aborted"},
            {"event": "orchestration.pipeline.emitted", "status": "reconciliation_failed"},
            {"logger": "prefect.flow_runs", "level": "ERROR"},
            {"event": "orchestration.health_check.emitted", "status": "degraded"},
            {"tags": ["etl_error"]},
        ):
            with self.subTest(record=record):
                self.assertTrue(matches(query, record))
        for record in (
            {"event": "orchestration.health_check.emitted", "status": "busy", "level": "INFO"},
            {"event": "orchestration.health_check.emitted", "status": "ok", "level": "INFO"},
            {"event": "orchestration.pipeline.emitted", "status": "completed", "level": "INFO"},
            {"message": "failed attempts: 0", "level": "INFO"},
        ):
            with self.subTest(record=record):
                self.assertFalse(matches(query, record))

    def test_rejections_use_same_canonical_event_filter_as_volumes(self) -> None:
        objects = {
            obj["id"]: obj
            for obj in (
                json.loads(line)
                for line in (ROOT / "observability/kibana/painel-operacional.ndjson")
                .read_text()
                .splitlines()
            )
        }
        self.assertEqual(
            objects["etl-viz-rejeicoes"]["attributes"]["kibanaSavedObjectMeta"]["searchSourceJSON"],
            objects["etl-viz-volumes"]["attributes"]["kibanaSavedObjectMeta"]["searchSourceJSON"],
        )

    def test_periodic_monitor_does_not_depend_on_prefect_health_or_collector(self) -> None:
        import yaml

        services = yaml.safe_load((ROOT / "docker-compose.yml").read_text())["services"]
        monitor = services["health-monitor"]
        self.assertEqual(
            monitor["depends_on"], {"prefect-server": {"condition": "service_started"}}
        )
        self.assertEqual(monitor["restart"], "unless-stopped")
        self.assertEqual(monitor["stop_grace_period"], "35s")
        self.assertEqual(monitor["logging"]["driver"], "gelf")
        self.assertIn("duck-data:/data", monitor["volumes"])
        self.assertEqual(
            monitor["command"][-4:], ["--interval-seconds", "60", "--timeout-seconds", "30"]
        )


if __name__ == "__main__":
    unittest.main()
