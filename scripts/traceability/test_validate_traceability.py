#!/usr/bin/env python3
"""Testes do contrato executável de rastreabilidade analítica."""

from __future__ import annotations

import copy
import hashlib
import os
import tempfile
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
        self.assertEqual(summary["pendingIndicators"], 3)

    def test_missing_question_fails(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["questions"].pop()
        with self.assertRaisesRegex(validate_traceability.TraceabilityError, "PB01–PB13"):
            validate_traceability.validate(changed, self.dmc)

    def test_indicator_gap_fails(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["questions"][0]["indicators"].remove("I01")
        with self.assertRaisesRegex(
            validate_traceability.TraceabilityError, "cobertura de indicadores"
        ):
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

    def test_pending_cube_requires_future_integration(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["questions"][9]["pendingCube"]["dependency"] = "Dependência indefinida"
        with self.assertRaisesRegex(validate_traceability.TraceabilityError, "integração futura"):
            validate_traceability.validate(changed, self.dmc)

    def test_quality_questions_do_not_use_questionnaire_cube(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["questions"][5]["cubes"] = ["C04"]
        changed["questions"][5]["artifacts"] = []
        with self.assertRaisesRegex(validate_traceability.TraceabilityError, "vínculo dimensional"):
            validate_traceability.validate(changed, self.dmc)

    def test_pending_indicators_are_restricted_to_response_and_versioning(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["questions"][9]["pendingIndicators"].append("I01")
        changed["questions"][9]["indicators"].append("I01")
        with self.assertRaisesRegex(validate_traceability.TraceabilityError, "I12, I13 e I15"):
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

    @unittest.skipUnless(
        os.getenv("SINDUSFARMA_SOURCE_DIR"),
        "fontes primárias externas não informadas",
    )
    def test_current_primary_sources_are_valid(self) -> None:
        summary = validate_traceability.validate_primary_sources(
            self.manifest, Path(os.environ["SINDUSFARMA_SOURCE_DIR"])
        )
        self.assertEqual(summary, {"sources": 2, "claims": 12})

    def test_primary_source_hash_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fonte.txt"
            path.write_text("Trecho confirmado", encoding="utf-8")
            manifest = self._primary_source_manifest("0" * 64, "Trecho confirmado")
            with self.assertRaisesRegex(validate_traceability.TraceabilityError, "SHA-256"):
                validate_traceability.validate_primary_sources(manifest, Path(directory))

    def test_primary_source_missing_claim_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fonte.txt"
            content = "Trecho confirmado"
            path.write_text(content, encoding="utf-8")
            manifest = self._primary_source_manifest(
                hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "Trecho ausente",
            )
            with self.assertRaisesRegex(validate_traceability.TraceabilityError, "não sustenta"):
                validate_traceability.validate_primary_sources(manifest, Path(directory))

    @staticmethod
    def _primary_source_manifest(expected_hash: str, phrase: str) -> dict:
        return {
            "primarySources": [
                {
                    "id": "FONTE_TESTE",
                    "filename": "fonte.txt",
                    "sha256": expected_hash,
                    "claims": [{"id": "afirmacao", "phrase": phrase}],
                }
            ]
        }


if __name__ == "__main__":
    unittest.main()
