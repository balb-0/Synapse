"""Integridade do pacote PBIR, sem afirmar execução no Desktop."""

import json
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
        self.assertEqual(len(order), 2)
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
