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

Captura histórica com dados sintéticos. O título do gráfico de etapas foi
corrigido no PBIR para dias corridos; a imagem ainda não foi recapturada.

### Objetivo

Apresentar uma visão operacional do portfólio de pesquisas, permitindo
acompanhar volume, situação do ciclo, duração das etapas e prorrogações.

### Filtros

| Filtro | Uso |
| :--- | :--- |
| Ano | Filtra `D01_CicloPesquisa[ano_edicao]`; não representa ano de solicitação. |
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
| Tempo por etapa e tipo | Duração média das etapas de validação, coleta e tabulação por tipo, apresentada em dias corridos nesta versão. |
| Pesquisas por status | Distribuição do portfólio por situação. |
| Volume por área | Distribuição das pesquisas por área. |
| Pesquisas prorrogadas | Quantidade e relação das pesquisas com prorrogação. |
| Acompanhamento das pesquisas | Pesquisa, status, área, tipo, ciclo total e entrega. |

### Base analítica

A tela está alinhada ao tema do cubo C01 — Portfólio e Ciclo. Os principais
recortes são status, área, tipo, complexidade e ano da edição. Nesta página, o filtro temporal é `ano_edicao`, não `data_solicitacao`.
O ano do Benchmark deriva de `data_divulgacao`; os dois marcos não são
equivalentes e não devem ser comparados como solicitações.

## Implementação técnica — Produção e Volume

No modelo semântico do report, o tema do cubo C01 é representado pela tabela
`D01_CicloPesquisa`. Os visuais da tela utilizam as medidas abaixo. Os campos
de corte são mantidos na própria tabela do cubo porque esta versão do modelo
utiliza os atributos categóricos diretamente na tabela importada.

| Visual | Medida ou campos utilizados | Dimensões/cortes |
| :--- | :--- | :--- |
| Taxa de finalização | `Taxa de Finalização` | `status`, `area`, `tipo`, `complexidade`, `ano_edicao` |
| Pesquisas | `Pesquisas` | `pesquisa_id_origem`, `status`, `area`, `tipo`, `complexidade`, `ano_edicao` |
| Pesquisas finalizadas | `Pesquisas Finalizadas` | `status`, `area`, `tipo`, `complexidade`, `ano_edicao` |
| Pesquisas em aberto | `Pesquisas em Aberto` | `status`, `area`, `tipo`, `complexidade`, `ano_edicao` |
| Ciclo médio em dias corridos | `Ciclo Médio em Dias Corridos` | `area`, `tipo`, `status`, `ano_edicao` |
| Tempo por etapa e tipo | `Ciclo Médio Validação em Dias Corridos`, `Ciclo Médio Coleta em Dias Corridos` e `Ciclo Médio Tabulação em Dias Corridos` | `tipo` e etapa do ciclo |
| Pesquisas por status | `Pesquisas` | `status` |
| Volume por área | `Pesquisas` | `area` |
| Pesquisas prorrogadas — cartão | `Pesquisas Prorrogadas` | `flag_prorrogada = TRUE()` |
| Pesquisas prorrogadas — tabela | Atributos do ciclo | `titulo`, `area`; filtro do visual por `flag_prorrogada` |
| Acompanhamento das pesquisas | Atributos do ciclo | `titulo`, `status`, `area`, `tipo`, `dias_ciclo_total_corridos`, `data_entrega` |

As colunas de duração são medidas em dias corridos. Valores ausentes não são
convertidos em zero: a função `AVERAGE` considera somente os valores
disponíveis, e um par de datas incompleto não representa uma duração válida.

## Benchmark Externo — V2

![Tela Benchmark Externo — V2](assets/dashboard/benchmark.png)

Captura histórica com dados sintéticos, anterior à correção do denominador
da coorte por área. A execução DAX e a nova captura permanecem pendentes.

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

A tela está alinhada ao tema do cubo C02 — Participação e Representatividade,
com apoio dos recortes de pesquisa e tempo. A comparação utiliza
**participação observada**, preservando a distinção em relação à medida de
participação de mercado sujeita à homologação da fonte oficial.

## Implementação técnica — Benchmark Externo — V2

No modelo semântico do report, o tema do cubo C02 é representado pela tabela
`D02_Participacao`. O relatório também utiliza as tabelas calculadas
`BE_Empresa`, `BE_Pesquisa` e `BE_Faixa` para representar a empresa escolhida,
o catálogo de pesquisas e as faixas do benchmark.

