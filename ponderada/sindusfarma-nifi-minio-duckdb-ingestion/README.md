# Pipeline de ingestão Sindusfarma com NiFi, MinIO, Parquet e DuckDB

Entrega individual para ingestão raw/bronze dos dados reais da Central de
Pesquisas Sindusfarma. O diferencial desta proposta é usar Apache NiFi como
plano de controle operacional: descoberta dos arquivos, leitura, hash SHA-256,
checagem de idempotência, conversão para Parquet, escrita no MinIO e registro
de manifest.

## Componentes

| Componente | Papel |
| --- | --- |
| NiFi 1.27.0 | Orquestra o fluxo de ingestão e falhas. |
| MinIO | Object storage S3 local, bucket `sindusfarma-data`. |
| Parquet/Snappy | Formato bronze colunar. |
| DuckDB | Warehouse analítico local, com tabelas bronze materializadas a partir dos Parquets no MinIO. |
| Manifest JSON | Histórico de `SUCCESS` e `SKIPPED_ALREADY_INGESTED`. |

## Dados reais

Os CSVs reais não são versionados. Para executar localmente, coloque estes seis
arquivos em `local/input/`, pasta ignorada pelo Git:

```text
local/input/
  clientes.csv
  empresas.csv
  pesquisas.csv
  questoes.csv
  respondentes.csv
  respostas.csv
```

O Docker Compose monta `local/input/` como `/opt/nifi/input` no container do
NiFi.

Datasets processados: `clientes`, `empresas`, `pesquisas`, `questoes`,
`respondentes` e `respostas`.

Nesta entrega, o DuckDB faz o papel de warehouse local para validação e
consulta. Ele não substitui o NiFi na ingestão: as tabelas do schema `bronze`
são materializadas depois que o NiFi escreve os Parquets no MinIO.

## Subir o ambiente

```powershell
cd ponderada\sindusfarma-nifi-minio-duckdb-ingestion
copy .env.example .env
New-Item -ItemType Directory -Force local\input
docker compose up -d
docker compose ps
```

Acessos locais:

| Serviço | URL |
| --- | --- |
| NiFi | `http://localhost:8080/nifi` |
| MinIO Console | `http://localhost:19001` |
| MinIO API | `http://localhost:19000` |

Credenciais de desenvolvimento ficam no `.env`, que está ignorado pelo Git.

## Criar/importar o fluxo

O fluxo versionado está em:

```text
nifi/flows/01_SINDUSFARMA_RAW_BRONZE.json
```

Para recriar pela API local do NiFi:

```powershell
python scripts\ingestion\bootstrap_nifi_all_datasets.py --reset
```

Para executar a ingestão inicial ou uma reexecução controlada:

```powershell
python -u scripts\ingestion\bootstrap_nifi_all_datasets.py --clear-listing-state --start --timeout-seconds 300
```

`--clear-listing-state` limpa o estado dos processors `ListFile`. Isso é
necessário para demonstrar reprocessamento/idempotência sobre os mesmos nomes
de arquivo, pois o `ListFile` do NiFi evita relistar arquivos já vistos.

Para criar as tabelas bronze no DuckDB local:

```powershell
python scripts\ingestion\build_duckdb_warehouse.py
```

O arquivo `local/warehouse/sindusfarma.duckdb` é gerado localmente e não entra
no Git.

## Layout no MinIO

```text
sindusfarma-data/
  raw/<dataset>/<file_hash>/<arquivo>.csv
  bronze/<dataset>/<file_hash>/<dataset>.parquet
  manifests/events/dataset=<dataset>/status=<status>/<evento>.json
  manifests/success_hashes/<dataset>/<file_hash>.json
  rejected/<dataset>/<evento>.json
```

Se o hash já existe em `manifests/success_hashes/`, o arquivo segue para
`SKIPPED_ALREADY_INGESTED` e não regrava raw/bronze.

## Validações

Com os seis CSVs em `local/input/`, rode o perfil dos arquivos de origem e a
comparação CSV vs Parquet:

```powershell
python scripts\ingestion\profile_sources.py
python scripts\ingestion\compare_storage_formats.py
```

Depois da ingestão, rode as validações sobre MinIO e DuckDB:

```powershell
python scripts\ingestion\validate_bronze_all.py
python scripts\ingestion\validate_manifest_all.py
python scripts\ingestion\build_duckdb_warehouse.py
python scripts\ingestion\run_failure_control.py --output local\evidence\failure-control.json
python -m unittest scripts.ingestion.test_ingestion_helpers
```

## Operação

Para reprocessar um arquivo sem duplicar dados, mantenha o marker em
`manifests/success_hashes/` e rode o bootstrap com `--clear-listing-state`.
O resultado esperado é um novo evento `SKIPPED_ALREADY_INGESTED`.

Para forçar uma nova carga de um arquivo alterado, o conteúdo precisa mudar.
Como o hash será outro, o pipeline grava uma nova versão em `raw/<dataset>/<hash>/`
e `bronze/<dataset>/<hash>/`.

Para investigar erro, confira no NiFi a fila de falha, os boletins do processor
e os objetos em `rejected/`. O teste local `run_failure_control.py` cobre o caso
de schema inesperado sem alterar os CSVs reais.

## Evidências

Os resultados reais da execução ficam em:

- `docs/diagnostico.md`
- `docs/architecture.md`
- `docs/adr-nifi-ingestion.md`
- `docs/execution-results.md`

## Limites atuais

- A camada implementada é raw/bronze; silver/gold não foram criadas para não
  inventar modelagem fora do escopo da ingestão.
- O manifest é composto por arquivos JSON append-only no MinIO, com markers por
  hash. Para concorrência alta, o próximo passo seria uma tabela transacional
  ou catálogo com controle de lock.
- A rota `FetchS3Object` usa `failure` do marker como sinal de arquivo novo
  quando o objeto ainda não existe; falhas de S3 diferentes de 404 exigiriam
  tratamento mais refinado em produção.
