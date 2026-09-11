#!/usr/bin/env bash
# Gate final da Sprint 3 (VB-11).
#
# Executa em sequência e falha no primeiro erro:
#   1. dependências instaladas (ou instalação, com --install);
#   2. ruff check + ruff format --check, usando o ruff.toml geral quando
#      presente e, caso contrário, o ruff-transformation.toml histórico;
#   3. suíte unittest completa (PYTHONPATH=src python -m unittest discover);
#   4. validação do dmc.json (scripts/dmc/validate_dmc.py e run_gates.py);
#   5. checklist impresso.
#
# Uso: scripts/gate_final.sh [--install]
set -euo pipefail
cd "$(dirname "$0")/.."

step() { printf '\n==> [%s] %s\n' "$1" "$2"; }

step 1/5 "dependências"
if [ "${1:-}" = "--install" ]; then
  python -m pip install -r requirements.txt
  [ -f requirements-transformation-dev.txt ] && python -m pip install -r requirements-transformation-dev.txt
fi
python -c "import duckdb, minio, prefect, coverage, ruff" 2>/dev/null \
  || python -c "import duckdb, minio, prefect" # ruff/coverage podem vir só do requirements de dev
python -m ruff --version >/dev/null
echo "dependências OK"

step 2/5 "ruff (lint + formatação)"
if [ -f ruff.toml ]; then
  RUFF_CFG=ruff.toml
  RUFF_PATHS="src tests scripts"
elif [ -f ruff-transformation.toml ]; then
  RUFF_CFG=ruff-transformation.toml
  RUFF_PATHS="src/etl/transformation tests/transformation scripts/transformation"
else
  echo "nenhuma configuração de ruff encontrada" >&2
  exit 1
fi
echo "configuração: $RUFF_CFG; caminhos: $RUFF_PATHS"
python -m ruff check --config "$RUFF_CFG" $RUFF_PATHS
python -m ruff format --config "$RUFF_CFG" --check $RUFF_PATHS

step 3/5 "suíte unittest completa"
PYTHONPATH=src python -m unittest discover -s tests -v

step 4/5 "validação do dmc.json"
python scripts/dmc/validate_dmc.py
python scripts/dmc/run_gates.py

step 5/5 "checklist"
cat <<'EOF'
[ ] dependências instaladas e importáveis
[ ] ruff check sem erros
[ ] ruff format --check sem diferenças
[ ] suíte unittest completa verde
[ ] dmc.json válido e gates de rastreabilidade aprovados
EOF
printf '\nGATE FINAL: OK\n'
