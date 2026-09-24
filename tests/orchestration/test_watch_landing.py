"""Disparo da ingestão pela chegada de objeto.

Cobre as funções puras do adaptador ``scripts/orchestration/watch_landing.py``
sem exigir MinIO em execução:

- ``infer_source``: só aceita ``<prefix>/<fonte>.csv`` para as seis fontes;
- ``extract_keys``: só reage a ``s3:ObjectCreated:*``, ignorando remoções e
  testes de notificação; pares sem bucket/chave são descartados.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts" / "orchestration"))

import watch_landing  # noqa: E402


class InferSourceTest(unittest.TestCase):
    def test_fontes_validas(self):
        for source in (
            "empresas",
            "pesquisas",
            "clientes",
            "questoes",
            "respondentes",
            "respostas",
        ):
            self.assertEqual(watch_landing.infer_source(f"landing/{source}.csv", "landing"), source)

    def test_fora_do_padrao(self):
        self.assertIsNone(watch_landing.infer_source("landing/desconhecido.csv", "landing"))
        self.assertIsNone(watch_landing.infer_source("landing/empresas.json", "landing"))
        self.assertIsNone(watch_landing.infer_source("landing/sub/empresas.csv", "landing"))
        self.assertIsNone(watch_landing.infer_source("outro/empresas.csv", "landing"))


class ExtractKeysTest(unittest.TestCase):
    def _payload(self, event: str, bucket: str = "sindusfarma", key: str = "landing/empresas.csv"):
        return {
            "Records": [
                {
                    "eventName": event,
                    "s3": {"bucket": {"name": bucket}, "object": {"key": key}},
                }
            ]
        }

    def test_object_created_dispara(self):
        pairs = watch_landing.extract_keys(self._payload("s3:ObjectCreated:Put"))
        self.assertEqual(pairs, [("sindusfarma", "landing/empresas.csv")])

    def test_remocao_nao_dispara(self):
        self.assertEqual(watch_landing.extract_keys(self._payload("s3:ObjectRemoved:Delete")), [])

    def test_par_incompleto_descartado(self):
        self.assertEqual(
            watch_landing.extract_keys(self._payload("s3:ObjectCreated:Put", bucket="")), []
        )
        self.assertEqual(watch_landing.extract_keys({"Records": []}), [])
        self.assertEqual(watch_landing.extract_keys({}), [])


if __name__ == "__main__":
    unittest.main()
