"""Public analytical connection policy: finite waits and no permanent retries."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import duckdb

from etl.analytics.load import load_analytics
from etl.load.connection import WriteLockTimeoutError, connect_with_retry
from etl.load.duckdb_repository import DuckDbLoadRepository
from tests.load.test_write_lock import HOLD_LOCK_SCRIPT


class PublicConnectionRetryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.database = Path(self.tmp.name) / "analytics.duckdb"
        with DuckDbLoadRepository(self.database):
            pass

    def hold_lock(self, seconds):
        holder = subprocess.Popen(
            [sys.executable, "-c", HOLD_LOCK_SCRIPT, str(self.database), str(seconds)],
            stdout=subprocess.PIPE,
            text=True,
        )
        self.addCleanup(holder.wait, timeout=10)
        self.addCleanup(holder.stdout.close)
        self.assertEqual(holder.stdout.readline().strip(), "locked")

    def test_read_only_waits_for_writer_then_enforces_no_write(self):
        self.hold_lock(0.4)
        with connect_with_retry(self.database, timeout_seconds=3, read_only=True) as con:
            self.assertEqual(
                con.execute('SELECT count(*) FROM "ingestao_pesquisas"').fetchone()[0], 0
            )
            with self.assertRaises(duckdb.InvalidInputException):
                con.execute("CREATE TABLE prohibited (id INTEGER)")

    def test_read_only_has_finite_lock_timeout(self):
        self.hold_lock(0.5)
        with self.assertRaises(WriteLockTimeoutError):
            connect_with_retry(self.database, timeout_seconds=0.1, read_only=True)

    def test_invalid_timeout_rejected_before_connection(self):
        with patch("etl.load.connection.duckdb.connect") as connect:
            for timeout in (0, -1, float("inf"), float("nan"), True, "2"):
                with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                    connect_with_retry(self.database, timeout_seconds=timeout)
            connect.assert_not_called()

    def test_permanent_error_is_not_repeated(self):
        with patch(
            "etl.load.connection.duckdb.connect",
            side_effect=duckdb.IOException("Permission denied"),
        ) as connect:
            with self.assertRaisesRegex(duckdb.IOException, "Permission denied"):
                connect_with_retry(self.database, timeout_seconds=1)
            self.assertEqual(connect.call_count, 1)

    def test_reconcile_cli_waits_then_reports_unavailable_source_without_modifying_database(self):
        with connect_with_retry(self.database) as con:
            loaded = load_analytics(con)
        before = hashlib.sha256(self.database.read_bytes()).hexdigest()
        self.hold_lock(0.4)
        run = subprocess.run(
            [
                sys.executable,
                "-m",
                "etl.analytics.reconcile",
                str(self.database),
                "--write-lock-timeout-seconds",
                "3",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(run.returncode, 1, run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(report["load_id"], loaded.load_id)
        self.assertFalse(report["reconciled"])
        participation = next(cube for cube in report["cubes"] if cube["cube"] == "C02")
        self.assertEqual(participation["status"], "source_unavailable")
        self.assertEqual(hashlib.sha256(self.database.read_bytes()).hexdigest(), before)

    def test_analytics_cli_waits_for_writer_and_commits_manifest(self):
        self.hold_lock(0.4)
        run = subprocess.run(
            [
                sys.executable,
                "-m",
                "etl.analytics.load",
                str(self.database),
                "--write-lock-timeout-seconds",
                "3",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        with connect_with_retry(self.database, read_only=True) as con:
            self.assertEqual(
                con.execute('SELECT count(*) FROM "analytics_load_run"').fetchone()[0], 1
            )


if __name__ == "__main__":
    unittest.main()
