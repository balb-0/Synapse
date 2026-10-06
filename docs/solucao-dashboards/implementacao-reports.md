# Documento da solução — implementação dos reports a partir dos cubos

Seção do documento da solução que descreve **como cada visualização dos
reports nasce dos cubos analíticos** C01–C04 (contratos da §5.2 do
[`projeto.md`](../projeto.md)): cubo de origem, medidas, dimensões, filtros,
relacionamentos, hierarquias e medidas personalizadas. Convenção de estado,
mantida em todo o documento: **[contrato]** = definido nos cubos/modelo e
válido para implementação; **[pendente: DX/RP]** = depende da entrega do
modelo semântico (DX) ou da construção das telas (RP) para virar
comportamento verificável. Nada marcado pendente é apresentado como entregue.

> **Atualização de 25/09/2026:** esta seção orienta as quatro telas planejadas.
> As páginas Produção e Volume e Benchmark Externo demonstram a interface
> usando dados de demonstração. O modelo TMDL dos sete Parquet agregados
> define o consumo analítico. A integração entre eles está detalhada em
> [`solucao_dashboard.md`](../solucao_dashboard.md).

## 1. Visualizações por tela e cubo de origem

<div align="center">
<sub>Tabela 1 - Tela, visual, cubo de origem, medidas e dimensões</sub><br>

| Tela | Visual | Cubo | Medidas | Dimensões de corte |
| :--- | :--- | :--- | :--- | :--- |
| Operação (D01) | Cartões de portfólio (total, por status) | C01 | Contagem de pesquisas (I01) | Status, tipo, área, complexidade |
| Operação (D01) | Evolução temporal de solicitações | C01 | Contagem por período (I02) | Tempo (papel: `data_solicitacao`) |
| Operação (D01) | Marcos e prorrogações | C01 | Contagem de prorrogações (I05); tempos entre marcos (I03–I04) | Papéis de tempo por marco, status |
| Operação (D01) | Fluxo mensal do pipeline | C03 | Estoque por status (semiaditiva); entradas e saídas indisponíveis sem histórico de transições | Tempo, status, área, tipo, perfil |
| Participação (D02) | Total de participações observadas | C02 | Contagem de participações (I07) | Pesquisa, tempo, empresa |
| Participação (D02) | Distribuição por empresa (agregada) | C02 | Contagem por empresa | Empresa (sem identificação nominal na tela) |
| Participação (D02) | Engajamento por cargo/departamento | C02 | Contagens agrupadas | Cargo, departamento — **[pendente: reconciliação DR03]** |
| Resultados (D03) | Distribuição por tipo de questão | C04 | Contagem de associações; número de alternativas é atributo da pergunta | Pesquisa, pergunta, tipo de questão |
| Resultados (D03) | Exemplos fechados do protótipo, para uso interno | Protótipo D03; publicação pendente de autorização | — (amostra rotulada) | Sem IDs de pesquisa/questão (limite LGPD) |
| Qualidade (D04) | Matriz de regras de completude/validade | Perfilamento (§5.3) | Numerador/denominador por regra (I16–I20) | Fonte, campo, regra, natureza do nulo |
| Qualidade (D04) | Integridade e órfãos | Perfilamento (§5.3) | Contagens de órfãos e elos em reconciliação | Relação, fonte |

<sup>Material produzido pelos autores (2026), a partir dos contratos C01–C04 (§5.2) e do mapa D01–D04 (§5.7)</sup>

</div><br>

## 2. Relacionamentos do modelo

Estrutura em estrela conforme os contratos: **[contrato]**

- `DIM_TEMPO` é **conformada nos quatro cubos**; em C01 atua por **papéis**
  (uma relação por marco: solicitação, aprovação, divulgação, prazo,
  prorrogação, entrega), com `data_solicitacao` como papel padrão das telas.
- `DIM_PESQUISA` é conformada em C01, C02 e C04; Status, Área, Tipo e Perfil
  são compartilhadas entre C01 e C03.
- Cardinalidade: dimensão (1) → fato (N) em todas as relações; filtro
  propaga da dimensão para o fato, em direção única. Caminhos ambíguos entre
  fatos não permanecem ativos — cruzamento entre fatos só por dimensão
  conformada. **[pendente: DX-05** materializar cardinalidade e direção no
  modelo da ferramenta de BI**]**
