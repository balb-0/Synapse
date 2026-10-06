# Estimativa de custos do ambiente do ETL

## 1. Escopo e data-base

Esta estimativa cobre o ambiente descrito na visão de tecnologia: Prefect,
processos Python do ETL, DuckDB, MinIO e Elastic Stack. Ela compara execução
local, piloto temporário e produção de referência. Não é cotação nem autorização
de compra.

- **Data-base:** 24/09/2026.
- **Moeda:** dólar dos Estados Unidos (USD), sem conversão cambial.
- **Horizonte:** mês de referência de 730 horas (365 × 24 ÷ 12, cerca de 30,42 dias) para recursos ligados continuamente.
- **Regime:** preços sob demanda, sem reserva, crédito promocional ou contrato.
- **Precisão:** duas casas decimais; valores intermediários não são arredondados.

## 2. Natureza dos valores

| Classe | Significado neste documento |
| :--- | :--- |
| **Premissa local** | USD 0,00 para contratação adicional de infraestrutura, assumindo equipamento e conexão já disponíveis. Não houve fatura ou medição para apurar esse valor; energia, mão de obra e depreciação não estão incluídas. |
| **Referência** | Tarifa unitária adotada apenas para tornar a comparação reproduzível. Precisa ser substituída por cotação na região e conta escolhidas. |
| **Projetado** | Resultado de quantidade estimada multiplicada pela tarifa de referência. Não é gasto observado. |

Nenhum total local, do piloto ou da produção deve ser apresentado como custo medido. O custo local de contratação adicional é uma premissa; os demais totais são projeções.

## 3. Premissas de capacidade e operação

| Dimensão | Local | Piloto | Produção de referência |
| :--- | :--- | :--- | :--- |
| Finalidade | desenvolvimento e validação | homologação com execução assistida | operação contínua com redundância mínima |
| Janela ligada | sob demanda | 180 h/mês | 730 h/mês |
| Controle e ETL | máquina existente | 1 VM média | 2 VMs médias |
| DuckDB e MinIO | contêineres locais | consolidados na VM do ETL | 2 VMs médias para processamento/armazenamento |
| Elastic Stack | não implantada; apenas contrato | 1 VM média, nó único | 3 VMs grandes, nós separados |
| Bloco SSD provisionado | 20 GB já disponíveis | 200 GB | 1.500 GB |
| Objetos ativos no mês | até 5 GB locais | 100 GB | 1.000 GB |
| Cópia de segurança | não incluída | 100 GB | 1.000 GB |
| Saída para internet | não medida | 20 GB/mês | 200 GB/mês |
| Retenção de telemetria | não aplicável | 14 dias | 30 dias |
| Execução do ETL | manual | diária | diária, com reprocessamento previsto |

A produção é deliberadamente uma topologia de referência, não uma previsão de
demanda confirmada. Volumes, concorrência, disponibilidade e retenção ainda
precisam ser medidos em piloto.

## 4. Tarifas de referência

As tarifas abaixo formam um modelo paramétrico simples. VMs representam o custo
agregado de CPU e memória; por isso CPU e RAM não são cobradas novamente.

| Variável | Unidade | Tarifa de referência |
| :--- | :--- | ---: |
| `vm_media_h` | VM-hora | USD 0,20 |
| `vm_grande_h` | VM-hora | USD 0,40 |
| `bloco_gb_mes` | GB-mês de SSD | USD 0,08 |
| `objeto_gb_mes` | GB-mês de objeto | USD 0,0265 |
| `egresso_gb` | GB transferido para internet | USD 0,09 |
| licenças Python, Prefect, DuckDB e MinIO | mês | USD 0,00 no modelo comunitário |
| licença Elastic autogerenciada Basic | mês | USD 0,00; suporte pago não incluído |

## 5. Fórmulas

Para cada cenário:

