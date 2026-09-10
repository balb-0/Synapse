#!/usr/bin/env python3
"""Gera um inventário reproduzível do Data Model Canvas versionado."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPECTED_CUBE_COUNT = 4
REQUIRED_TOP_LEVEL = (
    "schemaVersion",
    "metadata",
    "negocioEConsumo",
    "governancaCorporativa",
    "cubos",
)
REQUIRED_CUBE_LISTS = (
    "grao",
    "fatos",
    "metricas",
    "dimensoes",
    "fontes",
    "transformacoes",
    "qualidade",
    "scd",
)
REQUIRED_DATA_GOVERNANCE_FIELDS = (
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


def load_document(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("a raiz do DMC deve ser um objeto JSON")
    return document


def build_inventory(document: dict[str, Any]) -> dict[str, Any]:
    cubes = document.get("cubos")
    cube_list = cubes if isinstance(cubes, list) else []
    missing_top_level = [key for key in REQUIRED_TOP_LEVEL if key not in document]

    cube_inventory: list[dict[str, Any]] = []
    for position, cube in enumerate(cube_list, start=1):
        if not isinstance(cube, dict):
            cube_inventory.append(
                {
                    "position": position,
                    "id": None,
                    "name": None,
                    "missing_cube_lists": list(REQUIRED_CUBE_LISTS),
                    "missing_data_governance_fields": list(
                        REQUIRED_DATA_GOVERNANCE_FIELDS
                    ),
                }
            )
            continue

        fields = cube.get("fields") if isinstance(cube.get("fields"), dict) else {}
        lists = cube.get("lists") if isinstance(cube.get("lists"), dict) else {}
        missing_lists = [
            key for key in REQUIRED_CUBE_LISTS if not lists.get(key)
        ]
        missing_fields = [
            key for key in REQUIRED_DATA_GOVERNANCE_FIELDS if key not in fields
        ]
        cube_inventory.append(
            {
                "position": position,
                "id": cube.get("id"),
                "name": fields.get("nome"),
                "missing_cube_lists": missing_lists,
                "missing_data_governance_fields": missing_fields,
            }
        )

    metadata = document.get("metadata")
    governance = document.get("governancaCorporativa")
    blank_governance = []
    if isinstance(governance, dict):
        blank_governance = [
            key for key, value in governance.items() if not str(value).strip()
        ]

    return {
        "schema_version": document.get("schemaVersion"),
        "metadata": metadata if isinstance(metadata, dict) else {},
        "missing_top_level": missing_top_level,
        "cube_count": len(cube_list),
        "expected_cube_count": EXPECTED_CUBE_COUNT,
        "cube_count_matches": len(cube_list) == EXPECTED_CUBE_COUNT,
        "blank_governance_fields": blank_governance,
        "cubes": cube_inventory,
    }


def render_markdown(inventory: dict[str, Any], source: Path) -> str:
    metadata = inventory["metadata"]
    lines = [
        "# Inventário do Data Model Canvas",
        "",
        f"- Fonte: `{source.as_posix()}`",
        f"- `schemaVersion`: `{inventory['schema_version']}`",
        f"- Versão declarada: `{metadata.get('versao', 'não informada')}`",
        f"- Data declarada: `{metadata.get('data', 'não informada')}`",
        (
            f"- Cubos: `{inventory['cube_count']}` de "
            f"`{inventory['expected_cube_count']}` esperados"
        ),
        "",
        "## Cubos",
        "",
    ]
    for cube in inventory["cubes"]:
        lines.append(f"- `{cube['id']}` — {cube['name']}")

    lines.extend(["", "## Ajustes estruturais identificados", ""])
    adjustment_start = len(lines)
    if inventory["missing_top_level"]:
        lines.append(
            "- Seções de topo ausentes: " + ", ".join(inventory["missing_top_level"])
        )
    if inventory["blank_governance_fields"]:
        lines.append(
            "- Campos de governança vazios: "
            + ", ".join(inventory["blank_governance_fields"])
        )
    for cube in inventory["cubes"]:
        if cube["missing_cube_lists"]:
            lines.append(
                f"- `{cube['id']}` não preenche: "
                + ", ".join(cube["missing_cube_lists"])
            )
        if cube["missing_data_governance_fields"]:
            lines.append(
                f"- `{cube['id']}` não preenche campos de Dados/Governança: "
                + ", ".join(cube["missing_data_governance_fields"])
            )

    if len(lines) == adjustment_start:
        lines.append("- Nenhum ajuste estrutural detectado.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=Path("docs/dmc.json"))
    parser.add_argument("--json", action="store_true", help="emite o inventário em JSON")
    args = parser.parse_args()

    inventory = build_inventory(load_document(args.path))
    if args.json:
        print(json.dumps(inventory, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(inventory, args.path), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
