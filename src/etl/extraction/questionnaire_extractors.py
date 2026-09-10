"""Extratores das estruturas variáveis de questões e respostas."""

from __future__ import annotations

from .contracts import Record
from .csv_extractors import CsvObjectExtractor


QUESTOES_REQUIRED_COLUMNS = (
    "id_pergunta",
    "pesquisa_id",
    "pesquisa_titulo",
    "enunciado",
    "tipo",
    "qtd_alternativas",
    "alternativas",
    "linhas_matriz",
    "colunas_matriz",
    "confianca",
    "formato_arquivo",
    "col_origem",
    "observacoes",
)

RESPOSTAS_REQUIRED_COLUMNS = (
    "id_resposta",
    "pesquisa_id",
    "id_pergunta",
    "respondent_id",
    "id_empresa",
    "alternativa",
    "linha_matriz",
    "coluna_matriz",
    "valor",
)

VARIABLE_FIELD_SEPARATOR = " | "


def _split_variable_field(value: str) -> tuple[str, ...]:
    """Expõe listas delimitadas sem descartar o valor recebido da fonte."""

    if not value.strip():
        return ()
    return tuple(item.strip() for item in value.split(VARIABLE_FIELD_SEPARATOR))


class QuestoesExtractor(CsvObjectExtractor):
    """Extrai questões e explicita suas listas em uma estrutura estável."""

    source_name = "questoes"
    required_columns = QUESTOES_REQUIRED_COLUMNS

    def _prepare_record(self, record: dict[str, str]) -> Record:
        prepared: dict[str, object] = dict(record)
        prepared["estrutura"] = {
            "alternativas": _split_variable_field(record["alternativas"]),
            "linhas_matriz": _split_variable_field(record["linhas_matriz"]),
            "colunas_matriz": _split_variable_field(record["colunas_matriz"]),
        }
        return prepared


class RespostasExtractor(CsvObjectExtractor):
    """Extrai respostas atômicas com uma forma estável para o conteúdo."""

    source_name = "respostas"
    required_columns = RESPOSTAS_REQUIRED_COLUMNS

    def _prepare_record(self, record: dict[str, str]) -> Record:
        prepared: dict[str, object] = dict(record)
        prepared["conteudo"] = {
            field: record[field] or None
            for field in (
                "alternativa",
                "linha_matriz",
                "coluna_matriz",
                "valor",
            )
        }
        return prepared
