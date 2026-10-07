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

## Modelo carregado no ensaio histórico

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

O recibo desta rodada histórica é do pacote integrado `f068a01`, SHA256
`88a33f4963e9f2912794ad165c003d03822d24986817c2ce5909c8551207f89e`,
consultado em Power BI Desktop `2.158.1177.0` no Windows `10.0.26200.0`.
O recibo inicial do pacote `9726fd6` permanece no mesmo diretório de
evidências com sufixo `-inicial`; ele é histórico e usa o relógio já
sincronizado. Ambos usam o fixture, não a fonte final CB-16.

## Limite identificado no fixture histórico

A geração sintética `665cb490f85d49529488b4910e094923` antecede a correção
da identidade composta de respostas para questões. A publicação de
qualidade somava 11 correspondências em 13 chaves informadas; a consulta
independente com `(pesquisa_id, pergunta_id)` produz 10/13. A quantidade de
linhas das sete tabelas não muda, por isso as contagens sozinhas não
detectaram essa divergência. Os recibos dessa geração são históricos e
marcados `historical_stale_publication`; não aceitam o KPI I18.

O fixture foi regenerado com o publicador corrigido, na geração
`2c699f0b066847ee8559f1e31d88f49d`, conservando as sete contagens e
publicando 10/13. Sua execução Desktop corrigida está registrada na seção final desta página.
A fonte v3 tem todas as relações de qualidade conferidas contra a ingestão
sem divergências; este problema é da publicação sintética antiga.

## Execução final do pacote integrado

A revisão executada foi `ff760d6552a1d5d2d3d9d9da1f3467e2c913416a`, pacote SHA256
`a9b087e5a9e4e0d56af8d7b36fe0a687857b205e7c59b6dbd44c9dd7c2358cea`, inventário SHA256
`1624eef9ad87a61af4146cc0c67e469014cb830829bc9562a04ba70eaeca8ac6`, com 98 arquivos conferidos no Windows.
O fixture corrigido foi consultado em `2026-10-06T15:44:25.2528117Z` e a v3 em
`2026-10-06T15:49:13.5533810Z`, no Desktop real `2.158.1177.0`, Windows
`10.0.26200.0`, por automação em VM. O parâmetro local foi conferido
por arquivo e pela expressão no modelo ativo. As 13 partições do projeto
e duas automáticas de data estavam processadas sem erro. A comparação TOM
teve 128 itens e zero diferenças. Ela compara a projeção semântica
declarada; não fornece um marcador do commit exato dentro do engine.
O SHA do pacote executado permanece distinto dos commits documentais
posteriores anexados às MRs.

### Reproduzir a fonte do PBIP

A revisão executada está [no GitLab](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/tree/ff760d6552a1d5d2d3d9d9da1f3467e2c913416a).
Busque a branch de validação e abra essa revisão em uma pasta ainda
inexistente, preservando o checkout de trabalho:

```bash
git fetch origin test/bi-desktop-integrated
git worktree add --detach ../bi-pacote-conferido ff760d6552a1d5d2d3d9d9da1f3467e2c913416a
```

O inventário compara os arquivos versionados de `powerbi/`, exceto
`powerbi/CentralPesquisasBI.SemanticModel/definition/expressions.tmdl`,
cujo parâmetro foi adaptado somente na cópia privada Windows. O parâmetro
tem conferência própria por arquivo e expressão no modelo ativo.
Esse checkout reproduz a fonte PBIP e seu inventário; a geração Parquet
autorizada e o ZIP conferido permanecem privados.

As somas C02 por Ano, Trimestre e Mês retornaram o total 4 incluindo
o membro em branco virtual. Uma participação tem mês nulo; as três com
data e a parcela em branco reconciliam o total. C03 teve estoque 3 em
31/01/2026 e 4 em 28/02/2026. Os totais por Área, Área/Tipo e
Área/Tipo/Perfil coincidiram com 3 e 4 em cada fechamento. O último estoque
foi 4, sem somar os dois fechamentos em 7. Março de 2026 existe no
calendário por C02 e não tem fechamento C03; estoque retornou `BLANK()`.
Na v3, todas as 17740 participações têm mês nulo. Os totais por níveis do
calendário incluem esse membro em branco; a parcela com data é zero.
A v3 não oferece fechamento C03 para demonstrar navegação temporal observada.
Essas consultas exercitam as definições carregadas e a reconciliação por
nível; não declaram operação humana de drill na interface.

O [recibo final](evidencias/bi03/desktop-modelo-final.json) comprova
as definições e os resultados de reconciliação descritos.
