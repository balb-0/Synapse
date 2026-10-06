"""Publication must fail for missing, unsafe or stale inputs."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/docs/export_documentation.py"
SPEC = importlib.util.spec_from_file_location("export_documentation", SCRIPT)
export = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(export)


class ExportValidationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        self.source = self.root / "docs/projeto.md"
        self.source.parent.mkdir()
        self.source.write_text("# Documentação", encoding="utf-8")
        self.image = self.root / "docs/figura.png"
        self.image.write_bytes(b"example")

    def test_relative_image_is_tracked_and_made_absolute(self):
        parser = export.DocumentHTML(self.root, self.source, "abc123")
        parser.feed('<img src="figura.png" alt="Diagrama">')
        self.assertEqual({self.image}, parser.assets)
        self.assertIn(self.image.as_uri(), "".join(parser.parts))

    def test_missing_image_blocks_export(self):
        parser = export.DocumentHTML(self.root, self.source, "abc123")
        with self.assertRaisesRegex(ValueError, "ausente"):
            parser.feed('<img src="ausente.png">')

    def test_external_image_blocks_export(self):
        parser = export.DocumentHTML(self.root, self.source, "abc123")
        with self.assertRaisesRegex(ValueError, "externa"):
            parser.feed('<img src="https://example.org/image.png">')

    def test_path_traversal_blocks_export(self):
        with self.assertRaisesRegex(ValueError, "fora do repositório"):
            export.resolve_local(self.root, self.source, "../../outside.txt")

    def test_local_document_link_is_pinned_and_fragment_preserved(self):
        parser = export.DocumentHTML(self.root, self.source, "abc123")
        parser.feed('<a href="projeto.md#documentação">Origem</a>')
        self.assertIn("/-/blob/abc123/docs/projeto.md#documentação", "".join(parser.parts))

    def test_internal_anchors_are_collected_and_duplicates_rejected(self):
        parser = export.DocumentHTML(self.root, self.source, "abc123")
        parser.feed('<h1 id="introdução">Introdução</h1><a href="#introdução">Sumário</a>')
        self.assertEqual(parser.anchors, parser.fragments)
        with self.assertRaisesRegex(ValueError, "duplicada"):
            parser.feed('<h2 id="introdução">Outra seção</h2>')

    def test_active_html_is_rejected(self):
        for content in ("<script>alert(1)</script>", '<img onerror="alert(1)">'):
            with self.subTest(content=content), self.assertRaises(ValueError):
                export.DocumentHTML(self.root, self.source, "abc123").feed(content)

    def test_changed_inputs_fail_check_before_pdf_parse(self):
        manifest = self.root / export.MANIFEST
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"inputs": {"source": "old"}}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "desatualizado"):
            export.check(self.root, {"inputs": {"source": "new"}})

    def test_changed_pdf_bytes_fail_hash_check(self):
        manifest = self.root / export.MANIFEST
        manifest.parent.mkdir(parents=True)
        (self.root / export.OUTPUT).write_bytes(b"modified PDF")
        manifest.write_text(json.dumps({"pdf_sha256": "old"}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Hash do PDF"):
            export.check(self.root, {})


if __name__ == "__main__":
    unittest.main()
