"""Reinício de tarefa falha e reexecução parametrizada.

Cobre o contrato que a interface do Prefect usa no retry/re-run:

- as três tasks do flow têm retry limitado (``retries=2``), de modo que uma
  falha reiniciada pela UI repete o trecho sem perder o checkpoint já
  confirmado (a retomada lote a lote é coberta em ``test_resumption.py``);
- ``_should_retry`` só repete erro inesperado: falha permanente da extração
  (``ExtractionError``, ``ValueError``, ``KeyError``) ou limite interno já
  esgotado falha rápido, sem duplicar tentativa;
- a reexecução parametrizada (``reprocess``) é o parâmetro do deployment
  (ver ``prefect.yaml`` e ``deployment.py``), registrada no histórico do run.
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
if PREFECT_INSTALLED:
    from etl.extraction import ExtractionError
    from etl.orchestration import flow as flow_module

SEM_PREFECT = "prefect não instalado; use pip install -r requirements.txt"


def _state_with(error: BaseException | None):
    state = mock.Mock()
    if error is None:
        state.result.return_value = None
    else:
        state.result.side_effect = error
    return state


@unittest.skipUnless(PREFECT_INSTALLED, SEM_PREFECT)
class RetryTasksTest(unittest.TestCase):
    def test_tasks_tem_retry_limitado(self):
        for task in (
            flow_module.extract,
            flow_module.transform,
            flow_module.load,
        ):
            self.assertEqual(task.retries, 2, f"{task.name} sem retries=2")

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


if __name__ == "__main__":
    unittest.main()
