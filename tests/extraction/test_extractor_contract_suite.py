from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction import (  # noqa: E402
    ExtractedBatch,
    Extractor,
    ObjectReference,
)
from tests.extraction.helpers import MemoryObjectReader, csv_payload  # noqa: E402
from tests.extraction.synthetic_sources import SYNTHETIC_SOURCES  # noqa: E402

REQUIRED_TECHNICAL_ATTRIBUTES = {
    "source",
    "run_id",
    "task_id",
    "batch_id",
    "started_at",
    "finished_at",
    "record_count",
    "byte_count",
    "schema_version",
    "source_checksum",
    "contract_version",
    "checkpoint_position",
    "checkpoint_sequence",
    "checkpoint_source_version",
}


class ExtractorContractSuiteTests(unittest.TestCase):
    def test_all_extractors_implement_and_emit_the_common_contract(self) -> None:
        for fixture in SYNTHETIC_SOURCES:
            with self.subTest(source=fixture.source):
                payload = fixture.payload()
                reader = MemoryObjectReader(payload)
                extractor = fixture.extractor_type(
                    object_reader=reader,
                    object_reference=ObjectReference(
                        bucket="synthetic-data",
                        key=f"landing/{fixture.source}.csv",
                    ),
                    batch_size=2,
                )

                batches = list(
                    extractor.read(
                        run_id=f"contract-{fixture.source}", task_id=f"task-{fixture.source}"
                    )
                )

                self.assertIsInstance(extractor, Extractor)
                self.assertTrue(all(isinstance(batch, ExtractedBatch) for batch in batches))
                self.assertEqual(
                    sum(len(batch.records) for batch in batches),
                    fixture.expected_records,
                )
                self.assertEqual(
                    batches[-1].checkpoint.position,
                    f"row:{fixture.expected_records}",
                )
                self.assertEqual(len(reader.opened_references), 1)

                for batch in batches:
                    attributes = batch.as_attributes()
                    self.assertEqual(batch.metadata.source, fixture.source)
                    self.assertEqual(batch.checkpoint.source, fixture.source)
                    self.assertEqual(batch.metadata.byte_count, len(payload))
                    self.assertEqual(
                        batch.metadata.record_count,
                        len(batch.records),
                    )
                    self.assertTrue(REQUIRED_TECHNICAL_ATTRIBUTES.issubset(attributes))

    def test_all_extractors_represent_header_only_source_with_empty_batch(self) -> None:
        for fixture in SYNTHETIC_SOURCES:
            with self.subTest(source=fixture.source):
                payload = csv_payload(fixture.headers, [])
                extractor = fixture.extractor_type(
                    object_reader=MemoryObjectReader(payload),
                    object_reference=ObjectReference(
                        bucket="synthetic-data",
                        key=f"landing/{fixture.source}.csv",
                    ),
                )

                batches = list(
                    extractor.read(
                        run_id=f"empty-{fixture.source}", task_id=f"task-{fixture.source}"
                    )
                )

                self.assertEqual(len(batches), 1)
                self.assertEqual(batches[0].records, ())
                self.assertEqual(batches[0].metadata.record_count, 0)
                self.assertEqual(batches[0].checkpoint.position, "row:0")


if __name__ == "__main__":
    unittest.main()
