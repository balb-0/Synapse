"""Parametrização de conexão (threads, memory_limit) do repositório de carga.

Ausente, a conexão usa o padrão do próprio DuckDB.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None
SEM_DUCKDB = "duckdb não instalado; use pip install -r requirements.txt"

if DUCKDB_INSTALLED:
    from etl.load.duckdb_repository import DuckDbLoadRepository


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class ConnectionTuningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "ingestao.duckdb"

    def _setting(self, repository: DuckDbLoadRepository, name: str):
        return repository._conn.execute(f"SELECT current_setting('{name}')").fetchone()[0]

    def test_threads_is_applied_when_configured(self) -> None:
        with DuckDbLoadRepository(self.database_path) as repository:
            default_threads = self._setting(repository, "threads")

        with DuckDbLoadRepository(
            self.database_path, threads=default_threads + 1
        ) as repository:
            tuned_threads = self._setting(repository, "threads")

        self.assertEqual(tuned_threads, default_threads + 1)

    def test_memory_limit_is_applied_when_configured(self) -> None:
        # Unidade binária (MiB) evita a conversão decimal->binária do DuckDB
        # para entradas como "128MB", que voltaria em outro número.
        with DuckDbLoadRepository(self.database_path, memory_limit="128MiB") as repository:
            limit = self._setting(repository, "memory_limit")

        self.assertEqual(limit, "128.0 MiB")

    def test_memory_limit_is_left_untouched_when_not_configured(self) -> None:
        with DuckDbLoadRepository(self.database_path) as repository:
            limit = self._setting(repository, "memory_limit")

        self.assertNotEqual(limit, "128.0 MiB")


if __name__ == "__main__":
    unittest.main()
