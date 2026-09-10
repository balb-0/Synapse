from __future__ import annotations

import sys
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import BinaryIO
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction import (  # noqa: E402
    EMPRESAS_REQUIRED_COLUMNS,
    EmpresasExtractor,
    ExtractionSettings,
    FailureCategory,
    FailureNature,
    MalformedSourceError,
    MinioObjectReader,
    ObjectReference,
    PermanentSourceError,
    RetryExecutor,
    RetryLimitExceededError,
    RetryPolicy,
    SecretValue,
    SourceFailure,
    classify_source_failure,
)
from tests.extraction.helpers import csv_payload  # noqa: E402


class RecordingFailureRecorder:
    def __init__(self) -> None:
        self.failures: list[SourceFailure] = []

    def record(self, failure: SourceFailure) -> None:
        self.failures.append(failure)


class ControlledObjectReader:
    def __init__(
        self,
        payload: bytes,
        failures: list[BaseException],
        *,
        repeat_last_failure: bool = False,
    ) -> None:
        self.payload = payload
        self.failures = list(failures)
        self.repeat_last_failure = repeat_last_failure
        self.attempts = 0

    @contextmanager
    def open(self, reference: ObjectReference) -> Iterator[BinaryIO]:
        del reference
        self.attempts += 1
        if self.failures:
            failure = (
                self.failures[0]
                if self.repeat_last_failure
                else self.failures.pop(0)
            )
            raise failure
        yield BytesIO(self.payload)


class SourceServiceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class HttpSourceError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status
        super().__init__("detalhe não deve ser usado na classificação")


class TimeoutAfterPayloadStream(BytesIO):
    def __init__(self, payload: bytes) -> None:
        super().__init__(payload)
        self._payload_was_read = False

    def read(self, size: int = -1) -> bytes:
        if self._payload_was_read:
            raise TimeoutError("falha depois de uma leitura parcial")
        self._payload_was_read = True
        return super().read(size)


class InterruptedObjectReader:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.attempts = 0

    @contextmanager
    def open(self, reference: ObjectReference) -> Iterator[BinaryIO]:
        del reference
        self.attempts += 1
        if self.attempts == 1:
            yield TimeoutAfterPayloadStream(self.payload)
            return
        yield BytesIO(self.payload)


def _payload() -> bytes:
    return csv_payload(
        EMPRESAS_REQUIRED_COLUMNS,
        [
            [
                "1",
                "Empresa A",
                "1%",
                "Nacional",
                "Sim",
                "Efetivo",
                "SP",
                "SP",
                "Brasil",
            ]
        ],
    )


def _extractor(
    reader: ControlledObjectReader,
    executor: RetryExecutor,
) -> EmpresasExtractor:
    return EmpresasExtractor(
        object_reader=reader,
        object_reference=ObjectReference(
            bucket="sindusfarma-data",
            key="landing/empresas.csv",
        ),
        retry_executor=executor,
    )


