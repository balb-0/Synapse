"""Testes de integração da telemetria e do coletor indisponível (OB-10).

Duas garantias que nenhum teste de camada isolada prova sozinho, porque cada
um mocka a camada acima e abaixo dele:

1. Que os eventos publicados pelas quatro camadas, quando escritos pelo
   formatter de produção (``StructuredJsonFormatter``/``configure_json_logging``)
   durante um flow ``ingest-object`` completo, saem como uma linha JSON válida
   com os campos de correlação combinados (ADR 0001) e sem dado pessoal das
   fontes.
2. Que uma falha do lado do coletor — aqui simulada como o próprio logger de
   extração/transformação/carga quebrando ao publicar, o pior caso que o
   Python consegue expressar (o UDP real do OB-07 nunca chega a levantar uma
   exceção Python) — não impede o flow de terminar e carregar corretamente.

Não quebra o handler de ``prefect.task_runs``/``prefect.flow_runs``: esses
loggers já têm o ``APILogHandler`` do próprio Prefect anexado, e um handler
quebrado ali derrubaria também o bookkeeping interno do Prefect, não só o
nosso ``_log_event`` — um teste assim não provaria nada sobre o nosso código,
só sobre o Prefect. A resiliência de ``_log_event`` isolado já é coberta em
``tests/orchestration/test_orchestration_logs.py``.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import sys
import tempfile
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from io import BytesIO, StringIO
from pathlib import Path
from typing import BinaryIO
from unittest import mock

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction import ObjectReference  # noqa: E402
from etl.orchestration import flow as flow_module  # noqa: E402
from etl.orchestration.logging_config import (  # noqa: E402
    StructuredJsonFormatter,
    configure_json_logging,
)
from tests import fixtures  # noqa: E402

DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None
SEM_DUCKDB = "duckdb não instalado; use pip install -r requirements.txt"

BUCKET = "landing-test"
AMBIENTE_FICTICIO = {
    "ETL_MINIO_ENDPOINT": "http://minio.invalid:9000",
    "ETL_MINIO_BUCKET": BUCKET,
    "ETL_MINIO_ACCESS_KEY": "teste-sem-segredo",
    "ETL_MINIO_SECRET_KEY": "teste-sem-segredo",
}

# Loggers que o nosso código controla de ponta a ponta — não inclui
# prefect.task_runs/prefect.flow_runs (ver docstring do módulo).
LOGGERS_DAS_CAMADAS_DE_DADOS = ("etl.extraction", "etl.transformation", "etl.load")

# Valor sintético (não é PII de verdade — ver tests/fixtures/__init__.py) já
# presente no fixture de clientes: se aparecer no stream, o evento carregou
# um campo de negócio que não deveria estar num log técnico.
EMAIL_SINTETICO_NO_FIXTURE = "pessoa1@example.invalid"
NOME_FANTASIA_SINTETICO_NO_FIXTURE = "Empresa Alfa"


class LeitorEmMemoria:
    def __init__(self, payloads: dict[str, bytes]) -> None:
        self.payloads = payloads

    @contextmanager
    def open(self, reference: ObjectReference) -> Iterator[BinaryIO]:
        yield BytesIO(self.payloads[Path(reference.key).stem])


class HandlerQuebrado(logging.Handler):
    """Pior caso do lado do Python para "coletor fora do ar": a própria
    publicação do evento levanta. O transporte real (UDP/GELF, OB-07) nunca
    faz isso — o SO descarta o pacote sem que o processo perceba — então
    isto é deliberadamente mais hostil do que o cenário de produção.
    """

    def emit(self, record: logging.LogRecord) -> None:
        raise OSError("coletor indisponível (simulado)")


class _BaseIngestObjectFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = str(Path(self.temporary_directory.name) / "telemetria.duckdb")
        payloads = {source: fixtures.payload(source) for source in fixtures.ORDEM_CARGA}
        leitor = LeitorEmMemoria(payloads)
        ambiente = mock.patch.dict(os.environ, AMBIENTE_FICTICIO)
        self.addCleanup(ambiente.stop)
        ambiente.start()
        leitor_mock = mock.patch.object(flow_module, "MinioObjectReader", lambda client: leitor)
        self.addCleanup(leitor_mock.stop)
        leitor_mock.start()

    def _ingerir(self, source: str) -> dict:
        return flow_module.ingest_object(
            source=source,
            bucket=BUCKET,
            key=f"landing/{source}.csv",
            db_path=self.database_path,
        )


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class EventosSaemNoFormatoAcordadoTests(_BaseIngestObjectFixture):
    """O formatter de produção processa eventos reais de um flow completo,
    não uma chamada isolada com atributos escolhidos a dedo pelo teste."""

    def setUp(self) -> None:
        super().setUp()
        self.stream = StringIO()
        configure_json_logging(stream=self.stream)
        self.addCleanup(self._remover_handlers_json)

    def _remover_handlers_json(self) -> None:
        for logger_name in ("etl.extraction", "etl.transformation", "etl.load"):
            logger = logging.getLogger(logger_name)
            for handler in list(logger.handlers):
                if isinstance(handler.formatter, StructuredJsonFormatter):
                    logger.removeHandler(handler)

    def _linhas_de_evento(self) -> list[dict]:
        linhas = [json.loads(line) for line in self.stream.getvalue().splitlines() if line.strip()]
        return [linha for linha in linhas if "event" in linha]

    def test_o_flow_completo_publica_eventos_das_tres_camadas_de_dados_como_json_valido(
        self,
    ) -> None:
        self._ingerir("empresas")

        eventos = {linha["event"] for linha in self._linhas_de_evento()}

        self.assertIn("extraction.batch.emitted", eventos)
        self.assertIn("transformation.batch.emitted", eventos)
        self.assertIn("load.batch.emitted", eventos)

    def test_todo_evento_tem_os_campos_minimos_de_correlacao_acordados(self) -> None:
        self._ingerir("empresas")

        eventos = self._linhas_de_evento()
        self.assertTrue(eventos)
        for linha in eventos:
            with self.subTest(event=linha["event"]):
                self.assertIn("stage", linha)
                self.assertIn("timestamp", linha)
                self.assertIn("level", linha)
                self.assertIn("run_id", linha)

    def test_run_id_correlaciona_os_eventos_das_tres_camadas_de_dados(self) -> None:
        self._ingerir("empresas")

        run_ids = {linha["run_id"] for linha in self._linhas_de_evento()}

        self.assertEqual(len(run_ids), 1)

    def test_nenhum_evento_carrega_dado_de_negocio_das_fontes(self) -> None:
        # empresas primeiro (clientes depende dela por empresa_id).
        self._ingerir("empresas")
        self._ingerir("clientes")

        serializado = self.stream.getvalue()
        self.assertNotIn(EMAIL_SINTETICO_NO_FIXTURE, serializado)
        self.assertNotIn(NOME_FANTASIA_SINTETICO_NO_FIXTURE, serializado)


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class PipelineConcluiComColetorIndisponivelTests(_BaseIngestObjectFixture):
    def setUp(self) -> None:
        super().setUp()
        for logger_name in LOGGERS_DAS_CAMADAS_DE_DADOS:
            logger = logging.getLogger(logger_name)
            handler = HandlerQuebrado()
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            self.addCleanup(logger.removeHandler, handler)

    def test_ingest_object_conclui_e_carrega_mesmo_com_as_tres_camadas_de_dados_quebradas(
        self,
    ) -> None:
        resultado = self._ingerir("empresas")

        self.assertEqual(resultado["status"], "loaded")
        loaded = sum(r["loaded"] for r in resultado["reconciliation"])
        self.assertEqual(loaded, 3)

    def test_a_reconciliacao_bate_com_uma_conexao_nova_ao_banco(self) -> None:
        import duckdb

        self._ingerir("empresas")

        with duckdb.connect(self.database_path, read_only=True) as connection:
            total = connection.execute('SELECT count(*) FROM "ingestao_empresas"').fetchone()

        self.assertEqual(total, (3,))


if __name__ == "__main__":
    unittest.main()
