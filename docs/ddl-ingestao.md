# Contrato físico das tabelas de ingestão tratada

As tabelas de ingestão são o destino do fluxo
`Fonte → Extração → Transformações essenciais → Tabela de ingestão`. Este
documento registra o contrato físico dessas tabelas no DuckDB: nome, tipo,
constraints, metadados técnicos e as views de estado atual. Registra também as
estruturas de controle da carga — o que cada execução gravou, o que ela
rejeitou e por quê, e a conta que fecha as duas pontas.

O contrato executável está em [`src/etl/load/ddl.py`](../src/etl/load/ddl.py),
o SQL versionado em
[`sql/duckdb/001_ingestao_tratada.sql`](../sql/duckdb/001_ingestao_tratada.sql)
e a verificação de divergência em
[`scripts/load/render_ddl.py`](../scripts/load/render_ddl.py).

## Escopo

Este documento cobre a passagem do contrato canônico da transformação para o
banco de destino, que é onde nome, tipo e constraint deixam de ser convenção e
passam a ser recusa do banco. Ele cobre:

- o nome físico de cada tabela e o motivo do prefixo;
- a tradução do tipo declarado pelo contrato canônico para o tipo DuckDB;
- o que é uma linha da tabela de ingestão, e a chave que decorre disso;
- as constraints por fonte: chave primária, unicidade e obrigatoriedade;
- as views de estado atual e quando elas não existem;
- o registro por lote com status e contagens, e a chave que o identifica;
- a rejeição e seus motivos, gravados à parte das linhas aceitas;
- as views que agregam a execução e provam a equação de contagem;
- como o SQL versionado é mantido em sincronia com o contrato.

## Fora de escopo

- **Medir o lote e escolher o seu tamanho.** As estruturas aqui deixam a
  contagem por execução consultável; qual tamanho de lote adotar, e o relatório
  que compara execuções, dependem de rodar a carga com volume real.
- **Compensar e retomar uma falha parcial.** O lote perdido fica registrado com
  status e aparece como diferença na reconciliação, o que é o insumo da
  retomada — mas decidir o que reprocessar, e em que ordem, é a etapa de
  compensação.
- **Guardar o valor rejeitado.** A rejeição é gravada por referência (arquivo,
  posição e motivo), sem o conteúdo da linha. O dado bruto permanece no
  armazenamento restrito da extração, e a retenção dele é contrato do operador.
- **Carregar lotes.** Escrita em lotes, serialização do acesso de escrita e
  contagens confirmadas pelo banco pertencem ao repositório de carga.
- **Migrar schema existente.** As tabelas de ingestão usam
  `CREATE TABLE IF NOT EXISTS`, que cria o que falta e não altera o que existe.
  As tabelas de controle recebem um alinhamento de colunas ao abrir a conexão,
  o suficiente para um banco anterior continuar operando — mas reconstruir
  tabela para trocar chave, detectar campo incompatível, bloquear a carga e
  versionar a alteração é a etapa do gate de compatibilidade.
- **Decidir a classificação de duplicidade na transformação.** As constraints
  aqui declaram o que o banco aceita; quem decide se uma correção do parceiro
  vira versão nova ou rejeição é a etapa de deduplicação, na camada anterior.

## Nome físico

Cada fonte tem uma tabela `ingestao_<fonte>`:

| Fonte | Tabela | View de estado atual |
| :--- | :--- | :--- |
| `pesquisas` | `ingestao_pesquisas` | `ingestao_pesquisas_atual` |
| `empresas` | `ingestao_empresas` | `ingestao_empresas_atual` |
| `clientes` | `ingestao_clientes` | `ingestao_clientes_atual` |
| `respondentes` | `ingestao_respondentes` | — |
| `questoes` | `ingestao_questoes` | `ingestao_questoes_atual` |
| `respostas` | `ingestao_respostas` | `ingestao_respostas_atual` |

O prefixo separa a tabela de ingestão das camadas seguintes do tratamento do
dado, que ocupam o mesmo banco, e é o nome que o contrato da transformação e o
[inventário de contratos dimensionais](inventario-contratos-dimensionais.md) já
declaravam.

## Tipos

O contrato canônico nomeia os tipos na convenção do ClickHouse, destino
anterior à [ADR 0001](adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md).
A tradução acontece uma vez, no contrato físico:

| Tipo declarado | Tipo DuckDB | Observação |
| :--- | :--- | :--- |
| `String` | `VARCHAR` | |
| `Int64` | `BIGINT` | |
| `UInt64` | `UBIGINT` | |
| `Bool` | `BOOLEAN` | |
| `Date32` | `DATE` | |
| `Decimal(18, 6)` | `DECIMAL(18, 6)` | mesma precisão e escala |
| `DateTime64(6, 'UTC')` | `TIMESTAMP` | o fuso é normalizado para UTC antes da carga |
| `FixedString(64)` | `VARCHAR` | o DuckDB não tem largura fixa |
| `Array(String)` | `VARCHAR` | lista serializada como JSON |