- Não existe relação participação ↔ resposta (C02 ↔ C04): a ponte de
  identidade não foi conciliada (DR03) e o modelo não a presume.

## 3. Filtros e hierarquias

- Filtros compartilhados entre telas: período (papel `data_solicitacao` por
  padrão, outros marcos só rotulados), tipo, área, complexidade, status.
  **[contrato; comportamento entre telas pendente: RP-07]**
- Hierarquia de tempo: ano → trimestre → mês (→ dia onde o grão sustentar),
  sem quebrar o total entre níveis. **[DX-06: `DIM_TEMPO.Calendario` Ano → Trimestre → Mês no modelo de consumo; uso nas páginas previsto para a Sprint 5]**
- Hierarquias de classificação: área → tipo → perfil da pesquisa; e a
  hierarquia de qualidade fonte → campo → regra na D04. **[DX-06: `PUB_C03_PIPELINE_MENSAL.'Area, Tipo e Perfil'` implementada no modelo de consumo; uso nas páginas e hierarquia de qualidade previstos para a Sprint 5]**

## 4. Medidas personalizadas

Medidas que não são coluna direta dos cubos e precisam ser criadas no modelo
semântico, com a regra estatística correspondente (§ regras DX-03):

<div align="center">
<sub>Tabela 2 - Medidas personalizadas, fórmula e tratamento de nulo</sub><br>

| Medida | Fórmula (contrato) | Nulo/indisponível | Estado |
| :--- | :--- | :--- | :--- |
| Participações observadas | contagem de linhas de C02 (sem afirmar pessoa única) | — | [contrato] |
| % participação por empresa | contagem da empresa ÷ total de participações do recorte | denominador zero → indisponível (nunca 0%) | [pendente: DX-08] |
| Tempo de ciclo entre marcos | diferença entre pares de datas nomeados (RF03) | par incompleto → indisponível (nunca zero dias) | [pendente: DX-07] |
| Estoque mensal do pipeline | último valor do período (semiaditiva — **não** soma entre meses) | mês sem snapshot → indisponível | [pendente: DX-07] |
| Completude por campo | válidos ÷ avaliados, por regra, com ausência permitida separada | regra sem avaliação → indisponível | [pendente: DX-09] |
| Indicador bloqueado | rótulo "indisponível" + motivo textual | nunca exibido como zero | [pendente: DX-10] |

<sup>Material produzido pelos autores (2026), conforme contratos dos cubos e regras estatísticas</sup>

</div><br>

## 5. Rastreabilidade e pendências

- Cada visual analítico da Tabela 1 rastreia a um cubo (C01–C04) ou ao
  perfilamento (§5.3). Os exemplos fechados pertencem somente ao protótipo
  interno; sua publicação depende de autorização específica.
- Pendências abertas nesta seção: DX-05/06 (relacionamentos e hierarquias no
  modelo), DX-07/08/09/10 (medidas), RP-07 (filtros entre telas). Quando
  essas entregas ocorrerem, os marcadores **[pendente]** são resolvidos e
  esta seção passa a afirmar comportamento verificado — a conferência final
  é objeto do [checklist de avaliação](checklist-avaliacao.md).

## 6. Anexo Sprint 5 — Inventário PBIP → Parquet (RP-12, issue #317)

Inventário dos **48 visuais** das duas páginas já estruturadas em
`src/pbir dash/dashboard.pbip` (`dashboard.Report/definition/pages/`),
mapeados ao contrato publicado de sete Parquet
(`docs/acesso-cubos-bi.md`, parâmetro `PastaPublicacaoBI`):
`PUB_C01_CICLO` (grão área/status/tipo), `PUB_C02_PARTICIPACAO` (grão
área/tipo/mês), `PUB_C03_PIPELINE_MENSAL` (grão mês/status/área/tipo/perfil),
`PUB_C04_INSTRUMENTO` (grão área/tipo de pergunta) e as três tabelas de
qualidade. Classificação de publicáveis segue
`docs/indicadores-publicaveis-bi.md`: 7 calculáveis na camada BI (I01, I02,
I04 só em média, I14, I16–I18), I03 parcial, demais sem dado (sinalizar com
motivo textual, nunca zero — DX-10). Nenhum visual final promete chave
individual (pesquisa/empresa/pessoa) ausente da publicação.

