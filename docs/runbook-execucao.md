# Runbook de execução do ETL

Como outra pessoa do time sobe e executa o pipeline de ingestão
(CSVs → MinIO → Prefect → DuckDB) do zero. Todos os comandos partem da raiz do
repositório. As decisões por trás deste ambiente estão na ADR
[`adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md`](adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md)
e na ADR
[`adrs/0004-execucao-local-e-integracao-continua.md`](adrs/0004-execucao-local-e-integracao-continua.md).

## Pré-requisitos

- Git 2.40+
- Python 3.12+ (imagem do runner usa `python:3.12-slim`)
- Docker e Docker Compose (ambiente local com MinIO, runner e Elastic Stack)
- jq 1.6+ (apenas para os gates do `dmc.json`)

## Instalação

```bash
git clone https://git.inteli.edu.br/graduacao/2026-2a/t13/g05
cd g05
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Para contribuir na transformação (lint e cobertura locais, iguais ao CI):

```bash
pip install -r requirements-transformation-dev.txt
```

## Variáveis de ambiente

Copie `.env.example` para `.env` e preencha. O `.env` não é versionado. As
variáveis reais, lidas por `src/etl/extraction/config.py` e
`src/etl/load/config.py`:

| Variável | Padrão | Papel |
| :--- | :--- | :--- |
| `ETL_MINIO_ENDPOINT` | `http://minio:9000` | Endpoint do MinIO (com scheme) |
| `ETL_MINIO_BUCKET` | `sindusfarma-data` | Bucket de entrada |
| `ETL_MINIO_INPUT_PREFIX` | `landing` | Prefixo dos objetos de entrada |
| `ETL_MINIO_ACCESS_KEY` / `ETL_MINIO_SECRET_KEY` | — | Credenciais do MinIO (obrigatórias) |
| `ETL_REQUEST_TIMEOUT_SECONDS` | `30` | Timeout das requisições ao MinIO |
| `ETL_EXTRACTION_BATCH_SIZE` | `1000` | Registros por lote de extração |
| `ETL_EXTRACTION_MAX_ATTEMPTS` | `3` | Tentativas por falha transitória na extração |
| `ETL_EXTRACTION_RETRY_INITIAL_DELAY_SECONDS` | `0.5` | Atraso inicial do retry (backoff) |
| `ETL_EXTRACTION_RETRY_MAX_DELAY_SECONDS` | `5` | Atraso máximo do retry |
| `ETL_SOURCE_DIR` | — | Adaptador local de leitura, só para desenvolvimento e testes |
| `ETL_DUCKDB_PATH` | `data/duckdb/ingestao.duckdb` | Arquivo do banco de ingestão (caminho relativo ao diretório de execução) |
| `ETL_DUCKDB_THREADS` / `ETL_DUCKDB_MEMORY_LIMIT` | — | Tuning da conexão DuckDB (ausente = padrão do DuckDB) |
| `ETL_DUCKDB_WRITE_LOCK_TIMEOUT_SECONDS` | `300` | Espera pelo lock de escrita do arquivo |
| `ETL_PUBLISH_DIR` | — | Destino da publicação Parquet do pipeline completo (fora do checkout; no runner do Compose, `/data/publicacao`) |

No runner do Compose, `ETL_DUCKDB_PATH` é `/data/warehouse.duckdb`, em volume persistente. Flow e repositório usam esse mesmo contrato de configuração; o TLS do MinIO é derivado do esquema do endpoint.

Detalhes e regras de validação: [`configuracao-extracao.md`](configuracao-extracao.md).

## Subir o ambiente local (Docker Compose)

```bash
docker compose up -d
```

Serviços definidos em `docker-compose.yml`:

- `minio`: armazenamento de objetos na porta 9000; console web em
  http://localhost:9001 (usuário/senha de desenvolvimento: `minioadmin`/`minioadmin`).
- `createbucket`: cria o bucket `sindusfarma` na subida (`mc mb --ignore-existing`).
- `prefect-server`: backend persistente do Prefect com UI de pipelines em
  http://localhost:4200 e health check em http://localhost:4200/api/health
  (volume `prefect-data`: agendamentos e histórico sobrevivem a
  `docker compose down/up`).
