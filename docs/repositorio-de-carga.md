# Repositório de carga em lotes no DuckDB

O repositório de carga é quem grava, no arquivo local do DuckDB, os lotes que
a transformação já validou, tipou e separou entre aceitos e rejeitados. Este
documento registra como essa escrita acontece: em lotes parametrizados, com o
schema de destino validado antes de qualquer linha entrar, com contagens que
vêm de uma consulta ao banco em vez de um número calculado em memória, com o
acesso de escrita serializado entre processos e com a conexão parametrizável
para o volume de cada ambiente.

A implementação está em
[`src/etl/load/duckdb_repository.py`](../src/etl/load/duckdb_repository.py) e
[`src/etl/load/config.py`](../src/etl/load/config.py). O contrato físico das
tabelas — nome, tipo, constraints e as tabelas de controle que a carga
escreve — está registrado em [`ddl-ingestao.md`](ddl-ingestao.md).

## Escopo

Este documento cobre o caminho de escrita do repositório de carga:

- como um lote é gravado com uma escrita parametrizada por tabela, em vez de
  uma instrução por linha;
- por que a validação de schema desta etapa não precisa de uma checagem
  própria, e o que já a garante;
- de onde vêm as contagens que o repositório devolve, e por que passaram a
  vir de uma consulta ao banco;
- como o repositório espera o escritor anterior liberar o arquivo, em vez de
  falhar na primeira tentativa, quando dois processos disputam a mesma carga;
- os parâmetros de conexão que o ambiente pode ajustar, e o padrão quando
  nenhum é informado;
- como o insert do lote converge ao ser reexecutado com o mesmo `run_id` e
  `batch_id`, em vez de violar a chave primária da tabela de ingestão.

## Fora de escopo

- **Reprocessar sob uma execução diferente da que gravou o lote.** Este
  documento cobre a convergência de uma mesma tentativa repetida (mesmo
  `run_id`/`batch_id`). Um backfill que reapresenta o mesmo conteúdo sob um
  `run_id` novo é interceptado antes, pela deduplicação de linha — ver
  [ADR 0003](adrs/0003-convergencia-do-insert-no-reprocessamento-do-lote.md).
- **Aceitar a correção do parceiro como versão nova.** Chave de negócio igual
  com conteúdo diferente continua sendo conflito de identidade na
  transformação; isso é assunto de issue própria, não desta etapa (ver
  [ADR 0002](adrs/0002-identidade-e-versoes-na-tabela-de-ingestao.md)).
- **Decidir o que retomar depois de uma falha parcial.** O lote perdido já
  fica registrado com status de falha (ver [`ddl-ingestao.md`](ddl-ingestao.md));
  decidir o que reprocessar e em que ordem é a etapa de compensação, coberta em
  [`compensacao-e-retomada-de-carga.md`](compensacao-e-retomada-de-carga.md).
- **Bloquear campo incompatível ou migrar uma tabela existente.** As tabelas de
  ingestão usam `CREATE TABLE IF NOT EXISTS`; comparar o contrato atual com o
  que já está gravado, recusar uma alteração incompatível e versionar uma
  migração é uma etapa própria, à parte da escrita de lote.
- **Medir o tamanho de lote adequado ou provar a equação de contagem com
  volume real.** As contagens aqui descritas são o insumo dessa medição, não a
  medição em si.
- **Testes gray-box de ponta a ponta contra uma instância real.** Este
  documento descreve o comportamento por trás dos testes unitários da
  camada; um roteiro de integração mais amplo é um documento à parte.

## Escrita em lotes parametrizados

Cada chamada de carga recebe um lote já transformado e grava, numa única
transação:

- as linhas aceitas na tabela de ingestão da fonte, e a identidade de cada
  uma na tabela de identidades já carregadas;
- as ocorrências rejeitadas e os motivos de cada uma;
- o registro da execução, com status e contagens.

As linhas aceitas e as rejeitadas do lote inteiro são gravadas com uma
instrução parametrizada por tabela — todas as linhas do lote num só comando,
em vez de uma instrução por linha. Um lote com centenas de rejeições, por
exemplo, grava a lista de ocorrências e a lista de motivos em duas escritas,
não em uma por ocorrência.

## Validação de schema

A escrita não declara uma checagem própria de schema porque duas garantias
já cobrem o que essa checagem faria:

- **A lista de colunas gravadas vem do contrato canônico.** O repositório
  nunca grava um campo que a transformação não declarou; todo registro aceito
  chega com todas as colunas do contrato preenchidas (ausente é `NULL`
  explícito, nunca uma chave que falta).
- **As constraints do contrato físico recusam o que não pode ser gravado**, com
  um erro que já nomeia a coluna e o motivo: coluna obrigatória ausente,
  tipo incompatível ou coluna desconhecida são recusados pelo próprio banco,
  não por uma validação em Python que duplicaria a mesma checagem.

## Contagens confirmadas pelo banco

