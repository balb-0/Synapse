"""Disparo da ingestão pela chegada de objeto.

Cobre as funções puras do adaptador ``scripts/orchestration/watch_landing.py``
sem exigir MinIO em execução:

- ``infer_source``: só aceita ``<prefix>/<fonte>.csv`` para as seis fontes;
- ``extract_keys``: só reage a ``s3:ObjectCreated:*``, ignorando remoções e
  testes de notificação; pares sem bucket/chave são descartados.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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


def _obj(key: str):
    return mock.Mock(object_name=key)


class PollOnceTest(unittest.TestCase):
    def test_falha_numa_chave_nao_mata_a_varredura(self):
        client = mock.Mock()
        client.list_objects.return_value = iter(
            [
                _obj("landing/empresas.csv"),
                _obj("landing/clientes.csv"),
                _obj("landing/pesquisas.csv"),
            ]
        )
        calls = []

        def ingest(bucket, key, source):
            calls.append(key)
            if key == "landing/clientes.csv":
                raise RuntimeError("falha simulada")
            return {"status": "loaded"}

        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "seen.json"
            with (
                mock.patch.object(watch_landing, "_minio_client", return_value=client),
                mock.patch.object(watch_landing, "ingest", side_effect=ingest),
            ):
                outcomes = watch_landing.poll_once("balde", "landing", state)
            self.assertEqual([o["status"] for o in outcomes], ["loaded", "loaded"])
            self.assertEqual(
                calls,
                ["landing/empresas.csv", "landing/clientes.csv", "landing/pesquisas.csv"],
            )
            # progresso gravado mesmo com a falha no meio
            seen = watch_landing._load_seen(state)
            self.assertIn("landing/empresas.csv", seen)
            self.assertIn("landing/pesquisas.csv", seen)


if __name__ == "__main__":
    unittest.main()
