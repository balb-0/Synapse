# Conferência das medidas contra a apuração de referência

Cumpre a DX-11: confere cada medida publicada contra os valores já apurados
(`docs/resultados_analise.txt`, `docs/dmc.md`), com o resultado anexado —
automatizado onde há referência numérica fixa, documentado como checklist
manual onde não há.

## Conferência automatizada

[`scripts/analytics/conferir_medidas_bi.py`](../scripts/analytics/conferir_medidas_bi.py)
recalcula, a partir dos Parquet de uma geração publicada
(`docs/acesso-cubos-bi.md`), as três medidas que têm um valor de referência
numérico fixo já registrado na Sprint 2, com uma implementação independente
da fórmula (não reaproveita a consulta de `publish.py` — se reaproveitasse,
a "conferência" só provaria que o código concorda consigo mesmo):

| Medida | Referência | Fonte |
| :-- | :-- | :-- |
| `Qtd Pesquisas` | 366 | `docs/resultados_analise.txt`, T1 |
| `Base Valida Validacao` | 20 (limite superior) | `docs/resultados_analise.txt`, T1 (cobertura de `data_aprov`) |
| `Qtd Participacoes` | ≈18.735 | `docs/dmc.md`, seção 3.2 |

Rodar contra uma geração real:

```bash
PYTHONPATH=src python -m scripts.analytics.conferir_medidas_bi \
  --geracao /caminho/privado/publicacao-bi/GERACAO
```

O script nunca trata "maior que a referência" como falha — o snapshot da
apuração de 2026 é anterior à geração conferida, então mais pesquisas e
participações carregadas depois da apuração fazem a medida atual crescer,
nunca diminuir; só "menor que a referência" ou uma coluna ausente encerram
com código de saída 1, porque isso indicaria regressão ou publicação
incompleta. A suíte
[`scripts/analytics/test_conferir_medidas_bi.py`](../scripts/analytics/test_conferir_medidas_bi.py)
verifica as quatro situações (bate exato, diverge para cima, diverge para
baixo, arquivo ausente) com Parquet sintético — sem depender de acesso ao
DuckDB privado, que este repositório não versiona.

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
