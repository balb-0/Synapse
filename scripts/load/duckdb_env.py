#!/usr/bin/env python3
"""Cria o arquivo local do DuckDB e executa o health check de persistência."""

import argparse
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.load.config import ConfigurationError, load_duckdb_settings  # noqa: E402
from etl.load.environment import (  # noqa: E402
    DatabaseEnvironmentError,
    HealthCheckReport,
    run_health_check,
)


def render(report: HealthCheckReport) -> str:
    """Formata o relatório para leitura no terminal."""

    origem = "criado nesta execucao" if report.database_created else "ja existia"
    linhas = [
        f"Arquivo: {report.database_path} ({origem})",
        f"DuckDB: {report.duckdb_version} (embutido, sem servidor)",
    ]
    for check in report.checks:
        situacao = "ok" if check.passed else "falha"
        linhas.append(f"[{situacao}] {check.name}: {check.detail}")
    return "\n".join(linhas)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        type=Path,
        help="Caminho do arquivo do banco; tem prioridade sobre ETL_DUCKDB_PATH",
    )
    args = parser.parse_args()

    parameters = {"database_path": args.database}
    try:
        settings = load_duckdb_settings(
            {name: value for name, value in parameters.items() if value is not None}
        )
        report = run_health_check(settings)
    except (ConfigurationError, DatabaseEnvironmentError) as error:
        parser.exit(1, f"HEALTH_CHECK_FALHOU: {error}\n")
    else:
        print(render(report))
        if not report.passed:
            parser.exit(1, "HEALTH_CHECK_FALHOU: ver as verificacoes acima\n")


if __name__ == "__main__":
    main()
