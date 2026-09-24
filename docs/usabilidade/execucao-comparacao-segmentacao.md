# Execução — tarefas de comparação temporal e segmentação simultânea

Registro das sessões que executam o bloco D do
[roteiro](roteiro-execucao.md) (tarefas T-CMP-* e T-SEG-* de
[`tarefas-comparacao-segmentacao.md`](tarefas-comparacao-segmentacao.md)).
Além das métricas padrão, este bloco confere **precisão do dado exibido**
contra valores de referência e a **coerência do indicador entre
granularidades** — as duas exigências do card.

> **Estado: aguardando execução.** Fichas preenchidas durante as sessões;
> este documento só entra em revisão (MR) com as fichas completas. Alvo:
> telas RP-08; na indisponibilidade, piloto sobre o protótipo D01–D04,
> identificado na ficha.

## Identificação da rodada

| Campo | Valor |
| :--- | :--- |
| Alvo (telas RP-08 ou protótipo/piloto) | _a preencher_ |
| Versão/commit do alvo | _a preencher_ |
| Fonte dos valores de referência | _a preencher_ (ex.: `dados-dashboard.json` da mesma versão, consultas do repositório analítico) |
| Datas das sessões | _a preencher_ |
| Moderador / Observador | _a preencher_ |

## Precisão: valor exibido × valor de referência

Preenchida pelo moderador imediatamente após cada tarefa de comparação, com
o mesmo recorte aplicado na tela:

| Tarefa | Recorte usado (filtros e período) | Valor exibido | Valor de referência | Confere? | Observação |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T-CMP-01 (período A) | | | | | |
| T-CMP-01 (período B) | | | | | |
| T-CMP-02 (mês de pico) | | | | | |
| T-SEG-01 | | | | | |
| T-SEG-02 | | | | | |

Divergência é registrada com os dois valores e o recorte — nunca ajustada na
ficha.

## Coerência entre granularidades

Para os visuais com hierarquia temporal/dimensional: o total do nível mais
agregado deve bater com a soma dos níveis detalhados no mesmo recorte.

| Indicador/visual | Nível agregado (valor) | Soma dos níveis detalhados | Coerente? | Observação |
| :--- | :--- | :--- | :--- | :--- |
| | | | | |

## Ficha S2 — P2 (UC03, gestor): T-CMP-01, T-SEG-01

| Tarefa | Conclusão | Tempo | Aceitável? | Desvios | Erros observados | Recorte enunciado corretamente? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| T-CMP-01 | | | | | | |
| T-SEG-01 | | | | | | |

## Ficha S1 — P1 (UC01): T-CMP-02, T-SEG-03

| Tarefa | Conclusão | Tempo | Aceitável? | Desvios | Erros observados | Recorte enunciado corretamente? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| T-CMP-02 | | | | | | |
| T-SEG-03 | | | | | | |

## Ficha S3 — P3 (UC02): T-SEG-02

| Tarefa | Conclusão | Tempo | Aceitável? | Desvios | Erros observados | Recorte enunciado corretamente? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| T-SEG-02 | | | | | | |

## Síntese da rodada

_A preencher após as sessões: precisão (quantos valores conferiram),
coerência entre níveis, recortes enunciados errados e tarefas fora do tempo.
Divergências de dado alimentam a conferência de valores (RP-11) e o registro
de limitações (US-08)._
