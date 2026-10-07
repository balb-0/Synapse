# Matriz de regras, testes e rejeições

MG-11, card #180. Escopo: MG-01 a MG-11, transformação essencial anterior à
carga. [Catálogo de campos](catalogo-transformacao.md) e
[contrato de schema](schema-transformacao.md) identificam cada coluna de destino.

## Rastreabilidade

Testes abaixo estão em
[`test_transformation.py`](../tests/transformation/test_transformation.py).
Um registro pode violar várias regras; a contagem de motivos não deve ser
confundida com a quantidade de registros rejeitados.

| Regra | Campos/destino | Teste | Resultado inválido |
| --- | --- | --- | --- |
| R01 schema explícito | 64 campos do catálogo | `test_every_source_and_field_has_destination`, `test_all_six_valid_sources` | `UNKNOWN_SOURCE`, `UNKNOWN_FIELD` |
| R02 renomeação e formato | origem → coluna canônica do catálogo | `test_lists_and_unicode`, `test_input_is_not_mutated` | `INVALID_TEXT`, `FIELD_COLLISION` |
| R03 resíduos vazios | colunas sem nome em pesquisas | `test_unknown_names_collision_and_export_columns` | `NONEMPTY_EXPORT_COLUMN` |
| R04 identidade sem float | todos os campos id | `test_ids_do_not_lose_precision` | `INVALID_ID` |
| R05 precisão e domínio numérico | percentuais, contagens, tempos | `test_finite_precise_numbers`, `test_integer_destination_limits`, `test_negative_counts` | `INVALID_NUMBER`, `DECIMAL_PRECISION`, `PERCENT_RANGE`, `INVALID_INTEGER`, `NEGATIVE_MEASURE` |
| R06 datas e fuso | data_*, hora_* | `test_civil_dates`, `test_timestamp_requires_explicit_timezone`, `test_dst_gap_and_ambiguity`, `test_temporal_consistency` | `INVALID_DATE`, `DATE_RANGE`, `INVALID_DATETIME`, `TIMEZONE_REQUIRED`, `AMBIGUOUS_OR_NONEXISTENT_TIME`, `TEMPORAL_ORDER` |
| R07 sentinelas e presença | campos required/sentinels do catálogo | `test_sentinels_are_field_specific` | `REQUIRED` |
| R08 obrigatoriedade condicional | respostas.valor/alternativa/linha_matriz/coluna_matriz | `test_all_question_types_and_structural_nulls` | `CONDITIONAL_REQUIRED`, `NOT_APPLICABLE`, `INVALID_NUMERIC_ANSWER` |
| R09 grão atômico | pesquisa_id + resposta_id | `test_distinct_answer_elements_are_preserved` | Elementos diferentes permanecem aceitos |
| R10 nenhuma ponte pessoal inferida | respondent_id | `test_orphan_question_and_person_identity` | Não há join respondent_id → cliente_id |
| R10 token externo opaco preservado | respondent_id | `test_response_opaque_identifier_preserves_lexical_value`, `test_response_opaque_identifier_is_still_required`, `test_response_opaque_identifier_does_not_reconstruct_numeric_input` | Texto literal sem reconstrução numérica; ausência rejeitada; não prova identidade pessoal |
| R11 referência explícita | chaves listadas em `RELATIONS` | `test_missing_reference_is_not_empty_reference`, `test_duplicate_reference_rejected`, `test_domain_and_company_mismatch` | `ORPHAN_REFERENCE`, `CLIENT_COMPANY_MISMATCH`; falta do snapshot interrompe o lote |
| R12 duplicação e conflito | record_identity/content_checksum | `test_same_batch_twice_and_after_confirmed_load`, `test_conflicts_have_no_order_winner`, `test_decimal_canonicalization` | `IDENTITY_CONFLICT`; duplicata técnica é contabilizada separadamente |
| R13 participação sem chave de evento | source_checksum + source_offset | `test_participation_occurrences_are_not_collapsed` | Ocorrências diferentes preservadas; mesma ocorrência gera mesma chave |
| R14 quarentena e privacidade | ledger de rejeições | `test_logs_and_quarantine_do_not_contain_raw_values`, `test_quarantine_failure_does_not_consume_batch`, `test_quarantine_rejects_unsafe_paths` | Falha de persistência propagada; checkpoint não confirmado |
| R15 ingestão separada | ingested_at, run_id, batch_id, checksums | `test_configuration_errors_fail_before_processing`, `test_participation_occurrences_are_not_collapsed` | Configuração inválida interrompe o lote |
| R16 compatibilidade | seis schemas + metadados | `test_six_schemas_accept_transformed_rows` em `test_duckdb_contract.py` | Erro real de inserção no DuckDB falha o teste |
| Domínio booleano | empresas.associado | `test_boolean_closed_domain` | `INVALID_BOOLEAN` |
| JSON/listas | questoes.alternativas/linhas_matriz/colunas_matriz | `test_lists_and_unicode` | `INVALID_JSON_LIST`, `EMPTY_LIST_ITEM` |
| Tipo e número de alternativas | questoes.tipo/qtd_alternativas | `test_question_schema_errors`, `test_matrix_count_is_cells_not_alternatives` | `UNKNOWN_QUESTION_TYPE`, `ALTERNATIVE_COUNT_MISMATCH` |
| Alternativa/célula conhecida | respostas.alternativa/linha_matriz/coluna_matriz | `test_domain_and_company_mismatch` | `ANSWER_DOMAIN` |

