# Hierarquias do modelo semântico no Power BI

Cumpre a DX-06: constrói a hierarquia de tempo e a hierarquia de área, tipo e
perfil em [`powerbi/CentralPesquisasBI.SemanticModel/`](../powerbi/CentralPesquisasBI.SemanticModel/definition/tables/),
sobre os relacionamentos já montados pela DX-05.

## Hierarquia de tempo — `DIM_TEMPO.Calendario`

`Ano → Trimestre → Mês`. Não há nível de dia: nenhum dos quatro Parquet
publicados traz data diária (`docs/indicadores-publicaveis-bi.md`), e simular
um nível de dia vazio esconderia essa limitação em vez de documentá-la.
`DIM_TEMPO` é uma tabela calculada (`partition DIM_TEMPO = calculated`) que
reúne as datas mensais observadas em `PUB_C02_PARTICIPACAO.mes_resposta` e
`PUB_C03_PIPELINE_MENSAL.data_fim_mes` — os dois únicos cubos publicados com
coluna de data. C02 usa o primeiro dia do mês; C03 usa o último dia do mês
observado.
As duas datas mantêm os relacionamentos exatos com cada arquivo e recebem os
mesmos valores de ano, trimestre e mês. `ano_mes` é ordenado por uma chave
numérica `YYYYMM`, que permanece igual para as duas datas daquele mês. Datas
nulas de C02 continuam sem ano, trimestre ou mês; não são convertidas em uma
data de calendário fictícia. `PUB_C01_CICLO` e `PUB_C04_INSTRUMENTO` não têm
papel de tempo neste modelo: nenhum dos dois arquivos publica coluna de data.

`Trimestre` e `Mês` usam `sortByColumn` (`numero_trimestre`, `numero_mes`)
para ordenar cronologicamente, não por ordem alfabética — sem isso, "Abr"
apareceria antes de "Jan" ao percorrer a hierarquia.

## Hierarquia de área, tipo e perfil — `PUB_C03_PIPELINE_MENSAL."Area, Tipo e Perfil"`

`Área → Tipo → Perfil`. Diferente da hierarquia de tempo, esta é **degenerada
no próprio fato** `PUB_C03_PIPELINE_MENSAL`, não numa dimensão: perfil
(complexidade + tipo de resposta) só existe nesse cubo publicado
(`docs/contrato-fisico-cubos.md`; nenhum dos outros três traz essas colunas).
A coluna `perfil` é calculada porque o Parquet publica complexidade e tipo de
resposta em colunas separadas, e o nível da hierarquia precisa de uma única
coluna. Se ambas forem `NULL`, `perfil` também fica `BLANK()`; se só uma faltar,
essa parte aparece como `Indisponível`, sem sugerir um perfil completo.

Esta hierarquia não se estende aos outros três cubos publicados: `PUB_C01_CICLO`
e `PUB_C02_PARTICIPACAO` podem ser fatiados por Área → Tipo de pesquisa,
usando `DIM_AREA` e `DIM_TIPO_PESQUISA` (DX-05). `PUB_C04_INSTRUMENTO` não
publica tipo de pesquisa; seus campos categóricos são Área e Tipo de pergunta,
que usam `DIM_AREA` e `DIM_TIPO_PERGUNTA`. Nenhum desses cubos tem uma
hierarquia formal de dois níveis porque as colunas pertencem a dimensões
separadas e o objeto `hierarchy` do Power BI usa colunas da mesma tabela.
Para navegar pelos níveis, arraste os campos relacionados juntos no mesmo
visual.

## Verificação de total por nível

Como os quatro cubos chegam pré-agregados, um relacionamento ou hierarquia
mal montada quebra o total silenciosamente (a soma por subnível deixa de
bater com o nível agregado). Antes de considerar a DX-06 concluída, conferir
no Power BI Desktop:

- `SUM(qtd_participacoes)` sem filtro categórico bate com a soma por Ano →
  Trimestre → Mês em `PUB_C02_PARTICIPACAO`. Reconcilie separadamente a
  parcela cuja `mes_resposta` é `NULL`: ela permanece contada no total, mas
  não pertence a um nível do calendário. `PUB_C01_CICLO` não tem coluna de
  data publicada; nele, a checagem de total é entre os níveis de área, tipo e
  status, não de tempo.
- `SUM(qtd_pesquisas_no_status)` de `PUB_C03_PIPELINE_MENSAL`, filtrado por um
  único mês, bate ao somar por Área → Tipo → Perfil dentro desse mês — nunca
  somado entre meses diferentes (regra semiaditiva já registrada em
  `docs/especificacao-medidas-bi.md`).
