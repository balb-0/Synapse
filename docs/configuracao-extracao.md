# Configuração da extração

A etapa de extração recebe caminhos, endpoints e credenciais por parâmetros ou
variáveis de ambiente. Valores informados diretamente por parâmetro têm
prioridade sobre o ambiente. Não há credenciais fixas no código ou no arquivo
`.env.example`.

A implementação está em
[`src/etl/extraction/config.py`](../src/etl/extraction/config.py).

## Variáveis de ambiente

| Variável | Obrigatória | Uso |
| :--- | :---: | :--- |
| `ETL_MINIO_ENDPOINT` | Sim | Endpoint do MinIO usado pelo pipeline |
| `ETL_MINIO_BUCKET` | Sim | Bucket usado para os objetos do pipeline |
| `ETL_MINIO_INPUT_PREFIX` | Não | Prefixo dos objetos de entrada; padrão `landing` |
| `ETL_MINIO_ACCESS_KEY` | Sim | Identificador da credencial do MinIO |
| `ETL_MINIO_SECRET_KEY` | Sim | Segredo da credencial do MinIO |
| `ETL_REQUEST_TIMEOUT_SECONDS` | Não | Timeout das requisições; padrão `30` segundos |
| `ETL_EXTRACTION_BATCH_SIZE` | Não | Quantidade máxima de registros por lote; padrão `1000` |
| `ETL_EXTRACTION_MAX_ATTEMPTS` | Não | Total de tentativas por leitura; padrão `3` |
| `ETL_EXTRACTION_RETRY_INITIAL_DELAY_SECONDS` | Não | Espera antes do primeiro retry; padrão `0.5` segundo |
| `ETL_EXTRACTION_RETRY_MAX_DELAY_SECONDS` | Não | Limite da espera entre tentativas; padrão `5` segundos |
| `ETL_SOURCE_DIR` | Não | Diretório usado somente pelo adaptador local de desenvolvimento e testes |

O arquivo [`.env.example`](../.env.example) contém somente nomes, endpoints
locais e valores não sensíveis. As credenciais devem ser preenchidas apenas no
`.env` local ou injetadas pelo ambiente de execução.

## Validações

Ao carregar a configuração, o código verifica:

- presença do endpoint, bucket e credenciais obrigatórias;
- existência do diretório local, quando informado;
- uso de `http` ou `https` nos endpoints;
- ausência de usuário e senha dentro das URLs;
- prefixo relativo e sem referência ao diretório pai;
- nome válido para o bucket;
- timeout numérico maior que zero;
- tamanho de lote inteiro maior que zero;
- quantidade de tentativas inteira maior que zero;
- esperas de retry numéricas, finitas e não negativas;
- espera máxima maior ou igual à espera inicial;
- nomes válidos para parâmetros explícitos.

Uma configuração inválida gera `ConfigurationError`. A mensagem identifica o
campo incorreto, mas não inclui o valor da credencial.

## Uso no código

```python
from etl.extraction import (
    EmpresasExtractor,
    MinioObjectReader,
    ObjectReference,
    RetryExecutor,
    load_extraction_settings,
)

settings = load_extraction_settings()
reader = MinioObjectReader.from_settings(settings)
retry_executor = RetryExecutor.from_settings(settings)
extractor = EmpresasExtractor(
    object_reader=reader,
    object_reference=ObjectReference(
        bucket=settings.minio_bucket,
        key=f"{settings.minio_input_prefix}/empresas.csv",
    ),
    batch_size=settings.batch_size,
    retry_executor=retry_executor,
)
```

O timeout é aplicado à conexão e às leituras HTTP do MinIO. Os retries internos
do cliente HTTP ficam desativados, evitando tentativas ocultas além do limite
definido pela política da extração.

Parâmetros explícitos podem ser usados em execução local ou em testes:

```python
settings = load_extraction_settings(
    parameters={
        "minio_endpoint": "http://localhost:19000",
        "minio_input_prefix": "landing",
    }
)
```

Credenciais são armazenadas em `SecretValue`. Tanto `str` quanto `repr`
retornam um valor oculto. O valor original só é obtido de forma explícita pelo
adaptador responsável por realizar a conexão:

```python
access_key = settings.minio_access_key.get_secret_value()
```

Para diagnóstico, `safe_summary()` retorna endpoints e caminhos, mas substitui
as duas credenciais por `********`. Esse é o único formato que deve ser enviado
para logs.
