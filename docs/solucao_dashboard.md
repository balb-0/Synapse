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

### 2.3 Relacionamentos entre fatos e dimensões

O modelo [`CentralPesquisasBI.SemanticModel`](../powerbi/CentralPesquisasBI.SemanticModel/)
é uma constelação de fatos agregados com dimensões conformadas. Os 12
relacionamentos são todos **muitos para um, da dimensão para o fato, com
filtro em direção única** ([`relationships.tmdl`](../powerbi/CentralPesquisasBI.SemanticModel/definition/relationships.tmdl);
decisões em [relacionamentos do modelo BI](relacionamentos-modelo-bi.md)):

<div align="center">
<sub>Tabela 5 - Dimensões conformadas e fatos que elas filtram</sub><br>

| Dimensão | C01 | C02 | C03 | C04 | Qualidade |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `DIM_AREA` | ✓ | ✓ | ✓ | ✓ | — |
| `DIM_TIPO_PESQUISA` | ✓ | ✓ | ✓ | — | — |
| `DIM_STATUS_PESQUISA` | ✓ | — | ✓ | — | — |
| `DIM_TEMPO` | — | ✓ (`mes_resposta`) | ✓ (`data_fim_mes`) | — | — |
| `DIM_TIPO_PERGUNTA` | — | — | — | ✓ | — |

<sup>Material produzido pelos autores (2026), a partir de `relationships.tmdl`</sup>

</div><br>

Decisões que afetam a leitura das páginas:

- **Sem relacionamento fato–fato.** Os cubos têm grãos diferentes; o
  cruzamento entre eles acontece só pela dimensão comum (por exemplo, Área
  filtra C01 e C04 ao mesmo tempo), o que evita duplicar ou mudar o grão.
- **Direção única.** Um filtro aplicado num fato não volta para a dimensão
  nem passa para outro fato; não há caminho ambíguo no modelo.
- **Escopo por desenho.** C04 não tem status nem tempo, e as tabelas de
  qualidade descrevem a fonte inteira; por isso, Status e Mês da terceira
  página filtram só o estoque.
- **`DIM_TEMPO` é calculada** a partir dos meses observados em C02 e C03.
  Quando a geração não tem mês de resposta nem fechamento (caso da v3), a
  dimensão fica só com o valor vazio.

### 2.4 Filtros, segmentações e hierarquias

<div align="center">
<sub>Tabela 6 - Filtros por página</sub><br>

| Página | Slicer | Campo | Alcance |
| :--- | :--- | :--- | :--- |
| Produção e Volume | Área, Tipo, Status | `DIM_AREA.area`, `DIM_TIPO_PESQUISA.tipo`, `DIM_STATUS_PESQUISA.status` | Todos os visuais de C01 |
| Participação agregada (C02) | Ano, Área, Tipo | `DIM_TEMPO.ano`, `DIM_AREA.area`, `DIM_TIPO_PESQUISA.tipo` | Todos os visuais de C02 |
| Estoque, Instrumento e Qualidade | Status, Área, Mês | `DIM_STATUS_PESQUISA.status`, `DIM_AREA.area`, `DIM_TEMPO.ano_mes` | Status e Mês: só C03; Área: C03 e C04; qualidade: escopo global |

<sup>Material produzido pelos autores (2026), a partir da definição PBIR do RP-17 e do [RP-16](solucao-dashboards/filtros-hierarquias-detalhamento.md)</sup>

</div><br>

Além dos slicers, os gráficos de barras de status e de área filtram os
demais visuais da página por seleção cruzada (`drillFilterOtherVisuals`). Os
slicers **não são sincronizados entre páginas**: cada página guarda a sua
própria seleção.

Ano de edição e complexidade (C01), empresa e pesquisa individual (C02) não
são publicados. Onde a página de demonstração tinha esses slicers, há agora
um aviso textual, que não filtra.

**Hierarquias.** O modelo define duas hierarquias:

| Hierarquia | Níveis | Tabela |
| :--- | :--- | :--- |
| `Calendario` | Ano → Trimestre → Mês | `DIM_TEMPO` |
| `Area, Tipo e Perfil` | Área → Tipo → Perfil | `PUB_C03_PIPELINE_MENSAL` |

**Drill-down e drill-through — estado real.** Nos visuais publicados, os
eixos usam um único campo (`area`, `status`, `tipo`, `mes_resposta`,
`data_fim_mes`) e a tabela de estoque é plana. Por isso, nenhum visual
oferece hoje o comando de descer um nível: o usuário chega ao detalhe por
seleção cruzada ou por slicer. Não existe página de drill-through, por
decisão: a publicação não contém pesquisa, empresa nem pessoa, e o teste
`test_no_drillthrough_to_individual_keys` do RP-17 reprova qualquer
configuração que prometa essas chaves. O uso das hierarquias nos eixos é a
proposta A06 (§6).

### 2.5 Medidas DAX personalizadas

