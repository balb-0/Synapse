# Medidas de questionários e de qualidade do dado

Cumpre a DX-09: implementa a medida de questionário em
[`PUB_C04_INSTRUMENTO.tmdl`](../powerbi/CentralPesquisasBI.SemanticModel/definition/tables/PUB_C04_INSTRUMENTO.tmdl)
e as medidas de qualidade em três tabelas novas
(`PUB_QUALIDADE_CAMPO.tmdl`, `PUB_QUALIDADE_RELACAO.tmdl`,
`PUB_QUALIDADE_DUPLICIDADE.tmdl`), que passam a existir porque esta tarefa
também estende [`src/etl/analytics/publish.py`](../src/etl/analytics/publish.py)
com três publicações novas — decisão registrada abaixo.

## Questionário

| Medida | DAX | Regra aplicada |
| :-- | :-- | :-- |
| `Qtd Perguntas` | `SUM(PUB_C04_INSTRUMENTO[qtd_perguntas])` | Conta associação pesquisa-pergunta, não resposta nem respondente (regra 4 de DX-03). A regra de denominador por tipo de questão não se aplica aqui: `respostas` não é publicada, então não há distribuição de alternativa para dividir por tipo (`docs/especificacao-medidas-bi.md`). |

## Decisão sobre a fonte de qualidade do dado

`docs/indicadores-publicaveis-bi.md` (DX-01) já registrava que I16
(completude), I17 (duplicidade) e I18 (integridade referencial) eram
calculáveis na camada de dados mas **sem dado publicado** para o Power BI —
os scripts que calculam isso hoje
(`scripts/data_quality/valida_kpis_qualidade.py`,
`valida_integridade_referencial.py`) só imprimem no console, não geram
arquivo consumível.

