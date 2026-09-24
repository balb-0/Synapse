# Inventário da telemetria existente (OB-01)

Levantamento do que a Sprint 3 já deixou pronto em telemetria, do que foi
calculado e nunca chegou a um destino, e do que está apenas decidido em
documento, sem uma linha de código correspondente. Serve de base para OB-02
(ratificar o padrão frente ao que a Sprint 4 exige) e para as tasks de
implementação que seguem (OB-03 a OB-11).

## Escopo

Este inventário cobre as quatro etapas citadas pelos requisitos operacionais
do ETL (`docs/requisitos-operacionais-etl.md`): extração, transformação,
carga e orquestração. Para cada evento, métrica ou capacidade encontrada,
classifica em uma das três categorias exigidas pela task:

- **Evento emitido hoje** — já sai em produção/testes, com formato e destino
  reais.
- **Métrica calculada e descartada** — o valor já é computado em algum ponto
  do código, mas não sai da função onde nasce (não vira log, métrica de série
  temporal ou registro consultável).
- **Capacidade apenas decidida** — está registrada em ADR, visão ou
  requisito, sem nenhuma linha de código que a implemente.

## Fora de escopo

- Ratificar ou alterar o padrão de observabilidade — isso é OB-02.
- Implementar qualquer lacuna encontrada aqui — cada uma já aponta para a
  task de destino (OB-03 a OB-11).

## Evento emitido hoje

| Evento | Onde | Emitido por | Atributos | Destino atual |
| :--- | :--- | :--- | :--- | :--- |
| `extraction.batch.emitted` | `src/etl/extraction/log_events.py` (`ExtractionBatchLogEvent`) | `StandardLoggingSink` → `logging.getLogger("etl.extraction")` | `source`, `run_id`, `task_id`, `batch_id`, `duration_ms`, `record_count`, `byte_count`, `schema_version`, `contract_version`, checkpoint | `logging.info(..., extra=...)`, sem handler/formatter próprio configurado |
| `load.batch.emitted` | `src/etl/load/log_events.py` (`LoadBatchLogEvent`) | `StandardLoggingSink` → `logging.getLogger("etl.load")` | `source`, `run_id`, `task_id`, `batch_id`, `status`, `duration_ms`, `extracted_count`, `loaded_count`, `rejected_count`, `duplicate_count`, `balanced` | idem |
| `orchestration.extract.emitted` | `src/etl/orchestration/flow.py` (`_log_event`, task `extract`) | `prefect.get_run_logger()` | `status`, `source`, `run_id`, `batch_count`, `duration_ms` | Log do Prefect (console/histórico do run) |
| `orchestration.transform.emitted` | idem, task `transform` | idem | `status`, `source`, `run_id`, `accepted_count`, `duration_ms` | idem |
| `orchestration.load.emitted` | idem, task `load` | idem | `status`, `source`, `run_id`, `batch_count`, `loaded_count`, `rejected_count`, `duplicate_count`, `duration_ms` | idem |
| `orchestration.ingest_object.emitted` | idem, flow `ingest_object` | idem | `status` (`ignored`/`reprocess`/`loaded`), `source`, `run_id`, `object_key`, `source_checksum`, `duration_ms` | idem |
| `orchestration.backfill.emitted` | idem, flow `backfill` | idem | `status`, `sources`, `prefix`, `reprocess` | idem |

Todos os sete seguem a mesma convenção (ADR 0001): a mensagem do log é o
próprio nome do evento, sem interpolação, e os atributos de correlação vão em
`extra`, com chaves `None` removidas antes de emitir
(`ExtractionBatchLogEvent.as_dict`, `LoadBatchLogEvent.as_dict`).

**Achado — `task_id` não identifica uma execução.** Nas duas classes de
evento por lote, `task_id` vem de `BatchMetadata.task_id`, que os extratores
preenchem com um rótulo fixo por fonte (`task_id=f"extract-{self.source}"`,
`csv_extractors.py:357`) — o mesmo valor em toda execução da mesma fonte, não
um identificador de tentativa. Além disso, os cinco eventos de orquestração
em `flow.py` não carregam `task_id` nenhum, só `run_id`. O requisito de
"logs correlacionados por `run_id` e `task_id`" (`requisitos-operacionais-etl.md`,
linha "Logs estruturados correlacionados", entrega OV-05/OV-07) precisa de
uma decisão em OB-02 sobre o que `task_id` deve significar antes de
OB-03/OB-04 estenderem esse formato — hoje ele não serve para distinguir
tentativas de retry da mesma fonte.

## Métrica calculada e descartada

