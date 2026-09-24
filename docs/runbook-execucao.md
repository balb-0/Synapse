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
- `runner`: contêiner Python com Prefect e DuckDB (`Dockerfile`), com `src/` e
  `scripts/` montados; permanece ativo (`sleep infinity`) para executar comandos.
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
mapeamento de campos dos eventos. Não foi possível confirmar a importação
num Kibana real neste ambiente (Docker indisponível no WSL2 usado no
desenvolvimento) — ver a MR do OB-08 para o detalhe do que foi e não foi
validado. Para importar, com a stack no ar:

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
docker compose exec runner python scripts/orchestration/health_check.py
```

Sai com código 1 se qualquer checagem falhar, e publica um evento
`orchestration.health_check.emitted` no índice `etl-logs-*` (mesmo formato
técnico das demais camadas, ADR 0001) — consultável no painel do OB-08 e
usado pelo alerta de falha abaixo. A checagem do Prefect depende da variável
`PREFECT_API_URL` (o mesmo nome de variável que o próprio Prefect lê); sem
ela configurada, a checagem falha explicitamente em vez de tentar adivinhar
um endereço.

O servidor Prefect publicado em OQ-03 roda no host (`prefect server start` +
`prefect deploy --all`, fora do Compose — ver card #235), não como serviço
deste `docker-compose.yml`. Rodando `health_check.py` **dentro** do
container `runner`, `PREFECT_API_URL=http://localhost:4200/api` aponta para
o próprio container, não para o host — usar
`http://host.docker.internal:4200/api` (o runner já sai por essa rede, mesma
observação de resolução de nome feita para o `gelf-address` do Logstash na
MR do OB-07). Rodando o script fora do container (ambiente local sem
Docker), `localhost:4200` funciona normalmente.

### Alertas mínimos (Kibana Alerting, OB-09)

O schema de saved object de uma regra de alerta do Kibana (`type: "alert"`)
muda com mais frequência entre versões do que o de dashboard/visualização
(OB-08) e não há como confirmar a importação neste ambiente (Docker
indisponível). Uma regra de alerta mal formada falha silenciosamente — pior
do que simplesmente não existir — por isso as duas regras mínimas abaixo
ficam documentadas para criação manual em **Stack Management → Rules →
Create rule → Elasticsearch query**, em vez de um NDJSON não verificável:

| Regra | Índice | Campo de tempo | Consulta (KQL) | Condição | Janela | Frequência |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ETL - falha de execução | `etl-logs-*` | `@timestamp` | `tags: "_jsonparsefailure" or (event: "orchestration.health_check.emitted" and status: "degraded")` | contagem **acima de** 0 | últimos 5 min | a cada 1 min |
| ETL - fila parada | `etl-logs-*` | `@timestamp` | `stage: "orchestration"` | contagem **abaixo de** 1 | últimas 26 h | a cada 30 min |

A primeira regra cobre tanto uma falha real do pipeline (traceback do Python
vazando pro stdout, capturado pelo Logstash com a tag `_jsonparsefailure` —
ver `observability/logstash/pipeline/etl.conf`) quanto uma falha detectada
pelo próprio health check acima. A segunda cobre o deployment agendado
parar de rodar (cron diário às 03:00, `scripts/orchestration/deployment.py`)
— 26h dá margem sobre as 24h de intervalo esperado. Nenhuma das duas precisa
de uma action/connector configurada para "disparar alerta visível": o
estado da regra já aparece em **Alerts** no Kibana quando ativa.

Verificar o banco de ingestão local (cria o arquivo se não existir e roda
consulta smoke + verificação de persistência):

```bash
PYTHONPATH=src python scripts/load/duckdb_env.py
```

## Executar o pipeline

Ingestão de uma fonte (semeia o fixture no MinIO e roda o flow `ingest-object`):

```bash
docker compose exec runner python scripts/orchestration/run_ingest.py --source empresas
```

- Fontes válidas: `pesquisas`, `empresas`, `clientes`, `respondentes`,
  `questoes`, `respostas`. O fixture de orquestração versionado em
  `scripts/orchestration/fixtures/` cobre apenas `empresas` (há também
  `empresas_malformada.csv` para o cenário de rejeição); para as demais fontes,
  aponte um arquivo com `--fixture` (e `--key` para o destino). As seis
  fixtures sintéticas completas existem em `tests/fixtures/` e servem aos
  testes, não ao `run_ingest.py`.
- Rodar o mesmo comando duas vezes demonstra a idempotência: a segunda
  execução retorna `status: ignored` (objeto já concluído, controle por hash
  SHA-256 em `_control_object`).

