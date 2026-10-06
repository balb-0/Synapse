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

## Descrição técnica do que existe

O repositório contém extratores Python para seis fontes, transformação com contratos e testes, carga tratada em DuckDB e SQL dos fatos e dimensões analíticos. A orquestração usa Prefect; MinIO é o armazenamento de objetos do fluxo. O modelo de BI versiona um projeto Power BI e as especificações dos quatro cubos. A publicação analítica e a integração de ponta a ponta têm condições e limites descritos nos respectivos contratos; uma tela prototipada ou um contrato não comprova operação produtiva contínua.

| Camada | Evidência versionada | Limite relevante para a análise financeira |
| :--- | :--- | :--- |
| Extração e transformação | `src/etl/extraction/`, `src/etl/transformation/` e testes correspondentes | A disponibilidade e a frequência das fontes ainda precisam ser confirmadas no piloto. |
| Carga e cubos | `src/etl/load/`, `sql/duckdb/`, `docs/contrato-fisico-cubos.md` | O custo de operação depende de volume, retenção e frequência reais. |
| Orquestração e observabilidade | `src/etl/orchestration/`, `prefect.yaml`, `docs/estimativa-custos-ambiente.md` | Elastic Stack aparece no cenário de custo, mas não deve ser contabilizada como economia comprovada. |
| Consumo | `powerbi/`, `docs/solucao_dashboard.md`, `docs/acesso-cubos-bi.md` | O benefício de relatórios depende de adoção, treinamento e substituição de trabalho manual. |

Os dashboards apoiam perguntas sobre ciclo de pesquisas, participação, pipeline mensal e resultados/instrumentos. A decisão financeira é se o ganho operacional esperado justifica implantar e sustentar essas capacidades. O objetivo de reduzir cruzamentos manuais consta de `docs/projeto.md` e `docs/matriz-evidencias-problem-canvas.md`; esses documentos também registram que a magnitude de horas e retrabalho ainda não foi medida.

## Convenções e fontes de referência

- **Pessoal:** o [Anexo II vigente da Portaria SGD/MGI nº 750/2023](https://www.gov.br/governodigital/pt-br/contratacoes-de-tic/legislacao/modelo-de-contratacao-de-servicos-de-desenvolvimento-manutencao-e-sustentacao-de-software/portaria-sgd-mgi-no-750-de-20-de-marco-de-2023) publica salário e fator-k por perfil. Os documentos FN-02 a FN-04 usam `salário × fator-k ÷ 160 h` como custo horário de referência, não como salário contratado pelo parceiro. O fator já representa a composição de custo; encargos não são adicionados novamente.
- **Infraestrutura:** `docs/estimativa-custos-ambiente.md` fornece cenários paramétricos de USD 95,10/mês (piloto) e USD 1.651,00/mês (produção de referência). Esses valores não são faturas ou cotação regional. As páginas oficiais de [EC2](https://aws.amazon.com/pt/ec2/pricing/on-demand/), [EBS](https://aws.amazon.com/pt/ebs/pricing/) e [S3](https://aws.amazon.com/pt/s3/pricing/) indicam os componentes a recotar antes da compra.
- **Câmbio de referência:** [PTAX de venda do Banco Central em 05/10/2026](https://ptax.bcb.gov.br/ptax_internet/consultarUltimaCotacaoDolar.do), R$ 4,9859 por USD. A conversão é apenas para comparar parcelas em BRL; a taxa efetiva, impostos e spread podem diferir.
- **Licença:** a [assinatura Basic autogerenciada da Elastic](https://www.elastic.co/subscriptions) é gratuita na tabela consultada; hospedagem, operação e eventual suporte pago continuam sendo custos separados. Licenças e contratos devem ser confirmados antes de contratar.

Todas as quantidades de horas, relatórios, retrabalho, erros e adoção introduzidas nesta Sprint são **hipóteses de cenário** até que o parceiro forneça dados observados. Cada tabela deve indicar unidade, período, fórmula e origem da tarifa. O horizonte padrão para comparação é de 12 meses após implantação; FN-05 poderá mostrar horizontes adicionais sem misturar gastos iniciais e recorrentes.
