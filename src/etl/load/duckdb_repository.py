"""Repositório de carga em DuckDB para os lotes tratados.

Responsabilidades (conforme o ADR 0001):
- validar o schema de destino e carregar apenas registros tecnicamente conformes;
- persistir as rejeições com o motivo;
- reconciliar as contagens (extraído = aceito + rejeitado + duplicado);
- manter as tabelas de controle técnico:
  - ``_control_object``   idempotência por objeto (SHA-256 já concluído);
  - ``_loaded_identity``  identidades já carregadas (o ``previous`` do dedup);
  - ``_checkpoint``       posição de retomada por fonte;
  - ``_batch_metadata``   metadados técnicos de cada lote (sem PII).

O contrato físico das tabelas — nome, tipo, constraints e views de estado
atual — vive em :mod:`etl.load.ddl` e é aplicado por ``_ensure_schema``.

Não decide quando o pipeline executa nem contém regra de transformação.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

from etl.extraction.contracts import BatchMetadata, ExtractionCheckpoint
from etl.load.config import DEFAULT_WRITE_LOCK_TIMEOUT_SECONDS
from etl.load.ddl import (
    BATCH_METADATA_COLUMNS,
    BATCH_METADATA_TABLE,
    CONTROL_COLUMNS_ADDED,
    CONTROL_COLUMNS_RELAXED,
    BATCH_STATUS_FAILED,
    BATCH_STATUS_LOADED,
    BATCH_STATUS_LOADED_WITH_REJECTIONS,
    REJECTED_COLUMNS,
    REJECTED_REASON_COLUMNS,
    REJECTED_REASON_TABLE,
    REJECTED_TABLE,
    quote,
    table_name,
    table_statements,
    view_statements,
)
from etl.transformation.pipeline import TransformationResult
from etl.transformation.quarantine import RejectedRecord
from etl.transformation.schema import destination_columns


@dataclass(frozen=True)
class LoadResult:
    """Reconciliação de um lote carregado."""

    source: str
    run_id: str
    batch_id: str
    extracted: int
    loaded: int
    rejected: int
    duplicates: int

    def is_balanced(self) -> bool:
        return self.extracted == self.loaded + self.rejected + self.duplicates

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "run_id": self.run_id,
            "batch_id": self.batch_id,
            "extracted": self.extracted,
            "loaded": self.loaded,
            "rejected": self.rejected,
            "duplicates": self.duplicates,
            "balanced": self.is_balanced(),
        }


# O DuckDB já recusa uma segunda conexão de escrita ao mesmo arquivo com este
# erro, nomeando o processo concorrente. Só distinguimos essa mensagem de
# outro IOException (ex.: permissão negada) para saber quando vale esperar.
WRITE_LOCK_CONFLICT_MARKER = "Could not set lock"
WRITE_LOCK_POLL_INTERVAL_SECONDS = 0.05


class WriteLockTimeoutError(RuntimeError):
    """Não foi possível abrir o arquivo: outro processo mantinha a escrita."""


def _connect_with_retry(database: str, timeout_seconds: float) -> duckdb.DuckDBPyConnection:
    """Espera o escritor anterior liberar o arquivo em vez de falhar de imediato.

    O DuckDB só permite um processo com o arquivo aberto para escrita por vez.
    Um erro que não seja de lock (arquivo sem permissão, diretório ausente)
    propaga na primeira tentativa: esperar não o resolveria.
    """
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            return duckdb.connect(database)
        except duckdb.IOException as error:
            if WRITE_LOCK_CONFLICT_MARKER not in str(error):
                raise
            if time.monotonic() >= deadline:
                raise WriteLockTimeoutError(
                    f"não foi possível abrir {database} em {timeout_seconds}s: "
                    f"outra carga está em andamento ({error})"
                ) from error
            time.sleep(WRITE_LOCK_POLL_INTERVAL_SECONDS)


class DuckDbLoadRepository:
    """Grava lotes tratados no DuckDB e mantém as tabelas de controle."""

    def __init__(
        self,
        database: str | Path,
        *,
        threads: int | None = None,
        memory_limit: str | None = None,
        write_lock_timeout_seconds: float = DEFAULT_WRITE_LOCK_TIMEOUT_SECONDS,
    ) -> None:
        self._database = str(database)
        self._conn = _connect_with_retry(self._database, write_lock_timeout_seconds)
        self._apply_connection_tuning(threads, memory_limit)
        self._ensure_schema()

    def _apply_connection_tuning(self, threads: int | None, memory_limit: str | None) -> None:
        """Ajusta a conexão só quando configurado; ausente mantém o padrão do DuckDB.

        A gramática de `memory_limit` (ex.: `'2GB'`) é validada pelo próprio
        `SET`, com o erro do banco — reimplementá-la aqui duplicaria a checagem.
        """
        if threads is not None:
            self._conn.execute("SET threads=?", [threads])
        if memory_limit is not None:
            self._conn.execute("SET memory_limit=?", [memory_limit])

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> DuckDbLoadRepository:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # ---------- schema ----------

    def _ensure_schema(self) -> None:
        """Aplica o contrato físico versionado da camada de carga.

        As tabelas vêm primeiro, depois o alinhamento das que já existiam, e só
        então as views — que leem colunas que o alinhamento pode ter acabado de
        acrescentar.
        """
        for statement in table_statements():
            self._conn.execute(statement)
        self._align_control_tables()
        self._keyless_control_tables = self._control_tables_without_key()
        for statement in view_statements():
            self._conn.execute(statement)

    def _align_control_tables(self) -> None:
        """Acrescenta às tabelas de controle o que esta versão passou a exigir.

        Num banco novo é um no-op: as colunas já nascem no `CREATE TABLE`. Num
        banco anterior a esta versão é o que impede a carga de ficar inoperante
        — nem as views de execução seriam criadas sem `status`. O alinhamento
        não refaz chave primária: uma tabela de controle antiga continua sem a
        chave nova, e reconstruí-la é assunto da rotina de migração.
        """
        for table, column, declaration in CONTROL_COLUMNS_ADDED:
            self._conn.execute(
                f"ALTER TABLE {quote(table)} "
                f"ADD COLUMN IF NOT EXISTS {quote(column)} {declaration}"
            )
        for table, column in CONTROL_COLUMNS_RELAXED:
            if column in self._columns(table):
                self._conn.execute(
                    f"ALTER TABLE {quote(table)} ALTER COLUMN {quote(column)} DROP NOT NULL"
                )

    def _control_tables_without_key(self) -> frozenset[str]:
        """Tabelas de controle que nasceram sem chave, antes desta versão.

        ``INSERT OR REPLACE`` precisa de uma chave para saber o que substituir,
        então nessas tabelas o insert tem de ser simples. A consequência é que
        um reprocessamento acrescenta linha de controle em vez de convergir —
        que é o comportamento de uma tabela sem chave. Dar-lhe a chave exige
        reconstruir a tabela, assunto da rotina de migração.
        """
        keyed = {
            row[0]
            for row in self._conn.execute(
                "SELECT DISTINCT table_name FROM duckdb_constraints()"
                " WHERE constraint_type = 'PRIMARY KEY'"
            ).fetchall()
        }
        written = (REJECTED_TABLE, REJECTED_REASON_TABLE, BATCH_METADATA_TABLE)
        return frozenset(table for table in written if table not in keyed)

    def _columns(self, table: str) -> set[str]:
        rows = self._conn.execute(
            "SELECT column_name FROM duckdb_columns() WHERE table_name = ?", [table]
        ).fetchall()
        return {name for (name,) in rows}

    # ---------- idempotência por objeto ----------

    def object_already_loaded(self, source_checksum: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM _control_object WHERE source_checksum = ?", [source_checksum]
        ).fetchone()
        return row is not None

    def mark_object_loaded(self, source: str, source_checksum: str, run_id: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO _control_object VALUES (?, ?, ?, now())",
            [source, source_checksum, run_id],
        )

    # ---------- deduplicação: identidades já carregadas ----------

    def loaded_identities(self, source: str) -> dict[str, str]:
        rows = self._conn.execute(
            "SELECT record_identity, content_checksum FROM _loaded_identity WHERE source = ?",
            [source],
        ).fetchall()
        return {identity: checksum for identity, checksum in rows}

    # ---------- checkpoint (protocolo CheckpointStore) ----------

    def load(self, source: str) -> ExtractionCheckpoint | None:
        row = self._conn.execute(
            "SELECT position, sequence, source_version FROM _checkpoint WHERE source = ?",
            [source],
        ).fetchone()
        if row is None:
            return None
        position, sequence, source_version = row
        return ExtractionCheckpoint(source, position, int(sequence), source_version)

    def commit(self, checkpoint: ExtractionCheckpoint) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO _checkpoint VALUES (?, ?, ?, ?)",
            [checkpoint.source, checkpoint.position, checkpoint.sequence, checkpoint.source_version],
        )

    # ---------- carga do lote ----------

    def load_batch(self, result: TransformationResult, metadata: BatchMetadata) -> LoadResult:
        """Grava aceitos e rejeitados numa transação e reconcilia as contagens.

        ``loaded`` e ``rejected`` vêm de uma contagem no banco (por
        ``run_id``+``batch_id``), não do tamanho das listas em memória: assim a
        reconciliação não fecha só porque as duas pontas nasceram do mesmo lote
        transformado, e sim porque o que está gravado bate com o que se
        pretendia gravar.
        """
        source = metadata.source
        columns = list(destination_columns(source))
        placeholders = ", ".join("?" for _ in columns)
        insert_sql = (
            f"INSERT INTO {quote(table_name(source))} "
            f"({', '.join(quote(c) for c in columns)}) VALUES ({placeholders})"
        )
        rows = [record.as_clickhouse_row() for record in result.accepted]
        self._conn.execute("BEGIN TRANSACTION")
        try:
            if rows:
                self._conn.executemany(
                    insert_sql, [[_cell(row.get(c)) for c in columns] for row in rows]
                )
                self._conn.executemany(
                    "INSERT OR REPLACE INTO _loaded_identity VALUES (?, ?, ?)",
                    [[source, row["record_identity"], row["content_checksum"]] for row in rows],
                )
            self._record_rejections(result.rejected)
            loaded, rejected_count = self._confirmed_counts(metadata)
            self._record_batch(
                metadata,
                status=(
                    BATCH_STATUS_LOADED_WITH_REJECTIONS if result.rejected else BATCH_STATUS_LOADED
                ),
                accepted=loaded,
                rejected=rejected_count,
                duplicated=len(result.duplicates),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            self._record_failed_batch(metadata)
            raise
        return LoadResult(
            source=source,
            run_id=metadata.run_id,
            batch_id=metadata.batch_id,
            extracted=result.metrics["extracted_count"],
            loaded=loaded,
            rejected=rejected_count,
            duplicates=len(result.duplicates),
        )

    def _confirmed_counts(self, metadata: BatchMetadata) -> tuple[int, int]:
        """Conta o que o banco tem para este lote, não o que ficou em memória.

        Roda ainda dentro da transação aberta pelo ``load_batch``: o que se lê
        aqui é exatamente o que o ``COMMIT`` seguinte torna durável, ou some
        junto no rollback se a transação falhar depois — nunca diverge do que
        de fato persiste.
        """
        run_id, batch_id = metadata.run_id, metadata.batch_id
        loaded = self._conn.execute(
            f"SELECT count(*) FROM {quote(table_name(metadata.source))}"
            " WHERE run_id = ? AND batch_id = ?",
            [run_id, batch_id],
        ).fetchone()[0]
        rejected = self._conn.execute(
            f"SELECT count(*) FROM {quote(REJECTED_TABLE)} WHERE run_id = ? AND batch_id = ?",
            [run_id, batch_id],
        ).fetchone()[0]
        return int(loaded), int(rejected)

    # ---------- registro de rejeição ----------

    def _record_rejections(self, rejected: tuple[RejectedRecord, ...]) -> None:
        """Grava as ocorrências rejeitadas e os motivos do lote inteiro em duas escritas em lote.

        Duas ``executemany`` para o lote inteiro, não uma por ocorrência: é o
        que torna a escrita "em lotes parametrizados" de fato, em vez de N
        comandos avulsos. A rejeição converge em vez de falhar por chave
        repetida quando um backfill reprocessa o lote. Lote sem rejeição chega
        com listas vazias; ``_insert_many`` não emite comando nesse caso.
        """
        self._insert_many(
            "rejected",
            REJECTED_COLUMNS,
            [
                {
                    "rejection_id": record.rejection_id,
                    "source": record.source,
                    "source_checksum": record.source_checksum,
                    "source_offset": record.source_offset,
                    "run_id": record.run_id,
                    "batch_id": record.batch_id,
                    "ingested_at": record.ingested_at,
                }
                for record in rejected
            ],
        )
        self._insert_many(
            "rejected_reason",
            REJECTED_REASON_COLUMNS,
            [
                {"rejection_id": record.rejection_id, "code": violation.code, "field": violation.field}
                for record in rejected
                for violation in record.violations
            ],
        )

    # ---------- registro de execução (por lote) ----------

    def _record_batch(
        self,
        metadata: BatchMetadata,
        *,
        status: str,
        accepted: int,
        rejected: int,
        duplicated: int,
    ) -> None:
        """Grava o lote da execução com o status e as três contagens."""
        values = {
            "source": metadata.source,
            "run_id": metadata.run_id,
            "task_id": metadata.task_id,
            "batch_id": metadata.batch_id,
            "status": status,
            "record_count": metadata.record_count,
            "accepted_count": accepted,
            "rejected_count": rejected,
            "duplicated_count": duplicated,
            "byte_count": metadata.byte_count,
            "schema_version": metadata.schema_version,
            "source_checksum": metadata.source_checksum,
            "started_at": metadata.started_at,
            "finished_at": metadata.finished_at,
        }
        self._insert("_batch_metadata", BATCH_METADATA_COLUMNS, values)

    def _record_failed_batch(self, metadata: BatchMetadata) -> None:
        """Registra o lote perdido, já fora da transação revertida.

        Sem isto o lote revertido desapareceria do histórico e a reconciliação
        fecharia a conta sem notar a perda. As contagens são zero porque nada
        do lote sobreviveu ao rollback: a diferença contra ``record_count`` é o
        que denuncia a perda em ``reconciliacao_execucao``.
        """
        try:
            self._record_batch(
                metadata, status=BATCH_STATUS_FAILED, accepted=0, rejected=0, duplicated=0
            )
        except Exception:
            # Descartado de propósito: propagar daqui, de dentro do `except` da
            # carga, faria o erro de anotar o histórico virar o erro principal
            # e esconder a causa da perda. Perde-se o motivo da anotação ter
            # falhado; preserva-se o motivo do lote ter falhado, que é o que
            # permite agir. O `status` do lote fica ausente, e a execução
            # aparece como não conciliada pela diferença de contagem.
            pass

    def _insert(self, table: str, columns: tuple[str, ...], values: dict[str, Any]) -> None:
        """Insere uma linha por nome de coluna; ver :meth:`_insert_many`."""
        self._insert_many(table, columns, [values])

    def _insert_many(
        self, table: str, columns: tuple[str, ...], rows: list[dict[str, Any]]
    ) -> None:
        """Insere o lote inteiro num só ``executemany``, por nome de coluna.

        Nomear as colunas troca "valor deslocado em silêncio" por erro de
        coluna ausente quando o contrato ganha campo. ``INSERT OR REPLACE``
        porque um reprocessamento reapresenta a mesma linha de controle — o que
        só é possível onde existe chave para substituir.
        """
        if not rows:
            return
        verb = "INSERT INTO" if table in self._keyless_control_tables else "INSERT OR REPLACE INTO"
        names = ", ".join(quote(column) for column in columns)
        placeholders = ", ".join("?" for _ in columns)
        self._conn.executemany(
            f"{verb} {quote(table)} ({names}) VALUES ({placeholders})",
            [[row[column] for column in columns] for row in rows],
        )

    def count(self, source: str) -> int:
        return int(
            self._conn.execute(
                f"SELECT count(*) FROM {quote(table_name(source))}"
            ).fetchone()[0]
        )


def _cell(value: Any) -> Any:
    """Converte valores para o que o driver aceita (listas viram JSON)."""
    if isinstance(value, (list, tuple)):
        return json.dumps(list(value), ensure_ascii=False)
    return value
