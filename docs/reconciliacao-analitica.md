# Reconciliação dos cubos analíticos

`PYTHONPATH=src python -m etl.analytics.reconcile /caminho/para/analitico.duckdb` abre o banco somente para leitura, emite um JSON por consulta e retorna código 1 se encontrar diferença ou se não houver snapshot conciliado de `respondentes`. Execute depois de `load_analytics` no mesmo arquivo DuckDB. Se houver apenas ingestão, a função informa quais tabelas analíticas faltam e pede a carga antes da reconciliação. O relatório não publica identificadores de pesquisa, cliente, empresa ou participante; `respondent_checksum` identifica o arquivo selecionado e permite ligar o resultado ao controle de ingestão.

## População e equação

| Cubo | População elegível | Fato carregado | Regra de descarte |
| :--- | :--- | :--- | :--- |
| C01 | Uma linha por `pesquisa_id` em `ingestao_pesquisas_atual` | Uma linha de `FATO_CICLO_PESQUISA` por pesquisa | Nenhum descarte depois da view corrente. Versões anteriores da mesma pesquisa não pertencem à população elegível. |
| C02 | Ocorrências (`source_checksum`, `source_offset`) do último arquivo de `respondentes` concluído e conciliado | Ocorrências de `FATO_PARTICIPACAO` do mesmo checksum | Nenhum descarte. Outros arquivos são versões de snapshot fora do recorte, não rejeições desta carga. |
| C03 | Membros de `analytics_pipeline_membership` registrados na mesma transação de cada fechamento observado | Soma de `qtd_pesquisas_no_status` por mês e grupo | Nenhum descarte. `analytics_pipeline_closure` registra inclusive um mês observado com estoque zero. |
| C04 | Pares (`pesquisa_id`, `pergunta_id`) em `ingestao_questoes_atual` | Pares `pesquisa_id_origem`, `pergunta_id_origem` em `FATO_PESQUISA_PERGUNTA` | Nenhum descarte. Vínculo órfão da pesquisa usa a chave desconhecida sem descartar a pergunta. |

Para cada cubo, o relatório calcula `difference = eligible - loaded - discarded`. C01, C02 e C04 também fazem `EXCEPT` das identidades nos dois sentidos. C03 compara quantidade e instante observado por mês e grupo com os membros persistidos. Uma diferença zero não passa quando uma linha faltante é compensada por outra inesperada. Na carga atual, `discarded = 0` é uma regra do contrato e cada ocorrência elegível deve aparecer no fato. Se surgir uma política futura de descarte, ela exige motivo persistido por ocorrência e alteração desta equação; não use `0` para encobrir linhas rejeitadas.

Rejeições da transformação pertencem ao controle de ingestão (`reconciliacao_execucao`, `rejected`, `rejected_reason`) e não entram na população das views atuais. O relatório analítico não reclassifica rejeição da ingestão como descarte do cubo. Participações sem pesquisa ou empresa continuam no fato com a chave desconhecida. `cliente_id` ausente é uma ausência estrutural e deixa `sk_pessoa` nula; `cliente_id` informado sem dimensão correspondente usa a chave desconhecida. Para C04, uma pesquisa sem ID correspondente só recebe vínculo por título quando a correspondência normalizada é única; caso contrário mantém a chave desconhecida. `orphan_reasons` agrupa o registro de origem, alvo, motivo e método, sem mostrar IDs. `orphan_audit` compara os IDs técnicos de origem e sua multiplicidade com cada motivo registrado. O JSON informa apenas quantos IDs faltam ou sobram; não revela os IDs. Uma troca de ID no log faz o gate falhar mesmo quando as contagens por motivo conferem.

`analytics_load_run` identifica a última execução analítica com `load_id`, `loaded_at`, checksum de respondentes e digests das quatro views correntes usadas pela carga. O relatório recalcula esses digests antes de aceitar o estado: uma correção de conteúdo que mantém o mesmo grão e contagem invalida a reconciliação da execução anterior. A leitura deve ocorrer em um arquivo estável após o commit da carga; não confunda o horário local de leitura com o instante observado do negócio.

## Fechamentos mensais

