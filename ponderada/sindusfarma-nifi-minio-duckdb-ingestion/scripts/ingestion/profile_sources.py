from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from datasets_config import DATASETS, DatasetSpec, default_source_dir, schema_fields


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source, delimiter=";")
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError(f"CSV vazio: {path}") from exc
        return header, list(reader)


def key_stats(rows: list[list[str]], key_positions: list[int]) -> tuple[int, int]:
    values: list[tuple[str, ...]] = []
    empty = 0
    for row in rows:
        key = tuple(row[position].strip() if position < len(row) else "" for position in key_positions)
        if any(not value for value in key):
            empty += 1
        values.append(key)
    return len(values) - len(set(values)), empty


def profile_dataset(dataset: DatasetSpec, source_dir: Path) -> dict[str, Any]:
    path = source_dir / dataset.file_name
    fields = schema_fields(dataset)
    header, rows = read_csv_rows(path)
    positions = [fields.index(column) for column in dataset.key_columns]
    duplicate_keys, empty_keys = key_stats(rows, positions)

    return {
        "dataset": dataset.name,
        "source_file": str(path),
        "file_size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "source_row_count": len(rows),
        "expected_row_count": dataset.expected_rows,
        "row_count_matches_expected": len(rows) == dataset.expected_rows,
        "source_header": header,
        "expected_source_header": list(dataset.expected_source_header),
        "schema_matches_expected": tuple(header) == dataset.expected_source_header,
        "bronze_columns": fields,
        "key_columns": list(dataset.key_columns),
        "duplicate_key_count": duplicate_keys,
        "null_or_empty_key_count": empty_keys,
    }


def profile_all(source_dir: Path) -> dict[str, Any]:
    datasets = [profile_dataset(dataset, source_dir) for dataset in DATASETS]
    return {
        "source_dir": str(source_dir),
        "dataset_count": len(datasets),
        "total_source_rows": sum(item["source_row_count"] for item in datasets),
        "total_source_bytes": sum(item["file_size_bytes"] for item in datasets),
        "datasets": datasets,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Perfil dos CSVs reais Sindusfarma.")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=default_source_dir(),
        help="Diretorio local ignorado pelo Git com os CSVs reais. Padrao: local/input.",
    )
    args = parser.parse_args()
    print(json.dumps(profile_all(args.source_dir.resolve()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
