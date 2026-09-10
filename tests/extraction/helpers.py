"""Fixtures reutilizáveis dos testes de extração."""

from __future__ import annotations

import csv
from collections.abc import Iterator
from contextlib import contextmanager
from io import BytesIO, StringIO
from typing import BinaryIO

from etl.extraction import ObjectReference


def csv_payload(headers: tuple[str, ...], rows: list[list[str]]) -> bytes:
    stream = StringIO(newline="")
    writer = csv.writer(stream, delimiter=";", lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


class MemoryObjectReader:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.opened_references: list[ObjectReference] = []

    @contextmanager
    def open(self, reference: ObjectReference) -> Iterator[BinaryIO]:
        self.opened_references.append(reference)
        yield BytesIO(self.payload)

