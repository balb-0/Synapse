# Validação das páginas finais (RP-17, issue #322)

Percorrido estático das três páginas finais do relatório
`powerbi/CentralPesquisasBI.Report/definition/` sobre o modelo Parquet,
com vínculos de filtros e drill conferidos pela definição PBIR. Evidência
reproduzível: `tests/analytics/test_report_semantics.py`,
`tests/analytics/test_report_bindings.py`, `test_report_filters.py` e
`test_report_definition.py` — 23 testes passam com:
`PYTHONPATH=src python -m unittest tests.analytics.test_report_semantics tests.analytics.test_report_bindings tests.analytics.test_report_filters tests.analytics.test_report_definition -v`.
A atualização e a validação runtime no Desktop continuam pendentes, conforme
a fronteira abaixo.

## Percurso estático por página (filtros simultâneos + drill)

| Página | Filtros percorridos | Drill | Resultado |
| :-- | :-- | :-- | :-- |
| Produção e Volume | Área × Tipo × Status (`DIM_*` → `PUB_C01_CICLO`, direção única) | Área → Tipo no agregado; sem eixo de tempo publicado | OK estático; KPI usa `Qtd Pesquisas`, sem alegar taxa de finalização; avisos de ano/complexidade não filtram |
| Participação agregada (C02) | Área × Tipo × Ano (`DIM_TEMPO.ano` do mês observado) | Área → Tipo; Ano → (mês de resposta) | OK estático; sem seleção de empresa/pesquisa — comparações só por área/tipo/mês |
| Estoque e Qualidade (C03/C04) | Status × Área × Mês (`DIM_*` → `PUB_C03`) | `Area, Tipo e Perfil`; tempo até o mês observado (sem soma entre meses) | OK estático; Status/Mês afetam só C03 — C04 e qualidade exibem escopo global (sem relacionamento, por desenho) |

Sem-dado explícito em todas as páginas (motivo textual, nunca zero):
prorrogação/I05, `ano_edicao`, complexidade em C01, empresa/pesquisa
nominal e I07/I09, entradas/saídas de C03, I19/I20. Nenhum visual vincula
entidade ou coluna de grão individual (`D01_*/D02_*/D03_*/D04_*/BE_*`,
`título`, `flag_prorrogada`); nenhum drill-through promete essas chaves.

## Fronteira de validação

- **Refresh e valores no Desktop: pendentes.** O pacote integrado regenerado
  ainda precisa ser reaberto no Power BI Desktop no ambiente autorizado. Até
  essa reabertura, esta evidência não comprova refresh, valores, interação de
  filtros, drill em execução nem tempo de resposta.
- Após reabrir `powerbi/CentralPesquisasBI.pbip` com a publicação corrigida
  `fixture2c699`,
  atualizar as fontes e conferir `SUM(qtd_pesquisas)` de `PUB_C01`,
  `SUM(qtd_participacoes)` de `PUB_C02`, o estoque do último mês de `PUB_C03`
  e `SUM(qtd_perguntas)` de `PUB_C04` contra o manifesto e o DuckDB; então
  repetir o percurso acima com filtros simultâneos.
- **Resposta (proxy estático):** 76 JSON de definição válidos e 69 visuais
  (22 + 26 + 21); nenhuma medida com agregação ambígua nos vínculos. O tempo
  de resposta no Desktop continua pendente, com meta de navegação e drill sem
  erro impeditivo de leitura.

## Erros impeditivos encontrados e corrigidos

1. Filtro visual `flag_prorrogada = TRUE` (D01) persistido na tabela de
   prorrogação — removido; visual agora sinaliza I05 sem dado.
2. Seleção padrão de empresa demo (`'Empresa sintética 02 [EMP-002]'`)
   persistida no slicer de empresa — removida; a ausência de empresa e
   pesquisa individual agora aparece como texto e não filtra a página.
3. Metadados de série (`metadata`) e ordenações apontando para medidas
   antigas — reescritos para as medidas Parquet em todos os gráficos.
4. Slicers de Mês/Status da página 3 não alcançam `PUB_C04` (sem
   relacionamento, por desenho) — documentado o escopo global de C04 e
   qualidade nessa página em vez de prometer filtragem.
5. (Revisão) Card de Produção exibia o mesmo `Qtd Pesquisas` 3× com rótulos
   distintos (Pesquisas/Finalizadas/Em Aberto) — trocado por total, média
   de ciclo, base válida e média de coleta; `pvline` rel rotulado como base
   da taxa; o recorte Finalizadas × Em Aberto fica no gráfico por status.
6. (Revisão) KPIs 1 e 3 do Benchmark exibiam o mesmo valor com rótulos
   sinônimos — kpi3 agora mostra média de preenchimento.
7. (Revisão) O KPI de estoque identifica o último fechamento observado; o
   gráfico mensal não sugere divisão por status, pois status é filtro da página.
8. (Revisão) O KPI de C01 usa `Qtd Pesquisas` e o rótulo `Pesquisas no recorte`;
   a taxa de finalização é explicitamente indisponível. Ano de edição e
   complexidade aparecem como avisos, sem controles de filtro.
9. (Revisão) C02 é rotulado como agregado por área, tipo e mês; contagem de
   ocorrências não compartilha eixo com minutos, que permanecem no KPI de
   média. O catálogo de bloqueios não aparece como filtro.
10. (Revisão) Os títulos de C03/C04 agora refletem tipo de pergunta, medidas
    de qualidade e estoque e o grão de cada tabela; o filtro de tempo chama-se
    `Mês`, pois a dimensão reúne C02 e C03.

## Achado repassado (fora do escopo RP, para BI-04)

- `PUB_QUALIDADE_DUPLICIDADE.'Base Valida Duplicidade'` está com parêntese
  de fechamento ausente no TMDL (`SUM(...qtd_linhas)` sem `)`), o que pode
  quebrar o refresh. Não corrigido aqui por pertencer à frente de medidas
  (BI-04/Marlos) — fica o registro para correção e revalidação no Desktop.
