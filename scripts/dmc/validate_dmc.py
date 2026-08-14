#!/usr/bin/env python3
"""Valida o recorte da Sprint 1 no JSON do Data Model Canvas."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


EXPECTED_CUBES = (
    "Ciclo de Vida das Pesquisas",
    "Adesão e Participação",
    "Desempenho Operacional",
    "Qualidade e Publicação",
)
EXPECTED_CUBE_IDS = ("cubo-1", "cubo-2", "cubo-3", "cubo-4")
REQUIRED_TOP_LEVEL = (
    "schemaVersion",
    "metadata",
    "negocioEConsumo",
    "governancaCorporativa",
    "cubos",
)
CORPORATE_LISTS = (
    "objetivosNegocio",
    "perguntasNegocio",
    "processosNegocio",
    "indicadoresConsumo",
    "usuariosCanais",
    "decisoesRiscos",
)
GOVERNANCE_KEYS = (
    "owner",
    "steward",
    "custodian",
    "tecnico",
    "lgpd",
    "seg",
    "comp",
    "etico",
    "catalogo",
    "kpis",
    "maturidade",
    "evolucao",
)
DIMENSIONAL_LISTS = ("grao", "fatos", "metricas", "dimensoes")
DATA_GOVERNANCE_LISTS = ("fontes", "transformacoes", "qualidade", "scd")
DATA_GOVERNANCE_FIELDS = (
    "particionamento",
    "materializacoesAgregacoes",
    "indicesClusteringOrdenacao",
    "queriesCriticas",
    "classificacaoPublico",
    "classificacaoInterno",
    "classificacaoConfidencial",
    "classificacaoRestrito",
    "dadoPessoal",
    "dadoSensivel",
    "dadoCritico",
    "criticidade",
    "perfisAutorizados",
    "controleAcesso",
    "trilhaAuditoria",
    "retencao",
    "arquivamento",
    "descarte",
    "metadadosObrigatorios",
    "kpiQualidade",
    "kpiGovernanca",
)
class DmcValidationError(ValueError):
    """Indica uma divergência estrutural no canvas exportado."""


def load_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DmcValidationError(f"JSON inválido em {path}: {error}") from error
    if not isinstance(document, dict):
        raise DmcValidationError("a raiz do JSON deve ser um objeto")
    return document


def _nonempty_strings(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item.strip() for item in value)
    )


def _semantically_empty(value: Any) -> bool:
    return value is None or value == "" or value is False or (
        isinstance(value, list)
        and all(item is None or item == "" or item is False for item in value)
    )


def validate_document(document: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in REQUIRED_TOP_LEVEL if key not in document]
    if missing:
        raise DmcValidationError(f"seções obrigatórias ausentes: {', '.join(missing)}")
    if type(document["schemaVersion"]) is not int or document["schemaVersion"] != 1:
        raise DmcValidationError("schemaVersion deve ser 1")

    metadata = document["metadata"]
    if not isinstance(metadata, dict) or not all(
        isinstance(metadata.get(key), str) and metadata[key].strip()
        for key in ("parceiro", "data", "versao", "grupo")
    ):
        raise DmcValidationError("metadata deve preservar parceiro, data, versão e grupo")

    business = document["negocioEConsumo"]
    if not isinstance(business, dict) or not all(
        _nonempty_strings(business.get(key)) for key in CORPORATE_LISTS
    ):
        raise DmcValidationError("Negócio e Consumo Analítico perderam conteúdo obrigatório")

    governance = document["governancaCorporativa"]
    if not isinstance(governance, dict) or any(
        key not in governance for key in GOVERNANCE_KEYS
    ) or not all(
        isinstance(governance[key], str) and governance[key].strip()
        for key in GOVERNANCE_KEYS
    ):
        raise DmcValidationError("Governança Corporativa deve permanecer preenchida")

    cubes = document["cubos"]
    if not isinstance(cubes, list) or len(cubes) != len(EXPECTED_CUBES):
        raise DmcValidationError(f"o canvas deve conter {len(EXPECTED_CUBES)} cubos")

    ids = [cube.get("id") for cube in cubes if isinstance(cube, dict)]
    if len(ids) != len(cubes) or any(not isinstance(value, str) or not value for value in ids):
        raise DmcValidationError("todo cubo deve ter um ID não vazio")
    if len(set(ids)) != len(ids):
        raise DmcValidationError("os IDs dos cubos devem ser únicos")
    if tuple(ids) != EXPECTED_CUBE_IDS:
        raise DmcValidationError("os IDs dos cubos divergem do contrato da Sprint")

    names: list[str] = []
    for cube in cubes:
        fields = cube.get("fields")
        lists = cube.get("lists")
        if not isinstance(fields, dict) or not isinstance(lists, dict):
            raise DmcValidationError(f"cubo {cube['id']} deve conter fields e lists")

        name = fields.get("nome")
        if not isinstance(name, str) or not name.strip():
            raise DmcValidationError(f"cubo {cube['id']} deve ter nome")
        names.append(name)

        schemas = (
            fields.get("starSchema") is True,
            fields.get("snowflakeSchema") is True,
            isinstance(fields.get("outroSchema"), str) and bool(fields["outroSchema"].strip()),
        )
        if sum(schemas) != 1:
            raise DmcValidationError(f"cubo {name} deve selecionar exatamente um esquema")

        fact_types = (
            fields.get("transactionFact") is True,
            fields.get("periodicSnapshot") is True,
            fields.get("accumulatingSnapshot") is True,
        )
        if sum(fact_types) != 1:
            raise DmcValidationError(f"cubo {name} deve selecionar exatamente um tipo de fato")

        for key in DIMENSIONAL_LISTS:
            if not _nonempty_strings(lists.get(key)):
                raise DmcValidationError(f"cubo {name} deve preencher {key}")
        for key in DATA_GOVERNANCE_LISTS:
            if key not in lists or not _semantically_empty(lists[key]):
                raise DmcValidationError(f"cubo {name} preencheu Dados/Governança em {key}")
        for key in DATA_GOVERNANCE_FIELDS:
            if key not in fields or not _semantically_empty(fields[key]):
                raise DmcValidationError(f"cubo {name} preencheu Dados/Governança em {key}")

    if tuple(names) != EXPECTED_CUBES:
        raise DmcValidationError("nomes ou ordem dos cubos divergem do contrato da Sprint")
    return {"schemaVersion": 1, "cubos": names}


def validate_preserved_sections(
    document: dict[str, Any], baseline: dict[str, Any]
) -> None:
    changed = sorted(set(document) | set(baseline)) if document != baseline else []
    if changed:
        changed = [key for key in changed if document.get(key) != baseline.get(key)]
    if changed:
        raise DmcValidationError(
            f"round-trip alterou o documento nas seções: {', '.join(changed)}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=Path("docs/dmc.json"))
    parser.add_argument(
        "--baseline",
        type=Path,
        help="exportação anterior usada para conferir as seções preservadas",
    )
    args = parser.parse_args()

    try:
        document = load_document(args.path)
        summary = validate_document(document)
        if args.baseline:
            validate_preserved_sections(document, load_document(args.baseline))
    except DmcValidationError as error:
        print(f"DMC inválido: {error}", file=sys.stderr)
        return 1

    print(
        f"DMC válido: schema {summary['schemaVersion']}; "
        f"{len(summary['cubos'])} cubos; Dados/Governança dos cubos vazios"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
