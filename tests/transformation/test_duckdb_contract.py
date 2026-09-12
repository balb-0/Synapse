"""Contrato executável: cada registro tratado é aceito pelo DuckDB real."""

import importlib.util
import json
import unittest

from etl.transformation.schema import destination_columns
from tests.transformation.test_transformation import RAW, run

DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None

if DUCKDB_INSTALLED:
    import duckdb


@unittest.skipUnless(DUCKDB_INSTALLED, "duckdb não instalado; use pip install -r requirements.txt")
class DuckDBContractTests(unittest.TestCase):
    def test_six_schemas_accept_transformed_rows(self):
        for source, record in RAW.items():
            with self.subTest(source=source), duckdb.connect(":memory:") as connection:
                raw = dict(record)
                if source == "empresas":
                    raw["% de mercado"] = "12,345678%"
                if source == "pesquisas":
                    raw["data_solicitacao"] = "09/09/2026"
                if source == "respondentes":
                    raw["hora_inicio"] = "2026-09-09T09:00:00-03:00"

                row = run(source, [raw]).accepted[0].as_duckdb_row()
                columns = destination_columns(source)
                self.assertEqual(set(row), set(columns))
                definition = ", ".join(f'"{name}" {kind}' for name, kind in columns.items())
                connection.execute(f'CREATE TABLE "ingestao" ({definition})')
                names = ", ".join(f'"{name}"' for name in columns)
                placeholders = ", ".join("?" for _ in columns)
                values = [
                    json.dumps(row[name]) if isinstance(row[name], list) else row[name]
                    for name in columns
                ]
                connection.execute(
                    f'INSERT INTO "ingestao" ({names}) VALUES ({placeholders})', values
                )
                self.assertEqual(
                    connection.execute('SELECT count(*) FROM "ingestao"').fetchone(), (1,)
                )
