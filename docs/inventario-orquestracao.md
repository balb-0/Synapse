# Inventário da orquestração e requisitos operacionais descobertos

Matriz que liga cada requisito operacional da Sprint 4 (orquestração servida,
agendamento, reexecução, disparo por evento e dívida técnica) a uma evidência
executável no `develop` ou a uma lacuna declarada. Base: os requisitos
operacionais do ETL em [`requisitos-operacionais-etl.md`](requisitos-operacionais-etl.md)
(OV-01 a OV-11) e a especificação técnica, seção Orquestração.

Legenda: **evidência** = comando, arquivo ou teste que prova o atendimento;
**lacuna** = o que falta implementar nesta sprint, com a task que a fecha.

## Servidor, publicação e histórico

| Requisito | Evidência executável | Lacuna |
| :--- | :--- | :--- |
| Servidor do orquestrador com UI e histórico persistente | — | `docker-compose.yml` só declara `minio` + `runner`; sem `prefect-server`, cada execução usa API efêmera e o histórico se perde |
| Publicar fluxos e conservar histórico após o término | `src/etl/orchestration/flow.py` (`ingest-object`, `backfill`); `scripts/orchestration/deployment.py` (deployment `agendado`) | sem servidor, `deployment.py` serve em processo e o histórico não sobrevive; sem `prefect.yaml` para publicação pela CLI |
| Health check da própria interface do servidor | — | sem endpoint `/api/health` com volume próprio no ambiente declarado |

## Agendamento, reexecução e disparo

| Requisito | Evidência executável | Lacuna |
| :--- | :--- | :--- |
| Agendamento resiliente à parada do processo que o serve | `deployment.py` registra cron `0 3 * * *` | `.serve()` em processo: parar o contêiner interrompe o cron sem recuperação; histórico de parâmetros agendados não persiste |
| Reinício de tarefa falha e reexecução parametrizada pela UI | checkpoint lote a lote + `_control_object` (retomada sem duplicar, coberta em `tests/orchestration/test_resumption.py`); `backfill --reprocess` | `transform` e `load` sem `retries`; sem teste do contrato de retry |
| Disparo da ingestão pela chegada de objeto na área de entrada | idempotência por SHA-256 (`status: ignored` no reenvio, ver runbook) | sem adaptador de evento: `run_ingest.py` é manual; objeto novo não inicia execução sozinho |

## Dívida técnica e integração contínua

| Requisito | Evidência executável | Lacuna |
| :--- | :--- | :--- |
| Montagem de referências pela interface pública do repositório | `DuckDbLoadRepository` em `src/etl/load/duckdb_repository.py` | `_build_references` em `flow.py` lê `repo._conn` (atributo privado) |
| Caminho do banco único e variáveis documentadas com efeito | `load_duckdb_settings()` lido pelo flow e pelo repositório (`ETL_DUCKDB_PATH`); `load_extraction_settings()` lê as demais | sem teste que garanta que toda variável do `.env.example` é consumida e que não há variável paralela (`DUCKDB_PATH`, `ETL_MINIO_SECURE`) |
| Versões de execução fixadas | `Dockerfile` parte de `python:3.12-slim` | `requirements.txt` usa faixas (`>=`, `<`): ambiente novo pode instalar versões diferentes do CI |
| Relatório de testes no CI com bloqueio em falha | `.gitlab-ci.yml`: `coverage report --fail-under=85` bloqueia o pipeline; `coverage-etl.xml` como artefato | sem relatório JUnit por caso de teste (`reports:junit`) |

## Smoke de validação

| Requisito | Evidência executável | Lacuna |
| :--- | :--- | :--- |
| Fluxo executado pela UI, com falha provocada e reinício | `scripts/orchestration/run_ingest.py --source empresas` (sucesso + `ignored` no reenvio) | sem registro anexado de execução agendada, execução por evento, falha e reinício vindos da própria interface |
