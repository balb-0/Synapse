"""Referências técnicas explícitas; nenhuma inferência de identidade pessoal."""

from copy import deepcopy

from .schema import KEYS, QUESTION_TYPES
from .validation import Violation, conditional_fields

RELATIONS = {
    "pesquisas": (),
    "empresas": (),
    "clientes": (("empresas", ("empresa_id",)),),
    "respondentes": (
        ("empresas", ("empresa_id",)),
        ("pesquisas", ("pesquisa_id",)),
        ("clientes", ("cliente_id",)),
    ),
    "questoes": (("pesquisas", ("pesquisa_id",)),),
    "respostas": (
        ("empresas", ("empresa_id",)),
        ("pesquisas", ("pesquisa_id",)),
        ("questoes", ("pesquisa_id", "pergunta_id")),
    ),
}


class ReferenceData:
    """Snapshot privado de registros canônicos aceitos do mesmo universo.

    Fonte ausente difere de fonte carregada vazia. O chamador deve fornecer
    todas as referências necessárias, inclusive para um lote vazio.
    """

    def __init__(self, sources):
        self._indexes = {}
        for source, records in sources.items():
            if source not in KEYS:
                raise ValueError("INVALID_REFERENCE_SOURCE")
            keys = KEYS[source]
            index = {}
            for record in records:
                key = tuple(record.get(k) for k in keys)
                if any(not isinstance(v, str) or not v.isascii() or not v.isdigit() for v in key):
                    raise ValueError("INVALID_REFERENCE_KEY")
                if key in index:
                    raise ValueError("DUPLICATE_REFERENCE_KEY")
                index[key] = deepcopy(record)
            self._indexes[source] = index

    def require(self, source):
        if any(parent not in self._indexes for parent, _ in RELATIONS[source]):
            raise ValueError("REFERENCE_DATA_REQUIRED")

    def get(self, source, key):
        return deepcopy(self._indexes[source].get(key))


def validate_consistency(source, record, references):
    references.require(source)
    problems = []
    for parent, fields in RELATIONS[source]:
        key = tuple(record.get(k) for k in fields)
        if any(v is None for v in key):
            continue
        if references.get(parent, key) is None:
            problems.append(Violation("ORPHAN_REFERENCE", fields[-1]))
    if source == "respondentes" and record.get("cliente_id") is not None:
        client = references.get("clientes", (record["cliente_id"],))
        if client and client.get("empresa_id") != record["empresa_id"]:
            problems.append(Violation("CLIENT_COMPANY_MISMATCH", "cliente_id"))
    if source == "questoes":
        if record["tipo"] not in QUESTION_TYPES:
            problems.append(Violation("UNKNOWN_QUESTION_TYPE", "tipo"))
        count = record.get("qtd_alternativas")
        expected = len(record["alternativas"])
        if record["tipo"] == "matriz_avaliacao":
            # In the source dictionary this is the number of matrix cells.
            expected = len(record["linhas_matriz"]) * len(record["colunas_matriz"])
        if count is not None and count != expected:
            problems.append(Violation("ALTERNATIVE_COUNT_MISMATCH", "qtd_alternativas"))
    if source == "respostas":
        question = references.get("questoes", (record["pesquisa_id"], record["pergunta_id"]))
        if question:
            problems.extend(conditional_fields(record, question))
            for field, domain in (
                ("linha_matriz", "linhas_matriz"),
                ("coluna_matriz", "colunas_matriz"),
            ):
                if (
                    record[field] is not None
                    and question.get(domain)
                    and record[field] not in question[domain]
                ):
                    problems.append(Violation("ANSWER_DOMAIN", field))
            if question.get("alternativas"):
                answer = record["alternativa"]
                if answer is None and question["tipo"] == "multipla_escolha":
                    answer = record["valor"]
                if answer is not None and answer not in question["alternativas"]:
                    problems.append(Violation("ANSWER_DOMAIN", "alternativa"))
    pairs = {
        "respondentes": (("hora_inicio", "hora_termino"),),
        "pesquisas": (
            ("data_solicitacao", "data_entrega"),
            ("data_divulgacao", "data_limite"),
            ("data_limite", "prorrogada_ate"),
        ),
    }.get(source, ())
    for earlier, later in pairs:
        if (
            record[earlier] is not None
            and record[later] is not None
            and record[later] < record[earlier]
        ):
            problems.append(Violation("TEMPORAL_ORDER", later))
    for name in ("participantes", "qtd_alternativas", "tempo_preenchimento"):
        if record.get(name) is not None and record[name] < 0:
            problems.append(Violation("NEGATIVE_MEASURE", name))
    return sorted(set(problems))
