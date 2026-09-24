"""Provas do grão e dos vínculos dos fatos C01/C02."""

import unittest

import duckdb
from etl.analytics.dimensions_ddl import canonical_key, dimension_statements, surrogate_key

from etl.analytics.facts_cycle_participation import SQL_PATH, fact_statements, render_ddl


def insert_dimension(db, table, sk_column, identity_columns, *parts):
    key = surrogate_key(table, *parts)
    columns = [sk_column, "natural_key", *identity_columns]
    quoted_columns = ", ".join(f'"{column}"' for column in columns)
    placeholders = ", ".join("?" for _ in columns)
    db.execute(
        f'INSERT INTO "{table}" ({quoted_columns}) VALUES ({placeholders})',
        [key, canonical_key(*parts), *parts],
    )
    return key


class FactCycleParticipationTests(unittest.TestCase):
    def setUp(self):
        self.db = duckdb.connect(":memory:")
        for statement in (*dimension_statements(), *fact_statements()):
            self.db.execute(statement)

    def tearDown(self):
        self.db.close()

    def seed_dimensions(self):
        pesquisa = insert_dimension(self.db, "DIM_PESQUISA", "sk_pesquisa", ("pesquisa_id",), "P-1")
        empresa = insert_dimension(self.db, "DIM_EMPRESA", "sk_empresa", ("empresa_id",), "E-1")
        fonte = insert_dimension(self.db, "DIM_FONTE_DADO", "sk_fonte", ("source",), "pesquisas")
        carga = insert_dimension(
            self.db, "DIM_EXECUCAO_CARGA", "sk_carga", ("source", "run_id"), "pesquisas", "R-1"
        )
        return pesquisa, empresa, fonte, carga

    def test_versioned_file_executes_after_dimensions_twice(self):
        self.assertEqual(SQL_PATH.read_text(encoding="utf-8"), render_ddl())
        dimension_sql = SQL_PATH.with_name("002_dimensoes.sql").read_text(encoding="utf-8")
        db = duckdb.connect(":memory:")
        try:
            db.execute(dimension_sql)
            for _ in range(2):
                db.execute(SQL_PATH.read_text(encoding="utf-8"))
            self.assertEqual(
                db.execute("SELECT count(*) FROM FATO_CICLO_PESQUISA").fetchone(), (0,)
            )
            self.assertEqual(db.execute("SELECT count(*) FROM FATO_PARTICIPACAO").fetchone(), (0,))
        finally:
            db.close()

    def test_cycle_grain_nullable_measures_and_foreign_keys(self):
        pesquisa, _empresa, fonte, carga = self.seed_dimensions()
        statement = (
            "INSERT INTO FATO_CICLO_PESQUISA "
            "(sk_pesquisa, sk_fonte, sk_carga, flag_prorrogada) "
            "VALUES (?, ?, ?, FALSE)"
        )
        self.db.execute(statement, [pesquisa, fonte, carga])
        self.assertEqual(
            self.db.execute(
                "SELECT dias_corridos_validacao, qtd_empresas_na_pesquisa FROM FATO_CICLO_PESQUISA"
            ).fetchone(),
            (None, None),
        )
        with self.assertRaises(duckdb.ConstraintException):
            self.db.execute(statement, [pesquisa, fonte, carga])
        with self.assertRaises(duckdb.ConstraintException):
            self.db.execute(statement, ["orphan", fonte, carga])
        with self.assertRaises(duckdb.ConstraintException):
            self.db.execute(
                "UPDATE FATO_CICLO_PESQUISA SET dias_corridos_coleta = -1 WHERE sk_pesquisa = ?",
                [pesquisa],
            )

    def test_participation_physical_grain_and_foreign_keys(self):
        pesquisa, empresa, _fonte, _carga = self.seed_dimensions()
        statement = (
            "INSERT INTO FATO_PARTICIPACAO "
            "(source_checksum, source_offset, sk_pesquisa, sk_empresa, "
            "minutos_preenchimento) VALUES (?, ?, ?, ?, ?)"
        )
        self.db.execute(statement, ["file-A", 10, pesquisa, empresa, 5])
        self.db.execute(statement, ["file-A", 11, pesquisa, empresa, 5])
        self.assertEqual(
            self.db.execute("SELECT sum(qtd_participacao) FROM FATO_PARTICIPACAO").fetchone(),
            (2,),
        )
        with self.assertRaises(duckdb.ConstraintException):
            self.db.execute(statement, ["file-A", 10, pesquisa, empresa, 5])
        with self.assertRaises(duckdb.ConstraintException):
            self.db.execute(statement, ["file-A", 12, pesquisa, "orphan", 5])
        with self.assertRaises(duckdb.ConstraintException):
            self.db.execute(
                "UPDATE FATO_PARTICIPACAO SET seq_ocorrencia = 1 "
                "WHERE source_checksum = 'file-A' AND source_offset = 10"
            )

    def test_unavailable_minutes_require_reason(self):
        pesquisa, empresa, _fonte, _carga = self.seed_dimensions()
        statement = (
            "INSERT INTO FATO_PARTICIPACAO "
            "(source_checksum, source_offset, sk_pesquisa, sk_empresa, "
            "minutos_preenchimento, motivo_minutos_indisponivel) "
            "VALUES (?, ?, ?, ?, ?, ?)"
        )
        self.db.execute(statement, ["file-B", 1, pesquisa, empresa, None, "hora_inicio_ausente"])
        with self.assertRaises(duckdb.ConstraintException):
            self.db.execute(statement, ["file-B", 2, pesquisa, empresa, None, None])
        with self.assertRaises(duckdb.ConstraintException):
            self.db.execute(statement, ["file-B", 3, pesquisa, empresa, 5, "erro"])


if __name__ == "__main__":
    unittest.main()
