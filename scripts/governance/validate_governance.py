#!/usr/bin/env python3
"""Valida os contratos estruturais do artefato de governança de dados."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


class GovernanceValidationError(ValueError):
    """Indica que o artefato não atende ao contrato mínimo de governança."""


SECTION_ONE = "# 1. Estrutura Organizacional da Governança"
SECTION_THREE = "# 3. Gestão de Metadados e Catálogo"
SECTION_FOUR = "# 4. Classificação e Proteção de Dados"
SECTION_FIVE = "# 5. Segurança e Acesso"

REQUIRED_GOVERNANCE_ROLES = (
    "Data Owner",
    "Data Steward",
    "Data Custodian / TI",
)
REQUIRED_CATALOG_HEADINGS = (
    "## 3.1 Estado e objetivo do catálogo",
    "## 3.2 Estratégia e fontes de verdade",
    "## 3.3 Busca, reutilização, descoberta e rastreabilidade",
    "## 3.4 Metadados obrigatórios",
    "## 3.5 Atualização e versionamento",
    "## 3.6 Exemplo de catálogo: `FATO_CICLO_PESQUISA`",
    "## 3.7 Escopo dos cubos e limitações do catálogo",
    "## 3.8 Integração com qualidade, proteção e acesso",
)
REQUIRED_COMMON_METADATA_FIELDS = (
    "asset_id",
    "nome_negocio",
    "nome_tecnico",
    "tipo_ativo",
    "definicao",
    "dominio_negocio",
    "finalidade_uso",
    "pergunta_ids",
    "requisito_ids",
    "indicador_ids",
    "visualizacao_ids",
    "consumidor_ids",
    "unidade_analise",
    "grao",
    "fonte_origem",
    "campos_origem",
    "transformacao",
    "linhagem",
    "tipo_fisico",
    "tipo_semantico",
    "dominio_valores",
    "nulabilidade",
    "periodicidade_esperada",
    "frescor_observado",
    "owner",
    "steward",
    "custodian",
    "classificacao",
    "marcador_lgpd",
    "acesso",
    "regra_qualidade",
    "limiar",
    "retencao",
    "descarte",
    "estado_evidencia",
    "estado_ciclo",
    "versao",
    "vigencia_inicio",
    "vigencia_fim",
    "change_id",
    "atualizado_em",
    "atualizado_por",
    "aprovado_por",
)
REQUIRED_CATALOG_ASSET_TYPES = (
    "Fato",
    "Dimensão",
    "Medida",
    "Fonte ou campo de origem",
)
REQUIRED_EXAMPLE_DIMENSIONS = (
    "DIM_PESQUISA",
    "DIM_TEMPO",
    "DIM_AREA",
    "DIM_STATUS_PESQUISA",
    "DIM_TIPO_PESQUISA",
    "DIM_PERFIL_PESQUISA",
    "DIM_FAMILIA_PESQUISA",
    "DIM_FONTE_DADO",
    "DIM_EXECUCAO_CARGA",
)
REQUIRED_EXAMPLE_MEASURES = (
    "dias_uteis_validacao",
    "dias_uteis_coleta",
    "dias_uteis_tabulacao",
    "dias_uteis_ciclo_total",
    "qtd_empresas_na_pesquisa",
    "flag_prorrogada",
)
REQUIRED_CUBES = ("C01", "C02", "C03", "C04")
REQUIRED_CUBE_NAMES = {
    "C01": "Portfólio e Ciclo",
    "C02": "Participação e Representatividade",
    "C03": "Pipeline Mensal",
    "C04": "Resultados e Questionários",
}

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
    section: str,
    first_header: str,
    second_header: str | None = None,
    *,
    expected_headers: tuple[str, ...] | None = None,
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
        if expected_headers is not None and tuple(header) != expected_headers:
            raise GovernanceValidationError(
                "cabeçalho divergente na tabela "
                f"{first_header}: esperado " + " | ".join(expected_headers)
            )

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


def _require_terms(text: str, expected: tuple[str, ...], *, label: str) -> None:
    missing = [
        value
        for value in expected
        if not re.search(rf"(?<![\w]){re.escape(value)}(?![\w])", text)
    ]
    if missing:
        raise GovernanceValidationError(
            f"{label} obrigatórios ausentes: " + ", ".join(missing)
        )


def _require_single_headings(section: str, headings: tuple[str, ...]) -> None:
    for heading in headings:
        occurrences = len(
            re.findall(rf"^{re.escape(heading)}\s*$", section, re.MULTILINE)
        )
        if occurrences != 1:
            raise GovernanceValidationError(
                f"subseção obrigatória deve aparecer uma vez: {heading}"
            )


def _require_nonempty_rows(rows: list[list[str]], *, label: str) -> None:
    incomplete = [
        row[0] if row and row[0] else "<vazia>"
        for row in rows
        if any(not cell.strip() for cell in row)
    ]
    if incomplete:
        raise GovernanceValidationError(
            f"linhas com campo obrigatório vazio em {label}: "
            + ", ".join(incomplete)
        )


def validate_section_one(section: str) -> dict[str, int]:
    if "_conteúdo_" in section or re.search(r"\bTODO\b", section):
        raise GovernanceValidationError("a seção 1 contém placeholder")

    role_rows = table_rows(
        section,
        "Papel",
        "Referência documental",
        expected_headers=(
            "Papel",
            "Referência documental",
            "Autoridade e responsabilidade propostas",
            "Limites do papel",
        ),
    )
    role_by_name = _rows_by_first_column(
        role_rows, label="papéis de governança", width=4
    )
    _require_first_column(role_rows, REQUIRED_GOVERNANCE_ROLES)
    for role in REQUIRED_GOVERNANCE_ROLES:
        if any(not cell.strip() for cell in role_by_name[role][1:]):
            raise GovernanceValidationError(
                f"papel de governança possui campo vazio: {role}"
            )

    map_match = re.search(
        r"```mermaid\s+flowchart\b(?P<body>[\s\S]*?)```", section
    )
    if not map_match:
        raise GovernanceValidationError("mapa funcional Mermaid ausente na seção 1")
    _require_terms(
        map_match.group("body"),
        (
            "Data Owner",
            "Data Stewards",
            "Data Custodian / TI",
            "Controlador",
            "Operador e suboperadores",
            "Encarregado",
            "RentalHost",
        ),
        label="atores do mapa funcional",
    )
    required_nodes = {
        "OWNER": "Data Owner",
        "STEWARD": "Data Stewards",
        "CUST": "Data Custodian / TI",
        "CONTROLLER": "Controlador",
        "PROCESSORS": "Operador e suboperadores",
        "DPO": "Encarregado",
        "EXT": "RentalHost",
    }
    for node_id, label in required_nodes.items():
        if not re.search(
            rf"^\s*{node_id}\s*\[[^\n]*{re.escape(label)}",
            map_match.group("body"),
            re.MULTILINE,
        ):
            raise GovernanceValidationError(
                f"nó obrigatório ausente no mapa funcional: {label}"
            )
    required_relations = (
        ("CENTRAL", "STEWARD"),
        ("STEWARD", "OWNER"),
        ("OWNER", "CUST"),
        ("CUST", "STEWARD"),
    )
    for source, target in required_relations:
        if not re.search(
            rf"^\s*{source}\s+-->[^\n]*\b{target}\b",
            map_match.group("body"),
            re.MULTILINE,
        ):
            raise GovernanceValidationError(
                f"relação obrigatória ausente no mapa funcional: {source} → {target}"
            )

    raci_rows = table_rows(
        section,
        "Atividade",
        "Data Owner",
        expected_headers=(
            "Atividade",
            "Data Owner",
            "Data Steward",
            "Central de Pesquisas",
            "Áreas técnicas",
            "Data Custodian / TI",
            "Papéis LGPD a designar, conforme o tratamento",
            "Custódia externa",
        ),
    )
    _rows_by_first_column(raci_rows, label="matriz RACI", width=8)
    _require_nonempty_rows(raci_rows, label="matriz RACI")
    for row in raci_rows:
        assignments = " | ".join(row[1:])
        codes = set(re.findall(r"(?<!\w)[ARCI](?!\w)", assignments))
        if not {"A", "R"}.issubset(codes):
            raise GovernanceValidationError(
                f"atividade da matriz RACI deve identificar A e R: {row[0]}"
            )
    raci_text = "\n".join(" | ".join(row) for row in raci_rows).lower()
    for topic in (
        "metadados",
        "qualidade",
        "classificar dados",
        "autenticação",
        "risco residual",
        "disponibilizar resultados",
        "direitos dos titulares",
    ):
        if topic not in raci_text:
            raise GovernanceValidationError(
                f"responsabilidade obrigatória ausente na matriz RACI: {topic}"
            )

    custody_rows = table_rows(
        section,
        "Interface",
        "Quem entrega ou solicita",
        expected_headers=(
            "Interface",
            "Quem entrega ou solicita",
            "Quem executa",
            "Quem aprova ou valida",
            "Evidência mínima exigida",
        ),
    )
    custody_by_name = _rows_by_first_column(
        custody_rows, label="interfaces de custódia", width=5
    )
    _require_nonempty_rows(custody_rows, label="interfaces de custódia")
    for row in custody_rows:
        if any(cell.strip() == "—" for cell in row[1:]):
            raise GovernanceValidationError(
                f"interface de custódia usa responsabilidade ou evidência genérica: {row[0]}"
            )
    for prefix in (
        "Fonte operacional →",
        "staging` → `trusted",
        "trusted` → `analytics",
        "analytics` → publicação",
        "Correção, incidente ou direito do titular",
    ):
        if not any(prefix in name for name in custody_by_name):
            raise GovernanceValidationError(
                f"interface de custódia obrigatória ausente: {prefix}"
            )

    plain = re.sub(r"[*`]", "", section)
    _require_terms(
        plain,
        (
            "controlador",
            "operador",
            "suboperador",
            "encarregado",
            "pendente de homologação",
        ),
        label="distinções organizacionais e jurídicas",
    )
    if not re.search(r"RentalHost[\s\S]{0,240}depende do contrato", plain):
        raise GovernanceValidationError(
            "participação condicional da RentalHost não foi documentada"
        )

    return {
        "governance_roles": len(REQUIRED_GOVERNANCE_ROLES),
        "raci_activities": len(raci_rows),
        "custody_interfaces": len(custody_rows),
    }


def validate_section_three(section: str) -> dict[str, int]:
    if "_conteúdo_" in section or re.search(r"\bTODO\b", section):
        raise GovernanceValidationError("a seção 3 contém placeholder")

    _require_single_headings(section, REQUIRED_CATALOG_HEADINGS)

    common_rows = table_rows(section, "Metadado", "Conteúdo obrigatório")
    _rows_by_first_column(common_rows, label="metadados comuns", width=3)
    _require_nonempty_rows(common_rows, label="metadados comuns")
    common_names = "\n".join(row[0] for row in common_rows)
    _require_terms(
        common_names,
        REQUIRED_COMMON_METADATA_FIELDS,
        label="campos comuns do catálogo",
    )

    type_rows = table_rows(section, "Tipo", "Metadados adicionais obrigatórios")
    type_by_name = _rows_by_first_column(
        type_rows, label="requisitos por tipo de ativo", width=3
    )
    _require_first_column(type_rows, REQUIRED_CATALOG_ASSET_TYPES)
    type_requirements = {
        "Fato": (
            "tipo_fato",
            "grão",
            "chaves estrangeiras",
            "dimensões conformadas",
            "medidas",
            "fonte",
            "transformação",
            "execução de carga",
            "Exatamente um grão",
        ),
        "Dimensão": (
            "Grão",
            "chave substituta",
            "chave de negócio",
            "atributos",
            "domínios",
            "Não mapeado",
            "SCD",
            "vigência",
            "registro atual",
        ),
        "Medida": (
            "Fórmula",
            "unidade",
            "numerador",
            "denominador",
            "aditividade",
            "janela temporal",
            "timezone",
            "cobertura",
            "nulos/sentinelas",
            "filtros válidos",
            "regra de validação",
            "estado de disponibilidade",
        ),
        "Fonte ou campo de origem": (
            "Formato",
            "codificação",
            "chave",
            "nulabilidade",
            "sentinelas",
            "domínio observado",
            "hash",
            "confianca_extracao",
            "origem_evidencia",
            "status_mapeamento",
        ),
    }
    for asset_type, expected in type_requirements.items():
        _require_terms(
            " | ".join(type_by_name[asset_type][1:]),
            expected,
            label=f"metadados de {asset_type}",
        )

    example_rows = table_rows(section, "Metadado", "Valor catalogado")
    example_by_name = _rows_by_first_column(
        example_rows, label="exemplo de catálogo", width=2
    )
    _require_nonempty_rows(example_rows, label="exemplo de catálogo")
    _require_first_column(
        example_rows,
        (
            "asset_id",
            "Nome de negócio",
            "Nome técnico",
            "Tipo de ativo",
            "Definição",
            "Tipo e grão",
            "Fonte principal",
            "Periodicidade esperada",
            "Frescor observado",
            "Classificação e sensibilidade",
            "Responsáveis",
            "Qualidade e limiares",
            "Retenção e descarte",
            "Versão e vigência",
            "Mudança e auditoria",
        ),
    )
    technical_name = example_by_name["Nome técnico"][1]
    if "FATO_CICLO_PESQUISA" not in technical_name or "C01" not in technical_name:
        raise GovernanceValidationError(
            "exemplo FATO_CICLO_PESQUISA não está ligado ao C01"
        )
    example_semantics = {
        "Tipo de ativo": ("fato", "snapshot acumulado"),
        "Fonte principal": ("pesquisas.csv", "origem"),
        "Tipo e grão": ("snapshot acumulado", "uma linha por pesquisa"),
    }
    for field, expected in example_semantics.items():
        _require_terms(
            example_by_name[field][1].lower(),
            expected,
            label=f"conteúdo semântico do exemplo em {field}",
        )

    field_rows = table_rows(section, "Campo técnico", "Tipo e papel")
    _rows_by_first_column(field_rows, label="dicionário do exemplo", width=4)
    _require_nonempty_rows(field_rows, label="dicionário do exemplo")
    _require_first_column(field_rows, REQUIRED_EXAMPLE_MEASURES)
    for row in field_rows:
        for cell in row[2:]:
            if cell.strip().lower() in {"—", "observação livre", "indisponivel"}:
                raise GovernanceValidationError(
                    f"definição ou origem obrigatória ausente no campo: {row[0]}"
                )

    dimension_rows = table_rows(section, "Dimensão", "Grão e chaves")
    _rows_by_first_column(
        dimension_rows, label="dimensões do exemplo", width=4
    )
    _require_nonempty_rows(dimension_rows, label="dimensões do exemplo")
    _require_first_column(dimension_rows, REQUIRED_EXAMPLE_DIMENSIONS)
    for row in dimension_rows:
        grain_and_keys = row[1].lower()
        if "linha por" not in grain_and_keys or not re.search(
            r"\bsk_|\bchave", grain_and_keys
        ):
            raise GovernanceValidationError(
                f"grão ou chave ausente na dimensão: {row[0]}"
            )

    measure_rows = table_rows(section, "Medida", "Fórmula, unidade e janela")
    measure_by_name = _rows_by_first_column(
        measure_rows, label="contrato das medidas", width=4
    )
    _require_nonempty_rows(measure_rows, label="contrato das medidas")
    _require_first_column(measure_rows, REQUIRED_EXAMPLE_MEASURES)
    measure_formula_terms = {
        "dias_uteis_validacao": ("dias úteis", "janela", "menos"),
        "dias_uteis_coleta": ("dias úteis", "prorrogação", "menos"),
        "dias_uteis_tabulacao": ("dias úteis", "janela", "menos"),
        "dias_uteis_ciclo_total": ("dias úteis", "janela", "menos"),
        "qtd_empresas_na_pesquisa": ("unidade empresa", "grão"),
        "flag_prorrogada": ("unidade booleana", "1"),
    }
    for measure in REQUIRED_EXAMPLE_MEASURES:
        row_text = " | ".join(measure_by_name[measure][1:])
        _require_terms(
            measure_by_name[measure][1].lower(),
            measure_formula_terms[measure],
            label=f"fórmula, unidade e janela de {measure}",
        )
        if not re.search(r"Aditiva|Não aditiva|Indicador/filtro", row_text):
            raise GovernanceValidationError(
                f"aditividade ou uso ausente para a medida: {measure}"
            )
        if not re.search(r"NULL|Nulo|nulo|cobertura", row_text):
            raise GovernanceValidationError(
                f"tratamento de nulos ou cobertura ausente para a medida: {measure}"
            )

    cube_rows = table_rows(section, "Cubo", "Grão e fontes")
    cube_by_name = _rows_by_first_column(
        cube_rows, label="escopo dos cubos", width=4
    )
    _require_nonempty_rows(cube_rows, label="escopo dos cubos")
    cube_grain_source_patterns = {
        "C01": r"uma linha por pesquisa[\s\S]*pesquisas\.csv",
        "C02": r"uma linha por participação[\s\S]*respondentes\.csv",
        "C03": r"mês × status × área × tipo × perfil[\s\S]*(?:C01|snapshots|log de mudança)",
        "C04": r"uma pergunta por pesquisa[\s\S]*questoes\.csv",
    }
    for cube, expected_name in REQUIRED_CUBE_NAMES.items():
        expected_label = f"{cube} — {expected_name}"
        if expected_label not in cube_by_name:
            raise GovernanceValidationError(
                f"identificador ou nome canônico do cubo divergente: {cube}"
            )
        if not re.search(
            cube_grain_source_patterns[cube],
            cube_by_name[expected_label][1],
            re.IGNORECASE,
        ):
            raise GovernanceValidationError(
                f"grão ou fonte obrigatória ausente no cubo: {cube}"
            )

    plain = re.sub(r"[*`]", "", section)
    required_statements = {
        "fallback_por_titulo": r"fallback_por_titulo[\s\S]{0,480}não\s+(?:se\s+torna|vira)\s+chave\s+canônica",
        "histórico do C03": r"C03[\s\S]{0,480}snapshots\s+mensais\s+persistidos\s+ou\s+log\s+de\s+mudança",
        "limite do C04": r"C04[\s\S]{0,480}(?:10\s+de\s+aproximadamente\s+366|10\s+de\s+366)[\s\S]{0,240}não\s+contém\s+respostas\s+individuais",
        "capacidades não implantadas": r"capacidades[\s\S]{0,160}planejadas,\s+não\s+implantadas",
    }
    for label, pattern in required_statements.items():
        if not re.search(pattern, plain, re.IGNORECASE):
            raise GovernanceValidationError(
                f"regra obrigatória ausente no catálogo: {label}"
            )

    return {
        "catalog_common_fields": len(REQUIRED_COMMON_METADATA_FIELDS),
        "catalog_asset_types": len(REQUIRED_CATALOG_ASSET_TYPES),
        "catalog_dimensions": len(REQUIRED_EXAMPLE_DIMENSIONS),
        "catalog_measures": len(REQUIRED_EXAMPLE_MEASURES),
        "catalog_cubes": len(REQUIRED_CUBES),
    }


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
    section_one = extract_section(markdown, SECTION_ONE)
    section_three = extract_section(markdown, SECTION_THREE)
    section_four = extract_section(markdown, SECTION_FOUR)
    section_five = extract_section(markdown, SECTION_FIVE)
    return (
        validate_section_one(section_one)
        | validate_section_three(section_three)
        | validate_section_four(section_four)
        | validate_section_five(section_five)
    )


def validate_role_consistency(
    document: str, tapi: str, dmc: dict[str, object], architecture: str
) -> dict[str, int]:
    """Confronta os papéis documentados com as quatro fontes de evidência."""
    section = extract_section(document, SECTION_ONE)
    role_rows = table_rows(section, "Papel", "Referência documental")
    role_by_name = _rows_by_first_column(
        role_rows, label="papéis de governança", width=4
    )

    tapi_assignments = {
        "líder do projeto": (
            r"^[ \t]*(?:●[ \t]*)?LÍDER DO PROJETO:[ \t]*Felipe Fernandes Rojas\b",
            "Felipe Fernandes Rojas",
        ),
        "ponto focal backup": (
            r"^[ \t]*(?:●[ \t]*)?PONTO FOCAL BACKUP:[ \t]*Reinaldo Nobrega\b",
            "Reinaldo Nobrega",
        ),
        "analista de dados": (
            r"^[ \t]*Lucas Andrade[ \t]*[–-][ \t]*Analista de Dados Jr\.",
            "Lucas Andrade",
        ),
        "líder executivo": (
            r"^[ \t]*(?:●[ \t]*)?LÍDER EXECUTIVO(?: \[Onboarding Executivo\])?:[ \t]*Fabio Moreira\b",
            "Fabio Moreira",
        ),
    }
    for label, (pattern, expected_name) in tapi_assignments.items():
        if not re.search(pattern, tapi, re.MULTILINE):
            raise GovernanceValidationError(
                f"atribuição obrigatória ausente no TAPI: {label} — {expected_name}"
            )
    tapi_unique_assignments = {
        "líder do projeto": r"(?:●[ \t]*)?LÍDER DO PROJETO[ \t]*:[^\n]*",
        "ponto focal backup": r"(?:●[ \t]*)?PONTO FOCAL BACKUP[ \t]*:[^\n]*",
        "analista de dados": (
            r"Lucas Andrade[ \t]*[–-][ \t]*Analista de Dados Jr\.[^\n]*"
        ),
        "líder executivo": (
            r"(?:●[ \t]*)?LÍDER EXECUTIVO(?: \[Onboarding Executivo\])?"
            r"[ \t]*:[^\n]*"
        ),
    }
    for label, assignment_pattern in tapi_unique_assignments.items():
        assignment_lines = re.findall(
            rf"^[ \t]*{assignment_pattern}",
            tapi,
            re.MULTILINE | re.IGNORECASE,
        )
        if len(assignment_lines) != 1:
            raise GovernanceValidationError(
                f"o TAPI deve conter exatamente uma atribuição para {label}"
            )
        if re.search(r"\bnão\b", assignment_lines[0], re.IGNORECASE):
            raise GovernanceValidationError(
                f"a atribuição do TAPI contém negação contraditória para {label}"
            )
    _require_terms(tapi, ("Trello", "Outlook"), label="ferramentas do TAPI")

    governance = dmc.get("governancaCorporativa")
    if not isinstance(governance, dict):
        raise GovernanceValidationError(
            "governancaCorporativa ausente ou inválida no DMC"
        )
    dmc_requirements = {
        "owner": (
            "Baseline documental: Fabio Moreira como Data Owner para decisões de "
            "negócio, acesso, indicadores, publicação, exceções e risco residual; "
            "autoridade formal sujeita à homologação e sem inferência de papel "
            "jurídico na LGPD."
        ),
        "steward": (
            "Baseline documental: Felipe Rojas, Reinaldo Nobrega e Lucas Andrade "
            "como Data Stewards de semântica, catálogo, qualidade e linhagem; "
            "atribuição e grafia final sujeitas à homologação."
        ),
        "custodian": (
            "Baseline documental: Rodrigo Giorgetto e TI como Data Custodian de "
            "infraestrutura e controles técnicos; participação da RentalHost é "
            "condicional ao ambiente e contrato, ambos sujeitos à homologação."
        ),
    }
    for field, expected in dmc_requirements.items():
        value = governance.get(field)
        if not isinstance(value, str):
            raise GovernanceValidationError(
                f"campo obrigatório de governança ausente no DMC: {field}"
            )
        if value.strip() != expected:
            raise GovernanceValidationError(
                f"atribuição canônica divergente para {field} no DMC; esperado {expected}"
            )

    architecture_pattern = (
        r"Data Model Canvas identifica Fabio Moreira como Data Owner;\s*"
        r"Felipe Rojas, Reinaldo Nobrega e Lucas Andrade como Data Stewards"
        r"[\s\S]{0,120}Rodrigo Giorgetto/TI como Data Custodian"
        r"[\s\S]{0,120}RentalHost na custódia externa"
    )
    if not re.search(architecture_pattern, architecture):
        raise GovernanceValidationError(
            "atribuições canônicas ausentes na Arquitetura de Negócio"
        )
    architecture_role_pairs = (
        (r"Fabio Moreira", r"Data Owner"),
        (r"(?:Felipe Rojas|Reinaldo Nobrega|Lucas Andrade)", r"Data Stewards?"),
        (r"Rodrigo Giorgetto(?:/TI)?", r"Data Custodian"),
    )
    for actor_pattern, role_pattern in architecture_role_pairs:
        if re.search(
            rf"\b(?:{actor_pattern})\b[^.\n]{{0,80}}"
            rf"\bnão\s+(?:é|atua(?:\s+como)?|exerce|possui)\b"
            rf"[^.\n]{{0,80}}\b(?:{role_pattern})\b",
            architecture,
            re.IGNORECASE,
        ):
            raise GovernanceValidationError(
                "a Arquitetura de Negócio contém atribuição de papel contraditória"
            )

    document_roles = {
        "Data Owner": "Fabio Moreira",
        "Data Steward": "Felipe Rojas, Reinaldo Nobrega e Lucas Andrade",
        "Data Custodian / TI": "Rodrigo Giorgetto / TI",
    }
    for role, expected in document_roles.items():
        if role_by_name[role][1] != expected:
            raise GovernanceValidationError(
                f"referência documental canônica divergente para {role}; esperado {expected}"
            )
    role_table_text = "\n".join(" | ".join(row) for row in role_rows)
    for tool in ("Trello", "Outlook", "RentalHost"):
        if tool in role_table_text:
            raise GovernanceValidationError(
                f"ferramenta ou fornecedor não pode ocupar papel de governança: {tool}"
            )

    actor_rows = table_rows(section, "Ator ou grupo", "Dados, sistemas ou etapa")
    actor_by_name = _rows_by_first_column(
        actor_rows, label="atribuições internas e externas", width=4
    )
    owner_actor = actor_by_name.get("Fabio Moreira / Data Owner")
    steward_actor = actor_by_name.get(
        "Felipe Rojas, Reinaldo Nobrega e Lucas Andrade / Data Stewards"
    )
    custodian_actor = actor_by_name.get("Rodrigo Giorgetto / TI / Data Custodian")
    rentalhost_actor = actor_by_name.get("RentalHost")
    tools_actor = actor_by_name.get(
        "SurveyMonkey, Trello, Outlook, n8n e provedor de nuvem"
    )
    required_actors = {
        "Fabio Moreira": owner_actor,
        "Stewards": steward_actor,
        "Rodrigo Giorgetto": custodian_actor,
        "RentalHost": rentalhost_actor,
        "Trello e Outlook": tools_actor,
    }
    missing_actors = [name for name, row in required_actors.items() if row is None]
    if missing_actors:
        raise GovernanceValidationError(
            "atores obrigatórios ausentes na cadeia de custódia: "
            + ", ".join(missing_actors)
        )

    assert owner_actor and steward_actor and custodian_actor
    assert rentalhost_actor and tools_actor
    if "autoridade formal ainda depende de homologação" not in owner_actor[3]:
        raise GovernanceValidationError(
            "autoridade do Data Owner deve permanecer pendente de homologação"
        )
    if not re.search(
        r"Felipe Fernandes Rojas[\s\S]{0,180}equivalência[\s\S]{0,100}deve ser confirmada",
        steward_actor[3],
    ):
        raise GovernanceValidationError(
            "equivalência entre Felipe Fernandes Rojas e Felipe Rojas deve permanecer pendente"
        )
    if "não localizado no TAPI" not in custodian_actor[3]:
        raise GovernanceValidationError(
            "Rodrigo Giorgetto não pode ser atribuído ao TAPI sem evidência"
        )
    if not re.search(r"Executar custódia técnica", rentalhost_actor[2]):
        raise GovernanceValidationError(
            "RentalHost deve permanecer limitada à custódia técnica"
        )
    if not re.search(
        r"Participação condicional[\s\S]{0,180}Não decide finalidade",
        rentalhost_actor[3],
    ):
        raise GovernanceValidationError(
            "RentalHost não pode receber autoridade de negócio"
        )
    if re.search(
        r"\b(?:decidir|decide|aprovar|aprova|definir)\b[\s\S]{0,80}"
        r"(?:finalidade|classificação|publicação)",
        rentalhost_actor[2],
        re.IGNORECASE,
    ):
        raise GovernanceValidationError(
            "RentalHost não pode receber autoridade de negócio"
        )
    if not all(tool in tools_actor[0] for tool in ("Trello", "Outlook")) or not re.search(
        r"dependem de inventário e contrato", tools_actor[3]
    ):
        raise GovernanceValidationError(
            "Trello e Outlook devem permanecer ferramentas com escopo pendente"
        )
    if re.search(
        r"Data Owner|Data Steward|Data Custodian|\b(?:aprovar|aprova|decidir|decide)\b",
        tools_actor[2],
        re.IGNORECASE,
    ):
        raise GovernanceValidationError(
            "Trello e Outlook não podem receber papel ou autoridade de governança"
        )

    legal_actor = actor_by_name.get(
        "Controlador, operadores, suboperadores e encarregado"
    )
    if legal_actor is None or re.search(
        r"\bEquivalem?\s+(?:ao|aos)\s+(?:Data )?(?:Owner|Steward|Custodian)",
        " | ".join(legal_actor[1:]),
        re.IGNORECASE,
    ):
        raise GovernanceValidationError(
            "papéis jurídicos não podem ser equiparados aos papéis organizacionais"
        )

    if re.search(r"já (?:está )?homologad", owner_actor[3], re.IGNORECASE):
        raise GovernanceValidationError(
            "autoridade do Data Owner contém homologação contraditória"
        )
    if len(re.findall(r"confirmad", steward_actor[3], re.IGNORECASE)) != 1 or re.search(
        r"não (?:corresponde|é a mesma)|já está confirmada|"
        r"\bpessoas?\s+(?:diferentes?|distintas?)\b|\bhomologad\w*\b",
        steward_actor[3],
        re.IGNORECASE,
    ):
        raise GovernanceValidationError(
            "equivalência entre os nomes de Felipe contém estado contraditório"
        )

    plain = re.sub(r"[*`]", "", section)
    if not re.search(
        r"não equivalem automaticamente a controlador, operador,[\s\S]{0,80}encarregado",
        plain,
        re.IGNORECASE,
    ):
        raise GovernanceValidationError(
            "papéis jurídicos não podem ser equiparados aos papéis organizacionais"
        )

    return {
        "role_evidence_sources": 4,
        "consistent_governance_roles": len(REQUIRED_GOVERNANCE_ROLES),
    }


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
    parser.add_argument("--dmc", type=Path, default=Path("docs/dmc.json"))
    parser.add_argument(
        "--architecture",
        type=Path,
        default=Path("docs/arquitetura-de-negocio.md"),
    )
    return parser


def _resolve_repository_path(path: Path, repository_root: Path) -> Path:
    return path if path.is_absolute() else repository_root / path


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        document_path = _resolve_repository_path(args.document, args.repository_root)
        document = load_document(document_path)
        summary = validate_document(document)
        validate_tapi_hash(document, args.tapi)
        tapi = load_document(args.tapi)
        architecture_path = _resolve_repository_path(
            args.architecture, args.repository_root
        )
        try:
            architecture = load_document(architecture_path)
        except GovernanceValidationError as error:
            raise GovernanceValidationError(
                f"não foi possível ler a Arquitetura de Negócio: {architecture_path}"
            ) from error
        dmc_path = _resolve_repository_path(args.dmc, args.repository_root)
        try:
            dmc = json.loads(dmc_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise GovernanceValidationError(
                f"não foi possível ler o DMC: {dmc_path}"
            ) from error
        if not isinstance(dmc, dict):
            raise GovernanceValidationError("a raiz do DMC deve ser um objeto JSON")
        summary |= validate_role_consistency(document, tapi, dmc, architecture)
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
        f"{summary['governance_roles']} papéis de governança; "
        f"{summary['catalog_common_fields']} campos comuns de catálogo; "
        f"{summary['catalog_asset_types']} tipos de ativo; "
        f"{summary['catalog_dimensions']} dimensões e "
        f"{summary['catalog_measures']} medidas no exemplo; "
        f"{summary['catalog_cubes']} cubos; "
        f"{summary['consistent_governance_roles']} papéis consistentes em "
        f"{summary['role_evidence_sources']} fontes de evidência; "
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