- `scheduler`: serve o deployment `ingest-object/agendado` (cron `0 3 * * *`)
  e reinicia sozinho (`restart: unless-stopped`); usa o mesmo ambiente e o
  mesmo banco do `runner`, e o histórico vive no `prefect-server`.
- `runner`: contêiner Python com Prefect e DuckDB (`Dockerfile`), com `src/` e
  `scripts/` montados; permanece ativo (`sleep infinity`) para comandos
  interativos, enquanto o smoke usa containers one-shot para que o stdout seja
  coletado pelo driver GELF.
- `elasticsearch`: armazena a telemetria na porta 9200 (`discovery.type=single-node`,
  segurança desligada — só para desenvolvimento local).
- `logstash`: coletor (OB-07/ADR 0001); recebe UDP/GELF na porta 12201, decodifica
  o JSON de cada linha de log e grava em `etl-logs-YYYY.MM.dd` no Elasticsearch.
  Pipeline em `observability/logstash/pipeline/etl.conf`.
- `kibana`: painel operacional (OB-08) na porta 5601, sem autenticação — mesmo
  padrão de desenvolvimento local do Elasticsearch acima.

O `runner` nunca fala com o Logstash: quem envia é o próprio driver de log
`gelf` do Docker (configurado no serviço `runner`), por UDP — se o Logstash ou
o Elasticsearch estiverem fora do ar, o envio é descartado pelo SO sem
bloquear o runner nem interromper a carga (ADR 0001). Consultar os logs
coletados:

```bash
curl -s 'http://localhost:9200/etl-logs-*/_search?pretty&size=5&sort=@timestamp:desc'
```

### Painel operacional (Kibana, OB-08)

O índice `etl-logs-*` já reúne os eventos das quatro camadas (extração, carga,
transformação, orquestração — OB-06/OB-07). O painel só consulta esse índice;
nenhuma camada do ETL fala com o Kibana. Objetos salvos (index pattern, 5
visualizações e o dashboard) estão versionados em
`observability/kibana/painel-operacional.ndjson`, gerados uma vez a partir do
mapeamento de campos dos eventos. A importação real foi validada na stack Docker do OB-11
(evidência em [`smoke-observabilidade-sprint4.md`](smoke-observabilidade-sprint4.md)).
Para importar, com a stack no ar:

```bash
curl -s -X POST http://localhost:5601/api/saved_objects/_import?overwrite=true \
  -H "kbn-xsrf: true" \
  --form file=@observability/kibana/painel-operacional.ndjson
```

Abrir http://localhost:5601, ir em **Analytics → Dashboard → "ETL - Painel
operacional de execucao (OB-08)"**. O painel mostra, por execução:

- **status por etapa** (`etl-viz-status`: `stage` × `status`, contagem);
- **duração por etapa** (`etl-viz-duracao`: média e máximo de `duration_ms`
  agrupados por `stage`);
- **volumes por fonte** (`etl-viz-volumes`: soma de `byte_count`,
  `record_count`, `extracted_count`, `loaded_count`);
- **rejeições e duplicatas** (`etl-viz-rejeicoes`: soma de `rejected_count` e
  `duplicate_count` por fonte e etapa);
- **tentativas de repetição** (`etl-viz-retries`: contagem por
  `event.keyword`, com a tentativa média em campos separados —
  `attempt` só existe em `extraction.retry.emitted`, `attempts` só em
  `load.connect_retry.emitted`; os dois eventos não têm os mesmos campos
  extras, por isso o painel não os agrupa por categoria/status — faria linhas
  inteiras desaparecerem da tabela em vez de só deixar a métrica em branco).

Se um painel aparecer vazio, é porque ainda não há eventos daquele tipo no
índice (ex.: nenhuma tentativa de retry ocorreu ainda) — não é falha do
painel.

### Health check da orquestração (OB-09)

Checa, numa só chamada, se o servidor Prefect configurado responde e se o
banco de ingestão aceita conexão/consulta/persistência (reaproveita o mesmo
health check da carga, `etl.load.environment.run_health_check`):

```bash
docker compose run --rm --no-deps runner python scripts/orchestration/health_check.py
```

Sai com código 1 se qualquer checagem falhar, e publica um evento
`orchestration.health_check.emitted` no índice `etl-logs-*` (mesmo formato
técnico das demais camadas, ADR 0001) — consultável no painel do OB-08 e
usado pelo alerta de falha abaixo. A checagem do Prefect depende da variável
`PREFECT_API_URL` (o mesmo nome de variável que o próprio Prefect lê); sem
ela configurada, a checagem falha explicitamente em vez de tentar adivinhar
um endereço.

