#!/usr/bin/env python3
"""Valida as seções de classificação e segurança do artefato de governança."""

from __future__ import annotations

import argparse
import csv
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
REQUIRED_ACCESS_PROFILES = (
    "Equipe da Central",
    "Áreas técnicas",
    "Data Owner",
    "Data Steward",
    "Data Custodian / TI",
    "Solicitantes/participantes",
    "Público externo",
    "Equipe acadêmica",
)
INTERNAL_LAYERS = ("staging", "trusted", "analytics")
HIGH_RISK_CSV_HEADERS = {
    "cpf",
    "e-mail",
    "email",
    "endereco",
    "endereço",
    "id_cliente",
    "id_empresa",
    "id_pergunta",
    "id_pesq",
    "id_resposta",
    "nome",
    "pesquisa_id",
    "resposta",
    "respondent_id",
    "telefone",
}
RESTRICTED_SOURCE_NAMES = {
    "clientes.csv",
    "empresas.csv",
    "pesquisas.csv",
    "questoes.csv",
    "respondentes.csv",
    "respostas.csv",
    "teste.csv",
}

EXPECTED_ASSETS = {
    "Pesquisa": ("Interno", r"Não pessoal|Pessoal"),
    "Empresa": ("Confidencial", r"Não pessoal"),
    "Pessoa/Cliente": ("Confidencial", r"\bPessoal\b"),
    "Participação em Pesquisa": ("Sensível", r"Pessoal|Pseudonimizado"),
    "Questão": ("Interno", r"Não pessoal"),
    "Resposta": ("Sensível", r"Pessoal"),
    "Resultado analítico": (
        "Confidencial até aprovação",
        r"Pseudonimizado|Anonimizado",
    ),
    "Publicação autorizada": ("Público", r"Anonimizado"),
    "Consentimento e atendimento do titular": (
        "Sensível",
        r"Pessoal|Pseudonimizado",
    ),
    "Credenciais, segredos e chaves de reidentificação": (
        "Sensível",
        r"Pessoal|Não pessoal",
    ),
    "Logs de acesso e auditoria": ("Confidencial", r"Pessoal|Não pessoal"),
}

EXPECTED_OBJECT_PERMISSIONS = {
    "Equipe da Central": (
        "L/G",
        "L/G",
        "L no job autorizado",
        "L restrita; G de correção registrada",
        "L",
        "G de preparação",
        "—",
    ),
    "Áreas técnicas": (
        "L no escopo",
        "L/G de validação",
        "—",
        "—",
        "L no escopo",
        "—",
        "—",
    ),
    "Data Owner": (
        "L",
        "L",
        "—",
        "—",
        "L",
        "A de aprovação",
        "A de regra de negócio",
    ),
    "Data Steward": (
        "L/G",
        "L/G de regra",
        "L excepcional",
        "L/G excepcional",
        "L/G de qualidade",
        "L de evidência",
        "A de classificação e catálogo",
    ),
    "Data Custodian / TI": (
        "— por padrão",
        "— por padrão",
        "— por padrão",
        "— por padrão",
        "— por padrão",
        "G da versão aprovada",
        "A técnica",
    ),
    "Equipe acadêmica": (
        "—",
        "—",
        "—",
        "—",
        "L somente de agregado aprovado",
        "L da versão pública",
        "—",
    ),
}

EXPECTED_INTERNAL_LAYER_PERMISSIONS = {
    "Serviço de ingestão": ("G", "G de promoção", "—", "—"),
    "Equipe da Central": ("—", "L/G via aplicação", "L", "G de preparação"),
    "Áreas técnicas": (
        "—",
        "L/G no questionário e escopo",
        "L no escopo",
        "L quando autorizada",
    ),
    "Data Owner": ("—", "—", "L", "A de aprovação"),
    "Data Steward": (
        "L de quarentena",
        "L/G de qualidade",
        "L/G de regra",
        "L de evidência",
    ),
    "Data Custodian / TI": (
        "A técnica; L excepcional",
        "A técnica; L excepcional",
        "A técnica; L excepcional",
        "G da versão aprovada",
    ),
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
    # Remove somente marcadores Markdown nas bordas. Underscores internos fazem
    # parte de nomes de campo como id_cliente e precisam ser preservados.
    return cell.strip().strip("*_`").strip()


def table_rows(
    section: str, first_header: str, second_header: str | None = None
) -> list[list[str]]:
    """Retorna somente o corpo da tabela identificada pela primeira coluna."""
    lines = section.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        header = [_clean_cell(cell) for cell in stripped[1:-1].split("|")]
        if (
            not header
            or header[0] != first_header
            or (
                second_header is not None
                and (len(header) < 2 or header[1] != second_header)
            )
        ):
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
        "tabela obrigatória ausente: cabeçalho "
        + " / ".join(value for value in (first_header, second_header) if value)
    )


