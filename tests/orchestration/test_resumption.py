"""Retomada de carga depois de uma falha parcial entre lotes do mesmo objeto.

O checkpoint de um lote só era confirmado depois que todos os lotes do
objeto tivessem carregado com sucesso. Uma falha no meio (lote 2 de 3, por
exemplo) não deixava nenhum checkpoint confirmado, e a próxima tentativa
reextraía e retransformava até os lotes que já tinham sido carregados —
que o repositório converge sem duplicar, mas cujo registro de execução
deixava de refletir corretamente o que já estava confirmado. Este arquivo
cobre a confirmação lote a lote: o que sobrevive a uma falha no meio, e o
que a tentativa seguinte retoma a partir do checkpoint deixado por ela.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction.contracts import (  # noqa: E402
    BatchMetadata,
    ExtractedBatch,
    ExtractionCheckpoint,
)
from etl.transformation.consistency import ReferenceData  # noqa: E402
from etl.transformation.pipeline import transform_batch  # noqa: E402

DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None
PREFECT_INSTALLED = importlib.util.find_spec("prefect") is not None
if DUCKDB_INSTALLED and PREFECT_INSTALLED:
    from etl.load.duckdb_repository import DuckDbLoadRepository
    from etl.orchestration import flow as flow_module

SEM_DEPENDENCIAS = "duckdb e prefect não instalados; use pip install -r requirements.txt"

NOW = datetime(2026, 9, 10, 12, tzinfo=timezone.utc)
SOURCE_VERSION = "sha256:" + "a" * 64


def _batch(rows: list[dict], *, sequence: int, run_id: str = "run-1") -> ExtractedBatch:
    metadata = BatchMetadata(
        "pesquisas",
        run_id,
        "extract-pesquisas",
        f"pesquisas-{sequence:06d}",
        NOW,
        NOW + timedelta(seconds=1),
        len(rows),
        100,
        "1.0",
        SOURCE_VERSION.removeprefix("sha256:"),
    )
    checkpoint = ExtractionCheckpoint("pesquisas", f"row:{sequence}", sequence, SOURCE_VERSION)
    return ExtractedBatch(rows, checkpoint, metadata)


def _transformed(batch: ExtractedBatch):
    return transform_batch(
        batch, references=ReferenceData({}), previous={}, source_offset=0, ingested_at=NOW
    )


@unittest.skipUnless(DUCKDB_INSTALLED and PREFECT_INSTALLED, SEM_DEPENDENCIAS)
class LoadCommitsTheCheckpointBatchByBatchTests(unittest.TestCase):
    """`load` confirma o checkpoint assim que cada lote termina, não só no fim."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "ingestao.duckdb"
        logger_patch = mock.patch.object(flow_module, "get_run_logger", return_value=mock.MagicMock())
        logger_patch.start()
        self.addCleanup(logger_patch.stop)

    def _load(self, results: list) -> list:
        return flow_module.load.fn(str(self.database_path), results, {})

    def _checkpoint(self):
        with DuckDbLoadRepository(self.database_path) as repo:
            return repo.load("pesquisas")

    def _count(self) -> int:
        with DuckDbLoadRepository(self.database_path) as repo:
            return repo.count("pesquisas")

    def test_all_batches_succeeding_advances_the_checkpoint_to_the_last_one(self) -> None:
        batch1 = _batch([{"id": "1", "titulo": "A"}], sequence=1)
        batch2 = _batch([{"id": "2", "titulo": "B"}], sequence=2)
        results = [
            (_transformed(batch1), batch1.metadata, batch1.checkpoint),
            (_transformed(batch2), batch2.metadata, batch2.checkpoint),
        ]

        self._load(results)

        checkpoint = self._checkpoint()
        self.assertEqual(checkpoint.sequence, 2)
        self.assertEqual(checkpoint.position, "row:2")
        self.assertEqual(self._count(), 2)

    def test_a_batch_that_fails_does_not_advance_the_checkpoint_past_the_last_success(
        self,
    ) -> None:
        batch1 = _batch([{"id": "1", "titulo": "A"}], sequence=1)
        batch2 = _batch([{"id": "2", "titulo": "B"}], sequence=2)
        results = [
            (_transformed(batch1), batch1.metadata, batch1.checkpoint),
            (_transformed(batch2), batch2.metadata, batch2.checkpoint),
        ]

        original_load_batch = DuckDbLoadRepository.load_batch

        def flaky_load_batch(self, result, metadata):
            if metadata.batch_id == batch2.metadata.batch_id:
                raise RuntimeError("falha simulada de carga")
            return original_load_batch(self, result, metadata)

        with mock.patch.object(DuckDbLoadRepository, "load_batch", flaky_load_batch):
            with self.assertRaisesRegex(RuntimeError, "falha simulada de carga"):
                self._load(results)

        checkpoint = self._checkpoint()
        self.assertEqual(checkpoint.sequence, 1)
        self.assertEqual(checkpoint.position, "row:1")
        # o lote confirmado antes da falha permanece; o que falhou não chegou
        # a gravar nada.
        self.assertEqual(self._count(), 1)

    def test_resuming_after_the_failure_loads_only_the_remaining_batch_without_duplicating(
        self,
    ) -> None:
        batch1 = _batch([{"id": "1", "titulo": "A"}], sequence=1)
        batch2 = _batch([{"id": "2", "titulo": "B"}], sequence=2)

        original_load_batch = DuckDbLoadRepository.load_batch

        def flaky_load_batch(self, result, metadata):
            if metadata.batch_id == batch2.metadata.batch_id:
                raise RuntimeError("falha simulada de carga")
            return original_load_batch(self, result, metadata)

        with mock.patch.object(DuckDbLoadRepository, "load_batch", flaky_load_batch):
            with self.assertRaises(RuntimeError):
                self._load(
                    [
                        (_transformed(batch1), batch1.metadata, batch1.checkpoint),
                        (_transformed(batch2), batch2.metadata, batch2.checkpoint),
                    ]
                )

        # a retomada extrai só a partir do checkpoint confirmado: quem chama
        # de novo não reapresenta o lote 1, só o que ficou pendente.
        self._load([(_transformed(batch2), batch2.metadata, batch2.checkpoint)])

        checkpoint = self._checkpoint()
        self.assertEqual(checkpoint.sequence, 2)
        self.assertEqual(self._count(), 2)


@unittest.skipUnless(DUCKDB_INSTALLED and PREFECT_INSTALLED, SEM_DEPENDENCIAS)
class TransformForwardsTheBatchCheckpointTests(unittest.TestCase):
    """`transform` precisa repassar o checkpoint de cada lote para `load` confirmar."""

    def setUp(self) -> None:
        logger_patch = mock.patch.object(flow_module, "get_run_logger", return_value=mock.MagicMock())
        logger_patch.start()
        self.addCleanup(logger_patch.stop)

    def test_each_result_carries_its_own_batch_checkpoint(self) -> None:
        batch = _batch([{"id": "1", "titulo": "A"}], sequence=1)

        results = flow_module.transform.fn([batch], "pesquisas", ReferenceData({}), {})

        self.assertEqual(len(results), 1)
        _, metadata, checkpoint = results[0]
        self.assertEqual(metadata, batch.metadata)
        self.assertEqual(checkpoint, batch.checkpoint)


if __name__ == "__main__":
    unittest.main()
