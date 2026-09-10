"""Serialização de escrita: o DuckDB só permite um processo por arquivo.

O DuckDB já recusa uma segunda conexão de escrita ao mesmo arquivo com um
`IOException` que nomeia o processo concorrente (ver
https://duckdb.org/docs/stable/connect/concurrency). O repositório espera esse
escritor liberar o arquivo, em vez de propagar o erro na primeira tentativa.
"""

from __future__ import annotations

import importlib.util
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


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class WriteLockSerializationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "ingestao.duckdb"

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

    def test_waits_for_the_file_and_succeeds_once_it_is_released(self) -> None:
        holder = self._hold_lock_in_another_process(seconds=0.5)

        started = time.monotonic()
        with DuckDbLoadRepository(self.database_path, write_lock_timeout_seconds=5.0) as repository:
            elapsed = time.monotonic() - started
            self.assertEqual(repository.count("pesquisas"), 0)

        # Só chega aqui depois que o outro processo soltou o arquivo.
        self.assertGreaterEqual(elapsed, 0.4)
        holder.wait(timeout=5)

    def test_does_not_wait_for_an_error_that_is_not_a_lock_conflict(self) -> None:
        # Permissão negada é um IOException do mesmo tipo, mas não é disputa
        # de arquivo: esperar o timeout inteiro não o resolveria.
        directory = Path(self.temporary_directory.name) / "sem_permissao"
        directory.mkdir(mode=0o555)
        self.addCleanup(directory.chmod, 0o755)
        blocked_path = directory / "ingestao.duckdb"

        started = time.monotonic()
        with self.assertRaises(duckdb.IOException) as context:
            DuckDbLoadRepository(blocked_path, write_lock_timeout_seconds=5.0)
        elapsed = time.monotonic() - started

        self.assertNotIsInstance(context.exception, WriteLockTimeoutError)
        self.assertLess(elapsed, 2.0)


if __name__ == "__main__":
    unittest.main()
