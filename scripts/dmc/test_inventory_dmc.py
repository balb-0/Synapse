#!/usr/bin/env python3
"""Testes do inventário reproduzível do Data Model Canvas."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path

import inventory_dmc


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class InventoryDmcTest(unittest.TestCase):
    def setUp(self) -> None:
        self.document = inventory_dmc.load_document(REPOSITORY_ROOT / "docs/dmc.json")

    def test_current_document_has_four_cubes(self) -> None:
        inventory = inventory_dmc.build_inventory(self.document)

        self.assertEqual(inventory["cube_count"], 4)
        self.assertTrue(inventory["cube_count_matches"])
        self.assertEqual(inventory["missing_top_level"], [])
        self.assertEqual(inventory["tactic_count"], 3)
        self.assertTrue(inventory["etl_present"])

    def test_current_document_has_complete_data_and_governance_sections(self) -> None:
        inventory = inventory_dmc.build_inventory(self.document)

        for cube in inventory["cubes"]:
            self.assertEqual(cube["missing_cube_lists"], [])
            self.assertEqual(cube["missing_data_governance_fields"], [])

    def test_missing_dimensional_list_is_reported(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cubos"][0]["lists"]["metricas"] = []

        inventory = inventory_dmc.build_inventory(changed)

        self.assertEqual(
            inventory["cubes"][0]["missing_cube_lists"], ["metricas"]
        )

    def test_markdown_records_source_and_clean_structure(self) -> None:
        inventory = inventory_dmc.build_inventory(self.document)

        rendered = inventory_dmc.render_markdown(inventory, Path("docs/dmc.json"))

        self.assertIn("Fonte: `docs/dmc.json`", rendered)
        self.assertIn("Cubos: `4` de `4` esperados", rendered)
        self.assertIn("Nenhum ajuste estrutural detectado.", rendered)


if __name__ == "__main__":
    unittest.main()
