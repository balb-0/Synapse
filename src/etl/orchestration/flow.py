"""Flow de ingestão orquestrado (OV-02).

Sequência de um objeto: verificação de idempotência -> extração -> transformação
-> carga -> reconciliação e confirmação. Cada etapa é uma tarefa do Prefect; a
falha de uma interrompe as dependentes (o Prefect não executa a jusante). O
gatilho normal é o evento `s3:ObjectCreated` do MinIO (adaptador externo chama
`ingest_object`); a execução manual usa os mesmos parâmetros.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone

from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE
from prefect.runtime import flow_run, task_run

from etl.extraction import (
    ClientesExtractor,
    EmpresasExtractor,
    ExtractionError,
    FailureNature,
    MinioObjectReader,
    ObjectReference,
    PesquisasExtractor,
    QuestoesExtractor,
    RespondentesExtractor,
    RespostasExtractor,
    RetryExecutor,
    classify_source_failure,
    load_extraction_settings,
)
from etl.load import DuckDbLoadRepository, UnbalancedLoadError
from etl.load.config import load_duckdb_settings
from etl.orchestration.lock import database_lock
from etl.transformation.consistency import RELATIONS, ReferenceData
from etl.transformation.pipeline import transform_object
from etl.transformation.schema import KEYS

EXTRACTORS = {
    "empresas": EmpresasExtractor,
    "pesquisas": PesquisasExtractor,
    "clientes": ClientesExtractor,
    "questoes": QuestoesExtractor,
    "respondentes": RespondentesExtractor,
    "respostas": RespostasExtractor,
}

ORCHESTRATION_STAGE = "orchestration"
EXTRACT_TASK_EVENT = "orchestration.extract.emitted"
TRANSFORM_TASK_EVENT = "orchestration.transform.emitted"
LOAD_TASK_EVENT = "orchestration.load.emitted"
INGEST_OBJECT_EVENT = "orchestration.ingest_object.emitted"
BACKFILL_EVENT = "orchestration.backfill.emitted"


class SourceChangedError(ValueError):
    """O objeto mudou entre a verificação de identidade e a extração."""


def _current_task_id() -> str | None:
    """Identificador de correlação do Prefect para o marco atual (ADR 0008).

    Dentro de uma ``@task`` (``extract``/``transform``/``load``), cada
    tentativa tem seu próprio ``task_run.id``. Marcos publicados direto no
    corpo de um ``@flow`` (``ingest_object``, ``backfill``) não têm task run
    — usam o ``flow_run.id`` da própria execução. Fora de qualquer contexto
    do Prefect (chamada direta em teste unitário), os dois vêm `None`.
    """
    return task_run.id or flow_run.id


def _log_event(logger, event: str, **attributes: object) -> None:
    """Publica um marco no mesmo formato técnico da extração e da carga (ADR 0001).

    A mensagem é o próprio nome do evento — nada interpolado nela — e os
    atributos de correlação e contagem vão em ``extra``, consultáveis por
    campo depois que o log chegar à plataforma de observabilidade. ``None``
    fica de fora, como em ``ExtractionBatchLogEvent.as_dict``/``LoadBatchLogEvent.as_dict``.

    A chamada a ``logger.info`` fica isolada num try/except (OB-10): mesma
    garantia do ADR 0001 já aplicada em extração/carga/transformação — um
    coletor fora do ar não pode corromper nem interromper a orquestração.
    Diferente das outras camadas, aqui não há um sink injetável separado do
    logger; o próprio ``logger.info`` é o único ponto de falha.
    """
    attributes.setdefault("task_id", _current_task_id())
    payload = {"event": event, "stage": ORCHESTRATION_STAGE, **attributes}
    try:
        logger.info(
            event, extra={key: value for key, value in payload.items() if value is not None}
        )
    except Exception:
        pass


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
    """Monta as referências dos pais a partir do que já foi carregado no DuckDB.

    Lê todas as colunas de negócio da view de compatibilidade, não só a chave:
    as checagens de consistência usam mais do que ela — o vínculo cliente ->
    empresa compara ``empresa_id``, e as respostas validam o domínio contra o
    tipo e as listas da questão. Listas são persistidas como JSON e voltam a
    ser listas aqui.
    """
    sources: dict[str, list[dict]] = {}
    for parent, _fields in RELATIONS[source]:
        keys = KEYS[parent]
        records = []
        for record in repo.fetch_compatibility_records(parent):
            record = dict(record)
            for key in keys:
                record[key] = str(record[key])
            for name in ("alternativas", "linhas_matriz", "colunas_matriz"):
                if isinstance(record.get(name), str):
                    record[name] = json.loads(record[name])
            records.append(record)
        sources[parent] = records
    return ReferenceData(sources)


def _should_retry(task, task_run, state) -> bool:
    """Repete só falha transitória; permanente ou já esgotada, não.

    A extração já reexecuta falhas transitórias internamente (RetryExecutor). No
    nível do Prefect só faz sentido repetir um erro transitório: falha
    permanente da extração (credencial/schema/objeto ausente), S3 permanente
    (ex.: ``NoSuchKey``) e limite de retry esgotado falham rápido.
    """
    try:
        state.result(raise_on_failure=True)
    except (ExtractionError, ValueError, KeyError, UnbalancedLoadError):
        # Erros da extração já chegam terminais (transitório foi reexecutado
        # internamente); config/schema/objeto ausente também não se repetem.
        # Reconciliação desbalanceada é determinística para os mesmos lotes:
        # repetir a task reproduziria o mesmo bloqueio.
        return False
    except Exception as error:
        return _is_transient_unexpected(error)
    return False


def _is_transient_unexpected(error: Exception) -> bool:
    """Repete transitórios; schema DuckDB, caminho e permissão falham rápido.

    O ``minio`` é importado tarde para não virar dependência dura do módulo:
    sem ele instalado, todo erro inesperado continua repetindo.
    """

    import duckdb

    if isinstance(error, (TypeError, AttributeError, AssertionError)):
        return False
    if isinstance(error, OSError) and not isinstance(
        error, (TimeoutError, BlockingIOError, ConnectionError)
    ):
        return False
    if isinstance(error, duckdb.Error) and not isinstance(error, duckdb.TransactionException):
        return False
    try:
        from minio.error import S3Error
    except ImportError:
        return True
    if isinstance(error, S3Error):
        return classify_source_failure(error).nature is FailureNature.TRANSIENT
    return True


@task(
    retries=2,
    retry_delay_seconds=1,
    retry_condition_fn=_should_retry,
    timeout_seconds=120,
    cache_policy=NO_CACHE,
)
def extract(reader, reference, source: str, run_id: str, checkpoint=None, settings=None) -> list:
    """Lê o objeto do MinIO (retomando do checkpoint, se houver) e emite os lotes.

    ``settings`` (``ExtractionSettings``) aplica o tamanho de lote e a
    política de retry configurados por ``ETL_EXTRACTION_*``; sem ele, valem os
    padrões do extrator.
    """
    logger = get_run_logger()
    started = time.monotonic()
    task_id = _current_task_id()
    options = {}
    if settings is not None:
        options = {
            "batch_size": settings.batch_size,
            "retry_executor": RetryExecutor.from_settings(settings),
        }
    extractor = EXTRACTORS[source](object_reader=reader, object_reference=reference, **options)
    batches = list(extractor.read(run_id=run_id, task_id=task_id, checkpoint=checkpoint))
    _log_event(
        logger,
        EXTRACT_TASK_EVENT,
        status="success",
        source=source,
        run_id=run_id,
        task_id=task_id,
        batch_count=len(batches),
        duration_ms=round((time.monotonic() - started) * 1000, 3),
    )
    return batches


@task(
    retries=2,
    retry_delay_seconds=1,
    retry_condition_fn=_should_retry,
    timeout_seconds=120,
    cache_policy=NO_CACHE,
)
def transform(batches: list, source: str, references, previous: dict, run_id: str) -> list:
    """Transforma os lotes do objeto com posição absoluta e decisão global de identidade.

    ``source_offset`` vem de ``batch.metadata``, calculado pelo extrator a
    partir da posição física na fonte inteira — inclusive na retomada, em que
    ``batches`` só contém os lotes posteriores ao checkpoint. Um contador
    local reiniciado em zero faria duas ocorrências em posições físicas
    diferentes receberem a mesma identidade em fontes identificadas por
    checksum+posição (``respondentes``).

    A duplicidade é decidida por ``transform_object`` uma única vez sobre
    todos os lotes do objeto, contra as identidades já confirmadas
    (``previous``): repetição idêntica em outro lote vira duplicata e versões
    divergentes da mesma identidade viram conflito em todas as ocorrências.
    """
    logger = get_run_logger()
    started = time.monotonic()
    ingested_at = datetime.now(timezone.utc)
    for batch in batches:
        if batch.metadata.source_offset is None:
            raise ValueError(
                f"o extrator de {source!r} não informou source_offset no lote "
                f"{batch.metadata.batch_id!r}"
            )
    transformed = transform_object(
        batches, references=references, previous=previous, ingested_at=ingested_at
    )
    results = [
        (result, batch.metadata, batch.checkpoint)
        for result, batch in zip(transformed, batches, strict=True)
    ]
    total = sum(r.metrics["accepted_count"] for r, _, _ in results)
    _log_event(
        logger,
        TRANSFORM_TASK_EVENT,
        status="success",
        source=source,
        run_id=run_id,
        accepted_count=total,
        duration_ms=round((time.monotonic() - started) * 1000, 3),
    )
    return results


# O timeout do load cobre o objeto inteiro, não um lote: um objeto grande
# grava N lotes sequenciais na mesma task. 120 s (o mesmo das outras tasks)
# estourou na prática com ~20 mil registros rejeitados no runner do Compose
# (~7 s por lote de 1.000), matando a task no meio de um lote e exigindo
# retomada. Uma hora acomoda objetos na casa das centenas de milhares de
# registros sem remover o limite, que continua existindo.
@task(
    retries=2,
    retry_delay_seconds=1,
    retry_condition_fn=_should_retry,
    timeout_seconds=3600,
    cache_policy=NO_CACHE,
)
def load(db_path: str, results: list, tuning: dict, *, source: str, run_id: str) -> list:
    """Grava aceitos e rejeitados no DuckDB, reconciliando as contagens lote a lote.

    O checkpoint de cada lote é confirmado assim que o próprio lote termina de
    carregar, não só depois que todos os lotes do objeto tiverem passado. Uma
    falha no meio interrompe o laço (a exceção do lote propaga) sem confirmar o
    checkpoint dele nem dos que viriam depois — mas preserva o checkpoint dos
    lotes já confirmados, que é de onde a próxima tentativa deste objeto
    retoma a extração.

    O evento técnico de cada lote já é publicado pelo próprio repositório
    (``etl.load.log_events``); aqui só o resumo da task, um marco por
    execução, não por lote.
    """
    logger = get_run_logger()
    started = time.monotonic()
    with DuckDbLoadRepository(db_path, **tuning) as repo:
        reconciliations = []
        for result, metadata, checkpoint in results:
            outcome = repo.load_batch(result, metadata)
            repo.commit(checkpoint)
            reconciliations.append(outcome.as_dict())
    _log_event(
        logger,
        LOAD_TASK_EVENT,
        status="success",
        source=source,
        run_id=run_id,
        batch_count=len(reconciliations),
        loaded_count=sum(r["loaded"] for r in reconciliations),
        rejected_count=sum(r["rejected"] for r in reconciliations),
        duplicate_count=sum(r["duplicates"] for r in reconciliations),
        duration_ms=round((time.monotonic() - started) * 1000, 3),
    )
    return reconciliations


def _ingest_object(
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
    started = time.monotonic()
    if source not in EXTRACTORS:
        raise ValueError(f"fonte desconhecida: {source!r}")
    # Um único contrato de configuração para o caminho e tuning da conexão.
    # Antes o flow lia DUCKDB_PATH, enquanto o repositório lia
    # ETL_DUCKDB_PATH, permitindo que os dois apontassem para arquivos distintos.
    db_path = db_path or str(load_duckdb_settings().database_path)

    settings = load_extraction_settings()
    reader = MinioObjectReader(_minio_client(settings))
    reference = ObjectReference(bucket=bucket, key=key, version_id=version_id)

    checksum = _object_checksum(reader, reference)
    run_id = event_id or checksum[:16]
    tuning = _connection_tuning()
    with DuckDbLoadRepository(db_path, **tuning) as repo:
        if repo.object_already_loaded(checksum):
            if not reprocess:
                _log_event(
                    logger,
                    INGEST_OBJECT_EVENT,
                    status="ignored",
                    source=source,
                    run_id=run_id,
                    object_key=key,
                    source_checksum=checksum,
                    duration_ms=round((time.monotonic() - started) * 1000, 3),
                )
                return {"status": "ignored", "source": source, "source_checksum": checksum}
            # A proteção por linha depende de a deduplicação e a tabela
            # `_loaded_identity` concordarem sobre o que é identidade. Ao
            # aceitar correção como versão nova, rechavear o controle pela
            # identidade de idempotência antes de confiar nesta linha:
            # docs/adrs/0002-identidade-e-versoes-na-tabela-de-ingestao.md
            _log_event(
                logger,
                INGEST_OBJECT_EVENT,
                status="reprocess",
                source=source,
                run_id=run_id,
                object_key=key,
                source_checksum=checksum,
                duration_ms=round((time.monotonic() - started) * 1000, 3),
            )
        references = _build_references(repo, source)
        previous = repo.loaded_identities(source)
        checkpoint = repo.load(source)  # retomada: posição confirmada anterior
        if checkpoint and checkpoint.source_version != f"sha256:{checksum}":
            checkpoint = None  # checkpoint é de outra versão do objeto: lê do início

    batches = extract(
        reader, reference, source, run_id=run_id, checkpoint=checkpoint, settings=settings
    )
    if any(
        batch.metadata.source_checksum != checksum
        or batch.checkpoint.source_version != f"sha256:{checksum}"
        for batch in batches
    ):
        _log_event(
            logger,
            INGEST_OBJECT_EVENT,
            status="failed",
            source=source,
            run_id=run_id,
            error_type="SourceChangedError",
            duration_ms=round((time.monotonic() - started) * 1000, 3),
        )
        raise SourceChangedError("o objeto mudou antes da carga; nenhum lote foi confirmado")
    results = transform(batches, source, references, previous, run_id)
    reconciliations = load(db_path, results, tuning, source=source, run_id=run_id)

    # `load_batch` já recusa confirmar um lote desbalanceado; a checagem aqui
    # garante que o objeto só é marcado como concluído quando *todos* os lotes
    # reconciliaram — sucesso significa todos os registros classificados e
    # persistidos, nunca uma carga parcial.
    unbalanced = [r["batch_id"] for r in reconciliations if not r["balanced"]]
    if unbalanced:
        raise UnbalancedLoadError(
            f"objeto {key!r} da fonte {source!r} não reconciliou nos lotes {unbalanced}"
        )
    with DuckDbLoadRepository(db_path, **tuning) as repo:
        # O checkpoint de cada lote já foi confirmado dentro de `load`, lote a
        # lote; só falta marcar o objeto inteiro como concluído.
        repo.mark_object_loaded(source, checksum, run_id)

    _log_event(
        logger,
        INGEST_OBJECT_EVENT,
        status="loaded",
        source=source,
        run_id=run_id,
        object_key=key,
        source_checksum=checksum,
        duration_ms=round((time.monotonic() - started) * 1000, 3),
    )
    return {
        "status": "loaded",
        "source": source,
        "source_checksum": checksum,
        "reconciliation": reconciliations,
    }


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
    """Confirma um objeto sob o mesmo lock usado pelo trecho DW/publicação.

    Este flow não publica um conjunto após receber apenas uma fonte. Use
    ``run_pipeline(..., publish_dir=...)`` para concluir as seis fontes e DW.
    """
    settings = load_duckdb_settings({"database_path": db_path})
    with database_lock(settings.database_path, settings.write_lock_timeout_seconds):
        return _ingest_object(
            source,
            bucket,
            key,
            version_id=version_id,
            event_id=event_id,
            reprocess=reprocess,
            db_path=str(settings.database_path),
        )


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
    _log_event(
        logger,
        BACKFILL_EVENT,
        status="started",
        sources=list(sources),
        prefix=prefix,
        reprocess=reprocess,
    )
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
