# Execução — tarefas de navegação, filtros e detalhamento

Registro das sessões que executam os blocos A (navegação), B (filtros) e C
(detalhamento) do [roteiro](roteiro-execucao.md): sessões **S1** e **S2** da
rodada final, conforme a [preparação](preparacao-sessoes.md).

> **Estado: executada (S1 e S2).** Fichas preenchidas durante as sessões,
> sobre as páginas finais validadas no RP-17.

## Identificação da rodada final

| Campo | Valor |
| :--- | :--- |
| Alvo | Páginas finais do RP-17: Produção e Volume; Participação agregada (C02); Estoque, Instrumento e Qualidade |
| Versão do relatório | Tip RP-17 `94e91ef`, pacote SHA-256 `a9b087e5…c358cea` ([preparação, Tabela 3](preparacao-sessoes.md#3-versão-do-relatório-e-geração-usadas)) |
| Geração Parquet | v3 `6b1eaa686aac43b18b6d6545e1c2c5f1`; refresh sem erro e contagens 57/32/0/45 conferidas com o manifesto antes de cada sessão |
| Fonte dos valores de referência | [`valores-referencia-v3.md`](evidencias/valores-referencia-v3.md), gerado por [`consultas-referencia.sql`](evidencias/consultas-referencia.sql) sobre a mesma geração |
| Formato | Sessão moderada simulada, com participantes internos exercendo o perfil (roteiro, §1) |
| Datas das sessões | S1 e S2 em 06/10/2026 |
| Moderadora / Observador | Anna / integrante do grupo sem papel de participante |

## Rodada 0 — validação com o parceiro (sprint review)

| Campo | Valor |
| :--- | :--- |
| Data | 25/09/2026, sprint review da Sprint 4 |
| Participante | Representante do parceiro (Sindusfarma) |
| Alvo | Telas Power BI de Operação (RP-03) e Participação/Benchmark Externo (RP-04) |
| Formato | Demonstração conduzida pelo grupo, com feedback verbal do parceiro |
| Ressalva declarada | O grupo informou explicitamente que os dados exibidos eram sintéticos (mockados) |

Esta rodada não segue o protocolo moderado do [roteiro](roteiro-execucao.md)
(não mede tempo, desvio nem conclusão por tarefa) — é registro de validação
com o usuário real, complementar às sessões S1–S4.

### Achados sobre navegação e detalhamento

- **As duas telas foram bem recebidas**, com destaque do parceiro para a de
  Benchmark Externo.
- **Expandir as tabelas agradou**: o parceiro usou e elogiou o detalhamento
  das tabelas (Acompanhamento das pesquisas / Participação por pesquisa) —
  valida o caminho agregado → detalhe que as tarefas T-DET exercitam.
- **A leitura dos insights por tipo funcionou**: o corte por tipo de pesquisa
  (tempo por etapa e tipo) foi compreendido e considerado útil sem precisar
  de explicação adicional.

### Encaminhamentos (propostas, não decisões)

- Nenhum bloqueio de navegação ou de filtro foi apontado nesta rodada; os
  ajustes pedidos pelo parceiro são de **métrica e semântica temporal** e
  estão registrados na ficha de comparação
  ([`execucao-comparacao-segmentacao.md`](execucao-comparacao-segmentacao.md)),
  onde pertencem.

## Como preencher as fichas

- **Conclusão**: sim / assist. (com assistência) / não.
- **Tempo**: mm:ss, do enunciado ao critério de sucesso; **Aceitável?**
  compara com o tempo da tarefa.
- **Desvios**: número de páginas/cliques fora dos passos esperados e
  descrição curta.
- **Recorte interpretado**: o recorte que o participante declarou estar
  vendo, nas palavras dele.
- **Valor exibido × referência**: o número lido na página e o valor do
  recorte em [`valores-referencia-v3.md`](evidencias/valores-referencia-v3.md);
  **Discrepância** = `não`, `de dado` (valores diferentes) ou `de leitura`
  (valor certo, interpretação errada).
- **Justificativa do número** (bloco C): transcrição curta e avaliação
  correta / incompleta / errada.

## Ficha S1 — P1 (UC01, analista da Central)

| Tarefa | Conclusão | Tempo | Aceitável? | Desvios | Erros observados | Recorte interpretado | Valor exibido × referência | Discrepância | Justificativa do número |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| T-NAV-01 | sim | 01:25 | sim | 1 — leu primeiro o cartão "Indicadores principais" e parou nos quatro números antes de ir ao gráfico de status | Perguntou se "Base válida ciclo total" (331) era a quantidade de finalizadas; corrigiu sozinho ao ver 332 no gráfico de status | "Portfólio inteiro, todos os status" | 366 e 332 × 366 e 332 | não | — |
| T-NAV-02 | assist. | 04:50 | não | 2 — clicou no bloco "Central de Pesquisas" da faixa lateral esperando um menu; voltou à primeira página pela aba | Na terceira página, perguntou à moderadora se o cartão de estoque "deveria ter número"; chamou a página de "qualidade", sem citar estoque nem instrumento | "Três telas: produção, participação e qualidade" | estoque vazio × estoque `sem dado` (C03 sem fechamento) | de leitura | — |
| T-FIL-01 | sim | 03:30 | não | 3 — clicou duas vezes no quadro "Ano de edição indisponível" tentando abri-lo; foi à página de participação, abriu o slicer Ano (só "(Em branco)") e voltou | Nenhum ao final | "Área de assuntos regulatórios, em todos os anos — não dá para filtrar período aqui" | 88 × 88 | não | — |
| T-FIL-04 | sim | 01:50 | sim | 0 | Esperou alguns segundos achando que o cartão "ainda estava carregando" antes de concluir | "Inovação com pesquisa fixa anual: não tem nenhuma" | cartões em branco × recorte vazio | não | — |
| T-DET-01 | sim | 02:55 | sim | 2 — clicou com o botão direito em "Volume por Área" procurando "Detalhar" (sem opção de nível seguinte); usou o slicer Tipo depois de selecionar a barra "finalizada" | Perguntou se a média de ciclo em branco nas linhas não finalizadas da tabela era zero | "Finalizadas, e dentro delas solicitação de associado" | 332 e 163 × 332 e 163 | não | Correta: "332 das 366 estão finalizadas; 163 dessas 332 são solicitações de associado" |
| T-DET-05 | sim | 02:10 | sim | 2 — botão direito na linha sem opção de drill-through; procurou um filtro de pesquisa na página de participação e encontrou o aviso de pesquisa individual indisponível | Ao começar, leu "Acompanhamento das Pesquisas" como lista de pesquisas | "Assuntos regulatórios, finalizada, solicitação de associado" | 37 e 30,4 × 37 e 30,4 | não | Correta: "essa linha é um grupo de 37 pesquisas, não dá para abrir uma delas" |

Think-aloud e observações da sessão:

- "Na barra da esquerda, o que é filtro e o que é só aviso? Os quadros têm o
  mesmo tamanho." (T-FIL-01)
- "Cadê o menu? Achei que esse logo levava para as outras telas." (T-NAV-02)
- "Vinte e oito vírgula seis dias corridos... a Central fala em dias úteis."
  (T-NAV-01, cartão "Indicadores principais")
- "Na tela de produção que vi na sprint passada dava para abrir a pesquisa e
  ver o título; aqui a tabela tem o mesmo nome, mas é outra coisa." (T-DET-05)
- "Validação de zero dias para pesquisa fixa anual? Isso não existe." (gráfico
  "Tempo por Etapa e Tipo", comentário espontâneo durante T-DET-01)
- "Esses códigos I05, C02... eu teria que decorar o que são." (T-NAV-02)

## Ficha S2 — P2 (UC02, área técnica e papel de governança)

| Tarefa | Conclusão | Tempo | Aceitável? | Desvios | Erros observados | Recorte interpretado | Valor exibido × referência | Discrepância | Justificativa do número |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| T-FIL-02 | sim | 03:45 | não | 1 — selecionou só "em andamento" e leu 2; ao rever o gráfico de status, acrescentou "aguardando data predefinida" e "em análise da área técnica" | Primeira leitura (2) considerava apenas um dos três status não finalizados do tipo | "Pesquisa fixa anual que ainda não terminou" | 17 × 17 (primeira leitura: 2) | de leitura (corrigida) | — |
| T-FIL-03 | assist. | 01:40 | não | 2 — limpou o slicer Tipo e clicou em um item do Status, deixando outros dois marcados | Leu 27 como "portfólio completo"; ao comparar com o 366 anotado antes, perguntou se havia um botão para limpar tudo | "Tudo de novo" (com Status ainda ativo) | 27 × 366 (após limpar o Status: 366) | de leitura | — |
| T-DET-02 | sim | 03:30 | sim | 2 — procurou um filtro de empresa na faixa lateral e parou no aviso de empresa indisponível; voltou ao gráfico por área | Chamou as 17.740 participações de "pessoas que responderam"; perguntou o que era o "17" do cartão ao lado | "Todas as participações, por área" | 17.740 e 6.507 × 17.740 e 6.507 | de leitura | Incompleta: apontou a área certa (6.507), mas descreveu as participações como pessoas; o rodapé "conta ocorrências, não pessoas" não foi lido |
| T-DET-03 | não | 02:30 | sim | 1 — aplicou Área na primeira página e foi direto ao gráfico "Perguntas por tipo" da terceira | Não verificou o slicer Área na terceira página e leu o total global como sendo da área | "Assuntos regulatórios, por tipo de pergunta" | múltipla escolha 1.551 × 400 (área) | de leitura | Errada: "1.551 perguntas de múltipla escolha em assuntos regulatórios" — o número é do conjunto inteiro |
| T-DET-04 | assist. | 04:40 | não | 2 — selecionou um Status na faixa lateral esperando que as tabelas de qualidade mudassem; percorreu as quatro tabelas antes da de completude | Pediu à moderadora a quantidade de registros, porque a tabela só mostra o percentual; classificou `prorrogada_ate` como falha grave | "Campo prorrogada_ate da tabela pesquisas" | 18,6% × 18,6% (68 de 366 não exibidos) | de leitura | Errada: "faltam 81% das datas de prorrogação" — o campo só existe para pesquisas prorrogadas (ausência permitida) |

Think-aloud e observações:

- "Em andamento é o mesmo que não finalizada? Tem status demais e todos
  parecem a mesma coisa." (T-FIL-02)
- "Não tem um 'limpar filtros'? Vou ter que desmarcar um por um?" (T-FIL-03)
- "Dezessete o quê? Ah, indicadores sem dado... por que isso está em destaque
  numa tela de participação?" (T-DET-02, cartão "Indicadores sem dado")
- "A média de preenchimento está vazia; não sei se é zero ou se não
  carregou." (T-DET-02)
- "Mudei o status e as tabelas de qualidade não mexeram. O filtro está
  funcionando?" (T-DET-04)
- "`multipla_escolha`, `caixas_de_selecao`... isso é nome de coluna, não é?"
  (T-DET-03)

## Conferência dos valores exibidos

Cada valor foi lido na página com o recorte exatamente como estava aplicado
no momento (inclusive quando diferente do recorte pedido) e comparado com a
consulta independente sobre a mesma geração.

| Tarefa | Recorte aplicado na página | Valor exibido | Valor de referência | Confere? | Observação |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T-NAV-01 | nenhum | 366; finalizada 332; base válida 331; média de ciclo 28,6; média de coleta 13,9 | R-NAV-01: 366; 332; 331; 28,6; 13,9 | sim | Base válida (331) e finalizadas (332) diferem por um e foram confundidas na leitura |
| T-NAV-02 | Estoque, Instrumento e Qualidade, sem filtros | estoque em branco; 3.186 associações; completude 71,4% | R-ESTOQUE: 0 linhas; R-DET-03 total 3.186; R-DET-04 71,4% | sim | O branco do estoque é o estado `sem dado` esperado, mas a página não exibe o motivo |
| T-FIL-01 | Área = assuntos regulatórios | 88 | R-FIL-01: 88 | sim | — |
| T-FIL-04 | Área = inovação; Tipo = pesquisa fixa anual | cartões em branco; gráficos vazios | R-FIL-04: 0 linhas | sim | Vazio correto, sem mensagem de recorte vazio |
| T-DET-01 | Status = finalizada; depois Tipo = solicitação de associado | 332; 163 | R-DET-01: 332; 163 | sim | — |
| T-DET-05 | linha assuntos regulatórios × finalizada × solicitação de associado | 37; 30,4 | R-DET-05: 37; 30,4 | sim | — |
| T-FIL-02 | Tipo = pesquisa fixa anual; Status = em andamento | 2 | R-FIL-02 (parcial): em andamento 2 | sim | Recorte aplicado incompleto; após completar os status: 17 × 17 |
| T-FIL-03 | Status = aguardando data predefinida, em andamento, em análise da área técnica | 27 | 19 + 5 + 3 = 27 (distribuição por status, R-DET-01) | sim | Valor certo para o filtro remanescente; sem o filtro: 366 × 366 |
| T-DET-02 | nenhum | 17.740; maior área 6.507; média de preenchimento em branco | R-DET-02: 17.740; 6.507; base de preenchimento 0 | sim | Média em branco é `sem dado` (denominador zero), sem motivo exibido |
| T-DET-03 | Área = assuntos regulatórios na 1ª página; nenhum filtro na 3ª | múltipla escolha 1.551 | R-DET-03 total: 1.551 (área: 400) | sim, para o recorte aplicado | O filtro de Área não acompanhou a navegação; o participante leu o total global como sendo da área |
| T-DET-04 | nenhum | `prorrogada_ate` 18,6% | R-DET-04: 68 de 366, 18,6% | sim | Numerador, denominador e registros afetados (298) não aparecem na tabela |

**Resultado:** 11 de 11 valores conferem com a referência no recorte
efetivamente aplicado — nenhuma discrepância de dado. As seis discrepâncias
das fichas são **de leitura**: o número estava certo, mas o recorte
interpretado (T-FIL-02, depois corrigido; T-FIL-03; T-DET-03), o rótulo
(T-DET-02), a natureza
do nulo (T-DET-04) ou o estado vazio (T-NAV-02) foram lidos de forma errada.

## Debrief (perguntas fixas, por participante)

| Participante | "O que foi mais difícil?" | "Que número você não confiou?" |
| :--- | :--- | :--- |
| P1 | "Saber o que é filtro e o que é aviso na barra da esquerda, e entender se a página de estoque estava vazia ou com erro." | "A validação de 0,0 dia para pesquisa fixa anual e o estoque em branco." |
| P2 | "Perceber que o filtro de área não foi junto para a outra página; e limpar os filtros um a um." | "Os da página de participação: no topo está escrito 'dados simulados', então não sei se aqueles números são reais." |

## Síntese de S1–S2

<div align="center">
<sub>Tabela 1 - Resultado por sessão (S1–S2)</sub><br>

| Sessão | Tarefas | Sim | Com assistência | Não | Acima do tempo | Desvios | Justificativas corretas (bloco C) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| S1 | 6 | 5 | 1 | 0 | 2 | 10 | 2 de 2 |
| S2 | 5 | 2 | 2 | 1 | 3 | 8 | 0 de 3 (1 incompleta, 2 erradas) |
| **Total** | **11** | **7 (64%)** | **3 (27%)** | **1 (9%)** | **5 (45%)** | **18** | **2 de 5** |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

Erros por tipo, a partir das fichas:

| Tipo de erro | Ocorrências | Tarefas |
| :--- | ---: | :--- |
| Estado confundido (vazio, `sem dado`, ausência permitida) | 4 | T-NAV-02, T-FIL-04, T-DET-02 (média em branco), T-DET-04 |
| Recorte não percebido (filtro perdido, remanescente ou incompleto) | 3 | T-DET-03, T-FIL-03, T-FIL-02 |
| Rótulo lido com outro significado | 3 | T-NAV-01 (base válida), T-DET-02 (participações como pessoas), T-DET-05 (título da tabela) |
| Recurso procurado que a página não oferece | 5 | T-FIL-01 (período), T-DET-01 (drill), T-DET-05 (drill-through), T-NAV-02 (menu), T-DET-02 (empresa) |

Leitura da rodada:

- **Precisão sem falha de dado**: os 11 valores conferidos batem com a
  referência no recorte aplicado. Os problemas estão na comunicação do
  recorte e dos estados, não no cálculo.
- **Navegação e filtros simples funcionam**; os desvios se concentram nos
  pontos em que a página **parece** oferecer algo que a publicação não tem
  (avisos no formato de slicer, tabela com nome de lista, ausência de menu).
- **Detalhamento é o bloco mais frágil**: só 2 das 5 justificativas foram
  corretas, e o único "não" da rodada (T-DET-03) é a perda do filtro entre
  páginas, exatamente o erro-alvo da tarefa.
- **Confiança**: dois elementos sem relação com o cálculo — a faixa "dados
  simulados" na página C02 e médias exibidas sem base (0,0 dia de validação
  sobre uma única pesquisa) — foram citados como números "não confiáveis".

Os achados alimentam o registro de
[limitações e propostas](limitacoes-e-propostas.md).