### 6.1 Página Produção e Volume (`5d499bb7bb62646ad6e5`, 22 visuais)

| Visual | Tipo | Referência atual | Cubo/medida Parquet | Dimensão Parquet | Situação |
| :-- | :-- | :-- | :-- | :-- | :-- |
| `655b60cbe268a86e200c` | cardVisual | `D01_CicloPesquisa.Pesquisas`, `Pesquisas Finalizadas`, `Pesquisas em Aberto`, `Ciclo Médio em Dias Corridos` | `PUB_C01_CICLO.'Qtd Pesquisas'` (I01/I02); `'Media Dias Ciclo Total'` = `soma_dias_ciclo_total / qtd_ciclo_total_disponivel` (I04, só média) | status/área/tipo via filtro; sem dado → indisponível, nunca zero | Adaptável em RP-13; recortes "Finalizadas/Em Aberto" viram filtro de `status`, sem afirmar dia útil |
| `7ca374f79a7cd6921a48` | tableEx | `D01` `titulo`, `area`, `tipo`, `status`, `data_entrega`, `dias_ciclo_total_corridos` | `PUB_C01_CICLO.qtd_pesquisas` agregado | área, status, tipo | `titulo`/`data_entrega`/valor por pesquisa **não publicados** → tabela vira agregado por área/status/tipo (RP-13) |
| `e1943eaed82275129d4e` | clusteredColumnChart | `Ciclo Médio Validação/Coleta/Tabulação` por `tipo` | `PUB_C01_CICLO.'Media Dias Validacao/Coleta/Tabulacao'` (I04) | tipo | Adaptável; denominador `qtd_*_disponivel` explícito |
| `pvarea000000000010` | barChart | `Pesquisas` por `area` | `PUB_C01_CICLO.'Qtd Pesquisas'` (I01/I02) | área | Adaptável direto |
| `pvstatus0000000009` | barChart | `Pesquisas` por `status` | `PUB_C01_CICLO.'Qtd Pesquisas'` (I02) | status | Adaptável direto |
| `pvline000000000012` | cardVisual | `Taxa de Finalização` | Derivada de `Qtd Pesquisas` por status no recorte | status | Adaptável como razão; denominador zero → indisponível |
| `pvprorrocard0000015` | cardVisual | `Pesquisas Prorrogadas` | — (I05) | — | **Sem dado**: `flag_prorrogada` não publicada em `PUB_C01_CICLO` → sinalizar motivo (RP-13) |
| `pvprorrotable000016` | tableEx | `titulo`, `area`, `flag_prorrogada` | — (I05) | área | **Sem dado** pelo mesmo motivo; sem coluna individual → sinalizar/retirar (RP-13) |
| `pvslicerarea0000004` | slicer | `D01.area` | `PUB_C01_CICLO.area` / `DIM_AREA` | área | Adaptável |
| `pvslicertipo0000005` | slicer | `D01.tipo` | `PUB_C01_CICLO.tipo` / `DIM_TIPO_PESQUISA` | tipo | Adaptável |
| `pvslicerstat0000006` | slicer | `D01.status` | `PUB_C01_CICLO.status` / `DIM_STATUS_PESQUISA` | status | Adaptável |
| `pvslicercomp0000007` | slicer | `D01.complexidade` | — em C01 | — | **Sem dado em C01** (`complexidade` só existe em `PUB_C03_PIPELINE_MENSAL`); não filtrar C01 por ele (RP-13/RP-16) |
| `pvslicerano00000003` | slicer | `D01.ano_edicao` | — | — | **Sem dado**: `ano_edicao` sem origem homologada; `DIM_TEMPO.Calendario` só cobre C02/C03 → sinalizar (RP-13/RP-16) |
| `908f2a6c26962900d75c` | image | logo | — | — | Preservar |
| `pvbg…`, `pvhead…`, `pvline…`, `pvtitle…`, `pvsubtl…`, `pvfilter…`, `pvbrand…` (8) | textbox | textos de layout | — | — | Preservar identidade visual; revisar textos que prometam grão individual |

### 6.2 Página Benchmark Externo — V2 (`e18bd740de609936581b`, 26 visuais)

