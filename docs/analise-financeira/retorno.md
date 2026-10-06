# FN-05 — TCO, ROI e payback por cenário

**Data-base:** 06/10/2026. **Moeda:** BRL. **Horizonte:** 12 meses após implantação. **Natureza:** simulação condicionada, sem ganho ou desembolso observado pelo parceiro.

## Entradas e dependências

| Entrada | Piloto | Produção de referência | Origem |
| :--- | ---: | ---: | :--- |
| Investimento inicial (R$) | 49.297,56 | 74.557,27 | FN-02, `docs/analise-financeira/investimento-inicial.md`; horas hipotéticas e tarifa SGD/MGI. |
| Operação mensal (R$) | 4.921,86 | 16.088,45 | FN-03, `docs/analise-financeira/operacao-mensal.md`; infraestrutura, pessoal e Power BI Pro. |
| Benefício cauteloso (R$/mês) | 1.397,73 | 1.397,73 | FN-04, `docs/analise-financeira/beneficios.md`; 10 h/mês de capacidade. |
| Benefício base (R$/mês) | 5.031,82 | 5.031,82 | FN-04; 36 h/mês. |
| Benefício alto (R$/mês) | 14.536,38 | 14.536,38 | FN-04; 104 h/mês. |

Aplicamos o mesmo benefício aos dois ambientes para isolar o efeito do custo. Isso é uma hipótese forte: a produção pode atender mais usuários, mas só pode receber benefício maior após medição de volume e adoção. Os valores exibidos foram arredondados; as contas abaixo usam a precisão interna publicada nas fórmulas de origem.

## TCO de 12 meses

Definição neste documento: `TCO_12 = investimento inicial + 12 × custo operacional mensal`. É custo econômico modelado, não fluxo de caixa contratual. Não inclui desembolso de anos anteriores, impostos, suporte comercial, infraestrutura fora do perímetro, custo de capital nem preço de licença não definida.

| Componente | Piloto (R$) | Produção de referência (R$) |
| :--- | ---: | ---: |
| Investimento inicial | 49.297,56 | 74.557,27 |
| Operação de 12 meses | 59.062,29 | 193.061,37 |
| **TCO modelado de 12 meses** | **108.359,84** | **267.618,63** |

Memória com precisão interna: piloto `49.297,55558 + 12×4.921,857375 = 108.359,84408`; produção `74.557,26545 + 12×16.088,447445 = 267.618,63479`. Arredondamos para centavos somente na apresentação. Se o contrato Power BI Pro exigir pagamento anual antecipado, o calendário de caixa muda, mas a competência econômica acima não deve contar a mesma licença uma segunda vez.

## ROI econômico e payback simples

`saldo_12 = 12 × benefício mensal potencial − TCO_12`; `ROI_12 = saldo_12 ÷ TCO_12 × 100`. Se `benefício mensal > operação mensal`, `payback = investimento inicial ÷ (benefício mensal − operação mensal)` em meses desde o início da operação. Quando o benefício não paga nem a operação, não existe payback neste modelo. A capacidade liberada é tratada como valor econômico **condicional**, não como caixa recebido.

| Ambiente | Benefício | Saldo econômico em 12 meses (R$) | ROI econômico em 12 meses | Payback simples |
| :--- | :--- | ---: | ---: | :--- |
| Piloto | Cauteloso | −91.587,10 | −84,52% | Sem payback: benefício < operação |
| Piloto | Base | −47.977,96 | −44,28% | 448,3 meses; fora do horizonte de 12 meses |
| Piloto | Alto | 66.076,72 | 60,98% | 5,13 meses |
| Produção | Cauteloso | −250.845,89 | −93,73% | Sem payback |
| Produção | Base | −207.236,75 | −77,44% | Sem payback |
| Produção | Alto | −93.182,07 | −34,82% | Sem payback |

Exemplo piloto alto: `12×14.536,38056 − 108.359,84408 = R$ 66.076,72`; `66.076,72264 ÷ 108.359,84408 = 60,98%`; `49.297,55558 ÷ (14.536,38056 − 4.921,857375) = 5,13 meses`. O payback supõe ganho cheio desde o primeiro mês e custo mensal constante. **ROI financeiro baseado em caixa e VPL: indisponíveis**; faltam economia contratual comprovada e taxa de desconto fundamentada. Por isso não publicamos VPL.
