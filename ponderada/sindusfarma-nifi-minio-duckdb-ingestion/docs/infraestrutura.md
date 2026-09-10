# Infraestrutura local

## Objetivo

Subir um ambiente local mínimo para a ingestão:

- Apache NiFi: plano de controle operacional do fluxo.
- MinIO: object storage compatível com S3.
- Bucket `sindusfarma-data`: destino das camadas `raw/`, `bronze/`, `manifests/` e `rejected/`.

O foco é disponibilizar os serviços, montar a entrada local ignorada pelo Git e
permitir a recriação do fluxo NiFi versionado.

## Serviços

| Serviço | Porta local padrão | Uso |
| --- | ---: | --- |
| NiFi | `8080` | Interface web para construir/importar o fluxo. |
| MinIO API | `19000` | Endpoint S3 compatível usado pelo DuckDB a partir da máquina local. |
| MinIO Console | `19001` | Interface web para inspecionar buckets e objetos. |

Dentro da rede Docker, o MinIO continua respondendo em `http://minio:9000`.
Essa diferença é importante: containers usam o nome `minio` e a porta interna
`9000`; ferramentas rodando no Windows usam `localhost:19000`.

## Arquivos de configuração

| Arquivo | Papel |
| --- | --- |
| `.env.example` | Modelo de variáveis locais, sem segredo real. |
| `docker-compose.yml` | Define NiFi, MinIO e criação automática do bucket. |
| `.gitignore` | Impede commit de `.env`, saídas locais e artefatos gerados. |

## Montagens relevantes

| Origem local | Destino no container | Modo | Finalidade |
| --- | --- | --- | --- |
| `./local/input` | `/opt/nifi/input` | somente leitura | Entrada local com os CSVs reais do parceiro, não versionada. |
| `./nifi/flows` | `/opt/nifi/flows` | leitura/escrita | Exportação versionável do fluxo NiFi. |
| `./local/nifi-output` | `/opt/nifi/output` | leitura/escrita | Saídas locais temporárias, não versionadas. |
| volume `minio_data` | `/data` | leitura/escrita | Persistência dos objetos no MinIO. |

## Como subir

Copie o arquivo de exemplo:

```powershell
Copy-Item .env.example .env
New-Item -ItemType Directory -Force local\input
```

Coloque em `local/input/` os arquivos `clientes.csv`, `empresas.csv`,
`pesquisas.csv`, `questoes.csv`, `respondentes.csv` e `respostas.csv`.

Suba o ambiente:

```powershell
docker compose up -d
```

Acesse:

- NiFi: `http://localhost:8080/nifi`
- MinIO Console: `http://localhost:19001`

Credenciais padrão de desenvolvimento do MinIO:

```text
usuário: minioadmin
senha: minioadmin123
```

## Como parar

```powershell
docker compose down
```

Para remover também volumes persistidos de desenvolvimento:

```powershell
docker compose down -v
```

Use `down -v` apenas quando quiser apagar estado local de NiFi e MinIO.

## Solução de conflito de porta

As portas `9000` e `9001` costumam ser usadas pelo Docker/WSL ou por outro
MinIO local. Por isso, esta entrega expõe o MinIO no host pelas portas `19000`
e `19001`, configuradas em `.env.example`.

Se ainda houver conflito, escolha outras portas livres no `.env`:

```text
MINIO_API_PORT=29000
MINIO_CONSOLE_PORT=29001
```

## Validação feita

A configuração foi validada com:

```powershell
docker compose config
docker compose --env-file .env.example config
```

Os comandos expandiram os serviços, portas, variáveis e volumes corretamente.
Com `.env.example`, o projeto Compose ficou nomeado como
`sindusfarma-ingestion`. No ambiente local analisado apareceu um aviso de acesso a
`C:\Users\Inteli\.docker\config.json`, mas a validação terminou com código `0`.
Se o mesmo aviso impedir `docker compose up -d`, abra o Docker Desktop com o
usuário dono da pasta ou ajuste as permissões do arquivo de configuração do
Docker.

## Decisões desta etapa

- O NiFi enxerga os dados reais em `/opt/nifi/input`, mas a montagem é somente leitura.
- O MinIO é inicializado com um bucket único de desenvolvimento.
- O estado operacional fica em volumes Docker nomeados, fora do Git.
- Não há credenciais reais nos arquivos versionáveis.
- `latest` foi usado para MinIO e `mc` por simplicidade local. Em um ambiente
  compartilhado ou produtivo, a recomendação seria fixar versões específicas.
