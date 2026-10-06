"""Sinal de saúde periódico: limite de execução, falha explícita e retomada."""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import subprocess
import sys
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
        for status, exit_code in (("ok", 0), ("degraded", 1)):
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