def _require_first_column(rows: list[list[str]], expected: tuple[str, ...]) -> None:
    first_column = {row[0] for row in rows if row}
    missing = [value for value in expected if value not in first_column]
    if missing:
        raise GovernanceValidationError(
            "entradas obrigatórias ausentes em tabela: " + ", ".join(missing)
        )


def _rows_by_first_column(
    rows: list[list[str]], *, label: str, width: int
) -> dict[str, list[str]]:
    malformed = [row[0] if row else "<vazia>" for row in rows if len(row) != width]
    if malformed:
        raise GovernanceValidationError(
            f"linhas com largura inválida em {label}: " + ", ".join(malformed)
        )

    indexed: dict[str, list[str]] = {}
    duplicates: list[str] = []
    for row in rows:
        if row[0] in indexed:
            duplicates.append(row[0])
        indexed[row[0]] = row
    if duplicates:
        raise GovernanceValidationError(
            f"linhas duplicadas em {label}: " + ", ".join(sorted(set(duplicates)))
        )
    return indexed


def validate_section_four(section: str) -> dict[str, int]:
    # O documento usa naturalmente "Todo ativo..." em pt-BR. Por isso, o marcador
    # editorial TODO é deliberadamente sensível a maiúsculas.
    if "_conteúdo_" in section or re.search(r"\bTODO\b", section):
        raise GovernanceValidationError("a seção 4 contém placeholder")

    class_rows = table_rows(section, "Classe de informação")
    marker_rows = table_rows(section, "Marcador")
    asset_rows = table_rows(section, "Ativo")
    _rows_by_first_column(class_rows, label="classes", width=4)
    _rows_by_first_column(marker_rows, label="marcadores", width=2)
    asset_by_name = _rows_by_first_column(asset_rows, label="ativos", width=5)
    _require_first_column(class_rows, REQUIRED_CLASSES)
    _require_first_column(marker_rows, REQUIRED_MARKERS)

    asset_text = "\n".join(" | ".join(row) for row in asset_rows)
    missing_sources = [source for source in REQUIRED_SOURCES if source not in asset_text]
    if missing_sources:
        raise GovernanceValidationError(
            "fontes obrigatórias ausentes: " + ", ".join(missing_sources)
        )

    lowered = asset_text.lower()
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

    for asset_prefix, (expected_class, marker_pattern) in EXPECTED_ASSETS.items():
        matches = [
            row for name, row in asset_by_name.items() if name.startswith(asset_prefix)
        ]
        if len(matches) != 1:
            raise GovernanceValidationError(
                f"ativo obrigatório deve aparecer uma vez: {asset_prefix}"
            )
        row = matches[0]
        if row[2] != expected_class:
            raise GovernanceValidationError(
                f"classe mínima inválida para {asset_prefix}: {row[2]}"
            )
        if not re.search(marker_pattern, row[3]):
            raise GovernanceValidationError(
                f"marcador de proteção inválido para {asset_prefix}"
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


def validate_section_five(section: str) -> dict[str, int]:
    if "_conteúdo_" in section or re.search(r"\bTODO\b", section):
        raise GovernanceValidationError("a seção 5 contém placeholder")

    profile_rows = table_rows(section, "Perfil", "Necessidade de acesso")
    object_rows = table_rows(section, "Perfil", "Pesquisa e metadados")
    layer_rows = table_rows(section, "Perfil ou serviço")
    profile_by_name = _rows_by_first_column(
        profile_rows, label="perfis", width=3
    )
    object_by_profile = _rows_by_first_column(
        object_rows, label="permissões por objeto", width=8
    )
    layer_by_profile = _rows_by_first_column(
        layer_rows, label="permissões por camada", width=5
    )
    _require_first_column(list(profile_by_name.values()), REQUIRED_ACCESS_PROFILES)
    _require_first_column(list(object_by_profile.values()), REQUIRED_ACCESS_PROFILES)
    _require_first_column(list(layer_by_profile.values()), REQUIRED_ACCESS_PROFILES)

    for profile in (
        "Solicitantes/participantes",
        "Público externo",
        "Equipe acadêmica",
    ):
        row = layer_by_profile[profile]
        if any(cell != "—" for cell in row[1:4]):
            raise GovernanceValidationError(
                f"perfil externo não pode acessar camada interna: {profile}"
            )
        if not re.fullmatch(r"L(?: .*)?", row[4]):
            raise GovernanceValidationError(
                f"perfil externo deve ter somente leitura na publicação: {profile}"
            )

    for profile in ("Solicitantes/participantes", "Público externo"):
        row = object_by_profile[profile]
        if any(cell != "—" for cell in row[1:6]) or row[7] != "—":
            raise GovernanceValidationError(
                f"perfil externo não pode acessar objeto interno: {profile}"
            )
        if not re.fullmatch(r"L(?: .*)?", row[6]):
            raise GovernanceValidationError(
                f"perfil externo deve ter somente leitura no objeto Publicação: {profile}"
            )

    for profile, expected in EXPECTED_OBJECT_PERMISSIONS.items():
        if tuple(object_by_profile[profile][1:]) != expected:
            raise GovernanceValidationError(
                f"permissões por objeto divergem da política documentada: {profile}"
            )

    for profile, expected in EXPECTED_INTERNAL_LAYER_PERMISSIONS.items():
        if tuple(layer_by_profile[profile][1:]) != expected:
            raise GovernanceValidationError(
                f"permissões por camada divergem da política documentada: {profile}"
            )

    custodian = layer_by_profile["Data Custodian / TI"]
    if not all("A técnica" in cell for cell in custodian[1:4]):
        raise GovernanceValidationError(
            "Data Custodian precisa de administração técnica explícita por camada"
        )
    if not all("L excepcional" in cell for cell in custodian[1:4]):
        raise GovernanceValidationError(
            "leitura do Data Custodian deve permanecer excepcional"
        )

    plain = re.sub(r"[*_`]", "", section)
    required_statements = {
        "negação por padrão": r"acesso é negado por padrão",
        "autorização no servidor": r"validar a política no servidor",
        "escopo composto": (
            r"perfil × ação × recurso × classe × pesquisa × empresa × área × finalidade"
        ),
        "acesso emergencial": r"break-glass",
        "camadas internas": r"staging, trusted e analytics.{0,80}sempre internas",
        "publicação separada": r"versão publicável separada",
    }
    for label, pattern in required_statements.items():
        if not re.search(pattern, plain, re.IGNORECASE | re.DOTALL):
            raise GovernanceValidationError(f"regra de acesso ausente: {label}")

    for symbol in ("L", "G", "A", "—"):
        if not re.search(
            rf"^[-*] \*\*{re.escape(symbol)}\*\*", section, re.MULTILINE
        ):
            raise GovernanceValidationError(
                f"legenda da matriz de acesso ausente: {symbol}"
            )

    return {
        "profiles": len(REQUIRED_ACCESS_PROFILES),
        "internal_layers": len(INTERNAL_LAYERS),
    }


def validate_document(markdown: str) -> dict[str, int]:
    section_four = extract_section(markdown, SECTION_FOUR)
    section_five = extract_section(markdown, SECTION_FIVE)
    return validate_section_four(section_four) | validate_section_five(section_five)


def validate_tapi_hash(document: str, tapi_path: Path) -> str:
    section_four = extract_section(document, SECTION_FOUR)
    matches = re.findall(r"SHA-256[\s\S]{0,160}?([0-9a-fA-F]{64})", section_four)
    if len(matches) != 1:
        raise GovernanceValidationError(
            "a seção 4 deve conter exatamente um hash SHA-256 do TAPI"
        )

    try:
        actual = hashlib.sha256(tapi_path.read_bytes()).hexdigest()
    except OSError as error:
        raise GovernanceValidationError(f"não foi possível ler o TAPI: {tapi_path}") from error

    expected = matches[0].lower()
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
            continue

        if basename.endswith(".csv"):
            try:
                with (repository_root / item).open(
                    "r", encoding="utf-8-sig", errors="replace"
                ) as source:
                    first_line = source.readline(65536)
            except OSError as error:
                raise GovernanceValidationError(
                    f"não foi possível inspecionar o cabeçalho CSV: {normalized}"
                ) from error
            delimiter = ";" if first_line.count(";") > first_line.count(",") else ","
            headers = {
                value.strip().lower()
                for value in next(csv.reader([first_line], delimiter=delimiter), [])
            }
            if headers & HIGH_RISK_CSV_HEADERS:
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
        f"{summary['sources']} fontes; "
        f"{summary['profiles']} perfis; "
        f"{summary['internal_layers']} camadas internas; "
        "TAPI conferido; sem fonte conhecida ou CSV com cabeçalho de risco rastreado"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
