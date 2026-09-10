from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    file_name: str
    expected_rows: int
    key_columns: tuple[str, ...]
    expected_source_header: tuple[str, ...]


DATASETS: tuple[DatasetSpec, ...] = (
    DatasetSpec(
        name="clientes",
        file_name="clientes.csv",
        expected_rows=5430,
        key_columns=("id_cliente",),
        expected_source_header=(
            "id_cliente",
            "id_empresa",
            "cargo",
            "departamento",
            "e-mail",
        ),
    ),
    DatasetSpec(
        name="empresas",
        file_name="empresas.csv",
        expected_rows=779,
        key_columns=("id_empresa",),
        expected_source_header=(
            "ID",
            "Nome Fantasia",
            "% de mercado",
            "Nacionalidade",
            "Associado",
            "Tipo de Associado",
            "Cidade",
            "Estado",
            "Pa\u00eds",
        ),
    ),
    DatasetSpec(
        name="pesquisas",
        file_name="pesquisas.csv",
        expected_rows=366,
        key_columns=("id_pesquisa",),
        expected_source_header=(
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
            "dia da semana de lan\u00e7amento",
            "dias \u00fateis aberta",
            "dias entre a solicita\u00e7\u00e3o e a divulga\u00e7\u00e3o",
            "dias para tabula\u00e7\u00e3o",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ),
    ),
    DatasetSpec(
        name="questoes",
        file_name="questoes.csv",
        expected_rows=231,
        key_columns=("id_pergunta",),
        expected_source_header=(
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
        ),
    ),
    DatasetSpec(
        name="respondentes",
        file_name="respondentes.csv",
        expected_rows=18735,
        key_columns=("id_pesq", "id_empresa", "id_cliente"),
        expected_source_header=(
            "id_pesq",
            "hora_inicio",
            "hora_termino",
            "id_empresa",
            "market_share",
            "id_cliente",
        ),
    ),
    DatasetSpec(
        name="respostas",
        file_name="respostas.csv",
        expected_rows=20607,
        key_columns=("id_resposta",),
        expected_source_header=(
            "id_resposta",
            "pesquisa_id",
            "id_pergunta",
            "respondent_id",
            "id_empresa",
            "alternativa",
            "linha_matriz",
            "coluna_matriz",
            "valor",
        ),
    ),
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_source_dir() -> Path:
    return project_root() / "local" / "input"


def dataset_by_name(name: str) -> DatasetSpec:
    for dataset in DATASETS:
        if dataset.name == name:
            return dataset
    raise KeyError(f"Dataset desconhecido: {name}")


def schema_path(dataset: DatasetSpec) -> Path:
    return project_root() / "nifi" / "schemas" / f"{dataset.name}.avsc"


def schema_fields(dataset: DatasetSpec) -> list[str]:
    payload = json.loads(schema_path(dataset).read_text(encoding="utf-8"))
    return [field["name"] for field in payload["fields"]]
