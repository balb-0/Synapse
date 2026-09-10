"""Validação de presença e obrigatoriedade dependente do tipo de questão."""

from dataclasses import dataclass
from .conversion import ConversionError, number
from .schema import QUESTION_TYPES


@dataclass(frozen=True, order=True)
class Violation:
    code: str
    field: str


def missing(value, sentinels=()):
    return value is None or (isinstance(value, str) and
                            (not value.strip() or value.strip().casefold() in sentinels))


def required_fields(record, fields):
    return [Violation("REQUIRED", f.name) for f in fields
            if f.required and missing(record.get(f.name), f.sentinels)]


def conditional_fields(record, question):
    kind = question.get("tipo")
    if kind not in QUESTION_TYPES:
        return [Violation("UNKNOWN_QUESTION_TYPE", "pergunta_id")]
    required = {"aberta": ("valor",), "numerica": ("valor",),
                "caixas_de_selecao": ("alternativa",),
                "matriz_avaliacao": ("linha_matriz", "coluna_matriz"),
                "multipla_escolha": ()}[kind]
    problems = [Violation("CONDITIONAL_REQUIRED", name)
                for name in required if missing(record.get(name))]
    if kind == "multipla_escolha" and all(missing(record.get(n)) for n in ("valor", "alternativa")):
        problems.append(Violation("CONDITIONAL_REQUIRED", "valor"))
    if kind != "matriz_avaliacao":
        problems.extend(Violation("NOT_APPLICABLE", name) for name in
                        ("linha_matriz", "coluna_matriz") if not missing(record.get(name)))
    if kind == "numerica" and not missing(record.get("valor")):
        try:
            number(record["valor"])
        except ConversionError:
            problems.append(Violation("INVALID_NUMERIC_ANSWER", "valor"))
    return problems
