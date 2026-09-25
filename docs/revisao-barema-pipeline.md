# Revisão acadêmica da especificação do pipeline ETL

**Data:** 25/09/2026. Referência: especificação técnica fornecida para ETL Python, orquestração, observabilidade, CI, testes e cinco visões ISO/IEC 10746. Esta revisão confronta o enunciado com artefatos versionados. Documentação de intenção não é tomada como evidência de execução.

| Critério | Evidência concreta | Resultado e limite |
| :--- | :--- | :--- |
| Arquitetura e modularidade | `src/etl/extraction/`, `transformation/`, `load/`, `orchestration/` e `analytics/`; [visões](visao-negocio-etl.md) e [ADR 0001](adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md) | Separação de módulos verificável no código. Baixo acoplamento/reuso exige inspeção e testes de integração, não apenas estrutura de pastas. |
| Qualidade do pipeline, validação e retry | [testes de extração](../tests/extraction/), [transformação](../tests/transformation/), [carga](../tests/load/), [orquestração](../tests/orchestration/) e [compensação](compensacao-e-retomada-de-carga.md) | Cenários automatizados e política de retomada versionados. Taxa de sucesso em operação e todos os casos de borda não podem ser inferidos dos testes. |
| Orquestração | [flows Prefect](../src/etl/orchestration/flow.py), [deployments](../prefect.yaml), [compose](../docker-compose.yml) e [smoke registrado](smoke-orquestracao-sprint4.md) | Há evidência documental de UI, execução, falha e reexecução. O smoke demonstra reenvio idempotente; não equivale por si só a recuperação da mesma falha por retry. |
| CI e testes automatizados | [GitLab CI](../.gitlab-ci.yml) executa Ruff, suíte `unittest`, XML JUnit e coverage com mínimo de 85%; [estratégia](estrategia-de-testes.md) e [gate histórico](gate-final-sprint3.md) | Configuração bloqueia falha de lint/teste/cobertura. O gate de 93% é histórico da Sprint 3, não resultado desta revisão. Não há CD, conforme escopo. A especificação cita flake8/pylint como exemplos; a implementação escolheu Ruff. |
| Observabilidade | [eventos e lacunas inventariadas](inventario-telemetria-observabilidade.md), logs da [extração](../src/etl/extraction/log_events.py), [carga](../src/etl/load/log_events.py) e [orquestração](../src/etl/orchestration/flow.py) | Logs e algumas contagens/durações são emitidos. O inventário registra retries descartados por recorder nulo e telemetria não exportada. [Visão de tecnologia](visao-tecnologia-etl.md) escolhe Elastic Stack, mas a marca como não integrada. O [compose](../docker-compose.yml) contém health checks de serviços; isso não comprova painel, alertas nem coleta ponta a ponta. |
| Documentação arquitetural e UML | [cinco visões](visao-negocio-etl.md), [índice](index.md) e diagramas ligados nas visões | Material versionado; a conformidade depende de confrontar cada diagrama com o código e implantação vigente. |

## Inconsistências e correções necessárias

1. **Stack de observabilidade:** a especificação inicial oferecia Prometheus ou OpenTelemetry. O projeto registra Elastic Stack como decisão posterior. A formulação correta para esta entrega é **decisão Elastic Stack, integração ainda não comprovada pelo inventário**; não afirmar coleta Prometheus/OpenTelemetry nem dashboards operacionais prontos sem evidência.
2. **Métrica calculada versus exposta:** `duration_ms`, contagens por lote e resultados de transformação aparecem em pontos diferentes do fluxo. Um log em `extra` não prova série temporal consultável ou alerta. Critério de aceite: emitir nas quatro etapas, transportar ao coletor, consultar por `run_id`/`task_id`, demonstrar painel e disparo de alerta.
3. **Retry e retomada:** reprocessar um objeto já carregado sem duplicá-lo comprova idempotência. Para comprovar reinício de falha, registrar a tentativa que falhou, a tentativa seguinte e o mesmo lote/checkpoint ou uma justificativa técnica da reexecução.
4. **CI:** o limiar de 85% está no arquivo de configuração. A aprovação de um MR específico depende do job daquele MR; cobertura histórica não comprova cobertura atual.

## Evidências ainda necessárias

- Saída recente do CI da branch final, com lint, testes, XML e cobertura.
- Demonstração atual do coletor, painel operacional e alertas sobre falha/indisponibilidade, com configuração versionada ou capturas identificadas.
- Teste de falha transitória seguido de retry/retomada com correlação e reconciliação do lote; o smoke histórico documenta falha permanente e reenvio idempotente.
- Revisão dos diagramas UML contra as interfaces e deployments finais.

Estas pendências não foram preenchidas por suposição. O [dashboard analítico](solucao_dashboard.md) tem sua própria avaliação e não substitui o painel operacional da ETL.
