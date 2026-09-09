"""Adaptador LN-02 -> transformação: contabilização, linhagem e saída tipada."""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from zoneinfo import ZoneInfo

from etl.extraction.contracts import ExtractedBatch
from .consistency import ReferenceData, validate_consistency
from .identity import classify_duplicates, digest, json_value, record_identity
from .normalization import normalize_record
from .quarantine import RejectedRecord
from .schema import SCHEMAS, SCHEMA_VERSION
from .validation import Violation


@dataclass(frozen=True)
class AcceptedRecord:
    data: dict = field(repr=False)
    metadata: dict = field(repr=False)

    def as_clickhouse_row(self):
        return {**json_value(self.data), **self.metadata}


@dataclass(frozen=True)
class TransformationResult:
    accepted: tuple[AcceptedRecord, ...] = field(repr=False)
    rejected: tuple[RejectedRecord, ...] = field(repr=False)
    duplicates: tuple[dict, ...] = field(repr=False)
    metrics: dict

    def safe_summary(self):
        return dict(self.metrics)


def transform_batch(batch: ExtractedBatch, *, references: ReferenceData,
                    previous: dict[str, str], source_offset: int,
                    ingested_at: datetime, source_timezone: str | None = None):
    """Transforma sem escrever dados nem confirmar checkpoint.

    ``source_offset`` é a posição absoluta zero-based do primeiro registro,
    obtida pelo extrator, nunca interpretada a partir do checkpoint opaco.
    ``previous`` contém somente identidades confirmadas na carga. Não usar
    cache de tentativas: uma falha após transformação deve permitir reexecução.
    """
    started = perf_counter()
    meta = batch.metadata
    source = meta.source
    if source not in SCHEMAS:
        raise ValueError("UNKNOWN_SOURCE")
    if meta.contract_version != "1.0":
        raise ValueError("UNSUPPORTED_CONTRACT_VERSION")
    if not meta.source_checksum or not re.fullmatch(r"[a-f0-9]{64}", meta.source_checksum):
        raise ValueError("SOURCE_CHECKSUM_REQUIRED")
    if type(source_offset) is not int or source_offset < 0:
        raise ValueError("INVALID_SOURCE_OFFSET")
    if not isinstance(ingested_at, datetime) or ingested_at.utcoffset() is None:
        raise ValueError("INGESTION_TIMEZONE_REQUIRED")
    if source_timezone:
        ZoneInfo(source_timezone)  # Configuration error, not a rejected row.
    references.require(source)
    for value in (meta.run_id, meta.task_id, meta.batch_id):
        if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", value):
            raise ValueError("INVALID_TECHNICAL_ID")
    timestamp = ingested_at.astimezone(timezone.utc).isoformat()
    accepted, rejected, duplicates, candidates = [], [], [], []

    def rejection(offset, violations):
        return RejectedRecord(source, meta.source_checksum, offset, meta.run_id,
                              meta.batch_id, timestamp, tuple(sorted(set(violations))))

    for index, raw in enumerate(batch.records):
        offset = source_offset + index
        row, errors = normalize_record(source, raw, source_timezone)
        if not errors:
            errors = validate_consistency(source, row, references)
        if errors:
            rejected.append(rejection(offset, errors))
            continue
        identity = record_identity(source, row, meta.source_checksum, offset)
        checksum = digest(row)
        technical = {"source": source, "run_id": meta.run_id, "task_id": meta.task_id,
                     "batch_id": meta.batch_id, "source_checksum": meta.source_checksum,
                     "source_offset": offset, "content_checksum": checksum,
                     "record_identity": identity,
                     "idempotency_key": digest([identity, checksum]),
                     "ingested_at": timestamp, "schema_version": SCHEMA_VERSION}
        candidates.append((row, technical))
    outcomes = classify_duplicates(
        [(m["record_identity"], m["content_checksum"]) for _, m in candidates], previous)
    for (row, technical), outcome in zip(candidates, outcomes):
        if outcome == "accepted":
            accepted.append(AcceptedRecord(row, technical))
        elif outcome == "duplicate":
            duplicates.append(technical)
        else:
            rejected.append(rejection(technical["source_offset"], [Violation("IDENTITY_CONFLICT", "identity")]))
    total = len(batch.records)
    assert total == len(accepted) + len(rejected) + len(duplicates)
    metrics = {"source": source, "run_id": meta.run_id, "task_id": meta.task_id,
               "batch_id": meta.batch_id, "stage": "transformation",
               "status": "completed_with_rejections" if rejected else "completed",
               "extracted_count": total, "accepted_count": len(accepted),
               "rejected_count": len(rejected), "duplicate_count": len(duplicates),
               "input_bytes": meta.byte_count,
               "duration_seconds": perf_counter() - started}
    return TransformationResult(tuple(accepted), tuple(rejected), tuple(duplicates), metrics)
