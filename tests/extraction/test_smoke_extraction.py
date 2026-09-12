from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction import ExtractionBatchLogEvent, ObjectReference  # noqa: E402
from tests.extraction.helpers import MemoryObjectReader  # noqa: E402
from tests.extraction.synthetic_sources import SYNTHETIC_SOURCES  # noqa: E402

SMOKE_BATCH_SIZE = 2


class CollectingLogSink:
    def __init__(self) -> None:
        self.events: list[ExtractionBatchLogEvent] = []

    def emit(self, event: ExtractionBatchLogEvent) -> None:
        self.events.append(event)


class ExtractionSmokeTests(unittest.TestCase):
    def test_six_synthetic_sources_emit_expected_batches_and_counts(self) -> None:
        actual_counts: dict[str, int] = {}
        actual_batches: dict[str, int] = {}

        for fixture in SYNTHETIC_SOURCES:
            payload = fixture.payload()
            reader = MemoryObjectReader(payload)
            log_sink = CollectingLogSink()
            extractor = fixture.extractor_type(
                object_reader=reader,
                object_reference=ObjectReference(
                    bucket="synthetic-data",
                    key=f"landing/{fixture.source}.csv",
                    event_id=f"synthetic-event-{fixture.source}",
                ),
                batch_size=SMOKE_BATCH_SIZE,
                log_sink=log_sink,
            )

            batches = list(extractor.read(run_id="smoke-extraction-001"))
            actual_counts[fixture.source] = sum(batch.metadata.record_count for batch in batches)
            actual_batches[fixture.source] = len(batches)

            self.assertEqual(len(log_sink.events), len(batches))
            self.assertEqual(
                log_sink.events[-1].checkpoint_position,
                f"row:{fixture.expected_records}",
            )
            self.assertTrue(
                all(event.run_id == "smoke-extraction-001" for event in log_sink.events)
            )

        expected_counts = {
            fixture.source: fixture.expected_records for fixture in SYNTHETIC_SOURCES
        }
        expected_batches = {
            fixture.source: math.ceil(fixture.expected_records / SMOKE_BATCH_SIZE)
            for fixture in SYNTHETIC_SOURCES
        }
        self.assertEqual(actual_counts, expected_counts)
        self.assertEqual(actual_batches, expected_batches)
        self.assertEqual(sum(actual_counts.values()), 19)
        self.assertEqual(sum(actual_batches.values()), 11)


if __name__ == "__main__":
    unittest.main()
