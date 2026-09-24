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
    UNKNOWN_PESQUISA_KEY,
    fact_statements,
    render_ddl,
)

DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None
if DUCKDB_INSTALLED:
    import duckdb


MONTH_KEY = hashlib.sha256(b"v1|DIM_TEMPO|K|10:2026-08-31").hexdigest()
PESQUISA_A_KEY = hashlib.sha256(b"v1|DIM_PESQUISA|K|1:A").hexdigest()
PESQUISA_B_KEY = hashlib.sha256(b"v1|DIM_PESQUISA|K|1:B").hexdigest()
PERGUNTA_A_KEY = hashlib.sha256(b"v1|DIM_PERGUNTA|K|1:A2:q1").hexdigest()
PERGUNTA_ORFA_KEY = hashlib.sha256(b"v1|DIM_PERGUNTA|K|1:X2:q2").hexdigest()
PERGUNTA_TITULO_KEY = hashlib.sha256(b"v1|DIM_PERGUNTA|K|1:Y2:q3").hexdigest()


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
            ("DIM_PESQUISA", "sk_pesquisa", PESQUISA_A_KEY),
            ("DIM_PESQUISA", "sk_pesquisa", PESQUISA_B_KEY),
            ("DIM_PESQUISA", "sk_pesquisa", UNKNOWN_PESQUISA_KEY),
            ("DIM_PERGUNTA", "sk_pergunta", PERGUNTA_A_KEY),
            ("DIM_PERGUNTA", "sk_pergunta", PERGUNTA_ORFA_KEY),
            ("DIM_PERGUNTA", "sk_pergunta", PERGUNTA_TITULO_KEY),
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
            'INSERT INTO "FATO_PESQUISA_PERGUNTA" VALUES (?, ?, ?, ?, ?, ?)',
            [PESQUISA_A_KEY, PERGUNTA_A_KEY, None, "A", "q1", "id"],
        )
        self.assertEqual(
            self.db.execute('SELECT COUNT(*) FROM "FATO_PESQUISA_PERGUNTA"').fetchone(), (1,)
        )
        with self.assertRaises(duckdb.ConstraintException):
            self.db.execute(
                'INSERT INTO "FATO_PESQUISA_PERGUNTA" VALUES (?, ?, ?, ?, ?, ?)',
                [PESQUISA_A_KEY, PERGUNTA_A_KEY, MONTH_KEY, "A", "q1", "id"],
            )
        with self.assertRaises(duckdb.ConstraintException):
            self.db.execute(
                'INSERT INTO "FATO_PESQUISA_PERGUNTA" VALUES (?, ?, ?, ?, ?, ?)',
                [PESQUISA_A_KEY, "missing", None, "A", "q2", "id"],
            )
        columns = [
            row[1]
            for row in self.db.execute('PRAGMA table_info("FATO_PESQUISA_PERGUNTA")').fetchall()
        ]
        self.assertEqual(
            columns,
            [
                "sk_pesquisa",
                "sk_pergunta",
                "sk_data_pesquisa",
                "pesquisa_id_origem",
                "pergunta_id_origem",
                "metodo_vinculo",
            ],
        )

    def test_direct_id_rejects_question_a_with_research_b(self) -> None:
        for wrong_research, original_id, method in (
            (PESQUISA_B_KEY, "A", "id"),
            (UNKNOWN_PESQUISA_KEY, "A", "id"),
            (PESQUISA_A_KEY, "B", "id"),
            (PESQUISA_B_KEY, "A", "desconhecido"),
        ):
            with self.subTest(wrong_research=wrong_research, method=method):
                with self.assertRaises(duckdb.ConstraintException):
                    self.db.execute(
                        'INSERT INTO "FATO_PESQUISA_PERGUNTA" VALUES (?, ?, ?, ?, ?, ?)',
                        [wrong_research, PERGUNTA_A_KEY, None, original_id, "q1", method],
                    )

    def test_orphan_and_title_remap_have_explicit_methods(self) -> None:
        self.db.execute(
            'INSERT INTO "FATO_PESQUISA_PERGUNTA" VALUES (?, ?, ?, ?, ?, ?)',
            [UNKNOWN_PESQUISA_KEY, PERGUNTA_ORFA_KEY, None, "X", "q2", "desconhecido"],
        )
        # A carga prova o título único e registra origem/alvo antes deste método.
        self.db.execute(
            'INSERT INTO "FATO_PESQUISA_PERGUNTA" VALUES (?, ?, ?, ?, ?, ?)',
            [PESQUISA_B_KEY, PERGUNTA_TITULO_KEY, None, "Y", "q3", "titulo_unico"],
        )


if __name__ == "__main__":
    unittest.main()
