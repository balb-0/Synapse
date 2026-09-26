# Visão de Tecnologia do ETL (ISO/IEC 10746) — AN-08

Inventário das tecnologias, versões, protocolos e ferramentas do pipeline, lido
diretamente dos arquivos de dependência, do ambiente em contêiner e da
configuração de integração contínua. Cada linha aponta o arquivo onde a escolha
está declarada, para que a visão possa ser conferida sem depender deste texto.

As decisões que justificam cada escolha estão em
[`adrs/index.md`](adrs/index.md). Onde o enunciado cita ClickHouse, o alvo é o
**DuckDB**, conforme o
[ADR 0001](adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md).

## Pilha adotada

| Camada | Tecnologia | Versão declarada | Onde está declarada | Estado |
| :--- | :--- | :--- | :--- | :--- |
| Linguagem | Python | `python:3.12-slim` | `Dockerfile` | Em uso |
| Armazenamento de objetos | MinIO (servidor) | `minio/minio:latest` | `docker-compose.yml` | Em uso |
| Cliente de objetos | `minio` (SDK Python) | `==7.2.20` | `requirements.txt` | Em uso |
| HTTP | `urllib3` | `==2.7.0` | `requirements.txt` | Em uso |
| Certificados | `certifi` | `==2026.07.22` | `requirements.txt` | Em uso |
| Orquestração | Prefect | `==3.8.5` | `requirements.txt` | Em uso |
| Banco de ingestão | DuckDB | `==1.5.5` | `requirements.txt` | Em uso |
| Ferramenta de bucket | `minio/mc` | `latest` | `docker-compose.yml` | Em uso |
| Testes | `unittest` (biblioteca padrão) | Acompanha o Python | `tests/` | Em uso |
| Cobertura | `coverage` | `==7.16.0` | `requirements-transformation-dev.txt` | Em uso no CI |
| Lint e formatação | `ruff` | `==0.16.6` | `requirements-transformation-dev.txt` | Em uso no CI |
| Relatório de testes | `unittest-xml-reporting` (xmlrunner) | `==3.2.0` | `requirements-transformation-dev.txt` | Em uso no CI |
| Integração contínua | GitLab CI | — | `.gitlab-ci.yml` | Em uso |
| Observabilidade — coletor | Logstash + Elasticsearch | `8.15.0` | `docker-compose.yml`, `observability/logstash/pipeline/etl.conf` | Em uso (OB-07) |
| Observabilidade — painel | Kibana | `8.15.0` | `docker-compose.yml`, `observability/kibana/painel-operacional.ndjson` | Em uso (OB-08) |
| Contêineres | Docker e Docker Compose | — | `Dockerfile`, `docker-compose.yml` | Em uso |

O repositório **não tem** `pyproject.toml`, `setup.py` nem `setup.cfg`. O pacote
é resolvido por `PYTHONPATH=src`, definido no `Dockerfile`, no job de CI e nos
comandos de teste.

### Fonte canônica e política de versões

| Categoria | Fonte canônica | Política observada | Reprodutibilidade |
| :--- | :--- | :--- | :--- |
| Runtime Python | `Dockerfile` e `.gitlab-ci.yml` | imagem `python:3.12-slim` | Versão menor fixa; digest da imagem não fixado |
| Bibliotecas de execução | `requirements.txt` | versões exatas (`==`) | Mesmas versões no CI e no runner |
| Ferramentas de qualidade | `requirements-transformation-dev.txt` | `coverage==7.16.0`, `ruff==0.16.6` | Versões exatas |
| Serviços MinIO | `docker-compose.yml` | tags `latest` | Não reprodutível por versão |
| Elastic Stack | `docker-compose.yml` | `8.15.0` | Versão exata |

O card OQ-09 fixou as dependências de execução com `==` em `requirements.txt`;
o validador `scripts/architecture/validate_architecture_docs.py`, executado no
CI, falha se uma versão desta visão divergir do arquivo. As imagens do MinIO
continuam em `latest` e são o único ponto não fixado da pilha.

## Protocolos

