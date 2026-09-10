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

Não decide quando o pipeline executa nem contém regra de transformação.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

from etl.extraction.contracts import BatchMetadata, ExtractionCheckpoint
from etl.transformation.pipeline import TransformationResult
from etl.transformation.schema import KEYS, SCHEMAS, destination_columns

# ClickHouse (contrato canônico) -> DuckDB. Nullable é implícito no DuckDB.
_BASE_TYPES = {
    "String": "VARCHAR",
    "Int64": "BIGINT",
    "UInt64": "UBIGINT",
    "Bool": "BOOLEAN",
    "Date32": "DATE",
}


def _duckdb_type(clickhouse_type: str) -> str:
    inner = clickhouse_type
    if inner.startswith("Nullable(") and inner.endswith(")"):
        inner = inner[len("Nullable(") : -1]
    if inner.startswith("FixedString"):
        return "VARCHAR"
    if inner.startswith("Decimal"):
        return "DECIMAL(18, 6)"
    if inner.startswith("DateTime64"):
        return "TIMESTAMP"
    if inner.startswith("Array"):
        return "VARCHAR"  # lista serializada como JSON
    return _BASE_TYPES.get(inner, "VARCHAR")


def _quote(identifier: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", identifier):
        raise ValueError(f"identificador inválido: {identifier!r}")
    return f'"{identifier}"'


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
        for source, fields in SCHEMAS.items():
            cols = ", ".join(
                f"{_quote(name)} {_duckdb_type(ch_type)}"
                for name, ch_type in destination_columns(source).items()
            )
            self._conn.execute(f"CREATE TABLE IF NOT EXISTS {_quote(source)} ({cols})")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS rejected ("
            "source VARCHAR, source_checksum VARCHAR, source_offset UBIGINT, "
            "run_id VARCHAR, batch_id VARCHAR, ingested_at TIMESTAMP, reasons VARCHAR)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS _control_object ("
            "source VARCHAR, source_checksum VARCHAR PRIMARY KEY, "
            "run_id VARCHAR, concluded_at TIMESTAMP)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS _loaded_identity ("
            "source VARCHAR, record_identity VARCHAR PRIMARY KEY, content_checksum VARCHAR)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS _checkpoint ("
            "source VARCHAR PRIMARY KEY, position VARCHAR, sequence BIGINT, source_version VARCHAR)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS _batch_metadata ("
            "source VARCHAR, run_id VARCHAR, task_id VARCHAR, batch_id VARCHAR, "
            "record_count BIGINT, byte_count BIGINT, schema_version VARCHAR, "
            "source_checksum VARCHAR, started_at TIMESTAMP, finished_at TIMESTAMP)"
        )

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
            f"INSERT INTO {_quote(source)} "
            f"({', '.join(_quote(c) for c in columns)}) VALUES ({placeholders})"
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
        return int(self._conn.execute(f"SELECT count(*) FROM {_quote(source)}").fetchone()[0])


def _cell(value: Any) -> Any:
    """Converte valores para o que o driver aceita (listas viram JSON)."""
    if isinstance(value, (list, tuple)):
        return json.dumps(list(value), ensure_ascii=False)
    return value