| Visual | Medida ou campos utilizados | Dimensões/cortes |
| :--- | :--- | :--- |
| Pesquisas com participação | `BE Pesquisas da empresa` (rótulo do cartão: "Pesquisas com participação") | `BE_Empresa[Empresa]`, `BE_Pesquisa[Pesquisa]`, `BE_Pesquisa[Ano]` |
| Empresas no recorte | `BE Empresas observadas` | `BE_Pesquisa[Pesquisa]`, `BE_Pesquisa[Ano]`, `BE_Pesquisa[Área]`, `BE_Pesquisa[Tipo]` |
| Pesquisas no recorte | `BE Pesquisas no recorte` | `BE_Pesquisa[Pesquisa]`, `BE_Pesquisa[Ano]`, `BE_Pesquisa[Área]`, `BE_Pesquisa[Tipo]` |
| Perfil de participação | `BE % empresa por área` e `BE % demais por área` | `BE_Pesquisa[Área]`, `BE_Empresa[Empresa]` |
| Evolução da participação | `BE Pesquisas por ano` e `BE Média demais por ano` | `BE_Pesquisa[Ano]`, `BE_Empresa[Empresa]` |
| Posição no benchmark | `BE Empresas por faixa` e `BE Selecionada por faixa` | `BE_Faixa[Faixa]`, `BE_Empresa[Empresa]` |
| Participação por pesquisa | `BE Percentual observado`, `BE % observado Top 8` e `BE Empresa participou` | `BE_Pesquisa[Pesquisa]`, `BE_Empresa[Empresa]` |

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
| `BE % demais por área` | Forma uma coorte fixa de demais empresas observadas em todas as áreas selecionadas; calcula o percentual por empresa e inclui zero quando ela não participa da área do eixo. Sem coorte, retorna vazio. |
| `BE Empresas por faixa` | Conta empresas dentro dos limites `Minimo` e `Maximo` da faixa selecionada, excluindo a empresa analisada. |
| `BE Selecionada por faixa` | Marca a faixa que contém a quantidade de pesquisas da empresa selecionada. |
| `BE Empresa participou` | Retorna `Sim` ou `Não` conforme exista registro da empresa na pesquisa; sem seleção única, solicita a seleção de uma empresa. |
| `BE % observado Top 8` | Usa `RANKX` para limitar a exibição às oito pesquisas mais relevantes sem alterar a medida base. |

A regressão do Perfil de participação e os limites da conferência DAX estão
em [conferencia-benchmark-perfil.md](conferencia-benchmark-perfil.md).

As medidas do Benchmark usam `HASONEVALUE` para evitar interpretações sem uma
empresa selecionada, `REMOVEFILTERS` para construir o grupo comparável,
`KEEPFILTERS` para preservar os filtros ativos e `ALLSELECTED` para manter o
recorte escolhido pelo usuário ao calcular denominadores e percentuais.

As medidas representam participação observada no conjunto disponível. Elas não
calculam adesão, desempenho ou participação de mercado oficial. O campo
`pct_mercado_na_participacao` permanece fora dos indicadores oficiais até que
a fonte autoritativa seja homologada.

## Consumo dos cubos publicados

O projeto também contém o
[`CentralPesquisasBI.SemanticModel`](../powerbi/CentralPesquisasBI.SemanticModel/),
preparado para importar a geração Parquet produzida pela ETL. A publicação
reúne quatro recortes analíticos — C01 (ciclo), C02 (participação), C03
(pipeline mensal) e C04 (instrumento) — e três tabelas de qualidade. O
[manifesto da geração](acesso-cubos-bi.md) identifica os arquivos e suas contagens
para a conferência de cada geração.

Nesse modelo, as dimensões de área, tipo de pesquisa e status oferecem cortes
compartilhados aos cubos correspondentes. A dimensão de tempo organiza o mês
de resposta de C02 e o fechamento mensal de C03. Os relacionamentos
[`DIM_* → PUB_*`](../powerbi/CentralPesquisasBI.SemanticModel/definition/relationships.tmdl)
usam filtro da dimensão para o fato. A média de duração de C01 utiliza a soma
dos dias dividida pela quantidade de durações disponíveis, preservando a
ponderação quando o usuário combina grupos. O estoque de C03 representa o
fechamento do período selecionado.

