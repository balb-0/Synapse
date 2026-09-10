# Extratores das fontes

Os extratores leem os objetos de entrada sem alterá-los e entregam os registros
no contrato definido em [`contrato-lote-extraido.md`](contrato-lote-extraido.md).
A implementação não grava no DuckDB, não confirma checkpoints e não aplica as
regras da camada tratada.

## Fontes

| Fonte | Objeto esperado | Extrator | Situação |
| :--- | :--- | :--- | :--- |
| Pesquisas | `landing/pesquisas.csv` | `PesquisasExtractor` | Implementado na LN-04 |
| Empresas | `landing/empresas.csv` | `EmpresasExtractor` | Implementado na LN-04 |
| Clientes | `landing/clientes.csv` | `ClientesExtractor` | Implementado na LN-05 |
| Respondentes | `landing/respondentes.csv` | `RespondentesExtractor` | Implementado na LN-05 |
| Questões | `landing/questoes.csv` | `QuestoesExtractor` | Implementado na LN-06 |
| Respostas | `landing/respostas.csv` | `RespostasExtractor` | Implementado na LN-06 |

O prefixo pode ser alterado por configuração. A chave efetiva do objeto vem do
evento do MinIO e é representada por `ObjectReference`, junto ao bucket, à
versão e ao identificador do evento quando esses valores estiverem disponíveis.

## Implementação

O código está dividido em:

- [`object_storage.py`](../src/etl/extraction/object_storage.py), com o contrato
  de leitura e o adaptador para o cliente do MinIO;
- [`csv_extractors.py`](../src/etl/extraction/csv_extractors.py), com a leitura
  comum dos arquivos e os extratores das quatro fontes tabulares simples;
- [`questionnaire_extractors.py`](../src/etl/extraction/questionnaire_extractors.py),
  com a representação estrutural de questões e respostas;
- [`contracts.py`](../src/etl/extraction/contracts.py), com o lote, os metadados
  e o checkpoint entregues ao estágio seguinte.

```text
Evento do MinIO
      ↓
ObjectReference
      ↓
MinioObjectReader
      ↓
Extrator específico da fonte
      ↓
ExtractedBatch
```

O cliente do MinIO é recebido pelo adaptador, em vez de ser criado dentro do
extrator. Essa separação permite utilizar o serviço real na execução e um leitor
em memória nos testes, sem mudar a regra de leitura do CSV.

## Comportamento comum

Os seis extratores:

- abrem o objeto em modo somente leitura;
- interpretam CSV em UTF-8, com suporte a BOM e separador `;`;
- preservam nomes, chaves e valores recebidos da fonte;
- validam a presença das colunas conhecidas;
- rejeitam linhas cuja quantidade de campos difere do cabeçalho;
- calculam o SHA-256 sobre os bytes originais;
- produzem páginas de `ExtractedBatch` com tamanho configurável;
- informam quantidade de registros, bytes, horários, versão do schema e
  checkpoint candidato.

O arquivo `pesquisas.csv` possui colunas finais sem nome. Para que nenhuma
posição seja perdida, elas são expostas de forma determinística como
`unnamed_column_23`, `unnamed_column_24` e assim por diante. Colunas repetidas
recebem o sufixo `__2`, `__3` conforme sua ocorrência.

## Clientes e respondentes

O extrator de clientes preserva `id_cliente` e `id_empresa` como texto, inclusive
zeros à esquerda, valores não confirmados como `s/i` e campos vazios. O endereço
presente em `e-mail` faz parte do registro entregue à transformação, mas não é
incluído nos metadados, atributos de transporte ou mensagens de erro.

O extrator de respondentes preserva sem conversão os três componentes da chave
candidata: `id_pesq`, `id_empresa` e `id_cliente`. Horários e percentuais também
permanecem no formato recebido. A validação de chaves incompletas e a conversão
de tipos pertencem à transformação e não são antecipadas pela extração.

## Questões e respostas

Os campos `alternativas`, `linhas_matriz` e `colunas_matriz` de questões usam
` | ` como separador na fonte recebida. O `QuestoesExtractor` mantém esses
textos originais e acrescenta `estrutura`, sempre com as três propriedades. Os
itens são entregues como sequências de texto; quando um campo não se aplica, a
sequência correspondente fica vazia.

```python
{
    "estrutura": {
        "alternativas": ("Opção A", "Opção B"),
        "linhas_matriz": (),
        "colunas_matriz": (),
    }
}
```