| Protocolo | Uso | Onde |
| :--- | :--- | :--- |
| API S3 sobre HTTP | Leitura e escrita de objetos no MinIO | `MinioObjectReader`, scripts de orquestração |
| HTTPS | Derivado do esquema do endpoint; `secure=True` apenas com `https` | `_minio_client` em [`flow.py`](../src/etl/orchestration/flow.py) |
| SQL | Consulta e escrita no banco de ingestão | [`ddl.py`](../src/etl/load/ddl.py), [`duckdb_repository.py`](../src/etl/load/duckdb_repository.py) |
| Webhook HTTP | Notificação `s3:ObjectCreated` do MinIO ao adaptador | `scripts/orchestration/watch_landing.py` |
| GELF sobre UDP | Envio do stdout JSON dos contêineres ao Logstash | driver `gelf` no `docker-compose.yml` |
| HTTP (API Prefect) | Estados, logs e health check `/api/health` | `prefect-server`, `etl.orchestration.health` |
| Cron | Agendamento do deployment | `scripts/orchestration/deployment.py` |

### Padrão de observabilidade ratificado

O padrão separa produção de sinais, transporte e consumo. Eventos de extração,
transformação, carga e orquestração usam logging JSON com correlação por
`run_id`, `task_id`, `batch_id` e `source`, sem registros de negócio ou
segredos (ADR 0006 e 0008). Métricas de tempo, volume, status, retry,
latência e disponibilidade são campos desses eventos, agregados no Kibana; a
escolha da Elastic Stack em vez de Prometheus/OpenTelemetry está justificada no
ADR 0001 e ratificada no ADR 0008.

| Camada | Tecnologia/contrato | Situação verificável |
| :--- | :--- | :--- |
| Produção | `logging` Python, `ExtractionBatchLogEvent`, `TransformationBatchLogEvent`, `LoadBatchLogEvent`, marcos `orchestration.*`, estados Prefect | Implementada |
| Serialização | JSON (`etl.orchestration.logging_config`, `observability/prefect-logging.yml`) | Implementada nas quatro etapas |
| Transporte | stdout → driver GELF → Logstash (`observability/logstash/pipeline/etl.conf`) | Implementado no `docker-compose.yml` |
| Armazenamento | Elasticsearch, índice `etl-logs-*` | Implementado |
| Consulta e painel | Kibana, `observability/kibana/painel-operacional.ndjson` | Implementado |
| Alertas | regras "falha de execução" e "fila parada" sobre `etl-logs-*` | Especificadas no runbook; criadas manualmente no Kibana |

O ambiente é local: a Elastic Stack roda sem autenticação e sem política de
retenção, e não há implantação em produção nem Deploy Contínuo.

## Formatos

| Formato | Onde aparece |
| :--- | :--- |
| CSV com separador `;`, UTF-8 com BOM | As seis fontes de origem |
| JSON | Log estruturado, serialização de listas na carga e [`dmc.json`](dmc.json) |
| SQL | Contrato físico versionado em `sql/duckdb/001_ingestao_tratada.sql` |
| Cobertura (XML) | Artefato `coverage-etl.xml` do CI (Cobertura) |
| JUnit (XML) | Artefato `test-reports/*.xml` do CI (`reports:junit`) |
| Parquet | Geração publicada dos cubos (`PUB_*.parquet`) e `manifest.json` |
| TMDL/PBIR | Modelo semântico e relatório Power BI versionados |
| PlantUML e Mermaid | Diagramas em [`assets/uml/`](assets/uml/) e embutidos nas visões |

## Integração contínua

`.gitlab-ci.yml` declara o pipeline consolidado (VB-07/VB-08) em dois
estágios.

| Atributo | Valor |
| :--- | :--- |
| Jobs | `lint` (estágio `lint`) e `test` (estágio `test`) |
| Imagem | `python:3.12-slim` |
| Variáveis | `PYTHONPATH: src`, `PIP_DISABLE_PIP_VERSION_CHECK: "1"` |
| Gatilhos | Eventos de merge request e qualquer branch com commit |
| Artefato | `coverage-etl.xml` (relatório Cobertura) e `test-reports/` (relatório JUnit por caso de teste) |
| Bloqueio | Qualquer falha de lint, formatação, validação, teste ou cobertura abaixo de 85% reprova o job |

Passos executados, na ordem:

