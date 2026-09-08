#!/usr/bin/env python3
"""Testes da validação estrutural do Data Model Canvas."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import validate_dmc


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class ValidateDmcTest(unittest.TestCase):
    def setUp(self) -> None:
        self.document = validate_dmc.load_document(REPOSITORY_ROOT / "docs/dmc.json")

    def test_current_export_is_valid(self) -> None:
        summary = validate_dmc.validate_document(self.document)
        self.assertEqual(summary["cubos"], list(validate_dmc.EXPECTED_CUBES))

    def test_invalid_json_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dmc.json"
            path.write_text('{"schemaVersion":', encoding="utf-8")
            with self.assertRaisesRegex(validate_dmc.DmcValidationError, "JSON inválido"):
                validate_dmc.load_document(path)

    def test_duplicate_cube_id_fails(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cubos"][1]["id"] = changed["cubos"][0]["id"]
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "IDs.*únicos"):
            validate_dmc.validate_document(changed)

    def test_noncanonical_cube_id_fails(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cubos"][0]["id"] = "custom-1"
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "IDs.*contrato"):
            validate_dmc.validate_document(changed)

    def test_boolean_schema_version_fails(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["schemaVersion"] = True
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "schemaVersion"):
            validate_dmc.validate_document(changed)

    def test_multiple_schemas_fail(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cubos"][0]["fields"]["snowflakeSchema"] = True
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "exatamente um esquema"):
            validate_dmc.validate_document(changed)

    def test_multiple_fact_types_fail(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cubos"][0]["fields"]["transactionFact"] = True
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "tipo de fato"):
            validate_dmc.validate_document(changed)

    def test_dimensional_lists_reject_non_string_items(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cubos"][0]["lists"]["metricas"].append(42)
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "metricas"):
            validate_dmc.validate_document(changed)

    def test_missing_corporate_governance_key_fails(self) -> None:
        changed = copy.deepcopy(self.document)
        del changed["governancaCorporativa"]["owner"]
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "Governança Corporativa"):
            validate_dmc.validate_document(changed)

    def test_round_trip_must_preserve_corporate_sections(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["negocioEConsumo"]["usuariosCanais"].append("Canal perdido no round-trip")
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "round-trip alterou"):
            validate_dmc.validate_preserved_sections(changed, self.document)

    def test_round_trip_must_preserve_cubes(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cubos"][0]["lists"]["metricas"].append("Métrica perdida")
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "cubos"):
            validate_dmc.validate_preserved_sections(changed, self.document)

    def test_serialization_format_does_not_affect_validation(self) -> None:
        serialized = json.dumps(self.document, separators=(",", ":"), ensure_ascii=False)
        validate_dmc.validate_document(json.loads(serialized))

    def test_invalid_utf8_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dmc.json"
            path.write_bytes(b"\xff")
            with self.assertRaisesRegex(validate_dmc.DmcValidationError, "JSON inválido"):
                validate_dmc.load_document(path)


if __name__ == "__main__":
    unittest.main()
