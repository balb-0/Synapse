# Dashboard da Central de Pesquisas

## Visão geral

O dashboard organiza a leitura da operação da Central de Pesquisas em duas
perspectivas complementares:

- acompanhamento do volume e do ciclo das pesquisas;
- comparação da participação observada de uma empresa com o benchmark do
  recorte;

A estrutura das telas foi definida a partir dos relatórios e rascunhos
fornecidos pelo parceiro, preservando a finalidade de cada painel e adaptando
os visuais aos indicadores e dimensões disponíveis no modelo analítico.

## Produção e Volume

![Tela Produção e Volume](assets/dashboard/relatorio-producao-volume.png)

### Objetivo

Apresentar uma visão operacional do portfólio de pesquisas, permitindo
acompanhar volume, situação do ciclo, duração das etapas e prorrogações.

### Filtros

| Filtro | Uso |
| :--- | :--- |
| Ano | Define o período analisado. |
| Área | Restringe o portfólio à área selecionada. |
| Tipo | Restringe o portfólio ao tipo de pesquisa selecionado. |
| Status | Permite analisar as pesquisas por situação no ciclo. |
| Complexidade | Permite comparar o portfólio por nível de complexidade. |

### Indicadores e visuais

| Visual | Informação apresentada |
| :--- | :--- |
| Taxa de finalização | Percentual de pesquisas finalizadas no recorte. |
| Pesquisas | Quantidade total de pesquisas. |
| Pesquisas finalizadas | Quantidade de pesquisas finalizadas. |
| Pesquisas em aberto | Quantidade de pesquisas ainda abertas. |
| Ciclo médio em dias corridos | Duração média do ciclo completo. |
| Tempo por etapa e tipo | Duração das etapas de validação, coleta e tabulação por tipo, apresentada em dias úteis. |
| Pesquisas por status | Distribuição do portfólio por situação. |
| Volume por área | Distribuição das pesquisas por área. |
| Pesquisas prorrogadas | Quantidade e relação das pesquisas com prorrogação. |
| Acompanhamento das pesquisas | Pesquisa, status, área, tipo, ciclo total e entrega. |

### Base analítica

A tela utiliza principalmente o cubo C01 — Portfólio e Ciclo. Os principais
recortes são status, área, tipo, complexidade e tempo, com `data_solicitacao`
como marco temporal padrão quando aplicável.

## Implementação técnica — Produção e Volume

No modelo semântico, o cubo C01 é implementado pela tabela
`D01_CicloPesquisa`. Os visuais da tela utilizam as medidas abaixo. Os campos
de corte são mantidos na própria tabela do cubo porque esta versão do modelo
utiliza os atributos categóricos diretamente na tabela importada.

| Visual | Medida ou campos utilizados | Dimensões/cortes |
| :--- | :--- | :--- |
| Taxa de finalização | `Taxa de Finalização` | `status`, `area`, `tipo`, `complexidade`, `ano_edicao` |
| Pesquisas | `Pesquisas` | `pesquisa_id_origem`, `status`, `area`, `tipo`, `complexidade`, `ano_edicao` |
| Pesquisas finalizadas | `Pesquisas Finalizadas` | `status`, `area`, `tipo`, `complexidade`, `ano_edicao` |
| Pesquisas em aberto | `Pesquisas em Aberto` | `status`, `area`, `tipo`, `complexidade`, `ano_edicao` |
| Ciclo médio em dias corridos | `Ciclo Médio em Dias Corridos` | `data_solicitacao`, `data_entrega`, `area`, `tipo` |
| Tempo por etapa e tipo | `Ciclo Médio Validação em Dias Corridos`, `Ciclo Médio Coleta em Dias Corridos` e `Ciclo Médio Tabulação em Dias Corridos` | `tipo` e etapa do ciclo |
| Pesquisas por status | `Pesquisas` | `status` |
| Volume por área | `Pesquisas` | `area` |
| Pesquisas prorrogadas — cartão | `Pesquisas Prorrogadas` | `flag_prorrogada = TRUE()` |
| Pesquisas prorrogadas — tabela | `Pesquisas` e atributos do ciclo | `pesquisa_id_origem`, `titulo`, `area`, `status`, `data_prorrogacao` |
| Acompanhamento das pesquisas | `Pesquisas` e atributos do ciclo | `pesquisa_id_origem`, `titulo`, `status`, `area`, `tipo`, `dias_ciclo_total_corridos`, `data_entrega`, `flag_prorrogada` |

As colunas de duração são medidas em dias corridos. Valores ausentes não são
convertidos em zero: a função `AVERAGE` considera somente os valores
disponíveis, e um par de datas incompleto não representa uma duração válida.

## Benchmark Externo

![Tela Benchmark Externo](assets/dashboard/benchmark.png)

### Objetivo

Permitir que uma empresa compare sua participação observada com as demais
empresas do recorte selecionado.

