# FN-06 — Riscos, premissas e consistência financeira

**Revisão em:** 06/10/2026. **Escopo:** FN-01 a FN-05 e `docs/estimativa-custos-ambiente.md`. Valores são cenários em BRL, salvo a estimativa original de infraestrutura em USD. Não há orçamento aprovado, medição de benefício nem ROI de caixa.

## Registro de riscos e mitigação

| Risco | Efeito sobre a estimativa | Mitigação verificável | Responsável pela confirmação |
| :--- | :--- | :--- | :--- |
| Volume de relatórios e horas economizadas não medidos | O benefício de 10, 36 ou 104 h/mês pode não ocorrer. | Medir três meses de relatórios comparáveis antes/depois, com início/fim e classificação de revisão. | Central de Pesquisas e Data Owner. |
| Disponibilidade, formato e atualização das fontes | Falhas e mudanças de schema aumentam implantação, suporte e retrabalho. | Homologar acesso, frequência, contrato e testes de reconciliação por fonte no piloto. | Data Steward e responsáveis pelas fontes. |
| Licenças e direitos de compartilhamento | O número de licenças Power BI e planos necessários pode superar a hipótese. | Inventariar usuários, licenças já existentes e modo de publicação; obter proposta oficial. | TI/Data Custodian e compras. |
| Adoção inferior à hipótese | Horas liberadas não se transformam em capacidade útil ou economia. | Medir uso, treinar usuários, manter rampa mensal e reestimar benefício por adoção efetiva. | Central de Pesquisas. |
| Integração e operação produtiva incompletas | Protótipo ou contrato pode não substituir o fluxo manual. | Executar teste ponta a ponta com dados representativos, aceite do parceiro e registro de falhas. | Equipe técnica e parceiro. |

Riscos de LGPD, disponibilidade operacional e qualidade do indicador também afetam a decisão, mas só entram em dinheiro após haver custo ou exposição mensurável. Não atribuímos uma economia monetária arbitrária a eles.

## Premissas de custo que exigem recotação

| Premissa | Evidência e limite | Gatilho de revisão |
| :--- | :--- | :--- |
| Infraestrutura piloto USD 95,10/mês e produção USD 1.651,00/mês | `docs/estimativa-custos-ambiente.md` é um modelo paramétrico; [AWS EC2](https://aws.amazon.com/pt/ec2/pricing/on-demand/), [EBS](https://aws.amazon.com/pt/ebs/pricing/) e [S3](https://aws.amazon.com/pt/s3/pricing/) dependem de região, uso e configuração. | Escolha de nuvem, região, retenção, capacidade, rede ou compromisso de compra. |
| PTAX venda de R$ 4,9859/USD em 05/10/2026 | [Banco Central](https://ptax.bcb.gov.br/ptax_internet/consultarUltimaCotacaoDolar.do); não é taxa contratada. | Cotação em data de compra e inclusão de spread, tributos e pagamentos em moeda estrangeira. |
| Salário de referência e fator-k | [SGD/MGI, Portaria nº 750/2023 consolidada](https://www.gov.br/governodigital/pt-br/contratacoes-de-tic/legislacao/modelo-de-contratacao-de-servicos-de-desenvolvimento-manutencao-e-sustentacao-de-software/portaria-sgd-mgi-no-750-de-20-de-marco-de-2023); perfis públicos são proxy, não folha do parceiro. | Escopo de função, dedicação, fornecedor ou contrato distintos. |
| Power BI Pro, R$ 80,20/usuário/mês | [Microsoft Brasil](https://www.microsoft.com/pt-br/power-platform/products/power-bi/pricing); pagamento anual, preço sem impostos. | Usuários, licenças preexistentes, forma de compartilhamento ou plano diferente. |
| Elastic Basic autogerenciado sem tarifa de licença | [Tabela de assinaturas Elastic](https://www.elastic.co/subscriptions); operar a pilha tem custo e suporte comercial não está incluído. | Exigência de recurso pago, suporte, hospedagem gerenciada ou mudança de licença. |

Também faltam preço de suporte com SLA, requisitos de disponibilidade, redes, recuperação de desastre, impostos e eventual contrato de dados. Esses itens são **não cotados**, não custo zero. Sua inclusão pode alterar materialmente o TCO e tornar os retornos ainda menores.

## Conferência de totais, unidades e períodos

| Identidade conferida | Piloto | Produção | Resultado |
| :--- | :--- | :--- | :--- |
| Investimento único FN-02 (BRL) | 49.297,56 | 74.557,27 | Horas de construção e treinamento uma vez. |
| Operação FN-03 (BRL/mês) | 4.921,86 | 16.088,45 | Inclui infraestrutura, pessoal e licenças. |
| Operação FN-03 (BRL/12 meses) | 59.062,29 | 193.061,37 | Multiplicação antes de arredondar. |
| TCO FN-05 (BRL/12 meses) | 108.359,84 | 267.618,63 | Investimento único + operação de 12 meses. |
| Benefício alto FN-04 (BRL/mês) | 14.536,38 | 14.536,38 | Valor de 104 h; não é caixa observado. |
| Benefício alto FN-04 (BRL/12 meses) | 174.436,57 | 174.436,57 | Não se soma a outros cenários de benefício. |
| Saldo alto FN-05 (BRL/12 meses) | +66.076,72 | −93.182,07 | Benefício alto anual menos TCO. |

As identidades foram refeitas com valores internos de FN-02 a FN-04, antes do arredondamento de centavos. A produção tem diferença de R$ 0,01 entre soma das linhas exibidas do investimento e total calculado, explicada pelo arredondamento de cada linha. Não há erro de unidade: infraestrutura começa em USD/mês e é convertida uma vez para BRL/mês; horas de trabalho são por mês ou únicas conforme a tabela. Não se multiplica o investimento por 12 nem se soma piloto e produção.

**Dupla contagem evitada:** o fator-k já compõe o custo de pessoal; o custo de VM já contempla CPU e RAM; suporte funcional de BI e atualização estão nas mesmas horas; preparação normal, retrabalho e erro são eventos distintos; a licença Pro aparece apenas na operação. Uma hora liberada só pode ser monetizada como capacidade **ou** caixa evitado com evidência correspondente.
