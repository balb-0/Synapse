#!/usr/bin/env python3
"""Valida a cadeia PB → RF → indicador → cubo/dashboard da Sprint 1."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

EXPECTED_QUESTIONS = tuple(f"PB{number:02d}" for number in range(1, 14))
EXPECTED_REQUIREMENTS = tuple(f"RF{number:02d}" for number in range(1, 14))
EXPECTED_INDICATORS = {f"I{number:02d}" for number in range(1, 26)}
EXPECTED_DASHBOARDS = {f"D{number:02d}" for number in range(1, 5)}
EXPECTED_PENDING_QUESTIONS = {"PB10", "PB11", "PB13"}
EXPECTED_PENDING_INDICATORS = {"I12", "I13", "I15"}
EXPECTED_IMPLEMENTED_CUBES = {
    "PB01": ["C01"],
    "PB02": ["C01"],
    "PB03": ["C01"],
    "PB04": ["C02"],
    "PB05": ["C02"],
    "PB06": [],
    "PB07": [],
    "PB08": [],
    "PB09": [],
    "PB10": ["C04"],
    "PB11": ["C04"],
    "PB12": [],
    "PB13": ["C04"],
}
EXPECTED_ANALYTIC_ARTIFACTS = {
    "PB01": [],
    "PB02": [],
    "PB03": [],
    "PB04": [],
    "PB05": [],
    "PB06": ["Perfilamento de qualidade e governança"],
    "PB07": ["Perfilamento de qualidade e governança"],
    "PB08": ["Política de acesso proposta"],
    "PB09": ["Política de publicação proposta"],
    "PB10": [],
    "PB11": [],
    "PB12": ["Perfilamento de qualidade e governança"],
    "PB13": [],
}


class TraceabilityError(ValueError):
    """Indica uma lacuna ou contradição no contrato de rastreabilidade."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TraceabilityError(f"JSON inválido em {path}: {error}") from error
    if not isinstance(document, dict):
        raise TraceabilityError(f"a raiz de {path} deve ser um objeto")
    return document


def _string_list(value: Any, field: str, question: str) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise TraceabilityError(f"{question}.{field} deve ser uma lista de textos")
    if len(value) != len(set(value)):
        raise TraceabilityError(f"{question}.{field} contém duplicatas")
    return value


def _dmc_cubes(document: dict[str, Any]) -> dict[str, str]:
    cubes = document.get("cubos")
    if not isinstance(cubes, list):
        raise TraceabilityError("docs/dmc.json deve conter a lista cubos")
    result: dict[str, str] = {}
    for cube in cubes:
        if not isinstance(cube, dict) or not isinstance(cube.get("id"), str):
            raise TraceabilityError("todo cubo do DMC deve ter ID textual")
        fields = cube.get("fields")
        if not isinstance(fields, dict) or not isinstance(fields.get("nome"), str):
            raise TraceabilityError(f"cubo {cube['id']} deve ter nome textual")
        result[cube["id"]] = fields["nome"]
    return result


def _normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def validate_primary_sources(manifest: dict[str, Any], sources_dir: Path) -> dict[str, int]:
    sources = manifest.get("primarySources")
    if not isinstance(sources, list) or not sources:
        raise TraceabilityError("o manifesto deve registrar as fontes primárias")

    claim_count = 0
    seen_ids: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise TraceabilityError("cada fonte primária deve ser um objeto")
        source_id = source.get("id")
        filename = source.get("filename")
        expected_hash = source.get("sha256")
        claims = source.get("claims")
        if not all(
            isinstance(value, str) and value.strip()
            for value in (source_id, filename, expected_hash)
        ):
            raise TraceabilityError("fonte primária sem id, arquivo ou SHA-256")
        if source_id in seen_ids:
            raise TraceabilityError(f"fonte primária duplicada: {source_id}")
        seen_ids.add(source_id)
        if not isinstance(claims, list) or not claims:
            raise TraceabilityError(f"{source_id} deve registrar afirmações auditáveis")

        path = sources_dir / filename
        try:
            raw = path.read_bytes()
            content = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise TraceabilityError(f"não foi possível ler a fonte {source_id}: {error}") from error
        actual_hash = hashlib.sha256(raw).hexdigest()
        if actual_hash != expected_hash:
            raise TraceabilityError(f"SHA-256 da fonte {source_id} diverge do manifesto")

        normalized = _normalized_text(content)
        claim_ids: set[str] = set()
        for claim in claims:
            if not isinstance(claim, dict):
                raise TraceabilityError(f"afirmação inválida em {source_id}")
            claim_id, phrase = claim.get("id"), claim.get("phrase")
            if not all(isinstance(value, str) and value.strip() for value in (claim_id, phrase)):
                raise TraceabilityError(f"afirmação sem id ou trecho em {source_id}")
            if claim_id in claim_ids:
                raise TraceabilityError(f"afirmação duplicada em {source_id}: {claim_id}")
            claim_ids.add(claim_id)
            if _normalized_text(phrase) not in normalized:
                raise TraceabilityError(f"a fonte {source_id} não sustenta a afirmação {claim_id}")
            claim_count += 1

    return {"sources": len(sources), "claims": claim_count}


