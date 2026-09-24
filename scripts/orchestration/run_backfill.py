"""Executa o flow de backfill com parâmetros explícitos (OV-03).

    python scripts/orchestration/run_backfill.py --sources empresas [--reprocess]

Semeia os fixtures das fontes pedidas no MinIO e roda o flow `backfill`. Os
parâmetros (fontes, prefixo, reprocesso) ficam registrados no histórico do run.
"""

import argparse
import os
from pathlib import Path
from urllib.parse import urlsplit

from minio import Minio

from etl.orchestration import backfill, configure_json_logging


def _client() -> Minio:
    parsed = urlsplit(os.environ["ETL_MINIO_ENDPOINT"])
    return Minio(
        parsed.netloc or parsed.path,
        access_key=os.environ["ETL_MINIO_ACCESS_KEY"],
        secret_key=os.environ["ETL_MINIO_SECRET_KEY"],
        secure=parsed.scheme == "https",
    )


def _seed(sources: list[str], bucket: str, prefix: str) -> None:
    client = _client()
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    fixtures = Path(__file__).parent / "fixtures"
    for source in sources:
        fixture = fixtures / f"{source}.csv"
        if fixture.exists():
            client.fput_object(bucket, f"{prefix}/{source}.csv", str(fixture))
            print(f"[seed] {source}.csv")


def main() -> None:
    configure_json_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", nargs="+", default=["empresas"])
    ap.add_argument("--reprocess", action="store_true")
    args = ap.parse_args()

    bucket = os.environ["ETL_MINIO_BUCKET"]
    prefix = os.environ.get("ETL_MINIO_INPUT_PREFIX", "landing")
    _seed(args.sources, bucket, prefix)
    result = backfill(sources=args.sources, bucket=bucket, prefix=prefix, reprocess=args.reprocess)
    print("BACKFILL:", result)


if __name__ == "__main__":
    main()
