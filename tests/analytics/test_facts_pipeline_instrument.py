from __future__ import annotations

import hashlib
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from etl.analytics.facts_pipeline_instrument import (  # noqa: E402
    SQL_PATH,
    fact_statements,
    render_ddl,
)

DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None
if DUCKDB_INSTALLED:
    import duckdb


MONTH_KEY = hashlib.sha256(b"v1|DIM_TEMPO|K|10:2026-08-31").hexdigest()


class FactsDdlContractTests(unittest.TestCase):
    def test_versioned_sql_matches_generator(self) -> None:
        self.assertEqual(SQL_PATH.read_text(encoding="utf-8"), render_ddl())

    def test_only_two_facts_and_no_invented_measures(self) -> None:
        pipeline, instrument = fact_statements()
        self.assertIn('CREATE TABLE IF NOT EXISTS "FATO_PIPELINE_MENSAL"', pipeline)
        self.assertIn('CREATE TABLE IF NOT EXISTS "FATO_PESQUISA_PERGUNTA"', instrument)
        self.assertNotIn("qtd_a_finalizar", pipeline)
        for absent in (
            "qtd_pergunta",
            "qtd_alternativas",
            "qtd_linhas_matriz",
            "qtd_colunas_matriz",
        ):
            self.assertNotIn(absent, instrument)


@unittest.skipUnless(DUCKDB_INSTALLED, "duckdb não instalado")
class FactsDdlDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = duckdb.connect(":memory:")
        for table, key in (
            ("DIM_TEMPO", "sk_tempo"),
            ("DIM_STATUS_PESQUISA", "sk_status"),
            ("DIM_AREA", "sk_area"),
            ("DIM_TIPO_PESQUISA", "sk_tipo"),
            ("DIM_PERFIL_PESQUISA", "sk_perfil"),
            ("DIM_PESQUISA", "sk_pesquisa"),
            ("DIM_PERGUNTA", "sk_pergunta"),
        ):
            self.db.execute(f'CREATE TABLE "{table}" ("{key}" VARCHAR PRIMARY KEY)')
        for table, key, value in (
            ("DIM_TEMPO", "sk_tempo", MONTH_KEY),
            ("DIM_STATUS_PESQUISA", "sk_status", "s1"),
            ("DIM_AREA", "sk_area", "a1"),
            ("DIM_TIPO_PESQUISA", "sk_tipo", "ty1"),
            ("DIM_PERFIL_PESQUISA", "sk_perfil", "pf1"),
            ("DIM_PESQUISA", "sk_pesquisa", "p1"),
            ("DIM_PESQUISA", "sk_pesquisa", "unknown"),
            ("DIM_PERGUNTA", "sk_pergunta", "q1"),
        ):
            self.db.execute(f'INSERT INTO "{table}" ("{key}") VALUES (?)', [value])
        for statement in fact_statements():
            self.db.execute(statement)

    def tearDown(self) -> None:
        self.db.close()

    def insert_pipeline(
        self,
        *,
        month: str = "2026-08-31",
        date_key: str = MONTH_KEY,
        stock: int = 2,
        entries: int | None = None,
        exits: int | None = None,
    ) -> None:
        self.db.execute(
            """INSERT INTO "FATO_PIPELINE_MENSAL" VALUES
            (?, ?, TIMESTAMP '2026-09-01 09:00:00', 's1', 'a1', 'ty1', 'pf1', ?, ?, ?)""",
            [date_key, month, stock, entries, exits],
        )

    def test_pipeline_requires_observed_month_end_and_all_dimension_keys(self) -> None:
        self.insert_pipeline()
        self.assertEqual(
            self.db.execute(
                'SELECT qtd_entradas_no_mes, qtd_saidas_no_mes FROM "FATO_PIPELINE_MENSAL"'
            ).fetchone(),
            (None, None),
        )
        with self.assertRaises(duckdb.ConstraintException):
            self.insert_pipeline()
        with self.assertRaises(duckdb.ConstraintException):
            self.insert_pipeline(month="2026-08-30")
        with self.assertRaises(duckdb.ConstraintException):
            self.insert_pipeline(date_key="missing")
        with self.assertRaises(duckdb.ConstraintException):
            self.insert_pipeline(month="2026-09-30")
        with self.assertRaises(duckdb.ConstraintException):
            self.insert_pipeline(stock=-1)

    def test_pipeline_flows_are_nullable_but_cannot_be_negative(self) -> None:
        with self.assertRaises(duckdb.ConstraintException):
            self.insert_pipeline(entries=-1)
        with self.assertRaises(duckdb.ConstraintException):
            self.insert_pipeline(exits=-1)

    def test_instrument_is_factless_and_one_association_per_question(self) -> None:
        self.db.execute(
            'INSERT INTO "FATO_PESQUISA_PERGUNTA" VALUES (?, ?, ?)', ["unknown", "q1", None]
        )
        self.assertEqual(
            self.db.execute('SELECT COUNT(*) FROM "FATO_PESQUISA_PERGUNTA"').fetchone(), (1,)
        )
        with self.assertRaises(duckdb.ConstraintException):
            self.db.execute(
                'INSERT INTO "FATO_PESQUISA_PERGUNTA" VALUES (?, ?, ?)', ["p1", "q1", MONTH_KEY]
            )
        with self.assertRaises(duckdb.ConstraintException):
            self.db.execute(
                'INSERT INTO "FATO_PESQUISA_PERGUNTA" VALUES (?, ?, ?)', ["p1", "missing", None]
            )
        columns = [
            row[1]
            for row in self.db.execute('PRAGMA table_info("FATO_PESQUISA_PERGUNTA")').fetchall()
        ]
        self.assertEqual(columns, ["sk_pesquisa", "sk_pergunta", "sk_data_pesquisa"])


if __name__ == "__main__":
    unittest.main()
