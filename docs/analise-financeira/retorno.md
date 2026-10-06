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

## Sensibilidade e fontes para auditoria

Mantendo 4 horas/mês de retrabalho e erros evitados e 4 horas liberadas por relatório, com R$ 139,77289/h, o piloto precisaria de **8 relatórios/mês** para cobrir a operação e **16 relatórios/mês** para recuperar também o investimento em 12 meses. A produção precisaria de **28** e **39 relatórios/mês**, respectivamente. A fórmula antes do arredondamento para cima é `N = (custo mensal + investimento/12 − 4×tarifa_hora) ÷ (4×tarifa_hora)`; para apenas cobrir operação, usar investimento igual a zero. Esses volumes só são úteis se o tempo liberado por relatório for confirmado.

Fontes consultadas em 06/10/2026:

- [SGD/MGI, Portaria nº 750/2023 consolidada, Anexo II](https://www.gov.br/governodigital/pt-br/contratacoes-de-tic/legislacao/modelo-de-contratacao-de-servicos-de-desenvolvimento-manutencao-e-sustentacao-de-software/portaria-sgd-mgi-no-750-de-20-de-marco-de-2023): salário e fator-k de referência; não são salários observados no parceiro.
- [Banco Central, PTAX de 05/10/2026](https://ptax.bcb.gov.br/ptax_internet/consultarUltimaCotacaoDolar.do): conversão de referência, sujeita a spread e tributos.
- [Microsoft, preços do Power BI no Brasil](https://www.microsoft.com/pt-br/power-platform/products/power-bi/pricing): hipótese de licenças Pro por usuário/mês, sem impostos.
- [AWS Pricing Calculator](https://calculator.aws/) e `docs/estimativa-custos-ambiente.md`: a infraestrutura em USD continua paramétrica até cotação regional.
- `docs/projeto.md` e `docs/matriz-evidencias-problem-canvas.md`: objetivo de reduzir trabalho manual e ausência de linha de base medida.

O retorno deve ser recalculado quando FN-02, FN-03 ou FN-04 forem atualizados. Antes de decisão financeira, colher horas e custos observados, preço contratado, usuários licenciados, rampa de adoção e taxa de desconto aprovada se houver pedido de VPL.
