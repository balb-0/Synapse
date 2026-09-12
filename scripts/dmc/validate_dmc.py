#!/usr/bin/env python3
"""Valida o contrato ampliado do JSON do Data Model Canvas."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

EXPECTED_CUBES = (
    "Portfólio e Ciclo",
    "Participação e Representatividade",
    "Pipeline Mensal",
    "Resultados e Questionários",
)
EXPECTED_CUBE_IDS = ("cubo-1", "cubo-2", "cubo-3", "cubo-4")
REQUIRED_TOP_LEVEL = (
    "schemaVersion",
    "metadata",
    "negocioEConsumo",
    "governancaCorporativa",
    "cubos",
    "taticas",
    "etl",
)
CORPORATE_LISTS = (
    "objetivosNegocio",
    "perguntasNegocio",
    "processosNegocio",
    "indicadoresConsumo",
    "usuariosCanais",
    "decisoesRiscos",
)
EXPECTED_USER_CHANNELS = tuple(f"UC{number:02d}" for number in range(1, 5))
EXPECTED_DECISIONS_RISKS = tuple(f"DR{number:02d}" for number in range(1, 7))
EXPECTED_CONSUMPTION_INDICATORS = tuple(f"I{number:02d}" for number in range(1, 26))
EXPECTED_BUSINESS_QUESTIONS = tuple(f"PB{number:02d}" for number in range(1, 14))
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
GOVERNANCE_ROLE_KEYS = ("owner", "steward", "custodian", "tecnico")
DIMENSIONAL_FIELDS = (
    "nome",
    "starSchema",
    "snowflakeSchema",
    "outroSchema",
    "transactionFact",
    "periodicSnapshot",
    "accumulatingSnapshot",
    "bridgeTables",
    "junkDimensions",
    "dimensoesConformadas",
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
    "diagramaMermaid",
)
DIMENSIONAL_LISTS = (
    "grao",
    "fatos",
    "metricas",
    "dimensoes",
    "fontes",
    "transformacoes",
    "qualidade",
    "scd",
)
METADATA_KEYS = ("parceiro", "data", "versao", "grupo")
EXPECTED_TACTIC_IDS = ("tatica-1", "tatica-2", "tatica-3")
TACTIC_FIELDS = (
    "problema",
    "qaDesempenho",
    "qaDisponibilidade",
    "qaEscalabilidade",
    "qaSeguranca",
    "qaModificabilidade",
    "qaCusto",
    "qaOutro",
    "tatica",
    "implementacao",
    "consequencias",
    "diagramaMermaid",
)
TACTIC_BOOLEAN_FIELDS = (
    "qaDesempenho",
    "qaDisponibilidade",
    "qaEscalabilidade",
    "qaSeguranca",
    "qaModificabilidade",
    "qaCusto",
)
TACTIC_REQUIRED_TEXT_FIELDS = (
    "problema",
    "tatica",
    "implementacao",
    "consequencias",
    "diagramaMermaid",
)
TACTIC_LISTS = ("alternativas", "evidencias")
ETL_FIELDS = (
    "orquestrador",
    "frequencia",
    "janelaExecucao",
    "dependencias",
    "estrategiaCarga",
    "idempotencia",
    "reprocessamento",
    "tratamentoFalha",
    "metricasTelemetria",
    "alertas",
    "linhagem",
    "custoEstimado",
    "diagramaMermaid",
)
ETL_LISTS = ("fontesExtracao", "camadas", "verificacoes")
VERSION_PATTERN = re.compile(r"^[1-9]\d*\.\d+$")


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
    return (
        value is None
        or value == ""
        or value is False
        or (
            isinstance(value, list)
            and all(item is None or item == "" or item is False for item in value)
        )
    )


def validate_document(document: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in REQUIRED_TOP_LEVEL if key not in document]
    if missing:
        raise DmcValidationError(f"seções obrigatórias ausentes: {', '.join(missing)}")
    if type(document["schemaVersion"]) is not int or document["schemaVersion"] != 1:
        raise DmcValidationError("schemaVersion deve ser 1")

    metadata = document["metadata"]
    if not isinstance(metadata, dict) or not all(
        isinstance(metadata.get(key), str) and metadata[key].strip() for key in METADATA_KEYS
    ):
        raise DmcValidationError("metadata deve preservar parceiro, data, versão e grupo")
    try:
        date.fromisoformat(metadata["data"])
    except ValueError as error:
        raise DmcValidationError(
            "metadata.data deve usar uma data ISO válida (AAAA-MM-DD)"
        ) from error
    if not VERSION_PATTERN.fullmatch(metadata["versao"]):
        raise DmcValidationError("metadata.versao deve usar o formato inteiro.inteiro")

    business = document["negocioEConsumo"]
    if not isinstance(business, dict) or not all(
        _nonempty_strings(business.get(key)) for key in CORPORATE_LISTS
    ):
        raise DmcValidationError("Negócio e Consumo Analítico perderam conteúdo obrigatório")
    user_channel_ids = tuple(item.partition(" — ")[0] for item in business["usuariosCanais"])
    if user_channel_ids != EXPECTED_USER_CHANNELS:
        raise DmcValidationError("usuários e canais devem corresponder a UC01–UC04")
    if not all(
        any(term in item for term in ("autorizado", "bloqueado", "sem acesso"))
        for item in business["usuariosCanais"]
    ):
        raise DmcValidationError("todo canal deve explicitar sua restrição de acesso")
    decision_ids = tuple(item.partition(" — ")[0] for item in business["decisoesRiscos"])
    if decision_ids != EXPECTED_DECISIONS_RISKS:
        raise DmcValidationError("decisões e riscos devem corresponder a DR01–DR06")
    if not all("Impacto:" in item and "Estado:" in item for item in business["decisoesRiscos"]):
        raise DmcValidationError("toda decisão ou risco deve informar impacto e estado")
    indicator_ids = tuple(
        indicator.partition(" — ")[0] for indicator in business["indicadoresConsumo"]
    )
    if indicator_ids != EXPECTED_CONSUMPTION_INDICATORS:
        raise DmcValidationError("indicadores de consumo devem corresponder a I01–I25")
    question_ids = tuple(question.partition(" — ")[0] for question in business["perguntasNegocio"])
    if question_ids != EXPECTED_BUSINESS_QUESTIONS:
        raise DmcValidationError("perguntas de negócio devem corresponder a PB01–PB13")
    if not all(
        objective.startswith("Resultado pretendido:") for objective in business["objetivosNegocio"]
    ):
        raise DmcValidationError("objetivos devem ser identificados como resultados pretendidos")
    if not all(process.startswith("Processo atual:") for process in business["processosNegocio"]):
        raise DmcValidationError("processos devem preservar seu estado atual")

    governance = document["governancaCorporativa"]
    if (
        not isinstance(governance, dict)
        or any(key not in governance for key in GOVERNANCE_KEYS)
        or not all(
            isinstance(governance[key], str) and governance[key].strip() for key in GOVERNANCE_KEYS
        )
    ):
        raise DmcValidationError("Governança Corporativa deve permanecer preenchida")
    if not all(
        governance[key].startswith("Baseline documental:") and "homologa" in governance[key].lower()
        for key in GOVERNANCE_ROLE_KEYS
    ):
        raise DmcValidationError(
            "papéis de governança devem indicar fonte documental e homologação pendente"
        )
    if "RentalHost" not in governance["custodian"] or "condicional" not in governance["custodian"]:
        raise DmcValidationError("custódia externa deve permanecer condicional")

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

        unexpected_fields = sorted(set(fields) - set(DIMENSIONAL_FIELDS))
        unexpected_lists = sorted(set(lists) - set(DIMENSIONAL_LISTS))
        if unexpected_fields or unexpected_lists:
            unexpected = [f"fields.{key}" for key in unexpected_fields]
            unexpected.extend(f"lists.{key}" for key in unexpected_lists)
            raise DmcValidationError(
                f"cubo {cube['id']} contém campos desconhecidos: {', '.join(unexpected)}"
            )

        missing_fields = [key for key in DIMENSIONAL_FIELDS if key not in fields]
        missing_lists = [key for key in DIMENSIONAL_LISTS if key not in lists]
        if missing_fields or missing_lists:
            missing_keys = [f"fields.{key}" for key in missing_fields]
            missing_keys.extend(f"lists.{key}" for key in missing_lists)
            raise DmcValidationError(
                f"cubo {cube['id']} não preenche o contrato: {', '.join(missing_keys)}"
            )

        boolean_fields = (
            "starSchema",
            "snowflakeSchema",
            "transactionFact",
            "periodicSnapshot",
            "accumulatingSnapshot",
            "classificacaoPublico",
            "classificacaoInterno",
            "classificacaoConfidencial",
            "classificacaoRestrito",
            "dadoPessoal",
            "dadoSensivel",
            "dadoCritico",
        )
        if any(type(fields[key]) is not bool for key in boolean_fields):
            raise DmcValidationError(
                f"cubo {cube['id']} deve usar booleanos nos seletores e classificações"
            )

        classification_fields = (
            "classificacaoPublico",
            "classificacaoInterno",
            "classificacaoConfidencial",
            "classificacaoRestrito",
        )
        if sum(fields[key] for key in classification_fields) != 1:
            raise DmcValidationError(
                f"cubo {cube['id']} deve selecionar exatamente uma classificação"
            )
        if fields["dadoPessoal"] and not fields["classificacaoRestrito"]:
            raise DmcValidationError(
                f"cubo {cube['id']} com dado pessoal deve ser classificado como restrito"
            )

        text_fields = (
            "nome",
            "outroSchema",
            "bridgeTables",
            "junkDimensions",
            "dimensoesConformadas",
            "particionamento",
            "materializacoesAgregacoes",
            "indicesClusteringOrdenacao",
            "queriesCriticas",
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
            "diagramaMermaid",
        )
        if any(not isinstance(fields[key], str) or not fields[key].strip() for key in text_fields):
            raise DmcValidationError(f"cubo {cube['id']} deve preencher todos os campos textuais")

        name = fields.get("nome")
        if not isinstance(name, str) or not name.strip():
            raise DmcValidationError(f"cubo {cube['id']} deve ter nome")
        names.append(name)

        schemas = (
            fields.get("starSchema") is True,
            fields.get("snowflakeSchema") is True,
        )
        if sum(schemas) != 1:
            raise DmcValidationError(f"cubo {name} deve selecionar exatamente um esquema")

        fact_types = (
            fields.get("transactionFact") is True,
            fields.get("periodicSnapshot") is True,
            fields.get("accumulatingSnapshot") is True,
        )
        is_factless_association = cube["id"] == "cubo-4" and sum(fact_types) == 0
        if sum(fact_types) != 1 and not is_factless_association:
            raise DmcValidationError(f"cubo {name} deve selecionar exatamente um tipo de fato")

        for key in DIMENSIONAL_LISTS:
            if not _nonempty_strings(lists.get(key)):
                raise DmcValidationError(f"cubo {name} deve preencher {key}")
            normalized_items = [item.strip().casefold() for item in lists[key]]
            if len(normalized_items) != len(set(normalized_items)):
                raise DmcValidationError(f"cubo {name} contém itens duplicados em {key}")

    if tuple(names) != EXPECTED_CUBES:
        raise DmcValidationError("nomes ou ordem dos cubos divergem do contrato da Sprint")

    tactics = document["taticas"]
    if not isinstance(tactics, list) or len(tactics) != len(EXPECTED_TACTIC_IDS):
        raise DmcValidationError(
            f"o canvas deve conter {len(EXPECTED_TACTIC_IDS)} táticas arquiteturais"
        )
    tactic_ids: list[str] = []
    for tactic in tactics:
        if not isinstance(tactic, dict):
            raise DmcValidationError("cada tática deve ser um objeto")
        tactic_id = tactic.get("id")
        fields = tactic.get("fields")
        lists = tactic.get("lists")
        if not isinstance(tactic_id, str) or not tactic_id:
            raise DmcValidationError("toda tática deve ter ID")
        tactic_ids.append(tactic_id)
        if not isinstance(fields, dict) or not isinstance(lists, dict):
            raise DmcValidationError(f"tática {tactic_id} deve conter fields e lists")
        if set(fields) != set(TACTIC_FIELDS) or set(lists) != set(TACTIC_LISTS):
            raise DmcValidationError(f"tática {tactic_id} diverge do esquema oficial")
        if any(type(fields[key]) is not bool for key in TACTIC_BOOLEAN_FIELDS):
            raise DmcValidationError(f"tática {tactic_id} deve usar booleanos nos atributos")
        if (
            not any(fields[key] for key in TACTIC_BOOLEAN_FIELDS)
            and not str(fields["qaOutro"]).strip()
        ):
            raise DmcValidationError(f"tática {tactic_id} deve selecionar um atributo de qualidade")
        if any(
            not isinstance(fields[key], str) or not fields[key].strip()
            for key in TACTIC_REQUIRED_TEXT_FIELDS
        ):
            raise DmcValidationError(f"tática {tactic_id} possui campo textual obrigatório vazio")
        if not isinstance(fields["qaOutro"], str):
            raise DmcValidationError(f"tática {tactic_id} possui qaOutro inválido")
        if any(not _nonempty_strings(lists[key]) for key in TACTIC_LISTS):
            raise DmcValidationError(f"tática {tactic_id} deve preencher alternativas e evidências")
    if tuple(tactic_ids) != EXPECTED_TACTIC_IDS:
        raise DmcValidationError("IDs ou ordem das táticas divergem do contrato")

    etl = document["etl"]
    if not isinstance(etl, dict):
        raise DmcValidationError("ETL deve ser um objeto")
    etl_fields = etl.get("fields")
    etl_lists = etl.get("lists")
    if not isinstance(etl_fields, dict) or not isinstance(etl_lists, dict):
        raise DmcValidationError("ETL deve conter fields e lists")
    if set(etl_fields) != set(ETL_FIELDS) or set(etl_lists) != set(ETL_LISTS):
        raise DmcValidationError("ETL diverge do esquema oficial")
    if any(
        not isinstance(etl_fields[key], str) or not etl_fields[key].strip() for key in ETL_FIELDS
    ):
        raise DmcValidationError("ETL possui campo obrigatório vazio")
    if any(not _nonempty_strings(etl_lists[key]) for key in ETL_LISTS):
        raise DmcValidationError("ETL deve preencher fontes, camadas e verificações")

    return {
        "schemaVersion": 1,
        "cubos": names,
        "taticas": tactic_ids,
        "etl": True,
    }


def validate_preserved_sections(document: dict[str, Any], baseline: dict[str, Any]) -> None:
    changed = sorted(set(document) | set(baseline)) if document != baseline else []
    if changed:
        changed = [key for key in changed if document.get(key) != baseline.get(key)]
    if changed:
        raise DmcValidationError(f"round-trip alterou o documento nas seções: {', '.join(changed)}")


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
        f"{len(summary['cubos'])} cubos; {len(summary['taticas'])} táticas; "
        "ETL, Modelo, Dados e Governança preenchidos"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
