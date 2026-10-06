"""RP-16: filtros, hierarquias e detalhamento suportados — sem Chave individual.

Verifica sobre a definição PBIR final que nenhum visual vincula entidade ou
coluna de grão individual (D01_*/D02_*/D03_*/D04_*/BE_*) e que slicers usam
só dimensões conformadas ou tabelas PUB. Drill por tempo/área/tipo ocorre
onde o agregado permite; nenhum drill-through promete Chave ausente da
publicação.
"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "powerbi/CentralPesquisasBI.Report"
MODEL = ROOT / "powerbi/CentralPesquisasBI.SemanticModel"

BANNED_ENTITIES = {
    "D01_CicloPesquisa",
    "D02_Participacao",
    "D03_PesquisaPergunta",
    "D04_PipelineMensal",
    "D04_QualidadeGovernanca",
    "BE_Empresa",
    "BE_Faixa",
    "BE_Pesquisa",
}

# Colunas de grão individual ou não publicadas (Property de campo).
BANNED_PROPERTIES = {
    "titulo",
    "flag_prorrogada",
    "ano_edicao",
    "data_entrega",
    "dias_ciclo_total_corridos",
    "dias_validacao_corridos",
    "dias_coleta_corridos",
    "dias_tabulacao_corridos",
    "qtd_empresas_na_pesquisa",
    "Empresa",
    "Pesquisa",
    "ID Empresa",
    "ID Pesquisa",
    "Faixa",
    "Área",
    "Tipo",
    "Ano",
}


def load_visuals():
    out = []
    for path in sorted((REPORT / "definition/pages").rglob("*/visual.json")):
        out.append((path, json.loads(path.read_text())))
    assert out, "nenhum visual.json encontrado"
    return out


def iter_fields(node):
    """Percorre field Definitions {Measure|Column: {Expression: {SourceRef: {Entity}}, Property}}."""
    if isinstance(node, dict):
        if "Measure" in node or "Column" in node:
            for kind in ("Measure", "Column"):
                if kind in node and isinstance(node[kind], dict):
                    ent = ((node[kind].get("Expression") or {}).get("SourceRef") or {}).get(
                        "Entity"
                    )
                    prop = node[kind].get("Property")
                    yield kind, ent, prop
        for value in node.values():
            yield from iter_fields(value)
    elif isinstance(node, list):
        for item in node:
            yield from iter_fields(item)


class ReportFiltersTests(unittest.TestCase):
    def test_no_individual_grain_entities(self):
        offenders = []
        for path, visual in load_visuals():
            for kind, ent, prop in iter_fields(visual):
                if ent in BANNED_ENTITIES:
                    offenders.append(
                        f"{path.parent.parent.name}/{path.parent.name}: {kind} {ent}.{prop}"
                    )
        self.assertEqual(offenders, [], "vínculos de grão individual ainda presentes")

    def test_no_individual_grain_properties(self):
        offenders = []
        for path, visual in load_visuals():
            for kind, ent, prop in iter_fields(visual):
                if prop in BANNED_PROPERTIES:
                    offenders.append(
                        f"{path.parent.parent.name}/{path.parent.name}: {kind} {ent}.{prop}"
                    )
        self.assertEqual(offenders, [], "colunas individuais/não publicadas ainda vinculadas")

    def test_slicers_bind_dimensions_or_pub(self):
        offenders = []
        for path, visual in load_visuals():
            if visual.get("visual", {}).get("visualType") != "slicer":
                continue
            refs = [(e, p) for _, e, p in iter_fields(visual.get("visual", {}).get("query", {}))]
            self.assertTrue(refs, f"slicer sem projeção: {path.parent.name}")
            for ent, prop in refs:
                if ent is None or not (ent.startswith("DIM_") or ent.startswith("PUB_")):
                    offenders.append(f"{path.parent.name}: {ent}.{prop}")
        self.assertEqual(offenders, [], "slicer fora de DIM_*/PUB_*")

    def test_no_drillthrough_to_individual_keys(self):
        offenders = []
        for path, visual in load_visuals():
            text = json.dumps(visual)
            if re.search(r"[Dd]rill", text):
                for kind, ent, prop in iter_fields(visual):
                    if ent in BANNED_ENTITIES or prop in BANNED_PROPERTIES:
                        offenders.append(f"{path.parent.name}: {ent}.{prop}")
        self.assertEqual(offenders, [], "drill promete Chave individual ausente da publicação")

    def test_supported_hierarchies_exist_in_model(self):
        tempo = (MODEL / "definition/tables/DIM_TEMPO.tmdl").read_text()
        self.assertIn("hierarchy Calendario", tempo)
        for level in ("level Ano", "level Trimestre", "level 'Mes'"):
            self.assertIn(level, tempo)
        c03 = (MODEL / "definition/tables/PUB_C03_PIPELINE_MENSAL.tmdl").read_text()
        self.assertIn("hierarchy 'Area, Tipo e Perfil'", c03)


if __name__ == "__main__":
    unittest.main()
