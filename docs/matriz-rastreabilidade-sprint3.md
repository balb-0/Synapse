# Matriz de rastreabilidade da Sprint 3 (AN-02)

Cada obrigação do enunciado, registrada em
[`checklist-entregaveis-sprint3.md`](checklist-entregaveis-sprint3.md), aponta
aqui para as tarefas responsáveis, para o artefato que serve de evidência e para
o **estado observado no repositório**. O estado é verificado no código e nos
arquivos de configuração, não no planejamento das tarefas: uma obrigação com
tarefa concluída no board e sem artefato no repositório aparece como pendente.

O levantamento original foi feito na branch `feat/uml-diagrams`, idêntica a
`origin/develop` em 11/09/2026. **Revisão de 25/09/2026 (fechamento da Sprint
4):** os estados abaixo foram reconferidos após a integração da
observabilidade (OB-03 a OB-11), do disparo por evento e das correções de
reconciliação apontadas no feedback da Sprint 3. Trabalho existente em branch
não integrada continua registrado como **não integrado**.

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
| Extração das fontes | LN-01 a LN-11 | [`src/etl/extraction/`](../src/etl/extraction/), [`inventario-fontes-etl.md`](inventario-fontes-etl.md), [`contrato-lote-extraido.md`](contrato-lote-extraido.md), [`extratores.md`](extratores.md), `tests/extraction/`; posição absoluta `source_offset` por lote | Implementado |
| Transformações essenciais | MG-01 a MG-11 | [`src/etl/transformation/`](../src/etl/transformation/), [`schema-transformacao.md`](schema-transformacao.md), [`catalogo-transformacao.md`](catalogo-transformacao.md), [`matriz-transformacao.md`](matriz-transformacao.md), `tests/transformation/`; decisão de identidade global entre lotes (`transform_object`) | Implementado |
| Validação e tratamento antes da carga | MG-03 a MG-08 | `validation.py`, `consistency.py`, `identity.py`, `quarantine.py` em [`src/etl/transformation/`](../src/etl/transformation/) | Implementado |
| Carga na tabela de ingestão | MC-01 a MC-11 | [`src/etl/load/`](../src/etl/load/), [`ddl-ingestao.md`](ddl-ingestao.md), [`repositorio-de-carga.md`](repositorio-de-carga.md), [`ambiente-duckdb.md`](ambiente-duckdb.md), `sql/duckdb/001_ingestao_tratada.sql`, `tests/load/`; `COMMIT` só com reconciliação balanceada (`UnbalancedLoadError`) | Implementado |
| Orquestração dos pipelines | OV-01 a OV-04, OQ-01 a OQ-10 | [`src/etl/orchestration/flow.py`](../src/etl/orchestration/flow.py), `prefect-server` e `scheduler` no Compose, `prefect.yaml`, `scripts/orchestration/deployment.py`, `run_ingest.py`, `run_backfill.py`, `tests/orchestration/` e [`requisitos-operacionais-etl.md`](requisitos-operacionais-etl.md) | Implementado |
| Disparo por evento `s3:ObjectCreated` | OV-02, OQ-06 | `scripts/orchestration/watch_landing.py` (webhook ou polling) e `tests/orchestration/test_watch_landing.py` | Implementado |
| Observabilidade | OB-01 a OB-11 | Eventos JSON nas quatro etapas (`log_events.py` de cada pacote, `etl.orchestration.logging_config`); Logstash/Elasticsearch/Kibana no Compose; `observability/logstash/pipeline/etl.conf`, `observability/kibana/painel-operacional.ndjson`; `scripts/orchestration/health_check.py`; alertas no runbook; `tests/orchestration/test_json_logging.py`, `test_health.py`, `tests/e2e/test_telemetria_e_coletor_indisponivel.py` | Implementado |
| Integração Contínua | VB-06 a VB-08, OQ-10 | `.gitlab-ci.yml`: lint e formatação em `src`, `scripts` e `tests`; validação arquitetural, schema, suíte completa com relatório JUnit e cobertura de todo `etl` (`--fail-under=85`) | Implementado |
| Testes automatizados | LN-10/11, MG-10/11, MC-09/11, OV-09/11, VB-01 a VB-05, OB-10 | Suíte `unittest` em `tests/` (376 testes, cobertura 92% em 25/09/2026) cobrindo extração, transformação, carga, orquestração, integridade entre lotes (`tests/orchestration/test_integridade_entre_lotes.py`) e E2E (`tests/e2e/`) | Implementado |
| Documentação ISO/IEC 10746 | AN-04 a AN-08 | [`visao-negocio-etl.md`](visao-negocio-etl.md), [`visao-informacao-etl.md`](visao-informacao-etl.md), [`visao-computacional-etl.md`](visao-computacional-etl.md), [`visao-engenharia-etl.md`](visao-engenharia-etl.md), [`visao-tecnologia-etl.md`](visao-tecnologia-etl.md) | Implementado |
| Diagramas UML | AN-09, AN-10, AN-11, OV-10 | [`assets/uml/`](assets/uml/): casos de uso, componentes e sequência | Implementado |
| Decisões técnicas | AN-03, AR-09, OB-02 | [`adrs/index.md`](adrs/index.md), ADRs 0001 a 0008 | Implementado |
| Boas práticas de engenharia | Transversal | [`dev-rules.md`](dev-rules.md), [`gestao-configuração.md`](gestao-configuração.md), `ruff.toml`, `requirements.txt` com versões fixadas, `.env.example`, template de MR | Implementado |

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
| Área `bronze` do MinIO | Contrato do ADR 0001 | — | A extração lê `landing/` direto; a origem imutável é o objeto em `landing/` com SHA-256 |
| Regras de alerta fora do NDJSON do painel | Runbook, seção Alertas mínimos | OB-09 | O formato de regra do Kibana não é importável por NDJSON; as duas regras são criadas pela API de Alerting com os comandos do runbook |
| Imagens MinIO em `latest` | `docker-compose.yml` | — | Única parte da pilha sem versão fixada |

Pendências da Sprint 3 resolvidas na Sprint 4: observabilidade integrada
(OB-03 a OB-11), adaptador de eventos (`watch_landing.py`), dependências
fixadas (OQ-09), caminho do banco unificado (OQ-08), acesso a atributo privado
removido (OQ-07), confirmação condicionada à reconciliação, classificação
global de identidade entre lotes e posição absoluta na retomada.

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
| Publicação de fixture disparando execução automática | Cumprido localmente: `watch_landing.py` (webhook `s3:ObjectCreated` ou polling) |
| Execução das seis fontes com registro na Elastic Stack | Cumprido no ambiente local: eventos JSON via GELF → Logstash → `etl-logs-*`; roteiro OB-11 no runbook |
| Evidência automatizada de retry, rejeição, idempotência e retomada | Cumprido: `tests/extraction`, `tests/load` e `tests/orchestration` cobrem os cenários |
| Documento de estimativa de custos | Cumprido: [`estimativa-custos-ambiente.md`](estimativa-custos-ambiente.md) |

O grupo ratificou o ADR 0001 em 11/09/2026 sem exigir que todos os pontos
acima estivessem cumpridos; os pontos que estavam em acompanhamento (adaptador
de eventos, observabilidade integrada, estimativa de custos) foram cumpridos na
Sprint 4. A lista completa está em [`adrs/index.md`](adrs/index.md).
