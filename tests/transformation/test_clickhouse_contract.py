"""Compatibilidade real dos seis schemas, sem alterar MC-03 ou um banco externo."""

import json
import os
import subprocess
import unittest

from etl.transformation.schema import destination_columns
from tests.transformation.test_transformation import RAW, run

IMAGE = "clickhouse/clickhouse-server@sha256:800e82865530eb2f1c4bc1b960e43b435fd9b2d83b4bd04a2564a5cfd88fdb6e"


@unittest.skipUnless(
    os.getenv("ETL_TEST_CLICKHOUSE") == "1", "opt-in: Docker e imagem ClickHouse local"
)
class ClickHouseContractTests(unittest.TestCase):
    def test_six_schemas_accept_transformed_rows(self):
        for source, record in RAW.items():
            with self.subTest(source=source):
                raw = dict(record)
                if source == "empresas":
                    raw["% de mercado"] = "12,345678%"
                if source == "pesquisas":
                    raw["data_solicitacao"] = "09/09/2026"
                if source == "respondentes":
                    raw["hora_inicio"] = "2026-09-09T09:00:00-03:00"
                row = run(source, [raw]).accepted[0].as_clickhouse_row()
                columns = destination_columns(source)
                self.assertEqual(set(row), set(columns))
                structure = ", ".join(f"`{name}` {kind}" for name, kind in columns.items())
                command = [
                    "docker",
                    "run",
                    "--rm",
                    "-i",
                    "--network",
                    "none",
                    "--entrypoint",
                    "clickhouse",
                    IMAGE,
                    "local",
                    "--max_threads",
                    "2",
                    "--structure",
                    structure,
                    "--input-format",
                    "JSONEachRow",
                    "--date_time_input_format",
                    "best_effort",
                    "--query",
                    "SELECT count() FROM table",
                ]
                result = subprocess.run(
                    command,
                    input=json.dumps(row) + "\n",
                    text=True,
                    capture_output=True,
                    timeout=60,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "1")


if __name__ == "__main__":
    unittest.main()
