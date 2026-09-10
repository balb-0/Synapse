from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction import (  # noqa: E402
    REDACTED,
    ConfigurationError,
    SecretValue,
    load_extraction_settings,
)


class ExtractionSettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.source_dir = Path(self.temporary_directory.name)
        self.environment = {
            "ETL_MINIO_ENDPOINT": "http://minio:9000",
            "ETL_MINIO_BUCKET": "sindusfarma-data",
            "ETL_MINIO_INPUT_PREFIX": "landing",
            "ETL_MINIO_ACCESS_KEY": "access-key-for-test",
            "ETL_MINIO_SECRET_KEY": "secret-key-for-test",
            "ETL_REQUEST_TIMEOUT_SECONDS": "30",
            "ETL_EXTRACTION_BATCH_SIZE": "1000",
            "ETL_EXTRACTION_MAX_ATTEMPTS": "4",
            "ETL_EXTRACTION_RETRY_INITIAL_DELAY_SECONDS": "0.25",
            "ETL_EXTRACTION_RETRY_MAX_DELAY_SECONDS": "2",
        }

    def test_loads_complete_configuration_from_environment(self) -> None:
        settings = load_extraction_settings(environ=self.environment)

        self.assertIsNone(settings.source_dir)
        self.assertEqual(settings.minio_input_prefix, "landing")
        self.assertEqual(settings.request_timeout_seconds, 30.0)
        self.assertEqual(settings.batch_size, 1000)
        self.assertEqual(settings.max_attempts, 4)
        self.assertEqual(settings.retry_initial_delay_seconds, 0.25)
        self.assertEqual(settings.retry_max_delay_seconds, 2.0)
        self.assertEqual(
            settings.minio_access_key.get_secret_value(), "access-key-for-test"
        )

    def test_explicit_parameters_override_environment(self) -> None:
        settings = load_extraction_settings(
            parameters={
                "minio_endpoint": "http://localhost:19000/",
                "minio_input_prefix": "/incoming/",
                "request_timeout_seconds": 12,
                "batch_size": 250,
                "max_attempts": 2,
                "retry_initial_delay_seconds": 0,
                "retry_max_delay_seconds": 1,
            },
            environ=self.environment,
        )

        self.assertEqual(settings.minio_endpoint, "http://localhost:19000")
        self.assertEqual(settings.minio_input_prefix, "incoming")
        self.assertEqual(settings.request_timeout_seconds, 12.0)
        self.assertEqual(settings.batch_size, 250)
        self.assertEqual(settings.max_attempts, 2)
        self.assertEqual(settings.retry_initial_delay_seconds, 0.0)
        self.assertEqual(settings.retry_max_delay_seconds, 1.0)

    def test_uses_safe_defaults_for_optional_values(self) -> None:
        environment = dict(self.environment)
        environment.pop("ETL_MINIO_INPUT_PREFIX")
        environment.pop("ETL_REQUEST_TIMEOUT_SECONDS")
        environment.pop("ETL_EXTRACTION_BATCH_SIZE")
        environment.pop("ETL_EXTRACTION_MAX_ATTEMPTS")
        environment.pop("ETL_EXTRACTION_RETRY_INITIAL_DELAY_SECONDS")
        environment.pop("ETL_EXTRACTION_RETRY_MAX_DELAY_SECONDS")

        settings = load_extraction_settings(environ=environment)

        self.assertEqual(settings.minio_input_prefix, "landing")
        self.assertEqual(settings.request_timeout_seconds, 30.0)
        self.assertEqual(settings.batch_size, 1000)
        self.assertEqual(settings.max_attempts, 3)
        self.assertEqual(settings.retry_initial_delay_seconds, 0.5)
        self.assertEqual(settings.retry_max_delay_seconds, 5.0)

    def test_rejects_invalid_batch_size(self) -> None:
        for invalid_value in ("0", "1.5", "invalid", 0, True):
            with self.subTest(invalid_value=invalid_value):
                with self.assertRaisesRegex(ConfigurationError, "inteiro positivo"):
                    load_extraction_settings(
                        parameters={"batch_size": invalid_value},
                        environ=self.environment,
                    )

    def test_rejects_invalid_retry_configuration(self) -> None:
        invalid_parameters = (
            {"max_attempts": 0},
            {"max_attempts": "1.5"},
            {"retry_initial_delay_seconds": -1},
            {"retry_max_delay_seconds": "invalid"},
            {
                "retry_initial_delay_seconds": 2,
                "retry_max_delay_seconds": 1,
            },
        )

        for parameters in invalid_parameters:
            with self.subTest(parameters=parameters):
                with self.assertRaises(ConfigurationError):
                    load_extraction_settings(
                        parameters=parameters,
                        environ=self.environment,
                    )

    def test_accepts_optional_local_source_directory(self) -> None:
        environment = {
            **self.environment,
            "ETL_SOURCE_DIR": str(self.source_dir),
        }

        settings = load_extraction_settings(environ=environment)

        self.assertEqual(settings.source_dir, self.source_dir.resolve())

    def test_reports_missing_required_configuration_without_values(self) -> None:
        environment = dict(self.environment)
        environment.pop("ETL_MINIO_ACCESS_KEY")

        with self.assertRaises(ConfigurationError) as context:
            load_extraction_settings(environ=environment)

        message = str(context.exception)
        self.assertIn("ETL_MINIO_ACCESS_KEY", message)
        self.assertNotIn("secret-key-for-test", message)

    def test_rejects_missing_source_directory(self) -> None:
        environment = {
            **self.environment,
            "ETL_SOURCE_DIR": str(self.source_dir / "inexistente"),
        }

        with self.assertRaisesRegex(ConfigurationError, "não existe"):
            load_extraction_settings(environ=environment)

    def test_rejects_credentials_embedded_in_endpoint(self) -> None:
        environment = dict(self.environment)
        environment["ETL_MINIO_ENDPOINT"] = "http://usuario:senha@minio:9000"

        with self.assertRaises(ConfigurationError) as context:
            load_extraction_settings(environ=environment)

        self.assertNotIn("usuario", str(context.exception))
        self.assertNotIn("senha", str(context.exception))

    def test_rejects_malformed_endpoint_without_exposing_its_value(self) -> None:
        environment = dict(self.environment)
        environment["ETL_MINIO_ENDPOINT"] = "http://[segredo"

        with self.assertRaises(ConfigurationError) as context:
            load_extraction_settings(environ=environment)

        self.assertNotIn("segredo", str(context.exception))

    def test_rejects_parent_reference_in_minio_prefix(self) -> None:
        environment = dict(self.environment)
        environment["ETL_MINIO_INPUT_PREFIX"] = "landing/../private"

        with self.assertRaisesRegex(ConfigurationError, "prefixo relativo"):
            load_extraction_settings(environ=environment)

    def test_secrets_are_redacted_from_representations(self) -> None:
        settings = load_extraction_settings(environ=self.environment)
        rendered = f"{settings!r} {settings.safe_summary()}"

        self.assertNotIn("access-key-for-test", rendered)
        self.assertNotIn("secret-key-for-test", rendered)
        self.assertEqual(settings.safe_summary()["minio_access_key"], REDACTED)
        self.assertEqual(str(SecretValue("another-secret")), REDACTED)

    def test_rejects_unknown_parameter_name(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "desconhecidos"):
            load_extraction_settings(
                parameters={"minio_password": "must-not-be-used"},
                environ=self.environment,
            )


if __name__ == "__main__":
    unittest.main()
