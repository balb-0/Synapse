from __future__ import annotations

import os
from pathlib import Path

import duckdb


def read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def required_value(values: dict[str, str], key: str) -> str:
    value = values.get(key)
    if not value:
        raise RuntimeError(f"Variavel obrigatoria ausente: {key}. Copie .env.example para .env.")
    return value


def config_from_env(env_path: Path) -> dict[str, str]:
    file_values = read_env_file(env_path)
    merged = {**file_values, **os.environ}
    return {
        "bucket": merged.get("MINIO_BUCKET", "sindusfarma-data"),
        "endpoint": f"localhost:{merged.get('MINIO_API_PORT', '19000')}",
        "access_key": required_value(merged, "MINIO_ROOT_USER"),
        "secret_key": required_value(merged, "MINIO_ROOT_PASSWORD"),
    }


def configure_s3(con: duckdb.DuckDBPyConnection, config: dict[str, str]) -> None:
    con.execute("LOAD httpfs")
    con.execute("SET s3_url_style='path'")
    con.execute("SET s3_use_ssl=false")
    con.execute("SET s3_endpoint=?", [config["endpoint"]])
    con.execute("SET s3_access_key_id=?", [config["access_key"]])
    con.execute("SET s3_secret_access_key=?", [config["secret_key"]])
