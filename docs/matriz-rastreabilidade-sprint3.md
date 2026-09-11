# Matriz de rastreabilidade da Sprint 3 (AN-02)

Cada obrigação do enunciado, registrada em
[`checklist-entregaveis-sprint3.md`](checklist-entregaveis-sprint3.md), aponta
aqui para as tarefas responsáveis, para o artefato que serve de evidência e para
o **estado observado no repositório**. O estado é verificado no código e nos
arquivos de configuração, não no planejamento das tarefas: uma obrigação com
tarefa concluída no board e sem artefato no repositório aparece como pendente.

O levantamento foi feito na branch `feat/uml-diagrams`, idêntica a
`origin/develop` no momento do registro. Trabalho existente em branch não
integrada é registrado como **não integrado**, porque não compõe a entrega
enquanto não for mesclado.

## Vocabulário de estado

| Estado | Significado |
| :--- | :--- |
| Implementado | Existe código no `develop` e teste automatizado que o exercita |
| Implementado sem teste | Existe código no `develop`, sem teste automatizado |
| Documentado | Existe contrato ou documento, sem implementação correspondente |
| Não integrado | Existe trabalho em branch remota não mesclada ao `develop` |
| Pendente | Não foi encontrado artefato no repositório |

## Obrigações do pipeline ETL

| Requisito do enunciado | Tarefas | Evidência no repositório | Estado |
| :--- | :--- | :--- | :--- |
| Extração das fontes | LN-01 a LN-11 | [`src/etl/extraction/`](../src/etl/extraction/), [`inventario-fontes-etl.md`](inventario-fontes-etl.md), [`contrato-lote-extraido.md`](contrato-lote-extraido.md), [`extratores.md`](extratores.md), `tests/extraction/` (10 módulos) | Implementado |
| Transformações essenciais | MG-01 a MG-11 | [`src/etl/transformation/`](../src/etl/transformation/), [`schema-transformacao.md`](schema-transformacao.md), [`catalogo-transformacao.md`](catalogo-transformacao.md), [`matriz-transformacao.md`](matriz-transformacao.md), `tests/transformation/` | Implementado |
| Validação e tratamento antes da carga | MG-03 a MG-08 | `validation.py`, `consistency.py`, `identity.py`, `quarantine.py` em [`src/etl/transformation/`](../src/etl/transformation/) | Implementado |
| Carga na tabela de ingestão | MC-01 a MC-11 | [`src/etl/load/`](../src/etl/load/), [`ddl-ingestao.md`](ddl-ingestao.md), [`repositorio-de-carga.md`](repositorio-de-carga.md), [`ambiente-duckdb.md`](ambiente-duckdb.md), `sql/duckdb/001_ingestao_tratada.sql`, `tests/load/` (7 módulos) | Implementado |
| Orquestração dos pipelines | OV-01 a OV-04 | [`src/etl/orchestration/flow.py`](../src/etl/orchestration/flow.py), `scripts/orchestration/deployment.py`, `run_ingest.py`, `run_backfill.py`, [`requisitos-operacionais-etl.md`](requisitos-operacionais-etl.md) | Implementado sem teste |
| Disparo por evento `s3:ObjectCreated` | OV-02 | [ADR 0001](adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md) descreve o adaptador HTTP; não há módulo correspondente no repositório | Documentado |
| Observabilidade | OV-05 a OV-08 | `src/etl/extraction/log_events.py` cobre apenas o log estruturado do lote extraído; `observability/` existe nas branches `task-196` a `task-199` | Não integrado |
| Integração Contínua | VB-06 a VB-08 | `.gitlab-ci.yml` e `.gitlab/ci/transformation.yml`, com o job `transformation-quality` | Implementado para `transformation` |
| Testes automatizados | LN-10/11, MG-10/11, MC-09/11, OV-09/11, VB-01 a VB-05 | 19 módulos `unittest` em `tests/` cobrindo extração, transformação e carga | Implementado parcialmente |
| Documentação ISO/IEC 10746 | AN-04 a AN-08 | [`visao-negocio-etl.md`](visao-negocio-etl.md), [`visao-informacao-etl.md`](visao-informacao-etl.md), [`visao-computacional-etl.md`](visao-computacional-etl.md), [`visao-engenharia-etl.md`](visao-engenharia-etl.md), [`visao-tecnologia-etl.md`](visao-tecnologia-etl.md) | Implementado |
| Diagramas UML | AN-09, AN-10, AN-11, OV-10 | [`assets/uml/`](assets/uml/): casos de uso, componentes e sequência | Implementado |
| Decisões técnicas | AN-03 | [`adrs/index.md`](adrs/index.md), ADRs 0001 a 0004 | Implementado |
| Boas práticas de engenharia | Transversal | [`dev-rules.md`](dev-rules.md), [`gestao-configuração.md`](gestao-configuração.md), `ruff-transformation.toml` | Implementado parcialmente |

## Obrigações do Data Model Canvas

