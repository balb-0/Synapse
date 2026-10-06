"""Shared finite lock retry for ingestion, analytical loading and publication."""

from __future__ import annotations

import logging
import math
import time
from pathlib import Path

import duckdb

from etl.load.config import DEFAULT_WRITE_LOCK_TIMEOUT_SECONDS
from etl.load.log_events import LOAD_STAGE

# O DuckDB já recusa uma segunda conexão de escrita ao mesmo arquivo com este
# erro, nomeando o processo concorrente. Só distinguimos essa mensagem de
# outro IOException (ex.: permissão negada) para saber quando vale esperar.
# A mensagem mudou entre versões do DuckDB. A forma nova no Windows, por
# exemplo, informa que o arquivo "is being used by another process". Todas
# descrevem a mesma condição transitória: outro escritor mantém o arquivo.
WRITE_LOCK_CONFLICT_MARKERS = (
    "Could not set lock",
    "being used by another process",
    "sendo usado por outro processo",
)
WRITE_LOCK_POLL_INTERVAL_SECONDS = 0.05

CONNECT_RETRY_EVENT = "load.connect_retry.emitted"


class WriteLockTimeoutError(RuntimeError):
    """Não foi possível abrir o arquivo: outro processo mantinha a escrita."""


def _emit_connect_retry(
    *, status: str, attempts: int, duration_ms: float, logger: logging.Logger | None = None
) -> None:
    """Publica um evento por chamada, não por tentativa de poll (OB-06).

    O poll de lock roda a cada 50ms e pode iterar dezenas de vezes até o
    arquivo liberar ou o timeout vencer — logar cada tick violaria o próprio
    objetivo de rótulos limitados. Em vez disso, ``connect_with_retry`` só
    chama isto uma vez por conexão, resumindo quantas tentativas e quanto
    tempo o wait total levou.
    """
    target_logger = logger or logging.getLogger("etl.load")
    target_logger.info(
        CONNECT_RETRY_EVENT,
        extra={
            "event": CONNECT_RETRY_EVENT,
            "stage": LOAD_STAGE,
            "status": status,
            "attempts": attempts,
            "duration_ms": duration_ms,
        },
    )


def connect_with_retry(
    database: str | Path,
    timeout_seconds: float = DEFAULT_WRITE_LOCK_TIMEOUT_SECONDS,
    *,
    read_only: bool = False,
) -> duckdb.DuckDBPyConnection:
    """Espera o escritor anterior liberar o arquivo em vez de falhar de imediato.

    O DuckDB só permite um processo com o arquivo aberto para escrita por vez.
    Um erro que não seja de lock (arquivo sem permissão, diretório ausente)
    propaga na primeira tentativa: esperar não o resolveria.
    """
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)):
        raise ValueError("timeout_seconds deve ser finito e maior que zero")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds deve ser finito e maior que zero")
    started = time.monotonic()
    deadline = started + timeout_seconds
    attempts = 1
    while True:
        try:
            connection = duckdb.connect(str(database), read_only=read_only)
        except duckdb.IOException as error:
            if not any(marker in str(error) for marker in WRITE_LOCK_CONFLICT_MARKERS):
                raise
            if time.monotonic() >= deadline:
                _emit_connect_retry(
                    status="timed_out",
                    attempts=attempts,
                    duration_ms=round((time.monotonic() - started) * 1000, 3),
                )
                raise WriteLockTimeoutError(
                    f"não foi possível abrir {database} em {timeout_seconds}s: "
                    f"outra carga está em andamento ({error})"
                ) from error
            attempts += 1
            time.sleep(min(WRITE_LOCK_POLL_INTERVAL_SECONDS, max(0.0, deadline - time.monotonic())))
            continue
        if attempts > 1:
            _emit_connect_retry(
                status="recovered",
                attempts=attempts,
                duration_ms=round((time.monotonic() - started) * 1000, 3),
            )
        return connection
