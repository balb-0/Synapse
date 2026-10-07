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
nulas de C02 permanecem no fato, mas são filtradas da dimensão antes de
materializar as datas; não são convertidas em uma data de calendário fictícia.
Na relação, o Power BI pode representá-las pelo membro em branco virtual de
integridade referencial, sem uma linha física em `DIM_TEMPO`. `PUB_C01_CICLO`
e `PUB_C04_INSTRUMENTO` não têm papel de tempo neste modelo: nenhum dos dois
arquivos publica coluna de data.

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
  parcela cuja `mes_resposta` é `NULL`: ela permanece contada no total e deve
  ser reconciliada separadamente pelo membro em branco, sem uma linha física
  correspondente em `DIM_TEMPO`. `PUB_C01_CICLO` não tem coluna de
  data publicada; nele, a checagem de total é entre os níveis de área, tipo e
  status, não de tempo.
- `SUM(qtd_pesquisas_no_status)` de `PUB_C03_PIPELINE_MENSAL`, filtrado por um
  único mês, bate ao somar por Área → Tipo → Perfil dentro desse mês — nunca
  somado entre meses diferentes (regra semiaditiva já registrada em
  `docs/especificacao-medidas-bi.md`).

## Evidência de hierarquias carregadas

A [conferência TOM no Desktop](evidencias/bi03/desktop-modelo.json) incluiu as
hierarquias e colunas na projeção semântica do modelo ativo, sem diferenças
para o TMDL conferido. As consultas das publicações executaram com o modelo
processado. Esta evidência confirma as definições carregadas; não registra
uma pessoa usando os níveis de drill em cada visual. O recibo histórico não registra navegação humana ou reconciliação por todos
os subníveis. A seção final acrescenta a reconciliação DAX por nível, sem
declarar cliques humanos na interface.

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

Veja o [recibo final](evidencias/bi03/desktop-modelo-final.json).
