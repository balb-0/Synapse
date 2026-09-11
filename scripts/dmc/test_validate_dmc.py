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
        self.assertEqual(summary["taticas"], list(validate_dmc.EXPECTED_TACTIC_IDS))
        self.assertTrue(summary["etl"])

    def test_missing_tactics_fails(self) -> None:
        changed = copy.deepcopy(self.document)
        del changed["taticas"]
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "taticas"):
            validate_dmc.validate_document(changed)

    def test_tactic_requires_quality_attribute(self) -> None:
        changed = copy.deepcopy(self.document)
        fields = changed["taticas"][0]["fields"]
        for key in validate_dmc.TACTIC_BOOLEAN_FIELDS:
            fields[key] = False
        fields["qaOutro"] = ""
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "atributo de qualidade"):
            validate_dmc.validate_document(changed)

    def test_tactic_requires_evidence(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["taticas"][0]["lists"]["evidencias"] = []
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "evidências"):
            validate_dmc.validate_document(changed)

    def test_etl_requires_every_official_field(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["etl"]["fields"]["linhagem"] = " "
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "ETL.*vazio"):
            validate_dmc.validate_document(changed)

    def test_etl_requires_verifications(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["etl"]["lists"]["verificacoes"] = []
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "fontes, camadas"):
            validate_dmc.validate_document(changed)

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

    def test_invalid_metadata_date_fails(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["metadata"]["data"] = "2026-02-30"
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "data ISO válida"):
            validate_dmc.validate_document(changed)

    def test_invalid_metadata_version_fails(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["metadata"]["versao"] = "final"
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "inteiro.inteiro"):
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

    def test_missing_dimensional_field_fails(self) -> None:
        changed = copy.deepcopy(self.document)
        del changed["cubos"][0]["fields"]["bridgeTables"]
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "fields.bridgeTables"):
            validate_dmc.validate_document(changed)

    def test_non_boolean_selector_fails(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cubos"][0]["fields"]["snowflakeSchema"] = "false"
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "usar booleanos"):
            validate_dmc.validate_document(changed)

    def test_cube_requires_exactly_one_classification(self) -> None:
        changed = copy.deepcopy(self.document)
        fields = changed["cubos"][0]["fields"]
        for key in (
            "classificacaoPublico",
            "classificacaoInterno",
            "classificacaoConfidencial",
            "classificacaoRestrito",
        ):
            fields[key] = False
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "classificação"):
            validate_dmc.validate_document(changed)

        changed = copy.deepcopy(self.document)
        changed["cubos"][0]["fields"]["classificacaoPublico"] = True
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "classificação"):
            validate_dmc.validate_document(changed)

    def test_personal_data_requires_restricted_classification(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cubos"][1]["fields"]["classificacaoRestrito"] = False
        changed["cubos"][1]["fields"]["classificacaoInterno"] = True
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "dado pessoal"):
            validate_dmc.validate_document(changed)

    def test_blank_dimensional_text_field_fails(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cubos"][0]["fields"]["dimensoesConformadas"] = "  "
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "campos textuais"):
            validate_dmc.validate_document(changed)

    def test_dimensional_lists_reject_non_string_items(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cubos"][0]["lists"]["metricas"].append(42)
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "metricas"):
            validate_dmc.validate_document(changed)

    def test_dimensional_lists_reject_duplicate_items(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cubos"][0]["lists"]["fatos"].append(
            changed["cubos"][0]["lists"]["fatos"][0].upper()
        )
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "duplicados em fatos"):
            validate_dmc.validate_document(changed)

    def test_cube_rejects_unknown_field(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cubos"][0]["fields"]["campoInventado"] = "valor"
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "desconhecidos"):
            validate_dmc.validate_document(changed)

    def test_cube_rejects_unknown_list(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cubos"][0]["lists"]["listaInventada"] = ["valor"]
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "desconhecidos"):
            validate_dmc.validate_document(changed)

    def test_missing_corporate_governance_key_fails(self) -> None:
        changed = copy.deepcopy(self.document)
        del changed["governancaCorporativa"]["owner"]
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "Governança Corporativa"):
            validate_dmc.validate_document(changed)

    def test_governance_role_must_state_source_and_pending_approval(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["governancaCorporativa"]["owner"] = "Fabio Moreira"
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "fonte documental"):
            validate_dmc.validate_document(changed)

    def test_external_custody_must_remain_conditional(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["governancaCorporativa"]["custodian"] = (
            "Baseline documental: Rodrigo Giorgetto e RentalHost; homologação pendente."
        )
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "condicional"):
            validate_dmc.validate_document(changed)

    def test_user_channels_must_match_uc01_to_uc04(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["negocioEConsumo"]["usuariosCanais"].pop()
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "UC01–UC04"):
            validate_dmc.validate_document(changed)

    def test_every_channel_must_state_access_restriction(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["negocioEConsumo"]["usuariosCanais"][0] = (
            "UC01 — Central de Pesquisas: dashboard."
        )
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "restrição"):
            validate_dmc.validate_document(changed)

    def test_decisions_and_risks_must_match_dr01_to_dr06(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["negocioEConsumo"]["decisoesRiscos"].pop()
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "DR01–DR06"):
            validate_dmc.validate_document(changed)

    def test_every_decision_or_risk_must_state_impact_and_status(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["negocioEConsumo"]["decisoesRiscos"][0] = "DR01 — Pendente"
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "impacto e estado"):
            validate_dmc.validate_document(changed)

    def test_consumption_indicators_must_match_i01_to_i25(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["negocioEConsumo"]["indicadoresConsumo"].pop()
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "I01–I25"):
            validate_dmc.validate_document(changed)

    def test_consumption_indicators_must_keep_canonical_order(self) -> None:
        changed = copy.deepcopy(self.document)
        indicators = changed["negocioEConsumo"]["indicadoresConsumo"]
        indicators[0], indicators[1] = indicators[1], indicators[0]
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "I01–I25"):
            validate_dmc.validate_document(changed)

    def test_business_questions_must_match_pb01_to_pb13(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["negocioEConsumo"]["perguntasNegocio"][0] = "Pergunta sem ID"
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "PB01–PB13"):
            validate_dmc.validate_document(changed)

    def test_business_objective_cannot_claim_achieved_result(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["negocioEConsumo"]["objetivosNegocio"][0] = "Integração concluída"
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "pretendidos"):
            validate_dmc.validate_document(changed)

    def test_business_process_must_preserve_current_state(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["negocioEConsumo"]["processosNegocio"][0] = "Processo futuro"
        with self.assertRaisesRegex(validate_dmc.DmcValidationError, "estado atual"):
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
