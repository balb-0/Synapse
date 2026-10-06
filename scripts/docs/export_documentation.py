"""Export the complete principal Markdown document with tracked provenance."""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib.metadata
import json
import logging
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("docs/projeto.md")
OUTPUT = Path("docs/assets/documentacao/documentacao-principal.pdf")
MANIFEST = OUTPUT.with_suffix(".manifest.json")
FONTS = Path("docs/assets/documentacao/fonts")
REPOSITORY = "https://git.inteli.edu.br/graduacao/2026-2a/t13/g05"

STYLE = """
@font-face {font-family:Doc;src:url('fonts/NotoSans-Regular.ttf')}
@font-face {font-family:Doc;src:url('fonts/NotoSans-Bold.ttf');font-weight:700}
@font-face {font-family:Doc;src:url('fonts/NotoSans-Italic.ttf');font-style:italic}
@font-face {font-family:Mono;src:url('fonts/NotoSansMono-Regular.ttf')}
@font-face {font-family:DocMath;src:url('fonts/NotoSansMath-Regular.ttf')}
@font-face {font-family:DocSymbols;src:url('fonts/NotoSansSymbols2-Regular.ttf')}
@font-face {font-family:DocEmoji;src:url('fonts/NotoColorEmoji-subset.ttf')}
@page {size:A4 landscape;margin:15mm 17mm 17mm;
 @top-left {content:'Synapse | Central de Pesquisas';font:8pt Doc;color:#586678}
 @bottom-right {content:counter(page) ' / ' counter(pages);font:8pt Doc}
}
body {font:10pt/1.45 Doc,DocMath,DocEmoji,DocSymbols;color:#17283b}
h1,h2,h3,h4 {color:#17445c;break-after:avoid;line-height:1.2}
h1 {font-size:21pt;margin:10mm 0 5mm}
h2 {font-size:16pt;margin-top:7mm} h3 {font-size:12pt}
p,li {orphans:3;widows:3} a {color:#086584;text-decoration:underline}
table {border-collapse:collapse;width:100%;table-layout:fixed;font-size:8pt;
 line-height:1.35;margin:4mm 0;text-align:left}
thead {display:table-header-group} tr {break-inside:avoid}
th,td {border:0.3pt solid #b2c1c9;padding:2mm;overflow-wrap:anywhere}
th {background:#e8f0f3;text-align:left} td {vertical-align:top}
img {display:block;max-width:100%;max-height:145mm;width:auto;height:auto;
 object-fit:contain;margin:4mm auto;break-inside:avoid}
code {font:8.5pt Mono,DocMath,DocEmoji,DocSymbols;overflow-wrap:anywhere}
pre {font:8pt/1.35 Mono,DocMath,DocEmoji,DocSymbols;white-space:pre-wrap;overflow-wrap:anywhere;
 background:#eef3f5;padding:3mm;border-left:2pt solid #47778c}
pre code {font:inherit} blockquote {border-left:2pt solid #b0c5cc;
 margin:3mm 0;padding:1mm 4mm;color:#42566a}
sub,sup {font-size:8pt} .provenance {font-size:9pt;background:#eef3f5;padding:4mm}
div[align=center] {text-align:center} div[align=center] table {text-align:left}
"""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug(text: str) -> str:
    """Match GitLab/GitHub heading identifiers, keeping accented letters."""
    return re.sub(r"[^\w\- ]", "", text.lower(), flags=re.UNICODE).replace(" ", "-")


def resolve_local(root: Path, source: Path, value: str) -> Path:
    path = unquote(urlsplit(value).path)
    result = root / path.lstrip("/") if path.startswith("/") else source.parent / path
    result = result.resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError(f"Referência fora do repositório: {value}")
    if not result.is_file():
        raise ValueError(f"Arquivo referenciado ausente: {value}")
    return result


