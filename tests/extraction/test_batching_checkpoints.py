from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction import (  # noqa: E402
    EMPRESAS_REQUIRED_COLUMNS,
    EmpresasExtractor,
    ExtractionCheckpoint,
    InvalidCheckpointError,
    ObjectReference,
    StaleCheckpointError,
)
from tests.extraction.helpers import MemoryObjectReader, csv_payload  # noqa: E402


def _empresas_payload(*identifiers: str) -> bytes:
    rows = [
        [
            identifier,
            f"Empresa sintética {identifier}",
            "1,00%",
            "Nacional",
            "Sim",
            "Efetivo",
            "São Paulo",
            "São Paulo",
            "Brasil",
        ]
        for identifier in identifiers
    ]
    return csv_payload(EMPRESAS_REQUIRED_COLUMNS, rows)


def _extractor(payload: bytes, *, batch_size: int = 2) -> EmpresasExtractor:
    return EmpresasExtractor(
        object_reader=MemoryObjectReader(payload),
        object_reference=ObjectReference(
            bucket="sindusfarma-data",
            key="landing/empresas.csv",
        ),
        batch_size=batch_size,
    )


class BatchingCheckpointTests(unittest.TestCase):
    def test_splits_records_into_ordered_batches(self) -> None:
        payload = _empresas_payload("1", "2", "3", "4", "5")

        batches = list(_extractor(payload).read(run_id="run-batches", task_id="task-batches"))

        self.assertEqual(
            [[record["ID"] for record in batch.records] for batch in batches],
            [["1", "2"], ["3", "4"], ["5"]],
        )
        self.assertEqual(
            [batch.checkpoint.position for batch in batches],
            ["row:2", "row:4", "row:5"],
        )
        self.assertEqual(
            [batch.checkpoint.sequence for batch in batches],
            [1, 2, 3],
        )
        self.assertEqual(
            [batch.metadata.batch_id for batch in batches],
            ["empresas-000001", "empresas-000002", "empresas-000003"],
        )
        self.assertTrue(all(batch.metadata.byte_count == len(payload) for batch in batches))
        self.assertEqual(
            {batch.checkpoint.source_version for batch in batches},
            {"sha256:" + batches[0].metadata.source_checksum},
        )

    def test_resumes_after_confirmed_batch_without_repeating_its_rows(self) -> None:
        payload = _empresas_payload("1", "2", "3", "4", "5")
        first_attempt = _extractor(payload).read(
            run_id="run-before-interruption", task_id="task-before-interruption"
        )
        confirmed_batch = next(first_attempt)
        unconfirmed_batch = next(first_attempt)
        first_attempt.close()

        resumed_batches = list(
            _extractor(payload).read(
                run_id="run-after-interruption",
                task_id="task-after-interruption",
                checkpoint=confirmed_batch.checkpoint,
            )
        )

        resumed_ids = [record["ID"] for batch in resumed_batches for record in batch.records]
        self.assertEqual(resumed_ids, ["3", "4", "5"])
        self.assertEqual(
            [record["ID"] for record in unconfirmed_batch.records],
            ["3", "4"],
        )
        self.assertTrue(
            set(record["ID"] for record in confirmed_batch.records).isdisjoint(resumed_ids)
        )
        self.assertEqual(
            [batch.checkpoint.sequence for batch in resumed_batches],
            [2, 3],
        )

    def test_fully_confirmed_source_emits_no_duplicate_batch(self) -> None:
        payload = _empresas_payload("1", "2", "3")
        batches = list(_extractor(payload).read(run_id="run-complete", task_id="task-complete"))

        resumed = list(
            _extractor(payload).read(
                run_id="run-already-complete",
                task_id="task-already-complete",
                checkpoint=batches[-1].checkpoint,
            )
        )

        self.assertEqual(resumed, [])

    def test_rejects_checkpoint_from_another_source(self) -> None:
        payload = _empresas_payload("1")
        checkpoint = ExtractionCheckpoint(
            source="pesquisas",
            position="row:1",
            sequence=1,
            source_version="sha256:synthetic",
        )

        with self.assertRaisesRegex(InvalidCheckpointError, "outra fonte"):
            list(
                _extractor(payload).read(
                    run_id="run-wrong-source",
                    task_id="task-wrong-source",
                    checkpoint=checkpoint,
                )
            )

    def test_rejects_malformed_or_incomplete_checkpoint(self) -> None:
        payload = _empresas_payload("1")
        invalid_checkpoints = (
            ExtractionCheckpoint(
                source="empresas",
                position="page:1",
                sequence=1,
                source_version="sha256:synthetic",
            ),
            ExtractionCheckpoint(
                source="empresas",
                position="row:1",
                sequence=1,
            ),
        )

        for checkpoint in invalid_checkpoints:
            with self.subTest(checkpoint=checkpoint):
                with self.assertRaises(InvalidCheckpointError):
                    list(
                        _extractor(payload).read(
                            run_id="run-invalid-checkpoint",
                            task_id="task-invalid-checkpoint",
                            checkpoint=checkpoint,
                        )
                    )

    def test_rejects_checkpoint_when_source_content_changed(self) -> None:
        original_payload = _empresas_payload("1", "2")
        checkpoint = next(
            _extractor(original_payload).read(run_id="run-original", task_id="task-original")
        ).checkpoint
        changed_payload = _empresas_payload("1", "changed")

        with self.assertRaisesRegex(StaleCheckpointError, "fonte mudou"):
            list(
                _extractor(changed_payload).read(
                    run_id="run-changed-source",
                    task_id="task-changed-source",
                    checkpoint=checkpoint,
                )
            )

    def test_rejects_checkpoint_beyond_end_of_source(self) -> None:
        payload = _empresas_payload("1", "2")
        source_version = next(
            _extractor(payload).read(run_id="run-version", task_id="task-version")
        ).checkpoint.source_version
        checkpoint = ExtractionCheckpoint(
            source="empresas",
            position="row:3",
            sequence=2,
            source_version=source_version,
        )

        with self.assertRaisesRegex(InvalidCheckpointError, "fim da fonte"):
            list(
                _extractor(payload).read(
                    run_id="run-beyond-end",
                    task_id="task-beyond-end",
                    checkpoint=checkpoint,
                )
            )

    def test_requires_positive_integer_batch_size(self) -> None:
        payload = _empresas_payload("1")

        for invalid_batch_size in (0, -1, 1.5, True):
            with self.subTest(batch_size=invalid_batch_size):
                with self.assertRaisesRegex(ValueError, "inteiro positivo"):
                    _extractor(
                        payload,
                        batch_size=invalid_batch_size,  # type: ignore[arg-type]
                    )


if __name__ == "__main__":
    unittest.main()
