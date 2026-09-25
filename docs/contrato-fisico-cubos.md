# Contrato físico da camada analítica

Este contrato define as estruturas derivadas da ingestão tratada no DuckDB. A origem executável das colunas é `src/etl/transformation/schema.py`; as tabelas e views de ingestão são definidas em `src/etl/load/ddl.py`. O Data Model Canvas (`docs/dmc.json`) descreve o objetivo analítico, mas não substitui a verificação de uma coluna de origem. Os nomes físicos abaixo são únicos para os quatro cubos. Um estado `indisponível` significa ausência de evidência para calcular a medida e nunca significa zero.

## Limite da origem e seleção de versões

| Fonte | Relação usada | Regra de identidade |
| :--- | :--- | :--- |
| `pesquisas` | `ingestao_pesquisas_atual` | `pesquisa_id` na versão corrente |
| `empresas` | `ingestao_empresas_atual` | `empresa_id` na versão corrente |
| `clientes` | `ingestao_clientes_atual` | `cliente_id` na versão corrente |
| `respondentes` | `ingestao_respondentes` | ocorrência física (`source_checksum`, `source_offset`); não há chave natural confirmada |
| `questoes` | `ingestao_questoes_atual` | (`pesquisa_id`, `pergunta_id`) na versão corrente |
| `respostas` | nenhuma relação analítica nesta entrega | `respondent_id` não possui ponte comprovada para `cliente_id` |

A rotina de carga escolhe para `respondentes` o `source_checksum` da última execução completa e conciliada dessa fonte, ordenada por conclusão e, em empate, por checksum. Carrega as ocorrências daquele arquivo, identificadas por (`source_checksum`, `source_offset`). Reprocessar o mesmo arquivo não muda o conjunto mesmo quando a ingestão ignora linhas já gravadas. Uma execução sem checksum ou não conciliada não substitui o snapshot corrente. Somar todas as reexportações físicas como participações novas duplicaria fatos. `ingested_at` não é tempo de negócio.

## C01 — Portfólio e Ciclo

| Item | Contrato |
| :--- | :--- |
| Fato | `FATO_CICLO_PESQUISA` |
| Tipo e grão | Snapshot acumulativo, uma linha corrente por `pesquisa_id` |
| Origem | `ingestao_pesquisas_atual` |
| Chave | `sk_pesquisa` único, com `pesquisa_id` durável na dimensão |
| Dimensões | `DIM_PESQUISA`; seis papéis diários de `DIM_TEMPO` (`sk_data_solicitacao`, `sk_data_aprovacao`, `sk_data_divulgacao`, `sk_data_limite_coleta`, `sk_data_prorrogacao`, `sk_data_entrega`); `DIM_AREA`, `DIM_STATUS_PESQUISA`, `DIM_TIPO_PESQUISA`, `DIM_PERFIL_PESQUISA`, `DIM_FAMILIA_PESQUISA`, `DIM_FONTE_DADO`, `DIM_EXECUCAO_CARGA` |

| Medida armazenada | Tipo e cálculo | Agregação e limite |
| :--- | :--- | :--- |
| `dias_corridos_validacao` | Inteiro; `data_aprov - data_solicitacao` quando ambas existem e o fim não antecede o início | Duração por pesquisa; médias exigem denominador de pares válidos. Não rotular como dias úteis. |
| `dias_corridos_coleta` | Inteiro; `COALESCE(prorrogada_ate, data_limite) - data_divulgacao`, com par válido | Duração por pesquisa; não somar com ciclo total. |
| `dias_corridos_tabulacao` | Inteiro; `data_entrega - COALESCE(prorrogada_ate, data_limite)`, com par válido | Duração por pesquisa; não somar com ciclo total. |
| `dias_corridos_ciclo_total` | Inteiro; `data_entrega - data_solicitacao`, com par válido | Não aditiva em relação às fases; nunca somar ciclo total e fases como se fossem períodos disjuntos. |
| `qtd_empresas_na_pesquisa` | Inteiro anulável; `participantes` declarado na origem | Não aditiva entre pesquisas; não equivale às empresas distintas observadas em C02. |
| `flag_prorrogada` | Booleano; `prorrogada_ate IS NOT NULL` | Filtro, não medida para soma sem denominador. |