As colunas dos Parquet são somas e contagens por grupo; nenhuma média, taxa
ou estado vem pronta da publicação. Todas as medidas do relatório são DAX
personalizadas, escritas para respeitar o grão agregado (regras em
[regras estatísticas das medidas](regras-estatisticas-medidas.md) e
[especificação das medidas](especificacao-medidas-bi.md)):

<div align="center">
<sub>Tabela 7 - Medidas personalizadas e ligação com o modelo</sub><br>

| Família | Medidas | Regra DAX | Por que assim |
| :--- | :--- | :--- | :--- |
| Contagens aditivas | `Qtd Pesquisas`, `Qtd Participacoes`, `Qtd Perguntas` | `SUM` da contagem do grupo | Grupos disjuntos: a soma no recorte é exata e recompõe o total entre níveis |
| Médias ponderadas de duração | `Media Dias Validacao`, `Media Dias Coleta`, `Media Dias Tabulacao`, `Media Dias Ciclo Total`, `Media Minutos Preenchimento` | `DIVIDE(SUM(soma_*), SUM(qtd_*_disponivel))` | Média ponderada pela base válida; denominador zero devolve vazio, nunca zero. A média das médias por grupo daria outro número (23,8 em vez de 28,6 no ciclo total da v3) |
| Bases válidas | `Base Valida *` | `SUM(qtd_*_disponivel)` | Expõem o denominador de cada média e de cada taxa |
| Taxas de qualidade | `Completude`, `Integridade Referencial`, `Taxa de Duplicidade` | `DIVIDE` de preenchidas ÷ linhas; correspondentes ÷ informadas; (linhas − distintas) ÷ linhas | Mesmas razões do contrato da publicação, ponderadas pelo volume de cada tabela |
| Estoque semiaditivo | `Data de Referência do Estoque`, `Estoque no Último Mês Observado`, `Estoque no Status`, `Estado do Estoque` | Busca o último `data_fim_mes` observado no contexto e soma o estoque só nesse mês; o estado devolve texto quando não há fechamento | O estoque não pode ser somado entre meses; o mês sem linha fica `sem dado` |
| Entradas e saídas | `Entradas no Mês`, `Saídas no Mês` e os estados correspondentes | `SUM` com estado textual | As colunas existem no contrato, mas ficam vazias sem histórico de transições |
| Indicadores sem dado | `Taxa de Prorrogacao`, `Representatividade`, `Qtd Indicadores Sem Dado` | Medidas-texto com o motivo; contagem do catálogo `DIM_INDICADORES_BLOQUEADOS` | Indicador sem fonte aparece com motivo, nunca como zero ([sinalização](sinalizacao-indicadores-bloqueados.md)) |

<sup>Material produzido pelos autores (2026), a partir das tabelas TMDL do modelo integrado</sup>

</div><br>

As medidas ficam nas tabelas de fato e são avaliadas no contexto criado
pelas dimensões conformadas: um slicer de `DIM_AREA` restringe as linhas de
cada fato relacionado antes da agregação, e a medida recalcula numerador e
denominador nesse recorte. É isso que mantém médias e taxas coerentes ao
navegar entre níveis (§4.3).

### 2.6 Adaptações em relação às páginas de demonstração

As páginas da Sprint 4 usavam tabelas de demonstração em CSV no grão de
pesquisa e empresa (`D01_CicloPesquisa`, `D02_Participacao`, `BE_*`). A
publicação oficial é agregada, e as páginas foram migradas para ela (BI-01,
RP-13 a RP-16):

| Elemento da demonstração | Situação final | Justificativa |
| :--- | :--- | :--- |
| Taxa de finalização, pesquisas finalizadas e em aberto em cartões | Contagem por status no gráfico; cartão com total, médias e base válida | O antigo cartão repetia o mesmo valor com três rótulos; a distribuição por status é exata no grão publicado |
| Tabela de pesquisas com título e data de entrega | Tabela agregada por área, status e tipo | Título, data e identificador não são publicados |
| Prorrogação (cartão e tabela) | Aviso I05 sem dado | `flag_prorrogada` não está em C01 |
| Slicers de ano de edição e complexidade | Avisos textuais | Campos ausentes em C01 (complexidade só existe em C03) |
| Benchmark por empresa (empresa selecionada × demais, faixas) | Participação por área, tipo e mês; avisos de empresa e pesquisa | Empresa e pesquisa não são publicadas (I07); comparar empresas exigiria grão individual |
| Média de preenchimento no lugar de um terceiro cartão de contagem | `Media Minutos Preenchimento` | Evitar dois cartões com o mesmo valor |
| — | Página Estoque, Instrumento e Qualidade | C03, C04 e qualidade não tinham página na demonstração |

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

## Referência de estrutura

A seleção das páginas, filtros, visuais e indicadores está detalhada em
[`estrutura-dashboards.md`](solucao-dashboards/estrutura-dashboards.md), que consolida a relação
entre os relatórios do parceiro, os cubos analíticos e a finalidade de cada
tela.