A checagem do banco abre a conexão direto, sem o retry com espera que a
carga real usa (`duckdb_repository._connect_with_retry`) — rodar o health
check durante uma carga em andamento pode reportar `duckdb: falha` por um
lock de escrita transitório que a carga em si esperaria passar. Não é um
sinal de pipeline quebrado nesse caso, só de execução concorrente.

No Compose, o `runner` usa por padrão
`PREFECT_API_URL=http://prefect-server:4200/api`, o serviço `prefect-server`
deste mesmo `docker-compose.yml`. Para apontar para um Prefect rodando no host,
exporte `PREFECT_API_URL=http://host.docker.internal:4200/api` antes do
`docker compose run` (o Compose fornece esse alias também no Linux); dentro do
container, `localhost:4200` apontaria para o próprio container. O endereço GELF
usa a porta publicada no host porque é resolvido pelo daemon Docker. Rodando o
script fora do container, `http://localhost:4200/api` funciona normalmente.

### Alertas mínimos (Kibana Alerting, OB-09)

O schema de saved object de uma regra de alerta do Kibana (`type: "alert"`)
muda com mais frequência entre versões do que o de dashboard/visualização
(OB-08) e as regras de alerta não são importadas por NDJSON. Uma regra mal formada
falha silenciosamente — pior do que simplesmente não existir — por isso as
duas regras mínimas abaixo ficam documentadas para criação manual em **Stack Management → Rules →
Create rule → Elasticsearch query**, em vez de um NDJSON não verificável:

| Regra | Índice | Campo de tempo | Consulta (KQL) | Condição | Janela | Frequência |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ETL - falha de execução | `etl-logs-*` | `@timestamp` | `tags: "etl_error" or (event: "orchestration.health_check.emitted" and status: "degraded")` | contagem **acima de** 0 | últimos 5 min | a cada 1 min |
| ETL - fila parada | `etl-logs-*` | `@timestamp` | `stage: "orchestration"` | contagem **abaixo de** 1 | últimas 26 h | a cada 30 min |

As mesmas regras também podem ser criadas pela API de Alerting do Kibana,
com a stack no ar. Esse caminho foi usado no smoke de 25/09/2026
([evidência](smoke-observabilidade-sprint4.md)) e evita recriar as regras à
mão após um `docker compose down -v`:

```bash
curl -s -X POST localhost:5601/api/alerting/rule -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -d '{
  "name": "ETL - falha de execução", "rule_type_id": ".es-query", "consumer": "stackAlerts",
  "schedule": {"interval": "1m"}, "actions": [],
  "params": {"searchType": "esQuery", "index": ["etl-logs-*"], "timeField": "@timestamp",
    "esQuery": "{\"query\":{\"bool\":{\"should\":[{\"match\":{\"tags\":\"etl_error\"}},{\"bool\":{\"filter\":[{\"match\":{\"event.keyword\":\"orchestration.health_check.emitted\"}},{\"match\":{\"status\":\"degraded\"}}]}}],\"minimum_should_match\":1}}}",
    "size": 5, "thresholdComparator": ">", "threshold": [0], "timeWindowSize": 5, "timeWindowUnit": "m"}}'

curl -s -X POST localhost:5601/api/alerting/rule -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -d '{
  "name": "ETL - fila parada", "rule_type_id": ".es-query", "consumer": "stackAlerts",
  "schedule": {"interval": "30m"}, "actions": [],
  "params": {"searchType": "esQuery", "index": ["etl-logs-*"], "timeField": "@timestamp",
    "esQuery": "{\"query\":{\"match\":{\"stage\":\"orchestration\"}}}",
    "size": 5, "thresholdComparator": "<", "threshold": [1], "timeWindowSize": 26, "timeWindowUnit": "h"}}'
```

A primeira regra cobre tanto uma falha real do pipeline (traceback do Python
vazando no stdout/stderr, capturado pelo Logstash com a tag `etl_error` —
ver `observability/logstash/pipeline/etl.conf`; JSON inválido também recebe a
tag de diagnóstico `_jsonparsefailure`) quanto uma falha detectada
pelo próprio health check acima. A segunda cobre o deployment agendado
parar de rodar (cron diário às 03:00, `scripts/orchestration/deployment.py`)
— 26h dá margem sobre as 24h de intervalo esperado. Nenhuma das duas precisa
de uma action/connector configurada para "disparar alerta visível": o
estado da regra já aparece em **Alerts** no Kibana quando ativa.

