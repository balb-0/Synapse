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
| T-CMP-01 | | | | | |
| T-CMP-02 | | | | | |
| T-SEG-01 | | | | | |
| T-SEG-02 | | | | | |
| T-SEG-03 | | | | | |

Divergência é registrada com os dois valores e o recorte — nunca ajustada na
ficha.

## Coerência entre granularidades

Para contagens aditivas em grupos disjuntos, o total agregado deve bater com
a soma dos níveis detalhados no mesmo recorte. Médias, taxas e estoque mensal
não seguem essa regra: para médias e taxas, reconciliar numerador e
denominador antes de recalcular; para estoque, comparar o mesmo snapshot.

| Indicador/visual | Nível agregado (valor) | Recomposição correta no detalhe | Coerente? | Observação |
| :--- | :--- | :--- | :--- | :--- |
| | | | | |

## Tempo de resposta das páginas

Cronometrado pela observadora, do clique até o último visual da página
terminar de renderizar.

| Interação | Página | Tempo observado | Acima de 2 s? | Observação |
| :--- | :--- | :--- | :--- | :--- |
| | | | | |

## Debrief (perguntas fixas, por participante)

| Participante | "O que foi mais difícil?" | "Que número você não confiou?" |
| :--- | :--- | :--- |
| P3 | | |
| P4 | | |

## Síntese de S3–S4

_A preencher após as sessões: precisão (quantos valores conferiram),
coerência entre níveis, recortes enunciados errados, tarefas fora do tempo e
tempo de resposta. Divergências de dado voltam para BI-04/RP-17 e alimentam
o registro de [limitações e propostas](limitacoes-e-propostas.md)._