1. `lint`: `pip install -r requirements-transformation-dev.txt`,
   `ruff check src scripts tests` e `ruff format --check src scripts tests`
2. `test`: `pip install -r requirements.txt -r requirements-transformation-dev.txt`,
   `python scripts/architecture/validate_architecture_docs.py`,
   `python scripts/transformation/render_schema.py --check`,
   `coverage run --branch --source=etl -m xmlrunner discover -s tests -o test-reports -v`,
   `coverage report --fail-under=85` e `coverage xml -o coverage-etl.xml`

O `ruff` cumpre o papel de análise estática que o enunciado exemplifica com
flake8/pylint: aplica as regras do pyflakes (`F`), os erros de sintaxe e de
comando do pycodestyle (`E4`, `E7`, `E9`) e a ordenação de imports (`I`) num
único binário, mais rápido e com formatação
integrada. A configuração do `ruff` está em `ruff.toml`:
`target-version = "py312"` e `line-length = 100`. O lint de transformação
legado (`ruff-transformation.toml`) foi absorvido pelo pipeline consolidado.

**Escopo real:** a consolidação da VB-07/VB-08 ampliou o gate: lint cobre
`src`, `scripts` e `tests`, e a cobertura mede todo o pacote `etl` com limite
de 85% — extração, carga e orquestração incluídas.

**Não há Deploy Contínuo.** Nenhum job publica imagem, aplica migração ou promove
versão, em conformidade com a exclusão do enunciado.

### Artefatos tecnológicos verificáveis

| Artefato | Produtor | Consumidor | Retenção/publicação |
| :--- | :--- | :--- | :--- |
| `coverage-etl.xml` | job `test` | relatório de cobertura do GitLab | artefato do pipeline |
| DDL de ingestão | `scripts/load/render_ddl.py` | DuckDB e revisão de schema | versionado em `sql/duckdb/` |
| Logs JSON de lote | sinks padrão do ETL | stdout e futuro coletor | sem retenção central configurada |
| Histórico de flow runs | Prefect servido | operador pela UI/CLI | depende da persistência do servidor |
| Imagens Docker | build local/CI | runner ETL | não publicadas por este pipeline |

O gate automatiza lint, testes, schema e cobertura. Ele não valida preço de
infraestrutura, disponibilidade do servidor, retenção de logs nem promoção para
produção; esses limites pertencem ao runbook e à estimativa de custos.

## Divergências observadas

Registradas porque a visão precisa refletir os arquivos, inclusive quando eles
discordam entre si.

| Divergência | Declarações conflitantes | Risco |
| :--- | :--- | :--- |
| Versão do Python | resolvida na Sprint 3 (VB-06/VB-07): `Dockerfile`, CI (`python:3.12-slim`), `ruff.toml` (`py312`) e `README.md` (3.12+) alinhados em 3.12 | — |
| Dependências sem pin | resolvida: `requirements.txt` fixa `minio`, `urllib3`, `certifi`, `prefect` e `duckdb` com `==` | — |

## Tecnologias consideradas e não adotadas

| Tecnologia | Papel avaliado | Decisão |
| :--- | :--- | :--- |
| ClickHouse | Banco de ingestão | Substituído por DuckDB, com autorização registrada no ADR 0001 |
| Apache NiFi | Dataflow e coordenação | Fora da arquitetura principal; reavaliável se as fontes se diversificarem. Não adotado na arquitetura principal |
| Apache Airflow | Orquestração | Não selecionado; o Prefect foi escolhido no ADR 0001 |
| Prometheus e Grafana | Observabilidade | Não selecionados; a orientação da sprint direcionou à Elastic Stack |
| `pytest` | Testes | Não adotado; a suíte usa `unittest` e o CI o invoca diretamente |
| GitHub Actions | Integração contínua | Não aplicável: o repositório é hospedado no GitLab |

## Custos

O ADR 0001 exige um documento versionado de estimativa de custos, com cenário
acadêmico local e cenário hospedado, separando processamento, armazenamento de
objetos, banco de ingestão, execução do orquestrador, Elastic Stack,
transferência e retenção. **Esse documento ainda não existe.** Todo o software
listado aqui é livre de licença, o que não equivale a infraestrutura sem custo.
