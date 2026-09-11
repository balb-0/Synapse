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
| Integração contínua | GitLab CI | — | `.gitlab-ci.yml`, `.gitlab/ci/transformation.yml` | Em uso, escopo parcial |
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
| Cobertura Cobertura (XML) | Artefato `coverage-transformation.xml` do CI |
| PlantUML e Mermaid | Diagramas em [`assets/uml/`](assets/uml/) e embutidos nas visões |

## Integração contínua

`.gitlab-ci.yml` apenas inclui `.gitlab/ci/transformation.yml`, onde está
declarado um único job.

| Atributo | Valor |
| :--- | :--- |
| Job | `transformation-quality` |
| Estágio | `test` |
| Imagem | `python:3.11-slim` |
| Variáveis | `PYTHONPATH: src`, `PIP_DISABLE_PIP_VERSION_CHECK: "1"` |
| Gatilhos | Eventos de merge request e qualquer branch com commit |
| Artefato | `coverage-transformation.xml`, publicado como relatório Cobertura |

Passos executados, na ordem:

1. `pip install -r requirements-transformation-dev.txt`
2. `ruff check --config ruff-transformation.toml` sobre
   `src/etl/transformation`, `tests/transformation` e `scripts/transformation`
3. `ruff format --check` sobre os mesmos caminhos
4. `python scripts/transformation/render_schema.py --check`
5. `coverage run --branch --source=etl.transformation -m unittest discover -s tests -v`
6. `coverage report --fail-under=90`
7. `coverage xml -o coverage-transformation.xml`

A configuração do `ruff` está em `ruff-transformation.toml`:
`target-version = "py311"`, `line-length = 100` e regras `E4`, `E7`, `E9`, `F` e
`I`.

**Escopo real:** embora o passo 5 execute a suíte inteira, a medição de cobertura
e as verificações de estilo alcançam somente `etl.transformation`. As camadas de
extração, carga e orquestração não têm lint nem limite de cobertura no CI. O
próprio cabeçalho do arquivo registra que a consolidação pertence à tarefa
VB-07, que ainda não tem trabalho no repositório.

**Não há Deploy Contínuo.** Nenhum job publica imagem, aplica migração ou promove
versão, em conformidade com a exclusão do enunciado.

## Divergências observadas

Registradas porque a visão precisa refletir os arquivos, inclusive quando eles
discordam entre si.

| Divergência | Declarações conflitantes | Risco |
| :--- | :--- | :--- |
| Versão do Python | `Dockerfile` usa 3.12; o CI usa 3.11; `ruff-transformation.toml` mira `py311`; `README.md` registra 3.12+ | O código é verificado numa versão e executado em outra |
| Dependências sem pin | `requirements.txt` usa faixas para `minio`, `urllib3`, `prefect` e `duckdb` | Uma atualização de terceiros altera o comportamento sem mudança no repositório |
| Dependências de desenvolvimento parciais | `requirements-transformation-dev.txt` cobre apenas o gate de transformação | Não existe um conjunto declarado para rodar a suíte completa |
| Variável não lida | `docker-compose.yml` define `ETL_MINIO_SECURE` | Sugere um controle de TLS que nenhum módulo consulta |
| Caminho do banco | `docker-compose.yml` define `DUCKDB_PATH`; `load_duckdb_settings` lê `ETL_DUCKDB_PATH` | Caminho e tuning podem divergir na mesma execução |

## Tecnologias consideradas e não adotadas

| Tecnologia | Papel avaliado | Decisão |
| :--- | :--- | :--- |
| ClickHouse | Banco de ingestão | Substituído por DuckDB, com autorização registrada no ADR 0001 |
| Apache NiFi | Dataflow e coordenação | Fora da arquitetura principal; reavaliável se as fontes se diversificarem. Existe um exercício isolado em `ponderada/`, que não faz parte do pipeline |
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