```text
compute = Σ(quantidade_de_vms × horas_ligadas × tarifa_da_vm)
bloco = GB_de_bloco × bloco_gb_mes
objetos = GB_de_objetos_ativos × objeto_gb_mes
backup = GB_de_backup × objeto_gb_mes
transferencia = GB_de_egresso × egresso_gb
total_mensal = compute + bloco + objetos + backup + transferencia + licencas
total_anual = total_mensal × 12
```

As fórmulas não incluem impostos. Um orçamento em BRL deve converter o total
somente depois de registrar a taxa, a data e a fonte cambial usadas.

## 6. Cálculo dos cenários

### 6.1 Local — medido parcialmente

| Componente | Quantidade | Cálculo | USD/mês |
| :--- | ---: | :--- | ---: |
| Infraestrutura incremental | — | equipamento e conexão já disponíveis | **0,00 medido** |
| Energia, depreciação e trabalho | — | não medidos | **não disponível** |
| **Total de desembolso incremental conhecido** | | | **0,00 medido** |

O zero local significa somente que não houve fatura incremental de
infraestrutura. Ele não significa custo total de propriedade igual a zero.

### 6.2 Piloto — projetado

| Componente | Quantidade | Cálculo | USD/mês |
| :--- | ---: | :--- | ---: |
| Controle, ETL, DuckDB e MinIO | 1 VM média por 180 h | `1 × 180 × 0,20` | 36,00 |
| Elastic Stack | 1 VM média por 180 h | `1 × 180 × 0,20` | 36,00 |
| Bloco SSD | 200 GB-mês | `200 × 0,08` | 16,00 |
| Objetos ativos | 100 GB-mês | `100 × 0,0265` | 2,65 |
| Cópia de segurança | 100 GB-mês | `100 × 0,0265` | 2,65 |
| Transferência de saída | 20 GB | `20 × 0,09` | 1,80 |
| Licenças comunitárias | 1 mês | tarifa de referência | 0,00 |
| **Total projetado mensal** | | soma dos itens | **95,10** |
| **Total projetado anual** | | `95,10 × 12` | **1.141,20** |

O nó único da Elastic Stack torna o piloto inadequado para compromisso de alta
disponibilidade. Desligar as duas VMs fora da janela prevista é condição para
manter o custo de compute indicado.

### 6.3 Produção de referência — projetado

| Componente | Quantidade | Cálculo | USD/mês |
| :--- | ---: | :--- | ---: |
| Controle e workers do ETL | 2 VMs médias por 730 h | `2 × 730 × 0,20` | 292,00 |
| DuckDB e MinIO | 2 VMs médias por 730 h | `2 × 730 × 0,20` | 292,00 |
| Elastic Stack | 3 VMs grandes por 730 h | `3 × 730 × 0,40` | 876,00 |
| Bloco SSD | 1.500 GB-mês | `1.500 × 0,08` | 120,00 |
| Objetos ativos | 1.000 GB-mês | `1.000 × 0,0265` | 26,50 |
| Cópia de segurança | 1.000 GB-mês | `1.000 × 0,0265` | 26,50 |
| Transferência de saída | 200 GB | `200 × 0,09` | 18,00 |
| Licenças comunitárias | 1 mês | tarifa de referência | 0,00 |
| **Total projetado mensal** | | soma dos itens | **1.651,00** |
| **Total projetado anual** | | `1.651,00 × 12` | **19.812,00** |

O cenário não promete alta disponibilidade completa: DuckDB é embarcado e a
topologia de replicação do MinIO ainda precisa ser definida. As duas VMs da
camada de dados representam capacidade e separação operacional, não uma
garantia automática de failover.

## 7. Comparação e sensibilidade

| Cenário | Natureza do total | USD/mês | USD/ano | Principal condicionante |
| :--- | :--- | ---: | ---: | :--- |
| Local | medido parcialmente | 0,00 | não calculado | energia e trabalho não medidos |
| Piloto | projetado | 95,10 | 1.141,20 | desligamento após 180 h/mês |
| Produção de referência | projetado | 1.651,00 | 19.812,00 | sete VMs ligadas continuamente |