Nenhum termo específico do banco anterior sobrevive à tradução: não há `engine`,
`ORDER BY` de tabela nem `Nullable`, que no DuckDB é o padrão da coluna.

## O que é uma linha

**Uma linha da tabela de ingestão corresponde a uma linha da fonte.** O mesmo
registro pode ocupar mais de uma linha quando o parceiro reexporta o arquivo
com conteúdo corrigido: a versão anterior permanece e a nova é acrescentada.

As seis fontes são snapshots reexportados, então correção é caso normal, não
anomalia. Guardar as versões evita reprocessar todos os snapshots quando o
versionamento de dimensão previsto no modelo dimensional
([`projeto.md`](projeto.md)) for adotado, e evita que a reconciliação da carga
conte correção como defeito de dado.

Cada linha carrega a proveniência que permite reconstruir o estado em qualquer
momento:

| Coluna técnica | Registra |
| :--- | :--- |
| `source` | fonte de origem |
| `source_checksum` | SHA-256 do objeto lido, isto é, qual arquivo |
| `source_offset` | posição da linha dentro do arquivo |
| `run_id`, `task_id`, `batch_id` | execução, tarefa e lote |
| `content_checksum` | hash do conteúdo tratado da linha |
| `record_identity` | hash da chave de negócio |
| `idempotency_key` | hash de identidade e conteúdo |
| `ingested_at` | momento da carga |
| `schema_version` | versão do contrato canônico aplicado |

## Constraints

| Constraint | Colunas | O que garante |
| :--- | :--- | :--- |
| `PRIMARY KEY` | `idempotency_key` | A mesma versão do mesmo registro não entra duas vezes, ainda que a deduplicação anterior falhe |
| `UNIQUE` | chave de negócio + `content_checksum` | A chave é declarada no banco sem proibir versão nova do mesmo registro |
| `NOT NULL` | metadados técnicos | Linha aceita sem proveniência não existe |
| `NOT NULL` | campos obrigatórios da fonte | O que a transformação recusa quando ausente também é recusado pelo banco |

Chave de negócio e campos obrigatórios por fonte:

| Fonte | Chave de negócio | Campos obrigatórios |
| :--- | :--- | :--- |
| `pesquisas` | `pesquisa_id` | `pesquisa_id` |
| `empresas` | `empresa_id` | `empresa_id` |
| `clientes` | `cliente_id` | `cliente_id`, `empresa_id` |
| `respondentes` | `source_checksum` + `source_offset` | `pesquisa_id`, `empresa_id` |
| `questoes` | `pesquisa_id` + `pergunta_id` | `pergunta_id`, `pesquisa_id`, `tipo` |
| `respostas` | `pesquisa_id` + `resposta_id` | `resposta_id`, `pesquisa_id`, `pergunta_id`, `respondent_id` |

`source_checksum` é a única coluna técnica que aceita nulo: o contrato de lote
permite lote sem checksum de objeto, usado pelo adaptador local de
desenvolvimento.

### Participação, a fonte sem chave natural

`respondentes` não tem chave de negócio confirmada — o inventário de contratos
dimensionais já registrava que a participação é identificada pela ocorrência,
sem colapsar pessoas ausentes. A identidade é a ocorrência física, arquivo mais
linha, e a unicidade declarada é essa.

Isso tem uma consequência a registrar: como a identidade depende do arquivo, um
reexport da mesma participação é uma ocorrência nova, e a fonte é reingerida
por inteiro. Resolver isso exige uma chave para a participação, que é uma
pergunta ao parceiro, não uma decisão de banco.

## Views de estado atual

Cada fonte com chave de negócio tem uma view `ingestao_<fonte>_atual` que
devolve a linha mais recente de cada chave, com exatamente as mesmas colunas da
tabela. Quem quer o estado corrente consulta a view; quem quer o histórico
consulta a tabela. A ordenação usa `ingested_at` e, no empate, `source_offset`.

`respondentes` não tem view: sem chave de negócio não existe noção de versão
mais recente, e cada linha é uma ocorrência distinta.

## Execução, rejeição e reconciliação

As tabelas de ingestão guardam o que foi aceito. O que cada execução fez — e o
que ela recusou — vive em estruturas próprias, para que uma linha rejeitada
nunca ocupe a mesma tabela de uma linha aceita.

### O registro de cada lote

`_batch_metadata` tem uma linha por lote, com o status e as três contagens:

