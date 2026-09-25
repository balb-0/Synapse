# Hierarquias do modelo semântico no Power BI

Cumpre a DX-06: constrói a hierarquia de tempo e a hierarquia de área, tipo e
perfil em [`powerbi/CentralPesquisasBI.SemanticModel/`](../powerbi/CentralPesquisasBI.SemanticModel/definition/tables/),
sobre os relacionamentos já montados pela DX-05.

## Hierarquia de tempo — `DIM_TEMPO.Calendario`

`Ano → Trimestre → Mês`. Não há nível de dia: nenhum dos quatro Parquet
publicados traz data diária (`docs/indicadores-publicaveis-bi.md`), e simular
um nível de dia vazio esconderia essa limitação em vez de documentá-la.
`DIM_TEMPO` é uma tabela calculada (`partition DIM_TEMPO = calculated`) que
reúne os meses distintos de `PUB_C02_PARTICIPACAO.mes_resposta` e
`PUB_C03_PIPELINE_MENSAL.data_fim_mes` — os dois únicos cubos publicados com
coluna de data. `PUB_C01_CICLO` e `PUB_C04_INSTRUMENTO` não têm papel de
tempo neste modelo: não há coluna de data em nenhum dos dois arquivos
publicados para eles.

`Trimestre` e `Mês` usam `sortByColumn` (`numero_trimestre`, `numero_mes`)
para ordenar cronologicamente, não por ordem alfabética — sem isso, "Abr"
apareceria antes de "Jan" ao percorrer a hierarquia.

## Hierarquia de área, tipo e perfil — `PUB_C03_PIPELINE_MENSAL."Area, Tipo e Perfil"`

`Área → Tipo → Perfil`. Diferente da hierarquia de tempo, esta é **degenerada
no próprio fato** `PUB_C03_PIPELINE_MENSAL`, não numa dimensão: perfil
(complexidade + tipo de resposta) só existe nesse cubo publicado
(`docs/contrato-fisico-cubos.md`; nenhum dos outros três traz essas colunas).
A coluna `perfil` é calculada (`[complexidade] & " / " & [tipo_resposta]`)
porque o Parquet publica complexidade e tipo de resposta como duas colunas
separadas, e o nível único da hierarquia precisa de uma única coluna.

Esta hierarquia não se estende aos outros três cubos publicados: `PUB_C01_CICLO`,
`PUB_C02_PARTICIPACAO` e `PUB_C04_INSTRUMENTO` continuam fatiáveis só por
Área → Tipo, usando os campos de `DIM_AREA` e `DIM_TIPO_PESQUISA` (DX-05) —
sem hierarquia formal de dois níveis, porque o Power BI só permite construir
o objeto `hierarchy` com colunas da mesma tabela, e área/tipo desses três
cubos vivem em dimensões separadas por desenho (conformadas, reutilizadas
entre cubos). Quem quiser esse drill de dois níveis num visual arrasta
`DIM_AREA[area]` e `DIM_TIPO_PESQUISA[tipo]` juntos no mesmo eixo — funciona
igual a uma hierarquia para navegação, só não aparece como um objeto único no
painel de campos.

## Verificação de total por nível

Como os quatro cubos chegam pré-agregados, um relacionamento ou hierarquia
mal montada quebra o total silenciosamente (a soma por subnível deixa de
bater com o nível agregado). Antes de considerar a DX-06 concluída, conferir
no Power BI Desktop:

- `SUM(qtd_pesquisas)` sem filtro de `DIM_AREA`/`DIM_STATUS_PESQUISA`/`DIM_TIPO_PESQUISA`
  bate com a soma da mesma medida fatiada por Ano → Trimestre → Mês (via
  `PUB_C02_PARTICIPACAO`, que é o único cubo de portfólio com papel de tempo
  — para `PUB_C01_CICLO`, que não tem coluna de data, a checagem de total é
  só entre os níveis de área/tipo/status, não de tempo).
- `SUM(qtd_pesquisas_no_status)` de `PUB_C03_PIPELINE_MENSAL`, filtrado por um
  único mês, bate ao somar por Área → Tipo → Perfil dentro desse mês — nunca
  somado entre meses diferentes (regra semiaditiva já registrada em
  `docs/especificacao-medidas-bi.md`).
