"""Executa o comando único: backfill, carga, reconciliação e publicação (PL-01..PL-03, PL-05).

Uso (dentro do runner; `ETL_PUBLISH_DIR` já vem definido no Compose):
    python scripts/orchestration/run_pipeline.py
        [--publish-dir /caminho/privado/publicacao-bi]
        [--sources empresas pesquisas ...] [--reprocess] [--observed-at 2026-09-30T23:59:59]

Espera os objetos já publicados na área de entrada do MinIO (para semear
fixtures antes, ver `scripts/orchestration/run_backfill.py`). Sem `--sources`,
processa as seis fontes na ordem de dependência. Os sete Parquet só são
publicados no destino (`--publish-dir` ou `ETL_PUBLISH_DIR`, fora do checkout)
quando a reconciliação retorna `reconciled=true`. A saída resume o status por
fonte do backfill, o `load_id` da geração analítica e a geração publicada.

Códigos de saída: 0 sucesso; 1 falha com a etapa identificada no stderr
(`PIPELINE FALHOU na etapa <stage>`); 2 parâmetro inválido (argparse).
"""

import argparse
import os
import sys
from datetime import datetime

from etl.orchestration import PipelineStageError, configure_json_logging, run_pipeline


def main() -> None:
    configure_json_logging()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--publish-dir",
        default=os.environ.get("ETL_PUBLISH_DIR") or None,
        help="destino dos Parquet, fora do checkout (padrão: ETL_PUBLISH_DIR)",
    )
    ap.add_argument("--sources", nargs="+", default=None)
    ap.add_argument("--reprocess", action="store_true")
    ap.add_argument(
        "--observed-at",
        help="ISO timestamp de fechamento observado no último dia do mês (C03)",
    )
    args = ap.parse_args()
    if not args.publish_dir:
        ap.error("defina --publish-dir ou a variável de ambiente ETL_PUBLISH_DIR")

    observed = datetime.fromisoformat(args.observed_at) if args.observed_at else None
    try:
        result = run_pipeline(
            sources=args.sources,
            publish_dir=args.publish_dir,
            reprocess=args.reprocess,
            observed_at=observed,
        )
    except PipelineStageError as error:
        # Etapa identificada na saída; reexecutar o comando após corrigir a
        # causa é seguro (ingestão idempotente, fatos substituídos, publicação
        # atômica preserva o current.json anterior).
        print(f"PIPELINE FALHOU na etapa {error.stage}: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print("PIPELINE:", result)


if __name__ == "__main__":
    main()
