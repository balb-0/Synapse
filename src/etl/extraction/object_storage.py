"""Acesso somente leitura aos objetos que disparam a extração."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, BinaryIO, ContextManager, Protocol, runtime_checkable


def _require_text(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} não pode ser vazio")


@dataclass(frozen=True, slots=True)
class ObjectReference:
    """Identifica sem ambiguidade um objeto informado pelo evento do MinIO."""

    bucket: str
    key: str
    version_id: str | None = None
    event_id: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.bucket, "bucket")
        _require_text(self.key, "key")
        if self.version_id is not None:
            _require_text(self.version_id, "version_id")
        if self.event_id is not None:
            _require_text(self.event_id, "event_id")


@runtime_checkable
class ObjectReader(Protocol):
    """Abre um objeto remoto sem transferir sua responsabilidade ao extrator."""

    def open(self, reference: ObjectReference) -> ContextManager[BinaryIO]:
        """Retorna um stream binário que será fechado ao sair do contexto."""

        ...


class MinioObjectReader:
    """Adapta um cliente do SDK do MinIO ao contrato de leitura de objetos."""

    def __init__(self, client: Any) -> None:
        self._client = client

    @contextmanager
    def open(self, reference: ObjectReference) -> Iterator[BinaryIO]:
        options: dict[str, str] = {}
        if reference.version_id is not None:
            options["version_id"] = reference.version_id

        response = self._client.get_object(
            reference.bucket,
            reference.key,
            **options,
        )
        try:
            yield response
        finally:
            try:
                response.close()
            finally:
                response.release_conn()

