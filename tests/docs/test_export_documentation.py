"""Publication must fail for missing, unsafe or stale inputs."""

import importlib.util
import json
import subprocess
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

    def git(self, *arguments):
        return subprocess.check_output(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.org", *arguments],
            cwd=self.root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()

    def commit_source(self):
        self.git("init")
        self.git("add", "docs/projeto.md")
        self.git("commit", "-m", "source")
        return self.git("rev-parse", "HEAD")

    def test_snapshot_includes_link_target_added_after_source(self):
        source_revision = self.commit_source()
        target = self.root / "docs/novo.md"
        target.write_text("Novo documento", encoding="utf-8")
        self.git("add", "docs/novo.md")
        self.git("commit", "-m", "add link target")
        snapshot = export.select_snapshot(self.root, {self.source}, {target})
        self.assertNotEqual(source_revision, snapshot)
        self.assertEqual(self.git("rev-parse", "HEAD"), snapshot)

    def test_publication_only_commit_does_not_change_snapshot(self):
        source_revision = self.commit_source()
        pdf = self.root / "publication.pdf"
        pdf.write_bytes(b"PDF")
        self.git("add", "publication.pdf")
        self.git("commit", "-m", "publish PDF")
        self.assertEqual(source_revision, export.select_snapshot(self.root, {self.source}, set()))

    def test_uncommitted_link_target_blocks_snapshot(self):
        self.commit_source()
        target = self.root / "docs/novo.md"
        target.write_text("Ainda não commitado", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "não existe na revisão"):
            export.select_snapshot(self.root, {self.source}, {target})

    def test_modified_existing_link_target_blocks_snapshot(self):
        self.commit_source()
        target = self.root / "docs/novo.md"
        target.write_text("Texto original", encoding="utf-8")
        self.git("add", "docs/novo.md")
        self.git("commit", "-m", "add target")
        target.write_text("Texto alterado", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "alteração não commitada"):
            export.select_snapshot(self.root, {self.source}, {target})

    def test_staged_existing_link_target_blocks_snapshot(self):
        self.commit_source()
        target = self.root / "docs/novo.md"
        target.write_text("Texto original", encoding="utf-8")
        self.git("add", "docs/novo.md")
        self.git("commit", "-m", "add target")
        target.write_text("Texto alterado", encoding="utf-8")
        self.git("add", "docs/novo.md")
        # Restoring the working tree must not hide a staged contradiction.
        target.write_text("Texto original", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "divergente no stage"):
            export.select_snapshot(self.root, {self.source}, {target})


if __name__ == "__main__":
    unittest.main()
