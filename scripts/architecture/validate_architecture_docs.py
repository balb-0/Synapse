"""Valida os artefatos arquiteturais contra links, diagramas e código reais."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ARCHITECTURE_DOCUMENTS = (
    Path("docs/visao-negocio-etl.md"),
    Path("docs/visao-informacao-etl.md"),
    Path("docs/visao-computacional-etl.md"),
    Path("docs/visao-engenharia-etl.md"),
    Path("docs/visao-tecnologia-etl.md"),
)

DIAGRAMS = {
    Path("docs/assets/uml/casos-de-uso-etl.plantuml"): (
        "Publicador da fonte",
        "Operador de dados",
        "MinIO",
        "Prefect",
        "Elastic Stack",
        "<<planejado>>",
    ),
    Path("docs/assets/uml/componentes-etl.plantuml"): (
        "MinIO",
        "Prefect",
        "DuckDB",
        "Elastic Stack",
        "Logstash",
        "Elasticsearch",
        "Kibana",
        "<<planejado>>",
    ),
    Path("docs/assets/uml/sequencia-ingestao-etl.plantuml"): (
        "Operador de dados",
        "Prefect",
        "MinioObjectReader",
        "DuckDbLoadRepository",
        "DuckDB",
        "Logstash",
        "checkpoint",
        "UnbalancedLoadError",
        "mark_object_loaded",
    ),
}

LINK_DOCUMENTS = ARCHITECTURE_DOCUMENTS + (
    Path("docs/projeto.md"),
    Path("docs/adrs/index.md"),
)

CODE_SYMBOLS = (
    "MinioObjectReader",
    "DuckDbLoadRepository",
    "ingest_object",
    "backfill",
    "transform_batch",
    "transform_object",
    "UnbalancedLoadError",
)

MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))", re.MULTILINE)
HTML_LINK_RE = re.compile(r"(?:href|src)=[\"']([^\"']+)[\"']", re.IGNORECASE)
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
EXPLICIT_ANCHOR_RE = re.compile(r"<a\s+(?:name|id)=[\"']([^\"']+)[\"']", re.IGNORECASE)


def read_text(root: Path, relative_path: Path) -> str:
    return (root / relative_path).read_text(encoding="utf-8")


def markdown_anchors(text: str) -> set[str]:
    """Retorna âncoras no formato usado pelo GitLab para títulos Markdown."""
    anchors = set(EXPLICIT_ANCHOR_RE.findall(text))
    occurrences: dict[str, int] = {}
    for heading in HEADING_RE.findall(text):
        clean = re.sub(r"<[^>]+>", "", heading)
        clean = re.sub(r"[`*_~]", "", clean).strip().lower()
        clean = re.sub(r"[^\w\- ]", "", clean, flags=re.UNICODE)
        base = re.sub(r"\s", "-", clean).strip("-")
        duplicate = occurrences.get(base, 0)
        occurrences[base] = duplicate + 1
        anchors.add(base if duplicate == 0 else f"{base}-{duplicate}")
    return anchors


def iter_local_links(text: str):
    candidates = [first or second for first, second in MARKDOWN_LINK_RE.findall(text)]
    candidates.extend(HTML_LINK_RE.findall(text))
    for candidate in candidates:
        candidate = candidate.strip()
        parsed = urlsplit(candidate)
        if parsed.scheme or candidate.startswith("//"):
            continue
        yield unquote(parsed.path), unquote(parsed.fragment), candidate


def validate_links(root: Path, documents=LINK_DOCUMENTS) -> list[str]:
    errors: list[str] = []
    for document in documents:
        source = root / document
        if not source.is_file():
            errors.append(f"arquivo obrigatório ausente: {document.as_posix()}")
            continue
        text = source.read_text(encoding="utf-8")
        for path_part, fragment, original in iter_local_links(text):
            target = source if not path_part else (source.parent / path_part).resolve()
            if not target.exists():
                errors.append(f"{document.as_posix()}: link inexistente: {original}")
                continue
            if fragment and target.is_file() and target.suffix.lower() in {".md", ".markdown"}:
                anchors = markdown_anchors(target.read_text(encoding="utf-8"))
                if fragment not in anchors:
                    errors.append(
                        f"{document.as_posix()}: âncora inexistente em {original}: {fragment}"
                    )
    return errors


def validate_diagrams(root: Path) -> list[str]:
    errors: list[str] = []
    project = read_text(root, Path("docs/projeto.md"))
    for diagram, required_terms in DIAGRAMS.items():
        path = root / diagram
        if not path.is_file():
            errors.append(f"diagrama obrigatório ausente: {diagram.as_posix()}")
            continue
        text = path.read_text(encoding="utf-8")
        if "@startuml" not in text or "@enduml" not in text:
            errors.append(f"{diagram.as_posix()}: delimitadores PlantUML ausentes")
        for term in required_terms:
            if term not in text:
                errors.append(f"{diagram.as_posix()}: referência obrigatória ausente: {term}")
        if diagram.name not in project:
            errors.append(f"docs/projeto.md: diagrama não referenciado: {diagram.name}")
    return errors


def validate_code_coherence(root: Path) -> list[str]:
    errors: list[str] = []
    technology = read_text(root, Path("docs/visao-tecnologia-etl.md"))
    engineering = read_text(root, Path("docs/visao-engenharia-etl.md"))
    requirements = read_text(root, Path("requirements.txt"))
    dockerfile = read_text(root, Path("Dockerfile"))
    compose = read_text(root, Path("docker-compose.yml"))

    requirements_specs = [
        line.strip()
        for line in requirements.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    for specification in requirements_specs:
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)(.*)", specification)
        package, version = match.groups() if match else (specification, "")
        if package not in technology or (version and version not in technology):
            errors.append(
                f"docs/visao-tecnologia-etl.md: versão ausente ou divergente: {specification}"
            )

    image_match = re.search(r"^FROM\s+(\S+)", dockerfile, re.MULTILINE)
    if not image_match or image_match.group(1) not in technology:
        errors.append("docs/visao-tecnologia-etl.md: imagem do Dockerfile divergente")

    for port in ("9000:9000", "9001:9001"):
        if f'"{port}"' not in compose:
            errors.append(f"docker-compose.yml: porta obrigatória ausente: {port}")
        if port.split(":")[0] not in engineering:
            errors.append(f"docs/visao-engenharia-etl.md: porta não documentada: {port}")

    python_sources = "\n".join(
        path.read_text(encoding="utf-8") for path in (root / "src").rglob("*.py")
    )
    diagrams = "\n".join(read_text(root, path) for path in DIAGRAMS)
    for symbol in CODE_SYMBOLS:
        if symbol not in python_sources:
            errors.append(f"código: símbolo citado pela arquitetura não existe: {symbol}")
        if symbol not in diagrams:
            errors.append(f"diagramas: símbolo executável não referenciado: {symbol}")
    return errors


def validate_repository(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    errors.extend(validate_links(root))
    errors.extend(validate_diagrams(root))
    errors.extend(validate_code_coherence(root))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="raiz do repositório")
    args = parser.parse_args(argv)
    errors = validate_repository(args.root)
    if errors:
        print("Validação arquitetural reprovada:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "Validação arquitetural aprovada: 5 visões, 3 diagramas, links, âncoras, "
        "versões, portas e símbolos coerentes."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
