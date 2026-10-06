# Análise financeira da Central de Pesquisas

**Data-base:** 06/10/2026. **Moeda:** BRL. **Natureza:** simulação para decisão; não é orçamento aprovado, cotação, gasto observado nem retorno realizado.

## Resumo executivo

A solução reúne extração das fontes de pesquisa, tratamento, carga em DuckDB, cubos analíticos e relatórios. O objetivo financeiro é comparar o investimento de implantação e a operação com o tempo de trabalho que poderia ser liberado na produção de relatórios e na correção de erros. O projeto não dispõe de uma linha de base medida de horas, retrabalho ou volume mensal de relatórios; por isso, os benefícios e o retorno serão apresentados somente como cenários condicionais.

O custo de infraestrutura já estimado em `docs/estimativa-custos-ambiente.md` é uma projeção em USD, separada de pessoal e de investimento inicial. A análise financeira acrescenta essas parcelas sem transformar projeções em despesas observadas. A decisão de contratar ou ampliar o ambiente depende de medição em piloto e de cotação na região e conta escolhidas.

## Escopo da decisão

| Parcela | Pergunta de decisão | Entrega da Sprint 5 |
| :--- | :--- | :--- |
| Investimento inicial | Quanto custaria implantar e treinar? | FN-02, #336 |
| Operação mensal | Quanto custaria sustentar o ambiente e a equipe? | FN-03, #337 |
| Benefícios | Quantas horas e correções poderiam ser evitadas? | FN-04, #338 |
| Retorno | Em quais condições ROI e payback seriam positivos? | FN-05, #339 |
| Riscos | Que premissas podem invalidar o cálculo? | FN-06, #340 |

Os modelos são complementares. Valores de pessoal entram uma única vez: horas de construção no investimento, horas de sustentação na operação e horas liberadas no benefício, com populações e períodos explícitos.
