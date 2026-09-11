from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.load.config import DuckDBSettings  # noqa: E402

# O DuckDB é dependência de runtime da carga (requirements.txt). Ambientes que
# só exercitam extração ou transformação não a instalam, e ali a verificação do
# arquivo local não tem o que exercitar.
DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None

if DUCKDB_INSTALLED:
    from etl.load import environment as load_environment
    from etl.load.environment import (
        HEALTH_CHECK_SCHEMA,
        HEALTH_CHECK_TABLE,
        DatabaseEnvironmentError,
        open_connection,
        prepare_database,
        run_health_check,
    )

SEM_DUCKDB = "duckdb não instalado; use pip install -r requirements.txt"
SCRIPT = REPOSITORY_ROOT / "scripts/load/duckdb_env.py"


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class DuckDBEnvironmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.directory = Path(self.temporary_directory.name)
        self.database_path = self.directory / "duckdb" / "ingestao.duckdb"
        self.settings = DuckDBSettings(database_path=self.database_path)

    def test_prepare_creates_directory_and_file(self) -> None:
        created = prepare_database(self.settings)

        self.assertTrue(created)
        self.assertTrue(self.database_path.is_file())
        self.assertGreater(self.database_path.stat().st_size, 0)

    def test_prepare_is_idempotent_and_preserves_content(self) -> None:
        prepare_database(self.settings)
        with open_connection(self.settings) as connection:
            connection.execute("CREATE TABLE marcador_do_teste (id INTEGER)")
            connection.execute("INSERT INTO marcador_do_teste VALUES (1)")

        created_again = prepare_database(self.settings)

        self.assertFalse(created_again)
        with open_connection(self.settings) as connection:
            total = connection.execute("SELECT count(*) FROM marcador_do_teste").fetchone()
        self.assertEqual(total, (1,))

    def test_health_check_reports_every_verification(self) -> None:
        report = run_health_check(self.settings)

        self.assertTrue(report.passed, [check.detail for check in report.checks])
        self.assertTrue(report.database_created)
        self.assertEqual(report.database_path, self.database_path)
        self.assertTrue(report.duckdb_version.startswith("v"))
        self.assertEqual(
            [check.name for check in report.checks],
            ["arquivo_local", "consulta_smoke", "escrita_persistida"],
        )

    def test_health_check_leaves_no_object_in_the_database(self) -> None:
        run_health_check(self.settings)

        with open_connection(self.settings) as connection:
            tables = connection.execute("SELECT count(*) FROM duckdb_tables()").fetchone()
            schemas = connection.execute(
                "SELECT count(*) FROM duckdb_schemas() WHERE schema_name = ?",
                [HEALTH_CHECK_SCHEMA],
            ).fetchone()

        self.assertEqual(tables, (0,))
        self.assertEqual(schemas, (0,))

    def test_second_execution_reuses_the_persisted_file(self) -> None:
        first = run_health_check(self.settings)
        second = run_health_check(self.settings)

        self.assertTrue(first.database_created)
        self.assertFalse(second.database_created)
        self.assertTrue(second.passed, [check.detail for check in second.checks])

    def test_reports_clear_error_when_path_is_a_directory(self) -> None:
        settings = DuckDBSettings(database_path=self.directory)

        with self.assertRaises(DatabaseEnvironmentError) as context:
            run_health_check(settings)

        self.assertIn(str(self.directory), str(context.exception))
        self.assertIn("Is a directory", str(context.exception))

    def test_interrupted_health_check_removes_the_marker(self) -> None:
        prepare_database(self.settings)
        falha = DatabaseEnvironmentError("releitura interrompida")

        with mock.patch.object(load_environment, "_persistence_check", side_effect=falha):
            with self.assertRaises(DatabaseEnvironmentError):
                run_health_check(self.settings)

        with open_connection(self.settings) as connection:
            tables = connection.execute("SELECT count(*) FROM duckdb_tables()").fetchone()
        self.assertEqual(tables, (0,))

    def test_reports_leftover_when_the_cleanup_also_fails(self) -> None:
        prepare_database(self.settings)
        falha = DatabaseEnvironmentError("remocao recusada")

        with mock.patch.object(load_environment, "_drop_marker", side_effect=falha):
            with self.assertRaises(DatabaseEnvironmentError) as context:
                run_health_check(self.settings)

        self.assertIn("permaneceu no arquivo", str(context.exception))
        with open_connection(self.settings) as connection:
            remaining = connection.execute(f"SELECT count(*) FROM {HEALTH_CHECK_TABLE}").fetchone()
        self.assertEqual(remaining, (1,))

    def test_reports_lock_when_another_process_holds_the_file(self) -> None:
        prepare_database(self.settings)
        holder = subprocess.Popen(
            [
                sys.executable,
                "-c",
                "import duckdb, sys, time\n"
                "conexao = duckdb.connect(sys.argv[1])\n"
                "conexao.execute('SELECT 1')\n"
                "print('pronto', flush=True)\n"
                "time.sleep(30)\n",
                str(self.database_path),
            ],
            stdout=subprocess.PIPE,
            text=True,
        )
        self.addCleanup(holder.wait, 10)
        self.addCleanup(holder.terminate)
        self.assertEqual(holder.stdout.readline().strip(), "pronto")

        with self.assertRaises(DatabaseEnvironmentError) as context:
            run_health_check(self.settings)

        self.assertIn(str(self.database_path), str(context.exception))


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class DuckDBEnvironmentCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "ingestao.duckdb"

    def run_command(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--database", str(self.database_path), *arguments],
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_command_creates_database_and_reports_success(self) -> None:
        result = self.run_command()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.database_path.is_file())
        self.assertIn("escrita_persistida", result.stdout)
        self.assertNotIn("[falha]", result.stdout)

    def test_command_fails_with_invalid_configuration(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--database", ":memory:"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("HEALTH_CHECK_FALHOU", result.stderr)


class LoadPackageFacadeTests(unittest.TestCase):
    """O pacote resolve o repositório sob demanda, sem exigir o driver no import."""

    @unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
    def test_resolves_the_repository_on_demand(self) -> None:
        import etl.load as load_package

        self.assertEqual(load_package.DuckDbLoadRepository.__name__, "DuckDbLoadRepository")
        self.assertEqual(load_package.LoadResult.__name__, "LoadResult")

    def test_unknown_attribute_still_fails(self) -> None:
        import etl.load as load_package

        with self.assertRaises(AttributeError):
            load_package.RepositorioInexistente


if __name__ == "__main__":
    unittest.main()
