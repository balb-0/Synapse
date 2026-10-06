"""O resultado do comando é JSON, com falha identificada e sem causa sensível."""

from __future__ import annotations

import importlib.util
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from etl.orchestration.pipeline import PipelineStageError


class PipelineCliTests(unittest.TestCase):
    def setUp(self) -> None:
        path = Path(__file__).resolve().parents[2] / "scripts/orchestration/run_pipeline.py"
        spec = importlib.util.spec_from_file_location("pipeline_cli_under_test", path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        logging = mock.patch.object(self.module, "configure_json_logging")
        logging.start()
        self.addCleanup(logging.stop)

    def test_success_outputs_json_without_python_repr(self) -> None:
        expected = {"status": "completed", "reconciliation": {"reconciled": True}, "missing": None}
        output = StringIO()
        with (
            mock.patch("sys.argv", ["run_pipeline.py", "--publish-dir", "/tmp/fixture-published"]),
            mock.patch.object(self.module, "run_pipeline", return_value=expected),
            redirect_stdout(output),
        ):
            self.module.main()
        self.assertEqual(json.loads(output.getvalue()), expected)
        self.assertIn("true", output.getvalue())
        self.assertIn("null", output.getvalue())

    def test_failure_outputs_stage_and_type_without_original_message(self) -> None:
        error = PipelineStageError("publication", "private-source-and-secret")
        error.__cause__ = PermissionError("credential-private")
        stderr = StringIO()
        with (
            mock.patch("sys.argv", ["run_pipeline.py", "--publish-dir", "/tmp/fixture-published"]),
            mock.patch.object(self.module, "run_pipeline", side_effect=error),
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as context,
        ):
            self.module.main()
        self.assertEqual(context.exception.code, 1)
        self.assertEqual(
            json.loads(stderr.getvalue()),
            {"status": "failed", "failed_stage": "publication", "error_type": "PermissionError"},
        )
        self.assertNotIn("private", stderr.getvalue())
        self.assertNotIn("secret", stderr.getvalue())

    def test_invalid_timestamp_is_argument_error_and_does_not_run_pipeline(self) -> None:
        with (
            mock.patch(
                "sys.argv",
                [
                    "run_pipeline.py",
                    "--publish-dir",
                    "/tmp/fixture-published",
                    "--observed-at",
                    "invalid",
                ],
            ),
            mock.patch.object(self.module, "run_pipeline") as pipeline,
            redirect_stderr(StringIO()),
            self.assertRaises(SystemExit) as context,
        ):
            self.module.main()
        self.assertEqual(context.exception.code, 2)
        pipeline.assert_not_called()


if __name__ == "__main__":
    unittest.main()
