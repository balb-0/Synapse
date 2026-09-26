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
| Alvo | Telas Power BI de Operação (RP-03) e Participação (RP-04) na `develop`; Resultados/Qualidade pendentes |
| Versão/commit do alvo | _a preencher_ |
| Fonte dos valores de referência | _a preencher_ (ex.: `dados-dashboard.json` da mesma versão, consultas do repositório analítico) |
| Datas das sessões | _a preencher_ |
| Moderador / Observador | _a preencher_ |

## Rodada 0 — validação com o parceiro (sprint review)

| Campo | Valor |
| :--- | :--- |
| Data | 25/09/2026, sprint review da Sprint 4 |
| Participante | Representante do parceiro (Sindusfarma) |
| Alvo | Telas Power BI de Operação (RP-03) e Participação/Benchmark Externo (RP-04) |
| Formato | Demonstração conduzida pelo grupo, com feedback verbal do parceiro |
| Ressalva declarada | O grupo informou explicitamente que os dados exibidos eram sintéticos (mockados) |

Registro de validação com o usuário real, complementar às sessões moderadas
(pendentes). Os dois achados desta rodada são exatamente da natureza que as
tarefas de comparação temporal existem para capturar — semântica de tempo e
relevância das medidas de ciclo:

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
  ([`limitacoes-e-propostas.md`](limitacoes-e-propostas.md)) e do backlog da
  próxima sprint.

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

Para contagens aditivas em grupos disjuntos, o total agregado deve bater com
a soma dos níveis detalhados no mesmo recorte. Médias, taxas e estoque mensal
não seguem essa regra: para médias e taxas, reconciliar numerador e
denominador antes de recalcular; para estoque, comparar o mesmo snapshot.

| Indicador/visual | Nível agregado (valor) | Recomposição correta no detalhe | Coerente? | Observação |
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
