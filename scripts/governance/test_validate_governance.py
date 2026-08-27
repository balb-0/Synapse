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
        self.assertEqual(summary["classes"], 4)
        self.assertEqual(summary["sources"], 6)

    def test_missing_section_heading_fails(self) -> None:
        document = self.document.replace(
            "# 4. Classificação e Proteção de Dados",
            "# Classificação e Proteção de Dados",
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


if __name__ == "__main__":
    unittest.main()
