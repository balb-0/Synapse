# Conferência das medidas contra a apuração de referência

As consultas e capturas Desktop deste registro são do snapshot anterior ao
CF-05. Seus resultados históricos 18 entradas/17 estados "Sem dado" não
representam o catálogo atual: 19 entradas/18 "Sem dado", com I16 bloqueado.
A execução Desktop após CF-04/CF-05 e o aceite final permanecem pendentes.

Cumpre a DX-11: confere cada medida publicada contra os valores já apurados
(`docs/resultados_analise.txt`, `docs/dmc.md`), com o resultado anexado —
automatizado onde há referência numérica fixa, documentado como checklist
manual onde não há.

## Conferência automatizada

[`scripts/analytics/conferir_medidas_bi.py`](../scripts/analytics/conferir_medidas_bi.py)
recalcula, a partir dos Parquet de uma geração publicada
(`docs/acesso-cubos-bi.md`), três valores de referência numérica registrados
na Sprint 2, com uma implementação independente da consulta de `publish.py`.
Esses números pertencem a um snapshot histórico: valor diferente, inclusive
maior, não passa automaticamente como crescimento legítimo nem reprova sozinho
a população atual. O script registra se cada arquivo existe, quantas linhas
contém e qual agregado produziu. Distingue caminho ausente, Parquet existente
sem linhas e coluna sem valor agregado; todos ficam não validados junto com
qualquer divergência e encerram com código 1. Para aceitar uma geração nova,
compare-a com a carga DuckDB reconciliada da mesma geração. Igualdade com uma
referência antiga também não substitui essa reconciliação de identidades.

| Medida | Referência | Fonte |
| :-- | :-- | :-- |
| `Qtd Pesquisas` | 366 | `docs/resultados_analise.txt`, T1 |
| `Base Valida Validacao` | 20 (cobertura bruta histórica de `data_aprov`; não é limite da geração atual) | `docs/resultados_analise.txt`, T1 |
| `Qtd Participacoes` | ≈18.735 | `docs/dmc.md`, seção 3.2 |

Rodar contra uma geração real:

```bash
PYTHONPATH=src python -m scripts.analytics.conferir_medidas_bi \
  --geracao /caminho/privado/publicacao-bi/GERACAO
```

Nenhuma diferença para cima é considerada prova de atualização legítima: linhas
duplicadas também podem aumentar o agregado. A suíte
[`scripts/analytics/test_conferir_medidas_bi.py`](../scripts/analytics/test_conferir_medidas_bi.py)
verifica igualdade histórica, divergência para cima/baixo e arquivo ausente com
Parquet sintético, além de distinguir arquivo vazio de caminho ausente e de
agregado sem valor — sem depender de acesso ao DuckDB privado, que este
repositório não versiona.

**Resultado anexado (a preencher por Anna ao rodar contra uma geração
real):**

| Medida | Arquivo presente | Linhas publicadas | Valor publicado | Valor de referência | Status |
| :-- | :-- | :-- | :-- | :-- | :-- |
| `Qtd Pesquisas` | _(rodar o script)_ | _(rodar o script)_ | _(rodar o script)_ | 366 | _(rodar o script)_ |
| `Base Valida Validacao` | _(rodar o script)_ | _(rodar o script)_ | _(rodar o script)_ | 20 | _(rodar o script)_ |
| `Qtd Participacoes` | _(rodar o script)_ | _(rodar o script)_ | _(rodar o script)_ | 18735 | _(rodar o script)_ |

## Checklist manual — medidas sem referência numérica fixa

As demais medidas de DX-07, DX-08 e DX-09 não têm um número pré-calculado
equivalente no material da Sprint 2 (os levantamentos anteriores não
segmentavam por área/status/tipo nem mediam qualidade por campo/relação).
Para cada uma, a conferência é contra uma consulta direta ao DuckDB de
origem no mesmo recorte — que só quem tem acesso ao banco privado pode
rodar. Tabela de apoio:

| Medida | Consulta de conferência direta |
| :-- | :-- |
| `Media Dias Validacao/Coleta/Tabulacao/Ciclo Total` | Mesma fórmula da medida (`docs/medidas-portfolio-ciclo.md`) rodada como `SELECT AVG(...)` sobre `ingestao_pesquisas_atual`, filtrando o mesmo par de datas válido. |
| `Media Minutos Preenchimento` | Idem, sobre `ingestao_respondentes`. |
| `Qtd Perguntas` | `SELECT tipo, COUNT(*) FROM ingestao_questoes_atual GROUP BY tipo` comparado à saída de `PUB_C04_INSTRUMENTO`. |
| `Completude`, `Integridade Referencial`, `Taxa de Duplicidade` | Rodar `scripts/data_quality/valida_kpis_qualidade.py` e `valida_integridade_referencial.py` (Sprint 2) sobre os mesmos CSVs de origem e comparar contra `PUB_QUALIDADE_*`; divergência esperada de grão, porque os scripts da Sprint 2 leem CSV bruto e a DX-09 lê `ingestao_*_atual` já tratada. |

## Indicadores sinalizados (DX-10)

`DIM_INDICADORES_BLOQUEADOS` é atualmente um catálogo de 19 linhas. Não é uma coleção de 19 medidas DAX.
Confira suas colunas `indicador`, `medida`, `status` e `motivo`, os 18 estados
"Sem dado", o único estado "Parcial" e `Qtd Indicadores Sem Dado` = 18. Só
`Taxa de Prorrogacao` e `Representatividade` têm medidas textuais próprias;
confira que cada uma exibe o motivo em qualquer contexto de filtro. Para os
demais itens, valide a linha do catálogo, sem esperar uma medida numérica ou
textual implementada. As consultas 6/6a do Desktop devem listar as quatro colunas e
conferir o catálogo atual de 19 linhas/18 sem dado e mostram apenas essas duas
medidas de texto junto com `Qtd Indicadores Sem Dado`.