## Execução reproduzível

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-transformation-dev.txt
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/coverage run --branch --source=etl.transformation -m unittest discover -s tests
.venv/bin/coverage report --fail-under=90
.venv/bin/ruff check --config ruff-transformation.toml src/etl/transformation tests/transformation scripts/transformation
.venv/bin/ruff format --config ruff-transformation.toml --check src/etl/transformation tests/transformation scripts/transformation
PYTHONPATH=src python scripts/transformation/render_schema.py --check
```

O teste de compatibilidade real usa DuckDB em memória, sem Docker ou rede. Ele valida a inserção tipada das seis saídas, incluindo DECIMAL, DATE, TIMESTAMP e listas serializadas como JSON. A persistência, concorrência e orquestração são verificadas nas suítes de carga e orquestração.

## Evidência sobre o snapshot local anterior à v3

Auditoria de transformação, sem carga nem gravação dos registros:

```bash
PYTHONPATH=src python scripts/transformation/audit_sources.py --source-dir /caminho/externo/csv
```

| Fonte | Entrada | Aceitos | Rejeitados | Duplicatas |
| --- | ---: | ---: | ---: | ---: |
| empresas | 779 | 779 | 0 | 0 |
| pesquisas | 366 | 366 | 0 | 0 |
| clientes | 5430 | 5429 | 1 | 0 |
| respondentes | 18735 | 17740 | 995 | 0 |
| questoes | 231 | 187 | 44 | 0 |
| respostas | 20607 | 16903 | 3704 | 0 |

Resultado obtido sem fuso de origem configurado. Os 1.614 motivos
`TIMEZONE_REQUIRED` representam campos, não registros. A política não inventa
o fuso para fazer o dado passar. O script publica hashes dos arquivos para
identificar o snapshot e apenas agregados. A v3 precisa ser validada quando
os novos arquivos forem fornecidos; não extrapolar estes números.

Casos conhecidos incluem pesquisa sem correspondência, cadastro de cliente
incompleto, divergência cliente/empresa e alternativa ausente no domínio.
O teste da matriz foi corrigido com base na exportação: seu número de
alternativas corresponde a linhas × colunas. Referências rejeitadas não são
usadas para legitimar registros filhos. Uma cadeia de rejeição pode, portanto,
produzir vários motivos por resposta.

## Limites para revisão

- Os nomes das tabelas são um contrato para MC-03, não DDLs implantadas.
- `previous` deve vir do estado confirmado da carga. A transformação não
  reserva chaves nem oferece transação distribuída; MC deve controlar
  concorrência e a confirmação de checkpoints.
- O ledger guarda referência para a origem imutável, sem cópia bruta. Seu
  reprocessamento depende da retenção e do acesso restrito ao arquivo original.
- As configurações não homologadas ficam explícitas: fuso, domínio de novas
  categorias, identidade de pesquisas e atualização de participações entre
  snapshots diferentes.
- Revisão por pessoa diferente do autor continua pendente até ocorrer no MR.
  Passar testes ou executar autorrevisão não satisfaz esse item do DoD.
