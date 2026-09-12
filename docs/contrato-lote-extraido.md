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

## Convenção dos arquivos CSV

Os extratores CSV representam a posição como `row:N`, em que `N` é a quantidade
de registros lógicos já incluídos nos lotes. Cabeçalho e linhas vazias não entram
nessa contagem. A sequência começa em 1 e avança uma unidade por lote.

O checkpoint CSV inclui obrigatoriamente `source_version` com o SHA-256 do
objeto. Antes da retomada, o extrator valida a fonte, o formato da posição e essa
versão. Depois, pula exatamente os registros confirmados e emite a página
seguinte. Um checkpoint que já alcançou o fim resulta em uma sequência vazia,
sem recriar o último lote.

O `CheckpointStore` continua separado da leitura. Cabe ao fluxo carregar o
último checkpoint confirmado, entregá-lo ao extrator e chamar `commit` somente
depois que o lote tiver sido transformado, carregado e reconciliado.

## Atributos técnicos para transporte

Metadados e checkpoint podem ser representados como atributos por meio de
`ExtractedBatch.as_attributes()`. Os atributos não incluem os registros nem
campos de negócio, evitando que nomes, e-mails ou respostas apareçam nos logs
do orquestrador ou no mecanismo de transporte.

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

Os adaptadores de armazenamento de objetos, APIs, checkpoints e observabilidade
podem ser implementados sobre essas interfaces. Nenhum deles precisa importar
ou receber uma conexão com o banco de destino.

## Evento de log da extração

Para cada `ExtractedBatch`, o extrator produz um `ExtractionBatchLogEvent`. Esse
evento combina os metadados do lote com a posição do checkpoint, mas não carrega
a coleção `records`. O destino de logs recebe apenas o evento técnico por meio
de `ExtractionLogSink`.

Essa separação impede que respostas, e-mails, identificadores pessoais ou outros
valores das fontes sejam serializados acidentalmente. O adaptador
`StandardLoggingSink` publica os campos como atributos do `LogRecord`; a
formatação e o transporte dos logs permanecem externos ao contrato do extrator.