Os nomes antigos `dias_uteis_*` não podem representar subtração simples de datas: o calendário de feriados e sua homologação não existem na ingestão. Nenhuma medida de dias úteis é publicada nesta versão. `qtd_respondentes_na_pesquisa` foi removida de C01; `tempo_preenchimento` não é contagem de pessoas. `DIM_PESQUISA.ano_edicao` não tem coluna de origem nem derivação homologada e fica indisponível. `DIM_FAMILIA_PESQUISA` pode armazenar proposta determinística de título normalizado com estado de homologação pendente; não publicar família como classificação aprovada.

## C02 — Participação e Representatividade

| Item | Contrato |
| :--- | :--- |
| Fato | `FATO_PARTICIPACAO` |
| Tipo e grão | Fato transacional, uma linha por ocorrência elegível do snapshot de `respondentes` selecionado |
| Chave | Identidade da ocorrência de origem, sem confundir duplicata de pessoa com duplicata técnica de arquivo |
| Dimensões | `DIM_PESQUISA`, `DIM_EMPRESA`, `DIM_PESSOA` quando `cliente_id` for conciliado, `DIM_TEMPO` nos papéis opcionais `sk_data_pesquisa` e `sk_data_resposta` |

| Medida/atributo | Tipo e cálculo | Agregação e limite |
| :--- | :--- | :--- |
| `qtd_participacao` | Inteiro constante 1 por ocorrência carregada | Aditiva no conjunto de ocorrências; não é contagem de respostas a perguntas. |
| `seq_ocorrencia` | Inteiro anulável, ordenação determinística das ocorrências para (`pesquisa_id`, `cliente_id`) quando a pessoa existe | Atributo de deduplicação, não medida aditiva; sem `cliente_id` não atribuir sequência fictícia. |
| `minutos_preenchimento` | Inteiro anulável, diferença entre `hora_termino` e `hora_inicio` convertida em minutos completos quando o par e a ordem são válidos | Média exige contagem de pares válidos; ausências e pares inválidos ficam `NULL` com motivo. |
| `pct_mercado_na_participacao` | `DECIMAL(18,6)` anulável, valor de `respondentes.market_share` | Descritivo por participação; não somar nem publicar I09 enquanto a fonte autoritativa divergir de `empresas.part_mercado`. |

`cliente_id` é a chave de origem da entidade chamada `DIM_PESSOA`; trata-se de diferença de nome, não falta de origem. `respondent_id` de `respostas` não é uma chave dessa dimensão. `DIM_EMPRESA.regiao` não tem coluna de origem nem mapa estadual homologado; fica indisponível. Cargo e departamento de `clientes` são restritos e não entram no acesso externo sem regra de agrupamento e limiar de anonimização demonstrados.

## C03 — Pipeline Mensal

| Item | Contrato |
| :--- | :--- |
| Fato | `FATO_PIPELINE_MENSAL` |
| Tipo e grão | Snapshot periódico de fim de mês, uma linha por (`sk_data_fim_mes`, `sk_status`, `sk_area`, `sk_tipo`, `sk_perfil`) |
| Origem | Estado de C01 observado no fechamento mensal, **após** o início da captura; snapshots históricos não são reconstruídos por `ingested_at` |
| Dimensões | `DIM_TEMPO`, `DIM_STATUS_PESQUISA`, `DIM_AREA`, `DIM_TIPO_PESQUISA`, `DIM_PERFIL_PESQUISA` |

