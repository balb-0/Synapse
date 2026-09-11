"""Eventos técnicos emitidos pela etapa de carga.

Espelha o formato de ``etl.extraction.log_events``: um evento por lote,
sem os registros e sem dado pessoal, publicado por um sink injetável. O
tipo do resultado de carga (``LoadResult``) só é usado em anotação — importar
``duckdb_repository`` aqui de verdade criaria um ciclo, já que ele importa
este módulo para emitir o evento.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from etl.extraction.contracts import BatchMetadata

if TYPE_CHECKING:
    from .duckdb_repository import LoadResult

LOAD_BATCH_EVENT = "load.batch.emitted"
LOAD_STAGE = "load"


@dataclass(frozen=True, slots=True)
class LoadBatchLogEvent:
    """Representa a reconciliação de um lote carregado, sem os registros."""

    source: str
    run_id: str
    task_id: str
    batch_id: str
    status: str
    duration_ms: float
    extracted_count: int
    loaded_count: int
    rejected_count: int
    duplicate_count: int
    balanced: bool
    schema_version: str
    source_checksum: str | None = None

    @classmethod
    def from_result(
        cls,
        result: LoadResult,
        metadata: BatchMetadata,
        *,
        status: str,
        duration_ms: float,
    ) -> LoadBatchLogEvent:
        return cls(
            source=result.source,
            run_id=result.run_id,
            task_id=metadata.task_id,
            batch_id=result.batch_id,
            status=status,
            duration_ms=duration_ms,
            extracted_count=result.extracted,
            loaded_count=result.loaded,
            rejected_count=result.rejected,
            duplicate_count=result.duplicates,
            balanced=result.is_balanced(),
            schema_version=metadata.schema_version,
            source_checksum=metadata.source_checksum,
        )

    def as_dict(self) -> dict[str, str | int | float | bool]:
        attributes: dict[str, str | int | float | bool | None] = {
            "event": LOAD_BATCH_EVENT,
            "stage": LOAD_STAGE,
            "status": self.status,
            "source": self.source,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "batch_id": self.batch_id,
            "duration_ms": self.duration_ms,
            "extracted_count": self.extracted_count,
            "loaded_count": self.loaded_count,
            "rejected_count": self.rejected_count,
            "duplicate_count": self.duplicate_count,
            "balanced": self.balanced,
            "schema_version": self.schema_version,
            "source_checksum": self.source_checksum,
        }
        return {key: value for key, value in attributes.items() if value is not None}


@runtime_checkable
class LoadLogSink(Protocol):
    """Destino dos eventos estruturados produzidos pela carga."""

    def emit(self, event: LoadBatchLogEvent) -> None:
        """Publica a reconciliação de um lote sem receber os registros."""

        ...


class StandardLoggingSink:
    """Adapta eventos de carga para o módulo ``logging`` do Python."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("etl.load")

    def emit(self, event: LoadBatchLogEvent) -> None:
        attributes = event.as_dict()
        self._logger.info(LOAD_BATCH_EVENT, extra=attributes)
