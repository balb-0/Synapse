"""Contrato das variáveis de ambiente.

Prova que nenhuma variável documentada fica sem efeito:

- toda chave ``ETL_*`` do ``.env.example`` é reconhecida por ao menos um dos
  dois contratos de configuração (extração ou carga);
- o conjunto documentado no runbook (incluindo o tuning ``ETL_DUCKDB_*``,
  ausente do ``.env.example``) carrega sem erro quando preenchido;
- flow e repositório usam o mesmo contrato (``load_duckdb_settings``): o
  caminho do banco é único por ambiente, não há mais ``DUCKDB_PATH`` nem
  ``ETL_MINIO_SECURE`` paralelos.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction.config import ENVIRONMENT_VARIABLES as EXTRACTION_VARS  # noqa: E402
from etl.extraction.config import load_extraction_settings  # noqa: E402
from etl.load.config import ENVIRONMENT_VARIABLES as LOAD_VARS  # noqa: E402
from etl.load.config import load_duckdb_settings  # noqa: E402


def _env_keys() -> list[str]:
    keys = []
    for line in (REPOSITORY_ROOT / ".env.example").read_text().splitlines():
        line = line.strip()
        if line.startswith("ETL_") and "=" in line:
            keys.append(line.split("=", 1)[0])
    return keys


class EnvContractTest(unittest.TestCase):
    def test_toda_var_do_env_example_eh_lida(self):
        conhecidas = set(EXTRACTION_VARS.values()) | set(LOAD_VARS.values())
        desconhecidas = [key for key in _env_keys() if key not in conhecidas]
        self.assertEqual(desconhecidas, [], f"variáveis sem efeito: {desconhecidas}")

    def test_sem_variavel_paralela_antiga(self):
        conhecidas = set(EXTRACTION_VARS.values()) | set(LOAD_VARS.values())
        self.assertNotIn("DUCKDB_PATH", conhecidas)
        self.assertNotIn("ETL_MINIO_SECURE", conhecidas)

    def test_contratos_carregam_o_conjunto_documentado(self):
        environ = {
            "ETL_MINIO_ENDPOINT": "http://minio:9000",
            "ETL_MINIO_BUCKET": "sindusfarma",
            "ETL_MINIO_INPUT_PREFIX": "landing",
            "ETL_MINIO_ACCESS_KEY": "teste",
            "ETL_MINIO_SECRET_KEY": "teste",
            "ETL_REQUEST_TIMEOUT_SECONDS": "30",
            "ETL_EXTRACTION_BATCH_SIZE": "1000",
            "ETL_EXTRACTION_MAX_ATTEMPTS": "3",
            "ETL_EXTRACTION_RETRY_INITIAL_DELAY_SECONDS": "0.5",
            "ETL_EXTRACTION_RETRY_MAX_DELAY_SECONDS": "5",
            "ETL_SOURCE_DIR": "",
            "ETL_DUCKDB_PATH": "data/duckdb/ingestao.duckdb",
            "ETL_DUCKDB_THREADS": "2",
            "ETL_DUCKDB_MEMORY_LIMIT": "1GB",
            "ETL_DUCKDB_WRITE_LOCK_TIMEOUT_SECONDS": "300",
        }
        extraction = load_extraction_settings(environ=environ)
        duckdb_settings = load_duckdb_settings(environ=environ)
        self.assertEqual(extraction.minio_bucket, "sindusfarma")
        self.assertEqual(
            str(duckdb_settings.database_path),
            os.path.abspath(os.path.join("data", "duckdb", "ingestao.duckdb")),
        )
        self.assertEqual(duckdb_settings.threads, 2)


if __name__ == "__main__":
    unittest.main()
