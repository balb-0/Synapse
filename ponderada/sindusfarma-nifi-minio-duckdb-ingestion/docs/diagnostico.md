# Diagnóstico inicial da ingestão

## Objetivo desta etapa

Registrar as descobertas feitas antes de implementar o pipeline. A entrega foi
mantida em uma pasta isolada para não sobrescrever trabalhos existentes do
projeto e facilitar a abertura de um MR próprio.

## Estrutura relevante do repositório

O repositório principal possui uma organização predominantemente documental e
de scripts de validação:

| Caminho | Papel observado |
| --- | --- |
| `docs/` | Documentação principal do projeto, incluindo arquitetura, governança, modelagem quantitativa e evidências. |
| `scripts/analysis/` | Análises quantitativas e notebooks exploratórios. |
| `scripts/data_quality/` | Perfilamento, validações de qualidade, manifesto de fontes e testes. |
| `scripts/dmc/` | Validação do Data Model Canvas. |
| `scripts/governance/` | Validações ligadas à governança. |
| `scripts/traceability/` | Validação de rastreabilidade documental. |
| pasta local de dados | Fontes reais e documentos auxiliares usados apenas no ambiente local. |

Não foi identificada infraestrutura Docker/NiFi no nível raiz do repositório
durante este diagnóstico inicial.

## Dados reais encontrados

Foram identificados seis CSVs reais no ambiente local de desenvolvimento. Para
a entrega versionável, eles devem ser colocados em `local/input/`, pasta
ignorada pelo Git. Todos usam `;` como delimitador, conforme também indicado em
`scripts/data_quality/manifest.json`.

| Dataset | Arquivo | Linhas de dados | Tamanho bruto | SHA-256 |
| --- | --- | ---: | ---: | --- |
| clientes | `clientes.csv` | 5.430 | 393.677 bytes | `5073960065f3ce92a3eab34eeebb38af2b0aaa7e398c862963444a5b608719af` |
| empresas | `empresas.csv` | 779 | 66.691 bytes | `850aaa1840cd24f43c033a0f06d339c9b5186bdaad10f1b653c956e307d3ded5` |
| pesquisas | `pesquisas.csv` | 366 | 132.693 bytes | `b8b5773018953a59d25fabb0875825660efe1723fdd37af58a2d85b46b80e7dc` |
| questoes | `questoes.csv` | 231 | 72.003 bytes | `e2c592898d75d13fd4cc6a5181966707d8c836e7c52ad99ccbaef69b3efbec8f` |
| respondentes | `respondentes.csv` | 18.735 | 411.628 bytes | `cb53e8517e7c43793f14131bd76a792f658c808c034f56da95c3235444afca05` |
| respostas | `respostas.csv` | 20.607 | 1.315.398 bytes | `db4ebd90fdaf203084aff947b50d19a55dab9d0b05b6b692bcbb6eee9f3dd82a` |

O volume total observado com parser CSV é de 46.148 linhas de dados nos seis
arquivos. `pesquisas.csv` contém campos textuais com quebras de linha, então a
contagem por linhas físicas superestima o volume lógico.

## Schemas observados

### `clientes.csv`

```text
id_cliente;id_empresa;cargo;departamento;e-mail
```

Observação: contém e-mail, portanto deve ser tratado como dado pessoal. A
camada raw deve ficar restrita ao ambiente local/MinIO de desenvolvimento, e a
documentação não deve publicar valores de registros.

### `empresas.csv`

```text
ID;Nome Fantasia;% de mercado;Nacionalidade;Associado;Tipo de Associado;Cidade;Estado;Pais
```

Observação: possui baixo volume e menor sensibilidade direta que `clientes`.

### `pesquisas.csv`

```text
id;titulo;status;tipo;area;participantes;part_mercado;data_solicitacao;data_aprov;data_divulgacao;data_limite;prorrogada_ate;data_entrega;dias_uteis_para_entrega;complexidade;tipo de resposta;tempo_preenchimento;objetivos;dia da semana de lancamento;dias uteis aberta;dias entre a solicitacao e a divulgacao;dias para tabulacao
```

