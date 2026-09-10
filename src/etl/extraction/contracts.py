"""Interfaces compartilhadas pelos extratores.

O módulo contém apenas tipos de domínio. Ele não conhece o armazenamento de
objetos, o orquestrador, o banco nem a forma de persistir checkpoints.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, TypeAlias, runtime_checkable


CONTRACT_VERSION = "1.0"
Record: TypeAlias = Mapping[str, Any]


def _require_text(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} não pode ser vazio")


def _require_aware_datetime(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} deve possuir timezone")


def _isoformat(value: datetime) -> str:
    rendered = value.isoformat()
    return rendered[:-6] + "Z" if rendered.endswith("+00:00") else rendered


@dataclass(frozen=True, slots=True)
class ExtractionCheckpoint:
    """Posição opaca a partir da qual uma fonte pode retomar a leitura.

    ``position`` pode representar uma linha, página, cursor ou outro marcador.
    O extrator interpreta esse valor; o repositório de checkpoint apenas o
    persiste. ``source_version`` evita aplicar um checkpoint a outra versão da
    mesma fonte.
    """

    source: str
    position: str
    sequence: int
    source_version: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.source, "source")
        _require_text(self.position, "position")
        if self.sequence < 0:
            raise ValueError("sequence não pode ser negativo")
        if self.source_version is not None:
            _require_text(self.source_version, "source_version")

    def as_dict(self) -> dict[str, str | int | None]:
        return {
            "source": self.source,
            "position": self.position,
            "sequence": self.sequence,
            "source_version": self.source_version,
        }


@dataclass(frozen=True, slots=True)
class BatchMetadata:
    """Metadados técnicos de um lote, sem conteúdo dos registros."""

    source: str
    run_id: str
    task_id: str
    batch_id: str
    started_at: datetime
    finished_at: datetime
    record_count: int
    byte_count: int
    schema_version: str
    source_checksum: str | None = None
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "source",
            "run_id",
            "task_id",
            "batch_id",
            "schema_version",
            "contract_version",
        ):
            _require_text(getattr(self, field_name), field_name)

        if self.source_checksum is not None:
            _require_text(self.source_checksum, "source_checksum")
        _require_aware_datetime(self.started_at, "started_at")
        _require_aware_datetime(self.finished_at, "finished_at")
        if self.finished_at < self.started_at:
            raise ValueError("finished_at não pode ser anterior a started_at")
        if self.record_count < 0:
            raise ValueError("record_count não pode ser negativo")
        if self.byte_count < 0:
            raise ValueError("byte_count não pode ser negativo")

    def as_dict(self) -> dict[str, str | int | None]:
        return {
            "source": self.source,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "batch_id": self.batch_id,
            "started_at": _isoformat(self.started_at),
            "finished_at": _isoformat(self.finished_at),
            "record_count": self.record_count,
            "byte_count": self.byte_count,
            "schema_version": self.schema_version,
            "source_checksum": self.source_checksum,
            "contract_version": self.contract_version,
        }


@dataclass(frozen=True, slots=True)
class ExtractedBatch:
    """Lote entregue por qualquer extrator ao estágio seguinte do ETL."""

    records: Sequence[Record]
    checkpoint: ExtractionCheckpoint
    metadata: BatchMetadata

    def __post_init__(self) -> None:
        normalized_records = tuple(dict(record) for record in self.records)
        object.__setattr__(self, "records", normalized_records)

        if self.metadata.source != self.checkpoint.source:
            raise ValueError("metadata e checkpoint devem pertencer à mesma fonte")
        if self.metadata.record_count != len(normalized_records):
            raise ValueError("record_count deve corresponder à quantidade de registros")

    def as_attributes(self) -> dict[str, str]:
        """Representa metadados e checkpoint como atributos de transporte.

        O formato pode ser usado pelo orquestrador ou por outro mecanismo de
        mensageria sem incluir os registros ou qualquer PII nos atributos.
        """

        metadata = {
            key: str(value)
            for key, value in self.metadata.as_dict().items()
            if value is not None
        }
        checkpoint = {
            "checkpoint_position": self.checkpoint.position,
            "checkpoint_sequence": str(self.checkpoint.sequence),
        }
        if self.checkpoint.source_version is not None:
            checkpoint["checkpoint_source_version"] = self.checkpoint.source_version
        return {**metadata, **checkpoint}


@runtime_checkable
class Extractor(Protocol):
    """Lê uma fonte e produz lotes sem persistir estado ou metadados."""

    @property
    def source(self) -> str:
        """Nome estável da fonte extraída."""

        ...

    def read(
        self,
        *,
        run_id: str,
        checkpoint: ExtractionCheckpoint | None = None,
    ) -> Iterator[ExtractedBatch]:
        """Produz lotes a partir do checkpoint informado, quando houver."""

        ...


@runtime_checkable
class CheckpointStore(Protocol):
    """Persiste checkpoints somente após a confirmação de um lote."""

    def load(self, source: str) -> ExtractionCheckpoint | None:
        """Retorna o último checkpoint confirmado para a fonte."""

        ...

    def commit(self, checkpoint: ExtractionCheckpoint) -> None:
        """Confirma a posição depois que o consumidor aceitou o lote."""

        ...


@runtime_checkable
class MetadataSink(Protocol):
    """Publica metadados técnicos sem receber o conteúdo dos registros."""

    def emit(self, metadata: BatchMetadata) -> None:
        """Registra os metadados de um lote extraído."""

        ...