Backfill controlado de várias fontes, com parâmetros registrados no histórico
do run:

```bash
docker compose exec runner python scripts/orchestration/run_backfill.py --sources empresas pesquisas
docker compose exec runner python scripts/orchestration/run_backfill.py --sources empresas --reprocess
```

`--reprocess` ignora o controle de idempotência por objeto; a deduplicação por
linha (ADR
[`adrs/0002-identidade-e-versoes-na-tabela-de-ingestao.md`](adrs/0002-identidade-e-versoes-na-tabela-de-ingestao.md))
continua impedindo duplicatas.

## Orquestração Prefect

- Flows em `src/etl/orchestration/flow.py`: `ingest-object` (um objeto:
  verificação de idempotência → extração → transformação → carga →
  reconciliação) e `backfill` (subflows por fonte).
- Retry: a tarefa `extract` tem `retries=2` com condição (`_should_retry`) —
  só repete erro inesperado; falha permanente (credencial, schema, objeto
  ausente) ou limite interno de retry já esgotado falham rápido. Falhas
  transitórias de leitura são reexecutadas dentro da extração
  (`RetryExecutor`, configurável por `ETL_EXTRACTION_*`).
- Deployment agendado: `python scripts/orchestration/deployment.py` serve o
  deployment `ingest-object/agendado` (cron `0 3 * * *`). Execução manual com
  parâmetros explícitos:

  ```bash
  prefect deployment run 'ingest-object/agendado' -p source=empresas \
      -p bucket=sindusfarma -p key=landing/empresas.csv -p reprocess=true
  ```

## Logs e observabilidade

- Cada tarefa loga via `get_run_logger()` do Prefect (nível configurável por
  `PREFECT_LOGGING_LEVEL`, `INFO` no runner): contagens de lotes, aceitos e o
  resumo de reconciliação por lote.
- A extração emite eventos estruturados por lote
  (`src/etl/extraction/log_events.py`) — metadados técnicos (execução, fonte,
  lote, contagens), sem conteúdo dos registros.
- A reconciliação por lote é gravada na tabela `_batch_metadata` e validada na
  carga: `carregados + rejeitados + duplicados` precisa fechar com o extraído
  (ver [`ddl-ingestao.md`](ddl-ingestao.md)).

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

Suíte `unittest` em `tests/` (216 testes em 11/09/2026), organizada por camada
(`extraction`, `transformation`, `load`, `orchestration`, `e2e`, `fixtures`).
Testes que dependem de `duckdb` ou
`minio` são pulados quando a dependência não está instalada; o contrato `tests/transformation/test_duckdb_contract.py` valida os seis schemas em um DuckDB real. Estratégia completa:
[`estrategia-de-testes.md`](estrategia-de-testes.md).

## Integração contínua

O pipeline consolidado do GitLab (`.gitlab-ci.yml`, imagem `python:3.12-slim`)
roda em merge requests e pushes, em dois estágios:

1. `lint`: `ruff check` e `ruff format --check` (`ruff.toml`) sobre `src`,
   `scripts` e `tests`;
2. `test`: `python scripts/transformation/render_schema.py --check` (schema de
   destino versionado íntegro), suíte inteira via
   `coverage run --branch --source=etl -m unittest discover -s tests -v` e
   `coverage report --fail-under=85` sobre todo o pacote `etl`, publicando o
   relatório Cobertura (`coverage-etl.xml`) como artefato.

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
| Execução morreu no meio | falha entre extração e carga | reexecute o mesmo comando: o `_checkpoint` retoma da posição confirmada do mesmo objeto; checkpoint de outra versão é descartado |
| Falha transitória de leitura | timeout/instabilidade do MinIO | a extração já retenta (`ETL_EXTRACTION_MAX_ATTEMPTS`); o Prefect retenta só erro inesperado (`retries=2` na task `extract`) |
| `DDL_DESATUALIZADA` no CI | contrato físico mudou sem regerar o SQL | `python scripts/load/render_ddl.py` e commitar `sql/duckdb/001_ingestao_tratada.sql` |
| Nenhum log aparece no Elasticsearch | Logstash/Elasticsearch ainda subindo, ou pipeline com erro | `docker compose logs logstash`; a carga continua normalmente mesmo assim — o coletor é best-effort (ADR 0001) |
| Painel do Kibana vazio ou import falha | Kibana ainda subindo, ou índice `etl-logs-*` sem dados ainda | aguardar o healthcheck do `kibana`; conferir se já existe pelo menos um log via `curl` no Elasticsearch antes de abrir o painel |
