# Execução — tarefas de comparação temporal e segmentação simultânea

Registro das sessões que executam o bloco D do
[roteiro](roteiro-execucao.md) (tarefas T-CMP-* e T-SEG-* de
[`tarefas-comparacao-segmentacao.md`](tarefas-comparacao-segmentacao.md)):
sessões **S3** e **S4** da rodada final, conforme a
[preparação](preparacao-sessoes.md). Além das métricas padrão, este bloco
confere **precisão do dado exibido** contra valores de referência, a
**coerência do indicador entre granularidades** e o **tempo de resposta** das
páginas aos filtros.

> **Estado: executada (S3 e S4).** Fichas preenchidas durante as sessões,
> sobre as páginas finais validadas no RP-17. Erro de dado encontrado aqui
> volta para BI-04/RP-17 antes do aceite.

## Identificação da rodada final

| Campo | Valor |
| :--- | :--- |
| Alvo | Páginas finais do RP-17: Produção e Volume; Participação agregada (C02); Estoque, Instrumento e Qualidade |
| Versão do relatório | Tip RP-17 `94e91ef`, pacote SHA-256 `a9b087e5…c358cea` ([preparação, Tabela 3](preparacao-sessoes.md#3-versão-do-relatório-e-geração-usadas)) |
| Geração Parquet | v3 `6b1eaa686aac43b18b6d6545e1c2c5f1`; refresh sem erro e contagens 57/32/0/45 conferidas com o manifesto antes de cada sessão |
| Fonte dos valores de referência | [`valores-referencia-v3.md`](evidencias/valores-referencia-v3.md), gerado por [`consultas-referencia.sql`](evidencias/consultas-referencia.sql) sobre a mesma geração |
| Formato | Sessão moderada simulada, com participantes internos exercendo o perfil (roteiro, §1) |
| Datas das sessões | S3 e S4 em 06/10/2026 |
| Moderadora / Observador | Anna / integrante do grupo sem papel de participante |

## Rodada 0 — validação com o parceiro (sprint review)

| Campo | Valor |
| :--- | :--- |
| Data | 25/09/2026, sprint review da Sprint 4 |
| Participante | Representante do parceiro (Sindusfarma) |
| Alvo | Telas Power BI de Operação (RP-03) e Participação/Benchmark Externo (RP-04) |
| Formato | Demonstração conduzida pelo grupo, com feedback verbal do parceiro |
| Ressalva declarada | O grupo informou explicitamente que os dados exibidos eram sintéticos (mockados) |

Registro de validação com o usuário real, complementar às sessões moderadas.
Os dois achados desta rodada são exatamente da natureza que as tarefas de
comparação temporal existem para capturar — semântica de tempo e relevância
das medidas de ciclo:

### Achados sobre medidas e semântica temporal

1. **Ciclo em dias úteis, não em dias corridos.** A tela exibe "Ciclo Médio
   em Dias Corridos"; o parceiro pediu a contagem em **dias úteis**, que é
   como a operação da Central raciocina prazo. Implicação técnica real: a
   medida de tempo de ciclo precisa de um calendário com dias úteis na
   dimensão de tempo (ou regra equivalente no modelo), e o rótulo do visual
   deve declarar a unidade — mesma regra de temporalidade rotulada do RF03.
2. **Métrica principal da tela interna.** Para o parceiro, o cartão de
   destaque da tela de Produção e Volume deveria ser o **tempo médio de
   duração da pesquisa**, não a taxa de finalização — é o número que ele
   acompanha primeiro. Proposta: reordenar os cartões promovendo o ciclo
   médio (em dias úteis) à posição principal.

### Encaminhamentos (propostas, não decisões)

- Ajustar a medida de ciclo para dias úteis exige regra de calendário
  aprovada — encaminhado ao modelo semântico (medidas de tempo) e às telas.
- A troca da métrica principal é ajuste de composição da tela (RP), sem
  mudança de modelo.
- Ambos entram como insumo do registro de limitações e propostas
  ([`limitacoes-e-propostas.md`](limitacoes-e-propostas.md)).

## Ficha S3 — P3 (UC03, gestor)

Colunas com o mesmo significado da
[ficha de navegação](execucao-navegacao-detalhamento.md#como-preencher-as-fichas).

| Tarefa | Conclusão | Tempo | Aceitável? | Desvios | Erros observados | Recorte enunciado corretamente? | Discrepância |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| T-NAV-01 | sim | 01:05 | sim | 0 | Procurou a taxa de finalização vista na Rodada 0 antes de ler o gráfico de status | sim — "portfólio inteiro" | não (366 e 332) |
| T-CMP-01 | assist. | 05:20 | não | 3 — abriu o slicer Ano (só "(Em branco)"), selecionou essa opção, voltou à Produção e Volume procurando um ano e retornou | Perguntou à moderadora se "o ano deveria aparecer ali"; concluiu que o filtro estava com defeito antes de associar o vazio à falta do mês de resposta | parcial — disse "não dá para comparar", mas sem nomear o marco (mês de resposta) | não (17.740 com e sem "(Em branco)") |
| T-CMP-02 | não | 02:10 | sim | 1 — passou o mouse sobre a barra para ler a dica | Apontou "(Em branco)" como o mês de pico, com 17.740 participações | não — leu a categoria sem mês como um mês | de leitura |
| T-SEG-01 | sim | 02:05 | sim | 0 | Nenhum | sim — "sindical trabalhista e rh, pesquisa fixa anual, todos os status, sem período" | não (44) |

Think-aloud e observações:

- "Na demonstração tinha taxa de finalização e dava para ver por empresa;
  agora não aparece." (T-NAV-01)
- "Vinte e oito dias corridos. Para a diretoria eu preciso disso em dias
  úteis." (T-NAV-01)
- "O filtro de ano só tem 'em branco'. Os dados não têm ano ou o filtro
  quebrou?" (T-CMP-01)
- "Se eu não consigo comparar com o ano passado, essa tela não responde a
  pergunta que a diretoria mais faz." (T-CMP-01)
- "Um mês só, o 'em branco', com tudo." (T-CMP-02)
- "Na produção não tem data nenhuma; não sei quando essas 366 pesquisas
  foram pedidas." (T-SEG-01)

## Ficha S4 — P4 (UC01, analista da Central)

| Tarefa | Conclusão | Tempo | Aceitável? | Desvios | Erros observados | Recorte enunciado corretamente? | Discrepância |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| T-SEG-02 | assist. | 06:10 | não | 3 — na terceira página, reaplicou a Área; selecionou também o Status na faixa lateral esperando que o gráfico de perguntas mudasse; percorreu as tabelas de qualidade | Percebeu que a Área não acompanhou a navegação (sucesso parcial); perguntou se o Status "vale para as perguntas" | parcial — após a ajuda: "só a área vale aqui; tipo e status não chegam nas perguntas" | não (37 em C01; 400 em C04 para a área) |
| T-SEG-03 | sim | 03:20 | sim | 1 — antes de remover um filtro, clicou de novo no slicer Status achando que a seleção não tinha sido aplicada | Disse "deu erro?" ao ver os cartões em branco; corrigiu sozinho ao remover o Status | sim — "sindical, pesquisa fixa anual, em tabulação: nenhuma; sem o status, 44" | não (vazio; 44) |

Think-aloud e observações:

- "O filtro de área sumiu quando troquei de página; ainda bem que olhei."
  (T-SEG-02)
- "Mudei o status aqui e o gráfico de perguntas não mexeu. O status não vale
  para isso?" (T-SEG-02)
- "`multipla_escolha`, `matriz_avaliacao`... parece nome de campo de banco."
  (T-SEG-02)
- "Os cartões ficaram em branco; na hora achei que tinha dado erro. Não
  aparece nenhuma mensagem de 'sem resultado'." (T-SEG-03)
- "O estoque está vazio em qualquer filtro que eu escolho." (T-SEG-02,
  comentário sobre a seção de estoque)

## Precisão: valor exibido × valor de referência

Preenchida pela moderadora imediatamente após cada tarefa, com o mesmo
recorte aplicado na página e o valor de
[`valores-referencia-v3.md`](evidencias/valores-referencia-v3.md):

| Tarefa | Recorte usado (filtros e período) | Valor exibido | Valor de referência | Confere? | Observação |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T-NAV-01 (S3) | nenhum | 366; finalizada 332 | R-NAV-01: 366; 332 | sim | — |
| T-CMP-01 | Ano = "(Em branco)" (única opção) | 17.740 | R-CMP-01: nenhum ano observado; 17.740 sem mês | sim | Valor certo; a comparação pedida é `sem dado` porque `mes_resposta` está vazio nas 32 linhas |
| T-CMP-02 | nenhum | uma barra "(Em branco)" com 17.740 | R-CMP-02: uma categoria sem mês, 17.740 | sim | O gráfico mostra o vazio como categoria, sem aviso de mês indisponível |
| T-SEG-01 | Área = sindical trabalhista e rh; Tipo = pesquisa fixa anual | 44 | R-SEG-01: 44 | sim | — |
| T-SEG-02 | C01: Área = assuntos regulatórios; Tipo = solicitação de associado; Status = finalizada. C04: Área reaplicada | 37; múltipla escolha 400 | R-SEG-02: 37; R-DET-03 área: 400 | sim | Tipo de pesquisa e Status não filtram C04 (sem relacionamento, por desenho) |
| T-SEG-03 | + Status = em tabulação; depois sem Status | cartões em branco; 44 | R-SEG-03: 0 linhas; 44 | sim | Vazio correto, sem mensagem de recorte vazio |

**Resultado:** 6 de 6 valores conferem com a referência no recorte aplicado
— nenhuma discrepância de dado. Somadas às 11 conferências de S1–S2
([ficha de navegação](execucao-navegacao-detalhamento.md#conferência-dos-valores-exibidos)),
a rodada final conferiu 17 de 17 valores.

Divergência é registrada com os dois valores e o recorte — nunca ajustada na
ficha.

## Coerência entre granularidades

Para contagens aditivas em grupos disjuntos, o total agregado deve bater com
a soma dos níveis detalhados no mesmo recorte. Médias, taxas e estoque mensal
não seguem essa regra: para médias e taxas, reconciliar numerador e
denominador antes de recalcular; para estoque, comparar o mesmo snapshot.

| Indicador/visual | Nível agregado (valor) | Recomposição correta no detalhe | Coerente? | Observação |
| :--- | :--- | :--- | :--- | :--- |
| Pesquisas no recorte × Pesquisas por Status | 366 | soma das 7 barras de status = 366 | sim | Contagem aditiva em grupos disjuntos |
| Pesquisas no recorte × Volume por Área | 366 | soma das 13 barras de área = 366 | sim | — |
| Média de ciclo total (cartão) | 28,6 dias | (28,7 × 329 + 19,0 × 2) / 331 = 28,6, pela base válida de cada status | sim | A média simples das médias por status daria 23,8; o modelo usa `DIVIDE(soma, base)` e não a média das médias |
| Média de coleta (cartão) × Tempo por Etapa e Tipo | 13,9 dias | Σ soma de dias / Σ base dos 8 tipos = 13,9 | sim | A média simples dos 8 tipos seria 14,2 |
| Participações (cartão) × Participações por área | 17.740 | soma das 12 áreas = 17.740 | sim | — |
| Participações (cartão) × Participações por mês | 17.740 | uma única categoria sem mês = 17.740 | sim | Coerente, mas não há níveis temporais para descer |
| Associações pesquisa-pergunta × Perguntas por tipo | 3.186 | soma dos 5 tipos = 3.186; na área assuntos regulatórios, 682 = 400 + 200 + 43 + 38 + 1 | sim | — |
| Completude aplicável (cartão) × Completude por tabela e campo | 71,4% | Σ preenchidas / Σ linhas dos 64 campos = 71,4% | sim | A média simples dos percentuais seria 84,0%; o cartão pondera pelo volume de linhas |
| Estoque no último fechamento × estoque mensal | sem valor | nenhum fechamento observado em C03 | sim | Semiaditividade preservada (nada é somado entre meses); falta exibir o motivo |

Nenhuma incoerência entre níveis. As medidas não aditivas recompõem pelo
numerador e denominador, como exige a
[regra estatística das medidas](../regras-estatisticas-medidas.md).

## Tempo de resposta das páginas

Cronometrado pela observadora, do clique até o último visual da página
terminar de renderizar.

| Interação | Página | Tempo observado | Acima de 2 s? | Observação |
| :--- | :--- | :--- | :--- | :--- |
| Selecionar Área | Produção e Volume | 0,4 s | não | 6 visuais de dados atualizados |
| Selecionar Tipo com Área ativa | Produção e Volume | 0,3 s | não | — |
| Seleção cruzada na barra "finalizada" | Produção e Volume | 0,3 s | não | Destaca os demais visuais da página |
| Trocar para Participação agregada | — | 0,8 s | não | A página tem 3 visuais posicionados fora da área visível (1 × 1 px), que também consultam o modelo |
| Selecionar Ano | Participação agregada (C02) | 0,3 s | não | Só a opção "(Em branco)" |
| Trocar para Estoque, Instrumento e Qualidade | — | 1,1 s | não | Página com mais visuais de dados (9) |
| Selecionar Status | Estoque, Instrumento e Qualidade | 0,4 s | não | Só a seção de estoque responde |

Nenhuma interação passou de 2 s. O volume publicado é pequeno (57, 32, 0 e 45
linhas nos cubos), então o tempo de resposta não limita o uso nesta geração.
Os três visuais fora da área visível na página C02 (`v2_area`, `v2_detail`,
`v2_time`) não têm efeito perceptível no tempo, mas consultam o modelo sem
serem vistos e recebem foco ao navegar com Tab, o que atrapalha a leitura
por teclado.

## Debrief (perguntas fixas, por participante)

| Participante | "O que foi mais difícil?" | "Que número você não confiou?" |
| :--- | :--- | :--- |
| P3 | "Comparar com o ano anterior: o filtro de ano não tem nenhum ano." | "O gráfico por mês com uma barra 'em branco' — não sei a que período aquilo se refere." |
| P4 | "Saber quais filtros valem para cada parte da terceira página." | "O estoque, que fica vazio em qualquer filtro sem explicar por quê." |

## Encaminhamentos para RP-17 e BI-04

Nenhum valor exibido diverge da referência, então nenhuma correção de
**cálculo** volta para BI-04 antes do aceite. Os itens abaixo são falhas de
**apresentação de estado** ou de **dado de origem** que impediram ou
distorceram tarefas; foram encaminhados aos responsáveis do relatório e do
modelo, com a correção proposta.

| ID | Achado | Natureza | Destino | Correção proposta | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| E1 | Texto fixo "REGISTROS OBSERVADOS · DADOS SIMULADOS" no topo da página C02, exibido também com a geração real v3 | Apresentação; afeta a confiança nos números | RP-17 (visual `v2_status`) | Retirar o texto fixo ou substituí-lo por uma medida com a geração e o `load_reference` carregados | Encaminhado |
| E2 | Estoque no último fechamento em branco, sem motivo, quando C03 não tem fechamento observado | Apresentação de estado `sem dado` | RP-17 (visual `qkpiestoque00001`) e BI-04 | Exibir a medida existente `Estado do Estoque` no cartão ou como subtítulo ("Indisponível: a geração publicada não contém linha C03…") | Encaminhado |
| E3 | `mes_resposta` vazio nas 32 linhas de C02; `DIM_TEMPO` fica só com "(Em branco)", e o slicer Ano e o gráfico mensal não têm meses | Dado de origem/publicação; impeditivo para T-CMP-01 e T-CMP-02 | CB (carga e publicação) e BI-04 | Investigar a data de resposta na origem (a tabela de qualidade mostra `respondentes.hora_inicio` com 0% de completude); até lá, trocar a barra em branco por aviso "mês de resposta indisponível nesta geração" e ocultar o slicer Ano quando ele só tiver vazio | Encaminhado; impeditivo |
| E4 | Média de minutos de preenchimento em branco (base 0), sem motivo | Apresentação de estado `sem dado` | BI-04 / RP-17 (visual `v2_kpi3`) | Medida-texto de estado no mesmo padrão de `Estado do Estoque` | Encaminhado |

## Síntese de S3–S4

<div align="center">
<sub>Tabela 1 - Resultado por sessão (S3–S4)</sub><br>

| Sessão | Tarefas | Sim | Com assistência | Não | Acima do tempo | Desvios | Recorte enunciado corretamente |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| S3 | 4 | 2 | 1 | 1 | 1 | 4 | 2 de 4 (1 parcial, 1 não) |
| S4 | 2 | 1 | 1 | 0 | 1 | 4 | 1 de 2 (1 parcial) |
| **Total** | **6** | **3 (50%)** | **2 (33%)** | **1 (17%)** | **2 (33%)** | **8** | **3 de 6** |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

- **Precisão:** 6 de 6 valores conferidos (17 de 17 na rodada inteira);
  nenhuma discrepância de dado.
- **Coerência entre níveis:** 9 de 9 verificações coerentes; médias e
  completude recompõem pelo numerador e denominador.
- **Tempo de resposta:** todas as interações abaixo de 2 s.
- **Comparação temporal:** as duas tarefas T-CMP falharam ou precisaram de
  ajuda pelo mesmo motivo (E3). Sem mês de resposta, a pergunta "cresceu em
  relação ao período anterior?" não tem resposta em nenhuma página, e o
  relatório não explica isso.
- **Segmentação simultânea:** filtros em uma mesma página foram bem
  compreendidos (T-SEG-01 e T-SEG-03); o problema está entre páginas e
  entre seções da terceira página, onde não fica claro qual filtro vale
  para qual visual.

Os achados e encaminhamentos alimentam o registro de
[limitações e propostas](limitacoes-e-propostas.md).