O termo **participação observada** é utilizado porque o painel não representa
adesão, desempenho ou participação de mercado homologada.

### Filtros

| Filtro | Uso |
| :--- | :--- |
| Empresa | Seleciona a empresa analisada. |
| Pesquisa | Restringe o conjunto de pesquisas. |
| Ano | Define o período da comparação. |
| Área | Restringe a comparação à área selecionada. |
| Tipo | Restringe a comparação ao tipo de pesquisa selecionado. |

### Indicadores e visuais

| Visual | Informação apresentada |
| :--- | :--- |
| Pesquisas com participação | Quantidade de pesquisas com participação observada. |
| Empresas no recorte | Quantidade de empresas observadas. |
| Pesquisas no recorte | Quantidade de pesquisas consideradas na comparação. |
| Perfil de participação | Participação da empresa em comparação com o benchmark por área. |
| Evolução da participação | Comparação anual entre a empresa selecionada e o benchmark. |
| Posição no benchmark | Distribuição das empresas por faixa de participação. |
| Participação por pesquisa | Pesquisas, percentual agregado das demais empresas e participação da empresa selecionada. |

### Base analítica

A tela utiliza principalmente o cubo C02 — Participação e Representatividade,
com apoio das dimensões de pesquisa e tempo. O campo de participação de
mercado permanece sujeito à homologação da fonte oficial e não é tratado como
medida definitiva enquanto essa validação não existir.

## Implementação técnica — Benchmark Externo

No modelo semântico, o cubo C02 é implementado pela tabela
`D02_Participacao`. O relatório também utiliza as tabelas calculadas
`BE_Empresa`, `BE_Pesquisa` e `BE_Faixa` para representar a empresa escolhida,
o catálogo de pesquisas e as faixas do benchmark.

| Visual | Medida ou campos utilizados | Dimensões/cortes |
| :--- | :--- | :--- |
| Pesquisas com participação | `Pesquisas com Participação` ou `BE Pesquisas por empresa` | `BE_Pesquisa[Pesquisa]`, `BE_Pesquisa[Ano]`, `BE_Empresa[Empresa]` |
| Empresas no recorte | `BE Empresas observadas` | `BE_Pesquisa[Pesquisa]`, `BE_Pesquisa[Ano]`, `BE_Pesquisa[Área]`, `BE_Pesquisa[Tipo]` |
| Pesquisas no recorte | `BE Pesquisas no recorte` | `BE_Pesquisa[Pesquisa]`, `BE_Pesquisa[Ano]`, `BE_Pesquisa[Área]`, `BE_Pesquisa[Tipo]` |
| Perfil de participação | `BE % empresa por área` e `BE % demais por área` | `BE_Pesquisa[Área]`, `BE_Empresa[Empresa]` |
| Evolução da participação | `BE Pesquisas por ano` e `BE Média demais por ano` | `BE_Pesquisa[Ano]`, `BE_Empresa[Empresa]` |
| Posição no benchmark | `BE Empresas por faixa` e `BE Selecionada por faixa` | `BE_Faixa[Faixa]`, `BE_Empresa[Empresa]` |
| Participação por pesquisa | `BE Percentual sem registro`, `BE % observado Top 8` e `BE Empresa participou` | `BE_Pesquisa[Pesquisa]`, `BE_Empresa[Empresa]` |

O filtro de ano do Benchmark é derivado de `BE_Pesquisa[Ano]`, calculado a
partir de `D01_CicloPesquisa[data_divulgacao]`. Os filtros de área e tipo
também são disponibilizados por `BE_Pesquisa` e aplicados ao fato de
participação pela chave de pesquisa.

## Relacionamentos e propagação de filtros

Os fatos `D01_CicloPesquisa` e `D02_Participacao` são tabelas importadas
independentes. Não há relacionamento fato–fato entre elas. O relacionamento
entre a seleção do Benchmark e o fato de participação é virtual, aplicado
pelas medidas DAX com `TREATAS`:

- `BE_Pesquisa[ID Pesquisa]` é aplicado sobre
  `D02_Participacao[pesquisa_id_origem]`;
- `BE_Empresa[ID Empresa]` é aplicado sobre
  `D02_Participacao[empresa_id_duravel]`;
- `BE_Faixa` fornece os limites `Minimo` e `Maximo` usados no cálculo das
  faixas e não precisa de relacionamento físico com o fato.

`BE_Pesquisa` é derivada de `D01_CicloPesquisa`, enquanto `BE_Empresa` é
derivada de `D02_Participacao`. Por isso, os filtros dessas tabelas auxiliares
não devem ser interpretados como relacionamentos físicos tradicionais entre
os cubos. A propagação é controlada explicitamente pelas medidas, evitando
criar uma relação direta entre participação e ciclo que poderia duplicar ou
alterar a granularidade dos dados.

