from __future__ import annotations

import hashlib
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from validate_governance import (
    GovernanceValidationError,
    validate_document,
    validate_tapi_hash,
    validate_tracked_inputs,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_PATH = REPOSITORY_ROOT / "docs" / "Governança-de-Dados-do-Projeto.md"


class GovernanceDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = DOCUMENT_PATH.read_text(encoding="utf-8")

    def test_current_document_is_valid(self) -> None:
        summary = validate_document(self.document)
        self.assertEqual(summary["governance_roles"], 3)
        self.assertEqual(summary["catalog_common_fields"], 43)
        self.assertEqual(summary["catalog_asset_types"], 4)
        self.assertEqual(summary["catalog_dimensions"], 9)
        self.assertEqual(summary["catalog_measures"], 6)
        self.assertEqual(summary["catalog_cubes"], 4)
        self.assertEqual(summary["classes"], 4)
        self.assertEqual(summary["sources"], 6)
        self.assertEqual(summary["profiles"], 8)
        self.assertEqual(summary["internal_layers"], 3)

    def test_missing_section_heading_fails(self) -> None:
        document = self.document.replace(
            "# 4. Classificação e Proteção de Dados",
            "# Classificação e Proteção de Dados",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "heading obrigatório"):
            validate_document(document)

    def test_duplicate_section_heading_fails(self) -> None:
        document = self.document.replace(
            "# 5. Segurança e Acesso",
            "# 5. Segurança e Acesso\n\n# 5. Segurança e Acesso",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "heading obrigatório"):
            validate_document(document)

    def test_placeholder_in_section_four_fails(self) -> None:
        document = self.document.replace(
            "# 4. Classificação e Proteção de Dados",
            "# 4. Classificação e Proteção de Dados\n\n_conteúdo_",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "placeholder"):
            validate_document(document)

    def test_missing_class_fails(self) -> None:
        document = re.sub(
            r"^\| \*\*Público\*\*.*\n",
            "",
            self.document,
            count=1,
            flags=re.MULTILINE,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "Público"):
            validate_document(document)

    def test_duplicate_class_fails(self) -> None:
        row = next(
            line for line in self.document.splitlines() if line.startswith("| **Público**")
        )
        document = self.document.replace(row, f"{row}\n{row}", 1)
        with self.assertRaisesRegex(GovernanceValidationError, "duplicadas"):
            validate_document(document)

    def test_truncated_asset_row_fails(self) -> None:
        row = next(
            line
            for line in self.document.splitlines()
            if line.startswith("| **Pessoa/Cliente**")
        )
        document = self.document.replace(row, "| Pessoa/Cliente | campos | Confidencial |", 1)
        with self.assertRaisesRegex(GovernanceValidationError, "largura inválida"):
            validate_document(document)

    def test_missing_source_fails(self) -> None:
        document = self.document.replace("clientes.csv", "fonte-de-clientes")
        with self.assertRaisesRegex(GovernanceValidationError, "clientes.csv"):
            validate_document(document)

    def test_identifiable_source_cannot_be_public(self) -> None:
        source_line = next(
            line
            for line in self.document.splitlines()
            if line.startswith("| **Pessoa/Cliente**") and "`clientes.csv`" in line
        )
        public_line = source_line.replace("| Confidencial |", "| Público |")
        document = self.document.replace(source_line, public_line, 1)
        with self.assertRaisesRegex(GovernanceValidationError, "identificável"):
            validate_document(document)

    def test_person_cannot_be_downgraded_to_internal(self) -> None:
        row = next(
            line
            for line in self.document.splitlines()
            if line.startswith("| **Pessoa/Cliente**")
        )
        document = self.document.replace(
            row, row.replace("| Confidencial |", "| Interno |"), 1
        )
        with self.assertRaisesRegex(GovernanceValidationError, "classe mínima"):
            validate_document(document)

    def test_company_cannot_be_classified_as_public(self) -> None:
        row = next(
            line
            for line in self.document.splitlines()
            if line.startswith("| **Empresa**")
        )
        document = self.document.replace(
            row, row.replace("| Confidencial |", "| Público |"), 1
        )
        with self.assertRaisesRegex(GovernanceValidationError, "classe mínima"):
            validate_document(document)

    def test_required_risk_field_must_be_in_asset_matrix(self) -> None:
        document = self.document.replace("respondent_id", "identificador_resposta")
        with self.assertRaisesRegex(GovernanceValidationError, "respondent_id"):
            validate_document(document)

    def test_placeholder_in_section_five_fails(self) -> None:
        document = self.document.replace(
            "# 5. Segurança e Acesso",
            "# 5. Segurança e Acesso\n\n_conteúdo_",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "seção 5"):
            validate_document(document)

    def test_public_cannot_access_staging(self) -> None:
        source = "| Público externo | — | — | — | L da visão pública |"
        document = self.document.replace(
            source,
            "| Público externo | L | — | — | L da visão pública |",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "camada interna"):
            validate_document(document)

    def test_participant_cannot_access_analytics(self) -> None:
        source = (
            "| Solicitantes/participantes | — | — | — | "
            "L da entrega autorizada |"
        )
        document = self.document.replace(
            source,
            "| Solicitantes/participantes | — | — | L | L da entrega autorizada |",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "camada interna"):
            validate_document(document)

    def test_external_profile_cannot_write_publication(self) -> None:
        source = "| Público externo | — | — | — | L da visão pública |"
        document = self.document.replace(
            source,
            "| Público externo | — | — | — | G da visão pública |",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "somente leitura"):
            validate_document(document)

    def test_public_cannot_read_internal_object(self) -> None:
        source = "| Público externo | — | — | — | — | — | L da visão pública | — |"
        document = self.document.replace(
            source,
            "| Público externo | L | — | — | — | — | L da visão pública | — |",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "objeto interno"):
            validate_document(document)

    def test_custodian_content_reading_must_be_exceptional(self) -> None:
        source = (
            "| Data Custodian / TI | A técnica; L excepcional | "
            "A técnica; L excepcional | A técnica; L excepcional | "
            "G da versão aprovada |"
        )
        document = self.document.replace(
            source,
            "| Data Custodian / TI | A técnica; L | A técnica; L | "
            "A técnica; L | G da versão aprovada |",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "política documentada"):
            validate_document(document)

    def test_central_cannot_access_staging(self) -> None:
        source = "| Equipe da Central | — | L/G via aplicação | L | G de preparação |"
        document = self.document.replace(
            source,
            "| Equipe da Central | L | L/G via aplicação | L | G de preparação |",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "política documentada"):
            validate_document(document)

    def test_owner_cannot_read_person_identity(self) -> None:
        source = "| Data Owner | L | L | — | — | L | A de aprovação | A de regra de negócio |"
        document = self.document.replace(
            source,
            "| Data Owner | L | L | L | — | L | A de aprovação | A de regra de negócio |",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "política documentada"):
            validate_document(document)

    def test_academic_profile_cannot_read_identity(self) -> None:
        source = (
            "| Equipe acadêmica | — | — | — | — | "
            "L somente de agregado aprovado | L da versão pública | — |"
        )
        document = self.document.replace(
            source,
            "| Equipe acadêmica | — | — | L | — | "
            "L somente de agregado aprovado | L da versão pública | — |",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "política documentada"):
            validate_document(document)

    def test_custodian_cannot_gain_extra_layer_permission(self) -> None:
        source = (
            "| Data Custodian / TI | A técnica; L excepcional | "
            "A técnica; L excepcional | A técnica; L excepcional | "
            "G da versão aprovada |"
        )
        document = self.document.replace(
            source,
            "| Data Custodian / TI | A técnica; L/G excepcional | "
            "A técnica; L excepcional | A técnica; L excepcional | "
            "G da versão aprovada |",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "política documentada"):
            validate_document(document)

    def test_ingestion_service_cannot_access_analytics(self) -> None:
        source = "| Serviço de ingestão | G | G de promoção | — | — |"
        document = self.document.replace(
            source, "| Serviço de ingestão | G | G de promoção | L | — |", 1
        )
        with self.assertRaisesRegex(GovernanceValidationError, "política documentada"):
            validate_document(document)

    def test_duplicate_profile_fails(self) -> None:
        row = next(
            line
            for line in self.document.splitlines()
            if line.startswith("| **Equipe da Central**")
        )
        document = self.document.replace(row, f"{row}\n{row}", 1)
        with self.assertRaisesRegex(GovernanceValidationError, "duplicadas"):
            validate_document(document)

    def test_missing_governance_role_fails(self) -> None:
        row = next(
            line
            for line in self.document.splitlines()
            if line.startswith("| **Data Steward**")
        )
        document = self.document.replace(row, "", 1)
        with self.assertRaisesRegex(GovernanceValidationError, "Data Steward"):
            validate_document(document)

    def test_governance_map_is_required(self) -> None:
        document = self.document.replace("```mermaid\nflowchart LR", "```text\nfluxo", 1)
        with self.assertRaisesRegex(GovernanceValidationError, "mapa funcional"):
            validate_document(document)

    def test_governance_map_requires_actor_nodes(self) -> None:
        start = self.document.index("```mermaid\nflowchart LR")
        end = self.document.index("```", start + 3) + 3
        replacement = (
            "```mermaid\nflowchart LR\n"
            "%% Data Owner Data Stewards Data Custodian / TI Controlador "
            "Operador e suboperadores Encarregado RentalHost\n```"
        )
        document = self.document[:start] + replacement + self.document[end:]
        with self.assertRaisesRegex(GovernanceValidationError, "nó obrigatório"):
            validate_document(document)

    def test_governance_raci_is_required(self) -> None:
        document = self.document.replace(
            "| Atividade | Data Owner | Data Steward | Central de Pesquisas |",
            "| Processo | Data Owner | Data Steward | Central de Pesquisas |",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "Atividade"):
            validate_document(document)

    def test_governance_raci_cannot_have_empty_assignment(self) -> None:
        row = next(
            line
            for line in self.document.splitlines()
            if line.startswith("| Definir significado, criticidade")
        )
        document = self.document.replace(
            row,
            "| Definir significado, criticidade e uso de negócio dos metadados "
            "| | | | | | | |",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "matriz RACI"):
            validate_document(document)

    def test_custody_interface_cannot_have_empty_evidence(self) -> None:
        row = next(
            line
            for line in self.document.splitlines()
            if line.startswith("| Fonte operacional → `staging`")
        )
        cells = row.rsplit("|", 2)
        document = self.document.replace(row, f"{cells[0]}| |", 1)
        with self.assertRaisesRegex(GovernanceValidationError, "interfaces de custódia"):
            validate_document(document)

    def test_placeholder_in_section_three_fails(self) -> None:
        document = self.document.replace(
            "# 3. Gestão de Metadados e Catálogo",
            "# 3. Gestão de Metadados e Catálogo\n\n_conteúdo_",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "seção 3"):
            validate_document(document)

    def test_missing_common_catalog_field_fails(self) -> None:
        document = self.document.replace("`asset_id`", "identificador do ativo")
        with self.assertRaisesRegex(GovernanceValidationError, "asset_id"):
            validate_document(document)

    def test_common_catalog_field_cannot_have_empty_contract(self) -> None:
        row = next(
            line
            for line in self.document.splitlines()
            if line.startswith("| `asset_id` | Identificador estável")
        )
        document = self.document.replace(row, "| `asset_id` | | |", 1)
        with self.assertRaisesRegex(GovernanceValidationError, "metadados comuns"):
            validate_document(document)

    def test_missing_catalog_asset_type_fails(self) -> None:
        document = self.document.replace("| **Medida** |", "| **Métrica** |", 1)
        with self.assertRaisesRegex(GovernanceValidationError, "Medida"):
            validate_document(document)

    def test_source_mapping_evidence_is_required(self) -> None:
        document = self.document.replace(
            "`confianca_extracao`", "confiança da extração"
        )
        with self.assertRaisesRegex(GovernanceValidationError, "confianca_extracao"):
            validate_document(document)

    def test_catalog_example_requires_dimension(self) -> None:
        row = next(
            line
            for line in self.document.splitlines()
            if line.startswith("| `DIM_EXECUCAO_CARGA` |")
        )
        document = self.document.replace(row, "", 1)
        with self.assertRaisesRegex(GovernanceValidationError, "DIM_EXECUCAO_CARGA"):
            validate_document(document)

    def test_catalog_example_value_cannot_be_empty(self) -> None:
        row = next(
            line
            for line in self.document.splitlines()
            if line.startswith("| `asset_id` | `dw.fact.fato_ciclo_pesquisa`")
        )
        document = self.document.replace(row, "| `asset_id` | |", 1)
        with self.assertRaisesRegex(GovernanceValidationError, "exemplo de catálogo"):
            validate_document(document)

    def test_catalog_dimension_contract_cannot_be_empty(self) -> None:
        row = next(
            line
            for line in self.document.splitlines()
            if line.startswith("| `DIM_AREA` |")
        )
        document = self.document.replace(row, "| `DIM_AREA` | | | |", 1)
        with self.assertRaisesRegex(GovernanceValidationError, "dimensões do exemplo"):
            validate_document(document)

    def test_catalog_example_requires_measure_contract(self) -> None:
        row = next(
            line
            for line in self.document.splitlines()
            if line.startswith("| `dias_uteis_ciclo_total` | Medida inteira")
        )
        document = self.document.replace(row, "", 1)
        with self.assertRaisesRegex(GovernanceValidationError, "dias_uteis_ciclo_total"):
            validate_document(document)

    def test_catalog_requires_all_four_cubes(self) -> None:
        row = next(
            line
            for line in self.document.splitlines()
            if line.startswith("| **C04 — Resultados e Questionários**")
        )
        document = self.document.replace(row, "", 1)
        with self.assertRaisesRegex(GovernanceValidationError, "C04"):
            validate_document(document)

    def test_catalog_rejects_invalid_cube_prefix(self) -> None:
        document = self.document.replace(
            "| **C01 — Portfólio e Ciclo** |",
            "| **C01_extra — Portfólio e Ciclo** |",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "C01"):
            validate_document(document)

    def test_catalog_requires_canonical_cube_name(self) -> None:
        document = self.document.replace(
            "| **C04 — Resultados e Questionários** |",
            "| **C04 — Questionários e Cobertura** |",
            1,
        )
        with self.assertRaisesRegex(GovernanceValidationError, "C04"):
            validate_document(document)

    def test_catalog_must_distinguish_fallback_from_unmapped(self) -> None:
        document = self.document.replace("fallback_por_titulo", "nao_mapeado")
        with self.assertRaisesRegex(GovernanceValidationError, "fallback_por_titulo"):
            validate_document(document)


class TapiHashTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = DOCUMENT_PATH.read_text(encoding="utf-8")

    def test_matching_tapi_hash_passes(self) -> None:
        content = b"TAPI sintetico para teste\n"
        digest = hashlib.sha256(content).hexdigest()
        document = re.sub(
            r"(?<=SHA-256\n`)[0-9a-f]{64}", digest, self.document, count=1
        )
        with tempfile.TemporaryDirectory() as directory:
            tapi = Path(directory) / "tapi.txt"
            tapi.write_bytes(content)
            self.assertEqual(validate_tapi_hash(document, tapi), digest)

    def test_modified_tapi_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tapi = Path(directory) / "tapi.txt"
            tapi.write_bytes(b"conteudo diferente")
            with self.assertRaisesRegex(GovernanceValidationError, "divergente"):
                validate_tapi_hash(self.document, tapi)

    def test_missing_tapi_hash_fails(self) -> None:
        document = re.sub(r"[0-9a-f]{64}", "hash-ausente", self.document, count=1)
        with tempfile.TemporaryDirectory() as directory:
            tapi = Path(directory) / "tapi.txt"
            tapi.write_bytes(b"conteudo")
            with self.assertRaisesRegex(GovernanceValidationError, "exatamente um"):
                validate_tapi_hash(document, tapi)

    def test_multiple_tapi_hashes_fail(self) -> None:
        digest = re.search(r"[0-9a-f]{64}", self.document).group(0)
        document = self.document.replace(
            "# 5. Segurança e Acesso",
            f"SHA-256 adicional `{digest}`\n\n# 5. Segurança e Acesso",
            1,
        )
        with tempfile.TemporaryDirectory() as directory:
            tapi = Path(directory) / "tapi.txt"
            tapi.write_bytes(b"conteudo")
            with self.assertRaisesRegex(GovernanceValidationError, "exatamente um"):
                validate_tapi_hash(document, tapi)


class TrackedInputsTests(unittest.TestCase):
    def _repository(self, directory: str) -> Path:
        root = Path(directory)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        return root

    def test_ignored_or_untracked_csv_does_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._repository(directory)
            (root / "README.md").write_text("fixture segura", encoding="utf-8")
            (root / "clientes.csv").write_text("id\n1\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "README.md"], check=True)
            self.assertEqual(validate_tracked_inputs(root), [])

    def test_tracked_real_source_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._repository(directory)
            (root / "clientes.csv").write_text("id\n1\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "clientes.csv"], check=True)
            self.assertEqual(validate_tracked_inputs(root), ["clientes.csv"])

    def test_tracked_source_alias_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._repository(directory)
            (root / "teste.csv").write_text("id\n1\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "teste.csv"], check=True)
            self.assertEqual(validate_tracked_inputs(root), ["teste.csv"])

    def test_renamed_csv_with_high_risk_header_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._repository(directory)
            (root / "export.csv").write_text(
                "id_cliente,e-mail,valor\n1,pessoa@example.invalid,x\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "-C", str(root), "add", "export.csv"], check=True)
            self.assertEqual(validate_tracked_inputs(root), ["export.csv"])

    def test_synthetic_csv_without_project_schema_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._repository(directory)
            (root / "fixture.csv").write_text("cenario,total\na,1\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "fixture.csv"], check=True)
            self.assertEqual(validate_tracked_inputs(root), [])

    def test_renamed_csv_with_common_personal_header_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._repository(directory)
            (root / "contatos.csv").write_text(
                "nome,telefone\nPessoa,000000000\n", encoding="utf-8"
            )
            subprocess.run(["git", "-C", str(root), "add", "contatos.csv"], check=True)
            self.assertEqual(validate_tracked_inputs(root), ["contatos.csv"])


if __name__ == "__main__":
    unittest.main()
