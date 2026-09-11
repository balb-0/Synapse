"""Testes gray-box de integração através da orquestração (VB-05).

Os cenários atravessam o flow Prefect `ingest_object` de ponta a ponta —
extração, transformação, validação e carga conversam de verdade contra um
DuckDB temporário. O único mock é o leitor de objetos: o MinIO exige Docker e
rede, então um leitor em memória serve as fixtures sintéticas pelo mesmo
contrato ``ObjectReader``. O cliente MinIO real é construído (sem chamadas de
rede) e a configuração passa pelas validações de ambiente de verdade.

Cobertura: contrato entre extração -> transformação -> carga nas seis fontes,
idempotência por objeto, CSV malformado rejeitado sem marcar o objeto (a
fonte pode ser reprocessada) e falha transitória reexecutada pelo mecanismo
de retry da extração.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import BinaryIO
from unittest import mock

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction import ObjectReference  # noqa: E402
from etl.extraction.csv_extractors import MalformedSourceError  # noqa: E402
from etl.orchestration import flow as flow_module  # noqa: E402
from tests import fixtures  # noqa: E402
from tests.extraction.helpers import csv_payload  # noqa: E402

DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None
if DUCKDB_INSTALLED:
    import duckdb

    from etl.load.ddl import table_name

SEM_DUCKDB = "duckdb não instalado; use pip install -r requirements.txt"

BUCKET = "landing-test"
AMBIENTE_FICTICIO = {
    "ETL_MINIO_ENDPOINT": "http://minio.invalid:9000",
    "ETL_MINIO_BUCKET": BUCKET,
    "ETL_MINIO_ACCESS_KEY": "teste-sem-segredo",
    "ETL_MINIO_SECRET_KEY": "teste-sem-segredo",
}


class LeitorEmMemoria:
    """``ObjectReader`` que serve payloads por chave e registra as aberturas."""

    def __init__(self, payloads: dict[str, bytes]) -> None:
        self.payloads = payloads
        self.aberturas: list[str] = []

    @contextmanager
    def open(self, reference: ObjectReference) -> Iterator[BinaryIO]:
        self.aberturas.append(reference.key)
        yield BytesIO(self.payloads[Path(reference.key).stem])


class LeitorComFalhaTransitoria(LeitorEmMemoria):
    """Falha uma vez com erro transitório na abertura da extração.

    A primeira abertura é a leitura do checksum pelo flow e precisa funcionar;
    a segunda é a primeira tentativa da extração, que falha; o retry interno
    do extrator abre de novo e conclui.
    """

    def __init__(self, payloads: dict[str, bytes], falhas: int = 1) -> None:
        super().__init__(payloads)
        self.restantes = falhas

    @contextmanager
    def open(self, reference: ObjectReference) -> Iterator[BinaryIO]:
        self.aberturas.append(reference.key)
        if len(self.aberturas) > 1 and self.restantes > 0:
            self.restantes -= 1
            raise TimeoutError("tempo esgotado simulado")
        yield BytesIO(self.payloads[Path(reference.key).stem])


class EstadoFalso:
    """Simula o estado de uma task do Prefect para a condição de retry."""

    def __init__(self, erro: BaseException) -> None:
        self._erro = erro

    def result(self, raise_on_failure: bool = True):
        raise self._erro


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class GrayBoxOrquestracaoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = str(Path(self.temporary_directory.name) / "gray.duckdb")
        self.payloads = {source: fixtures.payload(source) for source in fixtures.ORDEM_CARGA}
        self.leitor = LeitorEmMemoria(self.payloads)
        ambiente = mock.patch.dict(os.environ, AMBIENTE_FICTICIO)
        self.addCleanup(ambiente.stop)
        ambiente.start()
        leitor_mock = mock.patch.object(
            flow_module, "MinioObjectReader", lambda client: self.leitor
        )
        self.addCleanup(leitor_mock.stop)
        leitor_mock.start()

    def ingestir(self, source: str) -> dict:
        return flow_module.ingest_object(
            source=source,
            bucket=BUCKET,
            key=f"landing/{source}.csv",
            db_path=self.database_path,
        )

    def consulta(self, statement: str):
        with duckdb.connect(self.database_path, read_only=True) as connection:
            return connection.execute(statement).fetchall()

    def test_contrato_entre_etapas_para_as_seis_fontes(self) -> None:
        for source in fixtures.ORDEM_CARGA:
            with self.subTest(fonte=source):
                resultado = self.ingestir(source)
                self.assertEqual(resultado["status"], "loaded")
                esperado = fixtures.ESPERADO[source]
                carregado = sum(r["loaded"] for r in resultado["reconciliation"])
                rejeitado = sum(r["rejected"] for r in resultado["reconciliation"])
                duplicado = sum(r["duplicates"] for r in resultado["reconciliation"])
                self.assertEqual(
                    (carregado, rejeitado, duplicado),
                    (
                        esperado["aceitos"],
                        esperado["rejeitados"],
                        esperado["duplicados"],
                    ),
                )
                total = self.consulta(f'SELECT count(*) FROM "{table_name(source)}"')
                self.assertEqual(total, [(esperado["aceitos"],)])

    def test_rejeicao_vai_para_quarentena_com_motivo(self) -> None:
        self.ingestir("empresas")
        self.ingestir("clientes")

        motivos = self.consulta(
            "SELECT code FROM rejected r JOIN rejected_reason rr USING (rejection_id)"
        )
        self.assertEqual(motivos, [("ORPHAN_REFERENCE",)])

    def test_segunda_entrega_do_mesmo_objeto_e_ignorada(self) -> None:
        primeiro = self.ingestir("empresas")
        segundo = self.ingestir("empresas")

        self.assertEqual(primeiro["status"], "loaded")
        self.assertEqual(segundo["status"], "ignored")
        total = self.consulta('SELECT count(*) FROM "ingestao_empresas"')
        self.assertEqual(total, [(fixtures.ESPERADO["empresas"]["aceitos"],)])

    def test_csv_malformado_falha_sem_marcar_o_objeto(self) -> None:
        self.payloads["empresas"] = csv_payload(("ID", "Nome Fantasia"), [["101", "Empresa Alfa"]])

        with self.assertRaises(MalformedSourceError):
            self.ingestir("empresas")

        carregadas = self.consulta('SELECT count(*) FROM "ingestao_empresas"')
        marcadas = self.consulta("SELECT count(*) FROM _control_object")
        self.assertEqual(carregadas, [(0,)])
        self.assertEqual(marcadas, [(0,)])

        # Sem a marca de concluído, a correção do arquivo permite reprocessar.
        self.payloads["empresas"] = fixtures.payload("empresas")
        resultado = self.ingestir("empresas")
        self.assertEqual(resultado["status"], "loaded")

    def test_falha_transitoria_e_reexecutada_pelo_retry_da_extracao(self) -> None:
        self.leitor = LeitorComFalhaTransitoria(self.payloads)

        resultado = self.ingestir("empresas")

        self.assertEqual(resultado["status"], "loaded")
        # checksum (1) + tentativa que falhou (2) + retry que concluiu (3)
        self.assertEqual(len(self.leitor.aberturas), 3)
        total = self.consulta('SELECT count(*) FROM "ingestao_empresas"')
        self.assertEqual(total, [(fixtures.ESPERADO["empresas"]["aceitos"],)])


class CondicaoDeRetryTests(unittest.TestCase):
    """A decisão de retry do Prefect: transitório inesperado sim, permanente não."""

    def test_erro_permanente_da_extracao_nao_repete(self) -> None:
        estado = EstadoFalso(MalformedSourceError("contrato violado"))
        self.assertFalse(flow_module._should_retry(None, None, estado))

    def test_erro_de_configuracao_nao_repete(self) -> None:
        estado = EstadoFalso(ValueError("configuração inválida"))
        self.assertFalse(flow_module._should_retry(None, None, estado))

    def test_erro_inesperado_repete(self) -> None:
        estado = EstadoFalso(RuntimeError("falha inesperada"))
        self.assertTrue(flow_module._should_retry(None, None, estado))


if __name__ == "__main__":
    unittest.main()