Esta tarefa publica diagnósticos físicos estendendo `publish.py` com três consultas SQL
novas sobre as views de ingestão (`ingestao_*_atual`), no mesmo padrão de
geração, checksum e manifesto dos quatro cubos originais — nenhuma mudança
no fluxo de publicação além de três entradas a mais no dicionário
`PUBLICATIONS`. Isso corresponde à opção (a) do plano original ("pedir um
artefato publicado adicional"), implementada diretamente em vez de deixada
como pedido em aberto.

### O que cada arquivo novo publica

| Arquivo | Consulta (`publish.py`) | Grão | Indicador |
| :-- | :-- | :-- | :-- |
| `PUB_QUALIDADE_CAMPO` | `_sql_qualidade_campo()` — completude por coluna de negócio (`COLUNAS_QUALIDADE`) | (tabela, campo) | Preenchimento físico; não implementa I16 aplicável |
| `PUB_QUALIDADE_RELACAO` | `_sql_qualidade_relacao()` — as mesmas oito relações de `valida_integridade_referencial.py`, com nomes canônicos pós-transformação (`RELACOES_QUALIDADE`) | (relação, ex. `respondentes.empresa_id`) | I18 |
| `PUB_QUALIDADE_DUPLICIDADE` | `_sql_qualidade_duplicidade()` — linhas vs. chaves de negócio distintas na tabela de ingestão **bruta** (`CHAVES_QUALIDADE`) | tabela de origem com chave de negócio | I17 |

`respondentes` fica fora de `PUB_QUALIDADE_DUPLICIDADE`: não tem chave de
negócio (identidade é a ocorrência física, ver
`etl.load.ddl.create_current_view`), então "duplicidade" não é um conceito
aplicável a essa fonte. Nenhuma das três consultas seleciona valor de campo
sensível (e-mail, enunciado, resposta) — só nome de tabela/campo/relação e
contagens agregadas, testado em
`tests/analytics/test_publish.py::test_publishes_physical_completion_integrity_and_duplicates`.

## Medidas de qualidade implementadas

| Medida | DAX | Regra aplicada |
| :-- | :-- | :-- |
| `Completude` (`PUB_QUALIDADE_CAMPO`) | `DIVIDE(SUM(qtd_preenchidas), SUM(qtd_linhas))` | Completude de preenchimento: `COUNT(coluna)` / `COUNT(*)`, sem filtro de aplicabilidade; `DIVIDE` retorna `BLANK()` com base zero. Base exposta (`Base Valida Completude`). |
| `Integridade Referencial` (`PUB_QUALIDADE_RELACAO`) | `DIVIDE(SUM(qtd_chaves_correspondentes), SUM(qtd_chaves_informadas))` | Idem, base `Base Valida Integridade`. FK nula já sai do numerador e do denominador na própria consulta de origem. |
| `Taxa de Duplicidade` (`PUB_QUALIDADE_DUPLICIDADE`) | `DIVIDE(SUM(qtd_linhas) - SUM(qtd_chaves_distintas), SUM(qtd_linhas))` | Base `Base Valida Duplicidade`; a diferença entre linhas e chaves distintas é a própria contagem de duplicatas. |

## Limite de completude e I16

A implementação mede preenchimento físico na ingestão tratada. O denominador
conta todas as linhas da fonte para cada campo. O numerador conta valores SQL
não nulos após transformação. Não valida conteúdo, sentinelas remanescentes
ou exigência de preenchimento. Um nulo condicional contribui para a base e
não para o numerador; isso não o classifica como defeito.

Ao selecionar vários campos, cada linha contribui uma célula por campo. A
razão total é ponderada por essas bases, sem média simples dos percentuais e
sem contar linhas ou pessoas distintas. Exemplo: duas questões sem atributos
de matriz produzem base 2 e preenchidas 0 em cada atributo monitorado; o
resultado físico é 0%, mesmo que esses atributos não sejam exigidos.

A completude aplicável de I16 exige regras homologadas de obrigatoriedade
por campo e tipo/status, com numerador e denominador restritos ao universo
aplicável. Essas regras não estão publicadas; I16 aparece como "Sem dado" em
`DIM_INDICADORES_BLOQUEADOS`. A medida `Completude` mantém seu identificador
para preservar vínculos existentes; sua descrição declara a semântica física.
Não usar seu valor para aprovar ou reprovar a meta de campos obrigatórios da
política de governança.

## O que ainda fica de fora (I19, I20)

Parseabilidade (I19) e divergência de título (I20) continuam sem consulta
publicada nesta rodada — não foram resolvidas pela mesma extensão porque
exigem lógica diferente (tentativa de conversão de tipo por campo, e
comparação textual de título entre fontes) que nenhum script existente já
calcula de forma reutilizável. Ficam registradas como candidatas à mesma
extensão de `publish.py`, sinalizadas como indisponíveis pela DX-10 até lá.

## Conferência da semântica (06/10/2026)

A correção altera descrições, rótulos PBIR e o catálogo de disponibilidade;
a fórmula e os sete arquivos publicados permanecem com o mesmo contrato.
O cartão e a tabela da página `c03c04qualidade01` usam "Completude de
preenchimento". O catálogo atual tem 19 entradas, sendo 18 "Sem dado" e
I03 "Parcial", após explicitar o bloqueio de I16.

Os testes de publicação exercitam nulos em campos de matriz de questões
não matriciais, soma de células por campo, texto não nulo vazio e fonte sem
linhas. Os testes PBIR verificam que os vínculos continuam apontando para
`PUB_QUALIDADE_CAMPO.Completude` e que seus rótulos não atribuem o resultado
a I16. Esses testes executam SQL em DuckDB e inspecionam definições; não
executam DAX nem renderizam a página no Power BI Desktop.

Capturas e recibos de Desktop anteriores a esta correção registram a revisão
executada na sua data. O título anterior "Completude aplicável (I16)" e as
contagens 18/17, quando presentes, são históricos e não demonstram o estado
corrigido. Não foi produzida uma nova captura Desktop nesta correção; a
conferência visual e o refresh desse modelo continuam necessários para
registrar sua execução no Desktop.
