# Dashboard da Central de Pesquisas

Documento da solução de dashboards da Sprint 5: como os reports foram
implementados sobre os cubos publicados pela ETL, como foram testados com
usuários e qual é a avaliação técnica e funcional resultante. As seções
seguem os itens do enunciado "Dashboards — versão 2": implementação com
base nos cubos (§2), plano de tarefas (§3), execução e validação (§4) e
avaliação de qualidade (§5).

## 1. Visão geral

### 1.1 Caminho do dado até a página

```text
fontes do parceiro → ETL (Prefect) → DuckDB (ingestão e cubos C01–C04)
  → reconciliação → publicação Parquet (7 arquivos + manifest.json)
  → Power BI (CentralPesquisasBI.pbip, parâmetro PastaPublicacaoBI)
```

O relatório não lê o DuckDB nem as fontes: consome somente a geração
Parquet indicada por `current.json`, com quatro recortes agregados dos cubos
e três tabelas de qualidade ([contrato da geração](acesso-cubos-bi.md)). A
versão avaliada nesta sprint usa a geração v3
`6b1eaa686aac43b18b6d6545e1c2c5f1`, publicada a partir da carga reconciliada
`afcde424-45e8-457b-8793-bf0866d142b2`.

### 1.2 Páginas

O relatório [`CentralPesquisasBI.Report`](../powerbi/CentralPesquisasBI.Report/)
tem três páginas e 69 visuais (22 + 26 + 21), validados no RP-17
([validação das páginas finais](solucao-dashboards/validacao-paginas-finais.md)):

| Página | Pergunta que responde | Perfis | Captura |
| :--- | :--- | :--- | :--- |
| Produção e Volume | Quantas pesquisas existem, em que status, de que área e tipo, e quanto dura cada etapa do ciclo? | UC01, UC03 | [C01](evidencias/bi06/final-fixture-c01.png) |
| Participação agregada (C02) | Como as participações observadas se distribuem por área, tipo e mês de resposta? | UC01, UC03 | [C02](evidencias/bi06/final-fixture-c02.png) |
| Estoque, Instrumento e Qualidade | Qual o estoque no último fechamento mensal, como os questionários se compõem por tipo de pergunta e qual a qualidade das fontes? | UC01, UC02, governança | [C03/C04](evidencias/bi06/final-fixture-c03-c04.png) |

As capturas por página foram feitas com a fixture sintética; a
[captura-resumo da geração v3](evidencias/bi06/final-v3-summary.png) é a única
com dado real. As três páginas compartilham a identidade visual definida na
Sprint 4: faixa lateral com marca e filtros, título e subtítulo descritivos,
cartões de síntese no topo e gráficos e tabelas abaixo.

## 2. Implementação dos reports com base nos cubos

### 2.1 Cubos utilizados

<div align="center">
<sub>Tabela 1 - Cubos e tabelas publicadas, grão e uso nas páginas</sub><br>

| Cubo / tabela publicada | Tema de negócio | Grão de uma linha | Linhas na v3 | Página |
| :--- | :--- | :--- | ---: | :--- |
| C01 — `PUB_C01_CICLO` | Portfólio e ciclo das pesquisas | área × status × tipo | 57 | Produção e Volume |
| C02 — `PUB_C02_PARTICIPACAO` | Participação observada | área × tipo × mês de resposta | 32 | Participação agregada (C02) |
| C03 — `PUB_C03_PIPELINE_MENSAL` | Estoque mensal do pipeline | fechamento do mês × status × área × tipo × perfil × tipo de resposta | 0 | Estoque, Instrumento e Qualidade |
| C04 — `PUB_C04_INSTRUMENTO` | Composição dos questionários | área × tipo de pergunta | 45 | Estoque, Instrumento e Qualidade |
| `PUB_QUALIDADE_CAMPO` | Completude | tabela × campo da fonte tratada | 64 | Estoque, Instrumento e Qualidade |
| `PUB_QUALIDADE_RELACAO` | Integridade referencial | relação (tabela filha e chave) | 8 | Estoque, Instrumento e Qualidade |
| `PUB_QUALIDADE_DUPLICIDADE` | Duplicidade de chave | tabela da ingestão | 5 | Estoque, Instrumento e Qualidade |

