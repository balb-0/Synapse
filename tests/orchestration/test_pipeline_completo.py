"""Testes do comando único do pipeline (PL-01/PL-02).

O contrato coberto aqui é o encadeamento: mesmo `db_path` em todas as etapas,
carga analítica somente após todas as fontes configuradas concluírem,
publicação somente com `reconciled=true` e manifesto apontando o `load_id`
efetivo. Backfill, carga, reconciliação e publicação têm suítes próprias
(gray-box de orquestração e tests/analytics); aqui as quatro rotinas são
substituídas por dublês que registram como foram chamadas.
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
from etl.analytics.reconcile import ReconciliationReport  # noqa: E402
from etl.orchestration import pipeline as pipeline_module  # noqa: E402
from etl.orchestration.pipeline import (  # noqa: E402
    PipelineAbortedError,
    ReconciliationFailedError,
    run_pipeline,
)

BUCKET = "landing-test"
AMBIENTE_FICTICIO = {
    "ETL_MINIO_ENDPOINT": "http://minio.invalid:9000",
    "ETL_MINIO_BUCKET": BUCKET,
    "ETL_MINIO_ACCESS_KEY": "teste-sem-segredo",
    "ETL_MINIO_SECRET_KEY": "teste-sem-segredo",
}

LOAD_ID = "carga-teste"

RESULTADO_ANALITICO = LoadResult(
    load_id=LOAD_ID,
    pesquisas=3,
    participacoes=5,
    perguntas=2,
    orfaos=0,
    respondentes_checksum=None,
    fechamento=date(2026, 9, 30),
)


def relatorio_reconciliacao(*, load_id: str | None = LOAD_ID, digests_match: bool = True):
    """Relatório real com o mínimo de campos; `reconciled` é a propriedade de verdade."""
    return ReconciliationReport(
        load_id=load_id,
        loaded_at="2026-09-29T12:00:00",
        source_digests_match=digests_match,
        respondent_checksum=None,
        respondent_run_id=None,
        cubes=(),
        orphan_reasons=(),
        orphan_audit=(),
        monthly_closures=(),
    )


def manifesto(load_reference: str) -> dict:
    return {
        "version": 1,
        "generation": "geracao-teste",
        "load_reference": load_reference,
        "tables": {f"PUB_{indice}": {"file": "x.parquet", "rows": indice} for indice in range(7)},
    }


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
        self.publish_dir = str(Path(self.temporary_directory.name) / "publicacao")
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

    def _reconciliacao_falsa(self, report):
        def reconcile_analytics(con):
            self.chamadas.append(("reconcile",))
            return report

        return reconcile_analytics

    def _publicacao_falsa(self):
        def publish_cubes(database, output, *, load_reference):
            self.chamadas.append(("publish", str(database), str(output), load_reference))
            return manifesto(load_reference)

        return publish_cubes

    def executar(self, statuses=None, report=None, **kwargs) -> dict:
        report = report if report is not None else relatorio_reconciliacao()
        kwargs.setdefault("publish_dir", self.publish_dir)
        with (
            mock.patch.object(pipeline_module, "backfill", self._backfill_falso(statuses or {})),
            mock.patch.object(pipeline_module, "load_analytics", self._carga_falsa()),
            mock.patch.object(
                pipeline_module, "reconcile_analytics", self._reconciliacao_falsa(report)
            ),
            mock.patch.object(pipeline_module, "publish_cubes", self._publicacao_falsa()),
        ):
            return run_pipeline(**kwargs)

    def etapas(self) -> list[str]:
        return [chamada[0] for chamada in self.chamadas]

    def test_sucesso_encadeia_as_quatro_etapas_no_mesmo_banco(self) -> None:
        resultado = self.executar()

        self.assertEqual(self.etapas(), ["backfill", "analytics", "reconcile", "publish"])
        self.assertEqual(self.chamadas[0][1], pipeline_module.DEFAULT_SOURCES)
        self.assertEqual(self.chamadas[0][2], BUCKET)
        self.assertEqual(self.chamadas[0][4], self.database_path)
        self.assertEqual(self.chamadas[3][1], self.database_path)
        self.assertEqual(resultado["db_path"], self.database_path)

    def test_saida_registra_status_por_fonte_e_ids_por_etapa(self) -> None:
        resultado = self.executar(statuses={"empresas": "loaded", "pesquisas": "ignored"})

        por_fonte = {r["source"]: r["status"] for r in resultado["backfill"]["results"]}
        self.assertEqual(por_fonte, {"empresas": "loaded", "pesquisas": "ignored"})
        self.assertEqual(resultado["analytics"]["load_id"], LOAD_ID)
        self.assertTrue(resultado["reconciliation"]["reconciled"])
        self.assertEqual(resultado["publication"]["generation"], "geracao-teste")
        self.assertEqual(resultado["status"], "completed")

    def test_fonte_sem_conclusao_bloqueia_carga_analitica(self) -> None:
        with self.assertRaises(PipelineAbortedError) as contexto:
            self.executar(statuses={"empresas": "loaded", "pesquisas": "failed"})

        self.assertIn("pesquisas", str(contexto.exception))
        self.assertEqual(self.etapas(), ["backfill"])

    def test_fonte_ignorada_conta_como_concluida(self) -> None:
        resultado = self.executar(
            statuses=dict.fromkeys(pipeline_module.DEFAULT_SOURCES, "ignored")
        )

        self.assertEqual(resultado["status"], "completed")
        self.assertEqual(self.etapas(), ["backfill", "analytics", "reconcile", "publish"])

    def test_fonte_desconhecida_falha_antes_do_backfill(self) -> None:
        with self.assertRaises(ValueError):
            self.executar(sources=["inexistente"])

        self.assertEqual(self.chamadas, [])

    def test_reconciliacao_reprovada_nao_publica_nada(self) -> None:
        with self.assertRaises(ReconciliationFailedError):
            self.executar(report=relatorio_reconciliacao(digests_match=False))

        self.assertEqual(self.etapas(), ["backfill", "analytics", "reconcile"])

    def test_load_id_divergente_nao_publica_nada(self) -> None:
        with self.assertRaises(ReconciliationFailedError):
            self.executar(report=relatorio_reconciliacao(load_id="outra-carga"))

        self.assertEqual(self.etapas(), ["backfill", "analytics", "reconcile"])

    def test_manifesto_aponta_o_load_id_efetivo(self) -> None:
        resultado = self.executar()

        publicacao = self.chamadas[3]
        self.assertEqual(publicacao[3], LOAD_ID)  # load_reference do manifesto
        self.assertEqual(publicacao[2], self.publish_dir)
        self.assertEqual(resultado["publication"]["load_reference"], LOAD_ID)


if __name__ == "__main__":
    unittest.main()
