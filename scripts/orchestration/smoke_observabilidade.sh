#!/usr/bin/env bash
# Smoke de observabilidade (OB-11): cenário de sucesso + falha controlada com
# o alerta correspondente.
#
# Roda no HOST, não dentro do runner: precisa do próprio `docker compose`
# para parar/religar o MinIO, que é o gatilho da falha controlada.
#
# Pré-requisitos:
#   - `docker compose up -d` já rodando (OB-07/OB-08), incluindo o serviço
#     `prefect-server` (OQ-03). O runner usa por padrão
#     PREFECT_API_URL=http://prefect-server:4200/api; para um Prefect no host,
#     exporte PREFECT_API_URL=http://host.docker.internal:4200/api (OB-09).
#   - As duas regras de alerta do OB-09 já criadas no Kibana, pela UI ou pela
#     API de Alerting (comandos no runbook) — não são importáveis por NDJSON.
#
# IMPORTANTE — o que este cenário B prova e o que não prova (confirmado na
# execução real de 25/09/2026, docs/smoke-observabilidade-sprint4.md): com o
# MinIO fora do ar, `run_ingest.py` falha já no upload do fixture (`_upload`,
# erro `MaxRetryError` para `minio:9000`), antes de chamar `ingest_object`.
# Nenhum flow run é criado nesse caso. O script prova a falha real e o alerta
# correspondente (a exceção propaga até o topo; o traceback cru vai para o
# stderr e o Docker GELF o entrega ao Logstash com a marca `etl_error`), mas
# **não** produz `extraction.retry.emitted` — isso exigiria derrubar o MinIO
# só depois do upload e do checksum e só durante a leitura da task, uma
# janela estreita demais para cronometrar de fora sem uma ferramenta de
# falha de rede mais cirúrgica (ex.: toxiproxy), que esta stack não tem.
# A prova determinística do mecanismo de retry já existe nos testes
# automatizados (tests/extraction/test_resilience.py, OB-06;
# tests/e2e/test_telemetria_e_coletor_indisponivel.py, OB-10) — não precisa
# ser reproduzida ao vivo para ser confiável.
set -euo pipefail

# `exec` rodaria o comando dentro do container cujo processo principal é
# `sleep infinity`; o driver GELF acompanha o processo principal e, portanto,
# não garante a coleta do stdout do comando. `run --rm` cria um container
# one-shot e faz do próprio script o processo observado pelo driver.
run_runner() {
  docker compose run --rm --no-deps -T runner "$@"
}

echo "=== Cenário A: execução com sucesso ==="
run_runner python scripts/orchestration/health_check.py
run_runner python scripts/orchestration/run_ingest.py --source empresas
cat <<'EVIDENCIA'
>>> Evidência a capturar (cenário A):
    - print do painel Kibana (OB-08) mostrando a execução de "empresas" com
      status "success" e duração/volumes preenchidos;
    - saída do comando acima ("RESULTADO: {...}", status "loaded").
    curl -s 'http://localhost:9200/etl-logs-*/_search?q=source:empresas&sort=@timestamp:desc&size=5&pretty'
EVIDENCIA

echo
echo "=== Cenário B: falha controlada (MinIO parado) + alerta ==="
echo ">>> Parando o MinIO para forçar a falha de acesso à fonte..."
docker compose stop minio

set +e
run_runner python scripts/orchestration/run_ingest.py --source pesquisas
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
    - a linha com tags:etl_error no Elasticsearch (traceback cru
      que run_ingest.py deixa propagar até o topo, sem capturar);
    curl -s 'http://localhost:9200/etl-logs-*/_search?q=tags:etl_error&sort=@timestamp:desc&size=5&pretty'
EVIDENCIA

echo
echo ">>> Restaurando o MinIO..."
docker compose start minio
echo ">>> Rode o mesmo comando de novo para confirmar a recuperação:"
echo "    docker compose run --rm --no-deps -T runner python scripts/orchestration/run_ingest.py --source pesquisas"
