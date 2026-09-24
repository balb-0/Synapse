# Smoke da orquestração servida — execução, falha e reinício pela interface

Registro da execução de um fluxo pela interface do Prefect Server local, com
falha controlada e reinício bem-sucedido. Comandos executados contra o ambiente
declarado em `docker-compose.yml` (serviços `prefect-server`, `scheduler`,
`runner`, `minio`). A UI vive em http://localhost:4200 (runs, deployments e
parâmetros); abaixo, os mesmos dados via CLI/API para reprodutibilidade.

## 1. Servidor, UI e deployment agendado

```bash
docker compose up -d --build
curl http://localhost:4200/api/health
# true
docker compose exec runner prefect deployment ls
# ingest-object/agendado
```

A UI lista o flow `ingest-object`, as tasks separadas (`extract`, `transform`,
`load`) e conserva o histórico após o término (seção 4). O deployment
`ingest-object/agendado` (cron `0 3 * * *`) cria runs `SCHEDULED` com os
parâmetros registrados.

## 2. Execução por evento (sucesso)

```bash
docker compose exec runner python scripts/orchestration/run_ingest.py --source empresas
# RESULTADO: {'status': 'loaded', 'source': 'empresas',
#   'reconciliation': [{'extracted': 3, 'loaded': 3, 'rejected': 0,
#   'duplicates': 0, 'balanced': True}]}
```

Reenvio do mesmo objeto (disparo repetido): `{'status': 'ignored', ...}` —
mesmo checksum, sem nova carga e sem duplicar.

Disparo pelo adaptador de chegada de objeto:

```bash
docker compose exec runner python scripts/orchestration/watch_landing.py --once
# [watch] s3://sindusfarma/landing/empresas.csv fonte=empresas -> ignored
# [watch] ignorada (fora do padrão <fonte>.csv): landing/recuperado.csv
```

## 3. Falha controlada

Objeto inexistente (falha permanente: sem retry, estado `Failed` no histórico):

```bash
docker compose exec runner python -c "...ingest_object(source='empresas', bucket='sindusfarma', key='landing/inexistente.csv')"
# S3Error: NoSuchKey ... landing/inexistente.csv
# Finished in state Failed(...)
```

Arquivo malformado (linha com campos a mais): `MalformedSourceError ...
linha 5`, também `Failed` sem retry — falha de dado não se repete.

## 4. Reinício bem-sucedido (reexecução parametrizada)

Reexecução com o objeto corrigido (mesma fonte, novo conteúdo):

```bash
docker compose exec runner python scripts/orchestration/run_ingest.py \
  --source empresas --key landing/recuperado.csv --fixture /tmp/rec.csv
# RESULTADO: {'status': 'loaded', ...
#   'reconciliation': [{'extracted': 4, 'loaded': 1, 'rejected': 0,
#   'duplicates': 3, 'balanced': True}]}
```

Só a linha nova foi carregada (`loaded: 1`); as 3 já confirmadas voltaram
como `duplicates: 3` — reinício sem perder nem duplicar registro confirmado.

## 5. Histórico na interface (runs e parâmetros)

`POST /api/flow_runs/filter` contra o servidor (o que a UI em
http://localhost:4200 mostra em Runs):

| Run | Estado | Parâmetros |
| :--- | :--- | :--- |
| `spry-skua` | COMPLETED | `source=empresas, key=landing/empresas.csv` |
| (reenvio) | COMPLETED | `status: ignored`, mesmo checksum |
| `certain-vole` | FAILED | `key=landing/inexistente.csv` (NoSuchKey) |
| (recuperado) | COMPLETED | `key=landing/recuperado.csv`, `loaded: 1, duplicates: 3` |
| `zealous-marten`, `cordial-snail`, ... | SCHEDULED | `key=landing/empresas.csv` (deployment `agendado`) |

## 6. Agendamento sobrevive ao reinício

```bash
docker compose restart scheduler
docker compose exec runner prefect deployment ls
# ingest-object/agendado   (mesmo ID de antes do restart)
# runs SCHEDULED preservados, com os parâmetros de cada execução
```

Agendamentos e histórico vivem no `prefect-server` (volume `prefect-data`),
não no processo que serve o deployment — derrubar e subir o ambiente
preserva ambos.