| Métrica | Onde é calculada | O que acontece com ela hoje |
| :--- | :--- | :--- |
| `TransformationResult.metrics` (aceitos, rejeitados, duplicados por lote) | `src/etl/transformation/pipeline.py` | Fica no objeto de retorno; só o total agregado (`accepted_count`) chega ao log de orquestração — rejeitados/duplicados da transformação não saem daí |
| `LoadResult` / reconciliação (`extracted`, `loaded`, `rejected`, `duplicates`, `is_balanced()`) | `src/etl/load/duckdb_repository.py` | Vira o evento `load.batch.emitted` (linha a linha) e o resumo da task `load`; não existe série temporal nem contador acumulado entre execuções |
| `SourceFailure` (categoria, natureza, tentativa, `next_delay_seconds`) | `src/etl/extraction/resilience.py` (`RetryExecutor._handle_failed_attempt`) | Vai para um `FailureRecorder` injetável — mas o padrão é `_NullFailureRecorder`, que descarta a falha (`del failure`). Nenhum extrator real injeta um recorder hoje: toda tentativa de retry é classificada e depois jogada fora |
| Latência por chamada (`duration_ms` das tasks `extract`/`transform`/`load`) | `flow.py`, via `time.monotonic()` | Só existe dentro da string do log daquela execução; não vira métrica agregável por etapa/fonte ao longo do tempo |

Essas quatro linhas são o material de partida de OB-05 (métricas de
transformação) e OB-06 (retries e latência): o cálculo já existe, falta
publicá-lo em vez de descartar.

## Capacidade apenas decidida

| Capacidade | Decisão registrada em | Estado no código |
| :--- | :--- | :--- |
| Stack de observabilidade = Elastic Stack (Logstash → Elasticsearch → Kibana), **não** Prometheus/Grafana | `docs/visao-tecnologia-etl.md` ("Prometheus e Grafana... Não selecionados; a orientação da sprint direcionou à Elastic Stack"), ADR 0001 | Nenhuma dependência no `requirements.txt`, nenhum serviço no `docker-compose.yml` — o próprio compose comenta "A Elastic Stack (observabilidade) é acrescentada no OV-07" |
| Coletor recebe telemetria das quatro etapas, indisponibilidade não corrompe carga | `requisitos-operacionais-etl.md` (linha "Telemetria ao coletor" / "Disponibilidade do coletor") | Sem transporte implementado; hoje não há nada que *possa* corromper porque não há envio nenhum ao coletor |
| Painel operacional (status, duração, volumes, rejeições, retries, saúde) | `requisitos-operacionais-etl.md` (linha "Painel operacional"), `visao-engenharia-etl.md` | Sem painel; dado teria que vir do Elasticsearch, que ainda não recebe nada |
| Health check do orquestrador e do banco | `requisitos-operacionais-etl.md` (linha "Health checks") | Sem endpoint/rotina de health check; depende também de OQ-03 (servidor do Prefect no ar) |
| Alertas mínimos em falha ou fila parada | `requisitos-operacionais-etl.md` (linha "Alertas mínimos") | Sem regra de alerta configurada em lugar nenhum |

**Achado — a auditoria da Sprint 3 já registrou isso.**
`docs/auditoria-entregaveis-sprint3.md` classifica "Telemetria, painel, health
checks, alertas (Elastic Stack)" como "Não (planejado)" e "Logs
estruturados"/"Métricas por etapa" como "Parcial" — o mesmo recorte que este
inventário reproduz, confirmando que nada mudou nesse ponto entre a auditoria
(11/09/2026) e o início da Sprint 4.

## Sanitização — já é estrutural, não apenas decidida

Vale registrar como exceção às duas tabelas acima: a política de "sem dado
pessoal nem segredo em log" não é só uma decisão de ADR — já está embutida no
código. `ExtractionBatchLogEvent`, `LoadBatchLogEvent` e `SourceFailure` são
`dataclasses` fechadas que só aceitam atributos técnicos (identificadores,
contagens, durações, categorias de erro); não existe caminho para incluir um
registro de negócio nesses eventos, porque as classes nunca recebem os
registros em si. OB-04 herda essa restrição ao estender o formato às quatro
etapas — não precisa recriá-la.

## Fontes usadas

- `docs/requisitos-operacionais-etl.md` — matriz de requisitos operacionais
  (OV-01), com a nota de disponibilidade de dependências revista em
  11/09/2026.
- `docs/auditoria-entregaveis-sprint3.md` — auditoria VB-10 contra o código
  real do `develop`.
- `docs/visao-tecnologia-etl.md` — decisão Elastic Stack vs. Prometheus/Grafana.
- `docs/adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md` — formato do
  evento técnico e arquitetura de referência.
- `docs/matriz-rastreabilidade-sprint3.md` — registro anterior de que a
  observabilidade não está integrada.
- `src/etl/extraction/log_events.py`, `src/etl/load/log_events.py`,
  `src/etl/orchestration/flow.py`, `src/etl/extraction/resilience.py`,
  `src/etl/extraction/failures.py`, `src/etl/extraction/contracts.py`,
  `src/etl/extraction/csv_extractors.py` — código inspecionado diretamente.
- `docker-compose.yml`, `requirements.txt` — confirmação de ausência de
  serviço/dependência de observabilidade no ambiente local.