### Smoke de observabilidade (OB-11)

Roteiro para provar, com uma execução real, os cenários exigidos pelo card:
uma execução concluída e uma falha controlada com o alerta correspondente.
Pré-requisitos: `docker compose up -d` (inclui `prefect-server` e a Elastic
Stack), painel importado e as duas regras de alerta criadas (seções acima).

```bash
./scripts/orchestration/smoke_observabilidade.sh
```

O script roda no host (não dentro do `runner`), porque o cenário de falha
depende de `docker compose stop/start minio` — algo que só o host consegue
fazer. Ele só produz os eventos reais; **não tira print nem confirma o
alerta sozinho**. Os cenários e o que capturar como evidência:

- **Sucesso**: `health_check.py` + `run_ingest.py --source empresas` com o
  MinIO no ar. Evidência: painel Kibana (OB-08) mostrando a execução com
  status `success`.
- **Falha controlada**: MinIO parado, `run_ingest.py --source pesquisas`
  falha já no upload do fixture (`_upload`, `MaxRetryError` para
  `minio:9000`), antes de `ingest_object` criar um flow run. Essa etapa não
  passa pelo `RetryExecutor` (OB-06), então este cenário não produz
  `extraction.retry.emitted`, só a falha em si. Evidência: a regra "ETL -
  falha de execução" (ver seção anterior) ativa em **Kibana → Alerts**; a
  linha com `tags:etl_error` no Elasticsearch (o traceback cru que
  `run_ingest.py` deixa propagar até o topo, capturado pelo Logstash —
  OB-07).
  A prova de que o retry em si funciona (a garantia "repetição visível")
  já é determinística nos testes automatizados
  (`tests/extraction/test_resilience.py`, OB-06;
  `tests/e2e/test_telemetria_e_coletor_indisponivel.py`, OB-10) —
  reproduzi-la ao vivo exigiria derrubar o MinIO só durante a leitura da
  task de extração, uma janela estreita demais para cronometrar de fora sem
  uma ferramenta de falha de rede mais cirúrgica (ex.: toxiproxy), que esta
  stack não tem.

**Este roteiro foi validado de ponta a ponta em uma stack Docker isolada**: o
health check respondeu `ok`, a ingestão de `empresas` terminou `loaded`, o
Elasticsearch recebeu os eventos estruturados sem `_jsonparsefailure`, e a
falha controlada com MinIO parado recebeu `etl_error` e ativou a regra "ETL -
falha de execução". A importação do painel no Kibana retornou sete objetos
salvos. Resultados, consultas e capturas de tela da execução de 25/09/2026 estão
em [`smoke-observabilidade-sprint4.md`](smoke-observabilidade-sprint4.md).

Verificar o banco de ingestão local (cria o arquivo se não existir e roda
consulta smoke + verificação de persistência):

```bash
PYTHONPATH=src python scripts/load/duckdb_env.py
```

## Executar o pipeline

Ingestão de uma fonte (semeia o fixture no MinIO e roda o flow `ingest-object`):

```bash
docker compose run --rm --no-deps runner python scripts/orchestration/run_ingest.py --source empresas
```

- Fontes válidas: `pesquisas`, `empresas`, `clientes`, `respondentes`,
  `questoes`, `respostas`. Os fixtures de orquestração versionados em
  `scripts/orchestration/fixtures/` cobrem `empresas` e `pesquisas` (usada no
  smoke OB-11; há também `empresas_malformada.csv` para o cenário de
  rejeição); para as demais fontes,
  aponte um arquivo com `--fixture` (e `--key` para o destino). As seis
  fixtures sintéticas completas existem em `tests/fixtures/` e servem aos
  testes, não ao `run_ingest.py`.
- Rodar o mesmo comando duas vezes demonstra a idempotência: a segunda
  execução retorna `status: ignored` (objeto já concluído, controle por hash
  SHA-256 em `_control_object`).

Backfill controlado de várias fontes, com parâmetros registrados no histórico
do run:

