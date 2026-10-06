"""RP-17: páginas finais ligadas ao modelo — vínculos resolvem e filtros alcançam os fatos.

Percorre as três páginas finais, confere que cada medida/coluna vinculada
existe no modelo semântico Parquet e que cada slicer de dimensão alcança as
tabelas fato da mesma página pelos relacionamentos (filtro dimensão → fato,
direção única). Slicers de sinalização (DIM_INDICADORES_BLOQUEADOS) são
desconectados por desenho: exibem motivo textual, não filtram.
Execução no Desktop com a geração real (BI-05) fica registrada em
docs/solucao-dashboards/validacao-paginas-finais.md.
"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "powerbi/CentralPesquisasBI.Report"
TABLES = ROOT / "powerbi/CentralPesquisasBI.SemanticModel/definition/tables"
REL = ROOT / "powerbi/CentralPesquisasBI.SemanticModel/definition/relationships.tmdl"

SIGNAL_TABLE = "DIM_INDICADORES_BLOQUEADOS"


def parse_model():
    model = {}
    for tmdl in TABLES.glob("*.tmdl"):
        name, columns, measures = None, set(), set()
        for line in tmdl.read_text().splitlines():
            m = re.match(r"table\s+(\S+)", line)
            if m:
                name = m.group(1)
                continue
            m = re.match(r"\s+(?:column|measure)\s+('(?:[^']+)'|\S+)", line)
            if m and name:
                token = m.group(0).split()[0]
                ident = m.group(1).strip("'")
                if token == "column":
                    columns.add(ident)
                else:
                    measures.add(ident)
        if name:
            model[name] = {"columns": columns, "measures": measures}
    assert model, "modelo sem tabelas"
    return model


def parse_relationships():
    rels = []
    cur = {}
    for line in REL.read_text().splitlines():
        m = re.match(r"relationship\s+(\S+)", line)
        if m:
            if cur:
                rels.append(cur)
            cur = {"name": m.group(1)}
            continue
        m = re.match(r"\s+(fromColumn|toColumn):\s+(\S+)\.(\S+)", line)
        if m and cur is not None:
            cur[m.group(1)] = (m.group(2), m.group(3))
    if cur:
        rels.append(cur)
    coverage = set()
    for rel in rels:
        frm = (rel.get("fromColumn") or (None, None))[0]
        to = (rel.get("toColumn") or (None, None))[0]
        if frm and to:
            coverage.add((to, frm))
    return coverage


def iter_fields(node):
    if isinstance(node, dict):
        if "Measure" in node or "Column" in node:
            for kind in ("Measure", "Column"):
                if kind in node and isinstance(node[kind], dict):
                    ent = ((node[kind].get("Expression") or {}).get("SourceRef") or {}).get("Entity")
                    prop = node[kind].get("Property")
                    yield kind, ent, prop
        for value in node.values():
            yield from iter_fields(value)
    elif isinstance(node, list):
        for item in node:
            yield from iter_fields(item)


def load_pages():
    pages = REPORT / "definition/pages"
    meta = json.loads((pages / "pages.json").read_text())
    out = {}
    for page_id in meta["pageOrder"]:
        visuals = []
        for path in sorted((pages / page_id / "visuals").glob("*/visual.json")):
            visuals.append((path.parent.name, json.loads(path.read_text())))
        out[page_id] = visuals
    return out


class ReportBindingsTests(unittest.TestCase):
    def test_all_visual_bindings_resolve_in_model(self):
        model = parse_model()
        offenders = []
        for page_id, visuals in load_pages().items():
            for vname, visual in visuals:
                for kind, ent, prop in iter_fields(visual.get("visual", {}).get("query", {})):
                    if ent not in model:
                        offenders.append(f"{page_id}/{vname}: tabela inexistente {ent}")
                    elif prop not in model[ent]["columns"] | model[ent]["measures"]:
                        offenders.append(f"{page_id}/{vname}: {kind} {ent}.{prop} inexistente")
        self.assertEqual(offenders, [], "vínculos que não resolvem no modelo")

    def test_slicer_dimensions_reach_page_facts(self):
        # fato <- dimensao (toColumn = dimensao, fromColumn = fato)
        coverage = parse_relationships()
        offenders = []
        for page_id, visuals in load_pages().items():
            # Tabelas de qualidade são standalone no modelo (sem
            # relacionamentos, por desenho): exibem o perfilamento global,
            # fora do recorte dos slicers.
            facts = {e for _, v in visuals for _, e, _ in iter_fields(v.get("visual", {}).get("query", {}))
                     if e and e.startswith("PUB_") and not e.startswith("PUB_QUALIDADE_")}
            for vname, visual in visuals:
                if visual.get("visual", {}).get("visualType") != "slicer":
                    continue
                for _, ent, prop in iter_fields(visual.get("visual", {}).get("query", {})):
                    if ent == SIGNAL_TABLE:
                        continue  # sinalização desconectada por desenho
                    reached = sorted(f for f in facts if (ent, f) in coverage)
                    if not reached:
                        offenders.append(f"{page_id}/{vname}: {ent} não alcança nenhum fato da página")
        self.assertEqual(offenders, [], "slicer sem caminho dimensão → fato")


if __name__ == "__main__":
    unittest.main()
