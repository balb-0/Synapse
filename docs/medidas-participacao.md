# Medidas de participação e representatividade

Cumpre a DX-08: implementa em
[`PUB_C02_PARTICIPACAO.tmdl`](../powerbi/CentralPesquisasBI.SemanticModel/definition/tables/PUB_C02_PARTICIPACAO.tmdl)
as medidas de participação e de representatividade, seguindo
`docs/especificacao-medidas-bi.md` (DX-02) e `docs/regras-estatisticas-medidas.md`
(DX-03).

## Medidas implementadas

| Medida | DAX | Regra aplicada |
| :-- | :-- | :-- |
| `Qtd Participacoes` | `SUM(PUB_C02_PARTICIPACAO[qtd_participacoes])` | Apurada sem contar ocorrência duplicada: a deduplicação de reprocessamento já ocorreu na carga (identidade física `source_checksum`/`source_offset`), o Parquet não repete o mesmo registro. Nomeada "Participações", nunca "Respondentes" (regra 4 de DX-03). |
| `Media Minutos Preenchimento` | `DIVIDE(SUM(soma_minutos_preenchimento), SUM(qtd_preenchimento_disponivel))` | `DIVIDE`, denominador exposto ao lado (`Base Valida Preenchimento`). |
| `Base Valida Preenchimento` | `SUM(qtd_preenchimento_disponivel)` | Medida-irmã de base (regra 3). |
| `Representatividade` | Medida de texto com o motivo do bloqueio | Indisponível: `pct_mercado_na_participacao` não é publicada; mesmo se fosse, I09 segue bloqueada por falta de fonte homologada. Nunca soma participação de mercado como se fosse uma média — a regra pedida ("representatividade soma a participação de mercado, nunca a média") só se aplica quando o indicador tiver dado, o que hoje não é o caso. |

## Por que representatividade não é "quase" calculável

A tarefa pede que "representatividade some a participação de mercado, nunca
a média" — isso é uma regra de **como** calcular, não uma garantia de que o
dado existe. `docs/indicadores-publicaveis-bi.md` já registra que I09 está
bloqueada em duas camadas independentes: a coluna de mercado não está no
Parquet publicado, e mesmo a fonte de mercado da camada de dados
(`empresas.part_mercado` vs. `respondentes.market_share`) diverge sem
homologação (`docs/dmc.md`, DR02). As duas causas precisam ser resolvidas
antes de qualquer soma — resolver só a publicação do Parquet não bastaria
enquanto a divergência de fonte não for decidida pelo parceiro.

## Conferência contra a apuração de referência

`Qtd Participacoes` sem filtro deve bater com o total de participações do
snapshot (aproximadamente 18.735 linhas, conforme `docs/dmc.md`, seção 3.2) —
a conferência exata com o valor do momento da carga é da DX-11.
`Media Minutos Preenchimento` não tem par direto em
`docs/resultados_analise.txt` (aquele levantamento não cobria tempo de
preenchimento); a DX-11 confere contra consulta direta ao DuckDB de origem.
