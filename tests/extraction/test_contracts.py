from __future__ import annotations

import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction import (  # noqa: E402
    BatchMetadata,
    ExtractedBatch,
    ExtractionCheckpoint,
)


class ExtractionContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.started_at = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)
        self.finished_at = self.started_at + timedelta(seconds=2)

    def metadata(self, *, source: str = "pesquisas", record_count: int = 1) -> BatchMetadata:
        return BatchMetadata(
            source=source,
            run_id="run-sintetico-001",
            task_id="extract-pesquisas",
            batch_id="pesquisas-0001",
            started_at=self.started_at,
            finished_at=self.finished_at,
            record_count=record_count,
            byte_count=18,
            schema_version="1",
            source_checksum="sha256:sintetico",
        )

    def checkpoint(self, *, source: str = "pesquisas") -> ExtractionCheckpoint:
        return ExtractionCheckpoint(
            source=source,
            position="row:1",
            sequence=1,
            source_version="sha256:sintetico",
        )

    def test_batch_preserves_records_and_exposes_safe_attributes(self) -> None:
        batch = ExtractedBatch(
            records=[{"id": "1", "titulo": "valor sintético"}],
            checkpoint=self.checkpoint(),
            metadata=self.metadata(),
        )

        self.assertEqual(len(batch.records), 1)
        self.assertIsInstance(batch.records, tuple)
        self.assertEqual(batch.as_attributes()["source"], "pesquisas")
        self.assertEqual(batch.as_attributes()["checkpoint_position"], "row:1")
        self.assertNotIn("records", batch.as_attributes())
        self.assertNotIn("titulo", batch.as_attributes())

    def test_empty_source_can_be_represented_without_fake_record(self) -> None:
        batch = ExtractedBatch(
            records=[],
            checkpoint=ExtractionCheckpoint(
                source="empresas",
                position="row:0",
                sequence=0,
            ),
            metadata=self.metadata(source="empresas", record_count=0),
        )

        self.assertEqual(batch.records, ())
        self.assertEqual(batch.metadata.record_count, 0)

    def test_batch_rejects_inconsistent_record_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "record_count"):
            ExtractedBatch(
                records=[{"id": "1"}],
                checkpoint=self.checkpoint(),
                metadata=self.metadata(record_count=2),
            )

    def test_batch_rejects_checkpoint_from_another_source(self) -> None:
        with self.assertRaisesRegex(ValueError, "mesma fonte"):
            ExtractedBatch(
                records=[{"id": "1"}],
                checkpoint=self.checkpoint(source="empresas"),
                metadata=self.metadata(source="pesquisas"),
            )

    def test_metadata_requires_timezone_and_valid_interval(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone"):
            BatchMetadata(
                source="pesquisas",
                run_id="run-1",
                task_id="extract-pesquisas",
                batch_id="batch-1",
                started_at=datetime(2026, 9, 9, 12, 0),
                finished_at=datetime(2026, 9, 9, 12, 1),
                record_count=0,
                byte_count=0,
                schema_version="1",
            )

        with self.assertRaisesRegex(ValueError, "anterior"):
            BatchMetadata(
                source="pesquisas",
                run_id="run-1",
                task_id="extract-pesquisas",
                batch_id="batch-1",
                started_at=self.finished_at,
                finished_at=self.started_at,
                record_count=0,
                byte_count=0,
                schema_version="1",
            )

    def test_checkpoint_rejects_negative_sequence(self) -> None:
        with self.assertRaisesRegex(ValueError, "negativo"):
            ExtractionCheckpoint(source="pesquisas", position="row:0", sequence=-1)


if __name__ == "__main__":
    unittest.main()