Observação: o cabeçalho local possui colunas extras vazias ao final. O pipeline
deve tratar isso de forma explícita ao definir schema.

### `questoes.csv`

```text
id_pergunta;pesquisa_id;pesquisa_titulo;enunciado;tipo;qtd_alternativas;alternativas;linhas_matriz;colunas_matriz;confianca;formato_arquivo;col_origem;observacoes
```

### `respondentes.csv`

```text
id_pesq;hora_inicio;hora_termino;id_empresa;market_share;id_cliente
```

### `respostas.csv`

```text
id_resposta;pesquisa_id;id_pergunta;respondent_id;id_empresa;alternativa;linha_matriz;coluna_matriz;valor
```

Observação: o grão é um elemento atômico de resposta, não um questionário
inteiro. Essa diferença é importante para validações e métricas.

## Escopo implementado

A entrega ficou concentrada na camada raw/bronze:

1. NiFi detecta os CSVs reais em uma pasta de entrada.
2. NiFi calcula SHA-256 do arquivo.
3. NiFi consulta o manifest de ingestão.
4. Arquivo já ingerido com sucesso vira `SKIPPED_ALREADY_INGESTED`.
5. Arquivo novo é armazenado em `raw/` no MinIO.
6. Arquivo válido é convertido para Parquet e armazenado em `bronze/`.
7. DuckDB consulta os Parquets no MinIO para validar contagens, schema, nulos e duplicidades.
8. DuckDB materializa tabelas bronze para consulta estruturada local.
9. Manifest registra status, hash, tamanho, contagens, destino e duração.

Silver/gold não entram no escopo inicial, porque os arquivos são pequenos e a
atividade pede robustez de ingestão, rastreabilidade, idempotência e qualidade
antes de modelagem analítica adicional.

## Organização proposta no MinIO

Bucket usado: `sindusfarma-data`

```text
sindusfarma-data/
  raw/<dataset>/<file_hash>/<arquivo_original>
  bronze/<dataset>/<file_hash>/<dataset>.parquet
  manifests/events/dataset=<dataset>/status=<status>/<evento>.json
  manifests/success_hashes/<dataset>/<file_hash>.json
  rejected/<dataset>/<evento>.json
```

Racional:

- `raw/` preserva o arquivo original.
- `bronze/` contém Parquet com metadados de ingestão.
- `manifests/` permite histórico e idempotência por hash.
- `rejected/` preserva arquivos ou metadados de falha controlada.

## Decisões iniciais

| Tema | Decisão inicial |
| --- | --- |
| Pasta da entrega | `ponderada/sindusfarma-nifi-minio-duckdb-ingestion/` |
| Datasets da entrega | Seis CSVs reais em `local/input/` |
| Estratégia de idempotência | SHA-256 do arquivo completo |
| Formato bronze | Parquet |
| Motor de validação | DuckDB lendo Parquet no MinIO |
| Dados brutos no Git | Não versionar |
| Particionamento | Não particionar inicialmente; volume pequeno e sem ganho claro agora. |

## Arquivos entregues

| Arquivo ou pasta | Finalidade |
| --- | --- |
| `docker-compose.yml` | Subir NiFi e MinIO localmente. |
| `.env.example` | Expor configurações e credenciais fictícias de desenvolvimento. |
| `nifi/flows/` | Guardar o fluxo NiFi versionável. |
| `scripts/ingestion/validate_bronze_all.py` | Validar os Parquets bronze no MinIO com DuckDB. |
| `scripts/ingestion/build_duckdb_warehouse.py` | Criar tabelas bronze em um DuckDB local. |
| `scripts/ingestion/` | Utilitários pequenos para bootstrap, manifest, validação e smoke tests. |
| `docs/architecture.md` | Documentar arquitetura real. |
| `docs/adr-nifi-ingestion.md` | Registrar decisão arquitetural. |
| `docs/execution-results.md` | Registrar evidências reais após execução. |

## Entrada operacional

A pasta `local/input/` é ignorada pelo Git e deve conter os seis CSVs reais
antes da execução. O NiFi acessa essa pasta no container como `/opt/nifi/input`.
