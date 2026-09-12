# Ambiente local do DuckDB e health check

O banco de ingestão do pipeline é o DuckDB, decidido em
[`adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md`](adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md).
O DuckDB é embutido no processo da carga: não existe serviço a iniciar, host,
porta ou credencial. O ambiente local é um arquivo em disco, criado e
verificado por um comando documentado.

Este documento registra esse comando, a configuração que ele aceita, o que o
health check comprova e a evidência de uma execução reproduzível.

A implementação está em
[`src/etl/load/config.py`](../src/etl/load/config.py),
[`src/etl/load/environment.py`](../src/etl/load/environment.py) e
[`scripts/load/duckdb_env.py`](../scripts/load/duckdb_env.py).

## Escopo

Este documento cobre a primeira etapa da camada de carga: ter, em qualquer
máquina do time, o mesmo arquivo de banco criado do mesmo jeito e com uma
verificação objetiva de que ele responde e persiste. Ele cobre:

- o comando que cria o diretório e o arquivo do banco, de forma idempotente;
- a variável de ambiente que define o caminho do arquivo;
- as verificações do health check e o significado de cada uma;
- a evidência de uma execução local, com versões e saída do comando;
- os limites operacionais do banco embutido que a carga precisa respeitar.

## Fora de escopo

- **Definir as tabelas de ingestão.** O health check não cria objeto
  permanente no banco: a tabela usada na verificação de persistência é
  removida ao final. O contrato por fonte, com tipos, constraints e metadados
  técnicos, pertence às DDLs versionadas da carga, e a tradução dos tipos
  declarados pela camada de transformação está registrada como pendência no
  [inventário de contratos dimensionais](inventario-contratos-dimensionais.md).
- **Escrever ou reconciliar lotes.** Carga em lotes, controle de duplicidade,
  rejeição e reconciliação de contagens dependem das tabelas de destino e
  ficam nas etapas seguintes da camada de carga.
- **Serializar o acesso de escrita do pipeline.** O arquivo aceita um único
  escritor por vez; transformar essa restrição em fila, lock ou processo único
  é responsabilidade do repositório de carga, não da criação do ambiente. Este
  documento descreve a restrição e o erro que ela produz.
- **Publicar o health check como gate de integração contínua.** A consolidação
  dos jobs do grupo em um pipeline único é conduzida pela frente de CI; aqui o
  comando é local e reproduzível por qualquer pessoa do time.
- **Provisionar servidor, volume ou container.** O banco é um arquivo lido pelo
  próprio processo Python; não há serviço para subir nem porta para expor.

## Como criar o ambiente

Os comandos partem da raiz do repositório, porque um caminho relativo é
resolvido a partir do diretório de execução.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python scripts/load/duckdb_env.py
```

O comando cria `data/duckdb/ingestao.duckdb`, executa o health check e devolve
código de saída diferente de zero se alguma verificação falhar. Repetir o
comando não recria o arquivo nem apaga o conteúdo já carregado.

Opções do comando:

| Opção | Uso |
| :--- | :--- |
| `--database CAMINHO` | Arquivo do banco; tem prioridade sobre `ETL_DUCKDB_PATH` |

## Variáveis de ambiente

| Variável | Obrigatória | Uso |
| :--- | :---: | :--- |
| `ETL_DUCKDB_PATH` | Não | Arquivo do banco de ingestão; padrão `data/duckdb/ingestao.duckdb` |

O arquivo [`.env.example`](../.env.example) traz os nomes e o caminho local
sugerido. Uma variável presente e em branco vale como não configurada e usa o
padrão. Nenhuma dessas variáveis carrega credencial: o banco embutido é
acessado pelo sistema de arquivos.

Ao carregar a configuração, o código verifica:

- caminho apontando para um arquivo, não para um diretório;
- ausência de referência ao diretório pai (`..`) no caminho;
- recusa de banco em memória (`:memory:`), que não sobrevive à execução;
- nomes válidos para parâmetros explícitos.

Uma configuração inválida gera `ConfigurationError` nomeando a configuração
incorreta — a mensagem vale tanto para a variável de ambiente quanto para o
parâmetro do comando.

## O que o health check verifica

| Verificação | O que comprova |
| :--- | :--- |
| `arquivo_local` | O arquivo existe em disco depois da criação, com o tamanho registrado |
| `consulta_smoke` | O banco responde a uma consulta e devolve o valor esperado |
| `escrita_persistida` | Uma linha gravada em uma conexão continua legível depois de fechar e reabrir o arquivo |

A verificação de persistência é a que distingue um banco em memória de um
ambiente reproduzível: ela grava uma linha com um marcador único, fecha a
conexão, reabre o arquivo, relê a linha e remove a tabela e o schema usados.
Uma execução concluída não deixa objeto no banco. Uma execução interrompida
entre as duas conexões tenta remover o marcador; quando nem isso é possível,
o erro informa que a tabela permaneceu, e a execução seguinte a remove.

## Resultado da execução

- Data: 10 de setembro de 2026
- Ambiente: Python 3.12.3, DuckDB v1.5.5, dependências de `requirements.txt`
- Comando: `python scripts/load/duckdb_env.py`

Primeira execução, com o diretório do banco ainda inexistente:

```text
Arquivo: /caminho/do/repositorio/data/duckdb/ingestao.duckdb (criado nesta execucao)
DuckDB: v1.5.5 (embutido, sem servidor)
[ok] arquivo_local: /caminho/do/repositorio/data/duckdb/ingestao.duckdb com 274432 bytes
[ok] consulta_smoke: consulta devolveu 42
[ok] escrita_persistida: linha gravada em uma conexão e relida depois de reabrir o arquivo
```

Segunda execução do mesmo comando, sobre o arquivo já criado:

```text
Arquivo: /caminho/do/repositorio/data/duckdb/ingestao.duckdb (ja existia)
DuckDB: v1.5.5 (embutido, sem servidor)
[ok] arquivo_local: /caminho/do/repositorio/data/duckdb/ingestao.duckdb com 274432 bytes
[ok] consulta_smoke: consulta devolveu 42
[ok] escrita_persistida: linha gravada em uma conexão e relida depois de reabrir o arquivo
```

## Limites do banco embutido

- **Um escritor por vez.** O arquivo é bloqueado pelo processo que o abre. Com
  o pipeline em execução, o mesmo comando falha com
  `HEALTH_CHECK_FALHOU`, informando o arquivo e o motivo devolvido pelo
  DuckDB. Se o lock for tomado no meio da verificação, a mensagem também
  informa que a tabela do marcador ficou no arquivo. Rode o health check com
  o pipeline parado.
- **O arquivo guarda dados carregados.** `data/duckdb/`, `*.duckdb` e o journal
  `*.duckdb.wal` são ignorados pelo Git: o banco local não é versionado nem
  compartilhado, pelo mesmo motivo que as bases brutas não são.
- **O ambiente é local.** Reproduzir o ambiente é reproduzir o comando, não
  copiar o arquivo entre máquinas.

## Testes

```bash
python -m unittest discover -s tests/load -t .
```

A suíte tem 20 testes: configuração, criação idempotente do arquivo, relatório
do health check, ausência de objetos remanescentes no banco, execução do
comando documentado, o erro esperado quando outro processo mantém o arquivo
aberto e os dois caminhos de execução interrompida — com e sem a limpeza do
marcador. Os testes que exigem o DuckDB instalado são marcados como ignorados em
ambientes que só exercitam extração ou transformação.
