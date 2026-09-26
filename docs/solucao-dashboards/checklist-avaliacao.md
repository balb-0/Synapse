# Documento da solução — checklist contra os critérios de avaliação

Conferência final do documento da solução de dashboards contra os critérios
de avaliação da sprint. Regra do checklist: **nenhum item é marcado sem
evidência apontada** (link ou âncora); item que depende de entrega pendente
fica **parcial**, com o que falta declarado — o estado de cada um reflete a
data da conferência.

**Conferência atualizada em 25/09/2026.** A descrição das páginas e do modelo
analítico está em [`solucao_dashboard.md`](../solucao_dashboard.md).

## Checklist

<div align="center">
<sub>Tabela 1 - Critério de avaliação, evidência e estado</sub><br>

| Critério | Evidência | Estado |
| :--- | :--- | :--- |
| Implementação dos reports com cubos | [`implementacao-reports.md`](implementacao-reports.md): tabela visual → cubo (C01–C04/perfilamento), relacionamentos, hierarquias e medidas personalizadas com estado [contrato]/[pendente] | **Parcial** — contrato completo; materialização depende de DX-05..10 e RP-03..09 |
| Plano de tarefas de validação | [`plano-execucao-avaliacao.md` §1](plano-execucao-avaliacao.md) e os cinco documentos de [`docs/usabilidade/`](../usabilidade/) (15 tarefas + roteiro com participantes e métricas) | **Atendido** |
| Validação funcional | Critérios de aceite por RF (§6.1.1 do [`projeto.md`](../projeto.md)) e testes de usuário (§6.1.2); execução de usabilidade com fichas prontas ([execução §2](plano-execucao-avaliacao.md)) | **Parcial** — critérios e fichas prontos; sessões aguardam RP-08 |
| Qualidade visual dos reports | Critérios objetivos em [`plano-execucao-avaliacao.md` §4](plano-execucao-avaliacao.md); protótipo já demonstra WCAG AA, tabela equivalente, reflow 320px e rótulos honestos ([README do protótipo](../assets/prototipos-dashboards/README.md)) | **Parcial** — demonstrado no protótipo; a reverificar nas telas finais |
| Aderência à arquitetura analítica | Visual→cubo previsto na [Tabela 1 da implementação](implementacao-reports.md); as páginas demonstram a interface e o modelo Parquet define o consumo agregado ([detalhes](../solucao_dashboard.md)) | **Parcial** — integração das páginas à geração publicada é a próxima etapa |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

## Pendências que mudam estado

| Pendência | Item(ns) afetado(s) | Passa a valer quando |
| :--- | :--- | :--- |
| Telas dos reports (RP-03..09) | Implementação; qualidade visual | telas mergeadas e reverificadas critério a critério |
| Modelo semântico e medidas (DX-05..10) | Implementação | medidas publicadas e conferidas (DX-11) |
| Sessões de usabilidade (US-06/07) | Validação funcional | fichas preenchidas e sintetizadas |
| Conferência de valores (RP-11) | Validação funcional | valor exibido × medida do modelo anexado |

## Indexação

Este documento e as demais partes da solução de dashboards ficam indexados no
[`docs/index.md`](../index.md), nas entradas de usabilidade e do documento da
solução.
