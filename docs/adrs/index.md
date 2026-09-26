# Índice das decisões arquiteturais (AN-03)

Registro das decisões técnicas do ETL das Sprints 3 e 4, com o status **verbatim** de
cada ADR e o ponto do checklist do enunciado que ela cobre. O índice não altera
nenhuma decisão: ele mostra o que já foi decidido, por quem, em que estado, e o
que ainda falta para cada decisão ser considerada firme.

O enunciado exige justificativa de linguagem, arquitetura, frameworks,
ferramentas, observabilidade e consumo analítico. As oito ADRs abaixo cobrem
esses pontos. Nenhuma delas pressupõe Deploy Contínuo ou publicação automática
em produção, que permanecem fora do escopo.

## Decisões registradas

| ADR | Título | Status | Decisões que cobre |
| :--- | :--- | :--- | :--- |
| [0001](0001-arquitetura-etl-python-prefect-minio-duckdb.md) | Arquitetura do ETL com Python, Prefect, MinIO e DuckDB | **Aceito em 11/09/2026** | Linguagem (Python), arquitetura geral, substituição de ClickHouse por DuckDB, orquestrador (Prefect), armazenamento de objetos (MinIO), observabilidade (Elastic Stack), rejeição do NiFi na arquitetura principal |
| [0002](0002-identidade-e-versoes-na-tabela-de-ingestao.md) | Identidade e versões na tabela de ingestão tratada | **Aceito em 11/09/2026** | Grão da tabela de ingestão, chave primária por identidade de idempotência, preservação de versões, views de estado atual |
| [0003](0003-convergencia-do-insert-no-reprocessamento-do-lote.md) | Convergência do insert principal ao reexecutar um lote já carregado | **Aceito** | Insert da tabela de ingestão com `ON CONFLICT (idempotency_key) DO NOTHING`, preservação da proveniência da primeira gravação |
| [0004](0004-execucao-local-e-integracao-continua.md) | Execução local e integração contínua do ETL | **Proposto** | Ambiente local em contêineres, agendamento em processo, ferramenta e escopo do CI, framework de testes, exclusão do Deploy Contínuo |
| [0005](0005-checkpoint-confirmado-lote-a-lote-na-retomada.md) | Checkpoint confirmado lote a lote na retomada após falha parcial | **Aceito** | Confirmação do checkpoint de cada lote assim que ele termina de carregar, em vez de só ao final de todos os lotes do objeto |
| [0006](0006-observabilidade-estruturada-do-etl.md) | Observabilidade estruturada do ETL | **Aceito em 25/09/2026** | Sinais, transporte pela Elastic Stack, desacoplamento da carga e limites de implantação |
| [0007](0007-consumo-analitico-controlado.md) | Consumo analítico controlado dos cubos | **Proposto** | Acesso aos cubos por views governadas, perfis de leitura e separação entre contrato e implantação |
| [0008](0008-ratificacao-do-padrao-de-observabilidade-para-a-sprint-4.md) | Ratificação do padrão de observabilidade para a Sprint 4 | **Aceito** | Confirma Elastic Stack sem reabrir a escolha; redefine `task_id` como o `task_run.id` do Prefect; remove `event_id` do padrão; exige evento de transformação por lote |

## Cobertura do checklist de decisões técnicas

| Ponto exigido | ADR que o cobre | Observação |
| :--- | :--- | :--- |
| Linguagem | 0001 | Python em todas as camadas de dados; o orquestrador apenas coordena |
| Arquitetura | 0001 | Plano de dados em Python, plano de controle no Prefect, contratos independentes de tecnologia |
| Substituição de ClickHouse por DuckDB | 0001 | Autorização registrada; evidências e pendências em [`matriz-rastreabilidade-sprint3.md`](../matriz-rastreabilidade-sprint3.md) |
| Orquestrador | 0001 e 0004 | Prefect como plano de controle (0001); forma de servir o deployment (0004) |
| Observabilidade | 0001, 0006 e 0008 | Elastic Stack decidida (0001); sinais, transporte e desacoplamento da carga (0006); correlação por `task_id` e evento por lote da transformação (0008). Coletor, índice, painel Kibana, health check e alertas estão versionados em `docker-compose.yml` e `observability/` |
| Estratégia de execução local e CI | 0004 | Registra o ambiente declarado e o escopo real do pipeline de CI |
| Modelo de dados da ingestão | 0002 | Grão, identidade e versionamento da tabela de ingestão |
| Consumo dos cubos | 0007 | Define recortes governados e perfis de leitura; os cubos são materializados pela carga analítica e publicados em Parquet agregado para o modelo semântico |

## Situação do ADR 0001

A equipe ratificou o ADR em 11/09/2026 sem exigir que os nove critérios
listados nele estivessem todos cumpridos — o que segue em aberto vira
acompanhamento, não condição para a aceitação já registrada.

