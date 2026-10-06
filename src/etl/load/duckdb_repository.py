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
from etl.load.connection import WriteLockTimeoutError as WriteLockTimeoutError
from etl.load.connection import connect_with_retry
from etl.load.ddl import (
    BATCH_METADATA_COLUMNS,
    BATCH_METADATA_TABLE,
    BATCH_STATUS_FAILED,
    BATCH_STATUS_LOADED,
    BATCH_STATUS_LOADED_WITH_REJECTIONS,
    CONTROL_COLUMNS_ADDED,
    CONTROL_COLUMNS_RELAXED,
    IDENTITY_COLUMN,
    REJECTED_COLUMNS,
    REJECTED_REASON_COLUMNS,
    REJECTED_REASON_TABLE,
    REJECTED_TABLE,
    quote,
    table_name,
    table_statements,
    view_statements,
)
from etl.load.log_events import LoadBatchLogEvent, LoadLogSink, StandardLoggingSink
from etl.transformation.pipeline import AcceptedRecord, TransformationResult
from etl.transformation.quarantine import RejectedRecord
from etl.transformation.schema import destination_columns
from etl.transformation.validation import Violation


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


class UnbalancedLoadError(RuntimeError):
    """A reconciliação do lote não fechou: extraído != carregado+rejeitado+duplicado.

    É a última barreira antes do ``COMMIT``: a transação é desfeita, o lote é
    registrado como falho e o checkpoint não avança. As causas conhecidas de
    desbalanceamento (a mesma identidade em dois lotes do objeto e identidade
    gravada entre o retrato inicial e a carga) já são classificadas antes —
    por ``transform_object`` e por ``_reconcile_with_persisted`` —, então este
    erro sinaliza uma divergência nova, que deve parar a carga, e não uma
    condição a ser repetida.
    """


def _connect_with_retry(database: str, timeout_seconds: float) -> duckdb.DuckDBPyConnection:
    """Compatibility entry point; all callers share the public finite retry policy."""
    return connect_with_retry(database, timeout_seconds)


