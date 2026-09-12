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

---

**Nota de disponibilidade das dependências (revista na auditoria VB-10, 11/09/2026):** OV-05 parte de um primitivo existente (`src/etl/extraction/log_events.py`); a resiliência (OV-04) reaproveita `resilience.py`/`failures.py`. O adaptador de carga no DuckDB **já existe** em `src/etl/load/` (`duckdb_repository.py`, `ddl.py`), com testes em `tests/load/`, e o fluxo E→T→L está fechado em `src/etl/orchestration/flow.py` (`ingest_object` e `backfill`). Permanecem sem implementação no `develop`: o adaptador de eventos HTTP (disparo por `s3:ObjectCreated`), a integração com a Elastic Stack (OV-07/OV-08) e a suíte de testes ponta a ponta do fluxo orquestrado (OV-09) — esta última em trabalho nas branches de teste da Sprint 3 (VB-03 a VB-05).
