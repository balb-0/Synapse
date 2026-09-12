# Integração da transformação essencial

Implementação das tarefas MG-01 a MG-11. O módulo `etl.transformation` recebe
`ExtractedBatch` de LN-02 e entrega registros tipados, rejeições e metadados de
duplicatas. Não acessa rede, banco de destino ou relógio de negócio implícito.

## Uso pelo consumidor

```python
from datetime import datetime, timezone
from etl.transformation.consistency import ReferenceData
from etl.transformation.pipeline import transform_batch
from etl.transformation.quarantine import QuarantineStore

# batch vem do extrator LN-02. Estas referências são registros canônicos
# aceitos, do mesmo universo de origem, obtidos pelo chamador.
references = ReferenceData(canonical_reference_records)
result = transform_batch(
    batch,
    references=references,
    previous=confirmed_identity_checksums,
    source_offset=absolute_first_record_offset,
    ingested_at=datetime.now(timezone.utc),
    source_timezone=confirmed_source_timezone,
)
quarantine = QuarantineStore(restricted_quarantine_path)
quarantine.persist(result.rejected)
rows_to_load = [record.as_duckdb_row() for record in result.accepted]
operational_metrics = result.safe_summary()
```

Os nomes descritivos do exemplo são entradas do adaptador; não são funções ou
serviços já implantados. O fluxo é: transformar, persistir quarentena, carregar
aceitos com idempotência, registrar duplicatas e somente então confirmar o
checkpoint. Se qualquer etapa falhar, não confirmar o checkpoint. Reexecutar
o lote completo usando o estado confirmado, nunca um cache de tentativas.

## Contratos para as outras frentes

| Frente | Entrada/saída necessária |
| --- | --- |
| LN | source canônico sem extensão, SHA-256 do arquivo, offset absoluto zero-based e registros que preservam todas as colunas |
| MC | `destination_columns(source)` define colunas de negócio e técnicas DuckDB; listas são serializadas como JSON |
| MC | Obter `previous: record_identity → content_checksum` do estado confirmado e serializar a decisão/carga por identidade |
| OV | Publicar `safe_summary()`: source/run/task/batch, status, duração, bytes de entrada e contagens; não publicar `.data` ou `.as_duckdb_row()` |
| VB | Importar os testes e o job `.gitlab/ci/transformation.yml` na suíte integrada; executar teste real de carga da frente MC |

Integração LN→MG comprovada nos testes usa a implementação real do contrato
LN-02. Para referências, a ordem é empresas/pesquisas, clientes/questões,
participações/respostas. A verificação é de integridade de chaves, sem
consolidar indicadores ou inferir correspondências entre sistemas.

## Decisões técnicas

Python e biblioteca padrão mantêm compatibilidade com LN-02. Decimal evita
perda binária nos percentuais; IDs são strings normalizadas sem float. Datas
civis usam DATE e horários usam UTC somente com informação explícita de
fuso. `zoneinfo` identifica horários inválidos/ambíguos. As dependências de
qualidade são fixadas separadamente e não entram no runtime.

Schema, conversões, validação, identidade, quarentena e adaptação de lotes são
módulos separados. A identidade e a classificação de duplicatas são funções
puras; não alteram estado antes da carga. O SQLite local fornece transação e
chave única para rejeições por referência, com arquivo 0600. É um adaptador
local de quarentena, não substituto do DuckDB ou do armazenamento central.

Participações não têm chave de evento homologada. Por isso, sua identidade é
a ocorrência identificada por checksum e posição absoluta. Reentrega do mesmo
arquivo converge; outro snapshot exige reconciliação pelo responsável pela
fonte. Não reduzir o grão a empresa/pesquisa/cliente quando cliente é ausente.

Valores sensíveis permanecem nos registros aceitos para carga restrita, pois
retirá-los mudaria o contrato de ingestão. Logs e ledger de rejeições contêm
somente metadados. O conteúdo original necessário à auditoria é encontrado
na fonte imutável pelo checksum e offset, inclusive para registros aceitos.

## Verificação e evolução

Consulte a [matriz de validação](matriz-transformacao.md), o
[catálogo completo](catalogo-transformacao.md) e o
[inventário de regras](inventario-regras-transformacao.md). Mudança de campos,
tipos ou política de identidade exige nova versão e revisão do consumidor.
O catálogo possui verificação automatizada contra o contrato executável.
