from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import duckdb

from datasets_config import DATASETS
from duckdb_s3 import config_from_env, configure_s3
from validate_bronze_all import bronze_path


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def quote_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def drop_existing_relation(con: duckdb.DuckDBPyConnection, schema: str, name: str) -> None:
    qualified_name = f"{quote_identifier(schema)}.{quote_identifier(name)}"
    view_exists = con.execute(
        """
        select count(*)
        from duckdb_views()
        where schema_name = ? and view_name = ?
        """,
        [schema, name],
    ).fetchone()[0]
    if view_exists:
        con.execute(f"drop view {qualified_name}")

    table_exists = con.execute(
        """
        select count(*)
        from duckdb_tables()
        where schema_name = ? and table_name = ?
        """,
        [schema, name],
    ).fetchone()[0]
    if table_exists:
        con.execute(f"drop table {qualified_name}")


def build_warehouse(config: dict[str, str], database_path: Path) -> dict[str, Any]:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(database_path))
    configure_s3(con, config)
    con.execute("create schema if not exists bronze")

    tables = []
    for dataset in DATASETS:
        table_name = f"bronze.{quote_identifier(dataset.name)}"
        path = quote_literal(bronze_path(config, dataset))
        drop_existing_relation(con, "bronze", dataset.name)
        con.execute(
            f"create or replace table {table_name} as select * from read_parquet({path})"
        )
        rows = con.execute(f"select count(*) from {table_name}").fetchone()[0]
        tables.append(
            {
                "table": f"bronze.{dataset.name}",
                "dataset": dataset.name,
                "rows": rows,
                "expected_rows": dataset.expected_rows,
                "matches_expected": rows == dataset.expected_rows,
            }
        )

    return {
        "duckdb_database": str(database_path),
        "schema": "bronze",
        "tables_created": len(tables),
        "all_tables_match_expected_rows": all(item["matches_expected"] for item in tables),
        "tables": tables,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materializa tabelas bronze em um DuckDB local a partir dos Parquets do MinIO."
    )
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("local/warehouse/sindusfarma.duckdb"),
    )
    args = parser.parse_args()

    result = build_warehouse(config_from_env(args.env_file), args.database)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
