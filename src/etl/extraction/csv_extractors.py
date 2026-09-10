"""Extratores CSV das fontes publicadas no MinIO."""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Iterator
from datetime import UTC, datetime
from io import StringIO

from .contracts import (
    BatchMetadata,
    ExtractedBatch,
    ExtractionCheckpoint,
    Record,
)
from .object_storage import ObjectReader, ObjectReference


PESQUISAS_REQUIRED_COLUMNS = (
    "id",
    "titulo",
    "status",
    "tipo",
    "area",
    "participantes",
    "part_mercado",
    "data_solicitacao",
    "data_aprov",
    "data_divulgacao",
    "data_limite",
    "prorrogada_ate",
    "data_entrega",
    "dias_uteis_para_entrega",
    "complexidade",
    "tipo de resposta",
    "tempo_preenchimento",
    "objetivos",
    "dia da semana de lançamento",
    "dias úteis aberta",
    "dias entre a solicitação e a divulgação",
    "dias para tabulação",
)

EMPRESAS_REQUIRED_COLUMNS = (
    "ID",
    "Nome Fantasia",
    "% de mercado",
    "Nacionalidade",
    "Associado",
    "Tipo de Associado",
    "Cidade",
    "Estado",
    "País",
)

CLIENTES_REQUIRED_COLUMNS = (
    "id_cliente",
    "id_empresa",
    "cargo",
    "departamento",
    "e-mail",
)

RESPONDENTES_REQUIRED_COLUMNS = (
    "id_pesq",
    "hora_inicio",
    "hora_termino",
    "id_empresa",
    "market_share",
    "id_cliente",
)


class ExtractionError(RuntimeError):
    """Erro conhecido durante a leitura de uma fonte."""


class MalformedSourceError(ExtractionError):
    """A fonte não pode ser interpretada segundo seu contrato CSV."""


class UnsupportedCheckpointError(ExtractionError):
    """A versão atual do extrator ainda não oferece retomada parcial."""


def _normalize_headers(headers: list[str]) -> tuple[str, ...]:
    """Cria nomes estáveis para colunas vazias ou repetidas sem perder posição."""

    normalized: list[str] = []
    occurrences: dict[str, int] = {}

    for position, original_name in enumerate(headers, start=1):
        base_name = original_name or f"unnamed_column_{position}"
        occurrences[base_name] = occurrences.get(base_name, 0) + 1
        occurrence = occurrences[base_name]
        normalized.append(
            base_name if occurrence == 1 else f"{base_name}__{occurrence}"
        )

    return tuple(normalized)


class CsvObjectExtractor:
    """Lê integralmente um CSV do MinIO e produz um lote no contrato comum."""

    delimiter = ";"
    encoding = "utf-8-sig"

    def __init__(
        self,
        *,
        source: str,
        schema_version: str,
        required_columns: tuple[str, ...],
        object_reader: ObjectReader,
        object_reference: ObjectReference,
    ) -> None:
        self._source = source
        self._schema_version = schema_version
        self._required_columns = required_columns
        self._object_reader = object_reader
        self._object_reference = object_reference

    @property
    def source(self) -> str:
        return self._source

    def read(
        self,
        *,
        run_id: str,
        checkpoint: ExtractionCheckpoint | None = None,
    ) -> Iterator[ExtractedBatch]:
        if not run_id or not run_id.strip():
            raise ValueError("run_id não pode ser vazio")
        if checkpoint is not None:
            raise UnsupportedCheckpointError(
                "retomada por checkpoint será implementada na LN-07"
            )

        started_at = datetime.now(UTC)
        payload = self._read_payload()
        checksum = "sha256:" + hashlib.sha256(payload).hexdigest()
        records = self._parse_records(payload)
        finished_at = datetime.now(UTC)

        extracted_checkpoint = ExtractionCheckpoint(
            source=self.source,
            position=f"row:{len(records)}",
            sequence=1,
            source_version=checksum,
        )
        metadata = BatchMetadata(
            source=self.source,
            run_id=run_id,
            task_id=f"extract-{self.source}",
            batch_id=f"{self.source}-000001",
            started_at=started_at,
            finished_at=finished_at,
            record_count=len(records),
            byte_count=len(payload),
            schema_version=self._schema_version,
            source_checksum=checksum,
        )

        yield ExtractedBatch(
            records=records,
            checkpoint=extracted_checkpoint,
            metadata=metadata,
        )

    def _read_payload(self) -> bytes:
        with self._object_reader.open(self._object_reference) as stream:
            payload = stream.read()

        if not isinstance(payload, bytes):
            raise MalformedSourceError("o objeto de origem deve fornecer bytes")
        return payload

    def _parse_records(self, payload: bytes) -> tuple[Record, ...]:
        try:
            text = payload.decode(self.encoding)
        except UnicodeDecodeError as exc:
            raise MalformedSourceError("o CSV deve usar codificação UTF-8") from exc

        reader = csv.reader(StringIO(text, newline=""), delimiter=self.delimiter)
        try:
            headers = next(reader)
        except StopIteration as exc:
            raise MalformedSourceError("o CSV não possui cabeçalho") from exc

        missing_columns = [
            column for column in self._required_columns if column not in headers
        ]
        if missing_columns:
            raise MalformedSourceError(
                "o CSV não possui todas as colunas obrigatórias"
            )

        normalized_headers = _normalize_headers(headers)
        records: list[Record] = []
        for line_number, row in enumerate(reader, start=2):
            if not row:
                continue
            if len(row) != len(normalized_headers):
                raise MalformedSourceError(
                    f"quantidade de campos inválida na linha {line_number}"
                )
            records.append(dict(zip(normalized_headers, row, strict=True)))

        return tuple(records)


class PesquisasExtractor(CsvObjectExtractor):
    """Extrai a fonte `pesquisas` sem modificar o objeto no MinIO."""

    def __init__(
        self,
        *,
        object_reader: ObjectReader,
        object_reference: ObjectReference,
    ) -> None:
        super().__init__(
            source="pesquisas",
            schema_version="1",
            required_columns=PESQUISAS_REQUIRED_COLUMNS,
            object_reader=object_reader,
            object_reference=object_reference,
        )


class EmpresasExtractor(CsvObjectExtractor):
    """Extrai a fonte `empresas` sem modificar o objeto no MinIO."""

    def __init__(
        self,
        *,
        object_reader: ObjectReader,
        object_reference: ObjectReference,
    ) -> None:
        super().__init__(
            source="empresas",
            schema_version="1",
            required_columns=EMPRESAS_REQUIRED_COLUMNS,
            object_reader=object_reader,
            object_reference=object_reference,
        )


class ClientesExtractor(CsvObjectExtractor):
    """Extrai `clientes` preservando identificadores e campos da origem."""

    def __init__(
        self,
        *,
        object_reader: ObjectReader,
        object_reference: ObjectReference,
    ) -> None:
        super().__init__(
            source="clientes",
            schema_version="1",
            required_columns=CLIENTES_REQUIRED_COLUMNS,
            object_reader=object_reader,
            object_reference=object_reference,
        )


class RespondentesExtractor(CsvObjectExtractor):
    """Extrai `respondentes` sem alterar os componentes da chave candidata."""

    def __init__(
        self,
        *,
        object_reader: ObjectReader,
        object_reference: ObjectReference,
    ) -> None:
        super().__init__(
            source="respondentes",
            schema_version="1",
            required_columns=RESPONDENTES_REQUIRED_COLUMNS,
            object_reader=object_reader,
            object_reference=object_reference,
        )
