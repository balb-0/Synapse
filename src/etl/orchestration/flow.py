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
    ExtractionError,
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
from etl.load.config import load_duckdb_settings

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


def _connection_tuning() -> dict:
    """Parâmetros de conexão do DuckDB configurados por variável de ambiente.

    Independentes de ``db_path``: vêm das próprias variáveis de tuning
    (`ETL_DUCKDB_THREADS`, `ETL_DUCKDB_MEMORY_LIMIT`,
    `ETL_DUCKDB_WRITE_LOCK_TIMEOUT_SECONDS`), não da configuração de extração.
    """
    settings = load_duckdb_settings()
    return {
        "threads": settings.threads,
        "memory_limit": settings.memory_limit,
        "write_lock_timeout_seconds": settings.write_lock_timeout_seconds,
    }


def _build_references(repo: DuckDbLoadRepository, source: str) -> ReferenceData:
    """Monta as referências dos pais a partir do que já foi carregado no DuckDB."""
    sources: dict[str, list[dict]] = {}
    for parent, _fields in RELATIONS[source]:
        keys = KEYS[parent]
        cols = ", ".join(f'"{k}"' for k in keys)
        rows = repo._conn.execute(f'SELECT {cols} FROM "{parent}"').fetchall()
        sources[parent] = [dict(zip(keys, [str(v) for v in row])) for row in rows]
    return ReferenceData(sources)


def _should_retry(task, task_run, state) -> bool:
    """Repete só falha transitória inesperada; permanente ou já esgotada, não.

    A extração já reexecuta falhas transitórias internamente (RetryExecutor). No
    nível do Prefect só faz sentido repetir um erro inesperado; falha permanente
    (credencial/schema/objeto ausente) e limite de retry esgotado falham rápido.
    """
    try:
        state.result(raise_on_failure=True)
    except (ExtractionError, ValueError, KeyError):
        # Erros da extração já chegam terminais (transitório foi reexecutado
        # internamente); config/schema/objeto ausente também não se repetem.
        return False
    except Exception:
        return True
    return False


@task(
    retries=2,
    retry_delay_seconds=1,
    retry_condition_fn=_should_retry,
    timeout_seconds=120,
    cache_policy=NO_CACHE,
)
def extract(reader, reference, source: str, run_id: str, checkpoint=None) -> list:
    """Lê o objeto do MinIO (retomando do checkpoint, se houver) e emite os lotes."""
    logger = get_run_logger()
    extractor = EXTRACTORS[source](object_reader=reader, object_reference=reference)
    batches = list(extractor.read(run_id=run_id, checkpoint=checkpoint))
    logger.info("extract concluído: %d lote(s) de '%s'", len(batches), source)
    return batches


@task(timeout_seconds=120, cache_policy=NO_CACHE)
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


@task(timeout_seconds=120, cache_policy=NO_CACHE)
def load(db_path: str, results: list, tuning: dict) -> list:
    """Grava aceitos e rejeitados no DuckDB e reconcilia as contagens."""
    logger = get_run_logger()
    with DuckDbLoadRepository(db_path, **tuning) as repo:
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
    reprocess: bool = False,
    db_path: str | None = None,
) -> dict:
    """Ingestão idempotente de um objeto do MinIO na camada tratada (DuckDB).

    ``reprocess=True`` ignora o controle de idempotência por objeto (backfill
    controlado); a deduplicação por linha continua protegendo contra duplicata.
    """
    logger = get_run_logger()
    if source not in EXTRACTORS:
        raise ValueError(f"fonte desconhecida: {source!r}")
    db_path = db_path or os.environ.get("DUCKDB_PATH", "warehouse.duckdb")

    settings = load_extraction_settings()
    reader = MinioObjectReader(_minio_client(settings))
    reference = ObjectReference(bucket=bucket, key=key, version_id=version_id)

    checksum = _object_checksum(reader, reference)
    tuning = _connection_tuning()
    with DuckDbLoadRepository(db_path, **tuning) as repo:
        if repo.object_already_loaded(checksum):
            if not reprocess:
                logger.info("objeto %s já concluído (hash %s) — ignorado", key, checksum[:12])
                return {"status": "ignored", "source": source, "source_checksum": checksum}
            # A proteção por linha depende de a deduplicação e a tabela
            # `_loaded_identity` concordarem sobre o que é identidade. Ao
            # aceitar correção como versão nova, rechavear o controle pela
            # identidade de idempotência antes de confiar nesta linha:
            # docs/adrs/0002-identidade-e-versoes-na-tabela-de-ingestao.md
            logger.info("reprocess: ignorando controle de objeto %s; dedup por linha protege", key)
        references = _build_references(repo, source)
        previous = repo.loaded_identities(source)
        checkpoint = repo.load(source)  # retomada: posição confirmada anterior
        if checkpoint and checkpoint.source_version != f"sha256:{checksum}":
            checkpoint = None  # checkpoint é de outra versão do objeto: lê do início

    batches = extract(
        reader, reference, source, run_id=event_id or checksum[:16], checkpoint=checkpoint
    )
    results = transform(batches, source, references, previous)
    reconciliations = load(db_path, results, tuning)

    with DuckDbLoadRepository(db_path, **tuning) as repo:
        repo.mark_object_loaded(source, checksum, event_id or checksum[:16])
        if batches:  # retomada: confirma a posição somente após a carga
            repo.commit(batches[-1].checkpoint)

    loaded = sum(r["loaded"] for r in reconciliations)
    logger.info("ingestão concluída: %d registro(s) carregado(s) de '%s'", loaded, source)
    return {
        "status": "loaded",
        "source": source,
        "source_checksum": checksum,
        "reconciliation": reconciliations,
    }


@flow(name="backfill")
def backfill(
    sources: list[str],
    bucket: str,
    *,
    prefix: str = "landing",
    reprocess: bool = False,
    db_path: str | None = None,
) -> dict:
    """Backfill controlado de um conjunto explícito de fontes.

    A janela, as fontes e o modo (reprocesso) são parâmetros e ficam registrados
    no histórico do run do Prefect. Cada fonte roda como um subflow `ingest-object`.
    """
    logger = get_run_logger()
    logger.info("backfill: fontes=%s prefixo=%s reprocess=%s", sources, prefix, reprocess)
    resultados = []
    for source in sources:
        key = f"{prefix}/{source}.csv"
        outcome = ingest_object(
            source=source, bucket=bucket, key=key, reprocess=reprocess, db_path=db_path
        )
        resultados.append({"source": source, "status": outcome["status"]})
    return {
        "mode": "backfill",
        "reprocess": reprocess,
        "sources": list(sources),
        "results": resultados,
    }
