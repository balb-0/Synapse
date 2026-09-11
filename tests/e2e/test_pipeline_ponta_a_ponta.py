"""Teste black-box ponta a ponta do pipeline de ingestão (VB-04).

Percorre as seis fontes na ordem dos relacionamentos, do CSV ao DuckDB:

    fixture (fonte) -> extrator -> transformação/validação -> carga -> DuckDB

Somente o armazenamento de objetos é substituído: o MinIO exigiria Docker e
rede, então os objetos vêm das fixtures sintéticas versionadas por um leitor
em memória que implementa o mesmo contrato ``ObjectReader``. Todos os demais
componentes conversam de verdade, e o DuckDB é um arquivo temporário real.
As conferências finais leem o banco por uma conexão nova, como um consumidor
externo faria: se qualquer etapa quebrar, as contagens e os dados esperados
não se materializam e o teste falha.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction import (  # noqa: E402
    ClientesExtractor,
    EmpresasExtractor,
    ObjectReference,
    PesquisasExtractor,
    QuestoesExtractor,
    RespondentesExtractor,
    RespostasExtractor,
)
from etl.transformation.consistency import RELATIONS, ReferenceData  # noqa: E402
from etl.transformation.pipeline import transform_batch  # noqa: E402
from etl.transformation.schema import KEYS  # noqa: E402
from tests import fixtures  # noqa: E402
from tests.extraction.helpers import MemoryObjectReader  # noqa: E402

DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None
if DUCKDB_INSTALLED:
    import duckdb

    from etl.load.ddl import REJECTED_REASON_TABLE, REJECTED_TABLE, table_name
    from etl.load.duckdb_repository import DuckDbLoadRepository

SEM_DUCKDB = "duckdb não instalado; use pip install -r requirements.txt"

EXTRACTORS = {
    "pesquisas": PesquisasExtractor,
    "empresas": EmpresasExtractor,
    "clientes": ClientesExtractor,
    "questoes": QuestoesExtractor,
    "respondentes": RespondentesExtractor,
    "respostas": RespostasExtractor,
}

BUCKET = "landing-test"


def _referencias(connection, source: str) -> ReferenceData:
    """Monta as referências dos pais a partir do que já foi carregado no DuckDB.

    Lê a view de compatibilidade da carga (todas as colunas de negócio), porque
    as checagens de consistência usam mais do que a chave: o cliente órfão
    precisa de ``empresa_id`` e as respostas precisam do tipo e das listas da
    questão. Listas são persistidas como JSON e precisam voltar a ser listas.
    """
    sources: dict[str, list[dict]] = {}
    for parent, _fields in RELATIONS[source]:
        cursor = connection.execute(f'SELECT * FROM "{parent}"')
        columns = [description[0] for description in cursor.description]
        records = []
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            for key in KEYS[parent]:
                record[key] = str(record[key])
            for name in ("alternativas", "linhas_matriz", "colunas_matriz"):
                if isinstance(record.get(name), str):
                    record[name] = json.loads(record[name])
            records.append(record)
        sources[parent] = records
    return ReferenceData(sources)


def _ingestar(repo: DuckDbLoadRepository, source: str) -> list[dict]:
    """Executa extração -> transformação -> carga de uma fonte e reconcilia."""
    extractor = EXTRACTORS[source](
        object_reader=MemoryObjectReader(fixtures.payload(source)),
        object_reference=ObjectReference(BUCKET, f"landing/{source}.csv"),
    )
    batches = list(extractor.read(run_id=f"e2e-{source}"))
    references = _referencias(repo._conn, source)
    previous = repo.loaded_identities(source)

    reconciliations = []
    offset = 0
    for batch in batches:
        result = transform_batch(
            batch,
            references=references,
            previous=previous,
            source_offset=offset,
            ingested_at=datetime.now(timezone.utc),
        )
        offset += len(batch.records)
        outcome = repo.load_batch(result, batch.metadata)
        reconciliations.append(outcome.as_dict())
    return reconciliations


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class PipelinePontaAPontaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary_directory = tempfile.TemporaryDirectory()
        cls.database_path = Path(cls.temporary_directory.name) / "e2e.duckdb"
        cls.reconciliations = {}
        with DuckDbLoadRepository(cls.database_path) as repo:
            for source in fixtures.ORDEM_CARGA:
                cls.reconciliations[source] = _ingestar(repo, source)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary_directory.cleanup()

    def consulta(self, statement: str, parameters: list | None = None):
        """Consulta o banco por uma conexão nova, como um consumidor externo."""
        with duckdb.connect(str(self.database_path), read_only=True) as connection:
            return connection.execute(statement, parameters or []).fetchall()

    def test_cada_fonte_reconcilia_aceitos_rejeitados_e_duplicados(self) -> None:
        for source, esperado in fixtures.ESPERADO.items():
            with self.subTest(fonte=source):
                extraido = sum(r["extracted"] for r in self.reconciliations[source])
                carregado = sum(r["loaded"] for r in self.reconciliations[source])
                rejeitado = sum(r["rejected"] for r in self.reconciliations[source])
                duplicado = sum(r["duplicates"] for r in self.reconciliations[source])
                self.assertEqual(extraido, esperado["registros"])
                self.assertEqual(carregado, esperado["aceitos"])
                self.assertEqual(rejeitado, esperado["rejeitados"])
                self.assertEqual(duplicado, esperado["duplicados"])
                self.assertTrue(all(r["balanced"] for r in self.reconciliations[source]))

    def test_contagens_finais_no_duckdb(self) -> None:
        for source, esperado in fixtures.ESPERADO.items():
            with self.subTest(fonte=source):
                total = self.consulta(f'SELECT count(*) FROM "{table_name(source)}"')
                self.assertEqual(total, [(esperado["aceitos"],)])

    def test_dados_esperados_materializados(self) -> None:
        rows = self.consulta(
            'SELECT nome_fantasia, part_mercado, estado, pais FROM "ingestao_empresas"'
            " WHERE empresa_id = '101'"
        )
        self.assertEqual(rows, [("Empresa Alfa", 12.5, "SP", "Brasil")])

        questoes = self.consulta(
            'SELECT tipo, alternativas FROM "ingestao_questoes" ORDER BY pergunta_id'
        )
        self.assertEqual(
            questoes,
            [("multipla_escolha", '["A", "B"]'), ("aberta", "[]")],
        )

    def test_duplicados_nao_entram_duas_vezes(self) -> None:
        respostas = self.consulta(
            "SELECT count(*) FROM \"ingestao_respostas\" WHERE resposta_id = '3001'"
        )
        self.assertEqual(respostas, [(1,)])

    def test_rejeicoes_persistidas_com_motivo(self) -> None:
        motivos = self.consulta(
            f'SELECT r.source, rr.code FROM "{REJECTED_TABLE}" r'
            f' JOIN "{REJECTED_REASON_TABLE}" rr USING (rejection_id)'
            " ORDER BY r.source, rr.code"
        )
        self.assertEqual(
            motivos,
            [
                ("clientes", "ORPHAN_REFERENCE"),
                ("pesquisas", "TEMPORAL_ORDER"),
                ("questoes", "UNKNOWN_QUESTION_TYPE"),
                ("respondentes", "TEMPORAL_ORDER"),
                ("respostas", "ANSWER_DOMAIN"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