def _project_matrix(path: Path) -> list[list[str]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise TraceabilityError(f"não foi possível ler {path}: {error}") from error
    try:
        section = lines.index("## 5.4 Rastreabilidade Analítica")
        header = next(
            index
            for index in range(section + 1, len(lines))
            if lines[index].startswith("| Pergunta de negócio |")
        )
    except (ValueError, StopIteration) as error:
        raise TraceabilityError("docs/projeto.md não contém a matriz da §5.4") from error

    rows: list[list[str]] = []
    for line in lines[header + 2 :]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 5:
            raise TraceabilityError("linha inválida na matriz da §5.4")
        rows.append(cells)
    return rows


def validate_project_matrix(manifest: dict[str, Any], project_path: Path) -> None:
    questions = manifest["questions"]
    expected: list[list[str]] = []
    for question in questions:
        cube_cells = list(question["cubes"]) + list(question.get("artifacts", []))
        if question["pendingIndicators"]:
            pending_cube = question.get("pendingCube")
            pending_name = (
                pending_cube.get("name")
                if isinstance(pending_cube, dict) and isinstance(pending_cube.get("name"), str)
                else "extensão futura"
            )
            pending = f"{pending_name} pendente de integração futura"
            cube_cells.append(pending)
        expected.append(
            [
                question["id"],
                question["requirement"],
                ", ".join(question["indicators"]),
                "; ".join(cube_cells),
                ", ".join(question["dashboards"]),
            ]
        )
    if _project_matrix(project_path) != expected:
        raise TraceabilityError("a matriz da §5.4 diverge de scripts/traceability/manifest.json")


def validate(manifest: dict[str, Any], dmc: dict[str, Any]) -> dict[str, int]:
    if type(manifest.get("schemaVersion")) is not int or manifest["schemaVersion"] != 1:
        raise TraceabilityError("schemaVersion do manifesto deve ser 1")

    cubes = manifest.get("cubes")
    if not isinstance(cubes, dict) or set(cubes) != {"C01", "C02", "C03", "C04"}:
        raise TraceabilityError("o manifesto deve mapear exatamente C01–C04")
    dmc_cubes = _dmc_cubes(dmc)
    for cube_id, mapping in cubes.items():
        if not isinstance(mapping, dict):
            raise TraceabilityError(f"mapeamento de {cube_id} deve ser um objeto")
        dmc_id, name = mapping.get("dmcId"), mapping.get("name")
        if dmc_cubes.get(dmc_id) != name:
            raise TraceabilityError(f"{cube_id} não corresponde ao ID/nome do dmc.json")

    questions = manifest.get("questions")
    if not isinstance(questions, list) or len(questions) != len(EXPECTED_QUESTIONS):
        raise TraceabilityError("o manifesto deve conter exatamente PB01–PB13")
    ids = [item.get("id") for item in questions if isinstance(item, dict)]
    if tuple(ids) != EXPECTED_QUESTIONS:
        raise TraceabilityError("perguntas ausentes, duplicadas ou fora da ordem PB01–PB13")

    requirements: list[str] = []
    indicators: set[str] = set()
    dashboards: set[str] = set()
    pending_questions: set[str] = set()
    pending_indicators: set[str] = set()

    for position, question in enumerate(questions):
        question_id = question["id"]
        requirement = question.get("requirement")
        requirements.append(requirement)
        if requirement != EXPECTED_REQUIREMENTS[position]:
            raise TraceabilityError(
                f"{question_id} deve apontar para {EXPECTED_REQUIREMENTS[position]}"
            )

        question_indicators = _string_list(question.get("indicators"), "indicators", question_id)
        question_cubes = _string_list(question.get("cubes"), "cubes", question_id)
        question_artifacts = _string_list(question.get("artifacts", []), "artifacts", question_id)
        question_dashboards = _string_list(question.get("dashboards"), "dashboards", question_id)
        question_pending = _string_list(
            question.get("pendingIndicators"), "pendingIndicators", question_id
        )
        if not question_indicators or not question_dashboards:
            raise TraceabilityError(f"{question_id} deve ter indicador e dashboard")
        if not set(question_indicators) <= EXPECTED_INDICATORS:
            raise TraceabilityError(f"{question_id} referencia indicador desconhecido")
        if not set(question_cubes) <= set(cubes):
            raise TraceabilityError(f"{question_id} referencia cubo desconhecido")
        if question_cubes != EXPECTED_IMPLEMENTED_CUBES[question_id]:
            raise TraceabilityError(f"{question_id} diverge do vínculo dimensional aprovado")
        if question_artifacts != EXPECTED_ANALYTIC_ARTIFACTS[question_id]:
            raise TraceabilityError(f"{question_id} diverge do vínculo analítico aprovado")
        if not set(question_dashboards) <= EXPECTED_DASHBOARDS:
            raise TraceabilityError(f"{question_id} referencia dashboard desconhecido")
        if not set(question_pending) <= set(question_indicators):
            raise TraceabilityError(f"{question_id} marca indicador que não pertence à pergunta")

        pending_cube = question.get("pendingCube")
        if question_pending:
            pending_questions.add(question_id)
            pending_indicators.update(question_pending)
            if (
                not isinstance(pending_cube, dict)
                or pending_cube.get("dependency") != "Integração futura"
            ):
                raise TraceabilityError(
                    f"{question_id} deve registrar a dependência de integração futura"
                )
            if not isinstance(pending_cube.get("name"), str) or not pending_cube["name"].strip():
                raise TraceabilityError(f"{question_id} deve nomear o cubo pendente")
        elif pending_cube is not None:
            raise TraceabilityError(f"{question_id} tem cubo pendente sem indicador pendente")
        if not question_cubes and not question_pending and not question_artifacts:
            raise TraceabilityError(
                f"{question_id} não tem cubo implementado, artefato analítico nem lacuna formal"
            )

        indicators.update(question_indicators)
        dashboards.update(question_dashboards)

    if tuple(requirements) != EXPECTED_REQUIREMENTS:
        raise TraceabilityError("requisitos ausentes ou duplicados")
    if indicators != EXPECTED_INDICATORS:
        missing = sorted(EXPECTED_INDICATORS - indicators)
        extra = sorted(indicators - EXPECTED_INDICATORS)
        raise TraceabilityError(
            f"cobertura de indicadores diverge; ausentes={missing}; extras={extra}"
        )
    if dashboards != EXPECTED_DASHBOARDS:
        raise TraceabilityError("a cobertura deve incluir exatamente D01–D04")
    if pending_questions != EXPECTED_PENDING_QUESTIONS:
        raise TraceabilityError("lacunas dimensionais devem ficar restritas a PB10, PB11 e PB13")
    if pending_indicators != EXPECTED_PENDING_INDICATORS:
        raise TraceabilityError("lacunas dimensionais devem ficar restritas a I12, I13 e I15")

    return {
        "questions": len(ids),
        "indicators": len(indicators),
        "cubes": len(cubes),
        "pendingIndicators": len(pending_indicators),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("scripts/traceability/manifest.json"),
    )
    parser.add_argument("--dmc", type=Path, default=Path("docs/dmc.json"))
    parser.add_argument("--project", type=Path, default=Path("docs/projeto.md"))
    parser.add_argument(
        "--sources-dir",
        type=Path,
        help="diretório externo com TAPI e Arquitetura para conferir hash e trechos",
    )
    args = parser.parse_args()
    try:
        manifest = load_json(args.manifest)
        summary = validate(manifest, load_json(args.dmc))
        validate_project_matrix(manifest, args.project)
        source_summary = (
            validate_primary_sources(manifest, args.sources_dir) if args.sources_dir else None
        )
    except TraceabilityError as error:
        print(f"Rastreabilidade inválida: {error}", file=sys.stderr)
        return 1
    message = (
        "Rastreabilidade válida: "
        f"{summary['questions']} perguntas; {summary['indicators']} indicadores; "
        f"{summary['cubes']} cubos; {summary['pendingIndicators']} indicadores "
        "com extensão futura de resposta conciliada"
    )
    if source_summary:
        message += (
            f"; {source_summary['sources']} fontes primárias e "
            f"{source_summary['claims']} afirmações conferidas"
        )
    else:
        message += "; fontes primárias não conferidas neste comando"
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
