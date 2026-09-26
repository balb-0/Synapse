"""Contrato executável das dimensões analíticas."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from etl.analytics.dimensions_ddl import (  # noqa: E402
    DIMENSIONS,
    SQL_PATH,
    canonical_key,
    render_ddl,
    surrogate_key,
    unknown_key,
)

try:
    import duckdb
except ImportError:
    duckdb = None


class DimensionContractTests(unittest.TestCase):
    def test_versioned_sql_matches_python(self) -> None:
        self.assertEqual(SQL_PATH.read_text(encoding="utf-8"), render_ddl())

    def test_all_dimensions_have_distinct_namespace_keys(self) -> None:
        self.assertEqual(len(DIMENSIONS), 12)
        self.assertEqual(len({d.name for d in DIMENSIONS}), 12)
        self.assertEqual(len({unknown_key(d.name) for d in DIMENSIONS}), 12)
        self.assertNotEqual(
            surrogate_key("DIM_PESQUISA", "112"), surrogate_key("DIM_EMPRESA", "112")
        )

    def test_canonical_composites_are_unambiguous(self) -> None:
        self.assertNotEqual(canonical_key("1", "23"), canonical_key("12", "3"))
        self.assertNotEqual(canonical_key(None), canonical_key(""))
        self.assertNotEqual(canonical_key("a:b", "c"), canonical_key("a", "b:c"))


@unittest.skipIf(duckdb is None, "duckdb não instalado")
class DimensionDuckDbTests(unittest.TestCase):
    def setUp(self) -> None:
        self.con = duckdb.connect(":memory:")
        self.con.execute(render_ddl())

    def tearDown(self) -> None:
        self.con.close()

    def test_ddl_can_be_reapplied_without_losing_rows(self) -> None:
        self.con.execute(render_ddl())
        for dim in DIMENSIONS:
            with self.subTest(table=dim.name):
                row = self.con.execute(
                    f'SELECT "{dim.sk}", is_unknown, natural_key FROM "{dim.name}"'
                ).fetchall()
                self.assertEqual(row, [(unknown_key(dim.name), True, None)])

    def test_hash_and_natural_identity_constraints(self) -> None:
        natural = canonical_key("112")
        key = surrogate_key("DIM_PESQUISA", "112")
        self.con.execute(
            "INSERT INTO DIM_PESQUISA (sk_pesquisa, natural_key, pesquisa_id, titulo) "
            "VALUES (?, ?, ?, ?)",
            [key, natural, "112", "Pesquisa"],
        )
        with self.assertRaises(duckdb.ConstraintException):
            self.con.execute(
                "INSERT INTO DIM_PESQUISA (sk_pesquisa, natural_key, pesquisa_id) VALUES (?, ?, ?)",
                ["0" * 64, canonical_key("113"), "113"],
            )
        with self.assertRaises(duckdb.ConstraintException):
            self.con.execute(
                "INSERT INTO DIM_PESQUISA (sk_pesquisa, natural_key, pesquisa_id) VALUES (?, ?, ?)",
                [surrogate_key("DIM_PESQUISA", "113"), canonical_key("113"), "114"],
            )
        with self.assertRaises(duckdb.ConstraintException):
            self.con.execute(
                "INSERT INTO DIM_PESQUISA (sk_pesquisa, natural_key, pesquisa_id) VALUES (?, ?, ?)",
                [surrogate_key("DIM_PESQUISA", "114"), canonical_key("114"), None],
            )

    def test_every_dimension_rejects_natural_key_disagreeing_with_identity(self) -> None:
        for dim in DIMENSIONS:
            if dim.name == "DIM_TEMPO":
                continue  # Atributos de calendário testados separadamente.
            actual = tuple("valor" for _ in dim.identity_columns)
            wrong = tuple("outro" for _ in dim.identity_columns)
            fields = ", ".join((dim.sk, "natural_key", *dim.identity_columns))
            placeholders = ", ".join("?" for _ in range(2 + len(actual)))
            with self.subTest(table=dim.name), self.assertRaises(duckdb.ConstraintException):
                self.con.execute(
                    f'INSERT INTO "{dim.name}" ({fields}) VALUES ({placeholders})',
                    [surrogate_key(dim.name, *wrong), canonical_key(*wrong), *actual],
                )

    def test_profile_nullable_part_and_question_composite_use_canonical_identity(self) -> None:
        self.con.execute(
            "INSERT INTO DIM_PERFIL_PESQUISA "
            "(sk_perfil, natural_key, complexidade, tipo_resposta) VALUES (?, ?, ?, ?)",
            [
                surrogate_key("DIM_PERFIL_PESQUISA", None, "aberta"),
                canonical_key(None, "aberta"),
                None,
                "aberta",
            ],
        )
        self.con.execute(
            "INSERT INTO DIM_PERGUNTA "
            "(sk_pergunta, natural_key, pesquisa_id, pergunta_id) VALUES (?, ?, ?, ?)",
            [surrogate_key("DIM_PERGUNTA", "112", "7"), canonical_key("112", "7"), "112", "7"],
        )

    def test_calendar_attributes_match_date_and_profile_absence_uses_unknown(self) -> None:
        self.con.execute(
            "INSERT INTO DIM_TEMPO "
            "(sk_tempo, natural_key, data, ano, trimestre, mes, dia, dia_semana, fim_mes) "
            "VALUES (?, ?, DATE '2026-09-30', 2026, 3, 9, 30, 3, TRUE)",
            [surrogate_key("DIM_TEMPO", "2026-09-30"), canonical_key("2026-09-30")],
        )
        with self.assertRaises(duckdb.ConstraintException):
            self.con.execute(
                "INSERT INTO DIM_TEMPO "
                "(sk_tempo, natural_key, data, ano, trimestre, mes, dia, dia_semana, fim_mes) "
                "VALUES (?, ?, DATE '2026-10-01', 2026, 4, 13, 1, 4, FALSE)",
                [surrogate_key("DIM_TEMPO", "2026-10-01"), canonical_key("2026-10-01")],
            )
        with self.assertRaises(duckdb.ConstraintException):
            self.con.execute(
                "INSERT INTO DIM_TEMPO "
                "(sk_tempo, natural_key, data, ano, trimestre, mes, dia, dia_semana, fim_mes) "
                "VALUES (?, ?, DATE '2026-10-01', 2026, 4, 10, 1, 4, FALSE)",
                [surrogate_key("DIM_TEMPO", "2026-10-02"), canonical_key("2026-10-02")],
            )
        with self.assertRaises(duckdb.ConstraintException):
            self.con.execute(
                "INSERT INTO DIM_PERFIL_PESQUISA (sk_perfil, natural_key) VALUES (?, ?)",
                [surrogate_key("DIM_PERFIL_PESQUISA", None, None), canonical_key(None, None)],
            )

    def test_question_key_is_composite_and_no_email_column_exists(self) -> None:
        columns = {
            row[1] for row in self.con.execute("PRAGMA table_info('DIM_PERGUNTA')").fetchall()
        }
        self.assertIn("pesquisa_id", columns)
        self.assertIn("pergunta_id", columns)
        person_columns = {
            row[1] for row in self.con.execute("PRAGMA table_info('DIM_PESSOA')").fetchall()
        }
        self.assertNotIn("email", person_columns)
        self.assertNotIn(
            "regiao",
            {row[1] for row in self.con.execute("PRAGMA table_info('DIM_EMPRESA')").fetchall()},
        )
        self.assertNotIn(
            "ano_edicao",
            {row[1] for row in self.con.execute("PRAGMA table_info('DIM_PESQUISA')").fetchall()},
        )


if __name__ == "__main__":
    unittest.main()
