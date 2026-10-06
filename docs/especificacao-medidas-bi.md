# Especificação das medidas — numerador, denominador, grão e nulos

Cumpre a DX-02: toda medida abaixo tem fórmula rastreável até uma coluna dos
sete arquivos publicados em `docs/acesso-cubos-bi.md` (quatro cubos) e
`src/etl/analytics/publish.py` (três artefatos de qualidade, DX-09), e
declara o que faz com nulo e com duplicata. As medidas seguem
[`docs/indicadores-publicaveis-bi.md`](indicadores-publicaveis-bi.md) (DX-01)
— só é especificada aqui a medida já classificada como calculável ou
parcialmente calculável na camada BI; a medida sem dado disponível não tem
fórmula, só o motivo do bloqueio (já registrado em DX-01, sinalizado em
DX-10).

Convenção: toda razão usa `DIVIDE(numerador, denominador)` em vez de `/`, e
todo relatório que mostrar a razão mostra o denominador ao lado (regra de
DX-03).

## PUB_C01_CICLO — grão publicado: área × status × tipo

| Medida | Numerador | Denominador | Tratamento de nulo | Tratamento de duplicata |
| :-- | :-- | :-- | :-- | :-- |
| Qtd Pesquisas | `SUM(qtd_pesquisas)` | — (contagem, não razão) | Não há nulo possível: cada grupo publicado já é `COUNT(*)` da consulta de origem. | Não aplicável — o arquivo chega pré-agregado por grupo; somar entre grupos é seguro porque área×status×tipo particiona as pesquisas sem sobreposição. |
| Média Dias de Validação/Coleta/Tabulação/Ciclo Total | `SUM(soma_dias_*)` | `SUM(qtd_*_disponivel)` | Pares de data inválidos já ficam fora da soma **e** da contagem na consulta de `publish.py`; a razão nunca precisa filtrar nulo à parte. | Não aplicável, mesmo motivo acima. |
| Taxa de Prorrogação | — | — | Sem fórmula: `flag_prorrogada` não está no arquivo publicado (DX-01, I05). Sinalizada como indisponível pela DX-10. | — |

## PUB_C02_PARTICIPACAO — grão publicado: área × tipo × mês da resposta

| Medida | Numerador | Denominador | Tratamento de nulo | Tratamento de duplicata |
| :-- | :-- | :-- | :-- | :-- |
| Qtd Participações | `SUM(qtd_participacoes)` | — | Sem nulo possível. **Nomear a medida deixando explícito que é participação, não pessoa** — o mesmo cliente pode aparecer em mais de uma linha. | A deduplicação de reprocessamento (mesmo arquivo carregado de novo) já ocorreu na carga, pela identidade física (`source_checksum`, `source_offset`); o Parquet não republica o mesmo registro duas vezes. |
| Média Minutos de Preenchimento | `SUM(soma_minutos_preenchimento)` | `SUM(qtd_preenchimento_disponivel)` | Participações sem par válido de hora início/fim já ficam fora de soma e contagem na origem. | Idem acima. |
| Representatividade | — | — | Sem fórmula: `pct_mercado_na_participacao` não é publicada (DX-01, I09). Sinalizada como indisponível pela DX-10. | — |

## PUB_C03_PIPELINE_MENSAL — grão publicado: mês de fechamento × status × área × tipo × perfil

| Medida | Numerador | Denominador | Tratamento de nulo | Tratamento de duplicata |
| :-- | :-- | :-- | :-- | :-- |
| Estoque no Último Mês Observado | `SUM(qtd_pesquisas_no_status)` no mês de referência | — (contagem, não razão) | A data de referência é a maior `data_fim_mes` no contexto de `DIM_TEMPO`; os filtros categóricos das dimensões e das colunas C03 são removidos só para encontrá-la. Assim, os níveis brutos `PUB_C03_PIPELINE_MENSAL[area]` → `[tipo]` → `[perfil]` e o filtro de área não fazem cada grupo voltar a um fechamento antigo. Para recuperar o estoque, a medida remove `DIM_TEMPO` e filtra diretamente `PUB_C03_PIPELINE_MENSAL[data_fim_mes]` pela data de referência; os filtros de categoria continuam ativos. Se outro grupo tem linha no fechamento global e o pacote está reconciliado, um grupo sem linha nesse fechamento vale `0`; sem qualquer linha C03 no tempo selecionado, data, estoque e estado ficam indisponíveis. | Estoque é semiaditivo: somar entre grupos do mesmo mês é válido; somar snapshots de meses distintos conta a mesma pesquisa mais de uma vez. Não aplicar média simples ou ponderada. |
| Qtd Entradas / Qtd Saídas no Mês | `SUM(qtd_entradas_no_mes)` / `SUM(qtd_saidas_no_mes)` | — | As medidas numéricas retornam `BLANK()` enquanto as colunas publicadas forem `NULL`. Medidas separadas de estado mostram “histórico de transições de status não publicado” quando há fechamento C03 global no tempo selecionado; se não houver nenhuma linha C03 nesse tempo, informam essa indisponibilidade. Quando a origem publicar transições, as somas passam a usar os valores disponíveis. Não combinar número e texto na mesma medida. | Entradas e saídas são fluxos aditivos no período selecionado; o contrato atual não publica histórico de transições. |

