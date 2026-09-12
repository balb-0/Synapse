from __future__ import annotations

import hashlib
import sys
import unittest
from io import BytesIO
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction import (  # noqa: E402
    EMPRESAS_REQUIRED_COLUMNS,
    PESQUISAS_REQUIRED_COLUMNS,
    EmpresasExtractor,
    MalformedSourceError,
    MinioObjectReader,
    ObjectReference,
    PesquisasExtractor,
)
from tests.extraction.helpers import MemoryObjectReader, csv_payload  # noqa: E402


class TrackingResponse(BytesIO):
    def __init__(self, payload: bytes) -> None:
        super().__init__(payload)
        self.connection_released = False

    def release_conn(self) -> None:
        self.connection_released = True


class FakeMinioClient:
    def __init__(self, response: TrackingResponse) -> None:
        self.response = response
        self.calls: list[tuple[str, str, dict[str, str]]] = []

    def get_object(
        self,
        bucket: str,
        key: str,
        **options: str,
    ) -> TrackingResponse:
        self.calls.append((bucket, key, options))
        return self.response


class CsvObjectExtractorTests(unittest.TestCase):
    def test_extracts_pesquisas_and_names_empty_headers_by_position(self) -> None:
        headers = PESQUISAS_REQUIRED_COLUMNS + ("", "")
        values = [str(position) for position in range(1, len(headers) + 1)]
        payload = csv_payload(headers, [values])
        reader = MemoryObjectReader(payload)
        reference = ObjectReference(
            bucket="sindusfarma-data",
            key="landing/pesquisas.csv",
            version_id="version-1",
            event_id="event-1",
        )

        batches = list(
            PesquisasExtractor(
                object_reader=reader,
                object_reference=reference,
            ).read(run_id="run-001")
        )

        self.assertEqual(len(batches), 1)
        batch = batches[0]
        self.assertEqual(batch.records[0]["id"], "1")
        self.assertEqual(batch.records[0]["unnamed_column_23"], "23")
        self.assertEqual(batch.records[0]["unnamed_column_24"], "24")
        self.assertEqual(batch.metadata.source, "pesquisas")
        self.assertEqual(batch.metadata.record_count, 1)
        self.assertEqual(batch.metadata.byte_count, len(payload))
        self.assertEqual(
            batch.metadata.source_checksum,
            hashlib.sha256(payload).hexdigest(),
        )
        self.assertEqual(
            batch.checkpoint.source_version,
            "sha256:" + hashlib.sha256(payload).hexdigest(),
        )
        self.assertEqual(batch.checkpoint.position, "row:1")
        self.assertEqual(reader.payload, payload)
        self.assertEqual(reader.opened_references, [reference])

    def test_extracts_empresas_preserving_source_keys_and_values(self) -> None:
        values = [
            "60",
            "Empresa sintética",
            "8,25%",
            "Nacional",
            "Sim",
            "Efetivo",
            "São Paulo",
            "São Paulo",
            "Brasil",
        ]
        payload = csv_payload(EMPRESAS_REQUIRED_COLUMNS, [values])
        reader = MemoryObjectReader(payload)

        batch = next(
            EmpresasExtractor(
                object_reader=reader,
                object_reference=ObjectReference(
                    bucket="sindusfarma-data",
                    key="landing/empresas.csv",
                ),
            ).read(run_id="run-002")
        )

        self.assertEqual(batch.records[0]["ID"], "60")
        self.assertEqual(batch.records[0]["% de mercado"], "8,25%")
        self.assertEqual(batch.records[0]["Nome Fantasia"], "Empresa sintética")
        self.assertEqual(batch.metadata.task_id, "extract-empresas")

    def test_emits_empty_batch_when_csv_has_only_header(self) -> None:
        payload = csv_payload(EMPRESAS_REQUIRED_COLUMNS, [])

        batch = next(
            EmpresasExtractor(
                object_reader=MemoryObjectReader(payload),
                object_reference=ObjectReference(
                    bucket="sindusfarma-data",
                    key="landing/empresas.csv",
                ),
            ).read(run_id="run-empty")
        )

        self.assertEqual(batch.records, ())
        self.assertEqual(batch.metadata.record_count, 0)
        self.assertEqual(batch.checkpoint.position, "row:0")

    def test_rejects_source_without_required_columns(self) -> None:
        payload = csv_payload(("ID", "Nome Fantasia"), [["1", "Empresa"]])
        extractor = EmpresasExtractor(
            object_reader=MemoryObjectReader(payload),
            object_reference=ObjectReference(
                bucket="sindusfarma-data",
                key="landing/empresas.csv",
            ),
        )

        with self.assertRaisesRegex(MalformedSourceError, "colunas obrigatórias"):
            list(extractor.read(run_id="run-invalid"))

    def test_rejects_rows_with_unexpected_field_count(self) -> None:
        payload = (
            ";".join(EMPRESAS_REQUIRED_COLUMNS).encode("utf-8") + b"\n1;campos;insuficientes\n"
        )
        extractor = EmpresasExtractor(
            object_reader=MemoryObjectReader(payload),
            object_reference=ObjectReference(
                bucket="sindusfarma-data",
                key="landing/empresas.csv",
            ),
        )

        with self.assertRaisesRegex(MalformedSourceError, "linha 2"):
            list(extractor.read(run_id="run-invalid-row"))

    def test_minio_reader_passes_version_and_releases_connection(self) -> None:
        response = TrackingResponse(b"conteudo")
        client = FakeMinioClient(response)
        reader = MinioObjectReader(client)
        reference = ObjectReference(
            bucket="sindusfarma-data",
            key="landing/empresas.csv",
            version_id="version-7",
        )

        with reader.open(reference) as stream:
            self.assertEqual(stream.read(), b"conteudo")

        self.assertEqual(
            client.calls,
            [
                (
                    "sindusfarma-data",
                    "landing/empresas.csv",
                    {"version_id": "version-7"},
                )
            ],
        )
        self.assertTrue(response.closed)
        self.assertTrue(response.connection_released)


if __name__ == "__main__":
    unittest.main()