| Visual | Tipo | Referência atual | Cubo/medida Parquet | Dimensão Parquet | Situação |
| :-- | :-- | :-- | :-- | :-- | :-- |
| `v2_kpi1` | cardVisual | `BE_Empresa.'BE Pesquisas da empresa'` | — (I07 sem dado) | — | **Sem dado individual**: `PUB_C02` agrega por área/tipo/mês sem empresa → virar `Qtd Participacoes` do recorte ou sinalizar (RP-14) |
| `v2_kpi2` | cardVisual | `BE_Empresa.'BE Empresas observadas'` | — (I07 sem dado) | — | **Sem dado**: contagem distinta de empresa não sobrevive à agregação → sinalizar (RP-14) |
| `v2_kpi3` | cardVisual | `BE_Empresa.'BE Pesquisas no recorte'` | `PUB_C02_PARTICIPACAO.'Qtd Participacoes'` (ocorrências, não pessoas — I13 não substituir) | área/tipo/mês | Adaptável como ocorrências do recorte |
| `v2_area`, `v2_frequent` | barChart | `BE % empresa/demais por área` | `PUB_C02_PARTICIPACAO.'Qtd Participacoes'` por área (comparação área/tipo/mês, sem empresa) | área | Adaptável sem seleção de empresa (RP-14) |
| `v2_time`, `v2_absent` | clusteredColumnChart | `BE Média demais/pesquisas por ano` | `PUB_C02_PARTICIPACAO.'Qtd Participacoes'` por mês (`mes_resposta` → `DIM_TEMPO.Calendario`) | tempo | Adaptável por mês; ano deriva do mês observado |
| `eebbcb005a12b1c98030` | clusteredColumnChart | `BE Empresas/Selecionada por faixa` | — | — | **Sem dado**: faixa/empresa individual não publicadas → retirar ou sinalizar (RP-14) |
| `v2_detail`, `5a299fc93da0a4eb0d07` | tableEx | `BE Empresa participou`, `% observado`, `Pesquisa` | `PUB_C02_PARTICIPACAO` agregado por área/tipo/mês | área, tipo, mês | Sem `Pesquisa`/empresa nominal → tabela agregada (RP-14) |
| `3307368b9b0eb3020a56` | slicer | `BE_Pesquisa.Ano` | `DIM_TEMPO.ano` (meses de C02) | tempo | Adaptável via mês observado |
| `9eae5b36e00a27061ac9` | slicer | `BE_Pesquisa.Área` | `PUB_C02_PARTICIPACAO.area` | área | Adaptável |
| `93a811b00a01082002b3` | slicer | `BE_Pesquisa.Tipo` | `PUB_C02_PARTICIPACAO.tipo` | tipo | Adaptável |
| `d3ee05e7e9ee90a905a0` | slicer | `BE_Empresa.Empresa` | — | — | **Sem dado**: empresa nominal não publicada → retirar/sinalizar (RP-14/RP-16) |
| `f8529f56a2b696a08788` | slicer | `BE_Pesquisa.Pesquisa` | — | — | **Sem dado**: pesquisa nominal não publicada → retirar/sinalizar (RP-14/RP-16) |
| Textos/imagem (`0011…`, `54dc…`, `7aea…`, `a8cb…`, `ac10…`, `e740…`, `v2_context`, `v2_privacy`, `v2_status`, `v2_title`, `b6a69…`) (11) | textbox/image | layout e avisos | — | — | Preservar; `v2_privacy` passa a declarar grão agregado |

### 6.3 Colunas não publicadas (fronteira técnica, `docs/acesso-cubos-bi.md`)

Chaves e atributos individuais nunca saem do DuckDB: `pesquisa_id`/`empresa_id`/`cliente_id`/`pergunta_id`, `titulo`, enunciado/alternativas/respostas, e-mail, `source_checksum`/`source_offset`, datas-marco por pesquisa, `flag_prorrogada`, `qtd_empresas_na_pesquisa`, `ano_edicao`, `cargo`/`departamento`, `pct_mercado`, `minutos` por ocorrência. Medidas I05–I13/I15/I19–I25 sem dado usam `DIM_INDICADORES_BLOQUEADOS` + motivo textual (DX-10), nunca zero. Drill-through para chave individual é proibido (RP-16).
