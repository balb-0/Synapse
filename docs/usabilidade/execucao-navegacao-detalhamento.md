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
| T-NAV-01 | | | | | | | | | — |
| T-NAV-02 | | | | | | | | | — |
| T-FIL-01 | | | | | | | | | — |
| T-FIL-04 | | | | | | | | | — |
| T-DET-01 | | | | | | | | | |
| T-DET-05 | | | | | | | | | |

Think-aloud e observações da sessão: _a preencher_

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