O estado atual de C01 não é prova do que existia no fim de um mês anterior. `analytics_pipeline_membership` conserva as chaves de pesquisa, grupo e instante observados no fechamento, na mesma transação que grava C03. `analytics_pipeline_closure` marca o mês, o instante e o `load_id`, inclusive quando não havia pesquisa. O relatório compara as quantidades desse registro com cada linha do fato, inclusive o instante, e rejeita dois instantes no mesmo mês. Também exige marcador para qualquer execução registrada com fechamento e lista cada mês observado, número de grupos e soma de `qtd_pesquisas_no_status`. `not_observed` significa que não há fechamento e que o estoque histórico é indisponível; não significa estoque zero. Um mês marcado com zero membros e zero fato tem `eligible = 0`, `loaded = 0` e status `ok`.

Entradas e saídas mensais seguem indisponíveis, pois os snapshots não registram transições. Nunca some estoques de meses diferentes. `reconciled=true` indica que a identidade dos cubos correntes, a contagem histórica de C03 e o log dos vínculos órfãos passaram. O ledger conserva as identidades de fechamento, mas o relatório não prova que a captura ocorreu no dia real de negócio declarado por uma fonte externa.

## Interpretação de estados

- `ok`: contagem e identidades do cubo corrente, ou membros e grupos do fechamento mensal, conferem.
- `mismatch`: diferença de contagem, identidade ausente/inesperada ou estrutura mensal inconsistente.
- `source_unavailable`: nenhum snapshot conciliado de `respondentes`; C02 não pode ser declarada vazia ou conciliada.
- `not_observed`: não existe fechamento mensal registrado.

`missing_keys` e `unexpected_keys` são diferenças de identidade entre origem e fato, ou de mês, grupo, instante e quantidade em C03; `difference` é a diferença aritmética. O relatório não altera tabelas. Se a carga falhar e o banco conservar o estado anterior, uma origem corrente nova produz `mismatch` até uma carga bem-sucedida. Repita o comando após a carga e registre `load_id`, horário da carga, totais e estados agregados na documentação, sem incluir dados individuais no Git.

## Resultado da execução

Em 2026-10-06, `etl.analytics.reconcile` foi executado em modo somente leitura sobre `data/duckdb/cb13-v3-analitico.duckdb`, o DuckDB local não versionado da carga CB-13. O JSON retornou `load_id=65d139e0-488d-4601-9361-ae153731145c`, `loaded_at=2026-10-06T20:32:49.419493`, `source_digests_match=true` e `reconciled=true`. O resultado `reconciled=true` atesta a consistência dos dados disponíveis; não implica que exista um fechamento observado para C03.

| Cubo | `eligible` | `loaded` | `discarded` | `difference` | `missing_keys` | `unexpected_keys` | `status` |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| C01 | 366 | 366 | 0 | 0 | 0 | 0 | `ok` |
| C02 | 17.740 | 17.740 | 0 | 0 | 0 | 0 | `ok` |
| C03 | `null` | 0 | 0 | `null` | 0 | 0 | `not_observed` |
| C04 | 3.186 | 3.186 | 0 | 0 | 0 | 0 | `ok` |

As identidades de origem e fato conferem nos dois sentidos para C01, C02 e C04. Em C03, `eligible=null`, `difference=null` e `monthly_closures=[]` indicam ausência de fonte temporal observada; as zero linhas do fato não são um estoque zero. O retrato recebido do parceiro não permite reconstruir um fechamento mensal passado. Esta reconciliação não verifica `ingestao_respostas_atual` nem amplia a cobertura de respostas descrita na carga CB-13.

`orphan_reasons=[]`: nenhum vínculo órfão foi registrado. A auditoria de identidades dos órfãos retornou os seguintes totais agregados, sem expor IDs de origem:

| Fonte | Dimensão alvo | Motivo | `expected` | `logged` | `missing_ids` | `unexpected_ids` |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| `respondentes` | `DIM_PESQUISA` | `pesquisa_id_ausente` | 0 | 0 | 0 | 0 |
| `respondentes` | `DIM_EMPRESA` | `empresa_id_ausente` | 0 | 0 | 0 | 0 |
| `respondentes` | `DIM_PESSOA` | `cliente_id_ausente` | 0 | 0 | 0 | 0 |
| `questoes` | `DIM_PESQUISA` | `sem_vinculo_unico` | 0 | 0 | 0 | 0 |
| `questoes` | `DIM_PESQUISA` | `id_divergente` | 0 | 0 | 0 | 0 |

Não houve `mismatch` nem correção localizada nesta execução. Uma mudança futura nas fontes exige nova carga e nova reconciliação do mesmo DuckDB; se houver falha, corrigir a causa identificada pelo JSON antes de registrar novos totais.
