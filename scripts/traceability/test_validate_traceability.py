#!/usr/bin/env python3
"""Testes do contrato executável de rastreabilidade analítica."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path

import validate_traceability


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class ValidateTraceabilityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = validate_traceability.load_json(
            REPOSITORY_ROOT / "scripts/traceability/manifest.json"
        )
        self.dmc = validate_traceability.load_json(REPOSITORY_ROOT / "docs/dmc.json")

    def test_current_contract_is_valid(self) -> None:
        summary = validate_traceability.validate(self.manifest, self.dmc)
        self.assertEqual(summary["questions"], 13)
        self.assertEqual(summary["indicators"], 25)
        self.assertEqual(summary["pendingIndicators"], 4)

    def test_missing_question_fails(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["questions"].pop()
        with self.assertRaisesRegex(validate_traceability.TraceabilityError, "PB01–PB13"):
            validate_traceability.validate(changed, self.dmc)

    def test_indicator_gap_fails(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["questions"][0]["indicators"].remove("I01")
        with self.assertRaisesRegex(validate_traceability.TraceabilityError, "cobertura de indicadores"):
            validate_traceability.validate(changed, self.dmc)

    def test_unknown_cube_fails(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["questions"][0]["cubes"] = ["C99"]
        with self.assertRaisesRegex(validate_traceability.TraceabilityError, "cubo desconhecido"):
            validate_traceability.validate(changed, self.dmc)

    def test_pb10_cannot_be_connected_to_c03(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["questions"][9]["cubes"] = ["C03"]
        with self.assertRaisesRegex(validate_traceability.TraceabilityError, "vínculo dimensional"):
            validate_traceability.validate(changed, self.dmc)

    def test_pb11_must_keep_c04(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["questions"][10]["cubes"] = []
        with self.assertRaisesRegex(validate_traceability.TraceabilityError, "vínculo dimensional"):
            validate_traceability.validate(changed, self.dmc)

    def test_pending_cube_requires_task_43(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["questions"][9]["pendingCube"]["dependency"] = "Task 99"
        with self.assertRaisesRegex(validate_traceability.TraceabilityError, "Task 43"):
            validate_traceability.validate(changed, self.dmc)

    def test_pending_indicators_are_restricted_to_i12_i15(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["questions"][9]["pendingIndicators"].append("I01")
        changed["questions"][9]["indicators"].append("I01")
        with self.assertRaisesRegex(validate_traceability.TraceabilityError, "I12–I15"):
            validate_traceability.validate(changed, self.dmc)

    def test_dmc_cube_name_must_match(self) -> None:
        changed = copy.deepcopy(self.dmc)
        changed["cubos"][0]["fields"]["nome"] = "Nome divergente"
        with self.assertRaisesRegex(validate_traceability.TraceabilityError, "dmc.json"):
            validate_traceability.validate(self.manifest, changed)

    def test_project_matrix_must_match_manifest(self) -> None:
        validate_traceability.validate_project_matrix(
            self.manifest, REPOSITORY_ROOT / "docs/projeto.md"
        )


if __name__ == "__main__":
    unittest.main()
