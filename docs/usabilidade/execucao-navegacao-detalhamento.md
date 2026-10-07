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
| T-FIL-02 | | | | | | | | | — |
| T-FIL-03 | | | | | | | | | — |
| T-DET-02 | | | | | | | | | |
| T-DET-03 | | | | | | | | | |
| T-DET-04 | | | | | | | | | |

Think-aloud e observações: _a preencher_

## Conferência dos valores exibidos

| Tarefa | Recorte | Valor exibido | Valor de referência | Confere? | Observação |
| :--- | :--- | :--- | :--- | :--- | :--- |
| | | | | | |

## Debrief (perguntas fixas, por participante)

| Participante | "O que foi mais difícil?" | "Que número você não confiou?" |
| :--- | :--- | :--- |
| P1 | | |
| P2 | | |

## Síntese de S1–S2

_A preencher após as sessões: taxa de conclusão por bloco, tarefas fora do
tempo aceitável, desvios recorrentes e erros por tipo (estado confundido,
recorte não percebido, número sem justificativa). Alimenta o registro de
[limitações e propostas](limitacoes-e-propostas.md)._
