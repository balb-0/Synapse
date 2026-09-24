from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.architecture import validate_architecture_docs as validator


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def write(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class MarkdownAnchorTests(unittest.TestCase):
    def test_generates_gitlab_anchors_with_accents_dashes_and_duplicates(self) -> None:
        anchors = validator.markdown_anchors(
            "# Visão geral\n## 5.2.1 C01 — Portfólio e Ciclo\n# Visão geral\n"
        )

        self.assertIn("visão-geral", anchors)
        self.assertIn("521-c01--portfólio-e-ciclo", anchors)
        self.assertIn("visão-geral-1", anchors)

    def test_preserves_explicit_html_anchor(self) -> None:
        anchors = validator.markdown_anchors('<a id="decisao-1"></a>\n# Título')

        self.assertIn("decisao-1", anchors)


class LinkValidationTests(unittest.TestCase):
    def test_accepts_existing_file_and_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root, "docs/origem.md", "[Destino](destino.md#seção-válida)")
            write(root, "docs/destino.md", "# Seção válida")

            errors = validator.validate_links(root, (Path("docs/origem.md"),))

            self.assertEqual([], errors)

    def test_reports_missing_file_and_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(
                root,
                "docs/origem.md",
                "[Arquivo](ausente.md) [Âncora](destino.md#ausente)",
            )
            write(root, "docs/destino.md", "# Existente")

            errors = validator.validate_links(root, (Path("docs/origem.md"),))

            self.assertEqual(2, len(errors))
            self.assertTrue(any("link inexistente" in error for error in errors))
            self.assertTrue(any("âncora inexistente" in error for error in errors))


class DiagramValidationTests(unittest.TestCase):
    def test_reports_missing_required_legend(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            diagram = Path("docs/assets/uml/exemplo.plantuml")
            write(root, str(diagram), "@startuml\nactor Operador\n@enduml")
            write(root, "docs/projeto.md", "[Diagrama](assets/uml/exemplo.plantuml)")

            with patch.object(validator, "DIAGRAMS", {diagram: ("Operador", "planejado")}):
                errors = validator.validate_diagrams(root)

            self.assertEqual(
                ["docs/assets/uml/exemplo.plantuml: referência obrigatória ausente: planejado"],
                errors,
            )


class RepositoryValidationTests(unittest.TestCase):
    def test_current_repository_is_coherent(self) -> None:
        self.assertEqual([], validator.validate_repository(PROJECT_ROOT))


if __name__ == "__main__":
    unittest.main()
