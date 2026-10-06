# Contratos físicos DuckDB

Esta pasta é a camada de banco do G05. O DuckDB é embutido: o processo Python abre um arquivo local, sem servidor, porta ou credencial de banco. A pasta versiona o contrato SQL; o arquivo `.duckdb` e os dados reais ficam fora do Git.

## Arquivos e dependências

| Arquivo | Responsabilidade | Fonte geradora |
| :--- | :--- | :--- |
| [`001_ingestao_tratada.sql`](001_ingestao_tratada.sql) | Ingestão tipada, metadados e views de estado atual. | [`etl.load.ddl`](../../src/etl/load/ddl.py), derivada do schema de transformação. |
| [`002_dimensoes.sql`](002_dimensoes.sql) | Dimensões conformadas, chave determinística e membro desconhecido. | [`etl.analytics.dimensions_ddl`](../../src/etl/analytics/dimensions_ddl.py). |
| [`003_fatos_ciclo_participacao.sql`](003_fatos_ciclo_participacao.sql) | Fatos de ciclo C01 e participação C02; depende das dimensões. | [`etl.analytics.facts_cycle_participation`](../../src/etl/analytics/facts_cycle_participation.py). |
| [`004_fatos_pipeline_instrumento.sql`](004_fatos_pipeline_instrumento.sql) | Fechamento mensal C03 e instrumento C04; depende das dimensões. | [`etl.analytics.facts_pipeline_instrument`](../../src/etl/analytics/facts_pipeline_instrument.py). |

A ordem numérica descreve as dependências. Aplicar DDL isoladamente não executa ingestão, reconciliação nem publicação. A rotina analítica também administra tabelas técnicas de execução e reconciliação. Para o estado completo, use o código de carga e seus testes; não monte um banco “final” apenas concatenando estes arquivos.

## Validar e regenerar

Na raiz do repositório, com as dependências instaladas:

```bash
python scripts/load/render_ddl.py --check
PYTHONPATH=src python -m etl.analytics.dimensions_ddl --check
PYTHONPATH=src python -m etl.analytics.facts_cycle_participation --check
PYTHONPATH=src python -m etl.analytics.facts_pipeline_instrument --check
```

`--check` compara a saída gerada com o SQL versionado e falha se divergir. Para regenerar após uma mudança no contrato, execute o mesmo comando sem `--check`, revise o diff e rode a suíte da camada. Não altere apenas o SQL se a fonte geradora permanecer diferente.

## Criar o arquivo e conferir persistência

```bash
python scripts/load/duckdb_env.py --database /caminho/privado/ingestao.duckdb
PYTHONPATH=src python -m unittest discover -s tests/load -t . -v
PYTHONPATH=src python -m unittest discover -s tests/analytics -t . -v
```

O health check cria o arquivo, testa consulta e persistência e remove seus objetos temporários. Ele não cria as tabelas definitivas do ETL e deve rodar sem outro escritor usando o arquivo. O parâmetro tem prioridade sobre `ETL_DUCKDB_PATH`.

## Carga e consumo

- [Runbook do ETL](../../docs/runbook-execucao.md), [ambiente DuckDB](../../docs/ambiente-duckdb.md) e [repositório de carga](../../docs/repositorio-de-carga.md): configuração, ingestão, lock e retomada.
- [Contrato dimensional](../../docs/contrato-fisico-cubos.md) e [decisão de consumo](../../docs/decisao-consumo-cubos.md): grão, agregação e dados permitidos no BI.
- [`etl.analytics.load`](../../src/etl/analytics/load.py) e [`etl.analytics.publish`](../../src/etl/analytics/publish.py): carga e publicação. Confira as opções com `--help` antes de operar sobre dados autorizados.

C03 representa fechamentos efetivamente observados; falta de observação não é estoque zero. Métricas indisponíveis permanecem nulas ou bloqueadas conforme o contrato. Permissões do arquivo DuckDB e da pasta Parquet são controles do sistema operacional; o SQL versionado não cria autorização produtiva.
