# Migração das páginas para o projeto Parquet (BI-01)

O projeto a abrir é `powerbi/CentralPesquisasBI.pbip`. Seu relatório usa PBIR
em `CentralPesquisasBI.Report/definition/` e mantém a referência relativa
`../CentralPesquisasBI.SemanticModel`, cujo parâmetro é `PastaPublicacaoBI`.
O `report.json` legado da página vazia foi removido para evitar dois formatos
de definição no mesmo relatório.

## Inventário migrado

| Ordem | Página | ID preservado | Visuais |
| :--- | :--- | :--- | ---: |
| 1 | Produção e Volume | `5d499bb7bb62646ad6e5` | 22 |
| 2 | Benchmark Externo — V2 | `e18bd740de609936581b` | 26 |

A página ativa permanece Benchmark Externo — V2, conforme a origem.
Foram copiados sem alteração os JSON de `definition/` e os recursos de
`StaticResources/` de `src/pbir dash/dashboard.Report/`: tema base
`Fluent2-CY26SU08` e a imagem SVG registrada do Sindusfarma. O tema JSON
externo `Sindusfarma_Acessivel_PowerBI_v2_SegoeUI.json` não é o tema aplicado
na definição de origem; não foi aplicado como parte desta migração.

## Verificação e limite do aceite

```bash
python -m unittest tests.analytics.test_report_definition -v
```

O teste verifica resolução do projeto/modelo, duas páginas ordenadas, IDs,
JSON, tema e recursos existentes. A comparação de arquivos na migração
confirma preservação integral de 53 JSON de definição e dois recursos.
Isso não comprova renderização, refresh, execução de DAX ou instalação do
visual público `htmlContent443BE3AD55E043BF878BED274D3A6855` no Desktop.

Os campos e medidas dos visuais ainda apontam para o modelo antigo.
RP-13 e RP-14 devem adaptar esses vínculos ao contrato publicado, preservando
as páginas. Erros de visual nessa etapa não são evidência de falha de
importação das sete tabelas; BI-02 verifica as consultas separadamente.
Até essas adaptações e a execução em Windows, o relatório não tem aceite
funcional das páginas.