| Coluna | Registra |
| :--- | :--- |
| `run_id`, `batch_id` | execução e lote |
| `source`, `task_id` | fonte e tarefa que produziram o lote |
| `status` | `carregado`, `carregado_com_rejeicoes` ou `falha` |
| `record_count` | quantas linhas a extração relatou no lote |
| `accepted_count` | quantas a carga gravou |
| `rejected_count` | quantas foram recusadas |
| `duplicated_count` | quantas já estavam carregadas |
| `byte_count` | tamanho lido |
| `started_at`, `finished_at` | janela de execução do lote |

A chave é o par `(run_id, batch_id)`, não `batch_id` sozinho: o identificador
do lote é sequencial por fonte (`pesquisas-000001`) e repete em toda execução,
então `batch_id` isolado faria cada execução sobrescrever a anterior e apagar o
histórico dela.

O status é gravado, não calculado a partir das contagens. Um lote revertido
grava zero nas três, exatamente como um lote vazio bem-sucedido: sem o status
gravado, as duas situações seriam indistinguíveis.

### O lote que falhou

Quando a carga de um lote falha, a transação é revertida — e por isso a linha
de `falha` é gravada **fora** dela, depois do rollback. Sem isso o lote perdido
desapareceria junto com a transação, e a execução fecharia a conta sem registro
de que algo se perdeu.

As contagens dessa linha são zero, porque nada do lote sobreviveu ao rollback.
A perda aparece como diferença entre `record_count` e o que foi contabilizado.
Se a falha impedir até a gravação desse registro, o erro original da carga
continua sendo o que chega a quem chamou: anotar o histórico não mascara a
causa da perda.

### A rejeição e seus motivos

| Estrutura | Guarda |
| :--- | :--- |
| `rejected` | a ocorrência recusada: fonte, arquivo, posição, execução, lote e momento |
| `rejected_reason` | um motivo por linha: `code` e `field` |

O motivo tem tabela própria em vez de uma lista JSON dentro da rejeição.
Contar rejeição por código ou por campo passa a ser consulta, e não exige que
quem lê saiba interpretar um documento:

```sql
SELECT code, count(*) FROM rejected_reason GROUP BY code ORDER BY 2 DESC;
```

A chave de `rejected` é `(rejection_id, run_id, batch_id)`. O `rejection_id`
identifica a ocorrência e o conjunto de motivos, mas não a execução: sozinho,
ele faria a rejeição vista por uma execução antiga ser sobrescrita pela
execução seguinte, e a lista de rejeições de uma execução passada mudaria a
cada reprocessamento. É a mesma chave usada no ledger durável da quarentena, na
camada anterior. Em `rejected_reason` a execução fica fora da chave de
propósito: o `rejection_id` já determina o conjunto de motivos, então
reapresentar a rejeição não repete os motivos.

As duas estruturas são gravadas com `INSERT OR REPLACE`. Um reprocessamento
reapresenta a mesma rejeição do mesmo lote, e o mesmo par código/campo pode
aparecer duas vezes na mesma ocorrência — nos dois casos a segunda passagem
converge em vez de derrubar a carga por violação de chave.

Convergir é o comportamento desejado quando a execução é a mesma: reprocessar o
mesmo objeto sem informar um identificador de evento reaproveita o mesmo
identificador de execução, e a segunda passagem atualiza as linhas da primeira
em vez de duplicá-las. O histórico de duas execuções fica separado quando os
identificadores de execução diferem, que é o caso de duas execuções distintas
do fluxo.

### Banco criado antes destas colunas

`CREATE TABLE IF NOT EXISTS` cria o que falta e não altera o que existe. Um
banco local criado antes desta versão manteria, portanto, a tabela de controle
antiga — sem `status` e sem as contagens — e a carga ficaria inoperante: as
views de execução não conseguiriam nem ser criadas, porque leem uma coluna que
não existe naquela tabela.

Por isso a carga alinha as tabelas de controle ao abrir a conexão, entre criar
as tabelas e criar as views. O alinhamento acrescenta as colunas que passaram a
ser exigidas e desobriga `reasons`, que ninguém mais preenche. Num banco novo é
um no-op, porque as colunas já nascem no `CREATE TABLE`.

O que o alinhamento **não** faz é refazer chave primária, porque isso exige
reconstruir a tabela. Uma tabela de controle criada antes desta versão continua
sem a chave nova e, sem chave, a gravação não tem o que substituir: nela um
reprocessamento acrescenta linha de controle em vez de convergir. Recriar o
arquivo local com o comando documentado em
[ambiente-duckdb.md](ambiente-duckdb.md) dá a forma completa; a reconstrução de
tabela com dado preservado é assunto da rotina de migração.

