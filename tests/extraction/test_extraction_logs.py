from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction import (  # noqa: E402
    CLIENTES_REQUIRED_COLUMNS,
    EMPRESAS_REQUIRED_COLUMNS,
    EXTRACTION_BATCH_EVENT,
    ClientesExtractor,
    EmpresasExtractor,
    ExtractionBatchLogEvent,
    ObjectReference,
    StandardLoggingSink,
)
from tests.extraction.helpers import MemoryObjectReader, csv_payload  # noqa: E402


class CollectingLogSink:
    def __init__(self) -> None:
        self.events: list[ExtractionBatchLogEvent] = []

    def emit(self, event: ExtractionBatchLogEvent) -> None:
        self.events.append(event)


class LogRecordCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _empresas_payload() -> bytes:
    return csv_payload(
        EMPRESAS_REQUIRED_COLUMNS,
        [
            ["1", "Empresa A", "1%", "Nacional", "Sim", "A", "SP", "SP", "Brasil"],
            ["2", "Empresa B", "2%", "Nacional", "Sim", "B", "RJ", "RJ", "Brasil"],
            ["3", "Empresa C", "3%", "Nacional", "Não", "", "MG", "MG", "Brasil"],
        ],
    )


class ExtractionLogTests(unittest.TestCase):
    def test_emits_complete_technical_event_for_each_batch(self) -> None:
        payload = _empresas_payload()
        sink = CollectingLogSink()
        extractor = EmpresasExtractor(
            object_reader=MemoryObjectReader(payload),
            object_reference=ObjectReference(
                bucket="sindusfarma-data",
                key="landing/empresas.csv",
            ),
            batch_size=2,
            log_sink=sink,
        )

        batches = list(extractor.read(run_id="run-log-batches"))

        self.assertEqual(len(batches), 2)
        self.assertEqual(len(sink.events), 2)
        self.assertEqual(
            [event.record_count for event in sink.events],
            [2, 1],
        )
        self.assertEqual(
            [event.checkpoint_position for event in sink.events],
            ["row:2", "row:3"],
        )
        self.assertEqual(
            [event.checkpoint_sequence for event in sink.events],
            [1, 2],
        )

        for event in sink.events:
            attributes = event.as_dict()
            self.assertEqual(attributes["event"], EXTRACTION_BATCH_EVENT)
            self.assertEqual(attributes["stage"], "extraction")
            self.assertEqual(attributes["status"], "success")
            self.assertEqual(attributes["source"], "empresas")
            self.assertEqual(attributes["run_id"], "run-log-batches")
            self.assertEqual(attributes["task_id"], "extract-empresas")
            self.assertEqual(attributes["byte_count"], len(payload))
            self.assertGreaterEqual(attributes["duration_ms"], 0)
            self.assertTrue(str(attributes["started_at"]).endswith("Z"))
            self.assertTrue(str(attributes["finished_at"]).endswith("Z"))
            self.assertEqual(
                "sha256:" + attributes["source_checksum"],
                attributes["checkpoint_source_version"],
            )

    def test_log_event_does_not_contain_records_or_personal_data(self) -> None:
        sensitive_email = "pessoa.sensivel@example.invalid"
        sensitive_identifier = "cliente-pessoal-0001"
        payload = csv_payload(
            CLIENTES_REQUIRED_COLUMNS,
            [
                [
                    sensitive_identifier,
                    "empresa-01",
                    "Cargo",
                    "Departamento",
                    sensitive_email,
                ]
            ],
        )
        sink = CollectingLogSink()
        extractor = ClientesExtractor(
            object_reader=MemoryObjectReader(payload),
            object_reference=ObjectReference(
                bucket="sindusfarma-data",
                key="landing/clientes.csv",
            ),
            log_sink=sink,
        )

        next(extractor.read(run_id="run-without-pii"))

        rendered_event = str(sink.events[0].as_dict())
        self.assertNotIn(sensitive_email, rendered_event)
        self.assertNotIn(sensitive_identifier, rendered_event)
        self.assertNotIn("e-mail", rendered_event)
        self.assertNotIn("records", sink.events[0].as_dict())

    def test_standard_logging_sink_exposes_structured_attributes(self) -> None:
        logger = logging.getLogger("tests.etl.extraction")
        collector = LogRecordCollector()
        previous_level = logger.level
        previous_propagation = logger.propagate
        logger.handlers.append(collector)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        self.addCleanup(logger.handlers.remove, collector)
        self.addCleanup(logger.setLevel, previous_level)
        self.addCleanup(setattr, logger, "propagate", previous_propagation)

        extractor = EmpresasExtractor(
            object_reader=MemoryObjectReader(_empresas_payload()),
            object_reference=ObjectReference(
                bucket="sindusfarma-data",
                key="landing/empresas.csv",
            ),
            log_sink=StandardLoggingSink(logger),
        )

        next(extractor.read(run_id="run-standard-logging"))

        self.assertEqual(len(collector.records), 1)
        record = collector.records[0]
        self.assertEqual(record.getMessage(), EXTRACTION_BATCH_EVENT)
        self.assertEqual(record.event, EXTRACTION_BATCH_EVENT)
        self.assertEqual(record.source, "empresas")
        self.assertEqual(record.run_id, "run-standard-logging")
        self.assertEqual(record.task_id, "extract-empresas")
        self.assertEqual(record.status, "success")
        self.assertEqual(record.checkpoint_position, "row:3")

    def test_header_only_source_emits_zero_count_event(self) -> None:
        sink = CollectingLogSink()
        payload = csv_payload(EMPRESAS_REQUIRED_COLUMNS, [])
        extractor = EmpresasExtractor(
            object_reader=MemoryObjectReader(payload),
            object_reference=ObjectReference(
                bucket="sindusfarma-data",
                key="landing/empresas.csv",
            ),
            log_sink=sink,
        )

        next(extractor.read(run_id="run-empty-log"))

        self.assertEqual(len(sink.events), 1)
        self.assertEqual(sink.events[0].record_count, 0)
        self.assertEqual(sink.events[0].checkpoint_position, "row:0")


if __name__ == "__main__":
    unittest.main()
