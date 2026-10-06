# FN-03 — Operação mensal e pessoal

**Data-base:** 06/10/2026. **Moeda:** BRL. **Natureza:** custo mensal projetado; não é despesa observada. Piloto e produção são alternativas, não ambientes cumulativos.

## Perímetro e conversão

A [estimativa versionada de infraestrutura](../estimativa-custos-ambiente.md) apresenta USD 95,10/mês no piloto e USD 1.651,00/mês na produção de referência. Multiplicamos pela [PTAX venda de 05/10/2026](https://ptax.bcb.gov.br/ptax_internet/consultarUltimaCotacaoDolar.do), R$ 4,9859/USD: **R$ 474,16/mês** e **R$ 8.231,72/mês**. Os valores em USD são tarifas de planejamento, sem cotação regional; a PTAX não inclui spread, impostos ou taxas de contratação.

Essa parcela já agrega VMs, armazenamento em bloco e objeto, backup simplificado e saída de dados. Não adicionamos CPU, RAM, MinIO, DuckDB ou transferência novamente. Uma nova arquitetura exige refazer a estimativa na [AWS Pricing Calculator](https://calculator.aws/) com região, instâncias, uso e impostos definidos.

O custo de pessoal usa `salário × fator-k ÷ 160 h` com os perfis DESENV-02, ABI-02, ANR-02 e ATQ-02 do [Anexo II vigente da Portaria SGD/MGI nº 750/2023](https://www.gov.br/governodigital/pt-br/contratacoes-de-tic/legislacao/modelo-de-contratacao-de-servicos-de-desenvolvimento-manutencao-e-sustentacao-de-software/portaria-sgd-mgi-no-750-de-20-de-marco-de-2023). A alocação é fracionária; não implica contratar quatro pessoas em tempo integral.
