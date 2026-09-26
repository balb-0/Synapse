"""Semeia um objeto no MinIO e executa o flow de ingestão orquestrado.

Uso (dentro do runner):
    python scripts/orchestration/run_ingest.py --source empresas

Faz o upload do fixture para a área de entrada do MinIO e chama `ingest_object`.
Rodar duas vezes demonstra a idempotência (a 2ª execução é ignorada).
"""

import argparse
import os
from pathlib import Path
from urllib.parse import urlsplit

from minio import Minio

from etl.orchestration import configure_json_logging, ingest_object


def _upload(local: Path, bucket: str, key: str) -> None:
    parsed = urlsplit(os.environ["ETL_MINIO_ENDPOINT"])
    client = Minio(
        parsed.netloc or parsed.path,
        access_key=os.environ["ETL_MINIO_ACCESS_KEY"],
        secret_key=os.environ["ETL_MINIO_SECRET_KEY"],
        secure=parsed.scheme == "https",
    )
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    client.fput_object(bucket, key, str(local))
    print(f"[seed] {local.name} -> s3://{bucket}/{key}")


def main() -> None:
    configure_json_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="empresas")
    ap.add_argument("--key")
    ap.add_argument("--fixture")
    args = ap.parse_args()

    bucket = os.environ["ETL_MINIO_BUCKET"]
    prefix = os.environ.get("ETL_MINIO_INPUT_PREFIX", "landing")
    key = args.key or f"{prefix}/{args.source}.csv"
    fixture = (
        Path(args.fixture)
        if args.fixture
        else (Path(__file__).parent / "fixtures" / f"{args.source}.csv")
    )

    _upload(fixture, bucket, key)
    result = ingest_object(source=args.source, bucket=bucket, key=key)
    print("RESULTADO:", result)


if __name__ == "__main__":
    main()