Cada linha de `respostas.csv` representa um elemento atômico de resposta, não
um questionário completo nem uma pessoa. Como os campos preenchidos variam de
acordo com o tipo da questão, o `RespostasExtractor` acrescenta `conteudo` com
as mesmas quatro propriedades em todos os registros. Campos não aplicáveis são
representados por `None` nessa estrutura derivada, enquanto continuam vazios
nos campos originais.

```python
{
    "conteudo": {
        "alternativa": None,
        "linha_matriz": "Linha sintética",
        "coluna_matriz": "Coluna sintética",
        "valor": "5",
    }
}
```

Essa representação resolve apenas a estrutura variável do CSV. Identificadores,
quantidades e valores continuam como texto, e nenhuma regra de qualidade altera
ou descarta registros durante a extração.

## Lotes e retomada

O tamanho padrão de cada lote é de 1.000 registros e pode ser alterado pelo
parâmetro `batch_size` do extrator. Na composição do pipeline, esse valor deve
vir de `ETL_EXTRACTION_BATCH_SIZE`. O cabeçalho e as linhas vazias não entram na
contagem de registros.

Para calcular o SHA-256 antes de emitir lotes sem manter objetos grandes na
memória, a origem é lida em blocos de 1 MiB para um buffer temporário. Até 8 MiB
ficam em memória; acima desse limite, a biblioteca transfere o buffer para um
arquivo temporário, removido automaticamente ao encerrar a leitura.

Cada lote informa:

- `batch_id` sequencial, como `empresas-000002`;
- `checkpoint.position` com a última posição lógica incluída, como `row:2000`;
- `checkpoint.sequence` com a ordem da página;
- `checkpoint.source_version` com o SHA-256 do objeto;
- `record_count` com a quantidade de registros da página;
- `byte_count` com o tamanho total do objeto lido.

Na retomada, o extrator aceita somente checkpoints da mesma fonte e do mesmo
SHA-256. Ele ignora a quantidade de registros já confirmada e começa no registro
seguinte. Uma página entregue, mas ainda não confirmada pelo consumidor, volta a
ser emitida depois de uma interrupção; páginas já confirmadas não são repetidas.
Esse comportamento mantém a entrega pelo menos uma vez sem avançar o estado
antes da transformação e da carga.

Checkpoints com posição inválida, versão ausente ou posição além do fim geram
`InvalidCheckpointError`. Quando o conteúdo da origem mudou, o resultado é
`StaleCheckpointError`, impedindo que uma posição antiga seja aplicada ao novo
arquivo. Se o último checkpoint já cobre toda a fonte, nenhum lote é emitido.

## Timeout, retry e falhas das fontes

O acesso ao MinIO utiliza timeout de conexão e de leitura configurado por
`ETL_REQUEST_TIMEOUT_SECONDS`. Os retries do cliente HTTP são desativados para
que todas as tentativas fiquem sujeitas ao mesmo limite explícito da extração.

Por padrão, uma leitura pode realizar até três tentativas. Depois da primeira
falha transitória, as esperas são de 0,5 segundo e 1 segundo. O crescimento é
exponencial e nunca ultrapassa o valor de
`ETL_EXTRACTION_RETRY_MAX_DELAY_SECONDS`. Antes de cada nova tentativa, o buffer
parcial é descartado, evitando juntar bytes de duas leituras do mesmo objeto.

As falhas são classificadas da seguinte forma:

| Natureza | Categorias | Comportamento |
| :--- | :--- | :--- |
| Transitória | timeout, indisponibilidade e limite de requisições | Repete até `ETL_EXTRACTION_MAX_ATTEMPTS` |
| Permanente | autenticação, objeto inexistente, CSV malformado e falha desconhecida | Interrompe na primeira ocorrência |

São consideradas transitórias as exceções conhecidas de timeout e conexão, os
status HTTP `408`, `425`, `429`, `500`, `502`, `503` e `504` e os códigos
equivalentes do armazenamento de objetos. Erros desconhecidos não são repetidos
automaticamente, pois podem representar defeitos de programação ou entradas que
uma nova tentativa não corrigiria.

Cada tentativa malsucedida produz um `SourceFailure` com fonte, operação,
categoria, natureza, número da tentativa, limite e próxima espera. A mensagem da
exceção e o conteúdo da fonte não fazem parte desse registro. O componente
`FailureRecorder` permite encaminhar esses eventos à observabilidade. A ligação
dos eventos de falha com o logger compartilhado permanece no escopo da OV-05.

Ao esgotar uma falha transitória, o extrator gera
`RetryLimitExceededError`. Falhas permanentes de acesso geram
`PermanentSourceError`. Problemas no conteúdo CSV continuam gerando
`MalformedSourceError`, sem retry. A repetição da tarefa completa no Prefect não
é configurada pelos extratores e permanece sob responsabilidade da OV-04.