### As views de execução e de reconciliação

`execucao` agrega os lotes de cada execução: status, quantidade de lotes,
extraídos, carregados, rejeitados, duplicados, bytes, início e fim. Uma
execução é `falha` se qualquer lote seu falhou — um lote perdido não é
compensado pelos que deram certo.

`reconciliacao_execucao` acrescenta a equação de contagem e o confronto
entre as duas gravações:

| Coluna | Significa |
| :--- | :--- |
| `extraidos` | o que a extração relatou no lote |
| `contabilizados` | `carregados + rejeitados + duplicados` |
| `diferenca` | `extraidos - contabilizados` |
| `rejeitados_registrados` | quantas linhas existem de fato em `rejected` |
| `conciliado` | a diferença é zero **e** `rejeitados` bate com `rejeitados_registrados` |

```sql
SELECT run_id, extraidos, contabilizados, diferenca, conciliado
FROM reconciliacao_execucao WHERE NOT conciliado;
```

As duas comparações pegam coisas diferentes, e vale saber qual é qual:

- `extraidos` contra `contabilizados` acusa **lote perdido**. Num lote que
  completou, as duas pontas descendem do mesmo lote em memória e fecham por
  construção; a diferença aparece quando um lote foi revertido e gravou zero
  nas contagens.
- `rejeitados` contra `rejeitados_registrados` confronta **dois caminhos de
  gravação distintos**: o contador do lote, gravado uma vez, contra a lista de
  rejeições, gravada uma linha por ocorrência. Se os dois discordarem, alguma
  rejeição não chegou ao banco — e é essa comparação que faz a conta ser
  verificável em vez de uma identidade que fecha sozinha.

As duas são **views, não tabelas**. Um agregado gravado teria um segundo
escritor e poderia divergir do que a carga registrou lote a lote; derivado, ele
não pode.

Uma execução só aparece aqui se gravou pelo menos um lote: os agregados são
derivados de `_batch_metadata`. Uma execução que morreu antes do primeiro lote
não fica com status `falha` — ela fica ausente. Registrar a execução antes de
haver lote é responsabilidade de quem a orquestra, que é onde o identificador
da execução nasce.

## Compatibilidade com o nome anterior

As tabelas antes se chamavam `<fonte>`, sem prefixo. O contrato cria uma view
com o nome antigo apontando para a tabela nova, com `CREATE VIEW IF NOT EXISTS`
— seguro também em banco anterior à renomeação, onde o nome ainda pertence a
uma tabela. São views **transitórias**, removíveis quando nenhum leitor usar
mais o nome sem prefixo; a condição está registrada na
[ADR 0002](adrs/0002-identidade-e-versoes-na-tabela-de-ingestao.md).

## Acoplamento com a deduplicação

A camada anterior ainda rejeita a correção do parceiro como conflito de
identidade, então a segunda versão de um registro não chega ao banco enquanto
essa classificação não mudar. Quando mudar, a tabela de controle
`_loaded_identity` precisa ser chaveada pela identidade de idempotência na
mesma entrega: caso contrário um reprocessamento explícito classifica versão
antiga como aceita e a carga viola a chave primária. A ADR 0002 registra o
acoplamento, e `tests/load/test_identity_coupling.py` falha se uma das duas
pontas mudar sozinha.

## Manutenção do SQL versionado

O SQL é gerado do contrato executável, e a divergência entre os dois é erro de
build:

```bash
PYTHONPATH=src python scripts/load/render_ddl.py           # regenera o arquivo
PYTHONPATH=src python scripts/load/render_ddl.py --check   # falha se divergir
```

O repositório de carga aplica o mesmo contrato ao abrir a conexão, então o
banco local, o SQL revisado no merge request e o código não podem descrever
estruturas diferentes.

## Testes

```bash
python -m unittest discover -s tests/load -t .
```

A suíte cobre nome físico por fonte, tradução de cada tipo, ausência de
vocabulário do banco anterior, obrigatoriedade dos metadados técnicos e dos
campos obrigatórios, recusa da recarga da mesma versão, recusa da mesma chave
com o mesmo conteúdo, convivência de duas versões com a view devolvendo a mais
recente, e a aplicação do mesmo contrato pelo repositório de carga.

Para as estruturas de controle, cobre o status e as contagens gravadas por
lote, o motivo consultável sem JSON, a convergência do reprocessamento nas duas
tabelas de rejeição, a sobrevivência da execução anterior quando o lote repete
o identificador, o acordo entre a contagem e a listagem de rejeições da mesma
execução, o registro do lote revertido depois do rollback, a diferença que essa
perda produz na reconciliação, e a garantia de que uma falha ao anotar o
histórico não esconde o erro da carga.
