"""Log estruturado emitido pela carga (VB-09... issue #219).

Cobre o que faltava para a carga publicar o mesmo formato técnico que a
extração já publica em ``etl.extraction.log_events``: um evento por lote,
sem os registros, com os campos de correlação da ADR 0001 (run_id, task_id,
fonte, lote) e as contagens de reconciliação.
"""

from __future__ import annotations

import importlib.util
import logging
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
from etl.load.ddl import (  # noqa: E402
    BATCH_STATUS_FAILED,
    BATCH_STATUS_LOADED,
    BATCH_STATUS_LOADED_WITH_REJECTIONS,
)
from etl.load.log_events import (  # noqa: E402
    LOAD_BATCH_EVENT,
    LOAD_STAGE,
    LoadBatchLogEvent,
    StandardLoggingSink,
)
from etl.transformation.consistency import ReferenceData  # noqa: E402
from etl.transformation.pipeline import TransformationResult, transform_batch  # noqa: E402

DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None
if DUCKDB_INSTALLED:
    import duckdb

    from etl.load.duckdb_repository import DuckDbLoadRepository, LoadResult

SEM_DUCKDB = "duckdb não instalado; use pip install -r requirements.txt"

NOW = datetime(2026, 9, 10, 12, tzinfo=timezone.utc)


class CollectingLogSink:
    def __init__(self) -> None:
        self.events: list[LoadBatchLogEvent] = []

    def emit(self, event: LoadBatchLogEvent) -> None:
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