## Medidas DAX do C03 (BI-04)

[`tests/analytics/test_medidas_bi.py`](../tests/analytics/test_medidas_bi.py)
calcula resultados de referência independentes para médias ponderadas,
denominador vazio, zero numérico, estoque 10→7 em dois fechamentos, período sem
fechamento e zero observado versus não observado. São testes Python do contrato,
não execução do motor DAX.

A consulta 1a compara o estoque da medida com a soma direta da fato C03 para
o fixture Desktop de `data_fim_mes` 28/02/2026 e estoque 4. A recuperação limpa
`DIM_TEMPO` e filtra a coluna de data da própria fato, mantendo os filtros de
categoria do estoque.

Para execução real no Windows com Power BI Desktop, abra o modelo carregado e
rode [`tests/analytics/dax/bi04-acceptance-queries.dax`](../tests/analytics/dax/bi04-acceptance-queries.dax)
na exibição de consultas DAX. Troque os dois meses de exemplo por fechamentos
observados na geração carregada. Confira também um mês que exista em
`DIM_TEMPO`, mas não tenha linha C03. O modelo deve mostrar o último fechamento
observado no contexto de tempo e os motivos textuais para estoque ausente e
transições não publicadas. A consulta 3 agrupa as colunas brutas C03 `[area]`,
`[tipo]` e `[perfil]`: com uma área filtrada sem linha no último fechamento,
confira que a data continua global e que o estoque do grupo é zero porque há
linhas C03 de outros grupos nesse fechamento. Sem linha C03 em todo o período,
estoque e data continuam `BLANK()`. A publicação atual não permite testar
fechamento observado sem nenhum grupo; não declare esse caso aceito até que o
contrato exponha o marcador.

## Consultas históricas do fixture em Power BI Desktop

O [recibo das medidas](evidencias/bi04/desktop-medidas-fixture.json) registra
consulta real em VM Windows em 06/10/2026 às 14:08:45 UTC, após sincronização
do relógio. A média ponderada de validação foi 5 dias com denominador 2,
e a média de preenchimento foi 10 minutos com denominador 2.
Os totais C01/C02/C04 foram 4/4/3.

O estoque da medida BI-04 foi 4 no último fechamento, 28/02/2026, igual à
soma direta filtrada na fato C03. As medidas de entrada e saída retornaram
valor nulo e o motivo de ausência de histórico. As duas medidas textuais
bloqueadas exibiram os motivos; o catálogo retornou 18 linhas e 17 estados
sem dado. A comparação TOM teve 128 itens e zero diferenças para a projeção
semântica do TMDL conferido, além de 98 arquivos de origem verificados.

O resultado é do fixture sintético. Não substitui a conferência das métricas
da geração v3. As consultas históricas acima não cobrem todas as médias de fases,
todos os recortes categóricos ou todos os edge cases do checklist acima.
Fechamento sem nenhum grupo observado continua sem representação suficiente
no contrato Parquet; não há aceite desse caso.

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

A geração corrigida `2c699f0b066847ee8559f1e31d88f49d`, referência
`synthetic-bi02-fixture`, retornou 2/3/4/2/64/8/5 linhas na ordem C01,
C02, C03, C04, qualidade por campo, relação e duplicidade. Seus totais
C01/C02/C04 foram 4/4/3. A integridade retornou 10/13, igual à consulta
independente de chave composta; o resultado antigo de 11/13 fica histórico.
As médias de validação, coleta, tabulação e ciclo total foram 5/5/4/15 dias,
com base 2 em cada fase; preenchimento teve média 10 minutos com base 2.

As consultas DAX de diagnóstico com `DATATABLE` e `DIVIDE` retornaram
média ponderada 8,2 contra média simples 5, zero numérico para numerador
zero/base positiva, e `BLANK()` para base zero. São probes de aritmética
no engine; não são medidas publicadas do modelo.

| Fase C01 v3 | Soma em dias | Base válida | Média ponderada |
| --- | ---: | ---: | ---: |
| Validação | 171 | 20 | 8,55 |
| Coleta | 4960 | 358 | 13,854748603351956 |
| Tabulação | 3020 | 330 | 9,151515151515152 |
| Ciclo total | 9468 | 331 | 28,604229607250755 |

C02 v3 retornou soma nula, base 0 e média nula. A completude foi
1844495/2584786 (0,7135967929259908), a integridade 833146/833146 (1),
e a duplicidade (275840-275840)/275840 (0). Os numeradores e denominadores
conferem com a apuração independente da ingestão. O catálogo manteve
18 entradas/17 estados "Sem dado" e duas medidas textuais individuais.
A taxa diagnóstica de finalização não é medida DAX publicada e não integra
os recibos públicos. C03 v3 retornou data e estoque nulos com motivo
textual de indisponibilidade. O contrato não representa fechamento global
observado sem grupo; esse caso continua sem aceite, sem converter ausência
em zero.

Recibos finais do [fixture](evidencias/bi04/desktop-medidas-fixture-final.json)
e da [v3](evidencias/bi04/desktop-medidas-v3-final.json) mantêm os resultados
separados das rodadas históricas.
