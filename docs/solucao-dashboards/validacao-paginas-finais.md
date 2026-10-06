# Validação das páginas finais (RP-17, issue #322)

Percorrido estático das três páginas finais do relatório
`powerbi/CentralPesquisasBI.Report/definition/` sobre o modelo Parquet,
com vínculos de filtros e drill conferidos pela definição PBIR. Evidência
reproduzível: `tests/analytics/test_report_semantics.py`,
`tests/analytics/test_report_bindings.py`, `test_report_filters.py` e
`test_report_definition.py` — a suíte estática pode ser executada com:
`PYTHONPATH=src python -m unittest tests.analytics.test_report_semantics tests.analytics.test_report_bindings tests.analytics.test_report_filters tests.analytics.test_report_definition -v`.
A conferência técnica histórica de refresh, consultas e capturas do pacote integrado no
Power BI Desktop foi registrado em 2026-10-06; a evidência e seus limites
estão descritos abaixo. As sessões humanas S1–S4 e a revisão externa de Anna
continuam pendentes.

As capturas são do snapshot anterior ao CF-05. As mudanças de C03 e
completude após esse pacote ainda exigem nova rodada Desktop; o aceite
final atual permanece pendente.

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

## Aceite técnico no Power BI Desktop

O root confirmou o aceite técnico do pacote integrado. O pacote tem SHA-256
`a9b087e5a9e4e0d56af8d7b36fe0a687857b205e7c59b6dbd44c9dd7c2358cea` e foi
gerado a partir do commit `ff760d6552a1d5d2d3d9d9da1f3467e2c913416a`, que
contém o tip RP17 `94e91ef5e9c009a162b02c1986a8ce8b60628e8b`. A definição
mantém três páginas e 69 visuais (22 + 26 + 21). O recibo de contagens v3
registra execução real no Analysis Services local do Power BI Desktop em
2026-10-06 15:49 UTC, geração `6b1eaa686aac43b18b6d6545e1c2c5f1`, com
partições processadas sem erro e projeção semântica do modelo compatível com
os 128 itens do PBIP (zero diferenças). As consultas registraram:

| Cubo | Linhas | Conferência no Desktop |
| :-- | --: | :-- |
| `PUB_C01_CICLO` | 57 | `SUM(qtd_pesquisas) = 366` |
| `PUB_C02_PARTICIPACAO` | 32 | `SUM(qtd_participacoes) = 17.740` |
| `PUB_C03_PIPELINE_MENSAL` | 0 | Sem fechamento observado na geração v3; estoque fica sem dado, não zero |
| `PUB_C04_INSTRUMENTO` | 45 | `SUM(qtd_perguntas) = 3.186` |

O recibo da fixture de validação, geração `2c699f0b066847ee8559f1e31d88f49d`,
é sintético e confirma o estoque observado de 3 em 31/01/2026 e 4 em
28/02/2026. As capturas mostram o aviso sem dado de C01, os eixos de contagem
de C02 e o eixo categórico mensal de C03. C01, C02 e C03/C04 vieram da fixture
sintética; somente o resumo v3 está marcado como captura não sintética. Os
recibos sanitizados de contagem estão em [BI-02 (fixture)](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/blob/30d692c163cf996b7b1fd9c4a2501fcf19e534de/docs/evidencias/bi02/desktop-fixture-corrigido-final.json)
e [BI-05 (v3)](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/blob/30d692c163cf996b7b1fd9c4a2501fcf19e534de/docs/evidencias/bi05/desktop-v3-final.json),
com a conferência em [BI-05](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/blob/30d692c163cf996b7b1fd9c4a2501fcf19e534de/docs/evidencias/bi05/conferencia-desktop-v3-final.json).
O [índice de capturas BI-06](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/blob/30d692c163cf996b7b1fd9c4a2501fcf19e534de/docs/evidencias/bi06/capturas-finais.json)
e a [validação de acesso BI](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/blob/30d692c163cf996b7b1fd9c4a2501fcf19e534de/docs/validacao-acesso-bi.md)
foram publicados na [MR !292](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/merge_requests/292).
As telas podem ser consultadas diretamente: [C01](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/blob/30d692c163cf996b7b1fd9c4a2501fcf19e534de/docs/evidencias/bi06/final-fixture-c01.png),
[C02](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/blob/30d692c163cf996b7b1fd9c4a2501fcf19e534de/docs/evidencias/bi06/final-fixture-c02.png),
[C03/C04](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/blob/30d692c163cf996b7b1fd9c4a2501fcf19e534de/docs/evidencias/bi06/final-fixture-c03-c04.png)
e o [resumo v3](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/blob/30d692c163cf996b7b1fd9c4a2501fcf19e534de/docs/evidencias/bi06/final-v3-summary.png).

Limite do recibo v3: ele confirma o hash do pacote e a projeção semântica do
modelo (`engine_semantic_projection_verified=true`), mas não verifica a
revisão Git carregada pelo engine (`engine_loaded_revision_verified=false`).
O aceite técnico não equivale às sessões humanas S1–S4: navegação manual,
filtros simultâneos, drill e percepção de latência ainda aguardam execução
humana. A revisão independente de Anna também permanece externa.

**Resposta (proxy estático):** 76 JSON de definição válidos e 69 visuais
(22 + 26 + 21); nenhuma medida com agregação ambígua nos vínculos. As telas
e os recibos não substituem a revisão externa nem as sessões humanas.

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

## Achado da revisão — encerrado após a validação BI-04

A suspeita anterior de parêntese ausente não se reproduz na definição
integrada: `Base Valida Duplicidade` está definida como
`SUM(PUB_QUALIDADE_DUPLICIDADE[qtd_linhas])`, com a expressão fechada. A
validação de medidas BI-04 foi executada no Power BI Desktop; o recibo v3
registra refresh sem erro e duplicidade conferida em 275.840 linhas e
275.840 chaves distintas (taxa 0). O resultado independente está marcado
`matched_independent_aggregate_reference`; a projeção TOM corresponde a 128
itens, sem diferenças. A suspeita fica resolvida, sem ação pendente para
BI-04.

Fontes: [TMDL integrado no pacote RP17](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/blob/ff760d6552a1d5d2d3d9d9da1f3467e2c913416a/powerbi/CentralPesquisasBI.SemanticModel/definition/tables/PUB_QUALIDADE_DUPLICIDADE.tmdl),
[validação de medidas BI-04](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/merge_requests/290),
[recibo Desktop v3 BI-04](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/blob/30d692c163cf996b7b1fd9c4a2501fcf19e534de/docs/evidencias/bi04/desktop-medidas-v3-final.json)
e [relatório BI-04](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/pipelines/88562).
