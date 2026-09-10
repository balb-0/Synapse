#!/usr/bin/env python3
"""Renderiza o contrato físico da carga; --check falha se o SQL divergir."""

import argparse
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.load.ddl import render_ddl  # noqa: E402


DDL_PATH = REPOSITORY_ROOT / "sql/duckdb/001_ingestao_tratada.sql"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compara o arquivo versionado com o contrato e falha se divergirem",
    )
    args = parser.parse_args()

    document = render_ddl()
    if args.check:
        if not DDL_PATH.exists():
            parser.exit(1, f"DDL_AUSENTE: {DDL_PATH} nao existe.\n")
        if DDL_PATH.read_text(encoding="utf-8") != document:
            parser.exit(1, "DDL_DESATUALIZADA: rode sem --check para regerar.\n")
        return

    DDL_PATH.parent.mkdir(parents=True, exist_ok=True)
    DDL_PATH.write_text(document, encoding="utf-8")
    print(f"{DDL_PATH.relative_to(REPOSITORY_ROOT)} atualizado")


if __name__ == "__main__":
    main()