Impacto marginal com as tarifas adotadas:

- mais 100 horas de uma VM média: **USD 20,00**;
- mais 100 GB-mês de bloco SSD: **USD 8,00**;
- mais 100 GB-mês de objetos ou backup: **USD 2,65**;
- mais 100 GB de saída para internet: **USD 9,00**.

Compute é a variável dominante no cenário de produção. Antes de contratar, o
piloto deve medir memória, CPU, duração dos jobs, crescimento diário dos logs e
taxa de reprocessamento para redimensionar as VMs e a retenção.

## 8. Exclusões e limites

Não estão incluídos:

- impostos, câmbio, compromisso de uso, créditos e descontos negociados;
- domínio, certificados, DNS, balanceador, VPN, firewall gerenciado e IPs;
- suporte comercial, plantão, treinamento, mão de obra e resposta a incidentes;
- energia, depreciação e internet do ambiente local;
- serviço gerenciado de banco, Prefect Cloud ou Elastic Cloud;
- tráfego entre zonas/regiões, restauração, requisições de objeto e snapshots
  além da cópia de segurança simplificada;
- ambientes paralelos de desenvolvimento, homologação e recuperação de
  desastre;
- crescimento além dos volumes e retenções declarados.

A licença sem tarifa não elimina o custo de hospedar, operar, atualizar e
proteger o software. Recursos corporativos ou suporte contratado devem entrar
como nova linha depois de cotação.

## 9. Fontes consultáveis

As tarifas deste documento são referências de planejamento arredondadas, não
uma reprodução integral da tabela de uma nuvem. Para uma contratação, as
quantidades deste modelo devem ser recalculadas nas fontes oficiais vigentes:

- [AWS Pricing Calculator](https://calculator.aws/) — cotação por região,
  configuração e regime de compra;
- [Amazon EC2 On-Demand Pricing](https://aws.amazon.com/ec2/pricing/on-demand/)
  — referência para compute sob demanda;
- [Amazon EBS Pricing](https://aws.amazon.com/ebs/pricing/) — armazenamento em
  bloco; a página explica cobrança por GB provisionado e desempenho adicional;
- [Amazon S3 Pricing](https://aws.amazon.com/s3/pricing/) — armazenamento de
  objetos, requisições, recuperação e transferência;
- [Elastic — assinaturas autogerenciadas](https://www.elastic.co/subscriptions)
  — recursos do nível Basic e opções comerciais;
- [Licença do Prefect](https://github.com/PrefectHQ/prefect/blob/main/LICENSE),
  [licença do DuckDB](https://github.com/duckdb/duckdb/blob/main/LICENSE) e
  [licença do MinIO](https://github.com/minio/minio/blob/master/LICENSE) — base
  para a premissa de software comunitário sem tarifa mensal neste cenário.

Consulta realizada em 24/09/2026. Preço, licença e disponibilidade regional
podem mudar; os links devem ser revisitados antes de qualquer decisão de compra.

## 10. Atualização da estimativa

Recalcular o documento quando ocorrer qualquer um destes eventos:

1. escolha de provedor, região, tipo de instância ou moeda de contratação;
2. medição do piloto alterar CPU, memória, armazenamento, duração ou retenção
   em mais de 20%;
3. inclusão de alta disponibilidade, recuperação de desastre ou segundo
   ambiente permanente;
4. adoção de suporte pago, Prefect Cloud, Elastic Cloud ou recurso licenciado;
5. mudança material nas tarifas ou no contrato das ferramentas.

O responsável pela atualização deve guardar a exportação da calculadora ou a
cotação usada e marcar cada linha como medida, cotada ou projetada. Assim, um
valor real nunca substitui silenciosamente uma premissa, nem uma projeção é
apresentada como fatura observada.
