# Índice das decisões arquiteturais (AN-03)

Registro das decisões técnicas do ETL da Sprint 3, com o status **verbatim** de
cada ADR e o ponto do checklist do enunciado que ela cobre. O índice não altera
nenhuma decisão: ele mostra o que já foi decidido, por quem, em que estado, e o
que ainda falta para cada decisão ser considerada firme.

O enunciado exige justificativa de linguagem, arquitetura, frameworks e
ferramentas. As cinco ADRs abaixo cobrem esses pontos. Nenhuma delas pressupõe
Deploy Contínuo, que está fora do escopo da sprint.

## Decisões registradas

| ADR | Título | Status | Decisões que cobre |
| :--- | :--- | :--- | :--- |
| [0001](0001-arquitetura-etl-python-prefect-minio-duckdb.md) | Arquitetura do ETL com Python, Prefect, MinIO e DuckDB | **Aceito em 11/09/2026** | Linguagem (Python), arquitetura geral, substituição de ClickHouse por DuckDB, orquestrador (Prefect), armazenamento de objetos (MinIO), observabilidade (Elastic Stack), rejeição do NiFi na arquitetura principal |
| [0002](0002-identidade-e-versoes-na-tabela-de-ingestao.md) | Identidade e versões na tabela de ingestão tratada | **Aceito em 11/09/2026** | Grão da tabela de ingestão, chave primária por identidade de idempotência, preservação de versões, views de estado atual |
| [0003](0003-convergencia-do-insert-no-reprocessamento-do-lote.md) | Convergência do insert principal ao reexecutar um lote já carregado | **Aceito** | Insert da tabela de ingestão com `ON CONFLICT (idempotency_key) DO NOTHING`, preservação da proveniência da primeira gravação |
| [0004](0004-execucao-local-e-integracao-continua.md) | Execução local e integração contínua do ETL | **Proposto** | Ambiente local em contêineres, agendamento em processo, ferramenta e escopo do CI, framework de testes, exclusão do Deploy Contínuo |
| [0005](0005-checkpoint-confirmado-lote-a-lote-na-retomada.md) | Checkpoint confirmado lote a lote na retomada após falha parcial | **Aceito** | Confirmação do checkpoint de cada lote assim que ele termina de carregar, em vez de só ao final de todos os lotes do objeto |
| [0006](0006-ratificacao-do-padrao-de-observabilidade-para-a-sprint-4.md) | Ratificação do padrão de observabilidade para a Sprint 4 | **Aceito** | Confirma Elastic Stack sem reabrir a escolha; redefine `task_id` como o `task_run.id` do Prefect; remove `event_id` do padrão; exige evento de transformação por lote |

## Cobertura do checklist de decisões técnicas

| Ponto exigido | ADR que o cobre | Observação |
| :--- | :--- | :--- |
| Linguagem | 0001 | Python em todas as camadas de dados; o orquestrador apenas coordena |
| Arquitetura | 0001 | Plano de dados em Python, plano de controle no Prefect, contratos independentes de tecnologia |
| Substituição de ClickHouse por DuckDB | 0001 | Autorização registrada; evidências e pendências em [`matriz-rastreabilidade-sprint3.md`](../matriz-rastreabilidade-sprint3.md) |
| Orquestrador | 0001 e 0004 | Prefect como plano de controle (0001); forma de servir o deployment (0004) |
| Observabilidade | 0001 e 0006 | Elastic Stack decidida (0001); **não integrada ao `develop`**, conforme a matriz de rastreabilidade; correlação por `task_id`/`event_id` esclarecida para a Sprint 4 (0006) |
| Estratégia de execução local e CI | 0004 | Registra o ambiente declarado e o escopo real do pipeline de CI |
| Modelo de dados da ingestão | 0002 | Grão, identidade e versionamento da tabela de ingestão |

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
| Publicação de fixture no MinIO disparar execução automática | **Ainda não cumprido**: o adaptador de eventos não existe |
| Execução das seis fontes com registro no Prefect e na Elastic Stack | **Ainda não cumprido**: não há observabilidade integrada |
| Repetição do mesmo conteúdo produzir estado de ignorado | Cumprido no fluxo (`ingest_object` consulta `_control_object`), sem teste automatizado no nível do flow |
| Retry, rejeição, idempotência e retomada com evidência automatizada | Parcial: coberto em `tests/extraction` e `tests/load`; coberto também no nível do flow por `tests/orchestration/` (VB-05) e ponta a ponta em `tests/e2e/` (VB-04) |
| Documento de estimativa de custos com premissas e cenários | **Ainda pendente** |

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

Decisão **Aceito** da Sprint 4 (OB-02): ratifica o padrão de observabilidade
do ADR 0001 sem trocar de stack, e resolve três divergências achadas pelo
inventário OB-01 — `task_id` passa a ser o `task_run.id` do Prefect,
`event_id` sai do padrão por nunca ter sido implementado como campo próprio,
e a transformação passa a ter um evento de log por lote, simétrico ao de
extração e carga. Implementação fica com OB-03/OB-04; esta decisão não altera
código.

## Nota de numeração

Até a auditoria da Sprint 3 (VB-10), este índice e o ADR de convergência do
insert usavam os dois o número 0003. A colisão foi resolvida renumerando o ADR
de execução local para 0004; referências em código (`duckdb_repository.py`)
sempre apontaram para o ADR de convergência e permanecem corretas. O ADR de
checkpoint por lote nasceu, por sua vez, também como 0004 numa branch paralela
à renumeração acima; resolvido como 0005 ao integrar as duas.
