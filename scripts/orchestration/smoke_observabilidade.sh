#!/usr/bin/env bash
# Smoke de observabilidade (OB-11): cenário de sucesso + falha controlada com
# retry visível no painel e o alerta correspondente.
#
# Roda no HOST, não dentro do runner: precisa do próprio `docker compose`
# para parar/religar o MinIO, que é o gatilho da falha controlada.
#
# Pré-requisitos:
#   - `docker compose up -d` já rodando (OB-07/OB-08).
#   - Servidor Prefect publicado no host (OQ-03) e PREFECT_API_URL configurado
#     no runner com host.docker.internal, não localhost (ver runbook, OB-09).
#   - As duas regras de alerta do OB-09 já criadas manualmente no Kibana
#     (Stack Management -> Rules) — não são importáveis por NDJSON.
#
# Este script só produz os eventos reais no Elasticsearch/Prefect. Ele NÃO
# tira print nem confirma o alerta sozinho — a evidência (prints do painel
# OB-08 e do Kibana Alerts) precisa ser capturada por quem rodar isto, com
# Docker de verdade. Não foi possível gerar essa evidência neste ambiente de
# desenvolvimento (sem Docker) — só o roteiro abaixo.
set -euo pipefail

echo "=== Cenário A: execução com sucesso ==="
docker compose exec -T runner python scripts/orchestration/health_check.py
docker compose exec -T runner python scripts/orchestration/run_ingest.py --source empresas
cat <<'EVIDENCIA'
>>> Evidência a capturar (cenário A):
    - print do painel Kibana (OB-08) mostrando a execução de "empresas" com
      status "success" e duração/volumes preenchidos;
    - saída do comando acima ("RESULTADO: {...}", status "loaded").
    curl -s 'http://localhost:9200/etl-logs-*/_search?q=source:empresas&sort=@timestamp:desc&size=5&pretty'
EVIDENCIA

echo
echo "=== Cenário B: falha controlada com retry visível + alerta ==="
echo ">>> Parando o MinIO para forçar falha transitória na extração..."
docker compose stop minio

set +e
docker compose exec -T runner python scripts/orchestration/run_ingest.py --source pesquisas
resultado=$?
set -e

if [ "$resultado" -eq 0 ]; then
  cat <<'AVISO'
!!! A ingestão terminou sem erro — o MinIO pode ter voltado rápido demais,
    ou os 3 attempts (padrão de ETL_EXTRACTION_MAX_ATTEMPTS) absorveram a
    janela em que ele ficou fora do ar. Repita com o MinIO parado por mais
    tempo antes de rodar o comando, ou aumente ETL_EXTRACTION_MAX_ATTEMPTS
    temporariamente para tornar a falha mais fácil de reproduzir.
AVISO
fi

cat <<'EVIDENCIA'
>>> Evidência a capturar (cenário B):
    - painel Kibana (OB-08), viz "ETL - Tentativas de repeticao"
      (etl-viz-retries) com extraction.retry.emitted > 0 para "pesquisas";
    - Kibana Alerts mostrando a regra "ETL - falha de execução" ativa
      (ver docs/runbook-execucao.md, seção Alertas mínimos);
    - a linha com tags:_jsonparsefailure no Elasticsearch (traceback do
      Prefect ao esgotar as tentativas).
    curl -s 'http://localhost:9200/etl-logs-*/_search?q=event:extraction.retry.emitted&sort=@timestamp:desc&size=10&pretty'
EVIDENCIA

echo
echo ">>> Restaurando o MinIO..."
docker compose start minio
echo ">>> Rode o mesmo comando de novo para confirmar a recuperação:"
echo "    docker compose exec -T runner python scripts/orchestration/run_ingest.py --source pesquisas"
