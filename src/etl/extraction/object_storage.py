"""Acesso somente leitura aos objetos que disparam a extração."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    BinaryIO,
    ContextManager,
    Protocol,
    runtime_checkable,
)
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from .config import ExtractionSettings


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

    @classmethod
    def from_settings(cls, settings: ExtractionSettings) -> MinioObjectReader:
        """Cria o adaptador com timeout e sem retry interno do cliente HTTP."""

        import certifi
        from minio import Minio
        from urllib3 import PoolManager, Timeout

        parsed_endpoint = urlsplit(settings.minio_endpoint)
        http_client = PoolManager(
            timeout=Timeout(
                connect=settings.request_timeout_seconds,
                read=settings.request_timeout_seconds,
            ),
            maxsize=10,
            cert_reqs="CERT_REQUIRED",
            ca_certs=certifi.where(),
            retries=False,
        )
        client = Minio(
            endpoint=parsed_endpoint.netloc,
            access_key=settings.minio_access_key.get_secret_value(),
            secret_key=settings.minio_secret_key.get_secret_value(),
            secure=parsed_endpoint.scheme == "https",
            http_client=http_client,
        )
        return cls(client)

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
