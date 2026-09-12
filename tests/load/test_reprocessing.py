"""Reexecução do mesmo lote na tabela de ingestão.

A escrita do lote já era atômica, mas o insert principal ainda era um
``INSERT INTO`` puro: reexecutar um lote já gravado (mesmo ``run_id`` e
``batch_id``, por exemplo um retomada depois de uma falha que o chamador não
observou) violava a chave primária em vez de convergir. Este arquivo cobre a
convergência em si — o que fica de fora está registrado em
``docs/repositorio-de-carga.md`` e na ADR 0003.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction.contracts import (  # noqa: E402
    BatchMetadata,
    ExtractedBatch,
    ExtractionCheckpoint,
)
from etl.transformation.consistency import ReferenceData  # noqa: E402
from etl.transformation.pipeline import TransformationResult, transform_batch  # noqa: E402

DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None
if DUCKDB_INSTALLED:
    from etl.load.duckdb_repository import DuckDbLoadRepository, LoadResult

SEM_DUCKDB = "duckdb não instalado; use pip install -r requirements.txt"

NOW = datetime(2026, 9, 10, 12, tzinfo=timezone.utc)


def _metadata(
    record_count: int,
    *,
    run_id: str = "run-1",
    batch_id: str = "pesquisas-000001",
    task_id: str = "task",
) -> BatchMetadata:
    return BatchMetadata(
        "pesquisas",
        run_id,
        task_id,
        batch_id,
        NOW,
        NOW + timedelta(seconds=5),
        record_count,
        100,
        "1.0",
        "a" * 64,
    )


def _transform(rows: list[dict], metadata: BatchMetadata) -> TransformationResult:
    """Transforma sem depender de referência de pai: ``pesquisas`` não tem uma."""
    batch = ExtractedBatch(rows, ExtractionCheckpoint("pesquisas", "cursor", 0), metadata)
    return transform_batch(
        batch, references=ReferenceData({}), previous={}, source_offset=0, ingested_at=NOW
    )


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class ReloadingTheSameBatchTests(unittest.TestCase):
    """``load_batch`` chamado de novo para o mesmo lote converge, não falha."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "ingestao.duckdb"
        self.repository = DuckDbLoadRepository(self.database_path)
        self.addCleanup(self.repository.close)

    def _count(self) -> int:
        return self.repository._conn.execute(
            'SELECT count(*) FROM "ingestao_pesquisas"'
        ).fetchone()[0]

    def _load(self, rows: list[dict], metadata: BatchMetadata) -> LoadResult:
        return self.repository.load_batch(_transform(rows, metadata), metadata)

    def test_reloading_the_same_batch_does_not_grow_the_table(self) -> None:
        rows = [{"id": "1", "titulo": "Faturamento 2025"}]
        metadata = _metadata(1)

        first = self._load(rows, metadata)
        second = self._load(rows, metadata)

        self.assertEqual(self._count(), 1)
        self.assertEqual(first.loaded, 1)
        self.assertEqual(second.loaded, 1)

    def test_reloading_the_same_batch_keeps_the_original_provenance(self) -> None:
        # Mesmo run_id/batch_id (é o mesmo lote sendo repetido); só o task_id
        # muda entre as duas tentativas, pra provar de qual delas a linha
        # gravada realmente veio.
        rows = [{"id": "1", "titulo": "Faturamento 2025"}]
        first_attempt = _metadata(1, task_id="tentativa-1")
        retry = _metadata(1, task_id="tentativa-2")

        self._load(rows, first_attempt)
        self._load(rows, retry)

        stored_task_id = self.repository._conn.execute(
            'SELECT task_id FROM "ingestao_pesquisas"'
        ).fetchone()[0]
        self.assertEqual(stored_task_id, "tentativa-1")

    def test_partial_overlap_only_inserts_the_new_rows(self) -> None:
        # Mesmo run_id/batch_id nas duas chamadas: é uma retomada do mesmo
        # lote, não um lote diferente. Cenário plausível quando a extração
        # recomeça de um pouco antes do checkpoint confirmado e o lote
        # retomado carrega uma linha a mais além das que já tinham sido
        # aceitas. Uma sobreposição entre run_id/batch_id diferentes é
        # cenário à parte, fora do que esta ADR cobre (ver ADR 0003).
        metadata = _metadata(1)
        self._load([{"id": "1", "titulo": "Faturamento 2025"}], metadata)

        retry_with_one_more_row = _metadata(2)
        outcome = self._load(
            [
                {"id": "1", "titulo": "Faturamento 2025"},  # já gravada na tentativa anterior
                {"id": "2", "titulo": "Novo registro"},
            ],
            retry_with_one_more_row,
        )

        self.assertEqual(self._count(), 2)
        # As duas linhas pertencem a este run_id/batch_id — a que já existia
        # inclusive, gravada nele desde a tentativa anterior — então a
        # contagem confirmada soma as duas, sem lacuna de reconciliação.
        self.assertEqual(outcome.loaded, 2)

    def test_confirmed_loaded_count_matches_after_replay(self) -> None:
        rows = [{"id": "1", "titulo": "A"}, {"id": "2", "titulo": "B"}]
        metadata = _metadata(2)

        first = self._load(rows, metadata)
        second = self._load(rows, metadata)

        self.assertEqual(first.loaded, 2)
        self.assertEqual(second.loaded, 2)


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class ResumedBatchRejectionTests(unittest.TestCase):
    """Retomada de um lote interrompido não acumula rejeição da tentativa anterior.

    A retomada retransforma o lote com o estado atual do banco, e a
    classificação pode mudar (a referência do pai apareceu entre uma tentativa
    e outra), gerando ``rejection_id`` novos para a mesma ocorrência da fonte.
    Sem a convergência, a contagem confirmada de rejeitados ultrapassa a de
    extraídos e a reconciliação do lote não fecha nunca mais.
    """

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "ingestao.duckdb"
        self.repository = DuckDbLoadRepository(self.database_path)
        self.addCleanup(self.repository.close)

    def _load_clientes(self, references: ReferenceData) -> LoadResult:
        metadata = BatchMetadata(
            "clientes",
            "run-1",
            "task",
            "clientes-000001",
            NOW,
            NOW + timedelta(seconds=5),
            1,
            100,
            "1.0",
            "a" * 64,
        )
        batch = ExtractedBatch(
            [{"id_cliente": "1", "id_empresa": "1", "e-mail": "teste@example.invalid"}],
            ExtractionCheckpoint("clientes", "cursor", 0),
            metadata,
        )
        result = transform_batch(
            batch, references=references, previous={}, source_offset=0, ingested_at=NOW
        )
        return self.repository.load_batch(result, metadata)

    def test_resume_replaces_the_rejections_of_the_interrupted_attempt(self) -> None:
        interrupted = self._load_clientes(ReferenceData({"empresas": []}))
        self.assertEqual(interrupted.rejected, 1)

        resumed = self._load_clientes(ReferenceData({"empresas": [{"empresa_id": "1"}]}))

        self.assertEqual(resumed.loaded, 1)
        self.assertEqual(resumed.rejected, 0)
        rejected_rows, reason_rows = self.repository._conn.execute(
            "SELECT"
            " (SELECT count(*) FROM rejected WHERE batch_id = 'clientes-000001'),"
            " (SELECT count(*) FROM rejected_reason)"
        ).fetchone()
        self.assertEqual(rejected_rows, 0)
        self.assertEqual(reason_rows, 0)

    def test_resume_with_identical_classification_keeps_a_single_rejection(self) -> None:
        first = self._load_clientes(ReferenceData({"empresas": []}))
        second = self._load_clientes(ReferenceData({"empresas": []}))

        self.assertEqual(first.rejected, 1)
        self.assertEqual(second.rejected, 1)


if __name__ == "__main__":
    unittest.main()
