# Documento da solução — checklist contra os critérios de avaliação

Conferência final do documento da solução de dashboards contra os critérios
de avaliação da sprint. Regra do checklist: **nenhum item é marcado sem
evidência apontada** (link ou âncora); item com achado grave ou impeditivo
aberto fica **parcial**, com o que falta declarado — o estado de cada um
reflete a data da conferência.

**Conferência atualizada em 06/10/2026**, após as sessões S1–S4 sobre as
páginas finais do RP-17 e a geração v3. A descrição completa está em
[`solucao_dashboard.md`](../solucao_dashboard.md).

## Checklist

<div align="center">
<sub>Tabela 1 - Critério de avaliação, evidência e estado</sub><br>

| Critério | Evidência | Estado |
| :--- | :--- | :--- |
| Implementação técnica com cubos de dados | Cubos e tabelas por página, medidas e dimensões por visual, relacionamentos, filtros, hierarquias, medidas DAX e adaptações justificadas ([§2 da solução](../solucao_dashboard.md#2-implementação-dos-reports-com-base-nos-cubos)) | **Atendido** — as hierarquias do modelo ainda não estão nos eixos (A06), declarado como estado real |
| Plano de tarefas para usabilidade | 16 tarefas com página, grão, estado esperado, critério de sucesso e tempo; roteiro, preparação e valores de referência ([§3 da solução](../solucao_dashboard.md#3-plano-de-tarefas-para-testes-de-usabilidade); [`docs/usabilidade/`](../usabilidade/)) | **Atendido** |
| Validação funcional dos reports | S1–S4 executadas: 17 de 17 valores conferidos, 9 de 9 verificações de coerência, respostas abaixo de 2 s, taxa de sucesso de 59% e conclusão de 88% ([§4 da solução](../solucao_dashboard.md#4-execução-e-validação-das-tarefas); [fichas S1–S2](../usabilidade/execucao-navegacao-detalhamento.md); [fichas S3–S4](../usabilidade/execucao-comparacao-segmentacao.md)) | **Parcial** — dois impeditivos encaminhados: estoque sem motivo (A15) e comparação temporal sem mês de resposta na v3 (A17) |
| Qualidade visual e interativa | Avaliação dos cinco critérios de qualidade ([§5 da solução](../solucao_dashboard.md#5-avaliação-da-qualidade-técnica-e-funcional)) | **Parcial** — filtros não sincronizados entre páginas (A12), sem drill-down nos eixos (A06) e estados `sem dado` exibidos em branco |
| Aderência à arquitetura analítica | Páginas consomem só a geração Parquet; dimensões conformadas em direção única; médias ponderadas pela base; indicadores sem fonte com motivo ([§2.3–2.5](../solucao_dashboard.md#23-relacionamentos-entre-fatos-e-dimensões)) | **Atendido** |
| Limitações com análise crítica e proposta | 23 achados classificados por tipo e severidade, com proposta, destino e reteste ([`limitacoes-e-propostas.md`](../usabilidade/limitacoes-e-propostas.md); [§6 da solução](../solucao_dashboard.md#6-limitações-efetivas-e-propostas)) | **Atendido** |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

## Pendências que mudam estado

| Pendência | Item(ns) afetado(s) | Passa a valer quando |
| :--- | :--- | :--- |
| Exibir `Estado do Estoque` nas páginas (A15) | Validação funcional; qualidade visual | T-NAV-02 reexecutada com o motivo visível |
| Mês de resposta em C02 ou aviso no lugar da barra vazia (A17) | Validação funcional | T-CMP-01 e T-CMP-02 reexecutadas |
| Sincronização dos slicers entre páginas (A12) | Qualidade visual e interativa | T-DET-03 e T-SEG-02 reexecutadas sem perda de filtro |
| Hierarquias nos eixos (A06) | Qualidade visual e interativa; implementação | T-DET-01 concluída por drill-down |

## Indexação

Este documento e as demais partes da solução de dashboards ficam indexados no
[`docs/index.md`](../index.md), nas entradas de usabilidade e do documento da
solução.
