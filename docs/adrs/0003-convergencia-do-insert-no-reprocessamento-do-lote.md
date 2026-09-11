# ADR 0003 — Convergência do insert principal ao reexecutar um lote já carregado

- **Status:** Aceito
- **Data:** 10/09/2026
- **Responsável pela decisão:** responsável pela camada de carga
- **Complementa:** [ADR 0002](0002-identidade-e-versoes-na-tabela-de-ingestao.md)

## Contexto

A carga em lotes (ADR 0001) grava cada lote numa única transação, mas o
insert das linhas aceitas na tabela de ingestão sempre foi um `INSERT INTO`
puro. As tabelas de controle (`rejected`, `rejected_reason`,
`_batch_metadata`, `_loaded_identity`, `_control_object`) já convergem ao
reexecutar — usam `INSERT OR REPLACE`, chaveadas por uma única constraint. A
tabela de ingestão nunca ganhou o mesmo tratamento.

Isso aparece quando um lote **já gravado com sucesso** é reexecutado com o
mesmo `run_id`/`batch_id` — por exemplo, o chamador não confirmou o sucesso
antes de cair, ou uma retomada futura reexecuta uma execução inteira
incluindo lotes que já tinham terminado. Nesse caso, o `INSERT` colide com a
chave primária (`idempotency_key`, ADR 0002) e o lote inteiro falha, em vez de
convergir para o mesmo estado.

Note-se que isto é distinto da deduplicação de linha: uma recarga
idêntica só chega a este ponto quando o `previous` passado à transformação
não reflete o que já está gravado — o que é exatamente o caso de uma
reexecução do mesmo lote, já que o `previous` é lido antes da tentativa
anterior ser conhecida como bem-sucedida.

## Decisão

**O insert das linhas aceitas passa a ter um alvo de conflito explícito na
identidade de idempotência, resolvido com `DO NOTHING`:**

```sql
INSERT INTO "ingestao_<fonte>" (...) VALUES (...)
ON CONFLICT ("idempotency_key") DO NOTHING
```

Testado ao vivo contra um DuckDB real antes de decidir: replicar o padrão das
tabelas de controle (`INSERT OR REPLACE`) falha de imediato nesta tabela,
porque ela tem **duas** constraints de unicidade — a chave primária
(`idempotency_key`) e um `UNIQUE` separado (chave de negócio + conteúdo, ADR
0002) — e o DuckDB recusa resolver o conflito sem que o alvo seja explícito:

```
BinderException: Conflict target has to be provided for a DO UPDATE operation
when the table has multiple UNIQUE/PRIMARY KEY constraints
```

### Por que `DO NOTHING` e não `DO UPDATE`

Testei as duas formas com o alvo explícito; ambas funcionam no DuckDB. A
diferença está no que sobra na linha depois do conflito:

- `DO UPDATE SET coluna = excluded.coluna, ...` sobrescreveria a linha
  existente com os valores da tentativa que chegou por último — inclusive
  `run_id`, `batch_id`, `task_id` e `ingested_at`, que deixariam de refletir
  a execução que gravou a linha pela primeira vez. Também exigiria montar a
  lista de colunas do `SET` dinamicamente, porque cada fonte declara um
  conjunto de colunas diferente.
- `DO NOTHING` não precisa dessa lista e preserva a proveniência de quem
  gravou a linha primeiro. Como a chave em conflito já é a identidade de
  idempotência (chave de negócio + conteúdo, por construção), um conflito
  aqui significa que a mesma versão está sendo reapresentada — não há
  conteúdo novo a absorver, só a tentativa duplicada a descartar.

Selecionada `DO NOTHING`.

## O que isto não resolve

- **Reprocessar sob um `run_id` diferente do original.** Um backfill que
  reintroduz conteúdo idêntico sob um `run_id` novo nem chega a este insert:
  a deduplicação de linha, ao consultar `_loaded_identity`, já
  classifica esse conteúdo como duplicado antes da carga. Este ADR cobre
  apenas o caso em que a mesma tentativa é repetida com o mesmo
  `run_id`/`batch_id`.
- **Aceitar a correção do parceiro como versão nova.** Chave de negócio igual
  com conteúdo diferente continua sendo classificado como conflito de
  identidade na camada de transformação (issue própria, ver ADR 0002) — este
  ADR não muda essa classificação, só o que acontece quando a identidade de
  idempotência já existe.

## Consequências

### Positivas

- Reexecutar um lote já carregado converge: não duplica linha, não derruba o
  lote, não exige que o chamador saiba se a tentativa anterior tinha
  terminado.
- Nenhuma coluna nova, nenhuma migração: a mudança é só na instrução de
  insert do repositório.

### Negativas e riscos

- A camada de carga passa a ter duas semânticas de convergência diferentes
  lado a lado: as tabelas de controle sobrescrevem (`OR REPLACE`), a tabela
  de ingestão preserva a primeira versão (`DO NOTHING`). Um leitor que
  assumir que o comportamento é uniforme entre as tabelas erra a suposição;
  é por isso que a razão de cada uma está registrada aqui.

## Alternativas consideradas

| Alternativa | Avaliação |
| :--- | :--- |
| `INSERT OR REPLACE`, igual às tabelas de controle | Não foi selecionada: falha com `BinderException` nesta tabela, que tem PK e UNIQUE separados. |
| `ON CONFLICT (idempotency_key) DO UPDATE SET ...` | Funciona, mas sobrescreve a proveniência da linha a cada replay e exige montar a lista de colunas por fonte. Não foi selecionada. |
| `ON CONFLICT (idempotency_key) DO NOTHING` | Selecionada. Converge sem sobrescrever proveniência e sem lista de colunas dinâmica. |
