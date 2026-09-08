# Estado inicial do Data Model Canvas — Sprint 3

## Escopo e fonte

Este registro usa exclusivamente o artefato versionado em `docs/dmc.json` e os
documentos Markdown do repositório. O arquivo foi aberto pelo parser JSON e
pelos validadores reproduzíveis do projeto. Nenhum conteúdo externo ou arquivo
alternativo foi incorporado ao baseline.

| Item | Estado inicial |
|---|---|
| Arquivo | `docs/dmc.json` |
| `schemaVersion` | `1` |
| Versão declarada | `1.0` |
| Data declarada | `2026-07-31` |
| Quantidade de cubos | 4 |
| IDs | `cubo-1`, `cubo-2`, `cubo-3`, `cubo-4` |
| Seções de topo obrigatórias | Presentes |
| Campos vazios em Governança Corporativa | Nenhum |

## Cubos encontrados

1. `cubo-1` — Portfólio e Ciclo.
2. `cubo-2` — Participação e Representatividade.
3. `cubo-3` — Pipeline Mensal.
4. `cubo-4` — Resultados e Questionários.

Os quatro cubos possuem grão, fatos, métricas e dimensões preenchidos. Seus IDs
e sua ordem atendem ao contrato estrutural atualmente versionado.

## Campos que precisam de ajuste

- A versão e a data em `metadata` ainda representam o baseline anterior à
  revisão da Sprint 3.
- Cada cubo ainda contém 25 chaves das subseções Dados e Governança que estão
  fora do recorte pedido para a Sprint 3. A remoção e a atualização do contrato
  do validador pertencem ao `KP-10` (`#157`).
- Negócio e Consumo Analítico precisam ser conferidos contra `docs/projeto.md`;
  esse trabalho foi registrado nos cards `KP-02` a `KP-05`.
- Governança Corporativa precisa de revisão semântica de segurança, LGPD,
  catálogo, indicadores e maturidade; esse trabalho pertence aos cards `KP-07`
  e `KP-08`.
- O Modelo Dimensional dos quatro cubos precisa ser reconciliado com as
  definições atuais de `docs/projeto.md`; esse trabalho pertence ao `KP-09`.

## Evidência reproduzível

Comandos executados na raiz do repositório:

```bash
python scripts/dmc/inventory_dmc.py docs/dmc.json
python scripts/dmc/validate_dmc.py docs/dmc.json
python scripts/traceability/validate_traceability.py \
  --manifest scripts/traceability/manifest.json \
  --dmc docs/dmc.json \
  --project docs/projeto.md
python -m unittest discover -s scripts/dmc -p "test_*.py"
python -m unittest discover -s scripts/traceability -p "test_*.py"
```

Resultado inicial:

- JSON sintaticamente válido e legível em UTF-8.
- Quatro cubos detectados.
- Validador DMC aprovado.
- Validador de rastreabilidade aprovado.
- 21 testes DMC aprovados.
- 14 testes de rastreabilidade aprovados, com um teste ignorado por depender
  de fonte primária não disponível no comando.

## Gate manual da ferramenta oficial

O repositório não informa URL, executável ou procedimento de acesso à
ferramenta oficial do Data Model Canvas. Por isso, este registro comprova a
abertura estrutural pelos mecanismos versionados, mas não afirma que houve uma
importação visual externa. Esse gate deve ser anexado ao card quando a
ferramenta for disponibilizada, informando data, responsável e resultado da
abertura dos quatro cubos.
