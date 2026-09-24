"""Log estruturado emitido pela transformação (OB-04, ADR 0006).

A transformação já calcula tudo que um evento por lote precisa em
``TransformationResult.metrics`` (ver ``pipeline.py``), mas nunca publicava
isso como log — só devolvia o dicionário para quem chamou. Este arquivo cobre
o formato que fecha essa lacuna, espelhando ``etl.extraction.log_events`` e
``etl.load.log_events``: uma classe fechada, sem registros, publicada por um
sink injetável.
"""

from __future__ import annotations

import logging
import sys
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
from etl.transformation.log_events import (  # noqa: E402
    TRANSFORMATION_BATCH_EVENT,
    TRANSFORMATION_STAGE,
    StandardLoggingSink,
    TransformationBatchLogEvent,
)
from etl.transformation.pipeline import transform_batch  # noqa: E402

NOW = datetime(2026, 9, 24, 12, tzinfo=timezone.utc)


class CollectingLogSink:
    def __init__(self) -> None:
        self.events: list[TransformationBatchLogEvent] = []

    def emit(self, event: TransformationBatchLogEvent) -> None:
        self.events.append(event)


class LogRecordCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _metadata(
    record_count: int,
    *,
    run_id: str = "run-1",
    task_id: str = "task-run-abc",
    batch_id: str = "pesquisas-000001",
) -> BatchMetadata:
    return BatchMetadata(
        "pesquisas",
        run_id,
        task_id,
        batch_id,
        NOW,
        NOW + timedelta(seconds=5),
        record_count,
        321,
        "1.0",
        "a" * 64,
    )


def _transform(rows: list[dict], metadata: BatchMetadata, **kwargs):
    """Transforma sem depender de referência de pai: ``pesquisas`` não tem uma."""
    batch = ExtractedBatch(rows, ExtractionCheckpoint("pesquisas", "cursor", 0), metadata)
    return transform_batch(
        batch, references=ReferenceData({}), previous={}, source_offset=0, ingested_at=NOW, **kwargs
    )


class TransformationBatchLogEventTests(unittest.TestCase):
    """A forma do evento, construída a partir de ``TransformationResult.metrics``."""

    def test_from_metrics_carries_the_correlation_and_reconciliation_fields(self) -> None:
        result = _transform([{"id": "1", "titulo": "a"}, {"titulo": "sem id"}], _metadata(2))

        event = TransformationBatchLogEvent.from_metrics(result.metrics)
        attributes = event.as_dict()

        self.assertEqual(attributes["event"], TRANSFORMATION_BATCH_EVENT)
        self.assertEqual(attributes["stage"], TRANSFORMATION_STAGE)
        self.assertEqual(attributes["status"], "completed_with_rejections")
        self.assertEqual(attributes["source"], "pesquisas")
        self.assertEqual(attributes["run_id"], "run-1")
        self.assertEqual(attributes["task_id"], "task-run-abc")
        self.assertEqual(attributes["batch_id"], "pesquisas-000001")
        self.assertEqual(attributes["extracted_count"], 2)
        self.assertEqual(attributes["accepted_count"], 1)
        self.assertEqual(attributes["rejected_count"], 1)
        self.assertEqual(attributes["duplicate_count"], 0)
        self.assertEqual(attributes["byte_count"], 321)
        self.assertGreaterEqual(attributes["duration_ms"], 0)

    def test_duration_ms_is_the_metrics_duration_seconds_converted(self) -> None:
        result = _transform([{"id": "1", "titulo": "a"}], _metadata(1))
        result.metrics["duration_seconds"] = 0.25

        event = TransformationBatchLogEvent.from_metrics(result.metrics)

        self.assertEqual(event.duration_ms, 250.0)

    def test_does_not_contain_records(self) -> None:
        result = _transform([{"id": "1", "titulo": "a"}], _metadata(1))

        event = TransformationBatchLogEvent.from_metrics(result.metrics)

        self.assertNotIn("records", event.as_dict())

    def test_standard_logging_sink_exposes_structured_attributes(self) -> None:
        logger = logging.getLogger("tests.etl.transformation")
        collector = LogRecordCollector()
        previous_level = logger.level
        previous_propagation = logger.propagate
        logger.handlers.append(collector)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        self.addCleanup(logger.handlers.remove, collector)
        self.addCleanup(logger.setLevel, previous_level)
        self.addCleanup(setattr, logger, "propagate", previous_propagation)

        result = _transform([{"id": "1", "titulo": "a"}], _metadata(1))
        event = TransformationBatchLogEvent.from_metrics(result.metrics)

        StandardLoggingSink(logger).emit(event)

        self.assertEqual(len(collector.records), 1)
        record = collector.records[0]
        self.assertEqual(record.getMessage(), TRANSFORMATION_BATCH_EVENT)
        self.assertEqual(record.event, TRANSFORMATION_BATCH_EVENT)
        self.assertEqual(record.stage, TRANSFORMATION_STAGE)
        self.assertEqual(record.run_id, "run-1")
        self.assertEqual(record.task_id, "task-run-abc")


class TransformBatchLogEmissionTests(unittest.TestCase):
    """``transform_batch`` publica o evento de verdade, no sink injetado."""

    def test_transform_batch_emits_one_event_per_call(self) -> None:
        sink = CollectingLogSink()

        result = _transform([{"id": "1", "titulo": "a"}], _metadata(1), log_sink=sink)

        self.assertEqual(len(sink.events), 1)
        event = sink.events[0]
        self.assertEqual(event.accepted_count, len(result.accepted))
        self.assertEqual(event.rejected_count, len(result.rejected))
        self.assertEqual(event.duplicate_count, len(result.duplicates))

    def test_default_sink_is_the_standard_logging_sink_and_needs_no_wiring(self) -> None:
        _transform([{"id": "1", "titulo": "a"}], _metadata(1))

    def test_log_event_does_not_contain_personal_data(self) -> None:
        sensitive_title = "Pesquisa de satisfação pessoal sigilosa"
        sink = CollectingLogSink()

        _transform([{"id": "1", "titulo": sensitive_title}], _metadata(1), log_sink=sink)

        rendered_event = str(sink.events[0].as_dict())
        self.assertNotIn(sensitive_title, rendered_event)

    def test_a_sink_that_fails_does_not_break_the_transformation(self) -> None:
        class FailingLogSink:
            def emit(self, event: TransformationBatchLogEvent) -> None:
                raise RuntimeError("sink fora do ar")

        result = _transform([{"id": "1", "titulo": "a"}], _metadata(1), log_sink=FailingLogSink())

        self.assertEqual(len(result.accepted), 1)

    def test_a_bug_building_the_event_is_not_confused_with_a_sink_down(self) -> None:
        """Só o envio ao sink é tolerante a falha (ADR 0001). Um bug na
        construção do evento (ex.: chave errada em ``metrics``) é um defeito
        de código, não uma falha de transporte — não pode ser engolido."""
        broken = mock.patch.object(
            TransformationBatchLogEvent,
            "from_metrics",
            side_effect=KeyError("campo_inexistente"),
        )
        with broken, self.assertRaises(KeyError):
            _transform([{"id": "1", "titulo": "a"}], _metadata(1))


if __name__ == "__main__":
    unittest.main()
