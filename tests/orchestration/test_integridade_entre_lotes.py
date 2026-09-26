"""Integridade de identidade na fronteira entre lotes e na retomada (feedback da Sprint 3).

Cobre os três casos que a suíte anterior não exercitava:

1. participações (``respondentes``), identificadas por checksum+posição,
   repetidas legitimamente e atravessando um checkpoint: a retomada precisa
   preservar a posição absoluta da extração, senão a segunda ocorrência
   colide com a primeira e vira duplicata;
2. a mesma identidade natural, com o mesmo conteúdo, em dois lotes do mesmo
   objeto: a segunda ocorrência é duplicata e a reconciliação fecha;
3. a mesma identidade natural com conteúdos diferentes em dois lotes: todas
   as ocorrências viram ``IDENTITY_CONFLICT``, a mesma decisão tomada quando
   as versões estão no mesmo lote.

Os cenários usam o extrator real (lote de um registro, para forçar várias
fronteiras), as tasks reais do flow e um DuckDB temporário.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction import (  # noqa: E402
    ObjectReference,
    PesquisasExtractor,
    RespondentesExtractor,
)
from etl.transformation.consistency import ReferenceData  # noqa: E402
from tests.extraction.helpers import MemoryObjectReader, csv_payload  # noqa: E402

DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None
PREFECT_INSTALLED = importlib.util.find_spec("prefect") is not None
if DUCKDB_INSTALLED and PREFECT_INSTALLED:
    from etl.load.duckdb_repository import DuckDbLoadRepository
    from etl.orchestration import flow as flow_module

SEM_DEPENDENCIAS = "duckdb e prefect não instalados; use pip install -r requirements.txt"

RESPONDENTES_HEADERS = (
    "id_pesq",
    "hora_inicio",
    "hora_termino",
    "id_empresa",
    "market_share",
    "id_cliente",
)
# Três participações idênticas: a fonte não tem identificador de evento, então
# cada linha física é uma ocorrência legítima distinta (ADR 0002).
PARTICIPACAO = ["1", "2026-01-10T09:00:00Z", "2026-01-10T09:30:00Z", "101", "12,5", "s/i"]
REFERENCIAS_RESPONDENTES = ReferenceData(
    {
        "empresas": [{"empresa_id": "101"}],
        "pesquisas": [{"pesquisa_id": "1"}],
        "clientes": [],
    }
)
PESQUISAS_HEADERS = tuple(
    (REPOSITORY_ROOT / "tests/fixtures/pesquisas.csv")
    .read_text(encoding="utf-8")
    .splitlines()[0]
    .split(";")
)


def _pesquisa(pesquisa_id: str, titulo: str) -> list[str]:
    """Linha de pesquisa com o cabeçalho completo e só id/título preenchidos."""
    valores = {"id": pesquisa_id, "titulo": titulo}
    return [valores.get(coluna, "") for coluna in PESQUISAS_HEADERS]


@contextmanager
def _falhando_no_lote(batch_id: str):
    """Faz `load_batch` falhar só para `batch_id`; os demais usam o método real."""
    original = DuckDbLoadRepository.load_batch

    def load_batch(self, result, metadata):
        if metadata.batch_id == batch_id:
            raise RuntimeError("falha simulada de carga")
        return original(self, result, metadata)

    with mock.patch.object(DuckDbLoadRepository, "load_batch", load_batch):
        yield


@unittest.skipUnless(DUCKDB_INSTALLED and PREFECT_INSTALLED, SEM_DEPENDENCIAS)
class IntegridadeEntreLotesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = str(Path(self.temporary_directory.name) / "lotes.duckdb")
        logger_patch = mock.patch.object(
            flow_module, "get_run_logger", return_value=mock.MagicMock()
        )
        logger_patch.start()
        self.addCleanup(logger_patch.stop)
        # `_current_task_id` fora do Prefect devolve None; o extrator exige um.
        task_patch = mock.patch.object(flow_module, "_current_task_id", return_value="task-teste")
        task_patch.start()
        self.addCleanup(task_patch.stop)

    def _extrair(self, extractor_class, payload: bytes, source: str, checkpoint=None):
        extractor = extractor_class(
            object_reader=MemoryObjectReader(payload),
            object_reference=ObjectReference("landing-test", f"landing/{source}.csv"),
            batch_size=1,
        )
        return list(extractor.read(run_id="run-1", task_id="task-teste", checkpoint=checkpoint))

    def _executar(self, source: str, batches: list, references: ReferenceData) -> list:
        with DuckDbLoadRepository(self.database_path) as repo:
            previous = repo.loaded_identities(source)
        results = flow_module.transform.fn(batches, source, references, previous, "run-1")
        return flow_module.load.fn(self.database_path, results, {}, source=source, run_id="run-1")

    def _consulta(self, sql: str) -> list[tuple]:
        with DuckDbLoadRepository(self.database_path) as repo:
            return repo._conn.execute(sql).fetchall()


class RetomadaDeParticipacoesPorPosicaoTests(IntegridadeEntreLotesTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.payload = csv_payload(RESPONDENTES_HEADERS, [PARTICIPACAO] * 3)

    def test_extrator_informa_a_posicao_absoluta_apos_o_checkpoint(self) -> None:
        todos = self._extrair(RespondentesExtractor, self.payload, "respondentes")
        retomados = self._extrair(
            RespondentesExtractor, self.payload, "respondentes", checkpoint=todos[0].checkpoint
        )

        self.assertEqual([b.metadata.source_offset for b in todos if b.records], [0, 1, 2])
        self.assertEqual([b.metadata.source_offset for b in retomados if b.records], [1, 2])

    def test_participacoes_repetidas_sobrevivem_a_retomada_sem_virar_duplicata(self) -> None:
        batches = self._extrair(RespondentesExtractor, self.payload, "respondentes")
        segundo_lote = next(b for b in batches if b.records and b.metadata.source_offset == 1)

        with _falhando_no_lote(segundo_lote.metadata.batch_id):
            with self.assertRaisesRegex(RuntimeError, "falha simulada"):
                self._executar("respondentes", batches, REFERENCIAS_RESPONDENTES)

        with DuckDbLoadRepository(self.database_path) as repo:
            checkpoint = repo.load("respondentes")
        retomados = self._extrair(
            RespondentesExtractor, self.payload, "respondentes", checkpoint=checkpoint
        )
        reconciliacoes = self._executar("respondentes", retomados, REFERENCIAS_RESPONDENTES)

        self.assertTrue(all(r["balanced"] for r in reconciliacoes))
        self.assertEqual(sum(r["duplicates"] for r in reconciliacoes), 0)
        self.assertEqual(
            self._consulta(
                "SELECT source_offset FROM ingestao_respondentes ORDER BY source_offset"
            ),
            [(0,), (1,), (2,)],
        )
        self.assertEqual(
            self._consulta("SELECT count(DISTINCT record_identity) FROM ingestao_respondentes"),
            [(3,)],
        )


class IdentidadeNaturalEntreLotesTests(IntegridadeEntreLotesTestCase):
    def test_mesma_linha_em_dois_lotes_vira_duplicata_e_reconcilia(self) -> None:
        payload = csv_payload(PESQUISAS_HEADERS, [_pesquisa("1", "A"), _pesquisa("1", "A")])
        batches = self._extrair(PesquisasExtractor, payload, "pesquisas")

        reconciliacoes = self._executar("pesquisas", batches, ReferenceData({}))

        com_registro = [r for r in reconciliacoes if r["extracted"]]
        self.assertEqual(
            [(r["loaded"], r["rejected"], r["duplicates"]) for r in com_registro],
            [(1, 0, 0), (0, 0, 1)],
        )
        self.assertTrue(all(r["balanced"] for r in reconciliacoes))
        self.assertEqual(self._consulta("SELECT count(*) FROM ingestao_pesquisas"), [(1,)])

    def test_versoes_divergentes_em_lotes_distintos_viram_conflito_em_todas(self) -> None:
        payload = csv_payload(PESQUISAS_HEADERS, [_pesquisa("1", "A"), _pesquisa("1", "B")])
        batches = self._extrair(PesquisasExtractor, payload, "pesquisas")

        reconciliacoes = self._executar("pesquisas", batches, ReferenceData({}))

        com_registro = [r for r in reconciliacoes if r["extracted"]]
        self.assertEqual(
            [(r["loaded"], r["rejected"], r["duplicates"]) for r in com_registro],
            [(0, 1, 0), (0, 1, 0)],
        )
        self.assertTrue(all(r["balanced"] for r in reconciliacoes))
        self.assertEqual(self._consulta("SELECT count(*) FROM ingestao_pesquisas"), [(0,)])
        self.assertEqual(
            self._consulta(
                "SELECT DISTINCT code FROM rejected_reason WHERE rejection_id IN "
                "(SELECT rejection_id FROM rejected WHERE source = 'pesquisas')"
            ),
            [("IDENTITY_CONFLICT",)],
        )


@unittest.skipUnless(DUCKDB_INSTALLED and PREFECT_INSTALLED, SEM_DEPENDENCIAS)
class ObjetoSoConcluiComReconciliacaoTests(unittest.TestCase):
    """`ingest_object` não marca o objeto como concluído se algum lote não fechou."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = str(Path(self.temporary_directory.name) / "objeto.duckdb")
        payload = csv_payload(PESQUISAS_HEADERS, [_pesquisa("1", "A")])
        ambiente = mock.patch.dict(
            os.environ,
            {
                "ETL_MINIO_ENDPOINT": "http://minio.invalid:9000",
                "ETL_MINIO_BUCKET": "landing-test",
                "ETL_MINIO_ACCESS_KEY": "teste-sem-segredo",
                "ETL_MINIO_SECRET_KEY": "teste-sem-segredo",
            },
        )
        ambiente.start()
        self.addCleanup(ambiente.stop)
        leitor = mock.patch.object(
            flow_module, "MinioObjectReader", lambda client: MemoryObjectReader(payload)
        )
        leitor.start()
        self.addCleanup(leitor.stop)
        for alvo, valor in (("get_run_logger", mock.MagicMock()), ("_current_task_id", "t")):
            patch = mock.patch.object(flow_module, alvo, return_value=valor)
            patch.start()
            self.addCleanup(patch.stop)

    def test_reconciliacao_desbalanceada_impede_marcar_o_objeto(self) -> None:
        desbalanceada = [
            {
                "source": "pesquisas",
                "run_id": "r",
                "batch_id": "pesquisas-000001",
                "extracted": 1,
                "loaded": 0,
                "rejected": 0,
                "duplicates": 0,
                "balanced": False,
            }
        ]
        with mock.patch.object(flow_module, "load", return_value=desbalanceada):
            with self.assertRaises(flow_module.UnbalancedLoadError):
                flow_module.ingest_object.fn(
                    source="pesquisas",
                    bucket="landing-test",
                    key="landing/pesquisas.csv",
                    db_path=self.database_path,
                )

        with DuckDbLoadRepository(self.database_path) as repo:
            self.assertEqual(
                repo._conn.execute("SELECT count(*) FROM _control_object").fetchall(), [(0,)]
            )


if __name__ == "__main__":
    unittest.main()
