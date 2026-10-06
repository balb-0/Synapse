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
