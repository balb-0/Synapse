# Contrato comum dos extratores

Os seis extratores seguem o mesmo contrato. Cada um lê sua fonte e entrega uma
sequência de lotes para a etapa seguinte do ETL. O contrato não conhece o banco
de destino, permitindo que transformação e carga evoluam sem alterar a leitura
das fontes.

A implementação está em
[`src/etl/extraction/contracts.py`](../src/etl/extraction/contracts.py).

## Responsabilidades

| Componente | Responsabilidade |
| :--- | :--- |
| `Extractor` | Ler uma fonte e produzir objetos `ExtractedBatch` |
| `ExtractedBatch` | Transportar os registros, o checkpoint candidato e os metadados do lote |
| `CheckpointStore` | Recuperar e confirmar checkpoints sem fazer a leitura da fonte |
| `MetadataSink` | Publicar metadados técnicos sem receber os registros do lote |

O extrator recebe um checkpoint já carregado, mas não o persiste. O checkpoint
produzido por um lote só deve ser confirmado depois que o consumidor aceitar o
lote. Assim, uma falha posterior não faz a extração avançar para uma posição
que ainda não foi processada.

## Estrutura do lote

| Parte | Campos |
| :--- | :--- |
| Registros | Sequência de registros no formato chave/valor, mantendo os nomes e valores recebidos da fonte |
| Checkpoint | `source`, `position`, `sequence` e, quando disponível, `source_version` |
| Metadados | `source`, `run_id`, `task_id`, `batch_id`, início, fim, quantidade de registros, quantidade de bytes, versão do schema, checksum da fonte e versão do contrato |

`position` é propositalmente opaco. Um extrator de arquivo pode usar o número da
linha, enquanto uma API pode usar uma página ou cursor. Essa diferença fica
dentro de cada extrator e não altera o contrato entregue ao restante do ETL.

## Uso com o NiFi

No NiFi, o conteúdo do FlowFile representa os registros do lote. Metadados e
checkpoint são enviados como atributos por meio de
`ExtractedBatch.as_attributes()`. Os atributos não incluem os registros nem
campos de negócio, evitando que nomes, e-mails ou respostas apareçam nos logs.

| Atributo | Descrição |
| :--- | :--- |
| `source` | Nome estável da fonte |
| `run_id` | Identificador da execução |
| `task_id` | Identificador da tarefa de extração |
| `batch_id` | Identificador único do lote na execução |
| `started_at` / `finished_at` | Início e fim da leitura, com timezone |
| `record_count` | Quantidade de registros no lote |
| `byte_count` | Quantidade de bytes lidos |
| `schema_version` | Versão do schema usada na leitura |
| `source_checksum` | Identidade da versão da fonte, quando disponível |
| `checkpoint_position` | Posição de retomada após a confirmação do lote |
| `checkpoint_sequence` | Ordem do lote na fonte |
| `checkpoint_source_version` | Versão da fonte à qual o checkpoint pertence, quando disponível |
| `contract_version` | Versão deste contrato |

Os adaptadores de arquivo, APIs, armazenamento de checkpoint e observabilidade
serão implementados sobre essas interfaces. Nenhum deles precisa importar ou
receber uma conexão com o ClickHouse.
