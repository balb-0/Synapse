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
