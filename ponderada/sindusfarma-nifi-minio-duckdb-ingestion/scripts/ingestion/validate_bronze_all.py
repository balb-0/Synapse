from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import duckdb

from datasets_config import DATASETS, DatasetSpec, schema_fields
from duckdb_s3 import config_from_env, configure_s3


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def bronze_path(config: dict[str, str], dataset: DatasetSpec) -> str:
    return f"s3://{config['bucket']}/bronze/{dataset.name}/*/{dataset.name}.parquet"


def validate_dataset(
    con: duckdb.DuckDBPyConnection,
    config: dict[str, str],
    dataset: DatasetSpec,
) -> dict[str, Any]:
    path = bronze_path(config, dataset)
    row_count = con.execute("select count(*) from read_parquet(?)", [path]).fetchone()[0]
    columns = con.execute("describe select * from read_parquet(?)", [path]).fetchall()
    column_names = [row[0] for row in columns]
    expected_columns = schema_fields(dataset)

    key_columns = ", ".join(quote_identifier(column) for column in dataset.key_columns)
    duplicate_count = con.execute(
        f"""
        select count(*)
        from (
            select {key_columns}
            from read_parquet(?)
            group by {key_columns}
            having count(*) > 1
        )
        """,
        [path],
    ).fetchone()[0]
    null_checks = " or ".join(
        f"{quote_identifier(column)} is null or {quote_identifier(column)} = ''"
        for column in dataset.key_columns
    )
    null_or_empty_key_count = con.execute(
        f"select count(*) from read_parquet(?) where {null_checks}",
        [path],
    ).fetchone()[0]

    parquet_meta = con.execute(
        """
        select
            count(distinct file_name) as parquet_files,
            coalesce(sum(total_compressed_size), 0) as compressed_column_bytes
        from parquet_metadata(?)
        """,
        [path],
    ).fetchone()

    return {
        "dataset": dataset.name,
        "bronze_path": path,
        "destination_row_count": row_count,
        "expected_source_row_count": dataset.expected_rows,
        "row_count_matches_source": row_count == dataset.expected_rows,
        "schema_matches_expected": column_names == expected_columns,
        "duplicate_key_count": duplicate_count,
        "null_or_empty_key_count": null_or_empty_key_count,
        "parquet_files": parquet_meta[0],
        "compressed_column_bytes": parquet_meta[1],
        "columns": [
            {"name": name, "type": data_type, "nullable": nullable}
            for name, data_type, nullable, *_ in columns
        ],
    }


def validate_all(config: dict[str, str]) -> dict[str, Any]:
    con = duckdb.connect()
    configure_s3(con, config)
    datasets = [validate_dataset(con, config, dataset) for dataset in DATASETS]
    return {
        "bucket": config["bucket"],
        "dataset_count": len(datasets),
        "total_destination_rows": sum(item["destination_row_count"] for item in datasets),
        "all_row_counts_match": all(item["row_count_matches_source"] for item in datasets),
        "all_schemas_match": all(item["schema_matches_expected"] for item in datasets),
        "datasets": datasets,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Valida os Parquets bronze no MinIO usando DuckDB."
    )
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    args = parser.parse_args()
    result = validate_all(config_from_env(args.env_file))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
