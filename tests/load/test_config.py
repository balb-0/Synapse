from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.load.config import (  # noqa: E402
    DEFAULT_DATABASE_PATH,
    ConfigurationError,
    load_duckdb_settings,
)


class DuckDBSettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.directory = Path(self.temporary_directory.name)
        self.environment = {
            "ETL_DUCKDB_PATH": str(self.directory / "ingestao.duckdb"),
        }

    def test_loads_configuration_from_environment(self) -> None:
        settings = load_duckdb_settings(environ=self.environment)

        self.assertEqual(settings.database_path, self.directory / "ingestao.duckdb")

    def test_uses_default_path_when_environment_is_empty(self) -> None:
        settings = load_duckdb_settings(environ={})

        self.assertTrue(settings.database_path.is_absolute())
        self.assertEqual(
            settings.database_path,
            Path.cwd() / DEFAULT_DATABASE_PATH,
        )

    def test_explicit_parameters_override_environment(self) -> None:
        settings = load_duckdb_settings(
            parameters={"database_path": self.directory / "outro.duckdb"},
            environ=self.environment,
        )

        self.assertEqual(settings.database_path, self.directory / "outro.duckdb")

    def test_relative_path_is_resolved_from_working_directory(self) -> None:
        settings = load_duckdb_settings(
            parameters={"database_path": "data/duckdb/local.duckdb"}, environ={}
        )

        self.assertEqual(settings.database_path, Path.cwd() / "data/duckdb/local.duckdb")

    def test_rejects_in_memory_database(self) -> None:
        for value in (":memory:", "memory", ":MEMORY:"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ConfigurationError, "arquivo persistente"):
                    load_duckdb_settings(environ={"ETL_DUCKDB_PATH": value})

    def test_rejects_blank_path_given_as_explicit_parameter(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "apontar para um arquivo"):
            load_duckdb_settings(parameters={"database_path": "   "}, environ={})

    def test_rejects_directory_as_database_path(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "não para um diretório"):
            load_duckdb_settings(environ={"ETL_DUCKDB_PATH": str(self.directory)})

    def test_rejects_parent_reference_in_database_path(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, r"'\.\.'"):
            load_duckdb_settings(environ={"ETL_DUCKDB_PATH": "data/../ingestao.duckdb"})

    def test_rejects_unknown_parameter_name(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "desconhecidos"):
            load_duckdb_settings(
                parameters={"duckdb_password": "não existe credencial aqui"},
                environ=self.environment,
            )


if __name__ == "__main__":
    unittest.main()
