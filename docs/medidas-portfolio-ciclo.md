# Medidas de portfólio, tempo de ciclo e prorrogação

Cumpre a DX-07: implementa em
[`PUB_C01_CICLO.tmdl`](../powerbi/CentralPesquisasBI.SemanticModel/definition/tables/PUB_C01_CICLO.tmdl)
as medidas de portfólio, tempo de ciclo e prorrogação, seguindo a fórmula já
registrada em `docs/especificacao-medidas-bi.md` (DX-02) e as regras de
`docs/regras-estatisticas-medidas.md` (DX-03).

## Medidas implementadas

| Medida | DAX | Regra aplicada |
| :-- | :-- | :-- |
| `Qtd Pesquisas` | `SUM(PUB_C01_CICLO[qtd_pesquisas])` | Soma segura entre grupos (área×status×tipo particiona sem sobreposição). |
| `Media Dias Validacao` / `Media Dias Coleta` / `Media Dias Tabulacao` / `Media Dias Ciclo Total` | `DIVIDE(SUM(soma_dias_*), SUM(qtd_*_disponivel))` | `DIVIDE` em vez de `/` (regra 2); só média, nunca mediana, pela limitação documentada em DX-03 (regra 1). |
| `Base Valida Validacao` / `Base Valida Coleta` / `Base Valida Tabulacao` / `Base Valida Ciclo Total` | `SUM(qtd_*_disponivel)` | Medida-irmã de base para exibir ao lado de cada média (regra 3). |
| `Taxa de Prorrogacao` | Medida de texto com o motivo do bloqueio | Indisponível: `flag_prorrogada` não está em `PUB_C01_CICLO` (DX-01, I05). Nunca aparece como `0` (regra 4 de DX-03 / mecanismo de DX-10). |

## Conferência contra a apuração de referência

`docs/dmc.md` (catálogo I01–I05) e `docs/resultados_analise.txt` (Sprint 2)
são a referência para o mesmo recorte:

- `Qtd Pesquisas` sem filtro deve bater com a contagem de pesquisas correntes
  do repositório analítico (366 no snapshot documentado em
  `docs/resultados_analise.txt`, seção T1) — a conferência final e formal com
  o valor do momento da carga é da DX-11.
- As médias de duração (`Media Dias Validacao` etc.) não têm um valor de
  referência pré-calculado equivalente no material da Sprint 2, porque aquele
  levantamento não segmentava por área/status/tipo; a conferência da DX-11
  compara contra uma consulta direta ao DuckDB de origem no mesmo recorte, não
  contra `resultados_analise.txt`.
- `Base Valida Validacao` para o grupo sem filtro deve bater com a cobertura
  de `data_aprov` já registrada (20 de 366, 5,5%, `docs/resultados_analise.txt`
  T1) — é o par de datas com menor cobertura entre os quatro medidos.

## Por que não há medida de I06 (atrasadas/prioritárias)

Diferente da prorrogação, `docs/indicadores-publicaveis-bi.md` já classifica
I06 como sem dado tanto na camada de dados quanto na camada BI (falta regra e
data de referência aprovadas) — não é uma coluna que ficou de fora da
publicação, é um indicador que nunca chegou a ter fórmula aprovada. Por isso
não há medida "de texto" para I06 aqui: a sinalização completa desse caso é
tratada de forma uniforme na DX-10, junto com os demais indicadores sem dado
de DX-08 e DX-09.
