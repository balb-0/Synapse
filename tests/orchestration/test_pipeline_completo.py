"""Testes do comando único de backfill seguido de carga analítica (PL-01).

O contrato coberto aqui é o encadeamento: mesmo `db_path` nas duas etapas,
carga analítica somente após todas as fontes configuradas concluírem, e a
saída com identificadores e status por etapa. O backfill e a carga analítica
em si já têm suítes próprias (gray-box de orquestração e tests/analytics);
aqui os dois são substituídos por dublês que registram como foram chamados.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.analytics.load import LoadResult  # noqa: E402
from etl.orchestration import pipeline as pipeline_module  # noqa: E402
from etl.orchestration.pipeline import PipelineAbortedError, run_pipeline  # noqa: E402

BUCKET = "landing-test"
AMBIENTE_FICTICIO = {
    "ETL_MINIO_ENDPOINT": "http://minio.invalid:9000",
    "ETL_MINIO_BUCKET": BUCKET,
    "ETL_MINIO_ACCESS_KEY": "teste-sem-segredo",
    "ETL_MINIO_SECRET_KEY": "teste-sem-segredo",
}

RESULTADO_ANALITICO = LoadResult(
    load_id="carga-teste",
    pesquisas=3,
    participacoes=5,
    perguntas=2,
    orfaos=0,
    respondentes_checksum=None,
    fechamento=date(2026, 9, 30),
)


def relatorio_backfill(statuses: dict[str, str]) -> dict:
    return {
        "mode": "backfill",
        "reprocess": False,
        "sources": list(statuses),
        "results": [{"source": source, "status": status} for source, status in statuses.items()],
    }


class PipelineCompletoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = str(Path(self.temporary_directory.name) / "pipeline.duckdb")
        ambiente = mock.patch.dict(
            os.environ, {**AMBIENTE_FICTICIO, "ETL_DUCKDB_PATH": self.database_path}
        )
        self.addCleanup(ambiente.stop)
        ambiente.start()
        self.chamadas: list[tuple] = []

    def _backfill_falso(self, statuses: dict[str, str]):
        def backfill(*, sources, bucket, prefix, reprocess, db_path):
            self.chamadas.append(("backfill", tuple(sources), bucket, prefix, db_path))
            return relatorio_backfill(statuses or dict.fromkeys(sources, "loaded"))

        return backfill

    def _carga_falsa(self):
        def load_analytics(con, *, observed_at=None):
            self.chamadas.append(("analytics", observed_at))
            return RESULTADO_ANALITICO

        return load_analytics

    def executar(self, statuses: dict[str, str] | None = None, **kwargs) -> dict:
        with (
            mock.patch.object(pipeline_module, "backfill", self._backfill_falso(statuses or {})),
            mock.patch.object(pipeline_module, "load_analytics", self._carga_falsa()),
        ):
            return run_pipeline(**kwargs)

    def test_sucesso_encadeia_backfill_e_carga_no_mesmo_banco(self) -> None:
        resultado = self.executar()

        etapas = [chamada[0] for chamada in self.chamadas]
        self.assertEqual(etapas, ["backfill", "analytics"])
        self.assertEqual(self.chamadas[0][1], pipeline_module.DEFAULT_SOURCES)
        self.assertEqual(self.chamadas[0][2], BUCKET)
        self.assertEqual(self.chamadas[0][4], self.database_path)
        self.assertEqual(resultado["db_path"], self.database_path)

    def test_saida_registra_status_por_fonte_e_load_id(self) -> None:
        resultado = self.executar(statuses={"empresas": "loaded", "pesquisas": "ignored"})

        por_fonte = {r["source"]: r["status"] for r in resultado["backfill"]["results"]}
        self.assertEqual(por_fonte, {"empresas": "loaded", "pesquisas": "ignored"})
        self.assertEqual(resultado["analytics"]["load_id"], "carga-teste")
        self.assertEqual(resultado["status"], "completed")

    def test_fonte_sem_conclusao_bloqueia_carga_analitica(self) -> None:
        with self.assertRaises(PipelineAbortedError) as contexto:
            self.executar(statuses={"empresas": "loaded", "pesquisas": "failed"})

        self.assertIn("pesquisas", str(contexto.exception))
        etapas = [chamada[0] for chamada in self.chamadas]
        self.assertEqual(etapas, ["backfill"])

    def test_fonte_ignorada_conta_como_concluida(self) -> None:
        resultado = self.executar(
            statuses=dict.fromkeys(pipeline_module.DEFAULT_SOURCES, "ignored")
        )

        self.assertEqual(resultado["status"], "completed")
        etapas = [chamada[0] for chamada in self.chamadas]
        self.assertEqual(etapas, ["backfill", "analytics"])

    def test_fonte_desconhecida_falha_antes_do_backfill(self) -> None:
        with self.assertRaises(ValueError):
            self.executar(sources=["inexistente"])

        self.assertEqual(self.chamadas, [])


if __name__ == "__main__":
    unittest.main()
