# Relacionamentos do modelo semântico no Power BI

Cumpre a DX-05: monta os relacionamentos entre fatos e dimensões do projeto
Power BI TMDL em [`powerbi/CentralPesquisasBI.SemanticModel/`](../powerbi/CentralPesquisasBI.SemanticModel/definition/relationships.tmdl),
com cardinalidade e direção de filtro explícitas em cada um, e sem caminho
ambíguo ativo.

## Por que não há chave substituta nos relacionamentos

`docs/contrato-fisico-cubos.md` descreve os fatos com chaves substitutas
(`sk_area`, `sk_tipo`, `sk_status` etc.). Os quatro Parquet publicados para o
Power BI (`docs/acesso-cubos-bi.md`) não carregam essas chaves — chegam já
agregados, só com os valores categóricos (`area`, `status`, `tipo`,
`tipo_pergunta`). Por isso as dimensões deste modelo não são cópias das
dimensões físicas: são tabelas calculadas com os valores distintos que
aparecem nos próprios cubos publicados, construídas em DAX
(`DISTINCT`/`UNION`/`ALLNOBLANKROW`, ver cada `tables/DIM_*.tmdl`).

## Dimensões e a que fatos se conectam

| Dimensão | Coluna-chave | Fonte dos valores distintos | Fatos relacionados |
| :-- | :-- | :-- | :-- |
| `DIM_AREA` | `area` | União de `PUB_C01_CICLO`, `PUB_C02_PARTICIPACAO`, `PUB_C03_PIPELINE_MENSAL`, `PUB_C04_INSTRUMENTO` | Todos os quatro cubos |
| `DIM_TIPO_PESQUISA` | `tipo` | União de `PUB_C01_CICLO`, `PUB_C02_PARTICIPACAO`, `PUB_C03_PIPELINE_MENSAL` | C01, C02, C03 |
| `DIM_TIPO_PERGUNTA` | `tipo_pergunta` | `PUB_C04_INSTRUMENTO` | Só C04 |
| `DIM_STATUS_PESQUISA` | `status` | União de `PUB_C01_CICLO`, `PUB_C03_PIPELINE_MENSAL` | C01, C03 |

`DIM_TIPO_PESQUISA` e `DIM_TIPO_PERGUNTA` são dimensões diferentes de
propósito: a primeira é o tipo da pesquisa (Mercado, Satisfação...), a
segunda é o tipo da questão do instrumento (única, múltipla...). Tratá-las
como a mesma dimensão juntaria dois domínios de valores sem relação, e é o
tipo de ambiguidade que este modelo evita deliberadamente.

`PUB_C04_INSTRUMENTO` publica `area` e `tipo_pergunta`; não publica `tipo`
de pesquisa. Use `DIM_TIPO_PERGUNTA` para segmentar questões e não ligue esse
cubo a `DIM_TIPO_PESQUISA` por um campo que não existe no contrato.

Os campos de relacionamento são os valores categóricos publicados. Em C02,
`mes_resposta` pode ser `NULL`: a participação permanece no fato agregado e a
data em branco é filtrada de `DIM_TEMPO`; a relação deixa essa chave para o
membro em branco virtual do Power BI, sem materializar uma linha física na
dimensão. Relatórios devem reconciliar essa parcela em separado. Em C03,
`data_fim_mes` é sempre o último dia do mês. A dimensão mantém essas datas
como chaves de relacionamento distintas e deriva a mesma hierarquia de ano,
trimestre e mês; `ano_mes` deve ser ordenado por `YYYYMM`, não pela data
física que varia entre os dois cubos.

## Cardinalidade e direção de filtro

Todo relacionamento em `relationships.tmdl` é **um-para-muitos** (um valor da
dimensão para muitas linhas do cubo agregado) com **filtro único** (a
dimensão filtra o fato, nunca o contrário):

```tmdl
relationship DimArea_PubC01Ciclo
	fromCardinality: many
	toCardinality: one
	crossFilteringBehavior: oneDirection
	fromColumn: PUB_C01_CICLO.area
	toColumn: DIM_AREA.area
```

Nenhum relacionamento deste modelo usa filtro bidirecional: como cada fato só
se conecta a cada dimensão por um único caminho (nenhuma dimensão está
duplicada nem existe relação fato-fato), o filtro único já basta para
qualquer combinação de fatia entre os quatro cubos, sem o risco de
ambiguidade que o filtro bidirecional introduziria numa constelação com
várias dimensões compartilhadas.

## Nenhum caminho ambíguo

O modelo é uma constelação (vários fatos, dimensões conformadas
compartilhadas), não uma única estrela — mas continua sem caminho ambíguo
porque:

- Nenhuma dimensão se repete no modelo (uma única `DIM_AREA`, não uma cópia
  por cubo).
- Nenhum fato se relaciona com outro fato.
- Nenhuma dimensão se relaciona com outra dimensão.

Ao abrir o modelo no Power BI Desktop, a Vista de Modelo não deve mostrar
nenhum aviso de relacionamento inativo por ambiguidade; se mostrar, é sinal
de que uma edição posterior introduziu um segundo caminho entre duas tabelas
e precisa ser revertida ou marcada como inativa (`isActive: false`), nunca
deixada ativa em paralelo com uma existente.

## Colunas ocultas nos fatos

Toda coluna de cada `PUB_C0*` fica `isHidden` no modelo — inclusive `area`,
`status` e `tipo`, apesar de serem a origem dos relacionamentos. Isso é
proposital: quem monta um visual deve fatiar sempre pela dimensão
(`DIM_AREA`, `DIM_TIPO_PESQUISA` etc.), nunca pela coluna bruta do fato, para
não acabar com dois campos "Área" diferentes no mesmo relatório. Coluna
oculta continua funcionando normalmente como lado do relacionamento — ocultar
não desativa o relacionamento, só tira a coluna da lista de campos do
relatório.

## Modelo carregado no Desktop

O [recibo do fixture](evidencias/bi03/desktop-modelo.json) registra consulta
real em VM Windows em 06/10/2026 às 14:08:45 UTC. As 13 partições do projeto
estavam processadas sem erro; o engine respondeu às consultas das sete
publicações. A comparação TOM do TMDL conferido com o engine teve 128 itens
e zero diferenças no escopo de tabelas, colunas, medidas, partições,
relacionamentos, hierarquias e expressões.

A comparação exclui tabelas automáticas de data, seus relacionamentos e
colunas internas de numeração de linha. Portanto, as afirmações de
cardinalidade e filtro acima descrevem os relacionamentos declarados pelo
projeto. Elas não descrevem todos os objetos internos que o Desktop cria.
O pacote sintético carregado foi ligado ao commit de origem `f068a01` pelo
inventário de 98 arquivos; o engine não fornece um marcador desse commit.
A carga v3 e a navegação visual pelas hierarquias têm aceites separados.

O recibo corrente é do pacote integrado `f068a01`, SHA256
`88a33f4963e9f2912794ad165c003d03822d24986817c2ce5909c8551207f89e`,
consultado em Power BI Desktop `2.158.1177.0` no Windows `10.0.26200.0`.
O recibo inicial do pacote `9726fd6` permanece no mesmo diretório de
evidências com sufixo `-inicial`; ele é histórico e usa o relógio já
sincronizado. Ambos usam o fixture, não a fonte final CB-16.
