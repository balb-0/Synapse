"""Eventos técnicos emitidos pela etapa de extração."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol, cast, runtime_checkable

from .contracts import ExtractedBatch


EXTRACTION_BATCH_EVENT = "extraction.batch.emitted"
EXTRACTION_STAGE = "extraction"
SUCCESS_STATUS = "success"


@dataclass(frozen=True, slots=True)
class ExtractionBatchLogEvent:
    """Representa um lote somente por atributos técnicos permitidos em logs."""

    source: str
    run_id: str
    task_id: str
    batch_id: str
    started_at: str
    finished_at: str
    duration_ms: float
    record_count: int
    byte_count: int
    schema_version: str
    contract_version: str
    checkpoint_position: str
    checkpoint_sequence: int
    source_checksum: str | None = None
    checkpoint_source_version: str | None = None

    @classmethod
    def from_batch(cls, batch: ExtractedBatch) -> ExtractionBatchLogEvent:
        metadata = batch.metadata
        metadata_values = metadata.as_dict()
        checkpoint = batch.checkpoint
        elapsed = metadata.finished_at - metadata.started_at
        return cls(
            source=metadata.source,
            run_id=metadata.run_id,
            task_id=metadata.task_id,
            batch_id=metadata.batch_id,
            started_at=cast(str, metadata_values["started_at"]),
            finished_at=cast(str, metadata_values["finished_at"]),
            duration_ms=round(elapsed.total_seconds() * 1000, 3),
            record_count=metadata.record_count,
            byte_count=metadata.byte_count,
            schema_version=metadata.schema_version,
            contract_version=metadata.contract_version,
            checkpoint_position=checkpoint.position,
            checkpoint_sequence=checkpoint.sequence,
            source_checksum=metadata.source_checksum,
            checkpoint_source_version=checkpoint.source_version,
        )

    def as_dict(self) -> dict[str, str | int | float]:
        attributes: dict[str, str | int | float | None] = {
            "event": EXTRACTION_BATCH_EVENT,
            "stage": EXTRACTION_STAGE,
            "status": SUCCESS_STATUS,
            "source": self.source,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "batch_id": self.batch_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "record_count": self.record_count,
            "byte_count": self.byte_count,
            "schema_version": self.schema_version,
            "contract_version": self.contract_version,
            "source_checksum": self.source_checksum,
            "checkpoint_position": self.checkpoint_position,
            "checkpoint_sequence": self.checkpoint_sequence,
            "checkpoint_source_version": self.checkpoint_source_version,
        }
        return {
            key: value
            for key, value in attributes.items()
            if value is not None
        }


@runtime_checkable
class ExtractionLogSink(Protocol):
    """Destino dos eventos estruturados produzidos pelos extratores."""

    def emit(self, event: ExtractionBatchLogEvent) -> None:
        """Publica um evento sem receber os registros extraídos."""

        ...


class StandardLoggingSink:
    """Adapta eventos de extração para o módulo ``logging`` do Python."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("etl.extraction")

    def emit(self, event: ExtractionBatchLogEvent) -> None:
        attributes = event.as_dict()
        self._logger.info(EXTRACTION_BATCH_EVENT, extra=attributes)
