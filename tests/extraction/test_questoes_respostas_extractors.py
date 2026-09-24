from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.extraction import (  # noqa: E402
    QUESTOES_REQUIRED_COLUMNS,
    RESPOSTAS_REQUIRED_COLUMNS,
    MalformedSourceError,
    ObjectReference,
    QuestoesExtractor,
    RespostasExtractor,
)
from tests.extraction.helpers import MemoryObjectReader, csv_payload  # noqa: E402


def _values_for(
    columns: tuple[str, ...],
    **overrides: str,
) -> list[str]:
    values = {column: "" for column in columns}
    values.update(overrides)
    return [values[column] for column in columns]


class QuestoesRespostasExtractorTests(unittest.TestCase):
    def test_questoes_exposes_variable_fields_in_stable_structure(self) -> None:
        payload = csv_payload(
            QUESTOES_REQUIRED_COLUMNS,
            [
                _values_for(
                    QUESTOES_REQUIRED_COLUMNS,
                    id_pergunta="0007",
                    pesquisa_id="0414",
                    tipo="matriz_avaliacao",
                    alternativas="Opção A | Opção B",
                    linhas_matriz="Linha 1 | Linha 2",
                    colunas_matriz="Coluna 1 | Coluna 2",
                )
            ],
        )
        batch = next(
            QuestoesExtractor(
                object_reader=MemoryObjectReader(payload),
                object_reference=ObjectReference(
                    bucket="sindusfarma-data",
                    key="landing/questoes.csv",
                ),
            ).read(run_id="run-questoes", task_id="task-questoes")
        )

        record = batch.records[0]
        self.assertEqual(record["id_pergunta"], "0007")
        self.assertEqual(record["alternativas"], "Opção A | Opção B")
        self.assertEqual(
            record["estrutura"],
            {
                "alternativas": ("Opção A", "Opção B"),
                "linhas_matriz": ("Linha 1", "Linha 2"),
                "colunas_matriz": ("Coluna 1", "Coluna 2"),
            },
        )
        self.assertEqual(batch.metadata.source, "questoes")
        self.assertEqual(batch.metadata.task_id, "task-questoes")

    def test_questoes_uses_empty_sequences_for_non_applicable_fields(self) -> None:
        payload = csv_payload(
            QUESTOES_REQUIRED_COLUMNS,
            [
                _values_for(
                    QUESTOES_REQUIRED_COLUMNS,
                    id_pergunta="8",
                    pesquisa_id="414",
                    tipo="aberta",
                )
            ],
        )
        batch = next(
            QuestoesExtractor(
                object_reader=MemoryObjectReader(payload),
                object_reference=ObjectReference(
                    bucket="sindusfarma-data",
                    key="landing/questoes.csv",
                ),
            ).read(run_id="run-questao-aberta", task_id="task-questao-aberta")
        )

        self.assertEqual(
            batch.records[0]["estrutura"],
            {
                "alternativas": (),
                "linhas_matriz": (),
                "colunas_matriz": (),
            },
        )

    def test_respostas_exposes_matrix_content_in_stable_structure(self) -> None:
        payload = csv_payload(
            RESPOSTAS_REQUIRED_COLUMNS,
            [
                _values_for(
                    RESPOSTAS_REQUIRED_COLUMNS,
                    id_resposta="000123",
                    pesquisa_id="0414",
                    id_pergunta="0007",
                    respondent_id="respondent-synthetic",
                    id_empresa="0060",
                    alternativa="Alternativa sintética",
                    linha_matriz="Linha sintética",
                    coluna_matriz="Coluna sintética",
                    valor="5",
                )
            ],
        )
        batch = next(
            RespostasExtractor(
                object_reader=MemoryObjectReader(payload),
                object_reference=ObjectReference(
                    bucket="sindusfarma-data",
                    key="landing/respostas.csv",
                ),
            ).read(run_id="run-respostas", task_id="task-respostas")
        )

        record = batch.records[0]
        self.assertEqual(record["id_resposta"], "000123")
        self.assertEqual(record["linha_matriz"], "Linha sintética")
        self.assertEqual(
            record["conteudo"],
            {
                "alternativa": "Alternativa sintética",
                "linha_matriz": "Linha sintética",
                "coluna_matriz": "Coluna sintética",
                "valor": "5",
            },
        )
        self.assertEqual(batch.metadata.source, "respostas")
        self.assertEqual(batch.metadata.task_id, "task-respostas")

    def test_respostas_represents_non_applicable_fields_as_none(self) -> None:
        sensitive_value = "conteúdo sintético reservado"
        payload = csv_payload(
            RESPOSTAS_REQUIRED_COLUMNS,
            [
                _values_for(
                    RESPOSTAS_REQUIRED_COLUMNS,
                    id_resposta="124",
                    pesquisa_id="414",
                    id_pergunta="8",
                    respondent_id="respondent-synthetic",
                    valor=sensitive_value,
                )
            ],
        )
        batch = next(
            RespostasExtractor(
                object_reader=MemoryObjectReader(payload),
                object_reference=ObjectReference(
                    bucket="sindusfarma-data",
                    key="landing/respostas.csv",
                ),
            ).read(run_id="run-resposta-aberta", task_id="task-resposta-aberta")
        )

        self.assertEqual(
            batch.records[0]["conteudo"],
            {
                "alternativa": None,
                "linha_matriz": None,
                "coluna_matriz": None,
                "valor": sensitive_value,
            },
        )
        self.assertNotIn(sensitive_value, str(batch.as_attributes()))

    def test_respostas_rejects_missing_required_column(self) -> None:
        incomplete_columns = tuple(
            column for column in RESPOSTAS_REQUIRED_COLUMNS if column != "valor"
        )
        extractor = RespostasExtractor(
            object_reader=MemoryObjectReader(csv_payload(incomplete_columns, [])),
            object_reference=ObjectReference(
                bucket="sindusfarma-data",
                key="landing/respostas.csv",
            ),
        )

        with self.assertRaisesRegex(MalformedSourceError, "colunas obrigatórias"):
            list(extractor.read(run_id="run-invalid-respostas", task_id="task-invalid-respostas"))


if __name__ == "__main__":
    unittest.main()
