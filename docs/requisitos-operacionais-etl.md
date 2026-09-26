# Requisitos Operacionais do ETL — Matriz de Rastreabilidade (OV-01)

Inventário dos requisitos operacionais do pipeline orquestrado (agendamento, execução, resiliência, histórico, logs, métricas, observabilidade e disponibilidade), cada um ligado a **como será atendido** e a uma **evidência executável ou visual**. Serve de espinha para as tarefas de orquestração e observabilidade (OV-02 a OV-11).

**Arquitetura de referência** (ver [ADR 0001](adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md)): Python (dados) · **Prefect** (controle) · **MinIO** (entrada/objetos) · **DuckDB** (ingestão tratada) · **Elastic Stack** (observabilidade). Onde tarefas ou diagramas ainda citam ClickHouse, o alvo passa a ser **DuckDB**, conforme a autorização registrada no ADR.

## Agendamento, execução e disparo

| Requisito | O que exige | Atendido por | Evidência | Entrega |
| :--- | :--- | :--- | :--- | :--- |
| Fluxo orquestrado | E→T→L com etapas separadas; falha em uma interrompe as dependentes | Flow do Prefect com tarefas declaradas | Execução mostra tarefas separadas e para as dependentes na falha | OV-02 |
| Disparo por evento | Ingestão inicia na criação do objeto, sem varredura periódica | Adaptador HTTP recebe `s3:ObjectCreated` do MinIO → deployment Prefect | Publicar uma fixture no MinIO dispara uma execução | OV-02 |
| Agendamento | Executar em janela definida | Schedule do deployment Prefect | Deployment agendado dispara a execução no horário | OV-03 |
| Execução manual / backfill | Rodar sob demanda com janela, fontes e modo explícitos | Parâmetros de run do Prefect | Run manual com os parâmetros registrados no histórico | OV-03 |

## Resiliência e estado

| Requisito | O que exige | Atendido por | Evidência | Entrega |
| :--- | :--- | :--- | :--- | :--- |
| Retry com limite | Falha transitória é re-tentada; falha permanente não | Retries do Prefect + `resilience.py`/`failures.py` (classifica transitória × permanente) | Log mostra retry limitado; credencial/schema inválido não repete | OV-04 |
| Timeout | Etapa não pendura indefinidamente | Timeout de tarefa do Prefect | Tarefa expira e registra o estado | OV-04 |
| Retomada segura | Reiniciar sem duplicar dado | Checkpoint + SHA-256 e tabela de controle (idempotência do ADR) | Reprocesso da mesma entrada não duplica | OV-04 / OV-02 |
| Estado final das tarefas | Sucesso, falha ou ignorado explícito por tarefa | Estados do Prefect | Histórico mostra o estado final de cada tarefa | OV-04 |
| Idempotência | Mesma entrada e parâmetros → mesmo resultado | SHA-256 do conteúdo + tabela de controle no DuckDB | Reenvio do mesmo objeto resulta em "ignorado", sem nova carga | OV-02 |
| Histórico operacional | Registro de execuções e parâmetros usados | Histórico de runs do Prefect | Histórico consultável por `run_id` | OV-02 / OV-03 |

## Logs, métricas e observabilidade

| Requisito | O que exige | Atendido por | Evidência | Entrega |
| :--- | :--- | :--- | :--- | :--- |
| Logs estruturados correlacionados | JSON com `run_id`, `task_id`, `event_id`, fonte, objeto, lote, etapa, duração, status e erro sanitizado | `log_events.py` + Logstash | Logs de uma execução correlacionados pelo mesmo `run_id` | OV-05 / OV-07 |
| Sanitização de logs | Sem dado pessoal nem segredo em log ou artefato | Política do ADR aplicada no logging | Logs da execução sem payload pessoal | OV-05 |
| Métricas por etapa | Duração, registros recebidos/carregados/rejeitados, bytes, tentativas, latência, por extração/transformação/carga/total | Instrumentação em Python | Métricas emitidas por etapa, com unidades e rótulos limitados | OV-06 |
| Telemetria ao coletor | Métricas e traces enviados ao padrão de observabilidade | Logstash → Elasticsearch | Coletor recebe a telemetria da execução | OV-07 |
| Disponibilidade do coletor | Coletor indisponível não corrompe nem confirma carga incompleta | Desacoplamento telemetria × carga (ADR) | Carga confirma mesmo com a Elastic Stack fora do ar | OV-07 |
| Painel operacional | Status, duração, volumes, rejeições, retries e saúde do orquestrador e do banco | Kibana | Painel visual da execução | OV-08 |
| Health checks | Saúde do Prefect e do DuckDB | Checks de saúde | Consulta/endpoint de saúde respondendo | OV-08 |
| Alertas mínimos | Avisar em falha ou limite excedido | Regra de alerta na Elastic Stack | Alerta dispara numa falha controlada | OV-08 |

## Qualidade e aceite

