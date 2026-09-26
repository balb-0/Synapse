"""Adaptador LN-02 -> transformação: contabilização, linhagem e saída tipada."""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from zoneinfo import ZoneInfo

from etl.extraction.contracts import ExtractedBatch

from .consistency import ReferenceData, validate_consistency
from .identity import classify_duplicates, digest, json_value, record_identity
from .log_events import StandardLoggingSink, TransformationBatchLogEvent, TransformationLogSink
from .normalization import normalize_record
from .quarantine import RejectedRecord
from .schema import SCHEMA_VERSION, SCHEMAS
from .validation import Violation


@dataclass(frozen=True)
class AcceptedRecord:
    data: dict = field(repr=False)
    metadata: dict = field(repr=False)

    def as_duckdb_row(self):
        return {**json_value(self.data), **self.metadata}


@dataclass(frozen=True)
class TransformationResult:
    accepted: tuple[AcceptedRecord, ...] = field(repr=False)
    rejected: tuple[RejectedRecord, ...] = field(repr=False)
    duplicates: tuple[dict, ...] = field(repr=False)
    metrics: dict

    def safe_summary(self):
        return dict(self.metrics)


@dataclass
class _PreparedBatch:
    """Lote normalizado e validado, ainda sem decisão de duplicidade."""

    meta: object
    timestamp: str
    started: float
    total: int
    rejected: list
    candidates: list

    def rejection(self, offset, violations):
        return RejectedRecord(
            self.meta.source,
            self.meta.source_checksum,
            offset,
            self.meta.run_id,
            self.meta.batch_id,
            self.timestamp,
            tuple(sorted(set(violations))),
        )


def _prepare_batch(
    batch: ExtractedBatch,
    *,
    references: ReferenceData,
    source_offset: int,
    ingested_at: datetime,
    source_timezone: str | None,
) -> _PreparedBatch:
    """Valida o contrato do lote, normaliza e separa rejeições por validação."""
    started = perf_counter()
    meta = batch.metadata
    source = meta.source
    if source not in SCHEMAS:
        raise ValueError("UNKNOWN_SOURCE")
    if meta.contract_version != "1.0":
        raise ValueError("UNSUPPORTED_CONTRACT_VERSION")
    if not meta.source_checksum or not re.fullmatch(r"[a-f0-9]{64}", meta.source_checksum):
        raise ValueError("SOURCE_CHECKSUM_REQUIRED")
    if type(source_offset) is not int or not 0 <= source_offset < 2**64:
        raise ValueError("INVALID_SOURCE_OFFSET")
    if source_offset + len(batch.records) > 2**64:
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
    if not 1900 <= ingested_at.astimezone(timezone.utc).year <= 2299:
        raise ValueError("INGESTION_DATE_RANGE")
    prepared = _PreparedBatch(meta, timestamp, started, len(batch.records), [], [])

    for index, raw in enumerate(batch.records):
        offset = source_offset + index
        row, errors = normalize_record(source, raw, source_timezone)
        if not errors:
            errors = validate_consistency(source, row, references)
        if errors:
            prepared.rejected.append(prepared.rejection(offset, errors))
            continue
        identity = record_identity(source, row, meta.source_checksum, offset)
        checksum = digest(row)
        technical = {
            "source": source,
            "run_id": meta.run_id,
            "task_id": meta.task_id,
            "batch_id": meta.batch_id,
            "source_checksum": meta.source_checksum,
            "source_offset": offset,
            "content_checksum": checksum,
            "record_identity": identity,
            "idempotency_key": digest([identity, checksum]),
            "ingested_at": timestamp,
            "schema_version": SCHEMA_VERSION,
        }
        prepared.candidates.append((row, technical))
    return prepared


