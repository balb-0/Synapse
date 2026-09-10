"""Extratores CSV das fontes publicadas no MinIO."""

from __future__ import annotations

import csv
import hashlib
import re
from collections.abc import Iterator
from datetime import UTC, datetime
from io import TextIOWrapper
from itertools import islice
from tempfile import SpooledTemporaryFile
from typing import BinaryIO

from .contracts import (
    BatchMetadata,
    ExtractedBatch,
    ExtractionCheckpoint,
    Record,
)
from .failures import FailureCategory
from .log_events import (
    ExtractionBatchLogEvent,
    ExtractionLogSink,
    StandardLoggingSink,
)
from .object_storage import ObjectReader, ObjectReference
from .resilience import RetryExecutor


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

DEFAULT_BATCH_SIZE = 1000
SOURCE_READ_CHUNK_SIZE = 1024 * 1024
SPOOL_MEMORY_LIMIT_BYTES = 8 * 1024 * 1024
CHECKPOINT_POSITION_PATTERN = re.compile(r"row:(0|[1-9][0-9]*)")


class ExtractionError(RuntimeError):
    """Erro conhecido durante a leitura de uma fonte."""


class MalformedSourceError(ExtractionError):
    """A fonte não pode ser interpretada segundo seu contrato CSV."""

    failure_category = FailureCategory.MALFORMED


class InvalidCheckpointError(ExtractionError):
    """O checkpoint não pode ser aplicado à fonte informada."""