| Requisito | O que exige | Atendido por | Evidência | Entrega |
| :--- | :--- | :--- | :--- | :--- |
| Testes de integração | Cobrir sucesso, falha na fonte, rejeição parcial, falha de carga e retomada | pytest + fixtures sintéticas | Suíte de integração passando nos cinco cenários | OV-09 |
| Diagrama de sequência | Execução normal, falha e reprocessamento, com logs, métricas, retry e confirmação no banco | UML de sequência | Diagrama versionado | OV-10 |
| Smoke operacional | Uma execução bem-sucedida e uma falha controlada com retry visível | Execução real + registro | Log/painel da execução e do retry | OV-11 |

## Estado verificado em 25/09/2026

Cada requisito acima confrontado com o artefato que o atende hoje. "Local"
indica que a capacidade está implementada e exercitada no ambiente Docker
Compose versionado, sem implantação produtiva (não há Deploy Contínuo).

| Requisito | Estado | Evidência |
| :--- | :--- | :--- |
| Fluxo orquestrado | Implementado | `src/etl/orchestration/flow.py` (`ingest_object`, `backfill`; tasks `extract` → `transform` → `load`); `tests/orchestration/test_gray_box_orquestracao.py` |
| Disparo por evento | Implementado (local) | `scripts/orchestration/watch_landing.py` (webhook `s3:ObjectCreated` ou polling); `tests/orchestration/test_watch_landing.py` |
| Agendamento | Implementado | Serviço `scheduler` + `scripts/orchestration/deployment.py` (cron `0 3 * * *`), histórico no `prefect-server` |
| Execução manual / backfill | Implementado | `run_ingest.py`, `run_backfill.py`, deployments `ingest-object/manual` e `backfill` em `prefect.yaml` |
| Retry com limite | Implementado | `RetryExecutor` (`ETL_EXTRACTION_*`) + `retries=2` com `_should_retry`; `tests/extraction/test_resilience.py`, `tests/orchestration/test_retry_reexecucao.py` |
| Timeout | Implementado | `timeout_seconds` em cada task (`flow.py`) |
| Retomada segura | Implementado | Checkpoint lote a lote após `COMMIT` e reconciliação (ADR 0005); `source_offset` absoluto preservado na retomada; `tests/orchestration/test_resumption.py`, `test_integridade_entre_lotes.py` |
| Confirmação condicionada à reconciliação | Implementado | `load_batch` levanta `UnbalancedLoadError` antes do `COMMIT`; `ingest_object` só marca o objeto com todos os lotes balanceados; `tests/load/test_control_tables.py`, `test_integridade_entre_lotes.py` |
| Identidade consistente entre lotes | Implementado | `transform_object` decide duplicidade uma vez por objeto; `_reconcile_with_persisted` confere contra o estado persistido; `tests/transformation/test_transformation.py` (`TransformObjectTests`) |
| Estado final das tarefas | Implementado | Estados do Prefect na UI (`prefect-server`) e `_batch_metadata.status` |
| Idempotência | Implementado | SHA-256 + `_control_object`; `test_segunda_entrega_do_mesmo_objeto_e_ignorada` |
| Histórico operacional | Implementado | `prefect-server` com volume `prefect-data`; views `execucao` e `reconciliacao_execucao` |
| Logs estruturados correlacionados | Implementado | JSON nas quatro etapas com `run_id`, `task_id`, `batch_id` (ADR 0008 remove `event_id` como campo próprio); `tests/orchestration/test_json_logging.py` |
| Sanitização de logs | Implementado | Eventos sem registros nem segredos; `tests/e2e/test_telemetria_e_coletor_indisponivel.py` |
| Métricas por etapa | Implementado | `duration_ms`, `byte_count`, contagens, `attempt`/`attempts` e latência nos eventos de lote e de retry |
| Telemetria ao coletor | Implementado (local) | GELF → Logstash (`observability/logstash/pipeline/etl.conf`) → Elasticsearch `etl-logs-*` |
| Disponibilidade do coletor | Implementado | Transporte best-effort; `tests/e2e/test_telemetria_e_coletor_indisponivel.py` |
| Painel operacional | Implementado (local) | `observability/kibana/painel-operacional.ndjson` (status, duração, volumes, rejeições, retries) |
| Health checks | Implementado | `scripts/orchestration/health_check.py` (Prefect + DuckDB); `tests/orchestration/test_health.py` |
| Alertas mínimos | Implementado (local) | Regras "falha de execução" e "fila parada" especificadas no runbook e criadas pela API de Alerting do Kibana; alerta de falha visto ativo no smoke de 25/09 ([evidência](smoke-observabilidade-sprint4.md)) |
| Testes de integração | Implementado | `tests/orchestration/` e `tests/e2e/` (sucesso, falha na fonte, rejeição parcial, falha de carga, retomada) |
| Diagrama de sequência | Implementado | `docs/assets/uml/sequencia-ingestao-etl.plantuml` e `.svg` |
| Smoke operacional | Implementado | `scripts/orchestration/smoke_observabilidade.sh`; roteiro e resultado no runbook (OB-11) |

---

**Nota histórica (auditoria VB-10, 11/09/2026):** na Sprint 3, o adaptador de
eventos, a suíte ponta a ponta e a integração com a Elastic Stack constavam
como pendentes. Os três foram integrados na Sprint 4, conforme a tabela acima.
