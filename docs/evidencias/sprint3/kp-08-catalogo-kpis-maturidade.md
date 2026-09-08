# KP-08 — catálogo, KPIs e maturidade de governança

## Resultado da revisão

Os campos corporativos do `docs/dmc.json` foram revisados contra
`docs/projeto.md`. Propostas da equipe são identificadas como propostas e
capacidades que dependem do pipeline permanecem indisponíveis até existirem os
metadados necessários.

| Bloco | Conteúdo registrado | Evidência no projeto |
|---|---|---|
| Catálogo | Contrato mínimo por fonte e campo, com versão, classificação, responsável, regra e estado | §§5.3, 6.6.2 e 6.6.6 |
| KPIs atuais | I16–I20, com numerador, denominador, unidade, grão, fonte e regra | §§5.3.3, 5.3.4 e 6.4 |
| KPIs futuros | I21–I25 condicionados a timestamp, linhagem, autorização, catálogo, execução, política e logs | §§5.6, 6.4 e 6.6.6 |
| Maturidade observada | Fontes fragmentadas, operação manual e linhagem parcial | §§2.2, 3 e 6.5 |
| Estado-alvo | Fonte integrada, governada e auditável | §§2.1 e 6.6 |
| Evolução | Gates incrementais de catálogo, pipeline, linhagem, acesso e publicação | §§2.1, 5.6 e 6.6.11 |

## Regras de mensuração

- Nenhum KPI é apresentado apenas por um nome genérico: o DMC exige a família
  de medida e seu contrato mínimo.
- Ausência de timestamp, catálogo, decisão ou log torna I21–I25 indisponíveis;
  não representa resultado zero.
- Metas de automação, atualização e publicação são estado-alvo e não evidência
  de capacidade já implantada.
- A expansão deve respeitar os gates de qualidade, linhagem, acesso e aprovação
  antes de disponibilizar dados para consumo.

## Verificações

```bash
python -m json.tool docs/dmc.json
python scripts/dmc/validate_dmc.py docs/dmc.json
python scripts/traceability/validate_traceability.py \
  --manifest scripts/traceability/manifest.json \
  --dmc docs/dmc.json \
  --project docs/projeto.md
```
