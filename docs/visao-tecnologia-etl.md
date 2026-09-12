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
| Cliente de objetos | `minio` (SDK Python) | `>=7.2,<8` | `requirements.txt` | Em uso |
| HTTP | `urllib3` | `>=2,<3` | `requirements.txt` | Em uso |
| Certificados | `certifi` | `>=2024` | `requirements.txt` | Em uso |
| Orquestração | Prefect | `>=3,<4` | `requirements.txt` | Em uso |
| Banco de ingestão | DuckDB | `>=1.1` | `requirements.txt` | Em uso |
| Ferramenta de bucket | `minio/mc` | `latest` | `docker-compose.yml` | Em uso |
| Testes | `unittest` (biblioteca padrão) | Acompanha o Python | `tests/` | Em uso |
| Cobertura | `coverage` | `==7.16.0` | `requirements-transformation-dev.txt` | Em uso no CI |
| Lint e formatação | `ruff` | `==0.16.6` | `requirements-transformation-dev.txt` | Em uso no CI |
| Integração contínua | GitLab CI | — | `.gitlab-ci.yml` | Em uso |
| Observabilidade | Elastic Stack (Logstash, Elasticsearch, Kibana) | — | [ADR 0001](adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md) | **Decidida, não integrada** |
| Contêineres | Docker e Docker Compose | — | `Dockerfile`, `docker-compose.yml` | Em uso |

O repositório **não tem** `pyproject.toml`, `setup.py` nem `setup.cfg`. O pacote
é resolvido por `PYTHONPATH=src`, definido no `Dockerfile`, no job de CI e nos
comandos de teste.

## Protocolos

| Protocolo | Uso | Onde |
| :--- | :--- | :--- |
| API S3 sobre HTTP | Leitura e escrita de objetos no MinIO | `MinioObjectReader`, scripts de orquestração |
| HTTPS | Derivado do esquema do endpoint; `secure=True` apenas com `https` | `_minio_client` em [`flow.py`](../src/etl/orchestration/flow.py) |
| SQL | Consulta e escrita no banco de ingestão | [`ddl.py`](../src/etl/load/ddl.py), [`duckdb_repository.py`](../src/etl/load/duckdb_repository.py) |
| Webhook HTTP | Notificação `s3:ObjectCreated` do MinIO ao adaptador | **Planejado** (ADR 0001) |
| Cron | Agendamento do deployment | `scripts/orchestration/deployment.py` |

## Formatos

| Formato | Onde aparece |
| :--- | :--- |
| CSV com separador `;`, UTF-8 com BOM | As seis fontes de origem |
| JSON | Log estruturado, serialização de listas na carga e [`dmc.json`](dmc.json) |
| SQL | Contrato físico versionado em `sql/duckdb/001_ingestao_tratada.sql` |
| Cobertura (XML) | Artefato `coverage-transformation.xml` do CI |
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
| Artefato | `coverage-etl.xml`, publicado como relatório Cobertura |

Passos executados, na ordem:

1. `lint`: `pip install -r requirements-transformation-dev.txt`,
   `ruff check src scripts tests` e `ruff format --check src scripts tests`
2. `test`: `pip install -r requirements.txt -r requirements-transformation-dev.txt`,
   `python scripts/transformation/render_schema.py --check`,
   `coverage run --branch --source=etl -m unittest discover -s tests -v`,
   `coverage report --fail-under=85` e `coverage xml -o coverage-etl.xml`

A configuração do `ruff` está em `ruff.toml`:
`target-version = "py312"` e `line-length = 100`. O lint de transformação
legado (`ruff-transformation.toml`) foi absorvido pelo pipeline consolidado.

**Escopo real:** a consolidação da VB-07/VB-08 ampliou o gate: lint cobre
`src`, `scripts` e `tests`, e a cobertura mede todo o pacote `etl` com limite
de 85% — extração, carga e orquestração incluídas.

**Não há Deploy Contínuo.** Nenhum job publica imagem, aplica migração ou promove
versão, em conformidade com a exclusão do enunciado.

## Divergências observadas

Registradas porque a visão precisa refletir os arquivos, inclusive quando eles
discordam entre si.

| Divergência | Declarações conflitantes | Risco |
| :--- | :--- | :--- |
| Versão do Python | resolvida na Sprint 3 (VB-06/VB-07): `Dockerfile`, CI (`python:3.12-slim`), `ruff.toml` (`py312`) e `README.md` (3.12+) alinhados em 3.12 | — |
| Dependências sem pin | `requirements.txt` usa faixas para `minio`, `urllib3`, `prefect` e `duckdb` | Uma atualização de terceiros pode alterar o comportamento sem mudança no repositório |

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
