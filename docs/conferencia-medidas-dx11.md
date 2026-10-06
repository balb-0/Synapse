# Conferência das medidas contra a apuração de referência

Cumpre a DX-11: confere cada medida publicada contra os valores já apurados
(`docs/resultados_analise.txt`, `docs/dmc.md`), com o resultado anexado —
automatizado onde há referência numérica fixa, documentado como checklist
manual onde não há.

## Conferência automatizada

[`scripts/analytics/conferir_medidas_bi.py`](../scripts/analytics/conferir_medidas_bi.py)
recalcula, a partir dos Parquet de uma geração publicada
(`docs/acesso-cubos-bi.md`), três valores de referência numérica registrados
na Sprint 2, com uma implementação independente da consulta de `publish.py`.
Esses números pertencem a um snapshot histórico: valor diferente, inclusive
maior, não passa automaticamente como crescimento legítimo nem reprova sozinho
a população atual. O script marca qualquer divergência ou arquivo ausente como
não validado e encerra com código 1; para aceitar uma geração nova, compare-a
com a carga DuckDB reconciliada da mesma geração. Igualdade com uma referência
antiga também não substitui essa reconciliação de identidades.

| Medida | Referência | Fonte |
| :-- | :-- | :-- |
| `Qtd Pesquisas` | 366 | `docs/resultados_analise.txt`, T1 |
| `Base Valida Validacao` | 20 (cobertura bruta histórica de `data_aprov`; não é limite da geração atual) | `docs/resultados_analise.txt`, T1 |
| `Qtd Participacoes` | ≈18.735 | `docs/dmc.md`, seção 3.2 |

Rodar contra uma geração real:

```bash
PYTHONPATH=src python -m scripts.analytics.conferir_medidas_bi \
  --geracao /caminho/privado/publicacao-bi/GERACAO
```

Nenhuma diferença para cima é considerada prova de atualização legítima: linhas
duplicadas também podem aumentar o agregado. A suíte
[`scripts/analytics/test_conferir_medidas_bi.py`](../scripts/analytics/test_conferir_medidas_bi.py)
verifica igualdade histórica, divergência para cima/baixo e arquivo ausente com
Parquet sintético — sem depender de acesso ao DuckDB privado, que este
repositório não versiona.

**Resultado anexado (a preencher por Anna ao rodar contra uma geração
real):**

| Medida | Valor publicado | Valor de referência | Status |
| :-- | :-- | :-- | :-- |
| `Qtd Pesquisas` | _(rodar o script)_ | 366 | _(rodar o script)_ |
| `Base Valida Validacao` | _(rodar o script)_ | 20 | _(rodar o script)_ |
| `Qtd Participacoes` | _(rodar o script)_ | 18735 | _(rodar o script)_ |

## Checklist manual — medidas sem referência numérica fixa

As demais medidas de DX-07, DX-08 e DX-09 não têm um número pré-calculado
equivalente no material da Sprint 2 (os levantamentos anteriores não
segmentavam por área/status/tipo nem mediam qualidade por campo/relação).
Para cada uma, a conferência é contra uma consulta direta ao DuckDB de
origem no mesmo recorte — que só quem tem acesso ao banco privado pode
rodar. Tabela de apoio:

| Medida | Consulta de conferência direta |
| :-- | :-- |
| `Media Dias Validacao/Coleta/Tabulacao/Ciclo Total` | Mesma fórmula da medida (`docs/medidas-portfolio-ciclo.md`) rodada como `SELECT AVG(...)` sobre `ingestao_pesquisas_atual`, filtrando o mesmo par de datas válido. |
| `Media Minutos Preenchimento` | Idem, sobre `ingestao_respondentes`. |
| `Qtd Perguntas` | `SELECT tipo, COUNT(*) FROM ingestao_questoes_atual GROUP BY tipo` comparado à saída de `PUB_C04_INSTRUMENTO`. |
| `Completude`, `Integridade Referencial`, `Taxa de Duplicidade` | Rodar `scripts/data_quality/valida_kpis_qualidade.py` e `valida_integridade_referencial.py` (Sprint 2) sobre os mesmos CSVs de origem e comparar contra `PUB_QUALIDADE_*`; divergência esperada de grão, porque os scripts da Sprint 2 leem CSV bruto e a DX-09 lê `ingestao_*_atual` já tratada. |

## Indicadores sinalizados (DX-10)

Para os 18 indicadores de `DIM_INDICADORES_BLOQUEADOS`
(`docs/sinalizacao-indicadores-bloqueados.md`), a conferência é sobre a
sinalização em si — a medida aparece com o motivo textual em qualquer
contexto de filtro, nunca como `0` — não sobre um valor numérico, porque não
há valor numérico a conferir por definição.

## Medidas DAX do C03 (BI-04)

[`tests/analytics/test_medidas_bi.py`](../tests/analytics/test_medidas_bi.py)
calcula resultados de referência independentes para médias ponderadas,
denominador vazio, zero numérico, estoque 10→7 em dois fechamentos, período sem
fechamento e zero observado versus não observado. São testes Python do contrato,
não execução do motor DAX.

Para execução real no Windows com Power BI Desktop, abra o modelo carregado e
rode [`tests/analytics/dax/bi04-acceptance-queries.dax`](../tests/analytics/dax/bi04-acceptance-queries.dax)
na exibição de consultas DAX. Troque os dois meses de exemplo por fechamentos
observados na geração carregada. Confira também um mês que exista em
`DIM_TEMPO`, mas não tenha linha C03. O modelo deve mostrar o último fechamento
observado no contexto de tempo e os motivos textuais para estoque ausente e
transições não publicadas. A consulta 3 agrupa as colunas brutas C03 `[area]`,
`[tipo]` e `[perfil]`: com uma área filtrada sem linha no último fechamento,
confira que a data continua global e que o estoque do grupo é zero porque há
linhas C03 de outros grupos nesse fechamento. Sem linha C03 em todo o período,
estoque e data continuam `BLANK()`. A publicação atual não permite testar
fechamento observado sem nenhum grupo; não declare esse caso aceito até que o
contrato exponha o marcador.
