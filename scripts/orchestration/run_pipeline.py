"""Executa o comando único: backfill, carga, reconciliação e publicação (PL-01..PL-03).

Uso (dentro do runner):
    python scripts/orchestration/run_pipeline.py --publish-dir /caminho/privado/publicacao-bi
        [--sources empresas pesquisas ...] [--reprocess] [--observed-at 2026-09-30T23:59:59]

Espera os objetos já publicados na área de entrada do MinIO (para semear
fixtures antes, ver `scripts/orchestration/run_backfill.py`). Sem `--sources`,
processa as seis fontes na ordem de dependência. Os sete Parquet só são
publicados em `--publish-dir` (fora do checkout) quando a reconciliação
retorna `reconciled=true`. A saída resume o status por fonte do backfill, o
`load_id` da geração analítica e a geração publicada.
"""

import argparse
import sys
from datetime import datetime

from etl.orchestration import PipelineStageError, configure_json_logging, run_pipeline


def main() -> None:
    configure_json_logging()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--publish-dir", required=True, help="destino dos Parquet, fora do checkout")
    ap.add_argument("--sources", nargs="+", default=None)
    ap.add_argument("--reprocess", action="store_true")
    ap.add_argument(
        "--observed-at",
        help="ISO timestamp de fechamento observado no último dia do mês (C03)",
    )
    args = ap.parse_args()

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
