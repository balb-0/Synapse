"""Flow de ingestão orquestrado (OV-02).

Sequência de um objeto: verificação de idempotência -> extração -> transformação
-> carga -> reconciliação e confirmação. Cada etapa é uma tarefa do Prefect; a
falha de uma interrompe as dependentes (o Prefect não executa a jusante). O
gatilho normal é o evento `s3:ObjectCreated` do MinIO (adaptador externo chama
`ingest_object`); a execução manual usa os mesmos parâmetros.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone

from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from etl.extraction import (
    ClientesExtractor,
    EmpresasExtractor,
    MinioObjectReader,
    ObjectReference,
    PesquisasExtractor,
    QuestoesExtractor,
    RespondentesExtractor,
    RespostasExtractor,
    load_extraction_settings,
)
from etl.transformation.consistency import RELATIONS
from etl.transformation.pipeline import transform_batch
from etl.transformation.schema import KEYS
from etl.transformation.consistency import ReferenceData
from etl.load import DuckDbLoadRepository

EXTRACTORS = {
    "empresas": EmpresasExtractor,
    "pesquisas": PesquisasExtractor,
    "clientes": ClientesExtractor,
    "questoes": QuestoesExtractor,
    "respondentes": RespondentesExtractor,
    "respostas": RespostasExtractor,
}


def _minio_client(settings):
    from urllib.parse import urlsplit

    from minio import Minio

    # A config valida um endpoint com scheme (http/https); o cliente MinIO quer
    # host:port puro. O TLS é derivado do scheme.
    parsed = urlsplit(settings.minio_endpoint)
    host = parsed.netloc or parsed.path
    return Minio(
        host,
        access_key=settings.minio_access_key.get_secret_value(),
        secret_key=settings.minio_secret_key.get_secret_value(),
        secure=parsed.scheme == "https",
    )


def _object_checksum(reader: MinioObjectReader, reference: ObjectReference) -> str:
    digest = hashlib.sha256()
    with reader.open(reference) as stream:
        for chunk in iter(lambda: stream.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _build_references(repo: DuckDbLoadRepository, source: str) -> ReferenceData:
    """Monta as referências dos pais a partir do que já foi carregado no DuckDB."""
    sources: dict[str, list[dict]] = {}
    for parent, _fields in RELATIONS[source]:
        keys = KEYS[parent]
        cols = ", ".join(f'"{k}"' for k in keys)
        rows = repo._conn.execute(f'SELECT {cols} FROM "{parent}"').fetchall()
        sources[parent] = [dict(zip(keys, [str(v) for v in row])) for row in rows]
    return ReferenceData(sources)


@task(retries=2, retry_delay_seconds=1, cache_policy=NO_CACHE)
def extract(reader, reference, source: str, run_id: str) -> list:
    """Lê o objeto do MinIO e materializa os lotes no contrato comum."""
    logger = get_run_logger()
    extractor = EXTRACTORS[source](object_reader=reader, object_reference=reference)
    batches = list(extractor.read(run_id=run_id))
    logger.info("extract concluído: %d lote(s) de '%s'", len(batches), source)
    return batches


@task(cache_policy=NO_CACHE)
def transform(batches: list, source: str, references, previous: dict) -> list:
    """Transforma cada lote; acumula o offset absoluto entre lotes."""
    logger = get_run_logger()
    ingested_at = datetime.now(timezone.utc)
    results, offset = [], 0
    for batch in batches:
        result = transform_batch(
            batch,
            references=references,
            previous=previous,
            source_offset=offset,
            ingested_at=ingested_at,
        )
        offset += len(batch.records)
        results.append((result, batch.metadata))
    total = sum(r.metrics["accepted_count"] for r, _ in results)
    logger.info("transform concluído: %d registro(s) aceito(s)", total)
    return results


@task(cache_policy=NO_CACHE)
def load(db_path: str, results: list) -> list:
    """Grava aceitos e rejeitados no DuckDB e reconcilia as contagens."""
    logger = get_run_logger()
    with DuckDbLoadRepository(db_path) as repo:
        reconciliations = []
        for result, metadata in results:
            outcome = repo.load_batch(result, metadata)
            reconciliations.append(outcome.as_dict())
            logger.info("load: %s", outcome.as_dict())
        return reconciliations


@flow(name="ingest-object")
def ingest_object(
    source: str,
    bucket: str,
    key: str,
    *,
    version_id: str | None = None,
    event_id: str | None = None,
    db_path: str | None = None,
) -> dict:
    """Ingestão idempotente de um objeto do MinIO na camada tratada (DuckDB)."""
    logger = get_run_logger()
    if source not in EXTRACTORS:
        raise ValueError(f"fonte desconhecida: {source!r}")
    db_path = db_path or os.environ.get("DUCKDB_PATH", "warehouse.duckdb")

    settings = load_extraction_settings()
    reader = MinioObjectReader(_minio_client(settings))
    reference = ObjectReference(bucket=bucket, key=key, version_id=version_id)

    checksum = _object_checksum(reader, reference)
    with DuckDbLoadRepository(db_path) as repo:
        if repo.object_already_loaded(checksum):
            logger.info("objeto %s já concluído (hash %s) — ignorado", key, checksum[:12])
            return {"status": "ignored", "source": source, "source_checksum": checksum}
        references = _build_references(repo, source)
        previous = repo.loaded_identities(source)

    batches = extract(reader, reference, source, run_id=event_id or checksum[:16])
    results = transform(batches, source, references, previous)
    reconciliations = load(db_path, results)

    with DuckDbLoadRepository(db_path) as repo:
        repo.mark_object_loaded(source, checksum, event_id or checksum[:16])

    loaded = sum(r["loaded"] for r in reconciliations)
    logger.info("ingestão concluída: %d registro(s) carregado(s) de '%s'", loaded, source)
    return {
        "status": "loaded",
        "source": source,
        "source_checksum": checksum,
        "reconciliation": reconciliations,
    }
