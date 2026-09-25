"""Log estruturado emitido pela orquestração (issue #219).

``flow.py`` publicava marcos de execução com ``get_run_logger().info(...)`` e
string livre interpolada — sem o formato técnico (evento, estágio, status,
atributos em ``extra``) que a extração e a carga já usam. Este arquivo cobre
o helper que fecha esse formato (``_log_event``) e, de ponta a ponta, os
eventos que o flow ``ingest-object`` publica de verdade.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
import tempfile
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import BinaryIO
from unittest import mock

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction import ObjectReference  # noqa: E402
from etl.orchestration import flow as flow_module  # noqa: E402
from tests import fixtures  # noqa: E402

DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None
SEM_DUCKDB = "duckdb não instalado; use pip install -r requirements.txt"

BUCKET = "landing-test"
AMBIENTE_FICTICIO = {
    "ETL_MINIO_ENDPOINT": "http://minio.invalid:9000",
    "ETL_MINIO_BUCKET": BUCKET,
    "ETL_MINIO_ACCESS_KEY": "teste-sem-segredo",
    "ETL_MINIO_SECRET_KEY": "teste-sem-segredo",
}


class LeitorEmMemoria:
    def __init__(self, payloads: dict[str, bytes]) -> None:
        self.payloads = payloads

    @contextmanager
    def open(self, reference: ObjectReference) -> Iterator[BinaryIO]:
        yield BytesIO(self.payloads[Path(reference.key).stem])


class LogRecordCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class StubLogger:
    """Substitui ``get_run_logger()`` só para testar o formato do helper."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def info(self, message: str, *, extra: dict) -> None:
        self.calls.append((message, extra))