class LoadBatchLogEventTests(unittest.TestCase):
    """A forma do evento, isolada do banco."""

    def test_as_dict_carries_the_correlation_and_reconciliation_fields(self) -> None:
        result = LoadResult(
            source="pesquisas",
            run_id="run-1",
            batch_id="pesquisas-000001",
            extracted=3,
            loaded=2,
            rejected=0,
            duplicates=0,
        )
        metadata = _metadata(3)

        event = LoadBatchLogEvent.from_result(
            result, metadata, status=BATCH_STATUS_LOADED_WITH_REJECTIONS, duration_ms=12.5
        )
        attributes = event.as_dict()

        self.assertEqual(attributes["event"], LOAD_BATCH_EVENT)
        self.assertEqual(attributes["stage"], LOAD_STAGE)
        self.assertEqual(attributes["status"], BATCH_STATUS_LOADED_WITH_REJECTIONS)
        self.assertEqual(attributes["source"], "pesquisas")
        self.assertEqual(attributes["run_id"], "run-1")
        self.assertEqual(attributes["task_id"], "task")
        self.assertEqual(attributes["batch_id"], "pesquisas-000001")
        self.assertEqual(attributes["duration_ms"], 12.5)
        self.assertEqual(attributes["extracted_count"], 3)
        self.assertEqual(attributes["loaded_count"], 2)
        self.assertEqual(attributes["rejected_count"], 0)
        self.assertEqual(attributes["duplicate_count"], 0)
        self.assertFalse(attributes["balanced"])
        self.assertEqual(attributes["schema_version"], "1.0")
        self.assertEqual(attributes["source_checksum"], "a" * 64)

    def test_does_not_contain_records(self) -> None:
        result = LoadResult(
            source="pesquisas",
            run_id="run-1",
            batch_id="pesquisas-000001",
            extracted=1,
            loaded=1,
            rejected=0,
            duplicates=0,
        )
        event = LoadBatchLogEvent.from_result(
            result, _metadata(1), status=BATCH_STATUS_LOADED, duration_ms=1.0
        )

        self.assertNotIn("records", event.as_dict())

    def test_standard_logging_sink_exposes_structured_attributes(self) -> None:
        logger = logging.getLogger("tests.etl.load")
        collector = LogRecordCollector()
        previous_level = logger.level
        previous_propagation = logger.propagate
        logger.handlers.append(collector)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        self.addCleanup(logger.handlers.remove, collector)
        self.addCleanup(logger.setLevel, previous_level)
        self.addCleanup(setattr, logger, "propagate", previous_propagation)

        result = LoadResult(
            source="pesquisas",
            run_id="run-1",
            batch_id="pesquisas-000001",
            extracted=1,
            loaded=1,
            rejected=0,
            duplicates=0,
        )
        event = LoadBatchLogEvent.from_result(
            result, _metadata(1), status=BATCH_STATUS_LOADED, duration_ms=1.0
        )

        StandardLoggingSink(logger).emit(event)

        self.assertEqual(len(collector.records), 1)
        record = collector.records[0]
        self.assertEqual(record.getMessage(), LOAD_BATCH_EVENT)
        self.assertEqual(record.event, LOAD_BATCH_EVENT)
        self.assertEqual(record.stage, LOAD_STAGE)
        self.assertEqual(record.status, BATCH_STATUS_LOADED)
        self.assertEqual(record.run_id, "run-1")
        self.assertEqual(record.batch_id, "pesquisas-000001")


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class DuckDbLoadRepositoryLogTests(unittest.TestCase):
    """A carga de verdade publica o evento a cada lote, no sink injetado."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "ingestao.duckdb"
        self.sink = CollectingLogSink()
        self.repository = DuckDbLoadRepository(self.database_path, log_sink=self.sink)
        self.addCleanup(self.repository.close)

    def test_load_batch_emits_one_event_with_the_confirmed_counts(self) -> None:
        rows = [{"id": "1", "titulo": "Faturamento 2025"}, {"titulo": "sem id"}]
        metadata = _metadata(len(rows))

        outcome = self.repository.load_batch(_transform(rows, metadata), metadata)

        self.assertEqual(len(self.sink.events), 1)
        event = self.sink.events[0]
        self.assertEqual(event.status, BATCH_STATUS_LOADED_WITH_REJECTIONS)
        self.assertEqual(event.loaded_count, outcome.loaded)
        self.assertEqual(event.rejected_count, outcome.rejected)
        self.assertEqual(event.duplicate_count, outcome.duplicates)
        self.assertEqual(event.extracted_count, outcome.extracted)
        self.assertGreaterEqual(event.duration_ms, 0)

    def test_default_sink_is_the_standard_logging_sink_and_needs_no_wiring(self) -> None:
        database_path = Path(self.temporary_directory.name) / "outro.duckdb"
        with DuckDbLoadRepository(database_path) as repository:
            metadata = _metadata(1)
            repository.load_batch(_transform([{"id": "1", "titulo": "x"}], metadata), metadata)


class FailingLogSink:
    def emit(self, event: LoadBatchLogEvent) -> None:
        raise RuntimeError("sink fora do ar")


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class FailedBatchIsStillLoggedTests(unittest.TestCase):
    """A ADR 0001 pede o estado final de cada lote — inclusive o de falha."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "ingestao.duckdb"
        self.sink = CollectingLogSink()
        self.repository = DuckDbLoadRepository(self.database_path, log_sink=self.sink)
        self.addCleanup(self.repository.close)
        self.result = _transform(
            [{"id": "1", "titulo": "a"}, {"id": "2", "titulo": "b"}], _metadata(2)
        )
        # Derruba a carga no meio: a tabela de ingestão deixa de aceitar linha.
        self.repository._conn.execute('DROP VIEW "pesquisas"')
        self.repository._conn.execute('DROP VIEW "ingestao_pesquisas_atual"')
        self.repository._conn.execute('DROP TABLE "ingestao_pesquisas"')

    def test_failure_emits_an_event_with_the_failed_status(self) -> None:
        with self.assertRaises(Exception):
            self.repository.load_batch(self.result, _metadata(2))

        self.assertEqual(len(self.sink.events), 1)
        event = self.sink.events[0]
        self.assertEqual(event.status, BATCH_STATUS_FAILED)
        self.assertEqual(event.loaded_count, 0)
        self.assertEqual(event.rejected_count, 0)
        self.assertEqual(event.extracted_count, 2)
        self.assertFalse(event.balanced)

    def test_a_sink_that_fails_does_not_hide_the_load_error(self) -> None:
        self.repository._log_sink = FailingLogSink()

        with self.assertRaises(duckdb.Error) as context:
            self.repository.load_batch(self.result, _metadata(2))

        self.assertIn("ingestao_pesquisas", str(context.exception))


if __name__ == "__main__":
    unittest.main()