def _finish_batch(
    prepared: _PreparedBatch,
    outcomes: list[str],
    log_sink: TransformationLogSink | None,
) -> TransformationResult:
    """Aplica as decisões de duplicidade, fecha as métricas e publica o evento."""
    meta = prepared.meta
    accepted, duplicates = [], []
    rejected = list(prepared.rejected)
    for (row, technical), outcome in zip(prepared.candidates, outcomes, strict=True):
        if outcome == "accepted":
            accepted.append(AcceptedRecord(row, technical))
        elif outcome == "duplicate":
            duplicates.append(technical)
        else:
            rejected.append(
                prepared.rejection(
                    technical["source_offset"], [Violation("IDENTITY_CONFLICT", "identity")]
                )
            )
    total = prepared.total
    assert total == len(accepted) + len(rejected) + len(duplicates)
    metrics = {
        "source": meta.source,
        "run_id": meta.run_id,
        "task_id": meta.task_id,
        "batch_id": meta.batch_id,
        "stage": "transformation",
        "status": "completed_with_rejections" if rejected else "completed",
        "extracted_count": total,
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "duplicate_count": len(duplicates),
        "input_bytes": meta.byte_count,
        "duration_seconds": perf_counter() - prepared.started,
    }
    sink = log_sink or StandardLoggingSink()
    event = TransformationBatchLogEvent.from_metrics(metrics)
    try:
        sink.emit(event)
    except Exception:
        # Mesma garantia da ADR 0001 já aplicada em extraction/load: o
        # transporte de observabilidade fora do ar não pode corromper nem
        # bloquear o resultado da transformação. Só o envio ao sink entra no
        # try — um bug na construção do evento (chave errada em `metrics`)
        # deve continuar estourando, não ser confundido com sink fora do ar.
        pass
    return TransformationResult(tuple(accepted), tuple(rejected), tuple(duplicates), metrics)


def _identity_items(prepared: _PreparedBatch) -> list[tuple[str, str]]:
    return [(m["record_identity"], m["content_checksum"]) for _, m in prepared.candidates]


def transform_batch(
    batch: ExtractedBatch,
    *,
    references: ReferenceData,
    previous: dict[str, str],
    source_offset: int,
    ingested_at: datetime,
    source_timezone: str | None = None,
    log_sink: TransformationLogSink | None = None,
):
    """Transforma sem escrever dados nem confirmar checkpoint.

    ``source_offset`` é a posição absoluta zero-based do primeiro registro,
    obtida pelo extrator, nunca interpretada a partir do checkpoint opaco.
    ``previous`` contém somente identidades confirmadas na carga. Não usar
    cache de tentativas: uma falha após transformação deve permitir reexecução.

    A duplicidade é decidida só dentro deste lote e contra ``previous``. Para
    um objeto com vários lotes, use ``transform_object``, que decide a
    duplicidade uma única vez sobre todos os lotes.
    """
    prepared = _prepare_batch(
        batch,
        references=references,
        source_offset=source_offset,
        ingested_at=ingested_at,
        source_timezone=source_timezone,
    )
    outcomes = classify_duplicates(_identity_items(prepared), previous)
    return _finish_batch(prepared, outcomes, log_sink)


def transform_object(
    batches: list[ExtractedBatch] | tuple[ExtractedBatch, ...],
    *,
    references: ReferenceData,
    previous: dict[str, str],
    ingested_at: datetime,
    source_timezone: str | None = None,
    log_sink: TransformationLogSink | None = None,
) -> list[TransformationResult]:
    """Transforma todos os lotes de um objeto com uma decisão global de identidade.

    Cada lote usa a posição absoluta que o extrator gravou em
    ``metadata.source_offset`` (inclusive após retomada). A classificação de
    duplicidade roda **uma vez** sobre as ocorrências válidas de todos os
    lotes, na ordem da fonte, e contra ``previous``: a mesma identidade com o
    mesmo conteúdo em dois lotes vira duplicata no segundo; com conteúdos
    diferentes, todas as ocorrências viram ``IDENTITY_CONFLICT`` — a mesma
    regra aplicada dentro de um lote. O resultado continua um por lote, para
    que a carga e o checkpoint permaneçam lote a lote (ADR 0005).
    """
    prepared_batches = []
    for batch in batches:
        offset = batch.metadata.source_offset
        if offset is None:
            raise ValueError("SOURCE_OFFSET_REQUIRED")
        prepared_batches.append(
            _prepare_batch(
                batch,
                references=references,
                source_offset=offset,
                ingested_at=ingested_at,
                source_timezone=source_timezone,
            )
        )
    items = [item for prepared in prepared_batches for item in _identity_items(prepared)]
    outcomes = classify_duplicates(items, previous)
    results, cursor = [], 0
    for prepared in prepared_batches:
        size = len(prepared.candidates)
        results.append(_finish_batch(prepared, outcomes[cursor : cursor + size], log_sink))
        cursor += size
    return results
