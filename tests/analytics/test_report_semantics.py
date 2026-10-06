"""Regression checks for report labels, units, and published grain.

These checks inspect the PBIR contract only. They do not claim a Power BI
Desktop refresh or value comparison against a live Parquet generation.
"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "powerbi/CentralPesquisasBI.Report"
MODEL = ROOT / "powerbi/CentralPesquisasBI.SemanticModel/definition/tables"
BENCHMARK_PAGE = "e18bd740de609936581b"


def read_json(path):
    return json.loads(path.read_text())


def page_dir(page_id):
    return REPORT / "definition/pages" / page_id


def load_visual(page_id, visual_id):
    return read_json(page_dir(page_id) / "visuals" / visual_id / "visual.json")


def load_page(page_id):
    return read_json(page_dir(page_id) / "page.json")


def visual_title(visual):
    title = visual.get("visual", {}).get("visualContainerObjects", {}).get("title", [])
    if not title:
        return ""
    expr = title[0].get("properties", {}).get("text", {}).get("expr", {})
    return (expr.get("Literal", {}).get("Value") or "").strip("'")


def visual_subtitle(visual):
    subtitle = visual.get("visual", {}).get("visualContainerObjects", {}).get("subTitle", [])
    if not subtitle:
        return ""
    expr = subtitle[0].get("properties", {}).get("text", {}).get("expr", {})
    return (expr.get("Literal", {}).get("Value") or "").strip("'")


def field_refs(node):
    if isinstance(node, dict):
        for kind in ("Measure", "Column"):
            field = node.get(kind)
            if isinstance(field, dict):
                entity = (
                    (field.get("Expression") or {}).get("SourceRef") or {}
                ).get("Entity")
                prop = field.get("Property")
                if entity and prop:
                    yield kind, entity, prop
        for value in node.values():
            yield from field_refs(value)
    elif isinstance(node, list):
        for value in node:
            yield from field_refs(value)


def role_fields(visual, role):
    state = visual.get("visual", {}).get("query", {}).get("queryState", {})
    return {
        (entity, prop)
        for _, entity, prop in field_refs(state.get(role, {}))
    }


def text_runs(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "value" and isinstance(value, str):
                yield value
            yield from text_runs(value)
    elif isinstance(node, list):
        for value in node:
            yield from text_runs(value)


def page_visuals(page_id):
    paths = sorted((page_dir(page_id) / "visuals").glob("*/visual.json"))
    return [(path.parent.name, read_json(path)) for path in paths]


class ReportSemanticsTests(unittest.TestCase):
    def test_duration_titles_match_supported_units_and_measures(self):
        cycle = load_visual("5d499bb7bb62646ad6e5", "e1943eaed82275129d4e")
        self.assertEqual(
            visual_title(cycle), "Tempo por Etapa e Tipo (dias corridos)"
        )
        self.assertEqual(
            role_fields(cycle, "Y"),
            {
                ("PUB_C01_CICLO", "Media Dias Validacao"),
                ("PUB_C01_CICLO", "Media Dias Coleta"),
                ("PUB_C01_CICLO", "Media Dias Tabulacao"),
            },
        )

        stock = load_visual("c03c04qualidade01", "qestoque000000004")
        self.assertEqual(visual_title(stock), "Estoque no fechamento mensal por status")
        self.assertEqual(
            role_fields(stock, "Y"),
            {("PUB_C03_PIPELINE_MENSAL", "Estoque no Status")},
        )

    def test_benchmark_labels_and_bindings_match_c02_grain(self):
        self.assertEqual(load_page(BENCHMARK_PAGE)["displayName"], "Participação agregada (C02)")

        by_area = load_visual(BENCHMARK_PAGE, "v2_frequent")
        self.assertEqual(visual_title(by_area), "Participações por área")
        self.assertEqual(
            role_fields(by_area, "Y"),
            {("PUB_C02_PARTICIPACAO", "Qtd Participacoes")},
        )

        by_month = load_visual(BENCHMARK_PAGE, "v2_absent")
        self.assertEqual(visual_title(by_month), "Participações por mês")
        self.assertEqual(
            role_fields(by_month, "Y"),
            {("PUB_C02_PARTICIPACAO", "Qtd Participacoes")},
        )

        detail = load_visual(BENCHMARK_PAGE, "5a299fc93da0a4eb0d07")
        self.assertEqual(
            visual_title(detail), "Participações agregadas por área, tipo e mês"
        )
        self.assertTrue(
            {
                ("PUB_C02_PARTICIPACAO", "area"),
                ("PUB_C02_PARTICIPACAO", "tipo"),
                ("PUB_C02_PARTICIPACAO", "mes_resposta"),
            }.issubset(role_fields(detail, "Values"))
        )

        hidden_detail = load_visual(BENCHMARK_PAGE, "v2_detail")
        self.assertEqual(
            visual_title(hidden_detail), "Detalhe agregado por área, tipo e mês"
        )

    def test_c02_charts_do_not_share_count_and_minutes_on_one_axis(self):
        for visual_id, visual in page_visuals(BENCHMARK_PAGE):
            if visual.get("visual", {}).get("visualType") not in {
                "barChart",
                "clusteredColumnChart",
                "lineChart",
            }:
                continue
            y_props = {prop for _, _, prop in field_refs(
                visual.get("visual", {}).get("query", {}).get("queryState", {}).get("Y", {})
            )}
            self.assertFalse(
                {"Qtd Participacoes", "Media Minutos Preenchimento"}.issubset(y_props),
                f"{visual_id} mixes occurrence counts and minutes on one axis",
            )

    def test_company_and_research_unavailability_are_not_filter_controls(self):
        for visual_id in ("d3ee05e7e9ee90a905a0", "f8529f56a2b696a08788"):
            visual = load_visual(BENCHMARK_PAGE, visual_id)
            self.assertEqual(visual.get("visual", {}).get("visualType"), "textbox")
            self.assertNotIn("query", visual.get("visual", {}))

        captions = {
            visual_id: " ".join(text_runs(load_visual(BENCHMARK_PAGE, visual_id)))
            for visual_id in ("d3ee05e7e9ee90a905a0", "f8529f56a2b696a08788")
        }
        self.assertIn("Empresa distinta por pesquisa (I07) indisponível", captions["d3ee05e7e9ee90a905a0"])
        self.assertIn("Pesquisa individual indisponível", captions["f8529f56a2b696a08788"])

        for visual_id, visual in page_visuals(BENCHMARK_PAGE):
            if visual.get("visual", {}).get("visualType") != "slicer":
                continue
            refs = set(field_refs(visual.get("visual", {}).get("query", {})))
            self.assertNotIn(
                ("Column", "DIM_INDICADORES_BLOQUEADOS", "motivo"), refs,
                f"{visual_id} exposes blocker reasons as a picker",
            )

    def test_blocker_catalog_count_is_unique_unavailable_indicators(self):
        table = (MODEL / "DIM_INDICADORES_BLOQUEADOS.tmdl").read_text()
        rows = re.findall(r'\{\s*"(I\d+)"\s*,\s*"[^"]*"\s*,\s*"([^"]+)"', table)
        unavailable = [indicator for indicator, status in rows if status == "Sem dado"]
        self.assertEqual(len(unavailable), 17)
        self.assertEqual(len(unavailable), len(set(unavailable)))

        chart = load_visual(BENCHMARK_PAGE, "eebbcb005a12b1c98030")
        self.assertEqual(visual_title(chart), "Indicadores sem dado por motivo")
        self.assertEqual(
            role_fields(chart, "Category"),
            {("DIM_INDICADORES_BLOQUEADOS", "motivo")},
        )
        self.assertEqual(
            role_fields(chart, "Y"),
            {("DIM_INDICADORES_BLOQUEADOS", "Qtd Indicadores Sem Dado")},
        )

        card = load_visual(BENCHMARK_PAGE, "v2_kpi2")
        data = card["visual"]["query"]["queryState"]["Data"]["projections"]
        self.assertEqual(data[0]["displayName"], "Qtd. de indicadores sem dado")

    def test_no_visible_benchmark_copy_claims_company_or_research_grain(self):
        labels = []
        for _, visual in page_visuals(BENCHMARK_PAGE):
            labels.extend(text_runs(visual))
            labels.append(visual_title(visual))
            labels.append(visual_subtitle(visual))
        report_text = " ".join(labels).casefold()
        for stale in (
            "perfil de participação",
            "posição no benchmark",
            "participação por pesquisa",
            "detalhe da sua empresa",
            "faixa teal indica a posição da sua empresa",
        ):
            self.assertNotIn(stale, report_text)


if __name__ == "__main__":
    unittest.main()
