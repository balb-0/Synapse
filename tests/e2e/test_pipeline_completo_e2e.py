"""Teste black-box e2e do pipeline completo coordenado (PL-04).

Cobre o encadeamento integral a partir de fixtures sintéticas versionadas:
    fontes (CSV) -> ingestão -> cubos analíticos -> reconciliação -> 7 Parquet

Valida que:
1. O caminho de sucesso consome as seis fontes sintéticas, popula a camada tratada
   e os quatro cubos no DuckDB, passa na reconciliação e gera os sete arquivos
   Parquet com manifesto e ponteiro ``current.json`` íntegros.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import BinaryIO
from unittest import mock

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction import ObjectReference  # noqa: E402
from etl.orchestration import flow as flow_module  # noqa: E402
from etl.orchestration.pipeline import run_pipeline  # noqa: E402
from tests import fixtures  # noqa: E402

DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None
if DUCKDB_INSTALLED:
    import duckdb

SEM_DUCKDB = "duckdb não instalado; use pip install -r requirements.txt"

BUCKET = "landing-test"
AMBIENTE_FICTICIO = {
    "ETL_MINIO_ENDPOINT": "http://minio.invalid:9000",
    "ETL_MINIO_BUCKET": BUCKET,
    "ETL_MINIO_INPUT_PREFIX": "landing",
    "ETL_MINIO_ACCESS_KEY": "teste-sem-segredo",
    "ETL_MINIO_SECRET_KEY": "teste-sem-segredo",
}

SETE_TABELAS_ESPERADAS = frozenset(
    {
        "PUB_C01_CICLO",
        "PUB_C02_PARTICIPACAO",
        "PUB_C03_PIPELINE_MENSAL",
        "PUB_C04_INSTRUMENTO",
        "PUB_QUALIDADE_CAMPO",
        "PUB_QUALIDADE_RELACAO",
        "PUB_QUALIDADE_DUPLICIDADE",
    }
)


class LeitorEmMemoria:
    """``ObjectReader`` que serve payloads por chave para o fluxo de orquestração."""

    def __init__(self, payloads: dict[str, bytes]) -> None:
        self.payloads = payloads
        self.aberturas: list[str] = []

    @contextmanager
    def open(self, reference: ObjectReference) -> Iterator[BinaryIO]:
        self.aberturas.append(reference.key)
        stem = Path(reference.key).stem
        if stem not in self.payloads:
            raise FileNotFoundError(f"objeto inexistente nas fixtures: {reference.key}")
        yield BytesIO(self.payloads[stem])


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class PipelineCompletoE2ETests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root_path = Path(self.temporary_directory.name)
        self.database_path = str(self.root_path / "pipeline_e2e.duckdb")
        self.publish_dir = str(self.root_path / "publicacao_bi")

        self.payloads = {source: fixtures.payload(source) for source in fixtures.ORDEM_CARGA}
        self.leitor = LeitorEmMemoria(self.payloads)

        ambiente_mock = mock.patch.dict(os.environ, AMBIENTE_FICTICIO)
        self.addCleanup(ambiente_mock.stop)
        ambiente_mock.start()

        leitor_mock = mock.patch.object(
            flow_module, "MinioObjectReader", lambda client: self.leitor
        )
        self.addCleanup(leitor_mock.stop)
        leitor_mock.start()

    def test_caminho_sucesso_fonte_ingestao_cubos_e_sete_arquivos(self) -> None:
        resultado = run_pipeline(
            db_path=self.database_path,
            publish_dir=self.publish_dir,
        )

        self.assertEqual(resultado["status"], "completed")
        self.assertEqual(resultado["db_path"], self.database_path)

        backfill_statuses = {
            item["source"]: item["status"] for item in resultado["backfill"]["results"]
        }
        for source in fixtures.ORDEM_CARGA:
            self.assertEqual(backfill_statuses.get(source), "loaded")

        analytics_info = resultado["analytics"]
        load_id = analytics_info["load_id"]
        self.assertTrue(load_id)
        self.assertGreater(analytics_info["pesquisas"], 0)
        self.assertGreater(analytics_info["participacoes"], 0)
        self.assertGreater(analytics_info["perguntas"], 0)
        self.assertEqual(analytics_info["orfaos"], 0)

        reconciliation_info = resultado["reconciliation"]
        self.assertTrue(reconciliation_info["reconciled"])
        self.assertEqual(reconciliation_info["load_id"], load_id)

        publication_info = resultado["publication"]
        generation = publication_info["generation"]
        self.assertTrue(generation)
        self.assertEqual(publication_info["load_reference"], load_id)
        self.assertEqual(set(publication_info["tables"].keys()), SETE_TABELAS_ESPERADAS)

        with duckdb.connect(self.database_path, read_only=True) as con:
            for source in fixtures.ORDEM_CARGA:
                tabela_ingestao = f"ingestao_{source}"
                contagem = con.execute(f'SELECT count(*) FROM "{tabela_ingestao}"').fetchone()[0]
                self.assertGreater(contagem, 0)

            for fato in (
                "FATO_CICLO_PESQUISA",
                "FATO_PARTICIPACAO",
                "FATO_PIPELINE_MENSAL",
                "FATO_PESQUISA_PERGUNTA",
            ):
                tabelas_fatos = [row[0] for row in con.execute("SHOW TABLES").fetchall()]
                self.assertIn(fato, tabelas_fatos)

        dir_publicacao = Path(self.publish_dir)
        current_file = dir_publicacao / "current.json"
        self.assertTrue(current_file.is_file(), "current.json não foi criado na pasta de publicação")

        current_data = json.loads(current_file.read_text(encoding="utf-8"))
        self.assertEqual(current_data, {"generation": generation})

        generation_dir = dir_publicacao / generation
        self.assertTrue(generation_dir.is_dir(), f"diretório da geração {generation} não existe")

        manifest_file = generation_dir / "manifest.json"
        self.assertTrue(manifest_file.is_file(), "manifest.json não foi criado no diretório da geração")

        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        self.assertEqual(manifest_data["generation"], generation)
        self.assertEqual(manifest_data["load_reference"], load_id)
        self.assertEqual(set(manifest_data["tables"].keys()), SETE_TABELAS_ESPERADAS)

        with duckdb.connect() as con_parquet:
            for nome_tabela, info in manifest_data["tables"].items():
                arquivo_parquet = generation_dir / info["file"]
                self.assertTrue(
                    arquivo_parquet.is_file(),
                    f"arquivo Parquet {info['file']} para {nome_tabela} não encontrado",
                )
                linhas_parquet = con_parquet.execute(
                    f"SELECT count(*) FROM read_parquet('{arquivo_parquet}')"
                ).fetchone()[0]
                self.assertEqual(
                    linhas_parquet,
                    info["rows"],
                    f"contagem no Parquet diverge do manifesto para {nome_tabela}",
                )
                self.assertEqual(
                    linhas_parquet,
                    publication_info["tables"][nome_tabela],
                    f"contagem no Parquet diverge do retorno do flow para {nome_tabela}",
                )


if __name__ == "__main__":
    unittest.main()
