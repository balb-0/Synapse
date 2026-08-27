#!/usr/bin/env python3
"""Valida as seções de classificação e segurança do artefato de governança."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path


class GovernanceValidationError(ValueError):
    """Indica que o artefato não atende ao contrato mínimo de governança."""


SECTION_FOUR = "# 4. Classificação e Proteção de Dados"
SECTION_FIVE = "# 5. Segurança e Acesso"

REQUIRED_CLASSES = ("Público", "Interno", "Confidencial", "Sensível")
REQUIRED_MARKERS = (
    "Não pessoal",
    "Pessoal",
    "Pessoal sensível",
    "Pseudonimizado",
    "Anonimizado ou agregado",
)
REQUIRED_SOURCES = (
    "pesquisas.csv",
    "empresas.csv",
    "clientes.csv",
    "respondentes.csv",
    "questoes.csv",
    "respostas.csv",
)
REQUIRED_RISK_FIELDS = (
    "id_cliente",
    "e-mail",
    "respondent_id",
    "id_empresa",
    "id_pesq",
    "valor",
    "enunciado",
    "objetivo",
    "observações",
)
RESTRICTED_SOURCE_NAMES = {
    "clientes.csv",
    "empresas.csv",
    "pesquisas.csv",
    "questoes.csv",
    "respondentes.csv",
    "respostas.csv",
}


def load_document(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise GovernanceValidationError(
            f"não foi possível ler o documento: {path}"
        ) from error


def extract_section(markdown: str, heading: str) -> str:
    matches = list(re.finditer(rf"^{re.escape(heading)}\s*$", markdown, re.MULTILINE))
    if len(matches) != 1:
        raise GovernanceValidationError(
            f"heading obrigatório deve aparecer uma vez: {heading}"
        )

    start = matches[0].end()
    next_root = re.search(r"^# \d+\.", markdown[start:], re.MULTILINE)
    end = start + next_root.start() if next_root else len(markdown)
    return markdown[start:end]


def _clean_cell(cell: str) -> str:
    return re.sub(r"[*_`]", "", cell).strip()


def table_rows(section: str, first_header: str) -> list[list[str]]:
    """Retorna somente o corpo da tabela identificada pela primeira coluna."""
    lines = section.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        header = [_clean_cell(cell) for cell in stripped[1:-1].split("|")]
        if not header or header[0] != first_header:
            continue

        rows: list[list[str]] = []
        for candidate in lines[index + 1 :]:
            candidate = candidate.strip()
            if not (candidate.startswith("|") and candidate.endswith("|")):
                if rows:
                    break
                continue
            cells = [_clean_cell(cell) for cell in candidate[1:-1].split("|")]
            if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                continue
            rows.append(cells)
        return rows

    raise GovernanceValidationError(
        f"tabela obrigatória ausente: cabeçalho {first_header}"
    )


def _require_first_column(rows: list[list[str]], expected: tuple[str, ...]) -> None:
    first_column = {row[0] for row in rows if row}
    missing = [value for value in expected if value not in first_column]
    if missing:
        raise GovernanceValidationError(
            "entradas obrigatórias ausentes em tabela: " + ", ".join(missing)
        )


def validate_section_four(section: str) -> dict[str, int]:
    # O documento usa naturalmente "Todo ativo..." em pt-BR. Por isso, o marcador
    # editorial TODO é deliberadamente sensível a maiúsculas.
    if "_conteúdo_" in section or re.search(r"\bTODO\b", section):
        raise GovernanceValidationError("a seção 4 contém placeholder")

    class_rows = table_rows(section, "Classe de informação")
    marker_rows = table_rows(section, "Marcador")
    asset_rows = table_rows(section, "Ativo")
    _require_first_column(class_rows, REQUIRED_CLASSES)
    _require_first_column(marker_rows, REQUIRED_MARKERS)

    missing_sources = [source for source in REQUIRED_SOURCES if source not in section]
    if missing_sources:
        raise GovernanceValidationError(
            "fontes obrigatórias ausentes: " + ", ".join(missing_sources)
        )

    lowered = section.lower()
    missing_fields = [field for field in REQUIRED_RISK_FIELDS if field.lower() not in lowered]
    if missing_fields:
        raise GovernanceValidationError(
            "campos de risco ausentes: " + ", ".join(missing_fields)
        )

    for row in asset_rows:
        joined = " | ".join(row)
        if any(source in joined for source in ("clientes.csv", "respondentes.csv", "respostas.csv")):
            if len(row) > 2 and row[2] == "Público":
                raise GovernanceValidationError(
                    "fonte com dado identificável não pode ser classificada como Público"
                )

    plain = re.sub(r"[*_`]", "", section)
    required_statements = {
        "distinção entre classe e conceito jurídico": r"Sensível.{0,40}classe organizacional",
        "limite da pseudonimização": r"continua (?:sujeito à LGPD|sendo dado pessoal)",
        "risco de reidentificação": r"reidentifica",
        "natureza da base não confirmada": r"fictícios ou anonimizados.{0,80}Não confirmado",
        "bloqueio de publicação identificável": r"respostas identificáveis|resposta identificável",
    }
    for label, pattern in required_statements.items():
        if not re.search(pattern, plain, re.IGNORECASE | re.DOTALL):
            raise GovernanceValidationError(f"declaração obrigatória ausente: {label}")

    return {
        "classes": len(REQUIRED_CLASSES),
        "markers": len(REQUIRED_MARKERS),
        "sources": len(REQUIRED_SOURCES),
    }


def validate_document(markdown: str) -> dict[str, int]:
    section_four = extract_section(markdown, SECTION_FOUR)
    extract_section(markdown, SECTION_FIVE)
    return validate_section_four(section_four)


def validate_tapi_hash(document: str, tapi_path: Path) -> str:
    section_four = extract_section(document, SECTION_FOUR)
    match = re.search(r"SHA-256[\s\S]{0,160}?([0-9a-fA-F]{64})", section_four)
    if not match:
        raise GovernanceValidationError("hash SHA-256 do TAPI ausente na seção 4")

    try:
        actual = hashlib.sha256(tapi_path.read_bytes()).hexdigest()
    except OSError as error:
        raise GovernanceValidationError(f"não foi possível ler o TAPI: {tapi_path}") from error

    expected = match.group(1).lower()
    if actual != expected:
        raise GovernanceValidationError(
            f"hash do TAPI divergente: esperado {expected}, obtido {actual}"
        )
    return actual


def validate_tracked_inputs(repository_root: Path) -> list[str]:
    try:
        process = subprocess.run(
            ["git", "-C", str(repository_root), "ls-files", "-z"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise GovernanceValidationError("não foi possível consultar o índice Git") from error

    tracked = process.stdout.decode("utf-8").split("\0")
    forbidden: list[str] = []
    for item in tracked:
        if not item:
            continue
        normalized = item.replace("\\", "/")
        basename = normalized.rsplit("/", 1)[-1].lower()
        scoped = f"/{normalized.lower()}"
        if (
            basename in RESTRICTED_SOURCE_NAMES
            or "/data/raw/" in scoped
            or "/data/private/" in scoped
        ):
            forbidden.append(normalized)
    return sorted(forbidden)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--document", type=Path, required=True)
    parser.add_argument("--tapi", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        document = load_document(args.document)
        summary = validate_document(document)
        validate_tapi_hash(document, args.tapi)
        forbidden = validate_tracked_inputs(args.repository_root)
        if forbidden:
            raise GovernanceValidationError(
                "fontes restritas rastreadas pelo Git: " + ", ".join(forbidden)
            )
    except GovernanceValidationError as error:
        print(f"Erro de governança: {error}", file=sys.stderr)
        return 1

    print(
        "Governança válida: "
        f"{summary['classes']} classes; "
        f"{summary['markers']} marcadores; "
        f"{summary['sources']} fontes; TAPI conferido; sem fonte bruta rastreada"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
