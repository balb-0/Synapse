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