O repositório devolve, por lote, quantos registros foram carregados e quantos
foram rejeitados. Essas duas contagens vêm de uma consulta ao banco — quantas
linhas existem, para a execução e o lote em questão, na tabela de ingestão e
na tabela de rejeitados — e não do tamanho das listas que a transformação
produziu em memória. A mesma consulta alimenta tanto o resultado devolvido
pela chamada quanto o registro gravado na tabela de execução: as duas nunca
divergem, porque são a mesma leitura.

A consulta acontece ainda dentro da transação que grava o lote, antes de
confirmá-la: o que ela lê é exatamente o que a confirmação torna permanente,
ou desaparece junto se a transação for revertida. Não há uma janela em que a
contagem lida possa ficar desatualizada em relação ao que de fato foi
gravado.

A quantidade de duplicados continua vindo da transformação: não existe uma
tabela própria de duplicados para confirmar essa contagem contra o banco.

## Reprocessamento do lote

Chamar `load_batch` de novo para um lote que já tinha sido gravado com
sucesso — mesmo `run_id` e `batch_id` — converge para o mesmo estado em vez
de falhar. É o caso, por exemplo, de quem chama o repositório não ter
confirmado que a tentativa anterior tinha terminado antes de repetir.

O insert das linhas aceitas declara um alvo de conflito explícito na
identidade de idempotência (`idempotency_key`, ver
[`ddl-ingestao.md`](ddl-ingestao.md)) e o resolve descartando a tentativa
repetida:

```sql
INSERT INTO "ingestao_<fonte>" (...) VALUES (...)
ON CONFLICT ("idempotency_key") DO NOTHING
```

Isso não é o mesmo `INSERT OR REPLACE` que as tabelas de controle usam: a
tabela de ingestão tem, além da chave primária, um `UNIQUE` separado (chave
de negócio mais conteúdo), e o DuckDB recusa resolver os dois sem um alvo
explícito. A linha gravada na primeira tentativa não é sobrescrita pela
repetição — `run_id`, `batch_id`, `task_id` e `ingested_at` continuam sendo
os de quem gravou a linha primeiro. A razão de ser `DO NOTHING` e não
`DO UPDATE` está na [ADR 0003](adrs/0003-convergencia-do-insert-no-reprocessamento-do-lote.md).

Um lote que mistura, no mesmo `executemany`, uma linha já gravada com uma
linha nova também converge: só a linha nova é inserida, a existente não é
tocada.

## Serialização de escrita

O arquivo do banco aceita um único processo com acesso de escrita por vez; uma
segunda tentativa enquanto o primeiro ainda está aberto é recusada pelo
próprio banco, que identifica o processo concorrente no erro. O repositório
não propaga esse erro na primeira tentativa: ele espera o escritor anterior
liberar o arquivo, checando periodicamente, até um tempo limite configurável.
Só depois de esgotado esse tempo o repositório informa que não conseguiu abrir
o arquivo, citando o prazo e o motivo devolvido pelo banco.

Um erro de abertura que não seja disputa de arquivo — permissão negada,
diretório inexistente — não é reinterpretado como disputa: ele é propagado de
imediato, porque esperar não o resolveria.

## Parâmetros de conexão

| Parâmetro | Variável de ambiente | Padrão | Uso |
| :--- | :--- | :--- | :--- |
| `threads` | `ETL_DUCKDB_THREADS` | o padrão do próprio DuckDB | Threads de execução da conexão |
| `memory_limit` | `ETL_DUCKDB_MEMORY_LIMIT` | o padrão do próprio DuckDB | Limite de memória da conexão |
| `write_lock_timeout_seconds` | `ETL_DUCKDB_WRITE_LOCK_TIMEOUT_SECONDS` | 300 segundos | Tempo de espera pelo escritor anterior antes de desistir |

`threads` e `memory_limit` ausentes significam não tocar no que o DuckDB já
usa por conta própria — nenhum dos dois é aplicado à conexão. Quando
informado, o valor de `memory_limit` segue a gramática que o próprio DuckDB
aceita (por exemplo `'2GB'`); um valor fora dessa gramática é recusado pelo
banco ao abrir a conexão, com o erro do próprio DuckDB.

O fluxo orquestrado lê esses três parâmetros do ambiente a cada execução e os
repassa para toda abertura do repositório dessa execução — não é preciso
alterar código para ajustá-los por ambiente, só a variável correspondente.

## Testes

```bash
python -m unittest discover -s tests/load -t .
```

A suíte cobre, além do que já está descrito em
[`ddl-ingestao.md`](ddl-ingestao.md): a contagem de carregados e rejeitados
batendo com uma linha gravada por fora da chamada de carga (prova de que a
contagem vem do banco, não da lista em memória); a aplicação dos parâmetros
de conexão quando informados e a ausência de efeito quando não informados; e
a espera pelo escritor anterior — tanto o caso em que ele libera o arquivo a
tempo quanto o caso em que o tempo limite se esgota primeiro.

`tests/load/test_reprocessing.py` cobre a convergência descrita em
"Reprocessamento do lote": a tabela não cresce ao reexecutar o mesmo lote, a
proveniência da primeira gravação sobrevive à repetição, um lote com
sobreposição parcial só grava a linha nova, e a contagem confirmada continua
correta depois do replay.