class LogEventHelperTests(unittest.TestCase):
    """O seam isolado: mensagem = evento, atributos técnicos em ``extra``."""

    def test_message_is_the_event_name_not_an_interpolated_string(self) -> None:
        logger = StubLogger()

        flow_module._log_event(logger, "orchestration.extract.emitted", source="empresas")

        self.assertEqual(len(logger.calls), 1)
        message, _ = logger.calls[0]
        self.assertEqual(message, "orchestration.extract.emitted")

    def test_extra_carries_the_event_the_stage_and_the_given_attributes(self) -> None:
        logger = StubLogger()

        flow_module._log_event(
            logger,
            "orchestration.extract.emitted",
            status="success",
            source="empresas",
            run_id="run-1",
            batch_count=2,
        )

        _, extra = logger.calls[0]
        self.assertEqual(extra["event"], "orchestration.extract.emitted")
        self.assertEqual(extra["stage"], "orchestration")
        self.assertEqual(extra["status"], "success")
        self.assertEqual(extra["source"], "empresas")
        self.assertEqual(extra["run_id"], "run-1")
        self.assertEqual(extra["batch_count"], 2)

    def test_task_id_comes_from_the_current_prefect_task_run_when_available(self) -> None:
        logger = StubLogger()

        with mock.patch("prefect.runtime.task_run.id", "task-run-123"):
            flow_module._log_event(logger, "orchestration.extract.emitted", source="empresas")

        _, extra = logger.calls[0]
        self.assertEqual(extra["task_id"], "task-run-123")

    def test_task_id_falls_back_to_the_flow_run_when_there_is_no_task_run(self) -> None:
        """Marcos publicados direto no corpo de um flow (`ingest_object`,
        `backfill`) não têm task run — só o flow run existe nesse escopo."""
        logger = StubLogger()

        with (
            mock.patch("prefect.runtime.task_run.id", None),
            mock.patch("prefect.runtime.flow_run.id", "flow-run-456"),
        ):
            flow_module._log_event(logger, "orchestration.ingest_object.emitted", source="empresas")

        _, extra = logger.calls[0]
        self.assertEqual(extra["task_id"], "flow-run-456")

    def test_task_id_is_absent_outside_any_prefect_context(self) -> None:
        """Chamada direta em teste unitário, fora de flow ou task: sem
        identificador do Prefect disponível, `task_id` fica de fora do
        `extra` (mesma regra de omitir `None` já usada pelos outros campos)."""
        logger = StubLogger()

        with (
            mock.patch("prefect.runtime.task_run.id", None),
            mock.patch("prefect.runtime.flow_run.id", None),
        ):
            flow_module._log_event(logger, "orchestration.extract.emitted", source="empresas")

        _, extra = logger.calls[0]
        self.assertNotIn("task_id", extra)

    def test_explicit_task_id_is_not_overridden_by_the_prefect_context(self) -> None:
        logger = StubLogger()

        with mock.patch("prefect.runtime.task_run.id", "task-run-123"):
            flow_module._log_event(
                logger, "orchestration.extract.emitted", source="empresas", task_id="explicit"
            )

        _, extra = logger.calls[0]
        self.assertEqual(extra["task_id"], "explicit")


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class IngestObjectLogEventsTests(unittest.TestCase):
    """Os marcos publicados de verdade ao longo do flow ``ingest-object``."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = str(Path(self.temporary_directory.name) / "logs.duckdb")
        self.payloads = {source: fixtures.payload(source) for source in fixtures.ORDEM_CARGA}
        leitor = LeitorEmMemoria(self.payloads)
        ambiente = mock.patch.dict(os.environ, AMBIENTE_FICTICIO)
        self.addCleanup(ambiente.stop)
        ambiente.start()
        leitor_mock = mock.patch.object(flow_module, "MinioObjectReader", lambda client: leitor)
        self.addCleanup(leitor_mock.stop)
        leitor_mock.start()

        self.task_collector = self._attach("prefect.task_runs")
        self.flow_collector = self._attach("prefect.flow_runs")

    def _attach(self, logger_name: str) -> LogRecordCollector:
        logger = logging.getLogger(logger_name)
        collector = LogRecordCollector()
        logger.addHandler(collector)
        logger.setLevel(logging.INFO)
        self.addCleanup(logger.removeHandler, collector)
        return collector

    def _events(self, records: list[logging.LogRecord]) -> list[logging.LogRecord]:
        return [record for record in records if hasattr(record, "event")]

    def test_ingest_object_publishes_a_structured_event_per_task_and_for_the_flow(self) -> None:
        flow_module.ingest_object(
            source="empresas", bucket=BUCKET, key="landing/empresas.csv", db_path=self.database_path
        )

        by_event = {
            record.event: record
            for record in self._events(self.task_collector.records)
            + self._events(self.flow_collector.records)
        }
        self.assertIn("orchestration.extract.emitted", by_event)
        self.assertIn("orchestration.transform.emitted", by_event)
        self.assertIn("orchestration.load.emitted", by_event)
        self.assertIn("orchestration.ingest_object.emitted", by_event)

        extract_event = by_event["orchestration.extract.emitted"]
        self.assertEqual(extract_event.stage, "orchestration")
        self.assertEqual(extract_event.status, "success")
        self.assertEqual(extract_event.source, "empresas")
        self.assertEqual(extract_event.batch_count, 1)

        transform_event = by_event["orchestration.transform.emitted"]
        load_event = by_event["orchestration.load.emitted"]
        ingest_event = by_event["orchestration.ingest_object.emitted"]
        self.assertEqual(load_event.status, "success")
        self.assertEqual(load_event.loaded_count, 3)
        self.assertEqual(load_event.rejected_count, 0)

        self.assertEqual(ingest_event.status, "loaded")
        self.assertEqual(ingest_event.source, "empresas")
        self.assertEqual(ingest_event.loaded_count, 3)

        # run_id correlaciona os quatro marcos (ADR 0001) — nenhum deles pode
        # ficar `None` (regressão: antes vinha de `batches[0]`/`results[0]`,
        # que fica vazio quando o objeto não produz lote/resultado).
        run_id = ingest_event.run_id
        self.assertTrue(run_id)
        for event in (extract_event, transform_event, load_event):
            with self.subTest(event=event.event):
                self.assertEqual(event.run_id, run_id)

        for event in (extract_event, transform_event, load_event, ingest_event):
            with self.subTest(event=event.event):
                self.assertGreaterEqual(event.duration_ms, 0)

        # task_id correlaciona a execução de cada tarefa (ADR 0006): as três
        # tasks do flow são execuções distintas do Prefect, então cada uma
        # tem o seu próprio task_id, todos preenchidos e diferentes entre si.
        task_ids = {extract_event.task_id, transform_event.task_id, load_event.task_id}
        self.assertTrue(all(task_ids))
        self.assertEqual(len(task_ids), 3)
        # O marco do flow (não é uma task) correlaciona pelo flow run.
        self.assertTrue(ingest_event.task_id)

    def test_second_delivery_of_the_same_object_is_logged_as_ignored(self) -> None:
        flow_module.ingest_object(
            source="empresas", bucket=BUCKET, key="landing/empresas.csv", db_path=self.database_path
        )
        self.flow_collector.records.clear()

        flow_module.ingest_object(
            source="empresas", bucket=BUCKET, key="landing/empresas.csv", db_path=self.database_path
        )

        ignored = [
            record
            for record in self._events(self.flow_collector.records)
            if record.event == "orchestration.ingest_object.emitted"
        ]
        self.assertTrue(ignored)
        self.assertEqual(ignored[-1].status, "ignored")

    def test_no_orchestration_event_message_is_a_free_form_interpolated_string(self) -> None:
        flow_module.ingest_object(
            source="empresas", bucket=BUCKET, key="landing/empresas.csv", db_path=self.database_path
        )

        all_records = self.task_collector.records + self.flow_collector.records
        for record in self._events(all_records):
            with self.subTest(event=record.event):
                self.assertEqual(record.getMessage(), record.event)


if __name__ == "__main__":
    unittest.main()
