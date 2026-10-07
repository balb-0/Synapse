# FN-03 — Operação mensal e pessoal

**Data-base:** 06/10/2026. **Moeda:** BRL. **Natureza:** custo mensal projetado; não é despesa observada. Piloto e produção são alternativas, não ambientes cumulativos.

## Perímetro e conversão

A [estimativa versionada de infraestrutura](../estimativa-custos-ambiente.md) apresenta USD 95,10/mês no piloto e USD 1.651,00/mês na produção de referência. Multiplicamos pela [PTAX venda de 05/10/2026](https://ptax.bcb.gov.br/ptax_internet/consultarUltimaCotacaoDolar.do), R$ 4,9859/USD: **R$ 474,16/mês** e **R$ 8.231,72/mês**. Os valores em USD são tarifas de planejamento, sem cotação regional; a PTAX não inclui spread, impostos ou taxas de contratação.

Essa parcela já agrega VMs, armazenamento em bloco e objeto, backup simplificado e saída de dados. Não adicionamos CPU, RAM, MinIO, DuckDB ou transferência novamente. Uma nova arquitetura exige refazer a estimativa na [AWS Pricing Calculator](https://calculator.aws/) com região, instâncias, uso e impostos definidos.

O custo de pessoal usa `salário × fator-k ÷ 160 h` com os perfis DESENV-02, ABI-02, ANR-02 e ATQ-02 do [Anexo II vigente da Portaria SGD/MGI nº 750/2023](https://www.gov.br/governodigital/pt-br/contratacoes-de-tic/legislacao/modelo-de-contratacao-de-servicos-de-desenvolvimento-manutencao-e-sustentacao-de-software/portaria-sgd-mgi-no-750-de-20-de-marco-de-2023). A alocação é fracionária; não implica contratar quatro pessoas em tempo integral.

## Horas mensais de sustentação

| Atividade | Perfil | Piloto (h/mês) | Produção (h/mês) | Limite da contagem |
| :--- | :--- | ---: | ---: | :--- |
| Hospedagem, monitoramento técnico, atualização e restauração | Desenvolvedor pleno | 16 | 24 | Inclui manutenção de código e configuração; não criar uma segunda linha de manutenção para as mesmas horas. |
| Atualização de relatórios, modelo e acompanhamento de usuários | Analista de BI pleno | 8 | 16 | Inclui pequenas correções de visual e suporte funcional de BI. |
| Atendimento, triagem e priorização de pedidos | Analista de negócios pleno | 4 | 8 | Não inclui as horas dos usuários para produzir relatórios manuais. |
| Conferência de qualidade e reconciliação | Analista de testes pleno | 4 | 8 | Não repetir como custo de erro na mesma operação. |
| **Horas totais** | | **32** | **56** | Trabalho recorrente, distinto das horas de implantação de FN-02. |

Essas alocações são hipóteses a medir durante o piloto. Trabalho de plantão 24×7, suporte contratado com SLA, integração nova e correção estrutural relevante não estão precificados. A demanda superior à capacidade prevista exige revisão de horas, não absorção gratuita.

## Custos mensais por cenário

Para compartilhar reports, modelamos **2 licenças Power BI Pro no piloto** e **5 na produção**, a [R$ 80,20 por usuário/mês, pago anualmente, sem impostos](https://www.microsoft.com/pt-br/power-platform/products/power-bi/pricing). A quantidade de usuários é hipótese. Se o parceiro já possui Microsoft 365/Office 365 E5 elegível, o desembolso incremental pode ser menor. A autoria local em Power BI Desktop não requer a licença Pro.

| Componente | Fórmula | Piloto (R$/mês) | Produção (R$/mês) |
| :--- | :--- | ---: | ---: |
| Infraestrutura | USD 95,10 ou 1.651,00 × 4,9859 | 474,16 | 8.231,72 |
| Hospedagem, manutenção e atualizações | 16 ou 24 h × 139,858753125 | 2.237,74 | 3.356,61 |
| BI e suporte funcional | 8 ou 16 h × 139,77289 | 1.118,18 | 2.236,37 |
| Triagem e apoio ao usuário | 4 ou 8 h × 121,9041525 | 487,62 | 975,23 |
| Qualidade e reconciliação | 4 ou 8 h × 110,93962625 | 443,76 | 887,52 |
| Power BI Pro | 2 ou 5 usuários × 80,20 | 160,40 | 401,00 |
| **Total mensal projetado** | Soma com precisão integral, arredondada ao final | **4.921,86** | **16.088,45** |
| **Total em 12 meses** | Total mensal sem arredondamento × 12 | **59.062,29** | **193.061,37** |

O desembolso de licença pode ocorrer antecipadamente pelo compromisso anual. A tabela expressa competência econômica mensal; FN-05 deve explicitar o fluxo de caixa quando o plano de compra for conhecido.

## Conferência e limites

Reprodução do piloto: `95,10×4,9859 + 16×(11023,35×2,03÷160) + 8×(11071,12×2,02÷160) + 4×(9561,11×2,04÷160) + 4×(8616,67×2,06÷160) + 2×80,20 = R$ 4.921,86/mês`. Na produção, substituir por `1651, 24, 16, 8, 8, 5`, respectivamente, resulta em **R$ 16.088,45/mês**. Usar precisão integral antes de arredondar.

| Item a validar | Consequência se mudar |
| :--- | :--- |
| Região, topologia, retenção, volume e período ligado | Recalcular USD da infraestrutura; sete VMs contínuas dominam o cenário de produção. |
| Horas efetivas por função | Recalcular pessoal; tarefas emergenciais podem elevar o custo. |
| Licenças já disponíveis e número de usuários | Reduzir ou ampliar a linha Power BI Pro; confirmar condições de compartilhamento. |
| Suporte comercial, segurança, rede, recuperação de desastre e tributos | Acrescentar linhas antes de contratar; estão fora do modelo atual. |

As horas de desenvolvimento desta tabela cobrem hospedagem **e** manutenção. As horas de BI cobrem atualização **e** suporte funcional. Não há segunda cobrança para esses nomes. Os custos de erro ou retrabalho usados como possível benefício em FN-04 devem representar trabalho manual da operação anterior, sem reaproveitar as horas desta tabela como ganho adicional.
