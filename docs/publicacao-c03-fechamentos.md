# Fechamentos observados de C03 na publicação

O [contrato físico](contrato-fisico-cubos.md#c03--pipeline-mensal) mantém
`FATO_PIPELINE_MENSAL` no grão mês, status, área, tipo e perfil. A carga grava
`analytics_pipeline_closure` mesmo quando o mês observado não tem pesquisas.
Nesse caso há um fechamento, zero membros e zero linhas no fato. A
[reconciliação](reconciliacao-analitica.md) valida esses controles antes de
`publish_cubes` escrever a geração, na mesma transação de leitura dos Parquet.

## Representação publicada

`PUB_C03_PIPELINE_MENSAL.parquet` conserva as nove colunas existentes e faz
parte dos mesmos sete Parquet da geração. Para não perder um fechamento vazio,
o publicador acrescenta **uma linha de marcador global por mês observado sem
grupos**. Essa é uma exceção ao grão dos grupos da publicação, declarada no
manifesto; não é um grupo dimensional nem uma nova linha do fato.

| Campo do marcador | Valor |
| :--- | :--- |
| `data_fim_mes` | Mês do fechamento persistido e conciliado |
| `status`, `area`, `tipo`, `complexidade`, `tipo_resposta` | `NULL`, pois não há grupo observado |
| `qtd_pesquisas_no_status` | `0` do tipo `BIGINT`, estoque global observado vazio |
| `qtd_entradas_no_mes`, `qtd_saidas_no_mes` | `NULL` do tipo `BIGINT`, pois o snapshot não registra transições |

Um mês sem fechamento não gera marcador e continua indisponível. Um grupo
positivo com categorias desconhecidas também pode ter os recortes `NULL`, mas
tem estoque positivo e um grupo no manifesto. Ele não é um marcador vazio.
A reconciliação rejeita um grupo de fato artificial com quantidade zero, pois
ele não corresponde a um grupo de membros observado.

## Campos do manifesto

Os campos abaixo ficam em `tables.PUB_C03_PIPELINE_MENSAL`, além de `file`,
`rows`, `columns` e `sha256`:

| Campo | Significado |
| :--- | :--- |
| `observation_state` | `observed` se há fechamento conciliado; `not_observed` se não há fechamento; `unverified` para fixture sintética sem controles |
| `fact_rows` | Quantidade de linhas de grupos em `FATO_PIPELINE_MENSAL`, incluindo todos os meses observados |
| `empty_closure_rows` | Quantidade de marcadores globais adicionados à publicação |
| `empty_closure_row_rule` | Regra explícita de identificação da linha de fechamento vazio |
| `observed_months` | Lista por mês com `month`, `observed_at`, `groups`, `stock` e `state` (`observed_zero` ou `observed_positive`) |

`observed_at` conserva o instante do controle DuckDB, sem atribuir um fuso que
a coluna `TIMESTAMP` não contém. Esses metadados não expõem IDs de pesquisa,
pessoa ou empresa, nem os membros individuais do fechamento. A reconciliação
prova coerência com o ledger persistido, sem atestar que uma fonte externa foi
capturada no instante de negócio declarado.

A equação de linhas da publicação é:

```text
rows = fact_rows + empty_closure_rows
fact_rows = soma de groups em observed_months
empty_closure_rows = quantidade de meses com groups = 0
```

`rows` não é a quantidade de pesquisas. Na reconciliação de C03, `loaded` é
a soma do estoque dos grupos, comparada aos membros persistidos. Por exemplo,
duas pesquisas num único grupo produzem `loaded = 2`, `fact_rows = 1` e
`rows = 1`. Um fechamento vazio tem `loaded = 0`, `fact_rows = 0`,
`empty_closure_rows = 1` e `rows = 1`. Nunca use essa soma de estoques históricos
como medida de BI entre períodos.

Uma fixture sem controles não recebe marcadores nem a lista de observações
verificadas. `observation_state = unverified` não permite concluir que houve
observação. Gerações antigas sem esses campos devem ser tratadas como sem prova
publicada de fechamento vazio; publique uma nova geração para obter a distinção.

## Consumo e limites dos filtros

No mês observado, a soma global de `qtd_pesquisas_no_status` retorna zero quando
o pacote contém somente o marcador daquele mês. No mês sem observação, a soma
sem linhas retorna `NULL` no DuckDB e deve permanecer indisponível no BI.
Não aplique `COALESCE(..., 0)` a meses sem observação. Estoque é semiaditivo:
some grupos disjuntos de um mesmo mês e nunca os estoques de vários meses.

O marcador tem recortes nulos e não cria estoque zero para cada área, status,
tipo ou perfil. Um filtro por uma categoria conhecida exclui o marcador; esse
recorte sem linhas continua indisponível. A lista `observed_months` permite
informar que o **estoque global** do mês foi observado vazio. Os consumidores
devem consultar essa lista para reconhecer o marcador em tabelas de detalhe e
navegação; não devem apresentar seus recortes nulos como um grupo de negócio.

A recarga no mesmo instante conserva o fechamento anterior. Uma observação
mais recente do mesmo mês substitui membros e grupos, podendo retirar o
marcador global e publicar estoque positivo. Os demais meses permanecem.
Uma falha de reconciliação bloqueia a publicação e mantém `current.json` na
geração anterior.

## Verificação reproduzível

```bash
PYTHONPATH=src python -m unittest tests.analytics.test_publish_c03 tests.analytics.test_publish -v
```

Os testes abrem um DuckDB isolado, carregam os controles reais, publicam os
sete Parquet e consultam os arquivos sem acesso ao banco de origem. Cobrem
estoque positivo, fechamento vazio, mês ausente, grupo desconhecido positivo,
recarga no mesmo instante, substituição por instante mais recente, filtro por
mês/categoria e fechamento adulterado. Conferem schema, manifesto e contagens.
Esses testes não afirmam execução DAX nem refresh no Power BI Desktop.
