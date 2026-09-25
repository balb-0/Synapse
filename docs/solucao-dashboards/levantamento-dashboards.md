# Levantamento inicial dos dashboards

Este documento registra a proposta de estruturação dos dashboards antes da
etapa de construção dos reports.

Os rascunhos fornecidos pelo parceiro foram utilizados como ponto de partida
para compreender a finalidade, a narrativa e os principais elementos de cada
tela. A estrutura abaixo foi então organizada com base nas informações
disponíveis no projeto e no que fazia sentido para responder às perguntas de
negócio de cada painel. Assim, o resultado não pretende reproduzir o rascunho
literalmente: ele preserva sua intenção e adapta a composição dos visuais,
indicadores e filtros ao contexto analítico disponível.

O levantamento se limita à definição das telas, dos visuais, dos indicadores
e dos filtros. Não define ainda medidas DAX, relacionamentos, regras de
interação, testes ou conexão física com a camada de dados.

## 1. Relatório 01 — Produção & Volume

![Rascunho do Relatório 01 — Produção & Volume](../assets/prototipos-dashboards/imagens/rascunho-relatorio-01.png)

**Objetivo:** oferecer uma visão operacional do volume de pesquisas, da situação
do portfólio, do tempo de ciclo e das pesquisas prorrogadas.

### 1.1 Filtros da tela

| Filtro | Finalidade |
| :--- | :--- |
| Ano | Definir o período de análise das pesquisas. |
| Área | Restringir o portfólio à área selecionada. |
| Tipo | Restringir o portfólio ao tipo de pesquisa selecionado. |
| Status | Analisar pesquisas em diferentes situações do ciclo. |
| Complexidade | Comparar o portfólio por nível de complexidade. |

Os filtros deverão atuar sobre os visuais da tela, preservando o mesmo recorte
de análise. O período deverá ser identificado de acordo com o marco temporal
utilizado, sem misturar datas de solicitação, divulgação ou entrega.

### 1.2 Visuais e indicadores previstos

| Visual | Tipo | Indicador ou informação apresentada |
| :--- | :--- | :--- |
| Taxa de finalização | Cartão | Percentual de pesquisas finalizadas no recorte. |
| Pesquisas | Cartão | Quantidade de pesquisas no recorte selecionado. |
| Pesquisas finalizadas | Cartão | Quantidade de pesquisas com status finalizado. |
| Pesquisas em aberto | Cartão | Quantidade de pesquisas ainda abertas. |
| Ciclo médio em dias corridos | Cartão | Média do tempo total do ciclo, identificada em dias corridos. |
| Tempo por etapa e tipo | Colunas agrupadas | Duração das etapas de validação, coleta e tabulação, distribuída por tipo de pesquisa. |
| Pesquisas por status | Barras horizontais | Quantidade de pesquisas em cada status. |
| Volume por área | Barras horizontais | Quantidade de pesquisas por área. |
| Pesquisas prorrogadas | Cartão | Quantidade de pesquisas que possuem prorrogação. |
| Pesquisas prorrogadas | Tabela | Relação das pesquisas prorrogadas, com pesquisa e área. |
| Acompanhamento das pesquisas | Tabela | Pesquisa, status, área, tipo, ciclo total, entrega e indicação de prorrogação. |

O rascunho sugeria uma leitura de volume por mês e uma distribuição por tipo.
Na proposta estruturada, a leitura operacional será organizada principalmente
por status, etapa/tipo e área, pois esses recortes respondem de forma mais
direta ao acompanhamento do portfólio disponível. A comparação com meta anual
ou com o ano anterior não será tratada como medida adicional sem regra e fonte
definidas.

## 2. Relatório 10 — Benchmark Externo

![Rascunho do Relatório 10 — Benchmark Externo](../assets/prototipos-dashboards/imagens/rascunho-relatorio-10.png)

**Objetivo:** permitir a comparação da participação observada de uma empresa
com o benchmark formado pelas demais empresas do recorte.

O termo “participação observada” será utilizado para evitar que o painel seja
interpretado como medida de adesão, desempenho ou participação de mercado
homologada.

### 2.1 Filtros da tela

| Filtro | Finalidade |
| :--- | :--- |
| Empresa | Selecionar a empresa analisada. |
| Pesquisa | Restringir o conjunto de pesquisas do benchmark. |
| Ano | Definir o período da comparação. |
| Área | Analisar a participação dentro de uma área. |
| Tipo | Restringir a comparação ao tipo de pesquisa selecionado. |

### 2.2 Visuais e indicadores previstos

| Visual | Tipo | Indicador ou informação apresentada |
| :--- | :--- | :--- |
| Pesquisas com participação | Cartão | Quantidade de pesquisas nas quais houve participação observada. |
| Empresas no recorte | Cartão | Quantidade de empresas observadas no recorte. |
| Pesquisas no recorte | Cartão | Quantidade de pesquisas consideradas no benchmark. |
| Perfil de participação | Barras horizontais | Proporção de participação da empresa selecionada em comparação com o benchmark agregado, por área. |
| Evolução da participação | Colunas agrupadas | Quantidade de pesquisas por ano, comparando a empresa selecionada com o benchmark agregado. |
| Posição no benchmark | Distribuição por faixas | Distribuição das empresas por faixa de participação, destacando a faixa da empresa selecionada. |
| Participação por pesquisa | Tabela | Pesquisa, percentual agregado das demais empresas e indicação se a empresa selecionada participou. |

O rascunho sugeria cartões de quartil, diferença para a média, quantidade de
indicadores e uma tabela de liderança. Esses elementos orientam a intenção de
comparação, mas a estrutura proposta prioriza os indicadores e recortes que
podem ser explicados diretamente pela participação observada disponível. Não
serão criadas métricas de quartil, média ou liderança sem regra estatística,
denominador e fonte definidos.

## 3. Escopo do levantamento

O levantamento contempla somente:

- as duas telas apresentadas nos rascunhos do parceiro;
- os visuais necessários para responder aos objetivos de cada painel;
- os indicadores que deverão ser acompanhados em cada visual;
- os filtros de recorte de cada tela;
- a adaptação do rascunho às informações disponíveis no projeto.

Ficam para etapas posteriores a implementação dos reports, a criação das
medidas, a configuração do modelo semântico, a validação dos valores, os
testes de navegação e a avaliação de usabilidade.

## 4. Referências

- Rascunho do parceiro: `rascunho-relatorio-01.png`.
- Rascunho do parceiro: `rascunho-relatorio-10.png`.
- [Proposta dos dashboards da Sprint 4](../proposta-dashboards-sprint-4.md).
- [Data Model Canvas](../dmc.md), utilizado como referência conceitual para os
  temas e indicadores já existentes no projeto.

