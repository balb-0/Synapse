"""Normalização por mapa explícito, com rejeição de colisões e campos extras."""

import json
from collections.abc import Mapping

from . import conversion as conv
from .schema import SCHEMAS
from .validation import Violation, missing, required_fields


def string_list(value):
    if isinstance(value, str):
        rendered = value.strip()
        if rendered.startswith("["):
            try:
                value = json.loads(rendered)
            except (ValueError, RecursionError):
                raise conv.ConversionError("INVALID_JSON_LIST") from None
        else:
            value = rendered.split("|")
    if not isinstance(value, list) or any(not isinstance(v, str) for v in value):
        raise conv.ConversionError("INVALID_JSON_LIST")
    result = [conv.text(v) for v in value]
    if any(not v for v in result):
        raise conv.ConversionError("EMPTY_LIST_ITEM")
    return result


def normalize_record(source, raw, source_timezone=None):
    if source not in SCHEMAS:
        raise ValueError("UNKNOWN_SOURCE")
    if not isinstance(raw, Mapping):
        return {}, [Violation("INVALID_RECORD", "record")]
    fields = SCHEMAS[source]
    aliases = {alias: f for f in fields for alias in (f.origin, f.name)}
    values, problems, seen = {}, [], set()
    for original, value in raw.items():
        if not isinstance(original, str):
            problems.append(Violation("UNKNOWN_FIELD", "schema"))
            continue
        name = conv.text(original.lstrip("\ufeff"))
        if source == "pesquisas" and (not name or name.startswith("Unnamed:")):
            if not missing(value):
                problems.append(Violation("NONEMPTY_EXPORT_COLUMN", "schema"))
            continue
        spec = aliases.get(name)
        if spec is None:
            if source in ("questoes", "respostas") and name in ("estrutura", "conteudo"):
                # Contêiner auxiliar do contrato de extração dos questionários:
                # os campos brutos já foram processados; a forma estável é
                # redundante para a normalização.
                continue
            # Never reflect attacker-controlled field names into logs.
            problems.append(Violation("UNKNOWN_FIELD", "schema"))
            continue
        if spec.name in seen:
            problems.append(Violation("FIELD_COLLISION", spec.name))
            continue
        seen.add(spec.name)
        if missing(value, spec.sentinels):
            values[spec.name] = [] if spec.kind == "list" else None
            continue
        try:
            convert = {
                "text": conv.text,
                "id": conv.identifier,
                "integer": conv.integer,
                "decimal": conv.decimal,
                "percent": lambda v: conv.decimal(v, percent=True),
                "date": conv.civil_date,
                "datetime": lambda v: conv.instant(v, source_timezone),
                "boolean": conv.boolean,
                "list": string_list,
            }[spec.kind]
            values[spec.name] = convert(value)
        except conv.ConversionError as error:
            values[spec.name] = None
            problems.append(Violation(error.code, spec.name))
    for spec in fields:
        values.setdefault(spec.name, [] if spec.kind == "list" else None)
    problems.extend(required_fields(values, fields))
    if source == "empresas":
        if values.get("pais") and values["pais"].casefold() in ("brasil", "brazil", "br"):
            values["pais"] = "Brasil"
        if values.get("estado"):
            values["estado"] = values["estado"].upper()
    if source == "questoes" and values.get("tipo"):
        values["tipo"] = values["tipo"].casefold()
    return values, sorted(set(problems))
