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
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

from etl.extraction.contracts import BatchMetadata, ExtractionCheckpoint
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


class DuckDbLoadRepository:
    """Grava lotes tratados no DuckDB e mantém as tabelas de controle."""

    def __init__(self, database: str | Path) -> None:
        self._database = str(database)
        self._conn = duckdb.connect(self._database)
        self._ensure_schema()

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
        """Grava aceitos e rejeitados numa transação e reconcilia as contagens."""
        source = metadata.source
        columns = list(destination_columns(source))
        placeholders = ", ".join("?" for _ in columns)
        insert_sql = (
            f"INSERT INTO {quote(table_name(source))} "
            f"({', '.join(quote(c) for c in columns)}) VALUES ({placeholders})"
        )
        self._conn.execute("BEGIN TRANSACTION")
        try:
            for record in result.accepted:
                row = record.as_clickhouse_row()
                self._conn.execute(insert_sql, [_cell(row.get(c)) for c in columns])
                self._conn.execute(
                    "INSERT OR REPLACE INTO _loaded_identity VALUES (?, ?, ?)",
                    [source, row["record_identity"], row["content_checksum"]],
                )
            for rejected in result.rejected:
                self._record_rejection(rejected)
            self._record_batch(
                metadata,
                status=(
                    BATCH_STATUS_LOADED_WITH_REJECTIONS if result.rejected else BATCH_STATUS_LOADED
                ),
                accepted=len(result.accepted),
                rejected=len(result.rejected),
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
            loaded=len(result.accepted),
            rejected=len(result.rejected),
            duplicates=len(result.duplicates),
        )

    # ---------- registro de rejeição ----------

    def _record_rejection(self, rejected: RejectedRecord) -> None:
        """Grava a ocorrência rejeitada e um motivo por linha.

        A rejeição converge em vez de falhar por chave repetida em dois casos
        reais: um backfill reprocessa o lote, e o mesmo par código/campo
        aparece duas vezes na mesma ocorrência.
        """
        self._insert(
            "rejected",
            REJECTED_COLUMNS,
            {
                "rejection_id": rejected.rejection_id,
                "source": rejected.source,
                "source_checksum": rejected.source_checksum,
                "source_offset": rejected.source_offset,
                "run_id": rejected.run_id,
                "batch_id": rejected.batch_id,
                "ingested_at": rejected.ingested_at,
            },
        )
        for violation in rejected.violations:
            self._insert(
                "rejected_reason",
                REJECTED_REASON_COLUMNS,
                {
                    "rejection_id": rejected.rejection_id,
                    "code": violation.code,
                    "field": violation.field,
                },
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
        """Insere por nome de coluna, convergindo quando a linha já existe.

        Nomear as colunas troca "valor deslocado em silêncio" por erro de
        coluna ausente quando o contrato ganha campo. ``INSERT OR REPLACE``
        porque um reprocessamento reapresenta a mesma linha de controle — o que
        só é possível onde existe chave para substituir.
        """
        verb = "INSERT INTO" if table in self._keyless_control_tables else "INSERT OR REPLACE INTO"
        names = ", ".join(quote(column) for column in columns)
        placeholders = ", ".join("?" for _ in columns)
        self._conn.execute(
            f"{verb} {quote(table)} ({names}) VALUES ({placeholders})",
            [values[column] for column in columns],
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
