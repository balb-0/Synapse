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
- produzem um único `ExtractedBatch`, inclusive quando não há registros;
- informam quantidade de registros, bytes, horários, versão do schema e
  checkpoint candidato.

O arquivo `pesquisas.csv` possui colunas finais sem nome. Para que nenhuma
posição seja perdida, elas são expostas de forma determinística como
`unnamed_column_23`, `unnamed_column_24` e assim por diante. Colunas repetidas
recebem o sufixo `__2`, `__3` conforme sua ocorrência.

A retomada parcial ainda não pertence à LN-04. Se um checkpoint for fornecido,
o extrator encerra com `UnsupportedCheckpointError`. A leitura em lotes e a
retomada a partir da última linha confirmada serão adicionadas na LN-07.

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
```

## Verificação com os arquivos fornecidos

Foi feita uma execução local somente leitura com a versão mais recente dos seis
arquivos, mantida fora do repositório. Os hashes foram calculados antes e depois
da execução e permaneceram iguais.

| Fonte | Registros | Colunas | Bytes lidos | Origem preservada |
| :--- | ---: | ---: | ---: | :---: |
| Pesquisas | 366 | 33 | 132.693 | Sim |
| Empresas | 779 | 9 | 66.691 | Sim |
| Clientes | 5.430 | 5 | 393.677 | Sim |
| Respondentes | 18.735 | 6 | 411.628 | Sim |
| Questões | 3.297 | 13 | 1.125.401 | Sim |
| Respostas | 281.835 | 9 | 20.291.071 | Sim |
