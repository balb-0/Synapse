# Documento da solução — plano, execução e avaliação de qualidade

Seções do documento da solução que consolidam o **plano de tarefas de
validação**, o **estado da execução** e a **avaliação da qualidade técnica e
visual** dos reports. Complementa a
[seção de implementação](implementacao-reports.md); a conferência final
contra os critérios de avaliação fica no
[checklist](checklist-avaliacao.md).

## 1. Plano de tarefas

O plano de validação com usuários está fechado e versionado em
[`docs/usabilidade/`](../usabilidade/):

<div align="center">
<sub>Tabela 1 - Plano de validação: documento, conteúdo e quantidade de tarefas</sub><br>

| Documento | Conteúdo | Tarefas |
| :--- | :--- | :--- |
| [`perfis-e-criterios.md`](../usabilidade/perfis-e-criterios.md) | Perfis UC01–UC04 × PBs × RFs; critérios de aceite e testes já documentados; lacunas | base |
| [`tarefas-navegacao-filtros.md`](../usabilidade/tarefas-navegacao-filtros.md) | Navegação nas duas páginas e filtros planos (com limpeza e recorte vazio) | 6 |
| [`tarefas-detalhamento.md`](../usabilidade/tarefas-detalhamento.md) | Agregado → detalhe com justificativa; duas tarefas futuras fora da rodada | 4 |
| [`tarefas-comparacao-segmentacao.md`](../usabilidade/tarefas-comparacao-segmentacao.md) | Comparação por edição/divulgação e filtros simultâneos; uma tarefa fora da rodada | 5 |
| [`roteiro-execucao.md`](../usabilidade/roteiro-execucao.md) | Participantes P1–P4, ordem em blocos, métricas e guarda de evidência | roteiro |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

Das 15 tarefas planejadas, 12 estão na rodada e três dependem das páginas
Resultados/Qualidade ausentes (T-DET-03, T-DET-04 e T-SEG-02).

Toda tarefa tem situação real, passos esperados, critério de sucesso
observável e tempo aceitável; as métricas coletadas são conclusão, tempo,
desvio de caminho, erros e a justificativa do número (blocos C/D).

## 2. Execução

**Estado em 25/09/2026:** as sessões moderadas S1–S4 compõem a próxima etapa
do plano de usabilidade. As fichas de registro estão preparadas em
(`docs/usabilidade/execucao-navegacao-detalhamento.md` e
`docs/usabilidade/execucao-comparacao-segmentacao.md`), com identificação da
rodada, tabelas por sessão e conferência de precisão valor exibido × referência.

A Rodada 0 registrou o retorno do parceiro sobre a navegação e a leitura dos
indicadores nas duas páginas apresentadas com dados de demonstração. Seus
achados orientam as sessões moderadas e a conferência dos reports com os
cubos publicados. A composição das páginas e o mapeamento ao modelo analítico
estão descritos em [`solucao_dashboard.md`](../solucao_dashboard.md).

Regras já fixadas para a execução (roteiro, §6):

- fichas preenchidas **durante** a sessão, nunca de memória;
- executar somente as 12 tarefas do report de duas páginas; manter as três
  dependentes de Resultados/Qualidade fora do denominador, sem resultado presumido;
- nenhuma célula de resultado vazia, presumida ou copiada entre sessões.

Esta seção será atualizada com a síntese das rodadas (taxa de conclusão por
bloco, tarefas fora do tempo, desvios recorrentes, precisão dos valores)
quando as fichas forem preenchidas — os números finais entram aqui **somente
vindos das fichas**.

## 3. Avaliação de qualidade técnica

Critérios objetivos, herdados dos contratos do projeto, pelos quais os
reports são avaliados (cada um verificável tela a tela):

1. **Estados distintos** — vazio, indisponível, erro e acesso negado nunca se
   confundem; dado ausente nunca aparece como zero (§6.1.1; medidas DX-10).
2. **Denominador explícito** — toda taxa exibe numerador e denominador;
   denominador ausente → "indisponível" com motivo (RF04/RF05; protótipo já
   implementa `null`, nunca `0%`).
3. **Temporalidade rotulada** — RF01/RF03 pedem solicitação como padrão.
   As páginas entregues usam `ano_edicao` em Produção e ano de divulgação
   no Benchmark; esses desvios devem ficar explícitos no rótulo e na tarefa,
   sem afirmar que medem solicitações.
4. **Semiaditividade respeitada** — estoque mensal do pipeline não é somado
   entre períodos (contrato C03).
5. **Rastreabilidade** — cada número da tela final deve rastrear a um
   cubo/medida da [seção de implementação](implementacao-reports.md); a
   conferência dos valores contra o repositório analítico ainda depende da
   rodada de RP-11/US-07.
6. **Privacidade** — nenhuma tela expõe e-mail, identificador de pessoa ou
   resposta individual (regra LGPD do protótipo, mantida nos reports).

## 4. Avaliação de qualidade visual

Critérios de apresentação, todos já demonstrados no protótipo e exigidos das
telas finais (RP-09):

1. **Identificação completa** — cada gráfico com título, unidade e fonte;
   legenda presente quando há mais de uma série.
2. **Alternativa acessível** — tabela equivalente para cada visual;
   navegação por teclado; foco visível; contraste conforme WCAG AA.
3. **Reflow** — leitura íntegra até 320px e zoom de 400% sem transbordo
   (verificado no protótipo; a reverificar nas telas finais).
4. **Rótulos honestos** — "participação observada" (nunca "adesão" sem
   denominador); indicador bloqueado com motivo textual.
5. **Consistência entre telas** — mesma identidade visual, mesmos nomes para
   os mesmos conceitos, filtros com o mesmo comportamento (RP-07/RP-09).

A avaliação final (técnica e visual) é preenchida por tela após a execução
das sessões e a entrega das telas, com o resultado por critério — atendido,
não atendido (com evidência) ou não verificável (com motivo).