As páginas de Produção e Benchmark usam o grão por pesquisa e empresa da
camada de demonstração. O modelo Parquet publica agregados por categoria; essa
publicação não permite comparação por empresa nem detalhe por pesquisa.
RP-13/RP-14 exigem redesenho desses visuais ou ampliação autorizada do contrato
de acesso. Trocar a fonte sem rever o grão não atende esses casos.

## Hierarquias, drill-down e drill-through

| Recurso | Onde está implementado | Estado |
| :--- | :--- | :--- |
| Hierarquia temporal Ano → Trimestre → Mês | `DIM_TEMPO.Calendario` no [modelo de consumo](../powerbi/CentralPesquisasBI.SemanticModel/definition/tables/DIM_TEMPO.tmdl), ligada a C02 (mês de resposta) e C03 (fechamento mensal) | Implementado no modelo semântico |
| Hierarquia Área → Tipo → Perfil | `PUB_C03_PIPELINE_MENSAL.'Area, Tipo e Perfil'` no [modelo de consumo](../powerbi/CentralPesquisasBI.SemanticModel/definition/tables/PUB_C03_PIPELINE_MENSAL.tmdl) | Implementado no modelo semântico |
| Filtro cruzado entre visuais | Gráficos "Pesquisas por status" e "Volume por área" filtram os demais visuais de Produção e Volume (cross-highlight) | Implementado nas páginas |
| Do agregado ao detalhe | Selecionar status ou área filtra a tabela "Acompanhamento das pesquisas", que mostra a pesquisa individual; em Benchmark, a tabela "Participação por pesquisa" detalha o recorte dos cartões | Implementado nas páginas |
| Drill-down por nível hierárquico e drill-through para página de detalhe | Dependem das hierarquias acima, disponíveis no modelo de consumo | Não implementado nas páginas de demonstração; previsto para a Sprint 5 |

