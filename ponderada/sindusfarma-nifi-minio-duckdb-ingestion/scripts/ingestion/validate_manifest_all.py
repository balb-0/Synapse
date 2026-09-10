from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import duckdb

from datasets_config import DATASETS
from duckdb_s3 import config_from_env, configure_s3


def validate_manifest(config: dict[str, str]) -> dict[str, Any]:
    con = duckdb.connect()
    configure_s3(con, config)

    events_path = f"s3://{config['bucket']}/manifests/events/dataset=*/status=*/*.json"
    markers_path = f"s3://{config['bucket']}/manifests/success_hashes/*/*.json"

    status_rows = con.execute(
        """
        select dataset, status, count(*) as events
        from read_json_auto(?, union_by_name = true)
        group by dataset, status
        order by dataset, status
        """,
        [events_path],
    ).fetchall()
    marker_rows = con.execute(
        """
        select dataset, count(*) as markers
        from read_json_auto(?, union_by_name = true)
        where status = 'SUCCESS'
        group by dataset
        order by dataset
        """,
        [markers_path],
    ).fetchall()
    success_marker_hashes = con.execute(
        """
        select dataset, file_hash, destination_path
        from read_json_auto(?, union_by_name = true)
        where status = 'SUCCESS'
        order by dataset
        """,
        [markers_path],
    ).fetchall()

    status_counts = [
        {"dataset": dataset, "status": status, "events": events}
        for dataset, status, events in status_rows
    ]
    markers = [{"dataset": dataset, "markers": markers} for dataset, markers in marker_rows]
    expected = {dataset.name for dataset in DATASETS}
    success_datasets = {
        item["dataset"]
        for item in status_counts
        if item["status"] == "SUCCESS" and item["events"] >= 1
    }
    skipped_datasets = {
        item["dataset"]
        for item in status_counts
        if item["status"] == "SKIPPED_ALREADY_INGESTED" and item["events"] >= 1
    }
    marker_datasets = {item["dataset"] for item in markers if item["markers"] >= 1}

    return {
        "events_path": events_path,
        "success_markers_path": markers_path,
        "status_counts": status_counts,
        "success_markers": markers,
        "success_marker_hashes": [
            {
                "dataset": dataset,
                "file_hash": file_hash,
                "destination_path": destination_path,
            }
            for dataset, file_hash, destination_path in success_marker_hashes
        ],
        "all_datasets_have_success": expected.issubset(success_datasets),
        "all_datasets_have_skip_after_rerun": expected.issubset(skipped_datasets),
        "all_datasets_have_success_marker": expected.issubset(marker_datasets),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida manifests e markers de idempotencia.")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    args = parser.parse_args()
    print(json.dumps(validate_manifest(config_from_env(args.env_file)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