<sup>Material produzido pelos autores (2026), a partir do manifesto da geração v3</sup>

</div><br>

Totais conferidos no Power BI Desktop contra o manifesto e contra consultas
diretas aos Parquet: 366 pesquisas (C01), 17.740 participações (C02) e 3.186
associações pesquisa-pergunta (C04). C03 não tem fechamento observado na
v3, e o estoque é tratado como `sem dado`, nunca como zero.

### 2.2 Medidas e dimensões por visual

Visuais analíticos de cada página, com a tabela do modelo, as medidas e os
campos de dimensão vinculados na definição PBIR. Os demais visuais são de
layout (fundo, faixa lateral, marca, título) ou avisos textuais de dado não
publicado.

<div align="center">
<sub>Tabela 2 - Produção e Volume (22 visuais: 6 analíticos, 3 slicers, 4 avisos, 9 de layout)</sub><br>

| Visual | Tipo | Tabela | Medidas | Dimensões |
| :--- | :--- | :--- | :--- | :--- |
| Pesquisas no recorte | cartão | `PUB_C01_CICLO` | `Qtd Pesquisas` | contexto dos slicers |
| Indicadores principais | cartão múltiplo | `PUB_C01_CICLO` | `Qtd Pesquisas`, `Media Dias Ciclo Total`, `Base Valida Ciclo Total`, `Media Dias Coleta` | contexto dos slicers |
| Tempo por Etapa e Tipo (dias corridos) | colunas agrupadas | `PUB_C01_CICLO` | `Media Dias Validacao`, `Media Dias Coleta`, `Media Dias Tabulacao` | `tipo` |
| Pesquisas por Status | barras | `PUB_C01_CICLO` | `Qtd Pesquisas` | `status` |
| Volume por Área | barras | `PUB_C01_CICLO` | `Qtd Pesquisas` | `area` |
| Acompanhamento das Pesquisas | tabela | `PUB_C01_CICLO` | `Qtd Pesquisas`, `Media Dias Ciclo Total` | `area`, `status`, `tipo` |
| Slicers Área, Tipo, Status | segmentação | `DIM_AREA`, `DIM_TIPO_PESQUISA`, `DIM_STATUS_PESQUISA` | — | `area`, `tipo`, `status` |
| Avisos de ano de edição, complexidade e prorrogação (I05) | texto | — | — | não filtram |

<sup>Material produzido pelos autores (2026), a partir da definição PBIR do RP-17</sup>

</div><br>

<div align="center">
<sub>Tabela 3 - Participação agregada (C02) (26 visuais: 7 analíticos, 3 fora da área visível, 3 slicers, 5 avisos, 8 de layout)</sub><br>

| Visual | Tipo | Tabela | Medidas | Dimensões |
| :--- | :--- | :--- | :--- | :--- |
| Participações observadas | cartão | `PUB_C02_PARTICIPACAO` | `Qtd Participacoes` | contexto dos slicers |
| Indicadores sem dado | cartão | `DIM_INDICADORES_BLOQUEADOS` | `Qtd Indicadores Sem Dado` | — |
| Média de preenchimento | cartão | `PUB_C02_PARTICIPACAO` | `Media Minutos Preenchimento` | contexto dos slicers |
| Participações por área | barras | `PUB_C02_PARTICIPACAO` | `Qtd Participacoes` | `area` |
| Participações por mês | colunas | `PUB_C02_PARTICIPACAO` | `Qtd Participacoes` | `mes_resposta` |
| Participações agregadas por área, tipo e mês | tabela | `PUB_C02_PARTICIPACAO` | `Qtd Participacoes`, `Media Minutos Preenchimento` | `area`, `tipo`, `mes_resposta` |
| Indicadores sem dado por motivo | colunas | `DIM_INDICADORES_BLOQUEADOS` | `Qtd Indicadores Sem Dado` | `motivo` |
| Slicers Ano, Área, Tipo | segmentação | `DIM_TEMPO`, `DIM_AREA`, `DIM_TIPO_PESQUISA` | — | `ano`, `area`, `tipo` |
| Avisos de empresa (I07), pesquisa individual, grão e privacidade | texto | — | — | não filtram |