class StaleCheckpointError(InvalidCheckpointError):
    """O checkpoint pertence a outra versão do objeto de origem."""


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
    """Lê um CSV do MinIO e produz páginas retomáveis no contrato comum."""

    delimiter = ";"
    encoding = "utf-8-sig"
    source_name = ""
    schema_version = "1"
    required_columns: tuple[str, ...] = ()

    def __init__(
        self,
        *,
        object_reader: ObjectReader,
        object_reference: ObjectReference,
        batch_size: int = DEFAULT_BATCH_SIZE,
        retry_executor: RetryExecutor | None = None,
        log_sink: ExtractionLogSink | None = None,
    ) -> None:
        if not self.source_name or not self.required_columns:
            raise TypeError(
                "o extrator CSV deve declarar fonte e colunas obrigatórias"
            )
        if isinstance(batch_size, bool) or not isinstance(batch_size, int):
            raise ValueError("batch_size deve ser um inteiro positivo")
        if batch_size <= 0:
            raise ValueError("batch_size deve ser um inteiro positivo")

        self._object_reader = object_reader
        self._object_reference = object_reference
        self._batch_size = batch_size
        self._retry_executor = retry_executor or RetryExecutor()
        self._log_sink = log_sink or StandardLoggingSink()

    @property
    def source(self) -> str:
        return self.source_name

    @property
    def batch_size(self) -> int:
        return self._batch_size

    def read(
        self,
        *,
        run_id: str,
        checkpoint: ExtractionCheckpoint | None = None,
    ) -> Iterator[ExtractedBatch]:
        if not run_id or not run_id.strip():
            raise ValueError("run_id não pode ser vazio")

        started_at = datetime.now(UTC)
        resume_row, next_sequence = self._checkpoint_position(checkpoint)

        with SpooledTemporaryFile(
            max_size=SPOOL_MEMORY_LIMIT_BYTES,
            mode="w+b",
        ) as buffered_source:
            byte_count, source_version = self._buffer_source(buffered_source)
            self._validate_source_version(checkpoint, source_version)
            buffered_source.seek(0)
            try:
                yield from self._read_batches(
                    buffered_source=buffered_source,
                    run_id=run_id,
                    started_at=started_at,
                    byte_count=byte_count,
                    source_version=source_version,
                    resume_row=resume_row,
                    next_sequence=next_sequence,
                    emit_empty_batch=checkpoint is None,
                )
            except MalformedSourceError as exc:
                self._retry_executor.record_failure(
                    exc,
                    source=self.source,
                    operation_name="parse",
                )
                raise

    def _buffer_source(self, destination: BinaryIO) -> tuple[int, str]:
        return self._retry_executor.execute(
            lambda: self._read_source_once(destination),
            source=self.source,
            operation_name="read",
        )

    def _read_source_once(self, destination: BinaryIO) -> tuple[int, str]:
        destination.seek(0)
        destination.truncate(0)
        digest = hashlib.sha256()
        byte_count = 0

        with self._object_reader.open(self._object_reference) as stream:
            while True:
                chunk = stream.read(SOURCE_READ_CHUNK_SIZE)
                if not isinstance(chunk, bytes):
                    raise MalformedSourceError(
                        "o objeto de origem deve fornecer bytes"
                    )
                if not chunk:
                    break
                destination.write(chunk)
                digest.update(chunk)
                byte_count += len(chunk)

        return byte_count, "sha256:" + digest.hexdigest()

    def _checkpoint_position(
        self,
        checkpoint: ExtractionCheckpoint | None,
    ) -> tuple[int, int]:
        if checkpoint is None:
            return 0, 1
        if checkpoint.source != self.source:
            raise InvalidCheckpointError("checkpoint pertence a outra fonte")

        match = CHECKPOINT_POSITION_PATTERN.fullmatch(checkpoint.position)
        if match is None:
            raise InvalidCheckpointError("posição de checkpoint CSV inválida")
        return int(match.group(1)), checkpoint.sequence + 1

    def _validate_source_version(
        self,
        checkpoint: ExtractionCheckpoint | None,
        source_version: str,
    ) -> None:
        if checkpoint is None:
            return
        if checkpoint.source_version is None:
            raise InvalidCheckpointError(
                "checkpoint CSV não informa a versão da fonte"
            )
        if checkpoint.source_version != source_version:
            raise StaleCheckpointError("a fonte mudou desde o checkpoint confirmado")

    def _read_batches(
        self,
        *,
        buffered_source: BinaryIO,
        run_id: str,
        started_at: datetime,
        byte_count: int,
        source_version: str,
        resume_row: int,
        next_sequence: int,
        emit_empty_batch: bool,
    ) -> Iterator[ExtractedBatch]:
        text_stream = TextIOWrapper(buffered_source, encoding=self.encoding, newline="")
        try:
            reader = csv.reader(text_stream, delimiter=self.delimiter)
            records = self._record_iterator(reader)
            self._skip_confirmed_records(records, resume_row)
            yielded = False
            current_row = resume_row
            sequence = next_sequence

            while batch_records := tuple(islice(records, self.batch_size)):
                yielded = True
                current_row += len(batch_records)
                yield self._build_batch(
                    records=batch_records,
                    run_id=run_id,
                    started_at=started_at,
                    byte_count=byte_count,
                    source_version=source_version,
                    current_row=current_row,
                    sequence=sequence,
                )
                sequence += 1

            if not yielded and resume_row == 0 and emit_empty_batch:
                yield self._build_batch(
                    records=(),
                    run_id=run_id,
                    started_at=started_at,
                    byte_count=byte_count,
                    source_version=source_version,
                    current_row=0,
                    sequence=next_sequence,
                )
        except UnicodeDecodeError as exc:
            raise MalformedSourceError("o CSV deve usar codificação UTF-8") from exc
        except csv.Error as exc:
            raise MalformedSourceError("o CSV possui estrutura inválida") from exc
        finally:
            text_stream.detach()

    def _record_iterator(
        self,
        reader: Iterator[list[str]],
    ) -> Iterator[Record]:
        try:
            headers = next(reader)
        except StopIteration as exc:
            raise MalformedSourceError("o CSV não possui cabeçalho") from exc

        missing_columns = [
            column for column in self.required_columns if column not in headers
        ]
        if missing_columns:
            raise MalformedSourceError(
                "o CSV não possui todas as colunas obrigatórias"
            )

        normalized_headers = _normalize_headers(headers)
        for line_number, row in enumerate(reader, start=2):
            if not row:
                continue
            if len(row) != len(normalized_headers):
                raise MalformedSourceError(
                    f"quantidade de campos inválida na linha {line_number}"
                )
            record = dict(zip(normalized_headers, row, strict=True))
            yield self._prepare_record(record)

    def _skip_confirmed_records(
        self,
        records: Iterator[Record],
        resume_row: int,
    ) -> None:
        for _ in range(resume_row):
            try:
                next(records)
            except StopIteration as exc:
                raise InvalidCheckpointError(
                    "checkpoint está além do fim da fonte"
                ) from exc

    def _build_batch(
        self,
        *,
        records: tuple[Record, ...],
        run_id: str,
        started_at: datetime,
        byte_count: int,
        source_version: str,
        current_row: int,
        sequence: int,
    ) -> ExtractedBatch:
        checkpoint = ExtractionCheckpoint(
            source=self.source,
            position=f"row:{current_row}",
            sequence=sequence,
            source_version=source_version,
        )
        metadata = BatchMetadata(
            source=self.source,
            run_id=run_id,
            task_id=f"extract-{self.source}",
            batch_id=f"{self.source}-{sequence:06d}",
            started_at=started_at,
            finished_at=datetime.now(UTC),
            record_count=len(records),
            byte_count=byte_count,
            schema_version=self.schema_version,
            source_checksum=source_version,
        )
        batch = ExtractedBatch(
            records=records,
            checkpoint=checkpoint,
            metadata=metadata,
        )
        self._log_sink.emit(ExtractionBatchLogEvent.from_batch(batch))
        return batch

    def _prepare_record(self, record: dict[str, str]) -> Record:
        """Permite especializar apenas a representação entregue pelo extrator."""

        return record


class PesquisasExtractor(CsvObjectExtractor):
    """Extrai a fonte `pesquisas` sem modificar o objeto no MinIO."""

    source_name = "pesquisas"
    required_columns = PESQUISAS_REQUIRED_COLUMNS


class EmpresasExtractor(CsvObjectExtractor):
    """Extrai a fonte `empresas` sem modificar o objeto no MinIO."""

    source_name = "empresas"
    required_columns = EMPRESAS_REQUIRED_COLUMNS


class ClientesExtractor(CsvObjectExtractor):
    """Extrai `clientes` preservando identificadores e campos da origem."""

    source_name = "clientes"
    required_columns = CLIENTES_REQUIRED_COLUMNS


class RespondentesExtractor(CsvObjectExtractor):
    """Extrai `respondentes` sem alterar os componentes da chave candidata."""

    source_name = "respondentes"
    required_columns = RESPONDENTES_REQUIRED_COLUMNS