## Metadados e logs por lote

Cada lote emitido gera o evento estruturado `extraction.batch.emitted`. O evento
possui `stage=extraction` e `status=success`, inclusive quando uma fonte contém
somente o cabeçalho e produz um lote com zero registros.

Os campos publicados são:

| Grupo | Campos |
| :--- | :--- |
| Correlação | `source`, `run_id`, `task_id` e `batch_id` |
| Tempo | `started_at`, `finished_at` e `duration_ms` |
| Volume | `record_count` e `byte_count` |
| Contrato | `schema_version` e `contract_version` |
| Origem | `source_checksum` |
| Retomada | `checkpoint_position`, `checkpoint_sequence` e `checkpoint_source_version` |

O `ExtractionBatchLogEvent` é criado a partir do lote, mas contém apenas esses
atributos técnicos. Os registros extraídos, nomes de colunas, respostas,
identificadores pessoais e valores de negócio não são repassados ao destino de
logs.

O `StandardLoggingSink` envia os atributos pelo parâmetro `extra` do módulo
`logging`, usando o logger `etl.extraction`. Dessa forma, o formatador e o
encaminhamento definidos pela OV-05 podem produzir JSON e enviar os eventos à
Elastic Stack sem exigir que o extrator conheça essa infraestrutura. Também é
possível fornecer outra implementação de `ExtractionLogSink` nos testes ou na
execução do pipeline.

Os timestamps são emitidos no padrão ISO 8601 com timezone UTC. A duração é
calculada em milissegundos e nunca inclui o conteúdo dos registros. O campo
`byte_count` representa o tamanho total do objeto de origem lido naquela
extração, conforme definido no contrato atual.

## Limites entre as etapas

A comparação do hash com o histórico de objetos concluídos pertence ao fluxo
orquestrado. O extrator calcula e informa o hash, mas não decide sozinho se a
execução deve ser ignorada. Da mesma forma, o checkpoint emitido é apenas um
candidato e só poderá ser confirmado depois da transformação, carga e
reconciliação do lote.

Conversão de tipos, normalização de datas e percentuais, tratamento de nulos,
deduplicação e rejeição são responsabilidades da transformação. Manter essas
regras fora do extrator preserva a fidelidade da entrada e evita acoplamento com
o schema do banco.

## Testes

Os testes usam somente dados sintéticos e não acessam os arquivos do parceiro.
Eles verificam as fontes implementadas, fonte vazia, cabeçalho incompatível,
linha malformada, cálculo de hash, preservação de campos, ausência de conteúdo
sensível nos atributos técnicos e fechamento da conexão do MinIO.

```bash
python -m unittest tests.extraction.test_csv_extractors -v
python -m unittest tests.extraction.test_clientes_respondentes_extractors -v
python -m unittest tests.extraction.test_questoes_respostas_extractors -v
python -m unittest tests.extraction.test_batching_checkpoints -v
python -m unittest tests.extraction.test_resilience -v
python -m unittest tests.extraction.test_extraction_logs -v
python -m unittest tests.extraction.test_extractor_contract_suite -v
python -m unittest tests.extraction.test_smoke_extraction -v
```

A matriz completa de cenários está em
[`testes-extracao.md`](testes-extracao.md), e o resultado reproduzível do smoke
test está em [`smoke-test-extracao.md`](smoke-test-extracao.md).

## Verificação com os arquivos fornecidos

Foi feita uma execução local somente leitura com a versão mais recente dos seis
arquivos, mantida fora do repositório. Os hashes foram calculados antes e depois
da execução e permaneceram iguais.

| Fonte | Registros | Colunas | Bytes lidos | Lotes de até 1.000 | Origem preservada |
| :--- | ---: | ---: | ---: | ---: | :---: |
| Pesquisas | 366 | 33 | 132.693 | 1 | Sim |
| Empresas | 779 | 9 | 66.691 | 1 | Sim |
| Clientes | 5.430 | 5 | 393.677 | 6 | Sim |
| Respondentes | 18.735 | 6 | 411.628 | 19 | Sim |
| Questões | 3.297 | 13 | 1.125.401 | 4 | Sim |
| Respostas | 281.835 | 9 | 20.291.071 | 282 | Sim |

Também foi simulada uma interrupção durante a leitura de `respostas.csv`. Na
retomada, o lote não confirmado foi emitido novamente e os lotes anteriores ao
checkpoint confirmado não foram repetidos.
