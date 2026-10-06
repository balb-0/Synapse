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
a população atual. O script registra se cada arquivo existe, quantas linhas
contém e qual agregado produziu. Distingue caminho ausente, Parquet existente
sem linhas e coluna sem valor agregado; todos ficam não validados junto com
qualquer divergência e encerram com código 1. Para aceitar uma geração nova,
compare-a com a carga DuckDB reconciliada da mesma geração. Igualdade com uma
referência antiga também não substitui essa reconciliação de identidades.

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
Parquet sintético, além de distinguir arquivo vazio de caminho ausente e de
agregado sem valor — sem depender de acesso ao DuckDB privado, que este
repositório não versiona.

**Resultado anexado (a preencher por Anna ao rodar contra uma geração
real):**

| Medida | Arquivo presente | Linhas publicadas | Valor publicado | Valor de referência | Status |
| :-- | :-- | :-- | :-- | :-- | :-- |
| `Qtd Pesquisas` | _(rodar o script)_ | _(rodar o script)_ | _(rodar o script)_ | 366 | _(rodar o script)_ |
| `Base Valida Validacao` | _(rodar o script)_ | _(rodar o script)_ | _(rodar o script)_ | 20 | _(rodar o script)_ |
| `Qtd Participacoes` | _(rodar o script)_ | _(rodar o script)_ | _(rodar o script)_ | 18735 | _(rodar o script)_ |

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

`DIM_INDICADORES_BLOQUEADOS` é um catálogo de 18 linhas, não 18 medidas DAX.
Confira suas colunas `indicador`, `medida`, `status` e `motivo`, os 17 estados
"Sem dado", o único estado "Parcial" e `Qtd Indicadores Sem Dado` = 17. Só
`Taxa de Prorrogacao` e `Representatividade` têm medidas textuais próprias;
confira que cada uma exibe o motivo em qualquer contexto de filtro. Para os
demais itens, valide a linha do catálogo, sem esperar uma medida numérica ou
textual implementada. As consultas 6/6a do Desktop listam as quatro colunas,
conferem a contagem de 18 linhas/17 sem dado e mostram apenas essas duas
medidas de texto junto com `Qtd Indicadores Sem Dado`.

## Medidas DAX do C03 (BI-04)

[`tests/analytics/test_medidas_bi.py`](../tests/analytics/test_medidas_bi.py)
calcula resultados de referência independentes para médias ponderadas,
denominador vazio, zero numérico, estoque 10→7 em dois fechamentos, período sem
fechamento e zero observado versus não observado. São testes Python do contrato,
não execução do motor DAX.

A consulta 1a compara o estoque da medida com a soma direta da fato C03 para
o fixture Desktop de `data_fim_mes` 28/02/2026 e estoque 4. A recuperação limpa
`DIM_TEMPO` e filtra a coluna de data da própria fato, mantendo os filtros de
categoria do estoque.

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

## Consultas reais do fixture em Power BI Desktop

O [recibo das medidas](evidencias/bi04/desktop-medidas-fixture.json) registra
consulta real em VM Windows em 06/10/2026 às 14:04:07 UTC, após sincronização
do relógio. A média ponderada de validação foi 5 dias com denominador 2,
e a média de preenchimento foi 10 minutos com denominador 2.
Os totais C01/C02/C04 foram 4/4/3.

O estoque da medida BI-04 foi 4 no último fechamento, 28/02/2026, igual à
soma direta filtrada na fato C03. As medidas de entrada e saída retornaram
valor nulo e o motivo de ausência de histórico. As duas medidas textuais
bloqueadas exibiram os motivos; o catálogo retornou 18 linhas e 17 estados
sem dado. A comparação TOM teve 128 itens e zero diferenças para a projeção
semântica do TMDL conferido, além de 98 arquivos de origem verificados.

O resultado é do fixture sintético. Não substitui a conferência das métricas
da geração v3. As consultas anexadas não cobrem todas as médias de fases,
todos os recortes categóricos ou todos os edge cases do checklist acima.
Fechamento sem nenhum grupo observado continua sem representação suficiente
no contrato Parquet; não há aceite desse caso.
