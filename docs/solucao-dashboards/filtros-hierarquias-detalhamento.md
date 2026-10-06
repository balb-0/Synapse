# Filtros, hierarquias e detalhamento suportados (RP-16, issue #321)

Drill por tempo, área e tipo onde o agregado publicado permite; nenhum
drill-through promete Chave individual (pesquisa/empresa/pessoa) ausente dos
sete Parquet. Verificação reproduzível: `tests/analytics/test_report_filters.py`.

## Filtros por página (slicers ligados a DIM_*/PUB_*)

| Página | Slicer | Entidade vinculada | Suporte |
| :-- | :-- | :-- | :-- |
| Produção e Volume | Área | `DIM_AREA.area` | Total; filtra `PUB_C01_CICLO` |
| Produção e Volume | Tipo | `DIM_TIPO_PESQUISA.tipo` | Total |
| Produção e Volume | Status | `DIM_STATUS_PESQUISA.status` | Total |
| Produção e Volume | Ano | `DIM_INDICADORES_BLOQUEADOS.motivo` | Sem dado: `ano_edicao` sem origem homologada — exibe motivo, não filtra |
| Produção e Volume | Complexidade | `DIM_INDICADORES_BLOQUEADOS.motivo` | Sem dado em C01 (`complexidade` só existe em `PUB_C03`) |
| Benchmark Externo — V2 | Área | `DIM_AREA.area` | Total |
| Benchmark Externo — V2 | Tipo | `DIM_TIPO_PESQUISA.tipo` | Total |
| Benchmark Externo — V2 | Ano | `DIM_TEMPO.ano` | Deriva do mês observado de C02 |
| Benchmark Externo — V2 | Empresa | `DIM_INDICADORES_BLOQUEADOS.motivo` | Sem dado: empresa nominal não publicada (I07) |
| Benchmark Externo — V2 | Pesquisa | `DIM_INDICADORES_BLOQUEADOS.motivo` | Sem dado: pesquisa nominal não publicada |
| Estoque e Qualidade | Status | `DIM_STATUS_PESQUISA.status` | Total; filtra `PUB_C03` |
| Estoque e Qualidade | Área | `DIM_AREA.area` | Total |
| Estoque e Qualidade | Mês | `DIM_TEMPO.ano_mes` | Meses observados em C02 ou C03; sem linha C03 no mês, o estoque fica indisponível |

Filtros simultâneos propagam da dimensão para o fato em direção única,
conforme `docs/relacionamentos-modelo-bi.md`; cruzamento entre fatos só por
dimensão conformada.

## Hierarquias e drill

| Hierarquia (modelo) | Níveis | Uso nas páginas |
| :-- | :-- | :-- |
| `DIM_TEMPO.Calendario` | Ano → Trimestre → Mês | Benchmark (mês de resposta) e Qualidade (mês de fechamento); Produção e Volume não tem eixo de tempo publicado — sem drill temporal nessa página |
| `PUB_C03_PIPELINE_MENSAL.'Area, Tipo e Perfil'` | Área → Tipo → Perfil | Página Estoque e Qualidade (tabela de estoque) |
| Área → Tipo (C01/C02) | Área → Tipo | Produção (barras) e Benchmark (barras por área) |

Regras de detalhamento: drill desce só até o grão publicado; a medida de
estoque é semiaditiva (não somar entre meses); médias de duração e de
preenchimento exigem denominador positivo (`qtd_*_disponivel`); denominador
zero ou mês sem snapshot → "indisponível", nunca zero. Não há página de
drill-through para pesquisa/empresa/pessoa — a verificação
`test_no_drillthrough_to_individual_keys` reprova qualquer configuração que
prometa essas chaves.
