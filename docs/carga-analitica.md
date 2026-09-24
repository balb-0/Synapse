# Carga analítica dos cubos C01–C04

Execute sobre um DuckDB que já tenha o DDL de ingestão tratada, as seis tabelas e as views `*_atual`, `_control_object`, `_batch_metadata` e `reconciliacao_execucao`. A rotina cria as dimensões e fatos analíticos na mesma transação em que carrega os dados. Não lê `respostas`: `respondent_id` não está conciliado com `cliente_id`.

```bash
PYTHONPATH=src python -m etl.analytics.load caminho/para/banco.duckdb
```

Para registrar um **fechamento observado** de C03, informe um instante no último dia do mês. Uma carga comum não produz meses históricos. O instante precisa corresponder a uma observação real da origem naquele fechamento; a opção não reconstrói estados passados.

```bash
PYTHONPATH=src python -m etl.analytics.load caminho/para/banco.duckdb \
  --observed-at 2026-09-30T23:00:00
```

Também é possível chamar `load_analytics(con, observed_at=...)` com uma conexão DuckDB aberta. O chamador mantém a conexão; a rotina controla `BEGIN`, `COMMIT` e `ROLLBACK`. Uma exceção reverte DDL e dados da carga. Não chame com uma transação externa aberta.

## Seleção e convergência

- C01, dimensões e C04 seguem as views de versão atual. A versão corrigida substitui os fatos correntes na próxima carga.
- Em C02, `sk_data_pesquisa` é a data de divulgação da pesquisa vinculada e `sk_data_resposta` é a data de `hora_inicio`; `hora_termino` serve apenas para a duração. Em C04, `sk_data_pesquisa` é a data de divulgação da pesquisa vinculada, inclusive por título único. Sem vínculo ou data, o papel opcional fica `NULL`.
- C02 usa apenas as ocorrências físicas do `source_checksum` de `respondentes` com objeto de controle e execução concluída, conciliada e sem lote falho. A ordenação é `concluded_at DESC, source_checksum DESC`. Sem arquivo elegível, a carga preserva o último C02 publicado. Repetir o mesmo arquivo converge para as mesmas chaves `(source_checksum, source_offset)`.
- C03 recebe somente uma observação explícita de fim de mês. `analytics_pipeline_closure` registra o fechamento mesmo quando o estoque observado é zero. O fato e `analytics_pipeline_membership` são substituídos juntos se a observação for mais recente que a registrada para aquele mês. O ledger mantém as chaves das pesquisas e grupos vistos no fechamento; alterações posteriores em C01 não reescrevem meses anteriores. Entradas e saídas ficam `NULL`, pois não há transições observadas.
- `analytics_reconciliation` registra vínculos órfãos de C02 e C04, com fonte, ID de origem, dimensão alvo e motivo. Para C04, o ID de origem é o par JSON `[pesquisa_id, pergunta_id]`. Uma questão pode usar pesquisa por título normalizado exato e único, com método `titulo_exato_unico`, ID original e ID de destino. Ambiguidade mantém a chave desconhecida.
- `analytics_load_run` registra um UUID da carga, instante, SHA-256 dos IDs técnicos das quatro views correntes e checksum selecionado de respondentes. `LoadResult.load_id` identifica a linha. `current_source_digests(con)` recalcula os quatro fingerprints para verificar se a origem corrente ainda corresponde à carga. O manifesto é inserido na mesma transação dos fatos.

As dimensões têm uma linha desconhecida por contrato. Ausência estrutural em FK opcional continua `NULL`; órfão usa a chave desconhecida. A tabela de reconciliação é uma fotografia da carga corrente, enquanto o ledger C03 é histórico. Os atributos de cargo e departamento ficam apenas no banco interno, sem publicação externa automática.
