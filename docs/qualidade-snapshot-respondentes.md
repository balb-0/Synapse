# Populações das publicações de qualidade

As tabelas de qualidade medem registros e células tratados; não contam pessoas
e não substituem regras homologadas de completude aplicável. A geração mantém
sete Parquet, com os mesmos nomes e colunas. O escopo de cada publicação é
declarado em `population_scope` no manifesto.

| Publicação | População em origem conciliada |
| :--- | :--- |
| `PUB_QUALIDADE_CAMPO` | Cinco views `ingestao_*_atual` e ocorrências de `respondentes` do snapshot selecionado em C02 |
| `PUB_QUALIDADE_RELACAO` | Filhos nas mesmas populações; pais nas respectivas views atuais; FK nula excluída da base |
| `PUB_QUALIDADE_DUPLICIDADE` | Histórico físico tratado das cinco fontes com chave de negócio declarada; exclui `respondentes` |

## Seleção de respondentes

C02 seleciona a última execução completa e conciliada de `respondentes`, usando
`selected_respondentes`. O relatório analítico conserva o checksum dessa
seleção. `publication_specification` usa o checksum do mesmo relatório para
filtrar os registros de preenchimento e integridade, dentro da transação de
leitura da geração. A qualidade não seleciona outro arquivo por timestamp nem
reexecuta uma regra própria de seleção.

Um arquivo mais novo, mas incompleto ou não conciliado, não substitui o último
snapshot válido. Repetições de participação dentro do arquivo escolhido são
ocorrências legítimas em C02 e continuam na base da qualidade. Linhas de
snapshots anteriores, inclusive seus nulos e órfãos, ficam fora dessas duas
publicações. Elas permanecem na ingestão para auditoria.

Um snapshot vazio completo e conciliado publica bases zero de preenchimento e
integridade de `respondentes`; taxas com denominador zero ficam indisponíveis.
Ausência de snapshot tem `source_unavailable` em C02 e impede uma publicação
conciliada. Não se usa o histórico acumulado como substituto de um arquivo
ausente nem se afirma qualidade de 100% sobre base zero.

O histórico das outras cinco fontes continua em `PUB_QUALIDADE_DUPLICIDADE`.
Sua contagem pode diferir da view atual e dos cubos: ela mede registros
históricos além da primeira chave de negócio. Não muda a população de C01/C02
nem a transforma em contagem de pessoas. O nome de ingestão física aqui não
significa CSV bruto, pois a tabela já contém a transformação aplicada.

## Manifesto, reuso e conferência

Nas publicações de preenchimento e integridade, `population_scope.respondentes`
é `selected_reconciled_c02_snapshot`; `population_scope.other_tables` é
`current_views`. Na duplicidade, `population_scope` é
`physical_ingestion_history`. Os Parquet e esses metadados não expõem o checksum
selecionado, IDs individuais ou credenciais.

Uma fixture sem controles analíticos exige referência `synthetic-...` explícita.
Ela usa suas linhas físicas de `respondentes` e declara
`synthetic_unverified_physical_rows`, sem afirmar seleção conciliada. Qualquer
controle analítico presente exige o schema completo e a reconciliação,
inclusive quando a referência é sintética; um schema parcial não permite esse
fallback.

`publication_report` estabelece o mesmo contexto para o publicador e para
`scripts/analytics/conferir_geracao_bi.py`. O reuso pelo orquestrador e o
conferidor usam a consulta efetiva de `publication_specification`, incluindo os
[marcadores de fechamento vazio de C03](publicacao-c03-fechamentos.md). Conferem
os metadados de escopo com tipos e valores exatos. O conferidor também compara
o conteúdo dos sete Parquet nos dois sentidos com `EXCEPT ALL`, além de
colunas, tipos físicos, hashes e contagens. Isso inclui os recortes de C03,
pois mês e estoque iguais não comprovam que área e perfil são os corretos.
Um hash recalculado sobre valores adulterados não basta para aprovar a geração.

Publicador, conferidor e reuso verificam os tipos físicos contra a consulta
efetiva antes de comparar valores. A coerção do DuckDB pode tornar números
em `VARCHAR`, `DOUBLE` ou `DECIMAL` iguais a inteiros em `EXCEPT ALL`; essa
igualdade não autoriza mudar o schema esperado pelo modelo. O manifesto
conserva seu formato e a lista de nomes de colunas. A versão do manifesto e
do recibo de pacote exige inteiro `1`, rejeitando `true`, `1.0` e `"1"`.

## Verificação reproduzível

```bash
PYTHONPATH=src python -m unittest tests.analytics.test_quality_snapshot tests.analytics.test_conferir_geracao_bi tests.analytics.test_publish tests.analytics.test_fixture_bi tests.orchestration.test_publish_c03_reuse -v
```

Os testes usam DuckDB e publicações isoladas fora do Git. Cobrem duas cargas,
órfãos e nulos somente no arquivo antigo, arquivo mais novo incompleto,
snapshot vazio, fonte ausente, referência sintética, controle analítico
parcial, reuso da geração, escopo adulterado, valores e tipos regravados com
hash novo, recortes C03 alterados sem mudar estoque e versões com tipo incorreto.
O conferidor distingue fechamento C03 vazio de ausência de observação.
Essas verificações não afirmam uma nova execução no Power BI Desktop.
