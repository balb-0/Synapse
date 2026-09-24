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
- Docker e Docker Compose (ambiente local com MinIO e runner)
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
- `prefect-server`: backend persistente do Prefect com UI de pipelines em
  http://localhost:4200 e health check em http://localhost:4200/api/health
  (volume `prefect-data`: agendamentos e histórico sobrevivem a
  `docker compose down/up`).
- `scheduler`: serve o deployment `ingest-object/agendado` (cron `0 3 * * *`)
  e reinicia sozinho (`restart: unless-stopped`).
- `runner`: contêiner Python com Prefect e DuckDB (`Dockerfile`), com `src/` e
  `scripts/` montados; permanece ativo (`sleep infinity`) para executar comandos.

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
