# Contrato físico das tabelas de ingestão tratada

As tabelas de ingestão são o destino do fluxo
`Fonte → Extração → Transformações essenciais → Tabela de ingestão`. Este
documento registra o contrato físico dessas tabelas no DuckDB: nome, tipo,
constraints, metadados técnicos e as views de estado atual.

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
- como o SQL versionado é mantido em sincronia com o contrato.

## Fora de escopo

- **Definir as tabelas de execução, rejeição e reconciliação.** O SQL
  versionado carrega as tabelas de controle já usadas pela carga para que o
  arquivo descreva o banco inteiro, mas a formalização dessas estruturas —
  status, contagens e motivos — pertence à etapa seguinte da camada de carga.
- **Carregar lotes.** Escrita em lotes, serialização do acesso de escrita e
  contagens confirmadas pelo banco pertencem ao repositório de carga.
- **Migrar schema existente.** O contrato usa `CREATE TABLE IF NOT EXISTS`, que
  cria o que falta e não altera o que existe. Detectar campo incompatível,
  bloquear a carga e versionar a alteração é a etapa do gate de compatibilidade.
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
