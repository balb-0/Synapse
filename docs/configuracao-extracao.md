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
| `ETL_SOURCE_DIR` | Sim | Diretório local e externo ao Git que contém os arquivos de entrada |
| `ETL_NIFI_API_URL` | Sim | Endpoint da API do NiFi |
| `ETL_NIFI_INPUT_DIR` | Não | Caminho da entrada dentro do container; padrão `/opt/nifi/input` |
| `ETL_MINIO_ENDPOINT` | Sim | Endpoint do MinIO usado pelo pipeline |
| `ETL_MINIO_BUCKET` | Sim | Bucket usado para os objetos do pipeline |
| `ETL_MINIO_ACCESS_KEY` | Sim | Identificador da credencial do MinIO |
| `ETL_MINIO_SECRET_KEY` | Sim | Segredo da credencial do MinIO |
| `ETL_REQUEST_TIMEOUT_SECONDS` | Não | Timeout das requisições; padrão `30` segundos |

O arquivo [`.env.example`](../.env.example) contém somente nomes, endpoints
locais e valores não sensíveis. As credenciais devem ser preenchidas apenas no
`.env` local ou injetadas pelo ambiente de execução.

## Validações

Ao carregar a configuração, o código verifica:

- presença do diretório, endpoints, bucket e credenciais obrigatórias;
- existência do diretório de entrada;
- uso de `http` ou `https` nos endpoints;
- ausência de usuário e senha dentro das URLs;
- caminho absoluto da entrada vista pelo NiFi;
- nome válido para o bucket;
- timeout numérico maior que zero;
- nomes válidos para parâmetros explícitos.

Uma configuração inválida gera `ConfigurationError`. A mensagem identifica o
campo incorreto, mas não inclui o valor da credencial.

## Uso no código

```python
from etl.extraction import load_extraction_settings

settings = load_extraction_settings()
```

Parâmetros explícitos podem ser usados em execução local ou em testes:

```python
settings = load_extraction_settings(
    parameters={
        "source_dir": "C:/dados/sindusfarma",
        "minio_endpoint": "http://localhost:19000",
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
