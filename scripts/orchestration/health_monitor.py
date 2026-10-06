"""Execute o health check periodicamente, mesmo quando nenhum flow está rodando."""

from __future__ import annotations

import argparse
import json
import logging
import math
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from etl.orchestration import configure_json_logging
from etl.orchestration.health import HEALTH_CHECK_EVENT, HEALTH_CHECK_STAGE

HEALTH_CHECK_SCRIPT = Path(__file__).with_name("health_check.py")


def positive_seconds(value: str) -> float:
    seconds = float(value)
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError("o intervalo deve ser positivo e finito")
    return seconds


def check_once(timeout: float) -> None:
    """Isole a checagem em processo para limitar até um travamento do DuckDB."""
    started = time.monotonic()
    failure = None
    try:
        completed = subprocess.run(
            [sys.executable, str(HEALTH_CHECK_SCRIPT), "--json-only"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        # Só aceite um relatório conclusivo. Exit code 1 é o resultado normal
        # de uma checagem degradada; 2 é busy. Nenhum encerra o monitor.
        reports = []
        for line in completed.stdout.splitlines():
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and payload.get("event") == HEALTH_CHECK_EVENT:
                reports.append(payload)
        if (
            len(reports) == 1
            and reports[0].get("status") in ("ok", "degraded", "busy")
            and completed.returncode == {"ok": 0, "degraded": 1, "busy": 2}[reports[0]["status"]]
        ):
            print(json.dumps(reports[0], ensure_ascii=False), flush=True)
            return
        failure = f"health check sem relatório conclusivo (exit code {completed.returncode})"
    except subprocess.TimeoutExpired:
        failure = f"health check excedeu o limite de {timeout:g} segundos"
    except OSError as error:
        failure = f"não foi possível iniciar o health check: {error}"

    logging.getLogger("etl.orchestration").error(
        HEALTH_CHECK_EVENT,
        extra={
            "event": HEALTH_CHECK_EVENT,
            "stage": HEALTH_CHECK_STAGE,
            "status": "degraded",
            "monitor_detail": failure,
            "duration_ms": round((time.monotonic() - started) * 1000, 3),
        },
    )


def monitor(interval: float, timeout: float, stopped: threading.Event) -> None:
    """Comece imediatamente e mantenha o próximo ciclo após uma falha."""
    while not stopped.is_set():
        started = time.monotonic()
        check_once(timeout)
        stopped.wait(max(0, interval - (time.monotonic() - started)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval-seconds", type=positive_seconds, default=60.0)
    parser.add_argument("--timeout-seconds", type=positive_seconds, default=30.0)
    args = parser.parse_args()
    configure_json_logging()
    stopped = threading.Event()
    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, lambda *_: stopped.set())
    monitor(args.interval_seconds, args.timeout_seconds, stopped)


if __name__ == "__main__":
    main()
