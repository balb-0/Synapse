#!/usr/bin/env python3
"""Executa os gates estruturais e semânticos do Data Model Canvas."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
JSON_CHECK = (
    "import json, pathlib, sys; json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))"
)


@dataclass(frozen=True)
class Gate:
    name: str
    command: tuple[str, ...]


def build_gates(
    python: str,
    dmc: Path,
    manifest: Path,
    project: Path,
    reexport: Path | None,
) -> list[Gate]:
    gates = [
        Gate("JSON canônico", (python, "-c", JSON_CHECK, str(dmc))),
        Gate(
            "Contrato semântico do DMC",
            (python, "scripts/dmc/validate_dmc.py", str(dmc)),
        ),
        Gate(
            "Rastreabilidade",
            (
                python,
                "scripts/traceability/validate_traceability.py",
                "--manifest",
                str(manifest),
                "--dmc",
                str(dmc),
                "--project",
                str(project),
            ),
        ),
        Gate(
            "Testes do DMC",
            (
                python,
                "-m",
                "unittest",
                "discover",
                "-s",
                "scripts/dmc",
                "-p",
                "test_*.py",
            ),
        ),
        Gate(
            "Testes de rastreabilidade",
            (
                python,
                "-m",
                "unittest",
                "discover",
                "-s",
                "scripts/traceability",
                "-p",
                "test_*.py",
            ),
        ),
    ]
    if reexport is not None:
        gates.extend(
            [
                Gate(
                    "JSON reexportado",
                    (python, "-c", JSON_CHECK, str(reexport)),
                ),
                Gate(
                    "Round-trip semântico",
                    (
                        python,
                        "scripts/dmc/validate_dmc.py",
                        str(reexport),
                        "--baseline",
                        str(dmc),
                    ),
                ),
            ]
        )
    return gates


def execute_gates(gates: Sequence[Gate]) -> int:
    for gate in gates:
        print(f"[gate] {gate.name}", flush=True)
        result = subprocess.run(gate.command, cwd=REPOSITORY_ROOT, check=False)
        if result.returncode != 0:
            print(f"[falha] {gate.name}", file=sys.stderr)
            return result.returncode
    print(f"[ok] {len(gates)} gates aprovados")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dmc", type=Path, default=Path("docs/dmc.json"))
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("scripts/traceability/manifest.json"),
    )
    parser.add_argument("--project", type=Path, default=Path("docs/projeto.md"))
    parser.add_argument(
        "--reexport",
        type=Path,
        help="JSON exportado em uma nova sessão da ferramenta oficial",
    )
    args = parser.parse_args()
    return execute_gates(
        build_gates(
            sys.executable,
            args.dmc,
            args.manifest,
            args.project,
            args.reexport,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
