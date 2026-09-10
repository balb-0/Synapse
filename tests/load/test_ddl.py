from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.load.ddl import (  # noqa: E402
    IDENTITY_COLUMN,
    business_key,
    create_current_view,
    current_view_name,
    duckdb_type,
    has_business_key,
    quote,
    render_ddl,
    required_columns,
    statements,
    table_name,
)
from etl.transformation.schema import SCHEMAS, destination_columns  # noqa: E402

DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None
if DUCKDB_INSTALLED:
    import duckdb

    from etl.load.duckdb_repository import DuckDbLoadRepository

SEM_DUCKDB = "duckdb não instalado; use pip install -r requirements.txt"
DDL_PATH = REPOSITORY_ROOT / "sql/duckdb/001_ingestao_tratada.sql"
RENDER_SCRIPT = REPOSITORY_ROOT / "scripts/load/render_ddl.py"


class DdlContractTests(unittest.TestCase):
    def test_physical_name_is_prefixed_per_source(self) -> None:
        self.assertEqual(table_name("pesquisas"), "ingestao_pesquisas")
        self.assertEqual(current_view_name("pesquisas"), "ingestao_pesquisas_atual")

    def test_every_source_has_a_table(self) -> None:
        rendered = "\n".join(statements())
        for source in SCHEMAS:
            with self.subTest(source=source):
                self.assertIn(f'CREATE TABLE IF NOT EXISTS "{table_name(source)}"', rendered)

    def test_business_keys_come_from_the_transformation_contract(self) -> None:
        self.assertEqual(business_key("pesquisas"), ("pesquisa_id",))
        self.assertEqual(business_key("questoes"), ("pesquisa_id", "pergunta_id"))
        self.assertEqual(business_key("respostas"), ("pesquisa_id", "resposta_id"))

    def test_participation_falls_back_to_the_physical_occurrence(self) -> None:
        self.assertFalse(has_business_key("respondentes"))
        self.assertEqual(business_key("respondentes"), ("source_checksum", "source_offset"))
        self.assertIsNone(create_current_view("respondentes"))

    def test_required_fields_are_declared_not_null(self) -> None:
        ddl = "\n".join(statements())
        for source in SCHEMAS:
            for column in required_columns(source):
                with self.subTest(source=source, column=column):
                    self.assertIn(f'    "{column}" ', ddl)
        self.assertIn('"pesquisa_id" VARCHAR NOT NULL', ddl)
        self.assertIn('"resposta_id" VARCHAR NOT NULL', ddl)

    def test_source_checksum_stays_nullable(self) -> None:
        # O contrato de lote permite lote sem checksum de objeto (adaptador local).
        self.assertIn('"source_checksum" VARCHAR,', "\n".join(statements()))

    def test_no_clickhouse_vocabulary_survives_the_translation(self) -> None:
        ddl = render_ddl().lower()
        for term in ("engine", "order by (", "mergetree", "fixedstring", "datetime64", "nullable("):
            with self.subTest(term=term):
                self.assertNotIn(term, ddl)

    def test_translates_canonical_types_to_duckdb(self) -> None:
        self.assertEqual(duckdb_type("String"), "VARCHAR")
        self.assertEqual(duckdb_type("Int64"), "BIGINT")
        self.assertEqual(duckdb_type("Decimal(18, 6)"), "DECIMAL(18, 6)")
        self.assertEqual(duckdb_type("DateTime64(6, 'UTC')"), "TIMESTAMP")
        self.assertEqual(duckdb_type("FixedString(64)"), "VARCHAR")
        self.assertEqual(duckdb_type("Array(String)"), "VARCHAR")
        self.assertEqual(duckdb_type("Nullable(Bool)"), "BOOLEAN")

    def test_rejects_unexpected_identifier(self) -> None:
        with self.assertRaisesRegex(ValueError, "identificador inválido"):
            quote("ingestao_pesquisas; DROP TABLE x")

    def test_keeps_a_view_with_the_name_used_before_the_prefix(self) -> None:
        # Compatibilidade transitória: leitores anteriores ao prefixo seguem
        # funcionando. Condição de remoção na ADR 0002.
        rendered = "\n".join(statements())
        for source in SCHEMAS:
            with self.subTest(source=source):
                self.assertIn(f'CREATE VIEW IF NOT EXISTS "{source}" AS', rendered)

    def test_versioned_file_matches_the_contract(self) -> None:
        self.assertTrue(DDL_PATH.is_file(), f"{DDL_PATH} nao existe")
        self.assertEqual(DDL_PATH.read_text(encoding="utf-8"), render_ddl())

    def test_check_command_accepts_the_versioned_file(self) -> None:
        result = subprocess.run(
            [sys.executable, str(RENDER_SCRIPT), "--check"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class DdlAppliedToDuckDbTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "ingestao.duckdb"
        self.connection = duckdb.connect(str(self.database_path))
        self.addCleanup(self.connection.close)
        for statement in statements():
            self.connection.execute(statement)

    def _insert(self, source: str, **values: object) -> None:
        columns = list(destination_columns(source))
        row = {column: None for column in columns}
        row.update(
            source=source,
            run_id="run-1",
            task_id="task-1",
            batch_id="batch-1",
            source_offset=1,
            content_checksum="conteudo-1",
            record_identity="identidade-1",
            idempotency_key="idem-1",
            ingested_at="2026-09-10 10:00:00",
            schema_version="1.0",
        )
        row.update(values)
        placeholders = ", ".join("?" for _ in columns)
        self.connection.execute(
            f'INSERT INTO "{table_name(source)}" VALUES ({placeholders})',
            [row[column] for column in columns],
        )

    def test_creates_one_table_per_source_and_the_control_tables(self) -> None:
        tables = {
            row[0]
            for row in self.connection.execute("SELECT table_name FROM duckdb_tables()").fetchall()
        }

        for source in SCHEMAS:
            self.assertIn(table_name(source), tables)
        for control in ("rejected", "_control_object", "_loaded_identity", "_checkpoint"):
            self.assertIn(control, tables)

    def test_keeps_both_versions_and_the_view_returns_the_most_recent(self) -> None:
        self._insert(
            "pesquisas",
            pesquisa_id="424",
            titulo="Faturamento 2025",
            idempotency_key="idem-antiga",
            content_checksum="conteudo-antigo",
            ingested_at="2026-09-09 10:00:00",
        )
        self._insert(
            "pesquisas",
            pesquisa_id="424",
            titulo="Faturamento 2026",
            idempotency_key="idem-nova",
            content_checksum="conteudo-novo",
            ingested_at="2026-09-10 09:30:00",
        )

        total = self.connection.execute(
            f'SELECT count(*) FROM "{table_name("pesquisas")}"'
        ).fetchone()
        atual = self.connection.execute(
            f'SELECT pesquisa_id, titulo FROM "{current_view_name("pesquisas")}"'
        ).fetchall()

        self.assertEqual(total, (2,))
        self.assertEqual(atual, [("424", "Faturamento 2026")])

    def test_primary_key_blocks_reloading_the_same_identity(self) -> None:
        self._insert("pesquisas", pesquisa_id="424", idempotency_key="idem-1")

        with self.assertRaises(duckdb.ConstraintException) as context:
            self._insert("pesquisas", pesquisa_id="424", idempotency_key="idem-1")

        self.assertIn(IDENTITY_COLUMN, str(context.exception))

    def test_unique_blocks_the_same_key_with_the_same_content(self) -> None:
        self._insert(
            "pesquisas",
            pesquisa_id="424",
            idempotency_key="idem-1",
            content_checksum="mesmo-conteudo",
        )

        with self.assertRaises(duckdb.ConstraintException):
            self._insert(
                "pesquisas",
                pesquisa_id="424",
                idempotency_key="idem-2",
                content_checksum="mesmo-conteudo",
            )

    def test_technical_metadata_is_mandatory(self) -> None:
        with self.assertRaises(duckdb.ConstraintException):
            self._insert("pesquisas", pesquisa_id="424", run_id=None)

    def test_required_business_field_is_mandatory(self) -> None:
        with self.assertRaises(duckdb.ConstraintException):
            self._insert("pesquisas", pesquisa_id=None)

    def test_repository_applies_the_same_contract(self) -> None:
        other = Path(self.temporary_directory.name) / "repositorio.duckdb"

        with DuckDbLoadRepository(other) as repository:
            tables = {
                row[0]
                for row in repository._conn.execute(
                    "SELECT table_name FROM duckdb_tables()"
                ).fetchall()
            }
            views = {
                row[0]
                for row in repository._conn.execute(
                    "SELECT view_name FROM duckdb_views() WHERE NOT internal"
                ).fetchall()
            }

        self.assertIn(table_name("pesquisas"), tables)
        self.assertIn(current_view_name("pesquisas"), views)
        self.assertNotIn("pesquisas", tables)


if __name__ == "__main__":
    unittest.main()