class DocumentHTML(HTMLParser):
    """Collect dependencies, pin local links and forbid active/remote assets."""

    def __init__(self, root: Path, source: Path, revision: str):
        super().__init__(convert_charrefs=False)
        self.root, self.source, self.revision = root, source, revision
        self.parts: list[str] = []
        self.assets: set[Path] = set()
        self.local_links: set[Path] = set()
        self.anchors: set[str] = set()
        self.fragments: set[str] = set()

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "iframe", "object", "embed"}:
            raise ValueError(f"Elemento ativo não permitido: {tag}")
        updated = []
        for key, value in attrs:
            if key.lower().startswith("on"):
                raise ValueError(f"Atributo ativo não permitido: {key}")
            if key == "id":
                if value in self.anchors:
                    raise ValueError(f"Âncora duplicada: {value}")
                self.anchors.add(value)
            if key == "href" and value:
                parsed = urlsplit(value)
                if value.startswith("#"):
                    self.fragments.add(unquote(value[1:]))
                elif not parsed.scheme and not parsed.netloc:
                    target = resolve_local(self.root, self.source, value)
                    self.local_links.add(target)
                    relative = target.relative_to(self.root).as_posix()
                    value = f"{REPOSITORY}/-/blob/{self.revision}/{quote(relative)}"
                    if parsed.fragment:
                        value += "#" + parsed.fragment
                elif parsed.scheme not in {"https", "http", "mailto"}:
                    raise ValueError(f"Esquema de link não permitido: {value}")
            if tag == "img" and key == "src":
                parsed = urlsplit(value)
                if parsed.scheme or parsed.netloc:
                    raise ValueError(f"Imagem externa não permitida: {value}")
                target = resolve_local(self.root, self.source, value)
                self.assets.add(target)
                value = target.as_uri()
            updated.append(key if value is None else f'{key}="{html.escape(value, quote=True)}"')
        self.parts.append("<" + tag + (" " + " ".join(updated) if updated else "") + ">")

    def handle_endtag(self, tag):
        self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        self.parts.append(data)

    def handle_entityref(self, name):
        self.parts.append(f"&{name};")

    def handle_charref(self, name):
        self.parts.append(f"&#{name};")


def select_snapshot(root: Path, inputs: set[Path], local_links: set[Path]) -> str:
    """Select a committed snapshot with every local hyperlink destination."""
    linked_paths = inputs | local_links
    revision = subprocess.check_output(
        ["git", "log", "-1", "--format=%H", "--"]
        + [p.relative_to(root).as_posix() for p in sorted(linked_paths)],
        cwd=root,
        text=True,
    ).strip()
    for target in local_links:
        relative = target.relative_to(root).as_posix()
        result = subprocess.run(
            ["git", "cat-file", "blob", f"{revision}:{relative}"],
            cwd=root,
            capture_output=True,
        )
        if result.returncode:
            raise ValueError(f"Link local não existe na revisão publicada: {relative}")
        if hashlib.sha256(result.stdout).hexdigest() != digest(target):
            raise ValueError(f"Link local tem alteração não commitada: {relative}")
        indexed = subprocess.run(
            ["git", "cat-file", "blob", f":{relative}"], cwd=root, capture_output=True
        )
        if indexed.returncode or hashlib.sha256(indexed.stdout).hexdigest() != digest(target):
            raise ValueError(f"Link local tem conteúdo divergente no stage: {relative}")
    return revision


