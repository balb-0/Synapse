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
from etl.load.ddl import quote, statements, table_name
from etl.transformation.pipeline import TransformationResult
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
        """Aplica o contrato físico versionado da camada de carga."""
        for statement in statements():
            self._conn.execute(statement)

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
                self._conn.execute(
                    "INSERT INTO rejected VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [
                        rejected.source,
                        rejected.source_checksum,
                        rejected.source_offset,
                        rejected.run_id,
                        rejected.batch_id,
                        rejected.ingested_at,
                        json.dumps(
                            [{"code": v.code, "field": v.field} for v in rejected.violations],
                            ensure_ascii=False,
                        ),
                    ],
                )
            self._conn.execute(
                "INSERT INTO _batch_metadata VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    metadata.source,
                    metadata.run_id,
                    metadata.task_id,
                    metadata.batch_id,
                    metadata.record_count,
                    metadata.byte_count,
                    metadata.schema_version,
                    metadata.source_checksum,
                    metadata.started_at,
                    metadata.finished_at,
                ],
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
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
