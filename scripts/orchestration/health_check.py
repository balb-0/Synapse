"""Health check do orquestrador (Prefect) e do banco de ingestão (OB-09).

Uso (dentro do runner):
    docker compose run --rm --no-deps runner python scripts/orchestration/health_check.py

Publica um evento estruturado (``orchestration.health_check.emitted``) no
mesmo índice do painel operacional (OB-08). Exit codes: 0 para ok, 1 para
falha e 2 para contenção de escrita (busy), com disponibilidade do banco
indeterminada. Utilizável em cron/CI além de execução manual.
"""

import argparse
import logging
import os
import sys
import time

from etl.load.config import ConfigurationError, load_duckdb_settings
from etl.orchestration import configure_json_logging
from etl.orchestration.health import (
    HEALTH_CHECK_EVENT,
    HEALTH_CHECK_STAGE,
    log_health_check,
    run_orchestration_health_check,
)


def render(report) -> str:
    linhas = [f"status geral: {report.status}"]
    for check in (report.prefect, report.database):
        situacao = (
            "ocupado" if getattr(check, "busy", False) else ("ok" if check.passed else "falha")
        )
        linhas.append(f"[{situacao}] {check.name}: {check.detail}")
    linhas.append(f"duração: {report.duration_ms} ms")
    return "\n".join(linhas)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-only", action="store_true", help="omite o resumo humano")
    args = parser.parse_args()
    configure_json_logging()
    # CLI independente: impedir que o console raiz do Prefect repita o evento
    # em stderr. O handler JSON deste logger continua publicando no stdout.
    logging.getLogger("etl.orchestration").propagate = False
    started = time.monotonic()
    try:
        settings = load_duckdb_settings()
    except ConfigurationError:
        # Mensagens de validadores podem conter valores fornecidos pelo usuário.
        # Publicar somente a categoria; nenhuma URL, caminho ou valor de env.
        detail = "configuração do DuckDB inválida; revise ETL_DUCKDB_*"
        logging.getLogger("etl.orchestration").error(
            HEALTH_CHECK_EVENT,
            extra={
                "event": HEALTH_CHECK_EVENT,
                "stage": HEALTH_CHECK_STAGE,
                "status": "degraded",
                "error_type": "ConfigurationError",
                "prefect_available": None,
                "prefect_detail": "não verificado: configuração inválida",
                "database_available": False,
                "database_status": "unavailable",
                "database_detail": detail,
                "duration_ms": round((time.monotonic() - started) * 1000, 3),
            },
        )
        if not args.json_only:
            print(f"status geral: degraded\n[falha] duckdb: {detail}")
        sys.exit(1)
    report = run_orchestration_health_check(
        api_url=os.environ.get("PREFECT_API_URL"), settings=settings
    )
    log_health_check(report)
    if not args.json_only:
        print(render(report))
    if report.status == "busy":
        sys.exit(2)
    if not report.passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