```bash
docker compose run --rm --no-deps runner python scripts/orchestration/run_backfill.py --sources empresas pesquisas
docker compose run --rm --no-deps runner python scripts/orchestration/run_backfill.py --sources empresas --reprocess
```

`--reprocess` ignora o controle de idempotência por objeto; a deduplicação por
linha (ADR
[`adrs/0002-identidade-e-versoes-na-tabela-de-ingestao.md`](adrs/0002-identidade-e-versoes-na-tabela-de-ingestao.md))
continua impedindo duplicatas.

### Pipeline completo (backfill → cubos → reconciliação → publicação)

Comando único que encadeia as quatro etapas no mesmo `ETL_DUCKDB_PATH` e só
publica os sete Parquet quando a reconciliação aprova a carga
(`reconciled=true`); o manifesto da geração aponta o `load_id` efetivo.

```bash
# fluxo completo das seis fontes, publicando em ETL_PUBLISH_DIR (/data/publicacao)
docker compose run --rm --no-deps runner python scripts/orchestration/run_pipeline.py

# subconjunto de fontes e destino explícito
docker compose run --rm --no-deps runner python scripts/orchestration/run_pipeline.py \
  --sources empresas pesquisas --publish-dir /data/publicacao
```

Parâmetros (todos opcionais no runner do Compose):

| Parâmetro | Padrão | Papel |
| :--- | :--- | :--- |
| `--publish-dir` | `ETL_PUBLISH_DIR` | Destino dos Parquet, fora de qualquer checkout (validado pela publicação) |
| `--sources` | as seis fontes | Subconjunto, na ordem de dependência (pais antes de filhos) |
| `--reprocess` | desligado | Ignora a idempotência por objeto no backfill (recarga controlada) |
| `--observed-at` | — | Fechamento observado do C03 (ISO, precisa ser o último dia do mês) |

Saída e códigos de erro observáveis:

- **Sucesso (exit 0)** — stdout termina com `PIPELINE: {"status": "completed",
  ...}` incluindo o status por fonte do backfill, o `load_id` da carga, o
  veredito da reconciliação e a geração publicada com linhas por tabela.
- **Falha (exit 1)** — stderr termina com `PIPELINE FALHOU na etapa <stage>:
  ...` (`backfill`, `load_analytics`, `reconciliation` ou `publication`), e o
  marco JSON `orchestration.pipeline.emitted` com `status=failed` e o campo
  `stage` chega ao Kibana como qualquer outro evento. Reexecutar após corrigir
  a causa é seguro: a ingestão é idempotente, os fatos são substituídos (nunca
  acumulados) e uma falha na publicação preserva o `current.json` anterior.
- **Parâmetro inválido (exit 2)** — erro do argparse (ex.: sem `--publish-dir`
  e sem `ETL_PUBLISH_DIR`).

A geração publicada fica em `/data/publicacao/<generation>/` (sete `.parquet`
+ `manifest.json` com hash SHA-256 por arquivo), e `current.json` aponta a
geração vigente — a troca é atômica e só acontece no fim.

## Orquestração Prefect

- Flows em `src/etl/orchestration/flow.py`: `ingest-object` (um objeto:
  verificação de idempotência → extração → transformação → carga →
  reconciliação) e `backfill` (subflows por fonte).
- Retry: as tarefas `extract`, `transform` e `load` têm `retries=2` com
  condição (`_should_retry`) — só repete erro transitório ou inesperado;
  falha permanente (credencial, schema, objeto ausente, `NoSuchKey`) ou
  limite interno de retry já esgotado falham rápido. Falhas transitórias de
  leitura são reexecutadas dentro da extração (`RetryExecutor`, configurável
  por `ETL_EXTRACTION_*`).
