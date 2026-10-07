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

| Filtro | Uso |
| :--- | :--- |
| Ano | Filtra `D01_CicloPesquisa[ano_edicao]`; não representa ano de solicitação. |
| Área | Restringe o portfólio à área selecionada. |
| Tipo | Restringe o portfólio ao tipo de pesquisa selecionado. |
| Status | Permite analisar as pesquisas por situação no ciclo. |
| Complexidade | Permite comparar o portfólio por nível de complexidade. |

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

A tela está alinhada ao tema do cubo C01 — Portfólio e Ciclo. Os principais
recortes são status, área, tipo, complexidade e ano da edição. Nesta página, o filtro temporal é `ano_edicao`, não `data_solicitacao`.
O ano do Benchmark deriva de `data_divulgacao`; os dois marcos não são
equivalentes e não devem ser comparados como solicitações.

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

## 3. Plano de tarefas para testes de usabilidade

O plano está em [`docs/usabilidade/`](usabilidade/): perfis e critérios
([`perfis-e-criterios.md`](usabilidade/perfis-e-criterios.md)), tarefas
([navegação e filtros](usabilidade/tarefas-navegacao-filtros.md),
[detalhamento](usabilidade/tarefas-detalhamento.md),
[comparação e segmentação](usabilidade/tarefas-comparacao-segmentacao.md)),
[roteiro](usabilidade/roteiro-execucao.md) e
[preparação das sessões](usabilidade/preparacao-sessoes.md). Cada tarefa
parte de uma situação real da Central, sem dica de caminho, e declara a
página, o grão disponível, o estado esperado (valor, `sem dado` ou aviso), o
critério de sucesso observável e o tempo aceitável.

<div align="center">
<sub>Tabela 8 - Tarefas, funcionalidade exercitada e sessão</sub><br>

| Tarefa | Funcionalidade exercitada | Página | Critério de sucesso (resumo) | Sessão |
| :--- | :--- | :--- | :--- | :--- |
| T-NAV-01 | Leitura do estado geral | Produção e Volume | Total e status predominante com os valores exibidos | S1, S3 |
| T-NAV-02 | Navegação entre painéis | as três | Nomeia cada página; lê estoque vazio como `sem dado` | S1 |
| T-FIL-01 | Filtro + ausência de período | Produção e Volume | Contagem da área e reconhecimento de que C01 não tem período | S1 |
| T-FIL-02 | Filtros combinados | Produção e Volume | Inclui todos os status não finalizados | S2 |
| T-FIL-03 | Limpar filtros | Produção e Volume | Volta ao total inicial e confere antes/depois | S2 |
| T-FIL-04 | Recorte vazio | Produção e Volume | Distingue vazio de erro | S1 |
| T-DET-01 | Drill-down total → status → tipo | Produção e Volume | Cita subconjuntos do total | S1 |
| T-DET-02 | Agregado → distribuição por área | Participação agregada | Usa "participações observadas" e reconhece que empresa não é publicada | S2 |
| T-DET-03 | Detalhamento entre páginas | Produção → Estoque, Instrumento e Qualidade | Verifica se o filtro sobreviveu à navegação | S2 |
| T-DET-04 | Indicador de qualidade → regra | Estoque, Instrumento e Qualidade | Registros afetados, denominador e natureza do nulo | S2 |
| T-DET-05 | Drill-through até a pesquisa | Produção e Volume | Reconhece que a linha é um grupo e que o detalhe não é publicado | S1 |
| T-CMP-01 | Métrica comparativa entre anos | Participação agregada | Compara com o marco nomeado ou declara `sem dado` | S3 |
| T-CMP-02 | Evolução mensal | Participação agregada | Aponta o pico e nomeia o marco temporal | S3 |
| T-SEG-01 | Dois filtros simultâneos | Produção e Volume | Enuncia o recorte completo | S3 |
| T-SEG-02 | Três filtros cruzando painéis | Produção → Estoque, Instrumento e Qualidade | Identifica filtros perdidos e inaplicáveis | S4 |
| T-SEG-03 | Segmentação que zera | Produção e Volume | Identifica o filtro que zerou o recorte | S4 |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

Cobertura das funcionalidades pedidas: filtros hierárquicos por período,
área, tipo e status (T-FIL-*, T-SEG-*); drill-down e drill-through
(T-DET-01, T-DET-05); métricas comparativas ao longo do tempo (T-CMP-*);
segmentações simultâneas e cruzamento entre painéis (T-SEG-*, T-DET-03).
Os valores esperados de cada recorte foram calculados por consulta
independente aos Parquet
([`consultas-referencia.sql`](usabilidade/evidencias/consultas-referencia.sql),
[`valores-referencia-v3.md`](usabilidade/evidencias/valores-referencia-v3.md)).

## 4. Execução e validação das tarefas

### 4.1 Rodadas executadas