**Limite de publicação do C03:** o ETL registra um fechamento observado mesmo quando o estoque total é zero, mas a geração BI publica apenas `FATO_PIPELINE_MENSAL`. Um fechamento vazio, portanto, não gera linha Parquet e fica indistinguível de um mês sem fechamento. As medidas atuais retornam estado indisponível nos dois casos; não criam linha sentinela nem convertem ausência em zero. A disponibilidade de um fechamento com estoque zero só poderá ser sinalizada após o contrato de publicação incluir o marcador correspondente, com mudança coordenada na carga/publicador/modelo. Até lá, esse cenário impede aceitar a distinção zero versus não observado no Power BI Desktop.

## PUB_C04_INSTRUMENTO — grão publicado: área × tipo de pergunta

| Medida | Numerador | Denominador | Tratamento de nulo | Tratamento de duplicata |
| :-- | :-- | :-- | :-- | :-- |
| Qtd Perguntas | `SUM(qtd_perguntas)` | — (é `COUNT(*)` das associações pesquisa-pergunta na origem, DX-02 exige declarar isso: não é contagem de respostas) | Sem nulo possível. | Não aplicável — associação pesquisa-pergunta é a chave de negócio de `questoes`, já corrente na origem (`ingestao_questoes_atual`). |

Regra de denominador por tipo de questão (I12/I14 em `dmc.md`): como
`respostas` não é publicada nesta versão (DX-01), a distribuição de respostas
por alternativa não tem denominador disponível na camada BI; só a contagem de
perguntas por tipo é publicável.

## Qualidade do dado (DX-09) — três grãos publicados

| Medida | Numerador | Denominador | Grão publicado | Tratamento de nulo | Tratamento de duplicata |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Completude por Campo (I16) | `SUM(qtd_preenchidas)` de `PUB_QUALIDADE_CAMPO` | `SUM(qtd_linhas)` do mesmo arquivo | Uma linha por (tabela, campo) | `qtd_preenchidas` já é `COUNT(coluna)`, que ignora nulo por definição SQL; nenhum tratamento adicional necessário. | Não aplicável — cada (tabela, campo) é uma linha única no arquivo. |
| Integridade Referencial (I18) | `SUM(qtd_chaves_correspondentes)` de `PUB_QUALIDADE_RELACAO` | `SUM(qtd_chaves_informadas)` do mesmo arquivo | Uma linha por relação (ex.: `respondentes.empresa_id`) | Chave estrangeira nula é excluída do denominador na própria consulta de origem (`WHERE ... IS NOT NULL`); FK nula não conta como órfã nem como correspondente. | Não aplicável, mesmo motivo. |
| Taxa de Duplicidade (I17) | `SUM(qtd_linhas) - SUM(qtd_chaves_distintas)` de `PUB_QUALIDADE_DUPLICIDADE` | `SUM(qtd_linhas)` do mesmo arquivo | Uma linha por tabela de origem com chave de negócio | Não se aplica (a medida mede duplicata, não trata nulo de chave). | É a própria medida: mede quanto do total é duplicata de chave de negócio na tabela de ingestão bruta, antes da view "_atual" escolher a versão corrente. |

## Nota sobre proibição de contar linha como respondente

Nenhuma medida desta especificação soma linha do Parquet como se fosse
pessoa: `qtd_participacoes` é ocorrência, `qtd_pesquisas` já é `COUNT(*)`
sobre pesquisa (não sobre respondente), e nenhuma medida de qualidade conta
`ingestao_respondentes`/`ingestao_respostas` como proxy de contagem de
pessoa. Ver a regra completa em `docs/regras-estatisticas-medidas.md` (DX-03).
