# Resultados de execução

Ambiente local executado em Docker Compose:

| Item | Valor |
| --- | --- |
| NiFi | 1.27.0 |
| MinIO bucket | `sindusfarma-data` |
| Fluxo | `01_SINDUSFARMA_RAW_BRONZE` |
| Warehouse local | `local/warehouse/sindusfarma.duckdb` |
| Processors/conexões | 94 / 148 |
| Validação NiFi | 0 processors inválidos |

## Dados processados

| Dataset | Arquivos | Linhas origem | Linhas destino | Tamanho origem | Bytes Parquet comprimidos | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| clientes | 1 | 5.430 | 5.430 | 393.677 | 85.900 | SUCCESS |
| empresas | 1 | 779 | 779 | 66.691 | 11.589 | SUCCESS |
| pesquisas | 1 | 366 | 366 | 132.693 | 51.685 | SUCCESS |
| questoes | 1 | 231 | 231 | 72.003 | 24.101 | SUCCESS |
| respondentes | 1 | 18.735 | 18.735 | 411.628 | 109.696 | SUCCESS |
| respostas | 1 | 20.607 | 20.607 | 1.315.398 | 172.519 | SUCCESS |
| **Total** | **6** | **46.148** | **46.148** | **2.392.090** | **455.490** | SUCCESS |

## Hashes

| Dataset | SHA-256 |
| --- | --- |
| clientes | `5073960065f3ce92a3eab34eeebb38af2b0aaa7e398c862963444a5b608719af` |
| empresas | `850aaa1840cd24f43c033a0f06d339c9b5186bdaad10f1b653c956e307d3ded5` |
| pesquisas | `b8b5773018953a59d25fabb0875825660efe1723fdd37af58a2d85b46b80e7dc` |
| questoes | `e2c592898d75d13fd4cc6a5181966707d8c836e7c52ad99ccbaef69b3efbec8f` |
| respondentes | `cb53e8517e7c43793f14131bd76a792f658c808c034f56da95c3235444afca05` |
| respostas | `db4ebd90fdaf203084aff947b50d19a55dab9d0b05b6b692bcbb6eee9f3dd82a` |

## Execução inicial

Comando:

```powershell
python -u scripts\ingestion\bootstrap_nifi_all_datasets.py --reset --clear-listing-state --start --timeout-seconds 300
```

Resultado NiFi observado:

| Métrica | Valor |
| --- | ---: |
| FlowFiles transferidos | 132 |
| Fila final | 0 |
| Bytes lidos | 7.666.700 |
| Bytes escritos | 2.876.367 |

## Idempotência

Reexecução com os mesmos arquivos:

```powershell
python -u scripts\ingestion\bootstrap_nifi_all_datasets.py --clear-listing-state --start --timeout-seconds 240
```

Resultado final observado:

| Check | Resultado |
| --- | --- |
| Bronze após reexecução | 46.148 linhas |
| Duplicação de dados | Não houve |
| Markers de sucesso | 1 por dataset |
| Eventos SUCCESS | 1 por dataset |
| Eventos SKIPPED_ALREADY_INGESTED | 2 por dataset |

Os dois eventos de skip existem porque a idempotência foi executada duas vezes
durante a validação final do fluxo.

## Qualidade

Comando:

```powershell
python scripts\ingestion\validate_bronze_all.py
```

Resultado:

| Check | Resultado |
| --- | --- |
| Contagem origem = destino | true |
| Schemas bronze esperados | true |
| Duplicidade em chaves avaliadas | 0 em todos os datasets |
| Chaves nulas/vazias | 856 em `respondentes`; 0 nos demais |

As 856 ocorrências em `respondentes` indicam lacunas em ao menos uma parte da
chave composta `id_pesq, id_empresa, id_cliente`. O pipeline preserva os dados
na bronze e registra o achado para tratamento em camada posterior.

## Tabelas DuckDB

Comando:

```powershell
python scripts\ingestion\build_duckdb_warehouse.py
```

Resultado: 6 tabelas criadas no schema `bronze`, todas com contagem igual aos
CSV reais.

| Tabela | Linhas |
| --- | ---: |
| `bronze.clientes` | 5.430 |
| `bronze.empresas` | 779 |
| `bronze.pesquisas` | 366 |
| `bronze.questoes` | 231 |
| `bronze.respondentes` | 18.735 |
| `bronze.respostas` | 20.607 |

## Falha controlada

Comando:

```powershell
python scripts\ingestion\run_failure_control.py --output local\evidence\failure-control.json
```

Resultado: `VALIDATION_FAILED` por `schema_header_mismatch` em um CSV temporário
de teste, sem alterar os dados reais. O flow NiFi final também possui rota de
falhas para `rejected/<dataset>/...json` antes do `LogAttribute`.

## Performance

Comando:

```powershell
python scripts\ingestion\compare_storage_formats.py
```

| Dataset | Leitura CSV ms | Leitura Parquet ms |
| --- | ---: | ---: |
| clientes | 121,942 | 56,569 |
| empresas | 55,292 | 40,027 |
| pesquisas | 24,559 | 51,716 |
| questoes | 29,889 | 35,858 |
| respondentes | 99,211 | 37,154 |
| respostas | 110,196 | 35,150 |

Nos arquivos maiores, Parquet no MinIO foi mais rápido e muito menor em bytes
comprimidos. Nos datasets pequenos, o overhead de acessar S3 local pode superar
o ganho do formato colunar.

## Rubrica

| Critério | Evidência |
| --- | --- |
| 1. Dados e fluxo | Diagnóstico dos seis CSVs reais, schemas Avro, layout raw/bronze e tabelas DuckDB. |
| 2. Métricas e qualidade | Contagem, hashes, duplicidades, nulos, schema e manifest por status. |
| 3. Eficiência | Parquet Snappy, idempotência por hash, markers e reprocessamento controlado. |
| 4. Design/documentação | README, Mermaid, ADR, flow JSON versionado e comandos testados. |
| 5. Análise dos resultados | Comparação CSV vs Parquet, comportamento idempotente e achados de qualidade. |
