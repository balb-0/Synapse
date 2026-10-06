# Filtros, hierarquias e detalhamento suportados (RP-16, issue #321)

Os dados de C02 têm grão mensal por área e tipo (`PUB_C02_PARTICIPACAO`);
empresa distinta por pesquisa e pesquisa individual não são publicadas. Esses
dois valores aparecem como avisos de texto e não filtram o relatório. Drill por
tempo, área e tipo ocorre onde o agregado publicado permite; nenhum
drill-through promete Chave individual (pesquisa/empresa/pessoa) ausente dos
sete Parquet. Verificação reproduzível: `tests/analytics/test_report_filters.py`.

## Filtros por página (slicers ligados a DIM_*/PUB_*)

| Página | Slicer ou aviso | Entidade vinculada | Suporte |
| :-- | :-- | :-- | :-- |
| Produção e Volume | Área | `DIM_AREA.area` | Total; filtra `PUB_C01_CICLO` |
| Produção e Volume | Tipo | `DIM_TIPO_PESQUISA.tipo` | Total |
| Produção e Volume | Status | `DIM_STATUS_PESQUISA.status` | Total |
| Produção e Volume | Ano | `DIM_INDICADORES_BLOQUEADOS.motivo` | Sem dado: `ano_edicao` sem origem homologada — exibe motivo, não filtra |
| Produção e Volume | Complexidade | `DIM_INDICADORES_BLOQUEADOS.motivo` | Sem dado em C01 (`complexidade` só existe em `PUB_C03`) |
| Participação agregada (C02) | Área | `DIM_AREA.area` | Total |
| Participação agregada (C02) | Tipo | `DIM_TIPO_PESQUISA.tipo` | Total |
| Participação agregada (C02) | Ano | `DIM_TEMPO.ano` | Deriva do mês de resposta observado em C02 |
| Participação agregada (C02) | Aviso de empresa distinta por pesquisa (texto) | — | Indisponível: C02 não publica empresa distinta por pesquisa (I07); o aviso não filtra |
| Participação agregada (C02) | Aviso de pesquisa individual (texto) | — | Indisponível: C02 não publica identificador de pesquisa individual; o aviso não filtra |
| Estoque e Qualidade | Status | `DIM_STATUS_PESQUISA.status` | Total; filtra `PUB_C03` |
| Estoque e Qualidade | Área | `DIM_AREA.area` | Total |
| Estoque e Qualidade | Mês | `DIM_TEMPO.ano_mes` | Meses observados em C02 ou C03; sem linha C03 no mês, o estoque fica indisponível |

Filtros simultâneos propagam da dimensão para o fato em direção única,
conforme `docs/relacionamentos-modelo-bi.md`; cruzamento entre fatos só por
dimensão conformada.

## Hierarquias e drill

| Hierarquia (modelo) | Níveis | Uso nas páginas |
| :-- | :-- | :-- |
| `DIM_TEMPO.Calendario` | Ano → Trimestre → Mês | Participação agregada (mês de resposta C02) e Qualidade (mês de fechamento); Produção e Volume não tem eixo de tempo publicado — sem drill temporal nessa página |
| `PUB_C03_PIPELINE_MENSAL.'Area, Tipo e Perfil'` | Área → Tipo → Perfil | Página Estoque e Qualidade (tabela de estoque) |
| Área → Tipo (C01/C02) | Área → Tipo | Produção (barras) e Participação agregada (barras por área) |

Regras de detalhamento: drill desce só até o grão publicado; a medida de
estoque é semiaditiva (não somar entre meses); médias de duração e de
preenchimento exigem denominador positivo (`qtd_*_disponivel`); denominador
zero ou mês sem snapshot → "indisponível", nunca zero. Não há página de
drill-through para pesquisa/empresa/pessoa — a verificação
`test_no_drillthrough_to_individual_keys` reprova qualquer configuração que
prometa essas chaves.
