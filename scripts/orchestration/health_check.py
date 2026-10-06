"""Health check do orquestrador (Prefect) e do banco de ingestão (OB-09).

Uso (dentro do runner):
    docker compose run --rm --no-deps runner python scripts/orchestration/health_check.py

Publica um evento estruturado (``orchestration.health_check.emitted``) no
mesmo índice do painel operacional (OB-08). Exit codes: 0 para ok, 1 para
falha e 2 para contenção de escrita (busy), com disponibilidade do banco
indeterminada. Utilizável em cron/CI além de execução manual.
"""

import argparse
import os
import sys

from etl.load.config import load_duckdb_settings
from etl.orchestration import configure_json_logging
from etl.orchestration.health import log_health_check, run_orchestration_health_check


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
    settings = load_duckdb_settings()
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