<sup>Material produzido pelos autores (2026), a partir da definição PBIR do RP-17</sup>

</div><br>

<div align="center">
<sub>Tabela 4 - Estoque, Instrumento e Qualidade (21 visuais: 9 analíticos, 3 slicers, 9 de layout e texto)</sub><br>

| Visual | Tipo | Tabela | Medidas | Dimensões |
| :--- | :--- | :--- | :--- | :--- |
| Estoque no último fechamento observado | cartão | `PUB_C03_PIPELINE_MENSAL` | `Estoque no Status` | contexto dos slicers |
| Associações pesquisa-pergunta (I14) | cartão | `PUB_C04_INSTRUMENTO` | `Qtd Perguntas` | Área |
| Completude aplicável (I16) | cartão | `PUB_QUALIDADE_CAMPO` | `Completude` | — |
| Estoque no fechamento mensal | colunas | `PUB_C03_PIPELINE_MENSAL` | `Estoque no Status` | `data_fim_mes` |
| Perguntas por tipo | barras | `PUB_C04_INSTRUMENTO` | `Qtd Perguntas` | `tipo_pergunta` |
| Estoque por área, status e tipo | tabela | `PUB_C03_PIPELINE_MENSAL` | `Estoque no Status` | `area`, `status`, `tipo` |
| Completude por tabela e campo | tabela | `PUB_QUALIDADE_CAMPO` | `Completude` | `tabela`, `campo` |
| Integridade por relação | tabela | `PUB_QUALIDADE_RELACAO` | `Integridade Referencial` | `relacao` |
| Duplicidade por fonte | tabela | `PUB_QUALIDADE_DUPLICIDADE` | `Taxa de Duplicidade` | `tabela` |
| Slicers Status, Área, Mês | segmentação | `DIM_STATUS_PESQUISA`, `DIM_AREA`, `DIM_TEMPO` | — | `status`, `area`, `ano_mes` |

<sup>Material produzido pelos autores (2026), a partir da definição PBIR do RP-17</sup>

</div><br>

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
separação preserva a finalidade de cada artefato e orienta a adaptação dos
visuais à geração oficial.

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
**Atendimento parcial delimitado:** a navegação por nível (Ano → Trimestre →
Mês, Área → Tipo → Perfil) e o drill-through serão concluídos na **Sprint 5**, quando as páginas forem
ligadas à geração Parquet (ver [Integração com a camada Gold](#integração-com-a-camada-gold)).
As tarefas T-DET de [`tarefas-detalhamento.md`](usabilidade/tarefas-detalhamento.md)
estão escritas para os dois modos. Para medidas não aditivas, a coerência
entre níveis é verificada pelos componentes da medida (numerador e
denominador). Estoque mensal não é somado entre meses.



O [roteiro de execução](usabilidade/roteiro-execucao.md) organiza 15 tarefas
para quatro perfis de uso. As atividades reproduzem consultas típicas da
Central e associam cada interação a um resultado observável.

| Grupo de tarefas | Interação proposta | Evidência registrada |
| :--- | :--- | :--- |
| [Navegação e filtros](usabilidade/tarefas-navegacao-filtros.md) | Localizar o painel, selecionar ano, área, tipo e status e combinar segmentações. | Contexto selecionado, mudança dos visuais e leitura do resultado. |
| [Detalhamento](usabilidade/tarefas-detalhamento.md) | Partir de um indicador agregado e localizar a pesquisa correspondente na tabela. | Caminho percorrido e explicação do número apresentado. |
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
| Páginas sobre CSV de demonstração, não sobre a geração Parquet | Os valores validam a composição e a leitura das páginas, mas não a precisão contra os cubos publicados | Sprint 5: ligar as páginas ao `CentralPesquisasBI.SemanticModel` e conferir cada visual com o `manifest.json` |
| Sem drill hierárquico nas páginas | O usuário chega ao detalhe por filtro cruzado, mas não desce um nível temporal ou de área | Sprint 5: trocar os eixos pelas hierarquias `Calendario` e `Area, Tipo e Perfil` e criar uma página de drill-through por pesquisa |
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