As duas páginas usam colunas planas das tabelas de demonstração
(`D01_CicloPesquisa`, `D02_Participacao`, `BE_*`). Por isso, o detalhamento é
feito por filtro cruzado e tabela de detalhe, e não por drill hierárquico.
A navegação por nível (Ano → Trimestre → Mês, Área → Tipo → Perfil) e o
drill-through nas páginas ainda exigem implementação e validação em RP-13/RP-14.
Detalhe por pesquisa não cabe no grão atual da geração Parquet (ver [Integração com a camada Gold](#integração-com-a-camada-gold)).
As tarefas T-DET de [`tarefas-detalhamento.md`](usabilidade/tarefas-detalhamento.md)
usam filtro cruzado e detalhe nas duas páginas atuais; as que exigem
Resultados/Qualidade ficam fora desta rodada. Para medidas não aditivas, a coerência
entre níveis é verificada pelos componentes da medida (numerador e
denominador). Estoque mensal não é somado entre meses.


## Plano de tarefas de usabilidade

O [roteiro de execução](usabilidade/roteiro-execucao.md) organiza 15 tarefas
para quatro perfis de uso, sendo 12 na rodada das duas páginas e três fora
da rodada por dependerem de Resultados/Qualidade. As atividades reproduzem consultas típicas da
Central e associam cada interação a um resultado observável.

| Grupo de tarefas | Interação proposta | Evidência registrada |
| :--- | :--- | :--- |
| [Navegação e filtros](usabilidade/tarefas-navegacao-filtros.md) | Localizar o painel, selecionar ano, área, tipo e status e combinar segmentações. | Contexto selecionado, mudança dos visuais e leitura do resultado. |
| [Detalhamento](usabilidade/tarefas-detalhamento.md) | Partir do total por status ou do benchmark e justificar o detalhe no mesmo recorte. | Caminho percorrido e explicação do número apresentado. |
| [Comparação e segmentação](usabilidade/tarefas-comparacao-segmentacao.md) | Comparar períodos e aplicar recortes simultâneos. | Valores do mesmo recorte, interpretação da medida e resposta dos painéis. |

O plano prevê registro de conclusão, tempo, desvios, erros de interpretação e
observações do participante. Cada sessão identifica a versão das páginas e
os filtros utilizados, permitindo reproduzir a leitura feita pelo usuário.

## Execução e validação

Em 25/09/2026, o grupo apresentou as páginas de Produção e Benchmark ao
parceiro com dados de demonstração. O
[registro da Rodada 0](usabilidade/execucao-navegacao-detalhamento.md)
destaca a boa recepção das tabelas expansíveis e da leitura por tipo de
pesquisa. O parceiro também sugeriu priorizar o tempo médio de duração e
expressar o ciclo em dias úteis; essas sugestões orientam a evolução das
medidas e da hierarquia visual.

As fichas das sessões S1–S4 estão preparadas em
[`execucao-navegacao-detalhamento.md`](usabilidade/execucao-navegacao-detalhamento.md)
e
[`execucao-comparacao-segmentacao.md`](usabilidade/execucao-comparacao-segmentacao.md).
Elas organizam a conferência dos valores exibidos com a fonte de referência,
a resposta dos filtros, a leitura entre níveis de detalhe e o tempo de
resposta. Para médias e percentuais, a conferência usa seus componentes no
mesmo recorte; para C03, compara o fechamento selecionado. Os resultados
serão consolidados nessas fichas após cada sessão.

## Qualidade técnica e funcional

A solução reúne identidade visual consistente, filtros agrupados, cartões de
síntese, gráficos de distribuição e tabelas de acompanhamento. Os dois temas
analíticos atendem a perguntas distintas: Produção e Volume acompanha o ciclo
das pesquisas; Benchmark Externo compara a participação observada da empresa
selecionada com o conjunto disponível.

A qualidade técnica é acompanhada pelo vínculo entre cada visual, sua medida
DAX e o recorte aplicado. A qualidade funcional é acompanhada pelas tarefas
de navegação, detalhamento e comparação, com conferência de valores e registro
das observações em [`docs/usabilidade/`](usabilidade/). As evoluções
identificadas nas sessões são tratadas em
[`limitacoes-e-propostas.md`](usabilidade/limitacoes-e-propostas.md).

## Limitações e propostas

| Limitação | Análise crítica | Proposta |
| :--- | :--- | :--- |
| Páginas sobre CSV de demonstração, não sobre a geração Parquet | Os valores validam a composição e a leitura das páginas, mas não a precisão contra os cubos publicados | RP-13/RP-14: redesenhar visuais para os agregados publicados ou homologar publicação com grão e acesso suficientes; conferir as medidas com o manifesto |
| Sem drill hierárquico nas páginas | O usuário chega ao detalhe por filtro cruzado, mas não desce um nível temporal ou de área | Sprint 5: trocar os eixos pelas hierarquias `Calendario` e `Area, Tipo e Perfil` ; detalhe por pesquisa depende de ampliação autorizada do grão, ausente no Parquet |
| Ciclo apresentado em dias corridos | O parceiro pediu dias úteis na Rodada 0, e as duas métricas não são equivalentes | Incluir o calendário de dias úteis no C01 e rotular a unidade em cada visual |
| Sessões moderadas S1–S4 ainda não executadas | Só a Rodada 0 (retorno do parceiro) tem resultados; ainda não há medidas de tempo nem de taxa de sucesso | Sprint 5: executar S1–S4 com as fichas preparadas depois da ligação ao Parquet |
| Participação de mercado sem fonte homologada | Publicá-la como indicador seria incorreto | Manter como "participação observada" até a homologação (DR02) |

O detalhamento das limitações L01–L08 e das encontradas nas sessões está em
[`limitacoes-e-propostas.md`](usabilidade/limitacoes-e-propostas.md).

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

## Integração com a camada Gold

O layout e a organização das páginas foram apresentados com uma camada de
dados de demonstração em CSV, adequada à validação da composição, dos filtros
e da leitura dos indicadores. O repositório também disponibiliza o modelo
semântico de consumo dos cubos publicados em Parquet, descrito em
[`acesso-cubos-bi.md`](acesso-cubos-bi.md). A integração das páginas a uma
geração publicada é a etapa seguinte do report analítico.

## Referência de estrutura

A seleção das páginas, filtros, visuais e indicadores está detalhada em
[`estrutura-dashboards.md`](solucao-dashboards/estrutura-dashboards.md), que consolida a relação
entre os relatórios do parceiro, os cubos analíticos e a finalidade de cada
tela.
