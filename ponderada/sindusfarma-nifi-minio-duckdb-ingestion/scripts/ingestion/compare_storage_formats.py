from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import duckdb

from datasets_config import DATASETS, default_source_dir
from validate_bronze_all import bronze_path
from duckdb_s3 import config_from_env, configure_s3


def timed_count(con: duckdb.DuckDBPyConnection, query: str, parameter: str) -> tuple[int, float]:
    started = time.perf_counter()
    rows = con.execute(query, [parameter]).fetchone()[0]
    elapsed_ms = (time.perf_counter() - started) * 1000
    return rows, elapsed_ms


def compare(config: dict[str, str], source_dir: Path) -> dict[str, Any]:
    con = duckdb.connect()
    configure_s3(con, config)
    results = []
    for dataset in DATASETS:
        source_path = source_dir / dataset.file_name
        csv_rows, csv_ms = timed_count(
            con,
            "select count(*) from read_csv(?, delim=';', header=true, all_varchar=true)",
            str(source_path),
        )
        parquet_rows, parquet_ms = timed_count(
            con,
            "select count(*) from read_parquet(?)",
            bronze_path(config, dataset),
        )
        compressed_bytes = con.execute(
            "select coalesce(sum(total_compressed_size), 0) from parquet_metadata(?)",
            [bronze_path(config, dataset)],
        ).fetchone()[0]
        results.append(
            {
                "dataset": dataset.name,
                "csv_rows": csv_rows,
                "parquet_rows": parquet_rows,
                "csv_size_bytes": source_path.stat().st_size,
                "parquet_compressed_column_bytes": compressed_bytes,
                "csv_read_ms": round(csv_ms, 3),
                "parquet_read_ms": round(parquet_ms, 3),
            }
        )
    return {"datasets": results}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compara leitura CSV local vs Parquet no MinIO.")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--source-dir", type=Path, default=default_source_dir())
    args = parser.parse_args()
    result = compare(config_from_env(args.env_file), args.source_dir.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