| Critério do ADR 0001 | Situação |
| :--- | :--- |
| Equipe aprovar a divisão de responsabilidades | Cumprido pela ratificação |
| Autorização do DuckDB registrada | Cumprido no próprio ADR e na matriz de rastreabilidade |
| Tarefas e critérios que citam ClickHouse ou NiFi atualizados | Cumprido: referências restantes são históricas ou do enunciado |
| Fluxo mínimo subir localmente por comando documentado | Cumprido por `docker-compose.yml` e `scripts/orchestration/run_ingest.py` |
| Publicação de fixture no MinIO disparar execução automática | Cumprido localmente: `scripts/orchestration/watch_landing.py` recebe a notificação `s3:ObjectCreated` (webhook) ou varre o prefixo (polling), coberto por `tests/orchestration/test_watch_landing.py`; a notificação do MinIO é configurada manualmente (runbook) |
| Execução das seis fontes com registro no Prefect e na Elastic Stack | Cumprido no ambiente local: o runner envia JSON por GELF ao Logstash, o Elasticsearch indexa em `etl-logs-*` e o painel Kibana (OB-08) consulta por fonte; roteiro e evidências no smoke OB-11 do runbook |
| Repetição do mesmo conteúdo produzir estado de ignorado | Cumprido no fluxo (`ingest_object` consulta `_control_object`) e testado no nível do flow (`tests/orchestration/test_orchestration_logs.py`, segunda entrega do mesmo objeto) |
| Retry, rejeição, idempotência e retomada com evidência automatizada | Cumprido: `tests/extraction` e `tests/load` por camada, `tests/orchestration/` no nível do flow (incluindo retomada de participações por posição e fronteira entre lotes) e `tests/e2e/` ponta a ponta |
| Documento de estimativa de custos com premissas e cenários | Cumprido: [`estimativa-custos-ambiente.md`](../estimativa-custos-ambiente.md) |

## Situação do ADR 0002

O grupo ratificou o ADR em 11/09/2026. Uma mudança de comportamento segue
pendente como acompanhamento, não como condição: a classificação de
duplicidade continua rejeitando correção do parceiro como conflito de
identidade. Os dois testes de `tests/load/test_identity_coupling.py` funcionam
como canário desse acoplamento e apontam para o ADR na mensagem de falha.

## Situação do ADR 0003

Decisão **Aceito** da camada de carga: o insert da tabela de ingestão converge
com `ON CONFLICT (idempotency_key) DO NOTHING`, sem sobrescrever a proveniência
da primeira gravação. Está implementada em
`src/etl/load/duckdb_repository.py` e coberta por `tests/load/test_reprocessing.py`.

## Situação do ADR 0004

É uma decisão nova, proposta junto com esta documentação. Ela registra o
ambiente e o CI que já existem, e depende da aprovação do grupo. O escopo
original (somente a camada de transformação) foi ampliado na Sprint 3: o
pipeline consolidado (VB-07/VB-08) cobre lint e a suíte inteira com cobertura
de todo o pacote `etl` (`--fail-under=85`).

## Situação do ADR 0005

Decisão **Aceito** da camada de carga: o checkpoint de cada lote passa a ser
confirmado assim que o próprio lote termina de carregar, não só depois que
todos os lotes do objeto tiverem passado — uma falha parcial preserva os
lotes já confirmados, e a retomada não reextrai nem retransmite o que já foi
carregado. Está implementada em `src/etl/orchestration/flow.py` e coberta por
`tests/orchestration/test_resumption.py`.

## Situação do ADR 0006

Decisão **Aceita em 25/09/2026**, com a integração de OB-03 a OB-11. Define a
Elastic Stack como destino da telemetria estruturada e determina que
indisponibilidade observacional não interfira na transação nem no checkpoint.
O ambiente local versionado passou a incluir Logstash, Elasticsearch e Kibana
(`docker-compose.yml`), o pipeline do coletor
(`observability/logstash/pipeline/etl.conf`), o painel operacional
(`observability/kibana/painel-operacional.ndjson`), o health check do Prefect e
do DuckDB (`scripts/orchestration/health_check.py`) e o smoke OB-11
(`scripts/orchestration/smoke_observabilidade.sh`). A não interferência do
coletor na carga é coberta por
`tests/e2e/test_telemetria_e_coletor_indisponivel.py`. Implantação fora do
ambiente local continua exigindo autenticação, retenção e aprovação próprias.

## Situação do ADR 0007

Decisão **Proposta** na Sprint 4. Define consumo por recortes governados, com
perfis separados para detalhe interno e agregados publicáveis. A carga
analítica materializa os quatro cubos no DuckDB e a publicação gera os
Parquet agregados consumidos pelo modelo semântico
(`powerbi/CentralPesquisasBI.SemanticModel`); o procedimento está em
[`acesso-cubos-bi.md`](../acesso-cubos-bi.md). A ADR não declara usuários,
publicação em serviço ou automação produtiva.

## Situação do ADR 0008

Decisão **Aceito** da Sprint 4 (OB-02): ratifica o padrão de observabilidade
do ADR 0001 sem trocar de stack e resolve três divergências achadas pelo
inventário OB-01 — `task_id` passa a ser o `task_run.id` do Prefect,
`event_id` sai do padrão por nunca ter sido implementado como campo próprio,
e a transformação passa a ter um evento de log por lote, simétrico ao de
extração e carga. Implementada por OB-03/OB-04 (`etl.orchestration.logging_config`,
`etl.transformation.log_events`).

## Nota de numeração

Até a auditoria da Sprint 3 (VB-10), este índice e o ADR de convergência do
insert usavam os dois o número 0003. A colisão foi resolvida renumerando o ADR
de execução local para 0004; referências em código (`duckdb_repository.py`)
sempre apontaram para o ADR de convergência e permanecem corretas. O ADR de
checkpoint por lote nasceu, por sua vez, também como 0004 numa branch paralela
à renumeração acima; resolvido como 0005 ao integrar as duas. Na Sprint 4, a
ratificação do padrão de observabilidade (OB-02) nasceu como 0006 numa branch
paralela ao ADR 0006 de observabilidade estruturada; ao integrar as duas, a
ratificação foi renumerada para 0008 e as referências em código e testes
foram atualizadas.
