"""Serialização de escrita: o DuckDB só permite um processo por arquivo.

O DuckDB já recusa uma segunda conexão de escrita ao mesmo arquivo com um
`IOException` que nomeia o processo concorrente (ver
https://duckdb.org/docs/stable/connect/concurrency). O repositório espera esse
escritor liberar o arquivo, em vez de propagar o erro na primeira tentativa.
"""

from __future__ import annotations

import importlib.util
import logging
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None
SEM_DUCKDB = "duckdb não instalado; use pip install -r requirements.txt"

if DUCKDB_INSTALLED:
    import duckdb

    from etl.load.duckdb_repository import DuckDbLoadRepository, WriteLockTimeoutError

# Precisa ser um processo à parte: dentro do mesmo processo, o driver do
# DuckDB reaproveita a conexão já aberta para o mesmo arquivo em vez de
# disputar o lock do arquivo com ela.
HOLD_LOCK_SCRIPT = (
    "import duckdb, sys, time\n"
    "conn = duckdb.connect(sys.argv[1])\n"
    "print('locked', flush=True)\n"
    "time.sleep(float(sys.argv[2]))\n"
)


class LogRecordCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class WriteLockSerializationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "ingestao.duckdb"
        self.logger = logging.getLogger("etl.load")
        self.collector = LogRecordCollector()
        previous_level = self.logger.level
        self.logger.handlers.append(self.collector)
        self.logger.setLevel(logging.INFO)
        self.addCleanup(self.logger.handlers.remove, self.collector)
        self.addCleanup(self.logger.setLevel, previous_level)

    def _connect_retry_events(self) -> list[logging.LogRecord]:
        return [
            record
            for record in self.collector.records
            if getattr(record, "event", None) == "load.connect_retry.emitted"
        ]

    def _hold_lock_in_another_process(self, seconds: float) -> subprocess.Popen:
        process = subprocess.Popen(
            [sys.executable, "-c", HOLD_LOCK_SCRIPT, str(self.database_path), str(seconds)],
            stdout=subprocess.PIPE,
            text=True,
        )
        self.addCleanup(process.wait, timeout=10)
        self.addCleanup(process.stdout.close)
        line = process.stdout.readline()
        assert line.strip() == "locked", f"processo auxiliar não confirmou o lock: {line!r}"
        return process

    def test_times_out_while_another_process_holds_the_file(self) -> None:
        self._hold_lock_in_another_process(seconds=2.0)

        started = time.monotonic()
        with self.assertRaises(WriteLockTimeoutError):
            DuckDbLoadRepository(self.database_path, write_lock_timeout_seconds=0.3)
        elapsed = time.monotonic() - started

        self.assertGreaterEqual(elapsed, 0.3)

        events = self._connect_retry_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].status, "timed_out")
        self.assertGreaterEqual(events[0].attempts, 1)
        self.assertGreaterEqual(events[0].duration_ms, 300)

    def test_waits_for_the_file_and_succeeds_once_it_is_released(self) -> None:
        holder = self._hold_lock_in_another_process(seconds=0.5)

        started = time.monotonic()
        with DuckDbLoadRepository(self.database_path, write_lock_timeout_seconds=5.0) as repository:
            elapsed = time.monotonic() - started
            self.assertEqual(repository.count("pesquisas"), 0)

        # Só chega aqui depois que o outro processo soltou o arquivo.
        self.assertGreaterEqual(elapsed, 0.4)
        holder.wait(timeout=5)

        events = self._connect_retry_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].status, "recovered")
        self.assertGreater(events[0].attempts, 1)
        self.assertGreaterEqual(events[0].duration_ms, 400)

    def test_does_not_emit_an_event_when_there_is_no_contention(self) -> None:
        with DuckDbLoadRepository(self.database_path):
            pass

        self.assertEqual(self._connect_retry_events(), [])

    def test_does_not_wait_for_an_error_that_is_not_a_lock_conflict(self) -> None:
        # Um diretório no lugar do arquivo causa IOException, mas não é
        # disputa de lock. Isso é portável: permissões POSIX (o caso
        # anterior) não bloqueiam administradores no Windows.
        blocked_path = Path(self.temporary_directory.name) / "diretorio_no_lugar_do_banco"
        blocked_path.mkdir()

        started = time.monotonic()
        with self.assertRaises(duckdb.IOException) as context:
            DuckDbLoadRepository(blocked_path, write_lock_timeout_seconds=5.0)
        elapsed = time.monotonic() - started

        self.assertNotIsInstance(context.exception, WriteLockTimeoutError)
        self.assertLess(elapsed, 2.0)


if __name__ == "__main__":
    unittest.main()
