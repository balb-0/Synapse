from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction import (  # noqa: E402
    CLIENTES_REQUIRED_COLUMNS,
    RESPONDENTES_REQUIRED_COLUMNS,
    ClientesExtractor,
    ObjectReference,
    RespondentesExtractor,
)
from tests.extraction.helpers import MemoryObjectReader, csv_payload  # noqa: E402


class MessageCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


class ClientesRespondentesExtractorTests(unittest.TestCase):
    def test_clientes_preserves_source_keys_and_sensitive_value(self) -> None:
        payload = csv_payload(
            CLIENTES_REQUIRED_COLUMNS,
            [
                [
                    "00048",
                    "001043",
                    "Contato técnico",
                    "Pesquisa",
                    "pessoa.sintetica@example.invalid",
                ]
            ],
        )
        extractor = ClientesExtractor(
            object_reader=MemoryObjectReader(payload),
            object_reference=ObjectReference(
                bucket="sindusfarma-data",
                key="landing/clientes.csv",
            ),
        )

        batch = next(extractor.read(run_id="run-clientes"))

        self.assertEqual(batch.records[0]["id_cliente"], "00048")
        self.assertEqual(batch.records[0]["id_empresa"], "001043")
        self.assertEqual(
            batch.records[0]["e-mail"],
            "pessoa.sintetica@example.invalid",
        )
        self.assertEqual(batch.metadata.source, "clientes")
        self.assertEqual(batch.metadata.task_id, "extract-clientes")

    def test_respondentes_preserves_candidate_composite_key(self) -> None:
        payload = csv_payload(
            RESPONDENTES_REQUIRED_COLUMNS,
            [
                [
                    "00414",
                    "16/03/2026 18:58",
                    "16/03/2026 19:05",
                    "001043",
                    "0,00%",
                    "00048",
                ]
            ],
        )
        extractor = RespondentesExtractor(
            object_reader=MemoryObjectReader(payload),
            object_reference=ObjectReference(
                bucket="sindusfarma-data",
                key="landing/respondentes.csv",
            ),
        )

        batch = next(extractor.read(run_id="run-respondentes"))

        candidate_key = (
            batch.records[0]["id_pesq"],
            batch.records[0]["id_empresa"],
            batch.records[0]["id_cliente"],
        )
        self.assertEqual(candidate_key, ("00414", "001043", "00048"))
        self.assertEqual(batch.records[0]["market_share"], "0,00%")
        self.assertEqual(batch.metadata.source, "respondentes")
        self.assertEqual(batch.metadata.task_id, "extract-respondentes")

    def test_sensitive_content_is_absent_from_logs_and_attributes(self) -> None:
        sensitive_email = "dado.sensivel@example.invalid"
        payload = csv_payload(
            CLIENTES_REQUIRED_COLUMNS,
            [["42", "60", "Cargo", "Área", sensitive_email]],
        )
        extractor = ClientesExtractor(
            object_reader=MemoryObjectReader(payload),
            object_reference=ObjectReference(
                bucket="sindusfarma-data",
                key="landing/clientes.csv",
                event_id="event-clientes",
            ),
        )
        collector = MessageCollector()
        root_logger = logging.getLogger()
        root_logger.addHandler(collector)
        try:
            batch = next(extractor.read(run_id="run-safe-log"))
        finally:
            root_logger.removeHandler(collector)

        rendered_logs = "\n".join(collector.messages)
        rendered_attributes = str(batch.as_attributes())
        self.assertNotIn(sensitive_email, rendered_logs)
        self.assertNotIn(sensitive_email, rendered_attributes)
        self.assertNotIn("e-mail", rendered_attributes)

    def test_clientes_accepts_unconfirmed_source_identifier(self) -> None:
        payload = csv_payload(
            CLIENTES_REQUIRED_COLUMNS,
            [["s/i", "", "", "", ""]],
        )
        extractor = ClientesExtractor(
            object_reader=MemoryObjectReader(payload),
            object_reference=ObjectReference(
                bucket="sindusfarma-data",
                key="landing/clientes.csv",
            ),
        )

        batch = next(extractor.read(run_id="run-source-value"))

        self.assertEqual(batch.records[0]["id_cliente"], "s/i")
        self.assertEqual(batch.records[0]["id_empresa"], "")


if __name__ == "__main__":
    unittest.main()