Na tela Produção e Volume, os filtros são aplicados diretamente às colunas de
`D01_CicloPesquisa`. Na tela Benchmark, os filtros de empresa, pesquisa, ano,
área e tipo são aplicados pelas medidas sobre o recorte de `D02_Participacao`.
Quando uma medida precisa comparar a empresa selecionada com as demais, ela
remove somente o filtro de empresa e preserva os demais filtros do usuário.

## Regras DAX dos indicadores

As medidas personalizadas implementam as regras de negócio abaixo:

| Medida | Regra de cálculo |
| :--- | :--- |
| `Pesquisas` | Conta pesquisas distintas por `pesquisa_id_origem` no contexto atual. |
| `Pesquisas Finalizadas` | Aplica `status = "Finalizada"` sobre `Pesquisas`. |
| `Pesquisas em Aberto` | Considera os status `Em andamento`, `Em tabulação` e `Planejada`. |
| `Taxa de Finalização` | Divide `Pesquisas Finalizadas` por `Pesquisas` usando `DIVIDE`, evitando erro de denominador zero. |
| `Pesquisas Prorrogadas` | Filtra `flag_prorrogada = TRUE()` e conta pesquisas distintas. |
| `Ciclo Médio em Dias Corridos` | Calcula a média de `dias_ciclo_total_corridos`, ignorando valores nulos. |
| `Pesquisas com Participação` | Conta pesquisas distintas no fato `D02_Participacao`. |
| `BE Empresas observadas` | Conta empresas distintas não nulas, removendo apenas o filtro da empresa e preservando o recorte de pesquisas. |
| `BE Pesquisas da empresa` | Exige uma única empresa selecionada e aplica sua chave ao fato com `TREATAS`. |
| `BE Demais empresas` | Remove a empresa selecionada e conta somente as demais empresas no mesmo recorte. |
| `BE Percentual observado` | Divide as demais empresas pelo denominador observado do recorte; denominador zero resulta em vazio. |
| `BE % empresa por área` | Divide as pesquisas da empresa pelo total da própria empresa nas áreas selecionadas. |
| `BE % demais por área` | Calcula a média do percentual das demais empresas, preservando as áreas selecionadas. |
| `BE Empresas por faixa` | Conta empresas dentro dos limites `Minimo` e `Maximo` da faixa selecionada, excluindo a empresa analisada. |
| `BE Selecionada por faixa` | Marca a faixa que contém a quantidade de pesquisas da empresa selecionada. |
| `BE Empresa participou` | Retorna `Sim` ou `Não` conforme exista registro da empresa na pesquisa; sem seleção única, solicita a seleção de uma empresa. |
| `BE % observado Top 8` | Usa `RANKX` para limitar a exibição às oito pesquisas mais relevantes sem alterar a medida base. |

As medidas do Benchmark usam `HASONEVALUE` para evitar interpretações sem uma
empresa selecionada, `REMOVEFILTERS` para construir o grupo comparável,
`KEEPFILTERS` para preservar os filtros ativos e `ALLSELECTED` para manter o
recorte escolhido pelo usuário ao calcular denominadores e percentuais.

As medidas representam participação observada no conjunto disponível. Elas não
calculam adesão, desempenho ou participação de mercado oficial. O campo
`pct_mercado_na_participacao` permanece fora dos indicadores oficiais até que
a fonte autoritativa seja homologada.

## Acessibilidade e identidade visual

As telas utilizam uma identidade visual única, com navegação lateral, títulos
descritivos, filtros agrupados e hierarquia visual consistente. Os indicadores
foram organizados para que o usuário consiga identificar o contexto antes de
interpretar os valores.

Foram priorizados os seguintes critérios:

- títulos que descrevem o conteúdo do visual;
- rótulos que preservam o significado original das medidas;
- unidades e períodos identificáveis;
- contraste entre texto, fundo e elementos gráficos;
- tabelas para leitura dos valores detalhados;
- indicação textual para resultados bloqueados ou indisponíveis;
- ordem de leitura coerente entre filtros, indicadores e visuais.

A verificação final de contraste, foco e navegação por teclado deve ser
realizada no Power BI Desktop com as telas finais abertas, pois esses aspectos
dependem também da renderização do ambiente.

## Limites da versão atual

O layout e a organização das páginas estão definidos, mas a fonte atualmente
utilizada no projeto é uma camada simulada em CSV. Por isso, os valores exibidos
servem para validar a composição e a leitura dos reports, não para representar
uma publicação definitiva da camada Gold.

A conexão com os cubos publicados em Parquet deve ser feita quando o caminho
oficial de consumo da camada Gold estiver fechado e disponibilizado para o
ambiente do dashboard.

## Referência de estrutura

A seleção das páginas, filtros, visuais e indicadores está detalhada em
[`estrutura-dashboards.md`](solucao-dashboards/estrutura-dashboards.md), que consolida a relação
entre os relatórios do parceiro, os cubos analíticos e a finalidade de cada
tela.
