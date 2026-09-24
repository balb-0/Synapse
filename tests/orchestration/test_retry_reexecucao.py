"""Reinício de tarefa falha com retry limitado.

Cobre o contrato de retry das tasks do flow:

- as três tasks têm retry limitado (``retries=2``) com a condição
  ``_should_retry``;
- falha permanente da extração e S3 permanente (ex.: ``NoSuchKey``) falham
  rápido; erro transitório (ex.: ``SlowDown``) e inesperado repetem.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

PREFECT_INSTALLED = importlib.util.find_spec("prefect") is not None
MINIO_INSTALLED = importlib.util.find_spec("minio") is not None
if PREFECT_INSTALLED:
    from etl.extraction import ExtractionError
    from etl.orchestration import flow as flow_module

SEM_PREFECT = "prefect não instalado; use pip install -r requirements.txt"
SEM_MINIO = "minio não instalado; use pip install -r requirements.txt"


def _state_with(error: BaseException | None):
    state = mock.Mock()
    if error is None:
        state.result.return_value = None
    else:
        state.result.side_effect = error
    return state


def _s3_error(code: str):
    from minio.error import S3Error

    return S3Error(mock.Mock(), code, "mensagem", "recurso", "req", "host", "balde", "chave")


@unittest.skipUnless(PREFECT_INSTALLED, SEM_PREFECT)
class RetryTasksTest(unittest.TestCase):
    def test_tasks_tem_retry_limitado_com_condicao(self):
        for task in (
            flow_module.extract,
            flow_module.transform,
            flow_module.load,
        ):
            self.assertEqual(task.retries, 2, f"{task.name} sem retries=2")
            self.assertIs(
                task.retry_condition_fn,
                flow_module._should_retry,
                f"{task.name} sem a condição de retry",
            )

    def test_falha_permanente_nao_repete(self):
        for error in (
            ExtractionError("fonte"),
            ValueError("schema"),
            KeyError("coluna"),
        ):
            self.assertFalse(
                flow_module._should_retry(mock.Mock(), mock.Mock(), _state_with(error)),
                f"{type(error).__name__} deveria falhar rápido",
            )

    def test_erro_inesperado_repete(self):
        self.assertTrue(
            flow_module._should_retry(mock.Mock(), mock.Mock(), _state_with(RuntimeError("boom")))
        )

    def test_sucesso_nao_repete(self):
        self.assertFalse(flow_module._should_retry(mock.Mock(), mock.Mock(), _state_with(None)))

    @unittest.skipUnless(MINIO_INSTALLED, SEM_MINIO)
    def test_s3_permanente_nao_repete(self):
        self.assertFalse(
            flow_module._should_retry(mock.Mock(), mock.Mock(), _state_with(_s3_error("NoSuchKey")))
        )

    @unittest.skipUnless(MINIO_INSTALLED, SEM_MINIO)
    def test_s3_transitorio_repete(self):
        self.assertTrue(
            flow_module._should_retry(mock.Mock(), mock.Mock(), _state_with(_s3_error("SlowDown")))
        )


if __name__ == "__main__":
    unittest.main()