class DuckDbLoadRepository:
    """Grava lotes tratados no DuckDB e mantém as tabelas de controle."""

    def __init__(
        self,
        database: str | Path,
        *,
        threads: int | None = None,
        memory_limit: str | None = None,
        write_lock_timeout_seconds: float = DEFAULT_WRITE_LOCK_TIMEOUT_SECONDS,
        log_sink: LoadLogSink | None = None,
    ) -> None:
        self._database = str(database)
        self._conn = _connect_with_retry(self._database, write_lock_timeout_seconds)
        self._log_sink = log_sink or StandardLoggingSink()
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
                f"ALTER TABLE {quote(table)} ADD COLUMN IF NOT EXISTS {quote(column)} {declaration}"
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
            [
                checkpoint.source,
                checkpoint.position,
                checkpoint.sequence,
                checkpoint.source_version,
            ],
        )

    # ---------- carga do lote ----------

    def load_batch(self, result: TransformationResult, metadata: BatchMetadata) -> LoadResult:
        """Grava aceitos e rejeitados numa transação e reconcilia as contagens.

        ``loaded`` e ``rejected`` vêm de uma contagem no banco (por
        ``run_id``+``batch_id``), não do tamanho das listas em memória: assim a
        reconciliação não fecha só porque as duas pontas nasceram do mesmo lote
        transformado, e sim porque o que está gravado bate com o que se
        pretendia gravar.

        Reexecutar o mesmo lote (mesmo ``run_id``/``batch_id``) não pode violar
        a chave primária: ``ON CONFLICT ... DO NOTHING`` faz o insert convergir
        em vez de falhar. Não é ``INSERT OR REPLACE`` — a tabela tem PK e
        UNIQUE separados, e o DuckDB recusa resolver os dois sem um alvo de
        conflito explícito. Ver ADR 0003.

        Ao final, publica um log técnico do lote no mesmo formato que a
        extração já usa (ADR 0001): um evento, sem os registros. A duração
        cobre a transação inteira, não só o insert principal.
        """
        started = time.monotonic()
        source = metadata.source
        columns = list(destination_columns(source))
        placeholders = ", ".join("?" for _ in columns)
        insert_sql = (
            f"INSERT INTO {quote(table_name(source))} "
            f"({', '.join(quote(c) for c in columns)}) VALUES ({placeholders}) "
            f"ON CONFLICT ({quote(IDENTITY_COLUMN)}) DO NOTHING"
        )
        self._conn.execute("BEGIN TRANSACTION")
        try:
            accepted, duplicates, conflicts = self._reconcile_with_persisted(result, metadata)
            rows = [record.as_duckdb_row() for record in accepted]
            if rows:
                self._conn.executemany(
                    insert_sql, [[_cell(row.get(c)) for c in columns] for row in rows]
                )
                self._conn.executemany(
                    "INSERT OR REPLACE INTO _loaded_identity VALUES (?, ?, ?)",
                    [[source, row["record_identity"], row["content_checksum"]] for row in rows],
                )
            self._converge_previous_rejections(metadata)
            rejections = (*result.rejected, *conflicts)
            self._record_rejections(rejections)
            loaded, rejected_count = self._confirmed_counts(metadata)
            duplicated = len(duplicates)
            extracted = result.metrics["extracted_count"]
            if extracted != loaded + rejected_count + duplicated:
                raise UnbalancedLoadError(
                    f"lote {metadata.batch_id!r} da fonte {source!r} (run_id="
                    f"{metadata.run_id!r}) não reconciliou: extraído={extracted} "
                    f"carregado={loaded} rejeitado={rejected_count} "
                    f"duplicado={duplicated}"
                )
            status = BATCH_STATUS_LOADED_WITH_REJECTIONS if rejections else BATCH_STATUS_LOADED
            self._record_batch(
                metadata,
                status=status,
                accepted=loaded,
                rejected=rejected_count,
                duplicated=duplicated,
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            self._record_failed_batch(metadata)
            self._log_failed_batch(result, metadata, started)
            raise
        outcome = LoadResult(
            source=source,
            run_id=metadata.run_id,
            batch_id=metadata.batch_id,
            extracted=result.metrics["extracted_count"],
            loaded=loaded,
            rejected=rejected_count,
            duplicates=duplicated,
        )
        duration_ms = round((time.monotonic() - started) * 1000, 3)
        self._emit_log(
            LoadBatchLogEvent.from_result(outcome, metadata, status=status, duration_ms=duration_ms)
        )
        return outcome

    def _reconcile_with_persisted(
        self, result: TransformationResult, metadata: BatchMetadata
    ) -> tuple[list[AcceptedRecord], list[dict], list[RejectedRecord]]:
        """Confere a decisão de identidade da transformação com o estado persistido.

        A transformação classifica contra o retrato de ``_loaded_identity``
        lido no início do flow. Entre esse retrato e a carga, outra execução
        (ou um lote anterior confirmado numa tentativa interrompida) pode ter
        gravado a mesma identidade. Roda dentro da transação do lote e
        reclassifica cada aceito:

        - mesma ``idempotency_key`` já gravada por este ``run_id``+``batch_id``
          — reexecução convergente do próprio lote (ADR 0003): continua
          aceito e é contado pela contagem no banco;
        - identidade já persistida com o mesmo conteúdo — duplicata;
        - identidade já persistida com outro conteúdo — ``IDENTITY_CONFLICT``;
        - identidade ausente — inserida.

        Uma duplicata da transformação cuja chave este mesmo lote já gravou
        numa tentativa anterior (commit feito, checkpoint não) passa a contar
        como carregada, não duplicada: a contagem no banco já a inclui, e
        contá-la duas vezes desbalancearia a reconciliação para sempre.
        """
        candidates = [record.metadata for record in result.accepted] + list(result.duplicates)
        if not candidates:
            return list(result.accepted), list(result.duplicates), []
        identities = sorted({item["record_identity"] for item in candidates})
        keys = sorted({item["idempotency_key"] for item in candidates})
        persisted = dict(
            self._conn.execute(
                "SELECT record_identity, content_checksum FROM _loaded_identity "
                "WHERE source = ? AND list_contains(?, record_identity)",
                [metadata.source, identities],
            ).fetchall()
        )
        same_batch = {
            row[0]
            for row in self._conn.execute(
                f"SELECT {quote(IDENTITY_COLUMN)} FROM {quote(table_name(metadata.source))} "
                f"WHERE run_id = ? AND batch_id = ? AND list_contains(?, {quote(IDENTITY_COLUMN)})",
                [metadata.run_id, metadata.batch_id, keys],
            ).fetchall()
        }
        accepted: list[AcceptedRecord] = []
        duplicates: list[dict] = []
        conflicts: list[RejectedRecord] = []
        claimed: set[str] = set()
        for record in result.accepted:
            technical = record.metadata
            key = technical["idempotency_key"]
            known = persisted.get(technical["record_identity"])
            if key in same_batch or known is None:
                accepted.append(record)
                claimed.add(key)
            elif known == technical["content_checksum"]:
                duplicates.append(technical)
            else:
                conflicts.append(
                    RejectedRecord(
                        technical["source"],
                        technical["source_checksum"],
                        technical["source_offset"],
                        metadata.run_id,
                        metadata.batch_id,
                        technical["ingested_at"],
                        (Violation("IDENTITY_CONFLICT", "identity"),),
                    )
                )
        for technical in result.duplicates:
            key = technical["idempotency_key"]
            if key in same_batch and key not in claimed:
                claimed.add(key)
                continue
            duplicates.append(technical)
        return accepted, duplicates, conflicts

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

    def _converge_previous_rejections(self, metadata: BatchMetadata) -> None:
        """Descarta as rejeições que uma tentativa anterior do mesmo lote gravou.

        A retomada retransforma o lote do zero e a classificação pode mudar
        entre tentativas (as referências de consistência vêm do estado atual do
        banco), gerando ``rejection_id`` diferentes para a mesma ocorrência da
        fonte. Sem a limpeza, a tentativa retomada se soma à interrompida e a
        reconciliação passa a contar rejeitado a mais que extraído
        (``balanced = False`` permanente). Como roda dentro da transação do
        ``load_batch``, ou substitui tudo ou não substitui nada. Os motivos são
        removidos antes por ``rejection_id``, porque ``rejected_reason`` não
        carrega ``run_id``/``batch_id``. O filtro por ``source_checksum``
        restringe a limpeza às linhas gravadas por tentativas deste mesmo
        objeto: uma rejeição inserida por fora (sem o checksum do lote) não é
        tocada e continua entrando na contagem confirmada.
        """
        self._conn.execute(
            f"DELETE FROM {quote(REJECTED_REASON_TABLE)} WHERE rejection_id IN ("
            f"SELECT rejection_id FROM {quote(REJECTED_TABLE)} "
            "WHERE run_id = ? AND batch_id = ? AND source_checksum = ?)",
            [metadata.run_id, metadata.batch_id, metadata.source_checksum],
        )
        self._conn.execute(
            f"DELETE FROM {quote(REJECTED_TABLE)} "
            "WHERE run_id = ? AND batch_id = ? AND source_checksum = ?",
            [metadata.run_id, metadata.batch_id, metadata.source_checksum],
        )

    def _record_rejections(self, rejected: tuple[RejectedRecord, ...]) -> None:
        """Grava as ocorrências rejeitadas e os motivos do lote inteiro em duas escritas em lote.

        Duas ``executemany`` para o lote inteiro, não uma por ocorrência: é o
        que torna a escrita "em lotes parametrizados" de fato, em vez de N
        comandos avulsos. A rejeição converge em vez de falhar por chave
        repetida quando um backfill reprocessa o lote: a tentativa anterior é
        descartada por ``_converge_previous_rejections`` antes desta escrita.
        Lote sem rejeição chega com listas vazias; ``_insert_many`` não emite
        comando nesse caso.
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
                {
                    "rejection_id": record.rejection_id,
                    "code": violation.code,
                    "field": violation.field,
                }
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

    def _log_failed_batch(
        self, result: TransformationResult, metadata: BatchMetadata, started: float
    ) -> None:
        """Publica o evento técnico do lote perdido.

        Mesmas contagens zeradas de :meth:`_record_failed_batch`: sem isto, a
        falha nunca chega à plataforma de observabilidade como um evento — só
        como a linha ``falha`` em ``_batch_metadata``, e a ADR 0001 pede o
        estado final de cada lote no log, não só na tabela de controle.
        """
        outcome = LoadResult(
            source=metadata.source,
            run_id=metadata.run_id,
            batch_id=metadata.batch_id,
            extracted=result.metrics["extracted_count"],
            loaded=0,
            rejected=0,
            duplicates=0,
        )
        duration_ms = round((time.monotonic() - started) * 1000, 3)
        self._emit_log(
            LoadBatchLogEvent.from_result(
                outcome, metadata, status=BATCH_STATUS_FAILED, duration_ms=duration_ms
            )
        )

    def _emit_log(self, event: LoadBatchLogEvent) -> None:
        """Publica no sink sem deixar uma falha de telemetria virar falha da carga.

        A mesma garantia do ADR 0001 vale para o log que vale para o registro em
        ``_batch_metadata``: o mecanismo de observabilidade não pode corromper
        nem confirmar uma carga incompleta — aqui, isso quer dizer não impedir o
        retorno (ou a propagação do erro real) por um sink fora do ar.
        """
        try:
            self._log_sink.emit(event)
        except Exception:
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
            self._conn.execute(f"SELECT count(*) FROM {quote(table_name(source))}").fetchone()[0]
        )

    def fetch_compatibility_records(self, source: str) -> list[dict[str, Any]]:
        """Lê todas as colunas de negócio da view de compatibilidade da fonte.

        Interface pública para a montagem de referências da orquestração:
        devolve uma lista de dicionários coluna→valor, sem expor a
        conexão interna. A view tem o nome sem prefixo (ex.: ``empresas``) e
        espelha a tabela de ingestão (ver ``create_legacy_view``).
        """

        cursor = self._conn.execute(f"SELECT * FROM {quote(source)}")
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _cell(value: Any) -> Any:
    """Converte valores para o que o driver aceita (listas viram JSON)."""
    if isinstance(value, (list, tuple)):
        return json.dumps(list(value), ensure_ascii=False)
    return value
