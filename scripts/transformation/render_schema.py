#!/usr/bin/env python3
"""Renderiza o catálogo de campos; --check falha se a documentação divergir."""

import argparse
from pathlib import Path

from etl.transformation.schema import SCHEMAS, TECHNICAL_COLUMNS


def render():
    lines = [
        "# Catálogo de campos da ingestão tratada",
        "",
        "MG-02/MG-11. Contrato v1.0. Gerado de `schema.py`; valide com",
        "`PYTHONPATH=src python scripts/transformation/render_schema.py --check`.",
        "",
        "A coluna Regra remete aos tipos e aos critérios em [schema-transformacao.md](schema-transformacao.md).",
        "Os testes e códigos de rejeição estão na [matriz de validação](matriz-transformacao.md).",
        "",
    ]
    for source, fields in SCHEMAS.items():
        lines.extend(
            [
                f"## {source}",
                "",
                "| Origem | Destino | Tipo DuckDB | Ausência | Regra |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for f in fields:
            null = "rejeitar" if f.required else "[]" if f.kind == "list" else "null"
            rule = f.kind + (("; sentinelas: " + ", ".join(f.sentinels)) if f.sentinels else "")
            lines.append(
                f"| `{f.origin}` | `ingestao_{source}.{f.name}` | `{f.duckdb_type}` | {null} | {rule} |"
            )
        lines.append("")
    lines.extend(["## Metadados comuns", "", "| Campo | Tipo |", "| --- | --- |"])
    lines.extend(f"| `{name}` | `{kind}` |" for name, kind in TECHNICAL_COLUMNS.items())
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true", help="Atualiza o catálogo versionado")
    args = parser.parse_args()
    if args.check and args.write:
        parser.error("--check e --write são mutuamente exclusivos")
    document = render()
    path = Path(__file__).resolve().parents[2] / "docs/catalogo-transformacao.md"
    if args.check:
        if path.read_text(encoding="utf-8") != document:
            parser.exit(1, "Catálogo desatualizado.\n")
    elif args.write:
        path.write_text(document, encoding="utf-8")
        print(f"{path} atualizado")
    else:
        print(document, end="")


if __name__ == "__main__":
    main()
