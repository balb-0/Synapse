"""Tabelas de execução, rejeição e reconciliação da camada de carga.

Cobre o que o contrato físico das tabelas de ingestão deixou de fora: onde a
carga registra status, contagens e motivos, e como a reconciliação por execução
é derivada do que foi efetivamente gravado.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction.contracts import (  # noqa: E402
    BatchMetadata,
    ExtractedBatch,
    ExtractionCheckpoint,
)
from etl.load.ddl import (  # noqa: E402
    BATCH_METADATA_COLUMNS,
    BATCH_METADATA_TABLE,
    BATCH_STATUS_FAILED,
    BATCH_STATUS_LOADED,
    BATCH_STATUS_LOADED_WITH_REJECTIONS,
    EXECUTION_VIEW,
    RECONCILIATION_VIEW,
    REJECTED_COLUMNS,
    REJECTED_REASON_COLUMNS,
    REJECTED_REASON_TABLE,
    REJECTED_TABLE,
    render_ddl,
    statements,
)
from etl.transformation.consistency import ReferenceData  # noqa: E402
from etl.transformation.normalization import normalize_record  # noqa: E402
from etl.transformation.pipeline import (  # noqa: E402
    TransformationResult,
    transform_batch,
)

DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None
if DUCKDB_INSTALLED:
    import duckdb

    from etl.load.duckdb_repository import DuckDbLoadRepository, LoadResult, UnbalancedLoadError

SEM_DUCKDB = "duckdb não instalado; use pip install -r requirements.txt"
RENDER_SCRIPT = REPOSITORY_ROOT / "scripts/load/render_ddl.py"


class ControlContractTests(unittest.TestCase):
    """O contrato declara as estruturas sem depender de um banco aberto."""

    def test_rejection_is_keyed_by_the_occurrence_and_the_batch(self) -> None:
        # `rejection_id` não carrega a execução: sozinho, ele faria a rejeição
        # de uma execução antiga ser sobrescrita pela nova.
        rejected = _statement_for(REJECTED_TABLE)

        self.assertIn("PRIMARY KEY (rejection_id, run_id, batch_id)", rejected)

    def test_reasons_have_their_own_table_keyed_by_code_and_field(self) -> None:
        reason = _statement_for(REJECTED_REASON_TABLE)

        self.assertIn("PRIMARY KEY (rejection_id, code, field)", reason)

    def test_opaque_reason_json_is_gone_from_the_rejection_table(self) -> None:
        # O motivo passa a ser consultável: contagem por código deixa de exigir
        # que o leitor saiba interpretar um JSON.
        self.assertNotIn("reasons", _statement_for(REJECTED_TABLE))

    def test_batch_carries_status_and_the_three_counts(self) -> None:
        batch = _statement_for(BATCH_METADATA_TABLE)

        for column in ("status", "accepted_count", "rejected_count", "duplicated_count"):
            with self.subTest(column=column):
                self.assertIn(f"    {column} ", batch)

    def test_batch_is_keyed_by_execution_and_batch(self) -> None:
        # `batch_id` é sequencial por fonte (`pesquisas-000001`) e repete em
        # toda execução: sozinho, ele faria uma execução sobrescrever a
        # anterior. A identidade do lote é o par com a execução.
        self.assertIn("PRIMARY KEY (run_id, batch_id)", _statement_for(BATCH_METADATA_TABLE))

    def test_column_tuples_match_the_ddl_they_describe(self) -> None:
        # As tuplas guiam o insert nomeado e são mantidas à mão ao lado do DDL.
        # Sem esta checagem, acrescentar coluna só num dos dois lugares passaria.
        for table, columns in (
            (REJECTED_TABLE, REJECTED_COLUMNS),
            (REJECTED_REASON_TABLE, REJECTED_REASON_COLUMNS),
            (BATCH_METADATA_TABLE, BATCH_METADATA_COLUMNS),
        ):
            with self.subTest(table=table):
                self.assertEqual(_declared_columns(table), list(columns))

    def test_execution_and_reconciliation_are_views(self) -> None:
        rendered = "\n".join(statements())

        self.assertIn(f'CREATE OR REPLACE VIEW "{EXECUTION_VIEW}" AS', rendered)
        self.assertIn(f'CREATE OR REPLACE VIEW "{RECONCILIATION_VIEW}" AS', rendered)

    def test_rejection_stays_physically_apart_from_the_accepted_rows(self) -> None:
        # Rejeitado é gravado à parte do aceito: nenhuma tabela de ingestão
        # carrega motivo de rejeição.
        for statement in statements():
            if statement.startswith('CREATE TABLE IF NOT EXISTS "ingestao_'):
                with self.subTest(statement=statement.splitlines()[0]):
                    self.assertNotIn('"code"', statement)
                    self.assertNotIn('"rejection_id"', statement)

    def test_versioned_file_matches_the_contract(self) -> None:
        path = REPOSITORY_ROOT / "sql/duckdb/001_ingestao_tratada.sql"

        self.assertEqual(path.read_text(encoding="utf-8"), render_ddl())

    def test_check_command_accepts_the_versioned_file(self) -> None:
        result = subprocess.run(
            [sys.executable, str(RENDER_SCRIPT), "--check"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


NOW = datetime(2026, 9, 10, 12, tzinfo=timezone.utc)

RAW = {
    "pesquisas": {"id": "1", "titulo": "Pesquisa fictícia"},
    "empresas": {"ID": "1", "Nome Fantasia": "Empresa fictícia", "Associado": "Sim"},
}


def _metadata(
    record_count: int, run_id: str = "run-1", batch_id: str = "pesquisas-000001"
) -> BatchMetadata:
    return BatchMetadata(
        "pesquisas",
        run_id,
        "task",
        batch_id,
        NOW,
        NOW + timedelta(seconds=5),
        record_count,
        100,
        "1.0",
        "a" * 64,
    )


def _transform(
    rows: list[dict],
    metadata: BatchMetadata | None = None,
    previous: dict[str, str] | None = None,
) -> TransformationResult:
    """Transforma o lote com o mesmo metadado com que ele será carregado.

    A rejeição carrega a execução em que foi vista, então transformar com um
    metadado e carregar com outro produziria histórico incoerente.
    """
    references = ReferenceData(
        {source: [normalize_record(source, RAW[source])[0]] for source in RAW}
    )
    batch = ExtractedBatch(
        rows,
        ExtractionCheckpoint("pesquisas", "cursor", 0),
        metadata or _metadata(len(rows)),
    )
    return transform_batch(
        batch,
        references=references,
        previous=previous or {},
        source_offset=0,
        ingested_at=NOW,
    )


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class LoadRepositoryTestCase(unittest.TestCase):
    """Banco temporário próprio por teste, com a carga já aberta nele."""

    database_name = "ingestao.duckdb"

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / self.database_name
        self.repository = DuckDbLoadRepository(self.database_path)
        self.addCleanup(self.repository.close)

    def _rows(self, sql: str) -> list[tuple]:
        return self.repository._conn.execute(sql).fetchall()

    def _load(self, rows: list[dict], metadata: BatchMetadata | None = None) -> LoadResult:
        metadata = metadata or _metadata(len(rows))
        return self.repository.load_batch(_transform(rows, metadata), metadata)


class ControlTablesWrittenByTheLoadTests(LoadRepositoryTestCase):
    """O que a carga grava de verdade num DuckDB aberto."""

    def test_batch_row_carries_the_status_and_the_three_counts(self) -> None:
        # Uma linha válida, uma rejeitada (sem `id`) e uma repetição da primeira.
        self._load([RAW["pesquisas"], {"titulo": "sem id"}, RAW["pesquisas"]])

        rows = self._rows(
            "SELECT status, record_count, accepted_count, rejected_count, duplicated_count"
            " FROM _batch_metadata"
        )

        self.assertEqual(rows, [(BATCH_STATUS_LOADED_WITH_REJECTIONS, 3, 1, 1, 1)])

    def test_batch_without_rejection_is_simply_loaded(self) -> None:
        self._load([RAW["pesquisas"]])

        self.assertEqual(self._rows("SELECT status FROM _batch_metadata"), [(BATCH_STATUS_LOADED,)])

    def test_each_reason_becomes_a_queryable_row(self) -> None:
        self._load([{"titulo": "sem id"}])

        reasons = self._rows("SELECT code, field FROM rejected_reason ORDER BY code, field")

        self.assertEqual(self._rows("SELECT count(*) FROM rejected"), [(1,)])
        self.assertEqual(reasons, [("REQUIRED", "pesquisa_id")])

    def test_reason_rows_point_at_their_rejection(self) -> None:
        self._load([{"titulo": "sem id"}])

        orphans = self._rows(
            "SELECT count(*) FROM rejected_reason r"
            " WHERE NOT EXISTS (SELECT 1 FROM rejected j WHERE j.rejection_id = r.rejection_id)"
        )

        self.assertEqual(orphans, [(0,)])

    def test_counting_rejections_by_code_needs_no_json(self) -> None:
        self._load([{"titulo": "a"}, {"titulo": "b"}])

        by_code = self._rows(
            "SELECT code, count(*) FROM rejected_reason GROUP BY code ORDER BY code"
        )

        self.assertEqual(by_code, [("REQUIRED", 2)])

    def test_reloading_the_same_batch_does_not_violate_the_keys(self) -> None:
        # Um `run_backfill --reprocess` reapresenta a mesma execução e o mesmo
        # lote: a segunda passagem converge em vez de derrubar a carga.
        rows = [{"titulo": "sem id"}]
        self._load(rows)
        self._load(rows)

        self.assertEqual(self._rows("SELECT count(*) FROM rejected"), [(1,)])
        self.assertEqual(self._rows("SELECT count(*) FROM rejected_reason"), [(1,)])
        self.assertEqual(self._rows("SELECT count(*) FROM _batch_metadata"), [(1,)])

    def test_a_second_execution_does_not_overwrite_the_first(self) -> None:
        # `batch_id` repete entre execuções e a mesma linha da fonte volta a
        # ser rejeitada: as duas execuções têm que sobreviver no histórico.
        rejected_row = [{"titulo": "sem id"}]
        self._load(rejected_row, _metadata(1, run_id="run-1"))
        self._load(rejected_row, _metadata(1, run_id="run-2"))

        self.assertEqual(
            self._rows("SELECT run_id FROM _batch_metadata ORDER BY run_id"),
            [("run-1",), ("run-2",)],
        )
        self.assertEqual(
            self._rows("SELECT run_id FROM rejected ORDER BY run_id"),
            [("run-1",), ("run-2",)],
        )

    def test_rejections_of_an_execution_match_its_counted_total(self) -> None:
        # A listagem e a contagem são gravadas por caminhos diferentes; que as
        # duas fechem é o que faz a reconciliação ser verificável.
        self._load([{"titulo": "a"}, {"titulo": "b"}], _metadata(2, run_id="run-1"))

        self.assertEqual(
            self._rows(
                "SELECT (SELECT sum(rejected_count) FROM _batch_metadata WHERE run_id = 'run-1'),"
                " (SELECT count(*) FROM rejected WHERE run_id = 'run-1')"
            ),
            [(2, 2)],
        )

    def test_execution_view_aggregates_the_batches(self) -> None:
        self._load([RAW["pesquisas"], {"titulo": "sem id"}], _metadata(2, batch_id="b-1"))
        self._load([{"titulo": "sem id"}], _metadata(1, batch_id="b-2"))

        rows = self._rows(
            f"SELECT run_id, fontes, status, lotes, extraidos, carregados, rejeitados"
            f" FROM {EXECUTION_VIEW}"
        )

        self.assertEqual(
            rows, [("run-1", "pesquisas", BATCH_STATUS_LOADED_WITH_REJECTIONS, 2, 3, 1, 2)]
        )

    def test_reconciliation_balances_when_nothing_is_lost(self) -> None:
        self._load([RAW["pesquisas"], {"titulo": "sem id"}, RAW["pesquisas"]])

        rows = self._rows(
            f"SELECT extraidos, contabilizados, diferenca, conciliado FROM {RECONCILIATION_VIEW}"
        )

        self.assertEqual(rows, [(3, 3, 0, True)])

    def test_reconciliation_compares_the_count_against_the_rejections_recorded(self) -> None:
        # A contagem do lote e a listagem de rejeições são gravadas por
        # caminhos diferentes. Se as duas discordarem, a execução não pode
        # aparecer como conciliada — é essa comparação que a torna verificável.
        self._load([RAW["pesquisas"], {"titulo": "sem id"}])
        self.repository._conn.execute("DELETE FROM rejected")

        self.assertEqual(
            self._rows(
                f"SELECT rejeitados, rejeitados_registrados, conciliado FROM {RECONCILIATION_VIEW}"
            ),
            [(1, 0, False)],
        )


class ConfirmedCountsComeFromTheDatabaseTests(LoadRepositoryTestCase):
    """`_confirmed_counts` vem de um SELECT no banco, não de `len()` em memória.

    Testado direto no método privado, não mais via `load_batch`: a
    reconciliação agora bloqueia qualquer lote cujas contas não fechem
    (``UnbalancedLoadError``, ver ``UnbalancedBatchIsNotConfirmedTests``), e
    uma linha órfã sob o mesmo run_id/batch_id sempre desbalanceia o lote —
    esse é exatamente o tipo de anomalia que o bloqueio existe para pegar, não
    algo que `load_batch` deveria mais engolir em silêncio.
    """

    def test_loaded_count_includes_a_row_the_batch_itself_did_not_insert(self) -> None:
        metadata = _metadata(1)
        self.repository._conn.execute(
            "INSERT INTO ingestao_pesquisas "
            "(pesquisa_id, source, run_id, task_id, batch_id, source_offset,"
            " content_checksum, record_identity, idempotency_key, ingested_at, schema_version)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                "linha-fora-do-lote",
                "pesquisas",
                metadata.run_id,
                metadata.task_id,
                metadata.batch_id,
                999,
                "b" * 64,
                "c" * 64,
                "d" * 64,
                NOW,
                "1.0",
            ],
        )

        loaded, _rejected = self.repository._confirmed_counts(metadata)

        self.assertEqual(loaded, 1)

    def test_rejected_count_includes_a_row_the_batch_itself_did_not_insert(self) -> None:
        metadata = _metadata(1)
        self.repository._conn.execute(
            "INSERT INTO rejected (rejection_id, source, source_offset, run_id, batch_id, ingested_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            ["e" * 64, "pesquisas", 999, metadata.run_id, metadata.batch_id, NOW],
        )

        _loaded, rejected = self.repository._confirmed_counts(metadata)

        self.assertEqual(rejected, 1)


class FailedBatchIsStillRecordedTests(LoadRepositoryTestCase):
    """Lote revertido não pode desaparecer do histórico da execução."""

    def setUp(self) -> None:
        super().setUp()
        self.result = _transform([RAW["pesquisas"], RAW["pesquisas"]])
        # Derruba a carga no meio: a tabela de ingestão deixa de aceitar linha.
        self.repository._conn.execute('DROP VIEW "pesquisas"')
        self.repository._conn.execute('DROP VIEW "ingestao_pesquisas_atual"')
        self.repository._conn.execute('DROP TABLE "ingestao_pesquisas"')

    def _fail(self, metadata: BatchMetadata | None = None) -> None:
        with self.assertRaises(duckdb.Error):
            self.repository.load_batch(self.result, metadata or _metadata(2))

    def test_failure_is_recorded_after_the_rollback(self) -> None:
        self._fail()

        self.assertEqual(
            self._rows(
                "SELECT status, record_count, accepted_count, rejected_count, duplicated_count"
                " FROM _batch_metadata"
            ),
            [(BATCH_STATUS_FAILED, 2, 0, 0, 0)],
        )

    def test_original_error_still_reaches_the_caller(self) -> None:
        # O erro que chega é o do banco, não um erro vindo do registro da
        # falha: anotar o histórico não pode mascarar a causa da perda.
        with self.assertRaises(duckdb.Error) as context:
            self.repository.load_batch(self.result, _metadata(2))

        self.assertIn("ingestao_pesquisas", str(context.exception))

    def test_reconciliation_shows_the_gap_left_by_the_failure(self) -> None:
        self._fail()

        self.assertEqual(
            self._rows(
                f"SELECT extraidos, contabilizados, diferenca, conciliado"
                f" FROM {RECONCILIATION_VIEW}"
            ),
            [(2, 0, 2, False)],
        )

    def test_execution_with_one_failed_batch_is_a_failed_execution(self) -> None:
        self._fail()

        self.assertEqual(
            self._rows(f"SELECT status FROM {EXECUTION_VIEW}"), [(BATCH_STATUS_FAILED,)]
        )

    def test_failing_to_record_the_failure_does_not_hide_the_load_error(self) -> None:
        # Pior caso: nem o histórico pode ser gravado. O chamador continua
        # recebendo o erro da carga, não o erro de anotar o histórico.
        self.repository._conn.execute('DROP TABLE "_batch_metadata"')

        with self.assertRaises(duckdb.Error) as context:
            self.repository.load_batch(self.result, _metadata(2))

        self.assertIn("ingestao_pesquisas", str(context.exception))


class UnbalancedBatchIsNotConfirmedTests(LoadRepositoryTestCase):
    """A reconciliação bloqueia a confirmação quando as contas não fecham.

    Cenário real (o mesmo do feedback da sprint passada): a mesma ocorrência
    aparece em dois lotes do mesmo objeto. `previous` só é carregado uma vez
    no início do flow — o segundo lote não sabe que o primeiro acabou de
    carregar aquela identidade, `transform_batch` classifica como aceito, e o
    `INSERT ... ON CONFLICT DO NOTHING` converge sem gravar nada. Sem o
    bloqueio, isso commitava como sucesso com extraído=1, carregado=0,
    rejeitado=0, duplicado=0 e `balanced=False`.
    """

    def test_a_row_identical_to_one_loaded_by_an_earlier_batch_blocks_the_commit(self) -> None:
        self._load([RAW["pesquisas"]], _metadata(1, batch_id="pesquisas-000001"))

        with self.assertRaises(UnbalancedLoadError):
            self._load([RAW["pesquisas"]], _metadata(1, batch_id="pesquisas-000002"))

    def test_the_earlier_batch_row_survives_the_blocked_one(self) -> None:
        self._load([RAW["pesquisas"]], _metadata(1, batch_id="pesquisas-000001"))

        with self.assertRaises(UnbalancedLoadError):
            self._load([RAW["pesquisas"]], _metadata(1, batch_id="pesquisas-000002"))

        self.assertEqual(self._rows("SELECT count(*) FROM ingestao_pesquisas"), [(1,)])

    def test_the_blocked_batch_is_recorded_as_failed_not_silently_dropped(self) -> None:
        self._load([RAW["pesquisas"]], _metadata(1, batch_id="pesquisas-000001"))

        with self.assertRaises(UnbalancedLoadError):
            self._load([RAW["pesquisas"]], _metadata(1, batch_id="pesquisas-000002"))

        self.assertEqual(
            self._rows("SELECT status FROM _batch_metadata WHERE batch_id = 'pesquisas-000002'"),
            [(BATCH_STATUS_FAILED,)],
        )

    def test_a_batch_that_balances_still_commits_normally(self) -> None:
        # Guarda-costas: o bloqueio não pode virar falso positivo numa carga
        # comum, sem duplicata entre lotes.
        outcome = self._load([RAW["pesquisas"]], _metadata(1, batch_id="pesquisas-000001"))

        self.assertTrue(outcome.is_balanced())


def _statement_for(table: str) -> str:
    return next(
        statement for statement in statements() if f'"{table}"' in statement.splitlines()[0]
    )


def _declared_columns(table: str) -> list[str]:
    """Colunas declaradas no `CREATE TABLE`, na ordem em que aparecem."""

    lines = _statement_for(table).splitlines()[1:-1]
    return [
        line.strip().split()[0]
        for line in lines
        if not line.strip().startswith(("PRIMARY KEY", "UNIQUE"))
    ]


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class DatabaseCreatedBeforeTheControlColumnsTests(unittest.TestCase):
    """Banco criado antes de status e contagens existirem continua abrindo.

    `CREATE TABLE IF NOT EXISTS` cria o que falta e não altera o que existe:
    sem um passo de alinhamento, a tabela de controle antiga sobreviveria sem
    `status` e as views de execução não conseguiriam nem ser criadas.
    """

    # Forma que as tabelas de controle tinham antes desta versão.
    LEGACY = (
        'CREATE TABLE "rejected" ('
        " source VARCHAR NOT NULL, source_checksum VARCHAR,"
        " source_offset UBIGINT NOT NULL, run_id VARCHAR NOT NULL,"
        " batch_id VARCHAR NOT NULL, ingested_at TIMESTAMP NOT NULL,"
        " reasons VARCHAR NOT NULL)",
        'CREATE TABLE "_batch_metadata" ('
        " source VARCHAR NOT NULL, run_id VARCHAR NOT NULL, task_id VARCHAR NOT NULL,"
        " batch_id VARCHAR NOT NULL, record_count BIGINT NOT NULL,"
        " byte_count BIGINT NOT NULL, schema_version VARCHAR NOT NULL,"
        " source_checksum VARCHAR, started_at TIMESTAMP NOT NULL,"
        " finished_at TIMESTAMP NOT NULL)",
    )

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "legado.duckdb"
        connection = duckdb.connect(str(self.database_path))
        for statement in self.LEGACY:
            connection.execute(statement)
        connection.close()

    def test_opening_it_does_not_fail(self) -> None:
        with DuckDbLoadRepository(self.database_path) as repository:
            columns = {
                row[0]
                for row in repository._conn.execute(
                    "SELECT column_name FROM duckdb_columns() WHERE table_name = '_batch_metadata'"
                ).fetchall()
            }

        self.assertLessEqual(
            {"status", "accepted_count", "rejected_count", "duplicated_count"}, columns
        )

    def test_the_execution_views_exist_after_opening_it(self) -> None:
        with DuckDbLoadRepository(self.database_path) as repository:
            views = {
                row[0]
                for row in repository._conn.execute(
                    "SELECT view_name FROM duckdb_views() WHERE NOT internal"
                ).fetchall()
            }

        self.assertIn(EXECUTION_VIEW, views)
        self.assertIn(RECONCILIATION_VIEW, views)

    def test_it_still_accepts_a_load(self) -> None:
        # A rejeição antiga exigia `reasons`, que a carga não preenche mais.
        rows = [RAW["pesquisas"], {"titulo": "sem id"}]
        metadata = _metadata(2)

        with DuckDbLoadRepository(self.database_path) as repository:
            repository.load_batch(_transform(rows, metadata), metadata)
            recorded = repository._conn.execute(
                f"SELECT status, extraidos, rejeitados FROM {EXECUTION_VIEW}"
            ).fetchall()

        self.assertEqual(recorded, [(BATCH_STATUS_LOADED_WITH_REJECTIONS, 2, 1)])


if __name__ == "__main__":
    unittest.main()
