#!/usr/bin/env bash
# Smoke de observabilidade (OB-11): cenário de sucesso + falha controlada com
# o alerta correspondente.
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
# IMPORTANTE — o que este cenário B prova e o que não prova (confirmado
# empiricamente rodando ingest_object com um leitor MinIO quebrado, sem
# Docker, direto no venv de teste): `ingest_object` calcula o checksum do
# objeto (`_object_checksum`, flow.py) ANTES de chamar a task `extract` —
# e esse cálculo não passa pelo `RetryExecutor` (OB-06), só a leitura de
# fato dentro da task passa. Um MinIO totalmente fora do ar derruba o flow
# bem nesse cálculo, ANTES da task de extração sequer começar — então este
# script prova a falha real e o alerta correspondente (a exceção propaga
# até `run_ingest.py`, que não a captura; o traceback cru vai pro stderr e
# o Docker GELF o entrega ao Logstash como `_jsonparsefailure`), mas **não**
# produz `extraction.retry.emitted` de forma confiável — isso exigiria
# derrubar o MinIO só depois do checksum e só durante a leitura da task, uma
# janela estreita demais para cronometrar de fora sem uma ferramenta de
# falha de rede mais cirúrgica (ex.: toxiproxy), que esta stack não tem.
# A prova determinística do mecanismo de retry já existe nos testes
# automatizados (tests/extraction/test_resilience.py, OB-06;
# tests/e2e/test_telemetria_e_coletor_indisponivel.py, OB-10) — não precisa
# ser reproduzida ao vivo para ser confiável.
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
echo "=== Cenário B: falha controlada (checksum sem MinIO) + alerta ==="
echo ">>> Parando o MinIO para forçar a falha no cálculo do checksum..."
docker compose stop minio

set +e
docker compose exec -T runner python scripts/orchestration/run_ingest.py --source pesquisas
resultado=$?
set -e

if [ "$resultado" -eq 0 ]; then
  cat <<'AVISO'
!!! A ingestão terminou sem erro — o MinIO pode ter voltado antes do
    comando rodar. Confirme com `docker compose ps minio` que ele está
    mesmo parado antes de repetir.
AVISO
fi

cat <<'EVIDENCIA'
>>> Evidência a capturar (cenário B):
    - Kibana Alerts mostrando a regra "ETL - falha de execução" ativa
      (ver docs/runbook-execucao.md, seção Alertas mínimos);
    - a linha com tags:_jsonparsefailure no Elasticsearch (traceback cru
      que run_ingest.py deixa propagar até o topo, sem capturar);
    - o marco JSON limpo do próprio Prefect para a mesma falha
      (prefect.flow_runs, level ERROR, "Encountered exception during
      execution") — sinal adicional, sem tag de erro, útil pra confirmar
      que os dois caminhos (stderr cru e stdout estruturado) descrevem o
      mesmo evento.
    curl -s 'http://localhost:9200/etl-logs-*/_search?q=tags:_jsonparsefailure&sort=@timestamp:desc&size=5&pretty'
EVIDENCIA

echo
echo ">>> Restaurando o MinIO..."
docker compose start minio
echo ">>> Rode o mesmo comando de novo para confirmar a recuperação:"
echo "    docker compose exec -T runner python scripts/orchestration/run_ingest.py --source pesquisas"
