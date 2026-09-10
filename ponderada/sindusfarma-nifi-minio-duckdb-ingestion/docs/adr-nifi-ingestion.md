# ADR - Apache NiFi para orquestração da ingestão raw/bronze

## Contexto

O projeto precisava de uma entrega de ingestão usando dados reais do
parceiro, com object storage, formato colunar, validação analítica e
idempotência. Também era necessário diferenciar esta proposta das arquiteturas
dos colegas, evitando Kafka, ClickHouse e pipeline Python tradicional.

## Decisão

Usar Apache NiFi + MinIO + Parquet + DuckDB, com manifest append-only e marker
de sucesso por SHA-256 do arquivo. O DuckDB fica como warehouse local da
entrega, com tabelas bronze materializadas a partir dos Parquets do MinIO.

## Por que NiFi

NiFi deixa o ciclo operacional visível: processors, rotas, filas, retry,
backpressure e provenance. A ingestão não fica escondida em um script; o script
principal cria o fluxo pela API para evitar cliques manuais e manter a entrega
reproduzível.

## Alternativas consideradas

| Alternativa | Motivo para não escolher |
| --- | --- |
| Python puro | Menos observabilidade operacional e ficaria parecido com outras soluções. |
| DuckDB direto | Bom para validar, mas não deve substituir o plano de controle da ingestão. |
| Kafka | Não há fluxo streaming no problema atual; adicionaria complexidade. |
| Airflow | Orquestra tarefas, mas não oferece a mesma visibilidade de dataflow/filas. |
| Logstash | Forte em logs/eventos, menos natural para conversão CSV/Parquet com manifest. |

## Trade-offs

- NiFi tem footprint maior que scripts pequenos.
- O versionamento do flow precisa de export JSON e bootstrap.
- Parâmetros sensíveis exigem cuidado, especialmente com Access Key/Secret Key.
- O `ListFile` tem estado próprio; reprocessamento controlado limpa esse estado.
- Para alta concorrência, o manifest JSON append-only deveria evoluir para uma
  tabela/catálogo com controle transacional.
