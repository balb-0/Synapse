"""Disparo da ingestão pela chegada de objeto na área de entrada.

Dois modos, mesmo efeito (chamar ``ingest_object`` uma vez por objeto novo;
objeto repetido retorna ``status: ignored`` por checksum SHA-256, sem nova
carga):

- webhook (padrão quando ``--webhook-port`` é informado): servidor HTTP que
  recebe a notificação ``s3:ObjectCreated`` do MinIO e ingere o objeto
  notificado. O servidor escuta em todas as interfaces sem autenticação
  (adequado ao Compose local; não exponha essa porta fora dele). Configure
  no MinIO (exemplo):

      mc event add local/sindusfarma arn:minio:sqs::1:webhook --event put
      mc event add local/sindusfarma arn:minio:sqs::1:webhook \\
        --prefix landing/ --suffix .csv --event put

- polling: varredura do prefixo a cada ``--interval`` segundos, com estado
  das chaves já vistas em ``--state-file`` (sobrevive a reinícios).

A fonte é inferida do nome do arquivo (``landing/<fonte>.csv``); chaves fora
desse padrão são ignoradas com aviso. Uso:

    # webhook (recomendado no Compose: MinIO notifica, sem varredura):
    python scripts/orchestration/watch_landing.py --webhook-port 8001
    # polling (adequado quando o webhook não está configurado):
    python scripts/orchestration/watch_landing.py --interval 30
    # uma varredura e sai (útil em smoke/teste):
    python scripts/orchestration/watch_landing.py --once
"""

from __future__ import annotations

import argparse
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

SOURCES = ("empresas", "pesquisas", "clientes", "questoes", "respondentes", "respostas")


def _minio_client():
    from minio import Minio

    parsed = urlsplit(os.environ["ETL_MINIO_ENDPOINT"])
    return Minio(
        parsed.netloc or parsed.path,
        access_key=os.environ["ETL_MINIO_ACCESS_KEY"],
        secret_key=os.environ["ETL_MINIO_SECRET_KEY"],
        secure=parsed.scheme == "https",
    )


def infer_source(key: str, prefix: str) -> str | None:
    """Devolve a fonte para ``<prefix>/<fonte>.csv`` ou ``None``."""

    name = key[len(prefix) + 1 :] if key.startswith(prefix + "/") else key
    if not name.endswith(".csv") or "/" in name:
        return None
    stem = name[: -len(".csv")]
    return stem if stem in SOURCES else None


def ingest(bucket: str, key: str, source: str) -> dict:
    from etl.orchestration import ingest_object

    result = ingest_object(source=source, bucket=bucket, key=key)
    print(f"[watch] s3://{bucket}/{key} fonte={source} -> {result.get('status')}")
    return result


def _load_seen(state_file: Path) -> set[str]:
    if state_file.exists():
        try:
            return set(json.loads(state_file.read_text()))
        except (ValueError, OSError):
            return set()
    return set()


def _save_seen(state_file: Path, seen: set[str]) -> None:
    try:
        state_file.write_text(json.dumps(sorted(seen)))
    except OSError as exc:
        print(f"[watch] aviso: não foi possível gravar {state_file}: {exc}")


def poll_once(bucket: str, prefix: str, state_file: Path) -> list[dict]:
    """Uma varredura: ingere chaves novas, marca vistas, retorna resultados.

    Falha em uma chave não mata a varredura nem perde o progresso: registra,
    segue para a próxima e grava o estado ao final. A chave com falha tenta
    de novo na próxima varredura (a ingestão é idempotente).
    """

    client = _minio_client()
    seen = _load_seen(state_file)
    outcomes = []
    try:
        for obj in client.list_objects(bucket, prefix=prefix, recursive=True):
            key = obj.object_name
            if key in seen:
                continue
            source = infer_source(key, prefix)
            if source is None:
                print(f"[watch] ignorada (fora do padrão <fonte>.csv): {key}")
                seen.add(key)
                continue
            try:
                outcomes.append(ingest(bucket, key, source))
            except Exception as exc:  # noqa: BLE001 — uma chave não derruba o daemon
                print(f"[watch] falha ao ingerir {key}: {exc}")
            else:
                seen.add(key)
    finally:
        _save_seen(state_file, seen)
    return outcomes


def poll_loop(bucket: str, prefix: str, state_file: Path, interval: int) -> None:
    print(f"[watch] polling s3://{bucket}/{prefix}/ a cada {interval}s (Ctrl+C para parar)")
    while True:
        poll_once(bucket, prefix, state_file)
        time.sleep(interval)


def extract_keys(payload: dict) -> list[tuple[str, str]]:
    """Extrai ``(bucket, key)`` dos registros ``s3:ObjectCreated`` do MinIO."""

    pairs = []
    records = payload.get("Records", []) if isinstance(payload, dict) else []
    for record in records:
        event = str(record.get("eventName", ""))
        if not event.startswith("s3:ObjectCreated"):
            continue
        s3 = record.get("s3", {})
        pairs.append(
            (
                s3.get("bucket", {}).get("name", ""),
                s3.get("object", {}).get("key", ""),
            )
        )
    return [(b, k) for b, k in pairs if b and k]


def serve_webhook(port: int, bucket_default: str, prefix: str) -> None:
    parent = {"bucket": bucket_default, "prefix": prefix}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # silencia o log padrão por request
            pass

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                self.send_response(400)
                self.end_headers()
                return
            pairs = extract_keys(payload)
            for bucket, key in pairs:
                source = infer_source(key, parent["prefix"])
                if source is None:
                    print(f"[watch] notificação ignorada (fora do padrão): {key}")
                    continue
                try:
                    ingest(bucket, key, source)
                except Exception as exc:  # noqa: BLE001 — webhook não pode cair
                    print(f"[watch] falha ao ingerir {key}: {exc}")
            self.send_response(200)
            self.end_headers()

    print(f"[watch] webhook ouvindo na porta {port} (POST /)")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket", default=os.environ.get("ETL_MINIO_BUCKET", "sindusfarma"))
    ap.add_argument("--prefix", default=os.environ.get("ETL_MINIO_INPUT_PREFIX", "landing"))
    ap.add_argument("--interval", type=int, default=30)
    ap.add_argument("--once", action="store_true", help="uma varredura e sai")
    ap.add_argument("--webhook-port", type=int, default=None)
    ap.add_argument("--state-file", default=".watch_landing_seen.json")
    args = ap.parse_args()

    if args.webhook_port is not None:
        serve_webhook(args.webhook_port, args.bucket, args.prefix)
    elif args.once:
        poll_once(args.bucket, args.prefix, Path(args.state_file))
    else:
        poll_loop(args.bucket, args.prefix, Path(args.state_file), args.interval)


if __name__ == "__main__":
    main()