def prepare(root: Path = ROOT) -> tuple[str, dict]:
    from markdown_it import MarkdownIt

    source = root / SOURCE
    revision = subprocess.check_output(
        ["git", "log", "-1", "--format=%H", "--", str(SOURCE)], cwd=root, text=True
    ).strip()
    markdown = MarkdownIt("commonmark", {"html": True}).enable("table")
    tokens = markdown.parse(source.read_text(encoding="utf-8-sig"))
    occurrences: dict[str, int] = {}
    for index, token in enumerate(tokens):
        if token.type == "heading_open":
            name = slug(tokens[index + 1].content)
            count = occurrences.get(name, 0)
            token.attrSet("id", name if count == 0 else f"{name}-{count}")
            occurrences[name] = count + 1
        if token.type == "fence" and token.info == "mermaid":
            # Preserve the complete original graph definition; no external renderer.
            token.content = "Diagrama Mermaid (definição integral):\n" + token.content
    parser = DocumentHTML(root, source, revision)
    parser.feed(markdown.renderer.render(tokens, markdown.options, {}))
    missing = parser.fragments - parser.anchors
    if missing:
        raise ValueError(f"Âncoras internas inexistentes: {sorted(missing)}")
    inputs = {source, root / "requirements-docs.txt", Path(__file__).resolve()}
    inputs.update(parser.assets)
    inputs.update((root / FONTS).glob("*"))
    inputs.update(parser.local_links)
    # Ignore publication-only commits when selecting a snapshot, avoiding a SHA
    # cycle between the PDF and the commit that adds the PDF and its manifest.
    repository_revision = select_snapshot(root, inputs, parser.local_links)
    body = "".join(parser.parts).replace(
        f"{REPOSITORY}/-/blob/{revision}/", f"{REPOSITORY}/-/blob/{repository_revision}/"
    )
    packages = {}
    for requirement in (root / "requirements-docs.txt").read_text().splitlines():
        if not requirement or requirement.startswith("#"):
            continue
        name, version = requirement.split("==")
        actual = importlib.metadata.version(name)
        if actual != version:
            raise ValueError(f"Dependência {name}: esperada {version}, instalada {actual}")
        packages[name] = actual
    provenance = {
        "schema_version": 1,
        "source": SOURCE.as_posix(),
        "source_revision": revision,
        "repository_revision": repository_revision,
        "scope": "Conteúdo integral de docs/projeto.md; links não expandem outros documentos.",
        "mermaid": "Definições integrais como código; imagens existentes preservadas.",
        "inputs": {p.relative_to(root).as_posix(): digest(p) for p in sorted(inputs)},
        "packages": packages,
    }
    note = (
        '<div class="provenance"><strong>Exportação integral da documentação principal</strong>'
        f"<br>Fonte: docs/projeto.md | SHA-256: {digest(source)}"
        f"<br>Última edição commitada da fonte: {revision}"
        f"<br>Snapshot dos links locais: {repository_revision}"
        "<br>Links locais apontam para o snapshot indicado no GitLab. "
        "Diagramas Mermaid permanecem como definição textual integral. "
        "As limitações e propostas do documento original foram preservadas.</div>"
    )
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        "<title>Governança e Integração de Dados da Central de Pesquisas</title>"
        f"<style>{STYLE}</style></head><body>{note}{body}</body></html>",
        provenance,
    )


def check(root: Path, expected: dict) -> None:
    pdf, manifest = root / OUTPUT, root / MANIFEST
    recorded = json.loads(manifest.read_text(encoding="utf-8"))
    if any(recorded.get(key) != value for key, value in expected.items()):
        raise ValueError("PDF desatualizado: fonte, imagens, exportador ou dependências mudaram")
    if recorded.get("pdf_sha256") != digest(pdf):
        raise ValueError("Hash do PDF difere do manifesto")
    from pypdf import PdfReader

    reader = PdfReader(pdf)
    if len(reader.pages) != recorded.get("pages") or not reader.pages:
        raise ValueError("Contagem de páginas diverge do manifesto")


def main() -> int:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("--check", action="store_true", help="Validar sem escrever arquivos")
    args = arguments.parse_args()
    try:
        document, provenance = prepare()
        if args.check:
            check(ROOT, provenance)
            print("PDF e manifesto atuais; arquivos de origem e âncoras conferidos.")
            return 0
        from pypdf import PdfReader
        from weasyprint import HTML, default_url_fetcher

        def local_fetcher(url):
            parsed = urlsplit(url)
            path = Path(unquote(parsed.path)).resolve()
            if parsed.scheme != "file" or not path.is_relative_to(ROOT):
                raise ValueError(f"Recurso externo recusado: {url}")
            return default_url_fetcher(url)

        # Resource failures must block publication, rather than yield a partial PDF.
        failures = []

        class CaptureErrors(logging.Handler):
            def emit(self, record):
                if record.levelno >= logging.ERROR:
                    failures.append(record.getMessage())

        handler = CaptureErrors()
        logging.getLogger("weasyprint").addHandler(handler)
        try:
            payload = HTML(
                string=document,
                base_url=(ROOT / OUTPUT.parent).as_uri() + "/",
                url_fetcher=local_fetcher,
            ).write_pdf()
        finally:
            logging.getLogger("weasyprint").removeHandler(handler)
        if failures:
            raise ValueError(f"Falhas na renderização: {failures}")
        pdf = ROOT / OUTPUT
        pdf.parent.mkdir(parents=True, exist_ok=True)
        temporary = pdf.with_suffix(".pdf.tmp")
        temporary.write_bytes(payload)
        provenance["pages"] = len(PdfReader(temporary).pages)
        provenance["pdf_sha256"] = digest(temporary)
        temporary.replace(pdf)
        (ROOT / MANIFEST).write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{OUTPUT}: {provenance['pages']} páginas; manifesto: {MANIFEST}")
        return 0
    except (OSError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
