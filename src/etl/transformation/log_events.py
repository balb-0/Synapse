"""Eventos técnicos emitidos pela etapa de transformação.

Espelha o formato de ``etl.extraction.log_events``/``etl.load.log_events``:
um evento por lote, sem os registros, publicado por um sink injetável.
``TransformationResult.metrics`` (``pipeline.py``) já calcula todo o
conteúdo — este módulo só fecha o formato como classe publicável, sem
recalcular nada (ADR 0008, ponto 3).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

TRANSFORMATION_BATCH_EVENT = "transformation.batch.emitted"
TRANSFORMATION_STAGE = "transformation"


@dataclass(frozen=True, slots=True)
class TransformationBatchLogEvent:
    """Representa a transformação de um lote, sem os registros."""

    source: str
    run_id: str
    task_id: str
    batch_id: str
    status: str
    duration_ms: float
    extracted_count: int
    accepted_count: int
    rejected_count: int
    duplicate_count: int
    byte_count: int

    @classmethod
    def from_metrics(cls, metrics: dict) -> TransformationBatchLogEvent:
        return cls(
            source=metrics["source"],
            run_id=metrics["run_id"],
            task_id=metrics["task_id"],
            batch_id=metrics["batch_id"],
            status=metrics["status"],
            duration_ms=round(metrics["duration_seconds"] * 1000, 3),
            extracted_count=metrics["extracted_count"],
            accepted_count=metrics["accepted_count"],
            rejected_count=metrics["rejected_count"],
            duplicate_count=metrics["duplicate_count"],
            byte_count=metrics["input_bytes"],
        )

    def as_dict(self) -> dict[str, str | int | float]:
        return {
            "event": TRANSFORMATION_BATCH_EVENT,
            "stage": TRANSFORMATION_STAGE,
            "status": self.status,
            "source": self.source,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "batch_id": self.batch_id,
            "duration_ms": self.duration_ms,
            "extracted_count": self.extracted_count,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "duplicate_count": self.duplicate_count,
            "byte_count": self.byte_count,
        }


@runtime_checkable
class TransformationLogSink(Protocol):
    """Destino dos eventos estruturados produzidos pela transformação."""

    def emit(self, event: TransformationBatchLogEvent) -> None:
        """Publica um lote transformado sem receber os registros."""

        ...


class StandardLoggingSink:
    """Adapta eventos de transformação para o módulo ``logging`` do Python."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("etl.transformation")

    def emit(self, event: TransformationBatchLogEvent) -> None:
        attributes = event.as_dict()
        self._logger.info(TRANSFORMATION_BATCH_EVENT, extra=attributes)
