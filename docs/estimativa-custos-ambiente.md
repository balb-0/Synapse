# Estimativa de custos do ambiente do ETL

## 1. Escopo e data-base

Esta estimativa cobre o ambiente descrito na visão de tecnologia: Prefect,
processos Python do ETL, DuckDB, MinIO e Elastic Stack. Ela compara execução
local, piloto temporário e produção de referência. Não é cotação nem autorização
de compra.

- **Data-base:** 24/09/2026.
- **Moeda:** dólar dos Estados Unidos (USD), sem conversão cambial.
- **Horizonte:** mês de 30 dias; 730 horas para recursos ligados continuamente.
- **Regime:** preços sob demanda, sem reserva, crédito promocional ou contrato.
- **Precisão:** duas casas decimais; valores intermediários não são arredondados.

## 2. Natureza dos valores

| Classe | Significado neste documento |
| :--- | :--- |
| **Medido** | Valor observado em fatura ou medidor. Só existe para o custo incremental de infraestrutura do ambiente local, que é USD 0,00 porque usa equipamento e conexão já disponíveis. Não houve medição de energia, mão de obra ou de nuvem. |
| **Referência** | Tarifa unitária adotada apenas para tornar a comparação reproduzível. Precisa ser substituída por cotação na região e conta escolhidas. |
| **Projetado** | Resultado de quantidade estimada multiplicada pela tarifa de referência. Não é gasto observado. |

Nenhum total do piloto ou da produção deve ser apresentado como custo medido.

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
