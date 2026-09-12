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
| Orquestração dos pipelines | OV-01 a OV-04 | [`src/etl/orchestration/flow.py`](../src/etl/orchestration/flow.py), `scripts/orchestration/deployment.py`, `run_ingest.py`, `run_backfill.py`, `tests/orchestration/` e [`requisitos-operacionais-etl.md`](requisitos-operacionais-etl.md) | Implementado |
| Disparo por evento `s3:ObjectCreated` | OV-02 | [ADR 0001](adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md) descreve o adaptador HTTP; não há módulo correspondente no repositório | Documentado |
| Observabilidade | OV-05 a OV-08 | `src/etl/extraction/log_events.py` cobre apenas o log estruturado do lote extraído; `observability/` existe nas branches `task-196` a `task-199` | Não integrado |
| Integração Contínua | VB-06 a VB-08 | `.gitlab-ci.yml`: lint em `src`, `scripts` e `tests`; schema, suíte completa e cobertura de todo `etl` | Implementado |
| Testes automatizados | LN-10/11, MG-10/11, MC-09/11, OV-09/11, VB-01 a VB-05 | Suíte `unittest` em `tests/` cobrindo extração, transformação, carga, orquestração e E2E | Implementado |
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
| Observabilidade não integrada | ADR 0001 e `requisitos-operacionais-etl.md` | OV-* | Há logs estruturados e reconciliação local; não há coletor, painel, health check da orquestração ou alerta integrados |
| Adaptador de eventos inexistente | Contrato no ADR 0001 | OV-02 | O disparo real é manual (`run_ingest.py`) ou agendado (`deployment.py`); não há ingestão iniciada por evento do MinIO |
| Dependências de runtime sem pin | `requirements.txt` usa faixas para `prefect`, `duckdb` e `minio` | VB-06 | A reprodução integral continua dependente das versões transitivas resolvidas pelo instalador |
| Caminho do banco unificado | `ETL_DUCKDB_PATH` no Compose, flow e repositório | OV-*/MC-* | Caminho e tuning usam a mesma configuração |

## Substituição ClickHouse por DuckDB

A troca está autorizada e registrada no ADR 0001. Entre os critérios que o
próprio ADR listava para a ratificação estava a autorização aparecer na matriz
de rastreabilidade, nos diagramas e nos critérios de aceite. Esta seção cumpre
a parte da matriz.

| Ponto exigido pelo ADR 0001 | Situação |
| :--- | :--- |
| Autorização registrada | Registrada no contexto do ADR 0001 e referenciada aqui |
| Matriz de rastreabilidade refletindo a troca | Cumprido por este documento |
| Diagramas refletindo a troca | Cumprido em [`assets/uml/`](assets/uml/), onde o destino é DuckDB |
| Tarefas e critérios que citam ClickHouse atualizados | Cumprido: somente referências históricas e ao enunciado permanecem |
| Fluxo mínimo subindo por comando documentado | Cumprido por `docker-compose.yml` e `scripts/orchestration/run_ingest.py` |
| Publicação de fixture disparando execução automática | Não cumprido: não há adaptador de eventos |
| Execução das seis fontes com registro na Elastic Stack | Não cumprido: não há observabilidade integrada |
| Evidência automatizada de retry, rejeição, idempotência e retomada | Cumprido: `tests/extraction`, `tests/load` e `tests/orchestration` cobrem os cenários |
| Documento de estimativa de custos | Pendente |

O grupo ratificou o ADR 0001 em 11/09/2026 sem exigir que todos os pontos
acima estivessem cumpridos — o que ainda falta (adaptador de eventos,
observabilidade integrada, estimativa de custos) segue como acompanhamento. A
lista completa está em [`adrs/index.md`](adrs/index.md).
