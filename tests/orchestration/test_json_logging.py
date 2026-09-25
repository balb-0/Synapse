"""Serialização estruturada dos logs em JSON (OB-03).

Os eventos técnicos (extração, carga, orquestração) já saem com o nome do
evento como mensagem e os atributos de correlação em ``extra`` — o que
faltava era o texto de log em si sair como JSON de verdade, não como um
``LogRecord`` em memória. Este arquivo cobre o formatter que fecha isso
(``StructuredJsonFormatter``) e a função que o liga aos loggers usados pelas
quatro etapas (``configure_json_logging``).
"""

from __future__ import annotations

import io
import json
import logging
import sys
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.orchestration.logging_config import (  # noqa: E402
    OBSERVED_LOGGERS,
    StructuredJsonFormatter,
    configure_json_logging,
)


def _make_record(
    logger_name: str = "etl.extraction",
    message: str = "extraction.batch.emitted",
    extra: dict | None = None,
) -> logging.LogRecord:
    logger = logging.getLogger(logger_name)
    handler = logging.Handler()
    captured: list[logging.LogRecord] = []
    handler.emit = captured.append  # type: ignore[method-assign]
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        logger.info(message, extra=extra or {})
    finally:
        logger.removeHandler(handler)
    return captured[0]


class StructuredJsonFormatterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.formatter = StructuredJsonFormatter()

    def test_output_is_valid_json(self) -> None:
        record = _make_record(extra={"event": "extraction.batch.emitted", "stage": "extraction"})

        formatted = self.formatter.format(record)

        json.loads(formatted)  # não lança

    def test_carries_every_extra_attribute_passed_to_the_log_call(self) -> None:
        extra = {
            "event": "orchestration.extract.emitted",
            "stage": "orchestration",
            "status": "success",
            "run_id": "run-1",
            "task_id": "task-1",
            "source": "empresas",
            "duration_ms": 12.5,
        }

        record = _make_record(extra=extra)
        parsed = json.loads(self.formatter.format(record))

        for key, value in extra.items():
            with self.subTest(key=key):
                self.assertEqual(parsed[key], value)

    def test_includes_timestamp_level_and_logger_name(self) -> None:
        record = _make_record(logger_name="etl.load", extra={"event": "load.batch.emitted"})

        parsed = json.loads(self.formatter.format(record))

        self.assertEqual(parsed["level"], "INFO")
        self.assertEqual(parsed["logger"], "etl.load")
        self.assertIn("timestamp", parsed)

    def test_does_not_leak_internal_logrecord_bookkeeping_fields(self) -> None:
        record = _make_record(extra={"event": "extraction.batch.emitted"})

        parsed = json.loads(self.formatter.format(record))

        for leaky_field in ("args", "msg", "exc_info", "pathname", "lineno", "funcName", "process"):
            with self.subTest(field=leaky_field):
                self.assertNotIn(leaky_field, parsed)

    def test_a_plain_log_call_without_extra_still_formats(self) -> None:
        """Cobre logs que não seguem nosso padrão de evento — por exemplo os
        próprios logs internos do Prefect nos mesmos loggers observados."""
        record = _make_record(message="Task run 'extract' - Finished in state Completed()")

        parsed = json.loads(self.formatter.format(record))

        self.assertEqual(parsed["message"], "Task run 'extract' - Finished in state Completed()")

    def test_a_non_serializable_extra_value_does_not_break_formatting(self) -> None:
        record = _make_record(extra={"event": "extraction.batch.emitted", "odd": {1, 2, 3}})

        formatted = self.formatter.format(record)

        parsed = json.loads(formatted)
        self.assertEqual(parsed["odd"], str({1, 2, 3}))


class ConfigureJsonLoggingTests(unittest.TestCase):
    def tearDown(self) -> None:
        for logger_name in OBSERVED_LOGGERS:
            logger = logging.getLogger(logger_name)
            for handler in list(logger.handlers):
                if isinstance(handler, logging.StreamHandler) and isinstance(
                    handler.formatter, StructuredJsonFormatter
                ):
                    logger.removeHandler(handler)

    def test_attaches_a_json_handler_to_every_observed_logger(self) -> None:
        configure_json_logging(stream=io.StringIO())

        for logger_name in OBSERVED_LOGGERS:
            with self.subTest(logger=logger_name):
                logger = logging.getLogger(logger_name)
                json_handlers = [
                    handler
                    for handler in logger.handlers
                    if isinstance(handler.formatter, StructuredJsonFormatter)
                ]
                self.assertEqual(len(json_handlers), 1)

    def test_calling_it_twice_does_not_attach_duplicate_handlers(self) -> None:
        configure_json_logging(stream=io.StringIO())
        configure_json_logging(stream=io.StringIO())

        for logger_name in OBSERVED_LOGGERS:
            with self.subTest(logger=logger_name):
                logger = logging.getLogger(logger_name)
                json_handlers = [
                    handler
                    for handler in logger.handlers
                    if isinstance(handler.formatter, StructuredJsonFormatter)
                ]
                self.assertEqual(len(json_handlers), 1)

    def test_does_not_remove_a_pre_existing_handler(self) -> None:
        """`prefect.task_runs`/`prefect.flow_runs` já chegam com o
        `APILogHandler` do próprio Prefect, que alimenta o histórico de
        execução da UI (OQ-02/OQ-03). Configurar o JSON soma um handler
        novo — não pode remover esse, ou o histórico para de ser alimentado.
        """
        pre_existing = logging.StreamHandler(io.StringIO())
        logger = logging.getLogger("prefect.task_runs")
        logger.addHandler(pre_existing)
        try:
            configure_json_logging(stream=io.StringIO())

            self.assertIn(pre_existing, logger.handlers)
        finally:
            logger.removeHandler(pre_existing)

    def test_a_logged_event_reaches_the_stream_as_one_json_line(self) -> None:
        stream = io.StringIO()
        configure_json_logging(stream=stream)

        logging.getLogger("etl.extraction").info(
            "extraction.batch.emitted",
            extra={"event": "extraction.batch.emitted", "source": "empresas"},
        )

        lines = [line for line in stream.getvalue().splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        parsed = json.loads(lines[0])
        self.assertEqual(parsed["source"], "empresas")


if __name__ == "__main__":
    unittest.main()