| Rodada | Data | Alvo | Registro |
| :--- | :--- | :--- | :--- |
| Rodada 0 — parceiro | 25/09/2026 | Páginas de demonstração da Sprint 4 | Retorno verbal do parceiro ([navegação](usabilidade/execucao-navegacao-detalhamento.md#rodada-0--validação-com-o-parceiro-sprint-review), [comparação](usabilidade/execucao-comparacao-segmentacao.md#rodada-0--validação-com-o-parceiro-sprint-review)) |
| S1–S2 | 06/10/2026 | Páginas finais do RP-17 sobre a geração v3 | [Execução de navegação, filtros e detalhamento](usabilidade/execucao-navegacao-detalhamento.md) |
| S3–S4 | 06/10/2026 | Páginas finais do RP-17 sobre a geração v3 | [Execução de comparação e segmentação](usabilidade/execucao-comparacao-segmentacao.md) |

As sessões S1–S4 foram moderadas e simuladas, com participantes internos
exercendo os perfis UC01, UC02 (com o papel de governança) e UC03, conforme
o roteiro. A versão do relatório (tip RP-17 `94e91ef`) e a geração foram
fixadas antes da primeira sessão.

### 4.2 Precisão dos dados apresentados

Todo número lido pelo participante foi comparado com o valor do mesmo
recorte calculado direto sobre os Parquet: **17 de 17 valores conferem**.
As seis discrepâncias anotadas nas fichas são de leitura (recorte, rótulo
ou estado interpretados de forma errada), não de dado.

### 4.3 Coerência entre níveis de granularidade

Nove verificações, todas coerentes
([tabela de coerência](usabilidade/execucao-comparacao-segmentacao.md#coerência-entre-granularidades)):
as contagens por status e por área somam o total (366); as participações
por área somam 17.740; as associações por tipo de pergunta somam 3.186 e
recompõem a área. As médias de ciclo (28,6 dias) e de coleta (13,9 dias) e a
completude (71,4%) recompõem pelo numerador e pelo denominador, e não pela
média das médias (que daria 23,8, 14,2 e 84,0). O estoque não é somado
entre meses.

### 4.4 Resposta aos filtros e desempenho

As sete interações medidas (slicers, seleção cruzada e troca de página)
responderam entre 0,3 s e 1,1 s; nenhuma passou de 2 s. O volume publicado é
pequeno, e não houve erro de consulta nem lentidão. Os filtros responderam
como modelado (§2.3–2.4); os problemas observados foram de **escopo não
comunicado**: filtro que não acompanha a troca de página e filtros da
terceira página que valem só para o estoque.

### 4.5 Resultado de usabilidade

| Indicador | Resultado |
| :--- | :--- |
| Execuções de tarefa | 17 (16 tarefas; T-NAV-01 por dois perfis) |
| Concluídas sem ajuda (taxa de sucesso) | 10 (59%) |
| Concluídas com assistência | 5 (29%) |
| Não concluídas | 2 (12%) — T-DET-03 e T-CMP-02 |
| Acima do tempo aceitável | 7 (41%); tempo médio 03:07 contra 03:11 aceitável |
| Justificativas corretas no detalhamento | 2 de 5 |
| Recorte enunciado corretamente (comparação e segmentação) | 3 de 6 |

Por bloco, a taxa de sucesso foi de 67% em navegação, 75% em filtros, 60%
em detalhamento e 40% em comparação e segmentação
([consolidação](usabilidade/limitacoes-e-propostas.md#2-resultados-das-sessões-s1s4)).
O padrão é claro: **o relatório calcula certo e responde rápido; a perda está
na comunicação do recorte e dos estados sem dado**. A comparação temporal
foi o único ponto em que o dado em si impediu a tarefa (mês de resposta
vazio na v3).

## 5. Avaliação da qualidade técnica e funcional

Avaliação dos critérios do enunciado com a evidência que a sustenta.
**Atende** = sem achado de severidade 3 ou 4 no critério; **atende
parcialmente** = o critério funciona, mas há achado grave ou impeditivo
registrado.

<div align="center">
<sub>Tabela 9 - Critérios de qualidade, evidência e avaliação</sub><br>

| Critério | Evidência | Avaliação | O que falta |
| :--- | :--- | :--- | :--- |
| Clareza e coerência visual | Identidade única nas três páginas; títulos descritivos com unidade ("dias corridos") e grão ("por área, status e tipo"); avisos textuais para dado não publicado | Atende parcialmente | Estados `sem dado` exibidos em branco (A15, A05, A11); texto "dados simulados" na página C02 (A10); códigos I05/C02 na interface (A22) |
| Organização lógica das visualizações | Ordem filtros → cartões → gráficos → tabelas; uma página por tema analítico | Atende | Cartão "Indicadores sem dado" em posição de destaque na página C02 (A11); total repetido em dois cartões (A03) |
| Consistência entre dados exibidos e métricas dos cubos | 17 de 17 valores conferidos; 9 de 9 verificações de coerência; totais do Desktop iguais ao manifesto (RP-17, BI-05) | Atende | — |
| Fluidez na navegação e na aplicação de filtros | Interações entre 0,3 s e 1,1 s; seleção cruzada nos gráficos; filtros simples entendidos (T-SEG-01, T-SEG-03) | Atende parcialmente | Slicers não sincronizados entre páginas (A12); sem drill-down nos eixos (A06); sem ação de limpar filtros (A04); escopo dos filtros da terceira página não indicado (A14) |
| Aderência ao objetivo analítico | Páginas respondem portfólio, ciclo, participação, instrumento e qualidade no grão publicado, sem prometer indicador sem fonte | Atende parcialmente | Comparação temporal impossível na v3 (A17) e ausência de período em C01 (A18); duração em dias corridos e não úteis (A20) |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

**Aproveitamento dos cubos e do modelo.** Os quatro cubos e as três tabelas
de qualidade têm visual nas páginas; as cinco dimensões conformadas filtram
os fatos em direção única, sem relação fato–fato; todas as médias e taxas
são ponderadas pela base válida e devolvem vazio, e não zero, sem
denominador; indicadores sem fonte aparecem com motivo. Duas capacidades do
modelo ainda não chegam às páginas: as hierarquias `Calendario` e
`Area, Tipo e Perfil` (sem uso nos eixos) e a medida `Estado do Estoque`
(sem visual que a exiba).

## 6. Limitações efetivas e propostas

Limitações confirmadas na rodada final, com análise crítica e proposta. As
23 limitações, com evidência, severidade, destino e critério de reteste,
estão em [`limitacoes-e-propostas.md`](usabilidade/limitacoes-e-propostas.md).

| Limitação | Análise crítica | Proposta (não decidida) | Estado |
| :--- | :--- | :--- | :--- |
| Sem mês de resposta na geração v3 (A17, impeditivo) | `mes_resposta` vazio nas 32 linhas de C02; Ano e o gráfico mensal só têm o valor vazio, e a pergunta "cresceu em relação ao período anterior?" fica sem resposta | Recuperar a data de resposta na origem e na carga de C02; até lá, aviso textual no lugar da barra vazia e slicer Ano oculto | Encaminhado a CB e RP |
| Estoque em branco sem motivo (A15, impeditivo) | C03 sem fechamento é estado legítimo, mas o cartão vazio é lido como erro | Exibir a medida `Estado do Estoque` no cartão e no gráfico mensal | Encaminhado a RP |
| Filtros não acompanham a troca de página (A12) | O usuário lê um total global como se fosse do recorte; causou a única falha de detalhamento | Sincronizar Área, Tipo e Status entre páginas | Encaminhado a RP |
| Drill-down não configurado nos eixos (A06) | As hierarquias existem no modelo, mas os visuais têm um nível só; o usuário contorna por slicer | Usar `tipo` como segundo nível, `Calendario` nos eixos de tempo e matriz com `Area, Tipo e Perfil` | Encaminhado a RP |
| Produção sem período e ciclo em dias corridos (A18, A20) | C01 não publica data; a Central raciocina em dias úteis, pedido já feito na Rodada 0 | Publicar ano/mês de solicitação e a duração em dias úteis (`dias_uteis_para_entrega`, 90,4% preenchido na origem) em C01 | Proposta ao contrato de C01 (CB) |
| Completude sem numerador e natureza do nulo (A13) | Ausência permitida (ex.: data de prorrogação) é lida como falha de qualidade | Mostrar linhas, preenchidas e registros afetados; classificar campos de preenchimento condicional | Encaminhado a RP e BI |
| Participação de mercado e empresa sem fonte homologada | Publicá-las como indicador seria incorreto; o benchmark por empresa da demonstração não é reproduzível no grão publicado | Manter "participação observada" e os avisos até a homologação (DR02) | Mantida por decisão |

## 7. Acessibilidade e identidade visual

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

Nas sessões da rodada final, a leitura com teclado mostrou que três visuais
posicionados fora da área visível da página C02 recebem foco (A21), e os
códigos de catálogo (I05, I07, I16, C02) dificultam a leitura sem
consulta à documentação (A22). Ambos estão no registro de limitações com
proposta.

## 8. Referências

- [`estrutura-dashboards.md`](solucao-dashboards/estrutura-dashboards.md):
  relação entre os relatórios do parceiro, os cubos e a finalidade de cada
  tela.
- [`implementacao-reports.md`](solucao-dashboards/implementacao-reports.md):
  inventário dos 48 visuais de demonstração mapeados ao modelo Parquet (RP-12).
- [`filtros-hierarquias-detalhamento.md`](solucao-dashboards/filtros-hierarquias-detalhamento.md)
  e [`validacao-paginas-finais.md`](solucao-dashboards/validacao-paginas-finais.md):
  filtros suportados e validação técnica das páginas finais (RP-16, RP-17).
- [`acesso-cubos-bi.md`](acesso-cubos-bi.md) e
  [`validacao-acesso-bi.md`](validacao-acesso-bi.md): contrato da geração e
  conexão do Power BI.
- [`checklist-avaliacao.md`](solucao-dashboards/checklist-avaliacao.md):
  conferência deste documento contra os critérios de avaliação.
