"""Serialização entre writers e publicação nos runners Linux do ETL."""

from __future__ import annotations

import fcntl
import threading
import time
from contextlib import contextmanager
from pathlib import Path

_locks: dict[str, threading.Lock] = {}
_guard = threading.Lock()


@contextmanager
def database_lock(database: Path, timeout_seconds: float):
    """Espera finita; o SO libera o lock após falha ou término do processo.

    O lock de thread complementa flock, que sozinho não serializa conexões
    abertas no mesmo processo. O arquivo permanece, mas não indica posse.
    """
    path = Path(database).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _guard:
        local = _locks.setdefault(str(path), threading.Lock())
    started = time.monotonic()
    if not local.acquire(timeout=timeout_seconds):
        raise TimeoutError("timeout aguardando outra execução do ETL")
    try:
        with Path(str(path) + ".orchestration.lock").open("a") as handle:
            while True:
                try:
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    remaining = timeout_seconds - (time.monotonic() - started)
                    if remaining <= 0:
                        raise TimeoutError("timeout aguardando outro runner do ETL") from None
                    time.sleep(min(0.1, remaining))
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        local.release()
