"""Integridade do pacote PBIR, sem afirmar execução no Desktop."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "powerbi/CentralPesquisasBI.Report"


class ReportDefinitionTests(unittest.TestCase):
    def test_project_resolves_report_and_parquet_model(self):
        project = json.loads((ROOT / "powerbi/CentralPesquisasBI.pbip").read_text())
        self.assertEqual(project["artifacts"][0]["report"]["path"], REPORT.name)
        reference = json.loads((REPORT / "definition.pbir").read_text())
        model = REPORT / reference["datasetReference"]["byPath"]["path"]
        self.assertTrue((model / "definition.pbism").is_file())
        self.assertTrue((model / "definition/expressions.tmdl").is_file())
        self.assertFalse((REPORT / "report.json").exists(), "Não misturar PBIR e PBIR-Legacy")

    def test_page_order_and_visual_ids_resolve(self):
        pages = REPORT / "definition/pages"
        metadata = json.loads((pages / "pages.json").read_text())
        order = metadata["pageOrder"]
        self.assertEqual(len(order), 3)
        self.assertIn("c03c04qualidade01", order)
        self.assertEqual(len(set(order)), len(order))
        self.assertEqual(set(order), {p.name for p in pages.iterdir() if p.is_dir()})
        self.assertIn(metadata["activePageName"], order)
        for page_id in order:
            page = json.loads((pages / page_id / "page.json").read_text())
            self.assertEqual(page["name"], page_id)
            self.assertGreater(page["width"], 0)
            self.assertGreater(page["height"], 0)
            visuals = list((pages / page_id / "visuals").glob("*/visual.json"))
            self.assertTrue(visuals)
            for path in visuals:
                visual = json.loads(path.read_text())
                self.assertEqual(visual["name"], path.parent.name)

    def test_theme_and_registered_resources_exist(self):
        report = json.loads((REPORT / "definition/report.json").read_text())
        resources = {}
        for package in report["resourcePackages"]:
            for item in package["items"]:
                path = REPORT / "StaticResources" / package["name"] / item["path"]
                self.assertTrue(path.is_file(), str(path))
                resources[(package["type"], item["name"])] = path
        theme = report["themeCollection"]["baseTheme"]
        self.assertIn((theme["type"], theme["name"]), resources)
        for path in REPORT.rglob("*.json"):
            json.loads(path.read_text())

    def test_c01_unavailable_prorrogation_is_explanatory_text(self):
        page = REPORT / "definition/pages/5d499bb7bb62646ad6e5/visuals"
        notices = {
            "pvprorrocard0000015": "I05 (prorrogação): sem dado publicado em C01.",
            "pvprorrotable000016": "Sem detalhamento por área no escopo C01.",
        }
        for visual_id, notice in notices.items():
            payload = json.loads((page / visual_id / "visual.json").read_text())
            visual = payload["visual"]
            self.assertEqual(visual.get("visualType"), "textbox")
            self.assertNotIn("query", visual)
            self.assertIn(notice, json.dumps(visual, ensure_ascii=False))
            self.assertNotIn("Taxa de Prorrogacao", json.dumps(visual))

    def test_quality_physical_completion_does_not_claim_i16_applicability(self):
        page = REPORT / "definition/pages/c03c04qualidade01/visuals"
        for visual_id in ("qkpicompletude0003", "qtabcompletud00007"):
            payload = json.loads((page / visual_id / "visual.json").read_text())
            visual = payload["visual"]
            projections = [
                projection
                for slot in visual["query"]["queryState"].values()
                for projection in slot["projections"]
                if projection.get("queryRef") == "PUB_QUALIDADE_CAMPO.Completude"
            ]
            self.assertEqual(len(projections), 1)
            self.assertEqual(projections[0]["field"]["Measure"]["Property"], "Completude")
            self.assertEqual(projections[0]["displayName"], "Completude de preenchimento")
            self.assertNotIn("I16", json.dumps(visual, ensure_ascii=False))
        subtitle = json.loads((page / "qsubtl0000000002/visual.json").read_text())
        self.assertIn("I16 aplicável", json.dumps(subtitle, ensure_ascii=False))

        tables = ROOT / "powerbi/CentralPesquisasBI.SemanticModel/definition/tables"
        measure = (tables / "PUB_QUALIDADE_CAMPO.tmdl").read_text()
        self.assertIn("todas as linhas por campo", measure)
        self.assertIn("Não aplica regras condicionais", measure)
        catalog = (tables / "DIM_INDICADORES_BLOQUEADOS.tmdl").read_text()
        self.assertIn('{"I16", "Completude aplicavel", "Sem dado",', catalog)
        states = re.findall(r'\{"(I[0-9]+)", "[^"]+", "([^"]+)"', catalog)
        self.assertEqual(len(states), 19)
        self.assertEqual(len(dict(states)), 19, "catalog IDs must remain unique")
        self.assertEqual(sum(state == "Sem dado" for _, state in states), 18)
        self.assertEqual(dict(states)["I03"], "Parcial")

    def test_c03_monthly_stock_uses_categorical_closing_dates(self):
        path = REPORT / "definition/pages/c03c04qualidade01/visuals/qestoque000000004/visual.json"
        visual = json.loads(path.read_text())["visual"]
        axis_type = visual["objects"]["categoryAxis"][0]["properties"]["axisType"]
        self.assertEqual(axis_type["expr"]["Literal"]["Value"], "'Categorical'")
        category = visual["query"]["queryState"]["Category"]["projections"][0]
        self.assertEqual(category["field"]["Column"]["Property"], "data_fim_mes")

    def test_c02_count_charts_use_auto_count_axes_and_only_count_selectors(self):
        page = REPORT / "definition/pages/e18bd740de609936581b/visuals"
        for visual_id in ("v2_area", "v2_frequent", "v2_time", "v2_absent"):
            visual = json.loads((page / visual_id / "visual.json").read_text())["visual"]
            value_axis = visual["objects"]["valueAxis"][0]["properties"]
            self.assertEqual(value_axis["start"]["expr"]["Literal"]["Value"], "0D", visual_id)
            self.assertNotIn("end", value_axis, visual_id)
            self.assertNotIn("labelDisplayUnits", value_axis, visual_id)
            label_properties = visual["objects"].get("labels", [{}])[0].get("properties", {})
            self.assertNotIn("labelDisplayUnits", label_properties, visual_id)

            selectors = {
                item.get("selector", {}).get("metadata")
                for item in visual["objects"].get("dataPoint", [])
            }
            self.assertEqual(selectors, {"PUB_C02_PARTICIPACAO.Qtd Participacoes"}, visual_id)


if __name__ == "__main__":
    unittest.main()
