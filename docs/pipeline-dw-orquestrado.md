# Pipeline completo com tarefas Prefect

`etl.orchestration.pipeline.run_pipeline` é o comando completo. O flow
`pipeline-completo` confirma o backfill das seis fontes antes das tarefas
`load_warehouse`, `reconcile_warehouse` e `publish_warehouse`. `ingest-object`
e `backfill` permanecem entradas para ingestão tratada; receber um objeto
isolado não publica um conjunto incompleto.

## Executar e agendar

No runner do Compose, com os seis objetos disponíveis no MinIO:

```sh
docker compose run --rm --no-deps runner python scripts/orchestration/run_pipeline.py
```

`ETL_DUCKDB_PATH` identifica o mesmo banco em todas as etapas.
`ETL_PUBLISH_DIR` identifica o destino privado dos sete Parquet e do manifesto;
no Compose, o padrão é `/data/publicacao`, fora de `/app`. O consumidor recebe
somente uma geração publicada, sem o DuckDB nem os CSVs de entrada.

O scheduler serve `pipeline-completo/agendado-dw` diariamente com cron
`0 3 * * *`. `prefect.yaml` também oferece `pipeline-completo/manual-dw` para
publicação explícita com `prefect deploy --all`. Credenciais e bucket/prefixo
vêm das variáveis de extração validadas, sem credencial no deployment.

A lista de fontes precisa conter exatamente pesquisas, empresas, clientes,
questoes, respondentes e respostas, sem repetição. O comando ordena a lista
pelas dependências. Resultado ausente, duplicado ou sem estado `loaded`/`ignored`
bloqueia o DW. Para carregar apenas uma fonte, use a entrada de ingestão.

`observed_at` é opcional e precisa representar uma observação real no último
dia do mês. A agenda não fornece esse parâmetro. Sem observação, C03 permanece
`not_observed`; a execução não inventa histórico nem converte ausência em zero.

## Falha e retomada

Cada uma das três tarefas DW tem `retries=2`, intervalo de um segundo,
`retry_condition_fn=_should_retry`, cache desabilitado e timeout de uma hora.
A abertura de DuckDB usa `etl.load.connection.connect_with_retry`, com espera
finita definida por `ETL_DUCKDB_WRITE_LOCK_TIMEOUT_SECONDS`. Falha permanente
de schema, caminho, permissão ou reconciliação não recebe retry automático.
Falhas transitórias esgotadas deixam a tarefa e o flow em falha.

O lock comum de `ingest_object` e do trecho DW serializa writers orquestrados
nos runners Linux, inclusive threads do mesmo processo. A espera é finita, e o
SO libera o lock quando o processo termina. Comandos externos de ingestão/DW
que não usam a orquestração não participam desse lock; evite executá-los em
paralelo com o pipeline. A conexão DuckDB também protege contra outro processo
que mantenha o arquivo aberto.

Uma falha analítica preserva checkpoints e objetos já confirmados na ingestão.
Ao repetir o comando, esses objetos ficam `ignored`, e os fatos são reconstruídos
na transação da carga. A reconciliação exige a carga deste run e as origens
correntes. A publicação verifica novamente essa condição antes de escrever.

A geração anterior fica ativa se a publicação falhar antes da troca atômica de
`current.json`. Se a troca já ocorreu e a mesma tarefa for repetida, ela só
reutiliza a geração quando load reference, nomes de arquivo, schema, contagens,
hashes e conteúdo coincidem com a origem. A comparação de conteúdo usa
`EXCEPT ALL` nos dois sentidos; contagens iguais não escondem valores diferentes.
Uma execução completa nova gera um novo load reference e pode produzir uma nova
geração, sem duplicar a contagem lógica dos fatos.

## Logs e verificações

O evento de volume da orquestração é `orchestration.load.emitted`.
`orchestration.ingest_object.emitted` confirma o objeto sem repetir `loaded_count`.
As tarefas DW emitem `orchestration.analytics_load.emitted`,
`orchestration.analytics_reconcile.emitted` e
`orchestration.analytics_publish.emitted`, com duração, status e tentativas.

O comando imprime um objeto JSON como última linha do stdout em sucesso.
Uma falha de execução sai com código 1 e objeto JSON no stderr contendo
`status=failed`, `failed_stage` e `error_type`, sem o texto da causa original.
Parâmetro inválido sai com código 2 pelo argparse.

`orchestration.pipeline.emitted` recebe `status=completed` somente depois da
publicação. Em falha, `failed_stage` identifica a etapa; `stage` continua sendo
`orchestration`, para não alterar os agrupamentos do painel.

As suítes abaixo cobrem o caminho real DuckDB/Parquet com entradas sintéticas,
a preservação da geração anterior, falhas e retomada. O teste de retry após a
troca do ponteiro usa o motor Prefect e exige uma única geração publicada:

```sh
PYTHONPATH=src python -m unittest tests.orchestration.test_pipeline_completo \
  tests.orchestration.test_warehouse_tasks tests.e2e.test_pipeline_completo_e2e
```

Esses testes não são evidência de execução no ambiente do parceiro nem de
atualização no Power BI Desktop. A execução de uma fonte autorizada e as
validações BI têm registros próprios.