- Deployment agendado: `python scripts/orchestration/deployment.py` serve o
  deployment `ingest-object/agendado` (cron `0 3 * * *`). Os deployments
  `ingest-object/manual` e `backfill`, declarados em `prefect.yaml`, são
  publicados pela CLI a partir da raiz do repositório (com o ambiente no ar):

  ```bash
  export PREFECT_API_URL=http://localhost:4200/api
  prefect work-pool create default --type process   # idempotente
  prefect deploy --all
  prefect deployment ls
  ```

  Execução manual com parâmetros explícitos (também pela UI em
  http://localhost:4200):

  ```bash
  prefect deployment run 'ingest-object/agendado' -p source=empresas \
      -p bucket=sindusfarma -p key=landing/empresas.csv -p reprocess=true
  ```

## Disparo pela chegada de objeto

`scripts/orchestration/watch_landing.py` inicia a ingestão quando um objeto
chega à área de entrada (`<prefixo>/<fonte>.csv`), sem varredura manual:

```bash
# webhook (MinIO notifica o adaptador, sem polling):
docker compose exec runner python scripts/orchestration/watch_landing.py --webhook-port 8001
# polling (quando o webhook não está configurado):
docker compose exec runner python scripts/orchestration/watch_landing.py --interval 30
# uma varredura e sai (smoke/teste):
docker compose exec runner python scripts/orchestration/watch_landing.py --once
```

Objeto repetido retorna `status: ignored` (idempotência por SHA-256 em
`_control_object`): não gera carga duplicada. Chaves fora do padrão
`<fonte>.csv` são ignoradas com aviso.

Limites do adaptador (ambiente de desenvolvimento): o modo webhook exige
configurar o notifier no MinIO (`mc event add local/sindusfarma
arn:minio:sqs::1:webhook --prefix landing/ --suffix .csv --event put`) e
expõe a porta escolhida sem autenticação; o `--state-file` do polling é
relativo ao diretório de execução — para sobreviver a `down/up`, aponte-o
para um volume (ex.: `/data/.watch_seen.json`).

## Logs e observabilidade

- Todas as etapas emitem um evento JSON por lote, sem registros de negócio:
  `extraction.batch.emitted`, `transformation.batch.emitted`,
  `load.batch.emitted`, além dos marcos `orchestration.*.emitted`, do
  `orchestration.health_check.emitted` e dos eventos de repetição
  `extraction.retry.emitted` e `load.connect_retry.emitted`. Todos carregam
  `run_id`, `task_id` (o `task_run.id` do Prefect) e, quando aplicável,
  `batch_id`, `source`, `duration_ms`, `byte_count` e contagens.
- `etl.orchestration.logging_config` serializa esses eventos em JSON no
  stdout; `observability/prefect-logging.yml` aplica o mesmo formato aos logs do
  Prefect. O driver GELF entrega o stdout ao Logstash (seções acima).
- A reconciliação por lote é gravada em `_batch_metadata` e validada na carga
  antes do `COMMIT`: `carregados + rejeitados + duplicados` precisa fechar com o
  extraído, senão o lote falha com `UnbalancedLoadError`, o checkpoint não
  avança e o objeto não é marcado como concluído (ver
  [`ddl-ingestao.md`](ddl-ingestao.md)).

## Banco DuckDB

- Banco embutido em arquivo: sem servidor, um escritor por vez. Local padrão
  dos scripts de carga: `data/duckdb/ingestao.duckdb` (`ETL_DUCKDB_PATH`); no
  runner do Compose: `/data/warehouse.duckdb` (volume `duck-data`).
- Tabelas de ingestão por fonte (`ingestao_<fonte>`), rejeições (`rejected`,
  `rejected_reason`) e controle (`_control_object`, `_loaded_identity`,
  `_checkpoint`, `_batch_metadata`) — DDL versionada em
  `sql/duckdb/001_ingestao_tratada.sql`, gerada por
  `python scripts/load/render_ddl.py`.
- Consultar (fora do contêiner, com `duckdb` instalado):

  ```bash
  python -c "import duckdb; c = duckdb.connect('data/duckdb/ingestao.duckdb', read_only=True); print(c.execute('SELECT count(*) FROM ingestao_empresas').fetchall())"
  ```

  ou pela CLI do DuckDB: `duckdb data/duckdb/ingestao.duckdb`. Abra em modo
  `read_only` enquanto o pipeline estiver rodando, para não disputar o lock de
  escrita do arquivo.

## Testes

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Suíte `unittest` em `tests/` (376 testes e cobertura de 92% em 25/09/2026),
organizada por camada (`extraction`, `transformation`, `load`, `orchestration`,
`e2e`, `analytics`, `fixtures`).
Testes que dependem de `duckdb` ou
`minio` são pulados quando a dependência não está instalada; o contrato `tests/transformation/test_duckdb_contract.py` valida os seis schemas em um DuckDB real. Estratégia completa:
[`estrategia-de-testes.md`](estrategia-de-testes.md).

## Integração contínua

O pipeline consolidado do GitLab (`.gitlab-ci.yml`, imagem `python:3.12-slim`)
roda em merge requests e pushes, em dois estágios:

1. `lint`: `ruff check` e `ruff format --check` (`ruff.toml`) sobre `src`,
   `scripts` e `tests`;
2. `test`: `python scripts/architecture/validate_architecture_docs.py`
   (coerência das visões e diagramas com o código),
   `python scripts/transformation/render_schema.py --check` (schema de destino
   versionado íntegro), suíte inteira via
   `coverage run --branch --source=etl -m xmlrunner discover -s tests -o test-reports -v`
   e `coverage report --fail-under=85` sobre todo o pacote `etl`, publicando o
   relatório Cobertura (`coverage-etl.xml`) e o JUnit (`test-reports/`) como
   artefatos. Qualquer falha reprova o job e bloqueia o merge.

Reproduzir localmente: instalar `requirements-transformation-dev.txt` e rodar
os mesmos comandos.

## Troubleshooting

| Sintoma | Causa provável | Ação |
| :--- | :--- | :--- |
| `connection refused` no runner | MinIO ainda não está saudável | `docker compose ps`; aguardar o healthcheck do `minio` e o log do `createbucket` |
| `bucket does not exist` | `createbucket` falhou | `docker compose logs createbucket`; o bucket é criado com `--ignore-existing`, basta `docker compose up -d` de novo |
| Erro de credencial no MinIO | `ETL_MINIO_ACCESS_KEY`/`SECRET_KEY` erradas | conferir `.env` e o ambiente do runner (`minioadmin`/`minioadmin` no Compose) |
| `ETL_DUCKDB_PATH` recusado | caminho aponta para diretório, contém `..` ou é `:memory:` | apontar para um arquivo; caminhos relativos partem do diretório de execução |
| Lock de escrita no DuckDB | outro processo com o arquivo aberto | o arquivo aceita um escritor por vez; fechar a outra conexão ou aguardar `ETL_DUCKDB_WRITE_LOCK_TIMEOUT_SECONDS` |
| CSV malformado | linhas inválidas da fonte | a transformação rejeita por linha com motivo em `rejected`/`rejected_reason`; o lote não cai — a reconciliação em `_batch_metadata` mostra quantos foram rejeitados |
| Objeto reenviado é ignorado (`status: ignored`) | idempotência por hash do objeto | comportamento esperado; para forçar, use `run_backfill.py --reprocess` (a dedup por linha protege) |
| Execução morreu no meio | falha entre extração e carga | reexecute o mesmo comando: o `_checkpoint` retoma da posição confirmada do mesmo objeto, preservando a posição absoluta das ocorrências; checkpoint de outra versão é descartado |
| `UnbalancedLoadError` | contagem gravada não fecha com o extraído | o lote foi desfeito e registrado como `falha`; não há retry automático porque o resultado seria o mesmo — investigar `_batch_metadata` e `rejected_reason` do `run_id` antes de reprocessar |
| Falha transitória de leitura | timeout/instabilidade do MinIO | a extração já retenta (`ETL_EXTRACTION_MAX_ATTEMPTS`); o Prefect retenta só erro transitório ou inesperado (`retries=2` com `_should_retry` nas tasks `extract`, `transform` e `load`) |
| `DDL_DESATUALIZADA` no CI | contrato físico mudou sem regerar o SQL | `python scripts/load/render_ddl.py` e commitar `sql/duckdb/001_ingestao_tratada.sql` |
| Nenhum log aparece no Elasticsearch | Logstash/Elasticsearch ainda subindo, ou pipeline com erro | `docker compose logs logstash`; a carga continua normalmente mesmo assim — o coletor é best-effort (ADR 0001) |
| Logstash registra `Elasticsearch Unreachable` logo após `docker compose up` | O Logstash sobe antes de o Elasticsearch ficar saudável (`depends_on` sem condição de saúde) | Transitório: aguardar `Pipeline started` em `docker compose logs logstash`; eventos emitidos antes disso podem se perder (transporte best-effort) |
| Painel do Kibana vazio ou import falha | Kibana ainda subindo, ou índice `etl-logs-*` sem dados ainda | aguardar o healthcheck do `kibana`; conferir se já existe pelo menos um log via `curl` no Elasticsearch antes de abrir o painel |