| Requisito do enunciado | Tarefas | Evidência no repositório | Estado |
| :--- | :--- | :--- | :--- |
| Canvas preenchido e exportado | KP-01 a KP-11 | [`dmc.json`](dmc.json), `schemaVersion 1`, versão 1.1, quatro cubos declarados | Implementado |
| Coerência com contexto e requisitos | KP-02 a KP-05 | [`projeto.md`](projeto.md) §5 e [`matriz-evidencias-problem-canvas.md`](matriz-evidencias-problem-canvas.md) | Implementado |
| Validação do arquivo exportado | KP-11 | `scripts/dmc/validate_dmc.py` e sua suíte em `scripts/dmc` | Implementado |

## Pendências nomeadas

Estas pendências fazem parte da entrega de documentação: elas são registradas,
não corrigidas por este bloco de tarefas.

| Pendência | Onde está | Quem resolve | Efeito enquanto não for resolvida |
| :--- | :--- | :--- | :--- |
| Nome ClickHouse no código | `Field.clickhouse_type` e `destination_columns` em `src/etl/transformation/schema.py`, `AcceptedRecord.as_clickhouse_row()` em `pipeline.py`, `tests/transformation/test_clickhouse_contract.py` | MG-* | O tipo canônico ainda é declarado em vocabulário ClickHouse e traduzido para DuckDB por `duckdb_type()` em `src/etl/load/ddl.py`; o destino efetivo é DuckDB |
| Nome ClickHouse na documentação de transformação | [`schema-transformacao.md`](schema-transformacao.md), [`catalogo-transformacao.md`](catalogo-transformacao.md), [`integracao-transformacao.md`](integracao-transformacao.md), [`inventario-regras-transformacao.md`](inventario-regras-transformacao.md) | MG-* | Leitor pode concluir que o destino é ClickHouse; o ADR 0001 é a fonte que prevalece |
| Observabilidade não integrada | Branches `task-196-ov-05` a `task-199-ov-08` | OV-* | Não há métricas, telemetria, painel, health check de orquestração nem alerta no `develop`; as branches precedem a camada de carga e vão conflitar na integração |
| Adaptador de eventos inexistente | Contrato no ADR 0001 | OV-02 | O disparo real é manual (`run_ingest.py`) ou agendado (`deployment.py`); não há ingestão iniciada por evento do MinIO |
| Fluxo orquestrado sem teste | `src/etl/orchestration/flow.py`; `tests/orchestration/` não existe | OV-09 | Nenhuma evidência automatizada de retry, timeout, retomada ou idempotência no nível do flow; os testes de integração estão na branch `task-200-ov-09` |
| CI não consolidado | `.gitlab/ci/transformation.yml` cobre só `etl.transformation` | VB-07 | `extraction`, `load` e `orchestration` não passam por lint nem por cobertura no CI |
| Versão do Python divergente | `Dockerfile` (3.12), `.gitlab/ci/transformation.yml` (3.11), `ruff-transformation.toml` (`py311`), `README.md` (3.12+) | VB-06 | O código é verificado numa versão e executado em outra |
| Dependências de runtime sem pin | `requirements.txt` usa faixas (`prefect>=3,<4`, `duckdb>=1.1`, `minio>=7.2,<8`) | VB-06 | A execução não é reproduzível entre ambientes |
| Nomes de variável divergentes | `docker-compose.yml` define `DUCKDB_PATH`; `src/etl/load/config.py` lê `ETL_DUCKDB_PATH` | OV-*/MC-* | O tuning do banco e o caminho do arquivo podem vir de fontes diferentes na mesma execução |
| ADR 0001 ainda proposto | [`adrs/0001-...`](adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md) | Grupo | A arquitetura é seguida na prática sem decisão formalmente aceita |
| ADR 0002 pendente de ratificação | [`adrs/0002-...`](adrs/0002-identidade-e-versoes-na-tabela-de-ingestao.md) | Grupo | A semântica de versões vale para a carga, mas não foi ratificada pelo grupo |

## Substituição ClickHouse por DuckDB

A troca está autorizada e registrada no ADR 0001, que exige, como condição para
o ADR passar de **Proposto** a **Aceito**, que a autorização apareça na matriz de
rastreabilidade, nos diagramas e nos critérios de aceite. Esta seção cumpre a
parte da matriz.

| Ponto exigido pelo ADR 0001 | Situação |
| :--- | :--- |
| Autorização registrada | Registrada no contexto do ADR 0001 e referenciada aqui |
| Matriz de rastreabilidade refletindo a troca | Cumprido por este documento |
| Diagramas refletindo a troca | Cumprido em [`assets/uml/`](assets/uml/), onde o destino é DuckDB |
| Tarefas e critérios que citam ClickHouse atualizados | Parcial: a documentação de transformação e o código ainda usam o nome |
| Fluxo mínimo subindo por comando documentado | Cumprido por `docker-compose.yml` e `scripts/orchestration/run_ingest.py` |
| Publicação de fixture disparando execução automática | Não cumprido: não há adaptador de eventos |
| Execução das seis fontes com registro na Elastic Stack | Não cumprido: não há observabilidade integrada |
| Evidência automatizada de retry, rejeição, idempotência e retomada | Parcial: coberto em `tests/extraction` e `tests/load`, ausente no nível do flow |
| Documento de estimativa de custos | Pendente |

Enquanto os pontos não cumpridos permanecerem, o ADR 0001 continua com status
**Proposto**. A lista completa está em [`adrs/index.md`](adrs/index.md).
