#!/usr/bin/env python3
"""Perfilador local e determinístico das bases da Central de Pesquisas.

O programa lê CSVs delimitados por ``;`` e somente grava agregados no diretório
de saída indicado. Ele não altera os arquivos de entrada e não grava amostras,
respostas, e-mails ou nomes de empresas nos resultados.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_MANIFEST = SCRIPT_DIR / "manifest.json"
OUTPUT_NAMES = (
    "resumo.csv",
    "campos.csv",
    "dominios.csv",
    "relacionamentos.csv",
    "datas.csv",
    "coerencia_temporal.csv",
    "identidades.csv",
    "nulos_condicionais.csv",
    "percentuais.csv",
    "denormalizados.csv",
    "dicionario_validacao.csv",
    "manifesto_aplicado.json",
)
RELATION_FIELDS = [
    "relacao", "origem", "chave_origem", "referencia", "chave_referencia",
    "linhas_origem", "comparaveis", "encontradas", "orfãs", "percentual_orfas",
    "chaves_origem_distintas", "chaves_orfas_distintas", "status", "interpretação",
]
DATE_FIELDS = [
    "source", "column", "nulos", "nao_nulos", "parseaveis", "nao_parseaveis",
    "pct_parseaveis_sobre_nao_nulos", "minimo", "maximo",
]
TEMPORAL_FIELDS = [
    "checagem", "fonte", "coluna_a", "coluna_b", "comparaveis", "violacoes",
    "percentual_violacoes", "status", "limiar",
]
IDENTITY_FIELDS = [
    "checagem", "sistema_a", "sistema_b", "distintos_a", "distintos_b",
    "intersecao", "somente_a", "somente_b", "observacao",
]
CONDITIONAL_FIELDS = [
    "source", "column", "tipo_questao", "total", "aplicavel", "nao_aplicavel",
    "presentes_aplicavel", "ausentes_aplicavel", "ausencias_inesperadas",
    "ausencias_condicionais", "preenchidos_nao_aplicavel", "percentual_inesperadas",
    "status",
]
PERCENT_FIELDS = [
    "source", "column", "total", "nao_nulos", "sentinelas", "parseaveis",
    "invalidos", "fora_0_100", "pct_parseaveis", "pct_invalidos", "pct_fora_0_100",
    "status",
]
DENORMALIZED_FIELDS = [
    "checagem", "origem", "referencia", "chave", "comparaveis", "coincidentes",
    "divergencias", "percentual_divergencias", "ids_divergentes", "status", "observacao",
]
DICTIONARY_FIELDS = [
    "arquivo", "variavel", "status", "cardinalidade_dicionario", "cardinalidade_medida",
    "divergencia_cardinalidade", "nulos_dicionario", "nulos_fisicos", "sentinelas",
    "nulos_semanticos", "divergencia_dicionario_vs_fisico",
    "divergencia_dicionario_vs_semantico", "minimo_dicionario", "maximo_dicionario",
    "minimo_medido", "maximo_medido", "observacao",
]


class ProfileError(Exception):
    """Falha de arquivo ou de schema que deve interromper o perfilamento."""


def fail(message: str) -> ProfileError:
    return ProfileError(message)


def is_null(value: str | None) -> bool:
    return value is None or not value.strip()


def normalized(value: str | None) -> str | None:
    if is_null(value):
        return None
    return value.strip()


def canonical_key(value: str | None) -> str | None:
    value = normalized(value)
    return value.casefold() if value is not None else None


def configured_sentinels(source: dict[str, Any], column: str) -> set[str]:
    sentinels = source.get("sentinels", {}).get(column, [])
    return {str(value).strip().casefold() for value in sentinels}


def is_sentinel(value: str | None, source: dict[str, Any], column: str) -> bool:
    value = normalized(value)
    return value is not None and value.casefold() in configured_sentinels(source, column)


def semantic_missing(value: str | None, source: dict[str, Any], column: str) -> bool:
    return is_null(value) or is_sentinel(value, source, column)


def comparison_key(value: str | None, source: dict[str, Any], column: str) -> str | None:
    if semantic_missing(value, source, column):
        return None
    return canonical_key(value)


def hash_domain(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"<hash:{digest}>"


def pct(count: int, total: int) -> str:
    if total == 0:
        return "0,0%"
    value = (Decimal(count) * Decimal(100) / Decimal(total)).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )
    return f"{value:.1f}".replace(".", ",") + "%"


def parse_number(value: str | None) -> Decimal | None:
    """Converte números brasileiros e percentuais sem inferir nulos como zero."""

    value = normalized(value)
    if value is None:
        return None
    text = value.replace("%", "").replace(" ", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


DATE_FORMATS = (
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
)


def parse_date(value: str | None) -> datetime | None:
    value = normalized(value)
    if value is None:
        return None
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue
    return None


def date_text(value: datetime | None) -> str:
    return value.isoformat(sep=" ") if value else ""


def read_manifest(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            manifest = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise fail(f"[manifesto] não foi possível ler {path.name}: {exc}") from exc
    if not isinstance(manifest, dict) or not isinstance(manifest.get("sources"), list):
        raise fail("[manifesto] 'sources' deve ser uma lista")
    return manifest


def source_by_id(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for source in manifest["sources"]:
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id:
            raise fail("[manifesto] cada fonte precisa de um 'id' não vazio")
        if source_id in result:
            raise fail(f"[manifesto] fonte duplicada: {source_id}")
        result[source_id] = source
    return result


def header_names(raw_header: list[str]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    empty_index = 0
    for raw_name in raw_header:
        name = raw_name.strip()
        if not name:
            empty_index += 1
            name = f"__empty_{empty_index:02d}"
        if name in seen:
            raise fail(f"[schema] coluna duplicada no cabeçalho: {name}")
        seen.add(name)
        names.append(name)
    return names


def read_source(input_dir: Path, source: dict[str, Any]) -> dict[str, Any]:
    candidates = [source["file"], *source.get("aliases", [])]
    file_path = next((input_dir / candidate for candidate in candidates if (input_dir / candidate).is_file()), None)
    if file_path is None:
        expected = ", ".join(candidates)
        raise fail(f"[arquivo] fonte {source['id']} ausente; esperado um de: {expected}")

    rows: list[dict[str, str]] = []
    try:
        with file_path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, delimiter=";", strict=True)
            try:
                raw_header = next(reader)
            except StopIteration as exc:
                raise fail(f"[schema] arquivo vazio: {file_path.name}") from exc
            names = header_names(raw_header)
            expected_columns = list(source.get("columns", []))
            missing = sorted(set(expected_columns) - set(names))
            unexpected = sorted(
                set(names) - set(expected_columns) - {name for name in names if name.startswith("__empty_")}
            )
            expected_empty = int(source.get("empty_header_columns", 0))
            actual_empty = sum(name.startswith("__empty_") for name in names)
            if missing:
                raise fail(f"[schema] {file_path.name}: colunas ausentes: {', '.join(missing)}")
            if unexpected:
                raise fail(f"[schema] {file_path.name}: colunas inesperadas: {', '.join(unexpected)}")
            if actual_empty != expected_empty:
                raise fail(
                    f"[schema] {file_path.name}: esperado {expected_empty} cabeçalho(s) vazio(s), "
                    f"encontrado(s) {actual_empty}"
                )
            for line_number, values in enumerate(reader, start=2):
                if len(values) != len(names):
                    raise fail(
                        f"[schema] {file_path.name}, linha {line_number}: "
                        f"esperadas {len(names)} colunas, encontradas {len(values)}"
                    )
                rows.append(dict(zip(names, values)))
    except ProfileError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise fail(f"[arquivo] falha ao ler {file_path.name}: {exc}") from exc

    return {
        "id": source["id"],
        "configured_file": source["file"],
        "file_used": file_path.name,
        "columns": names,
        "rows": rows,
        "config": source,
    }


def key_tuple(row: dict[str, str], key_columns: list[str], source: dict[str, Any]) -> tuple[str, ...] | None:
    values = tuple(comparison_key(row.get(column), source, column) for column in key_columns)
    if any(value is None for value in values):
        return None
    return values  # type: ignore[return-value]


def duplicate_extra(rows: Iterable[dict[str, str]], columns: list[str]) -> tuple[int, int]:
    counts = Counter(tuple(row.get(column, "") for column in columns) for row in rows)
    groups = sum(count > 1 for count in counts.values())
    extras = sum(count - 1 for count in counts.values() if count > 1)
    return groups, extras


def profile_summary(data: dict[str, Any]) -> dict[str, Any]:
    rows = data["rows"]
    columns = data["columns"]
    groups, extras = duplicate_extra(rows, columns)
    key_columns = data["config"].get("key", [])
    key_values = [key_tuple(row, key_columns, data["config"]) for row in rows]
    key_counts = Counter(value for value in key_values if value is not None)
    key_groups = sum(count > 1 for count in key_counts.values())
    key_extras = sum(count - 1 for count in key_counts.values() if count > 1)
    empty_data = [column for column in columns if all(is_null(row.get(column)) for row in rows)]
    semantic_empty = [
        column for column in columns
        if all(semantic_missing(row.get(column), data["config"], column) for row in rows)
    ]
    incomplete_keys = sum(value is None for value in key_values)
    return {
        "source": data["id"],
        "file_configurado": data["configured_file"],
        "arquivo_lido": data["file_used"],
        "registros": len(rows),
        "colunas": len(columns),
        "colunas_cabecalho_vazio": sum(column.startswith("__empty_") for column in columns),
        "colunas_sem_dado": len(empty_data),
        "colunas_sem_dado_semantico": len(semantic_empty),
        "linhas_duplicadas_extras": extras,
        "grupos_linhas_duplicadas": groups,
        "chave": ", ".join(key_columns),
        "linhas_chave_duplicadas_extras": key_extras,
        "grupos_chave_duplicados": key_groups,
        "linhas_chave_incompleta": incomplete_keys,
        "completude_chave": pct(len(rows) - incomplete_keys, len(rows)),
        "status_unicidade_chave": "UNICA" if key_extras == 0 else "DUPLICADA",
        "status_completude_chave": "COMPLETA" if incomplete_keys == 0 else "INCOMPLETA",
        "status_schema": "OK",
    }


def infer_type(source: dict[str, Any], column: str, values: list[str]) -> str:
    if column.startswith("__empty_"):
        return "coluna_vazia"
    if column in source.get("percent_columns", []):
        return "percentual"
    if column in source.get("date_columns", []):
        return "data_hora" if any(" " in (normalized(value) or "") for value in values) else "data"
    non_null = [value for value in values if not is_null(value)]
    if non_null and all(parse_number(value) is not None for value in non_null):
        return "numerica"
    return "texto"


def profile_fields(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = data["rows"]
    result: list[dict[str, Any]] = []
    for column in data["columns"]:
        values = [row.get(column, "") for row in rows]
        physical_nulls = sum(is_null(value) for value in values)
        sentinels = sum(is_sentinel(value, data["config"], column) for value in values)
        semantic_nulls = physical_nulls + sentinels
        comparable = [
            value for value in values
            if not semantic_missing(value, data["config"], column)
        ]
        result.append(
            {
                "source": data["id"],
                "column": column,
                "tipo_inferido": infer_type(data["config"], column, values),
                "nulos": physical_nulls,
                "pct_nulos": pct(physical_nulls, len(values)),
                "sentinelas": sentinels,
                "nulos_semanticos": semantic_nulls,
                "pct_nulos_semanticos": pct(semantic_nulls, len(values)),
                "distintos": len(set(comparable)),
                "completude": pct(len(values) - semantic_nulls, len(values)),
            }
        )
    return result


def profile_domains(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = data["rows"]
    configured = data["config"].get("domain_columns", {})
    result: list[dict[str, Any]] = []
    for column, mode in configured.items():
        counts: Counter[str] = Counter()
        for row in rows:
            value = normalized(row.get(column))
            if value is None:
                label = "<VAZIO>"
            elif is_sentinel(value, data["config"], column):
                label = f"<SENTINELA:{value}>"
            elif mode == "hash":
                label = hash_domain(value)
            else:
                label = value
            counts[label] += 1
        for label, count in sorted(counts.items(), key=lambda item: (item[0].casefold(), item[0])):
            result.append(
                {
                    "source": data["id"],
                    "column": column,
                    "dominio": label,
                    "ocorrencias": count,
                    "percentual": pct(count, len(rows)),
                }
            )
    return result


def profile_dates(data: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    rows = data["rows"]
    for column in data["config"].get("date_columns", []):
        parsed = [parse_date(row.get(column)) for row in rows]
        non_null = [row.get(column, "") for row in rows if not is_null(row.get(column))]
        valid = [value for value in parsed if value is not None]
        result.append(
            {
                "source": data["id"],
                "column": column,
                "nulos": len(rows) - len(non_null),
                "nao_nulos": len(non_null),
                "parseaveis": len(valid),
                "nao_parseaveis": len(non_null) - len(valid),
                "pct_parseaveis_sobre_nao_nulos": pct(len(valid), len(non_null)),
                "minimo": date_text(min(valid)) if valid else "",
                "maximo": date_text(max(valid)) if valid else "",
            }
        )
    return result


def relation_rows(data_by_id: dict[str, dict[str, Any]], manifest: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for relation in manifest.get("relations", []):
        child = data_by_id[relation["child"]]
        parent = data_by_id[relation["parent"]]
        child_key = relation["child_key"]
        parent_key = relation["parent_key"]
        parent_values = {
            key_tuple(row, parent_key, parent["config"])
            for row in parent["rows"]
            if key_tuple(row, parent_key, parent["config"]) is not None
        }
        comparable = 0
        matched = 0
        child_values: set[tuple[str, ...]] = set()
        orphan_values: set[tuple[str, ...]] = set()
        for row in child["rows"]:
            value = key_tuple(row, child_key, child["config"])
            if value is None:
                continue
            comparable += 1
            child_values.add(value)
            if value in parent_values:
                matched += 1
            else:
                orphan_values.add(value)
        orphan = comparable - matched
        result.append(
            {
                "relacao": relation["name"],
                "origem": relation["child"],
                "chave_origem": ", ".join(child_key),
                "referencia": relation["parent"],
                "chave_referencia": ", ".join(parent_key),
                "linhas_origem": len(child["rows"]),
                "comparaveis": comparable,
                "encontradas": matched,
                "orfãs": orphan,
                "percentual_orfas": pct(orphan, comparable),
                "chaves_origem_distintas": len(child_values),
                "chaves_orfas_distintas": len(orphan_values),
                "status": "OK" if orphan == 0 else "ORFAOS_DETECTADOS",
                "interpretação": relation.get("interpretation", "Conferir a chave antes de agregar."),
            }
        )
    return result


def identity_rows(data_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    required_sources = {"pesquisas", "respondentes", "questoes", "respostas", "clientes"}
    if not required_sources.issubset(data_by_id):
        return []

    def values(source_id: str, column: str) -> set[str]:
        output: set[str] = set()
        source = data_by_id[source_id]["config"]
        for row in data_by_id[source_id]["rows"]:
            value = comparison_key(row.get(column), source, column)
            if value is None:
                continue
            output.add(value)
        return output

    result: list[dict[str, Any]] = []
    id_sets = {
        "pesquisas.id": values("pesquisas", "id"),
        "respondentes.id_pesq": values("respondentes", "id_pesq"),
        "questoes.pesquisa_id": values("questoes", "pesquisa_id"),
        "respostas.pesquisa_id": values("respostas", "pesquisa_id"),
    }
    id_names = list(id_sets)
    for index, left_name in enumerate(id_names):
        for right_name in id_names[index + 1 :]:
            left = id_sets[left_name]
            right = id_sets[right_name]
            result.append(
                {
                    "checagem": "ids_pesquisa_multi_sistema",
                    "sistema_a": left_name,
                    "sistema_b": right_name,
                    "distintos_a": len(left),
                    "distintos_b": len(right),
                    "intersecao": len(left & right),
                    "somente_a": len(left - right),
                    "somente_b": len(right - left),
                    "observacao": "IDs somente de um sistema exigem identidade canônica antes de KPI cruzado.",
                }
            )

    clients = values("clientes", "id_cliente")
    respondent_clients = values("respondentes", "id_cliente")
    result.append(
        {
            "checagem": "id_cliente",
            "sistema_a": "clientes.id_cliente",
            "sistema_b": "respondentes.id_cliente",
            "distintos_a": len(clients),
            "distintos_b": len(respondent_clients),
            "intersecao": len(clients & respondent_clients),
            "somente_a": len(clients - respondent_clients),
            "somente_b": len(respondent_clients - clients),
            "observacao": "Comparação textual normalizada; o tipo declarado difere entre as fontes.",
        }
    )

    response_ids = values("respostas", "respondent_id")
    result.append(
        {
            "checagem": "respondent_id_sem_chave_explicita",
            "sistema_a": "respostas.respondent_id",
            "sistema_b": "respondentes (sem respondent_id)",
            "distintos_a": len(response_ids),
            "distintos_b": 0,
            "intersecao": 0,
            "somente_a": len(response_ids),
            "somente_b": 0,
            "observacao": "Não declarar órfão: a base de respondentes não oferece essa chave.",
        }
    )
    return result


def conditional_null_rows(
    data_by_id: dict[str, dict[str, Any]], manifest: dict[str, Any]
) -> list[dict[str, Any]]:
    if not {"respostas", "questoes"}.issubset(data_by_id):
        return []
    question_types = {
        (
            comparison_key(row.get("pesquisa_id"), data_by_id["questoes"]["config"], "pesquisa_id"),
            comparison_key(row.get("id_pergunta"), data_by_id["questoes"]["config"], "id_pergunta"),
        ): normalized(row.get("tipo")) or "<TIPO_AUSENTE>"
        for row in data_by_id["questoes"]["rows"]
    }
    rules = manifest.get("conditional_nulls", {}).get("respostas", {})
    result: list[dict[str, Any]] = []
    response_config = data_by_id["respostas"]["config"]
    for column, rule in rules.items():
        applicable_types = set(rule.get("applicable_types", []))
        required_types = set(rule.get("required_types", []))
        by_type: dict[str, Counter[str]] = {}
        for row in data_by_id["respostas"]["rows"]:
            question_key = (
                comparison_key(row.get("pesquisa_id"), response_config, "pesquisa_id"),
                comparison_key(row.get("id_pergunta"), response_config, "id_pergunta"),
            )
            question_type = question_types.get(question_key, "<TIPO_DESCONHECIDO>")
            counter = by_type.setdefault(question_type, Counter())
            applicable = question_type in applicable_types
            required = question_type in required_types
            missing = semantic_missing(row.get(column), response_config, column)
            counter["total"] += 1
            counter["applicable"] += applicable
            counter["not_applicable"] += not applicable
            if missing and applicable and required:
                counter["unexpected_missing"] += 1
            elif missing and applicable:
                counter["conditional_missing"] += 1
            elif missing:
                counter["not_applicable_missing"] += 1
            elif applicable:
                counter["present_applicable"] += 1
            else:
                counter["present_not_applicable"] += 1
        for question_type, counter in sorted(by_type.items()):
            result.append(
                {
                    "source": "respostas",
                    "column": column,
                    "tipo_questao": question_type,
                    "total": counter["total"],
                    "aplicavel": counter["applicable"],
                    "nao_aplicavel": counter["not_applicable"],
                    "presentes_aplicavel": counter["present_applicable"],
                    "ausentes_aplicavel": counter["unexpected_missing"] + counter["conditional_missing"],
                    "ausencias_inesperadas": counter["unexpected_missing"],
                    "ausencias_condicionais": counter["conditional_missing"] + counter["not_applicable_missing"],
                    "preenchidos_nao_aplicavel": counter["present_not_applicable"],
                    "percentual_inesperadas": pct(counter["unexpected_missing"], counter["applicable"]),
                    "status": "OK" if counter["unexpected_missing"] == 0 else "AUSENCIA_INESPERADA",
                }
            )
    return result


def percentage_rows(data_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for data in data_by_id.values():
        for column in data["config"].get("percent_columns", []):
            values = [row.get(column, "") for row in data["rows"]]
            sentinel_count = sum(is_sentinel(value, data["config"], column) for value in values)
            candidates = [
                value for value in values
                if not semantic_missing(value, data["config"], column)
            ]
            parsed = [parse_number(value) for value in candidates]
            invalid = sum(number is None for number in parsed)
            out_of_range = sum(number is not None and not Decimal("0") <= number <= Decimal("100") for number in parsed)
            result.append(
                {
                    "source": data["id"],
                    "column": column,
                    "total": len(values),
                    "nao_nulos": len(candidates),
                    "sentinelas": sentinel_count,
                    "parseaveis": len(candidates) - invalid,
                    "invalidos": invalid,
                    "fora_0_100": out_of_range,
                    "pct_parseaveis": pct(len(candidates) - invalid, len(candidates)),
                    "pct_invalidos": pct(invalid, len(candidates)),
                    "pct_fora_0_100": pct(out_of_range, len(candidates)),
                    "status": "OK" if invalid == 0 and out_of_range == 0 else "PERCENTUAL_INVALIDO",
                }
            )
    return result


def denormalized_rows(data_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    if not {"questoes", "pesquisas"}.issubset(data_by_id):
        return []
    research = data_by_id["pesquisas"]
    questions = data_by_id["questoes"]
    titles = {
        comparison_key(row.get("id"), research["config"], "id"): normalized(row.get("titulo"))
        for row in research["rows"]
    }
    comparable = 0
    matching = 0
    divergent_ids: set[str] = set()
    for row in questions["rows"]:
        research_id = comparison_key(row.get("pesquisa_id"), questions["config"], "pesquisa_id")
        if research_id is None or research_id not in titles:
            continue
        comparable += 1
        if normalized(row.get("pesquisa_titulo")) == titles[research_id]:
            matching += 1
        else:
            divergent_ids.add(research_id)
    divergences = comparable - matching
    return [
        {
            "checagem": "questoes.pesquisa_titulo_vs_pesquisas.titulo",
            "origem": "questoes",
            "referencia": "pesquisas",
            "chave": "pesquisa_id",
            "comparaveis": comparable,
            "coincidentes": matching,
            "divergencias": divergences,
            "percentual_divergencias": pct(divergences, comparable),
            "ids_divergentes": ",".join(sorted(divergent_ids, key=lambda value: int(value) if value.isdigit() else value)),
            "status": "OK" if divergences == 0 else "DIVERGENCIAS_DETECTADAS",
            "observacao": "Título denormalizado não substitui a dimensão canônica da pesquisa.",
        }
    ]


def parse_claim_integer(text: str, pattern: str) -> int | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match is None:
        return None
    return int(match.group(1).replace(".", ""))


def validate_dictionary(
    dictionary_path: Path, manifest: dict[str, Any], data_by_id: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    config = manifest.get("dictionary", {})
    expected_columns = list(config.get("required_columns", []))
    expected_variables = list(config.get("required_variables", []))
    try:
        with dictionary_path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream, delimiter=",", strict=True)
            actual_columns = reader.fieldnames or []
            if actual_columns != expected_columns:
                raise fail(
                    f"[dicionário] cabeçalho incompatível: esperado {expected_columns}, encontrado {actual_columns}"
                )
            rows = list(reader)
    except ProfileError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise fail(f"[dicionário] falha ao ler {dictionary_path.name}: {exc}") from exc
    variables = [normalized(row.get("Variável")) for row in rows]
    if variables != expected_variables:
        missing = sorted(set(expected_variables) - set(variables))
        unexpected = sorted(set(variables) - set(expected_variables))
        raise fail(
            f"[dicionário] variáveis incompatíveis; ausentes={missing}; inesperadas={unexpected}"
        )
    for row in rows:
        for column in config.get("required_nonempty_columns", []):
            if is_null(row.get(column)):
                raise fail(f"[dicionário] conteúdo mínimo ausente em {row['Variável']}.{column}")

    response = data_by_id.get("respostas")
    if response is None:
        raise fail("[dicionário] fonte respostas ausente para validar conteúdo")
    measured_rows: list[dict[str, Any]] = []
    for variable, dictionary_row in zip(expected_variables, rows):
        claim_text = dictionary_row.get("Valores ou Domínio Esperado", "")
        cardinality_claim = parse_claim_integer(
            claim_text, r"([0-9.]+)\s+(?:valores únicos|categorias)"
        )
        if "sem nulos" in claim_text.casefold():
            null_claim = 0
        else:
            null_claim = parse_claim_integer(claim_text, r"([0-9.]+)\s+nulos")

        values = [row.get(variable, "") for row in response["rows"]]
        physical = sum(is_null(value) for value in values)
        sentinels = sum(is_sentinel(value, response["config"], variable) for value in values)
        semantic = physical + sentinels
        comparable = [
            normalized(value) for value in values if not is_null(value)
        ]
        measured_cardinality = len(set(value for value in comparable if value is not None))

        range_start = parse_claim_integer(claim_text, r"(?:sequencial,|de)\s*([0-9.]+)\s+a")
        range_end = parse_claim_integer(claim_text, r"(?:sequencial,|de)\s*[0-9.]+\s+a\s*([0-9.]+)")
        measured_numbers = [parse_number(value) for value in comparable]
        measured_numbers = [number for number in measured_numbers if number is not None]
        measured_min = min(measured_numbers) if measured_numbers else None
        measured_max = max(measured_numbers) if measured_numbers else None

        cardinality_delta = (
            measured_cardinality - cardinality_claim if cardinality_claim is not None else ""
        )
        physical_delta = null_claim - physical if null_claim is not None else ""
        semantic_delta = null_claim - semantic if null_claim is not None else ""
        mismatch = (
            (cardinality_claim is not None and cardinality_delta != 0)
            or (null_claim is not None and semantic_delta != 0)
            or (range_start is not None and (measured_min is None or measured_min != range_start))
            or (range_end is not None and (measured_max is None or measured_max != range_end))
        )
        if mismatch:
            raise fail(
                f"[dicionário] alegação incompatível em {variable}: "
                f"cardinalidade={cardinality_claim}/{measured_cardinality}; "
                f"nulos={null_claim}/{semantic}"
            )
        if null_claim is None:
            observation = "Sem alegação de nulos; nenhuma exigência foi inventada."
        elif physical_delta:
            observation = "A diferença entre a alegação e vazios físicos é explicada por sentinelas configuradas."
        else:
            observation = "Alegações verificáveis de cardinalidade e nulos conferem."
        measured_rows.append(
            {
                "arquivo": dictionary_path.name,
                "variavel": variable,
                "status": "OK" if not mismatch else "INCOMPATIVEL",
                "cardinalidade_dicionario": cardinality_claim if cardinality_claim is not None else "",
                "cardinalidade_medida": measured_cardinality,
                "divergencia_cardinalidade": cardinality_delta,
                "nulos_dicionario": null_claim if null_claim is not None else "",
                "nulos_fisicos": physical,
                "sentinelas": sentinels,
                "nulos_semanticos": semantic,
                "divergencia_dicionario_vs_fisico": physical_delta,
                "divergencia_dicionario_vs_semantico": semantic_delta,
                "minimo_dicionario": range_start if range_start is not None else "",
                "maximo_dicionario": range_end if range_end is not None else "",
                "minimo_medido": measured_min if measured_min is not None else "",
                "maximo_medido": measured_max if measured_max is not None else "",
                "observacao": observation,
            }
        )
    return measured_rows


def temporal_rows(data_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    checks = [
        ("pesquisas", "data_solicitacao", "data_aprov", "solicitacao <= aprovacao"),
        ("pesquisas", "data_aprov", "data_divulgacao", "aprovacao <= divulgacao"),
        ("pesquisas", "data_solicitacao", "data_entrega", "solicitacao <= entrega"),
        ("pesquisas", "data_limite", "prorrogada_ate", "limite <= prorrogacao"),
        ("respondentes", "hora_inicio", "hora_termino", "inicio <= termino"),
    ]
    result: list[dict[str, Any]] = []
    for source_id, left_column, right_column, name in checks:
        if source_id not in data_by_id:
            continue
        comparable = 0
        violations = 0
        for row in data_by_id[source_id]["rows"]:
            left = parse_date(row.get(left_column))
            right = parse_date(row.get(right_column))
            if left is None or right is None:
                continue
            comparable += 1
            if left > right:
                violations += 1
        result.append(
            {
                "checagem": name,
                "fonte": source_id,
                "coluna_a": left_column,
                "coluna_b": right_column,
                "comparaveis": comparable,
                "violacoes": violations,
                "percentual_violacoes": pct(violations, comparable),
                "status": "OK" if violations == 0 else "INCONSISTENCIAS_DETECTADAS",
                "limiar": "proposta: 0 violacoes; confirmar com Data Steward",
            }
        )
    return result


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter=";", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def run(input_dir: Path, output_dir: Path, manifest_path: Path, dictionary_path: Path | None = None) -> dict[str, Any]:
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    if not input_dir.is_dir():
        raise fail(f"[arquivo] diretório de entrada inexistente: {input_dir}")
    if output_dir == input_dir or input_dir in output_dir.parents:
        raise fail("[segurança] diretório de saída não pode estar dentro do diretório de entrada")
    manifest = read_manifest(manifest_path)
    sources = source_by_id(manifest)
    data_by_id = {source_id: read_source(input_dir, source) for source_id, source in sources.items()}
    dictionary_result = (
        validate_dictionary(dictionary_path, manifest, data_by_id)
        if dictionary_path is not None
        else [{
            "arquivo": "",
            "variavel": "__manifesto__",
            "status": "NAO_INFORMADO",
            "cardinalidade_dicionario": "",
            "cardinalidade_medida": "",
            "divergencia_cardinalidade": "",
            "nulos_dicionario": "",
            "nulos_fisicos": "",
            "sentinelas": "",
            "nulos_semanticos": "",
            "divergencia_dicionario_vs_fisico": "",
            "divergencia_dicionario_vs_semantico": "",
            "minimo_dicionario": "",
            "maximo_dicionario": "",
            "minimo_medido": "",
            "maximo_medido": "",
            "observacao": "Forneça --dictionary para validar o contrato semântico.",
        }]
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary = [profile_summary(data) for data in data_by_id.values()]
    fields = [field for data in data_by_id.values() for field in profile_fields(data)]
    domains = [domain for data in data_by_id.values() for domain in profile_domains(data)]
    dates = [date for data in data_by_id.values() for date in profile_dates(data)]
    relations = relation_rows(data_by_id, manifest)
    temporal = temporal_rows(data_by_id)
    identities = identity_rows(data_by_id)
    conditional = conditional_null_rows(data_by_id, manifest)
    percentages = percentage_rows(data_by_id)
    denormalized = denormalized_rows(data_by_id)

    write_csv(output_dir / "resumo.csv", summary, list(summary[0]))
    write_csv(output_dir / "campos.csv", fields, list(fields[0]))
    write_csv(output_dir / "dominios.csv", domains, ["source", "column", "dominio", "ocorrencias", "percentual"])
    write_csv(output_dir / "relacionamentos.csv", relations, RELATION_FIELDS)
    write_csv(output_dir / "datas.csv", dates, DATE_FIELDS)
    write_csv(output_dir / "coerencia_temporal.csv", temporal, TEMPORAL_FIELDS)
    write_csv(output_dir / "identidades.csv", identities, IDENTITY_FIELDS)
    write_csv(output_dir / "nulos_condicionais.csv", conditional, CONDITIONAL_FIELDS)
    write_csv(output_dir / "percentuais.csv", percentages, PERCENT_FIELDS)
    write_csv(output_dir / "denormalizados.csv", denormalized, DENORMALIZED_FIELDS)
    write_csv(output_dir / "dicionario_validacao.csv", dictionary_result, DICTIONARY_FIELDS)

    applied = {
        "manifest_version": manifest.get("version", "desconhecida"),
        "encoding": "utf-8-sig",
        "delimiter": ";",
        "decimal": "vírgula",
        "percentual": "sufixo %",
        "sources": [
            {
                "id": data["id"],
                "file_configurado": data["configured_file"],
                "arquivo_lido": data["file_used"],
                "registros": len(data["rows"]),
            }
            for data in data_by_id.values()
        ],
        "dictionary_provided": dictionary_path is not None,
        "dictionary_file": dictionary_path.name if dictionary_path else "",
        "dictionary_status": dictionary_result[0]["status"],
        "temporal": manifest.get("temporal", {}),
        "outputs": list(OUTPUT_NAMES[:-1]),
        "raw_data_written": False,
    }
    (output_dir / "manifesto_aplicado.json").write_text(
        json.dumps(applied, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return applied


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", "--input", dest="input_dir", type=Path, required=True, help="diretório somente leitura com os CSVs")
    parser.add_argument("--output-dir", "--output", dest="output_dir", type=Path, required=True, help="diretório novo/temporário para agregados")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="manifesto JSON")
    parser.add_argument("--dictionary", type=Path, required=True, help="dicionário local a validar (CSV separado por vírgula)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.dictionary is not None and not args.dictionary.is_file():
            raise fail(f"[arquivo] dicionário inexistente: {args.dictionary}")
        applied = run(args.input_dir, args.output_dir, args.manifest, args.dictionary)
    except ProfileError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"OK: {len(applied['sources'])} fontes perfiladas; saída agregada em {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