| Medida | Tipo e cálculo | Agregação e limite |
| :--- | :--- | :--- |
| `qtd_pesquisas_no_status` | Inteiro, contagem de pesquisas distintas da combinação no fechamento observado | Semiaditiva: somável entre grupos disjuntos do **mesmo mês**, nunca entre meses. Sem fechamento observado, não há linha histórica. |
| `qtd_entradas_no_mes` | Inteiro anulável | Indisponível sem histórico de transições; diferença líquida entre snapshots não fornece entradas. |
| `qtd_saidas_no_mes` | Inteiro anulável | Indisponível sem histórico de transições; diferença líquida entre snapshots não fornece saídas. |

`qtd_a_finalizar` foi removida do fato. O conceito depende de uma flag homologada na `DIM_STATUS_PESQUISA` e pertence à camada semântica. `flag_em_aberto`, `flag_conta_como_a_finalizar` e `flag_terminal` ficam anuláveis até a regra dos valores de status ser aprovada; um estado não reconhecido não recebe classificação inventada. A ausência de fechamento observado não equivale a estoque zero.

## C04 — Instrumento de pesquisa

| Item | Contrato |
| :--- | :--- |
| Fato | `FATO_PESQUISA_PERGUNTA` (nome físico único do fato de instrumento) |
| Tipo e grão | Fato sem medidas, uma associação por (`pesquisa_id` de origem, `pergunta_id`) na versão corrente de `questoes` |
| Origem | `ingestao_questoes_atual` e pesquisa corrente quando houver vínculo comprovado |
| Dimensões | `DIM_PESQUISA`, `DIM_PERGUNTA`, `DIM_TEMPO` no papel opcional `sk_data_pesquisa` |
| Medidas armazenadas | Nenhuma |

`qtd_pergunta` é `COUNT(*)` das associações distintas no recorte, não uma coluna constante. `qtd_alternativas` é atributo de `DIM_PERGUNTA`, não medida do fato. `qtd_linhas_matriz` e `qtd_colunas_matriz` não têm medida nem regra de cálculo aprovada e não entram no fato; as listas `linhas_matriz` e `colunas_matriz` da ingestão permanecem atributos da pergunta quando necessárias. `FATO_INSTRUMENTO` era um nome divergente do diagrama, substituído por `FATO_PESQUISA_PERGUNTA`.

Para `questoes.pesquisa_id` sem pesquisa homônima por ID, uma ligação por título só é válida se o título normalizado tiver correspondência exata e **única** com a pesquisa corrente e a execução registrar método, ID original e alvo. Ambiguidade ou ausência de correspondência não cria pesquisa fictícia: manter chave desconhecida controlada e registrar o órfão na reconciliação. O relato de quatro IDs órfãos e 231 linhas pertence ao snapshot analisado anteriormente; a versão v3 tem outro volume e exige nova apuração. Não associar `respostas.respondent_id` a pessoas ou participações nesta entrega.

## Dimensões e chaves

`DIM_TEMPO`, `DIM_PESQUISA`, `DIM_STATUS_PESQUISA`, `DIM_AREA`, `DIM_TIPO_PESQUISA` e `DIM_PERFIL_PESQUISA` são conformadas entre os cubos citados. `DIM_EMPRESA`, `DIM_PESSOA`, `DIM_PERGUNTA`, `DIM_FAMILIA_PESQUISA`, `DIM_FONTE_DADO` e `DIM_EXECUCAO_CARGA` têm escopo mais restrito. Cada chave substituta precisa de geração determinística a partir da chave durável/valor canônico, com tratamento explícito de ausentes e colisões. Não usar ID de linha de arquivo como identidade de empresa, pessoa ou pesquisa.

FK opcional é `NULL` quando a ausência é estrutural. Vínculo órfão deve usar a política de chave desconhecida documentada pela dimensão e registrar chave original e motivo na reconciliação. O acesso externo nunca inclui e-mail, resposta individual ou atributo que permita reidentificação sem uma regra de publicação homologada.
