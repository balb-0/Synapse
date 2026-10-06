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

## Execução com o conjunto autorizado

Em 2026-10-06, a rotina acima foi executada em `data/duckdb/cb13-v3-analitico.duckdb`, cópia local e ignorada pelo Git de `data/duckdb/real_warehouse_fast4.duckdb`. O banco original e os CSVs do parceiro foram lidos sem alteração. Os objetos de controle das cinco fontes consumidas pela carga (`pesquisas`, `empresas`, `clientes`, `questoes` e `respondentes`) têm SHA-256 correspondente aos respectivos CSVs de `Central de Pesquisas - MD11 ES v3/`. O snapshot de `respondentes` foi considerado elegível pela rotina.

- `load_id`: `65d139e0-488d-4601-9361-ae153731145c`.
- `loaded_at` no DuckDB: `2026-10-06 20:32:49` (horário local).
- O relatório de reconciliação retornou `source_digests_match=true` e `reconciled=true`; C01, C02 e C04 não tiveram chaves faltantes, inesperadas ou descartes. Não houve vínculos órfãos registrados. O resultado `reconciled=true` atesta a consistência da carga disponível, sem transformar C03 em mês observado.

| Cubo e fato | Fonte elegível | Linhas no fato | Cobertura observada |
| --- | ---: | ---: | --- |
| C01 — `FATO_CICLO_PESQUISA` | 366 pesquisas | 366 | 366/366 pesquisas; duração de validação 20/366, coleta 358/366, tabulação 330/366 e ciclo total 331/366. |
| C02 — `FATO_PARTICIPACAO` | 17.740 ocorrências de respondentes | 17.740 | 17.740/17.740 ocorrências; vínculo de pesquisa 17.740/17.740, pessoa 16.883/17.740 e data da pesquisa 17.601/17.740. `hora_inicio` e `hora_termino` estão ausentes nas 17.740 linhas de origem; data da resposta e minutos de preenchimento têm cobertura 0/17.740. |
| C03 — `FATO_PIPELINE_MENSAL` | Nenhum fechamento mensal observado | 0 | **Bloqueado para cobertura mensal:** nenhum registro em `analytics_pipeline_closure`. Status `not_observed`; zero linhas não representa estoque zero. |
| C04 — `FATO_PESQUISA_PERGUNTA` | 3.186 questões | 3.186 | 3.186/3.186 pares pesquisa–pergunta, todos vinculados por ID; data da pesquisa 3.158/3.186. |

O pacote autorizado contém também `respostas.csv`, mas `ingestao_respostas_atual` está vazia **nesta cópia local**. A rotina C01–C04 não lê essa fonte; portanto esta execução não comprova cobertura de respostas nem autoriza indicadores derivados delas. A publicação de qualquer medida dependente de respostas fica bloqueada até que essa fonte esteja carregada e conciliada.

O parceiro disponibilizou apenas este retrato da base, sem uma observação do estado no fim de um mês. Assim, C03 permanece bloqueado por falta dessa fonte temporal; recarregar o mesmo retrato não resolve a cobertura. Quando houver um fechamento mensal efetivamente observado e autorizado, ele poderá ser registrado com `--observed-at`. Não se deve atribuir ao retrato atual uma data histórica presumida.