class ExtractionResilienceTests(unittest.TestCase):
    def test_retries_transient_timeout_with_limited_backoff(self) -> None:
        recorder = RecordingFailureRecorder()
        delays: list[float] = []
        executor = RetryExecutor(
            policy=RetryPolicy(
                max_attempts=3,
                initial_delay_seconds=0.1,
                max_delay_seconds=1,
            ),
            recorder=recorder,
            sleep=delays.append,
        )
        reader = ControlledObjectReader(
            _payload(),
            [TimeoutError("endpoint-secreto"), TimeoutError("endpoint-secreto")],
        )

        batches = list(_extractor(reader, executor).read(run_id="run-retry"))

        self.assertEqual(reader.attempts, 3)
        self.assertEqual(delays, [0.1, 0.2])
        self.assertEqual(batches[0].records[0]["ID"], "1")
        self.assertEqual(
            [failure.category for failure in recorder.failures],
            [FailureCategory.TIMEOUT, FailureCategory.TIMEOUT],
        )
        self.assertTrue(all(failure.retry_scheduled for failure in recorder.failures))

    def test_discards_partial_buffer_before_retrying_read(self) -> None:
        payload = _payload()
        recorder = RecordingFailureRecorder()
        executor = RetryExecutor(
            policy=RetryPolicy(
                max_attempts=2,
                initial_delay_seconds=0,
                max_delay_seconds=0,
            ),
            recorder=recorder,
            sleep=lambda _: None,
        )
        reader = InterruptedObjectReader(payload)
        extractor = EmpresasExtractor(
            object_reader=reader,
            object_reference=ObjectReference(
                bucket="sindusfarma-data",
                key="landing/empresas.csv",
            ),
            retry_executor=executor,
        )

        batch = next(extractor.read(run_id="run-partial-read"))

        self.assertEqual(reader.attempts, 2)
        self.assertEqual(batch.metadata.byte_count, len(payload))
        self.assertEqual(batch.records[0]["ID"], "1")

    def test_stops_after_retry_limit_for_transient_failure(self) -> None:
        recorder = RecordingFailureRecorder()
        delays: list[float] = []
        executor = RetryExecutor(
            policy=RetryPolicy(
                max_attempts=3,
                initial_delay_seconds=0.25,
                max_delay_seconds=1,
            ),
            recorder=recorder,
            sleep=delays.append,
        )
        reader = ControlledObjectReader(
            _payload(),
            [ConnectionError("http://usuario:senha@fonte")],
            repeat_last_failure=True,
        )

        with self.assertRaises(RetryLimitExceededError) as context:
            list(_extractor(reader, executor).read(run_id="run-exhausted"))

        self.assertEqual(reader.attempts, 3)
        self.assertEqual(delays, [0.25, 0.5])
        self.assertEqual(len(recorder.failures), 3)
        self.assertFalse(recorder.failures[-1].retry_scheduled)
        self.assertNotIn("usuario", str(context.exception))
        self.assertNotIn("senha", str(context.exception))

    def test_does_not_retry_permanent_authentication_failure(self) -> None:
        recorder = RecordingFailureRecorder()
        delays: list[float] = []
        executor = RetryExecutor(
            policy=RetryPolicy(max_attempts=4),
            recorder=recorder,
            sleep=delays.append,
        )
        reader = ControlledObjectReader(
            _payload(),
            [SourceServiceError("AccessDenied", "chave-super-secreta")],
        )

        with self.assertRaises(PermanentSourceError) as context:
            list(_extractor(reader, executor).read(run_id="run-auth"))

        self.assertEqual(reader.attempts, 1)
        self.assertEqual(delays, [])
        self.assertEqual(
            context.exception.failure.category,
            FailureCategory.AUTHENTICATION,
        )
        self.assertEqual(context.exception.failure.nature, FailureNature.PERMANENT)
        self.assertNotIn("chave-super-secreta", str(context.exception))

    def test_records_malformed_csv_as_permanent_without_retry(self) -> None:
        recorder = RecordingFailureRecorder()
        executor = RetryExecutor(recorder=recorder, sleep=lambda _: None)
        malformed_payload = csv_payload(("coluna_desconhecida",), [["valor"]])
        reader = ControlledObjectReader(malformed_payload, [])

        with self.assertRaises(MalformedSourceError):
            list(_extractor(reader, executor).read(run_id="run-malformed"))

        self.assertEqual(reader.attempts, 1)
        self.assertEqual(len(recorder.failures), 1)
        self.assertEqual(recorder.failures[0].operation, "parse")
        self.assertEqual(recorder.failures[0].category, FailureCategory.MALFORMED)
        self.assertFalse(recorder.failures[0].retryable)

    def test_classifies_rate_limit_as_transient(self) -> None:
        classification = classify_source_failure(HttpSourceError(429))

        self.assertEqual(classification.category, FailureCategory.RATE_LIMITED)
        self.assertEqual(classification.nature, FailureNature.TRANSIENT)

    def test_failure_attributes_do_not_include_exception_message(self) -> None:
        recorder = RecordingFailureRecorder()
        executor = RetryExecutor(
            policy=RetryPolicy(max_attempts=1),
            recorder=recorder,
            sleep=lambda _: None,
        )
        reader = ControlledObjectReader(
            _payload(),
            [TimeoutError("token=nao-pode-aparecer")],
        )

        with self.assertRaises(RetryLimitExceededError):
            list(_extractor(reader, executor).read(run_id="run-safe-record"))

        attributes = str(recorder.failures[0].as_dict())
        self.assertNotIn("token=nao-pode-aparecer", attributes)
        self.assertEqual(recorder.failures[0].exception_type, "TimeoutError")

    def test_minio_reader_configures_timeout_without_hidden_retry(self) -> None:
        settings = ExtractionSettings(
            minio_endpoint="http://minio:9000",
            minio_bucket="sindusfarma-data",
            minio_access_key=SecretValue("access-for-test"),
            minio_secret_key=SecretValue("secret-for-test"),
            request_timeout_seconds=7.5,
        )

        with (
            patch("minio.Minio") as minio_factory,
            patch("urllib3.PoolManager") as pool_factory,
        ):
            reader = MinioObjectReader.from_settings(settings)

        self.assertIsInstance(reader, MinioObjectReader)
        pool_arguments = pool_factory.call_args.kwargs
        self.assertEqual(pool_arguments["timeout"].connect_timeout, 7.5)
        self.assertEqual(pool_arguments["timeout"].read_timeout, 7.5)
        self.assertFalse(pool_arguments["retries"])
        minio_arguments = minio_factory.call_args.kwargs
        self.assertEqual(minio_arguments["endpoint"], "minio:9000")
        self.assertFalse(minio_arguments["secure"])
        self.assertIs(minio_arguments["http_client"], pool_factory.return_value)

    def test_retry_policy_rejects_unbounded_or_invalid_values(self) -> None:
        invalid_policies = (
            {"max_attempts": 0},
            {"initial_delay_seconds": -1},
            {"backoff_multiplier": 0.5},
            {"initial_delay_seconds": 2, "max_delay_seconds": 1},
        )

        for parameters in invalid_policies:
            with self.subTest(parameters=parameters):
                with self.assertRaises(ValueError):
                    RetryPolicy(**parameters)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
