from __future__ import annotations

import argparse
import csv
import json
import tempfile
from pathlib import Path
from typing import Any

from datasets_config import dataset_by_name
from profile_sources import read_csv_rows


def validate_header(path: Path, dataset_name: str) -> dict[str, Any]:
    dataset = dataset_by_name(dataset_name)
    header, rows = read_csv_rows(path)
    valid = tuple(header) == dataset.expected_source_header
    return {
        "dataset": dataset.name,
        "test_file": str(path),
        "status": "VALIDATION_FAILED" if not valid else "UNEXPECTED_SUCCESS",
        "detected_problem": "schema_header_mismatch" if not valid else None,
        "expected_header": list(dataset.expected_source_header),
        "observed_header": header,
        "observed_rows": len(rows),
    }


def create_invalid_csv(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.writer(target, delimiter=";")
        writer.writerow(["id_cliente", "coluna_inesperada"])
        writer.writerow(["1", "valor"])


def run_controlled_failure(dataset_name: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / f"{dataset_name}_schema_invalido.csv"
        create_invalid_csv(path)
        return validate_header(path, dataset_name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa falha controlada de schema.")
    parser.add_argument("--dataset", default="clientes")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = run_controlled_failure(args.dataset)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

