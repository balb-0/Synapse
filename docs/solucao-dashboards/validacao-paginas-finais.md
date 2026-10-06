# Validação das páginas finais (RP-17, issue #322)

Percorrido estático das três páginas finais do relatório
`powerbi/CentralPesquisasBI.Report/definition/` sobre o modelo Parquet,
com filtros simultâneos e drill conferidos por vínculo (sem Desktop neste
checkout). Evidência reproduzível: `tests/analytics/test_report_bindings.py`,
`test_report_filters.py` e `test_report_definition.py` (10 testes, todos
verdes em `PYTHONPATH=src python -m unittest`).

## Percorrido por página (filtros simultâneos + drill)

| Página | Filtros percorridos | Drill | Resultado |
| :-- | :-- | :-- | :-- |
| Produção e Volume | Área × Tipo × Status (`DIM_*` → `PUB_C01_CICLO`, direção única) | Área → Tipo no agregado; sem eixo de tempo publicado | OK estático; cards usam `Qtd Pesquisas` e médias com denominador `qtd_*_disponivel` |
| Benchmark Externo — V2 | Área × Tipo × Ano (`DIM_TEMPO.ano` do mês observado) | Área → Tipo; Ano → (mês de resposta) | OK estático; sem seleção de empresa/pesquisa — comparações só por área/tipo/mês |
| Estoque e Qualidade (C03/C04) | Status × Área × Mês (`DIM_*` → `PUB_C03`) | `Area, Tipo e Perfil`; tempo até o mês observado (sem soma entre meses) | OK estático; Status/Mês afetam só C03 — C04 e qualidade exibem escopo global (sem relacionamento, por desenho) |

Sem-dado explícito em todas as páginas (motivo textual, nunca zero):
prorrogação/I05, `ano_edicao`, complexidade em C01, empresa/pesquisa
nominal e I07/I09, entradas/saídas de C03, I19/I20. Nenhum visual vincula
entidade ou coluna de grão individual (`D01_*/D02_*/D03_*/D04_*/BE_*`,
`título`, `flag_prorrogada`); nenhum drill-through promete essas chaves.

## Comparação com BI-05 e resposta

- **Valores × BI-05**: pendente — o ramo de BI-05 (`test-315-…`) ainda não
  tem refresh registrado neste checkout e não há geração real autorizada
  aqui. Roteiro para o ambiente Windows autorizado: abrir
  `powerbi/CentralPesquisasBI.pbip`, ajustar `PastaPublicacaoBI` para a
  geração de CB-16, atualizar, conferir `SUM(qtd_pesquisas)` de `PUB_C01`,
  `SUM(qtd_participacoes)` de `PUB_C02`, estoque do último mês de `PUB_C03`
  e `SUM(qtd_perguntas)` de `PUB_C04` contra o manifesto e o DuckDB, e
  repetir o percorrido acima com filtros simultâneos.
- **Resposta (proxy estático)**: 76 JSON de definição válidos; 22 + 26 + 21
  visuais; nenhuma medida com agregação ambígua nos vínculos. Tempo de
  resposta no Desktop deve ser medido no ambiente autorizado (roteiro acima)
  — meta: navegação e drill sem erro impeditivo de leitura.

## Erros impeditivos encontrados e corrigidos

1. Filtro visual `flag_prorrogada = TRUE` (D01) persistido na tabela de
   prorrogação — removido; visual agora sinaliza I05 sem dado.
2. Seleção padrão de empresa demo (`'Empresa sintética 02 [EMP-002]'`)
   persistida no slicer de empresa — removida; slicer sinaliza sem dado.
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
7. (Revisão) Card de estoque usa a medida `Estoque no Status`, que mostra o
   último fechamento observado no contexto; o rótulo agora informa esse recorte.

## Achado repassado (fora do escopo RP, para BI-04)

- `PUB_QUALIDADE_DUPLICIDADE.'Base Valida Duplicidade'` está com parêntese
  de fechamento ausente no TMDL (`SUM(...qtd_linhas)` sem `)`), o que pode
  quebrar o refresh. Não corrigido aqui por pertencer à frente de medidas
  (BI-04/Marlos) — fica o registro para correção e revalidação no Desktop.
