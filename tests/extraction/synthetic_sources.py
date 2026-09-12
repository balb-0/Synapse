"""Fixtures mínimas e inteiramente sintéticas para os seis extratores."""

from __future__ import annotations

from dataclasses import dataclass

from etl.extraction import (
    CLIENTES_REQUIRED_COLUMNS,
    EMPRESAS_REQUIRED_COLUMNS,
    PESQUISAS_REQUIRED_COLUMNS,
    QUESTOES_REQUIRED_COLUMNS,
    RESPONDENTES_REQUIRED_COLUMNS,
    RESPOSTAS_REQUIRED_COLUMNS,
    ClientesExtractor,
    CsvObjectExtractor,
    EmpresasExtractor,
    PesquisasExtractor,
    QuestoesExtractor,
    RespondentesExtractor,
    RespostasExtractor,
)
from tests.extraction.helpers import csv_payload


@dataclass(frozen=True, slots=True)
class SyntheticSource:
    source: str
    extractor_type: type[CsvObjectExtractor]
    headers: tuple[str, ...]
    expected_records: int

    def payload(self) -> bytes:
        rows = [
            [
                _synthetic_value(self.source, row_number, column, column_number)
                for column_number, column in enumerate(self.headers, start=1)
            ]
            for row_number in range(1, self.expected_records + 1)
        ]
        return csv_payload(self.headers, rows)


def _synthetic_value(
    source: str,
    row_number: int,
    column: str,
    column_number: int,
) -> str:
    if column == "e-mail":
        return f"synthetic-{row_number}@example.invalid"
    if column in {"alternativas", "linhas_matriz", "colunas_matriz"}:
        return f"synthetic-{source}-{row_number}-a | synthetic-{source}-{row_number}-b"
    return f"synthetic-{source}-{row_number}-{column_number}"


SYNTHETIC_SOURCES = (
    SyntheticSource(
        source="pesquisas",
        extractor_type=PesquisasExtractor,
        headers=PESQUISAS_REQUIRED_COLUMNS,
        expected_records=2,
    ),
    SyntheticSource(
        source="empresas",
        extractor_type=EmpresasExtractor,
        headers=EMPRESAS_REQUIRED_COLUMNS,
        expected_records=3,
    ),
    SyntheticSource(
        source="clientes",
        extractor_type=ClientesExtractor,
        headers=CLIENTES_REQUIRED_COLUMNS,
        expected_records=4,
    ),
    SyntheticSource(
        source="respondentes",
        extractor_type=RespondentesExtractor,
        headers=RESPONDENTES_REQUIRED_COLUMNS,
        expected_records=2,
    ),
    SyntheticSource(
        source="questoes",
        extractor_type=QuestoesExtractor,
        headers=QUESTOES_REQUIRED_COLUMNS,
        expected_records=3,
    ),
    SyntheticSource(
        source="respostas",
        extractor_type=RespostasExtractor,
        headers=RESPOSTAS_REQUIRED_COLUMNS,
        expected_records=5,
    ),
)
