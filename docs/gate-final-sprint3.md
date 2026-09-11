# Gate Final da Sprint 3 (VB-11)

Execução real do gate em checkout limpo **integrado localmente**. O merge
integrado existiu apenas em worktree local e **não foi enviado para o
`develop`**; apenas as branches de trabalho foram atualizadas no remoto.

Este documento registra duas rodadas: a primeira (11/09/2026, manhã) encontrou
a branch da VB-08 vazia e divergências de lint entre as branches de teste e o
ruff geral; a segunda (11/09/2026, após a recriação da `chore-210-vb-08` e a
propagação das correções de lint) é a execução válida do gate.

## Integração local (rodada válida)

Ordem recomendada de merge sobre `develop` (`949cbe1`), executada nesta ordem
e **sem nenhum conflito**:

1. `chore-208-vb-06` (!171) — ruff.toml geral + formatação
2. `chore-209-vb-07` (!172) — CI consolidado (stages `lint` + `test`, remove
   `.gitlab/ci/transformation.yml`)
3. `chore-210-vb-08` (!173) — cobertura estendida: o job de teste do CI
   consolidado executa `coverage run --branch --source=etl` sobre a suíte
   completa, com `coverage report --fail-under=85` e relatório `coverage-etl.xml`
4. `test-205-vb-03` (!175) — fixtures sintéticas (já com a correção de lint)
5. `test-206-vb-04` (!176) — e2e (já formatado)
6. `test-207-vb-05` (!177) — gray-box de orquestração (já formatado)
7. `docs-204-vb-02` (!170) — estratégia de testes
8. `docs-211-vb-09` (!174) — runbook + README
9. `test-212-vb-10` (!178) — auditoria (incluída para validar o estado final
   dos documentos e do `dmc.json`)
10. `test-213-vb-11` (!179) — script do gate

Na rodada anterior, `chore-208` × `chore-209` conflitavam em duas linhas de
`docs/matriz-rastreabilidade-sprint3.md`; as branches foram re-feitas desde
então e o conflito não existe mais.

### Correções feitas na primeira rodada (já incorporadas às branches)

Os testes das branches VB-03/VB-04/VB-05 haviam sido escritos antes do
`ruff.toml` geral (VB-06) e falhavam no lint consolidado:

- `tests/fixtures/test_fixtures_sinteticas.py`: 7× E741 (variável `l`) e 1×
  E731 (lambda atribuída) — corrigido na `test-205` (`d21589c`);
- `tests/e2e/test_pipeline_ponta_a_ponta.py` e
  `tests/orchestration/test_gray_box_orquestracao.py`: formatação —
  corrigido nas branches `test-206` (`bbdc8a4`) e `test-207` (`0eaad28`),
  com `line-length 100`.

Sem essas correções, o job `lint` do CI consolidado falharia após o merge dos
MRs. Na rodada válida, o lint passa sem nenhuma correção adicional.

## Resultado real do gate (rodada válida)

Comando: `scripts/gate_final.sh` (sem `--install`; venv dedicado criado no
checkout). Ambiente local: Python 3.14.5 (o CI usa `python:3.12-slim`; a
diferença segue registrada como risco na matriz de rastreabilidade — sem sinal
de incompatibilidade na execução).

| Etapa | Resultado |
| :--- | :--- |
| Dependências (`requirements.txt` + dev) | OK |
| `ruff check src scripts tests` | OK, 0 erros |
| `ruff format --check src scripts tests` | OK, 91 arquivos formatados |
| Suíte `unittest` completa | **216 testes, 23,9 s, OK (1 skip)** |
| `scripts/dmc/validate_dmc.py` | DMC válido (schema 1; 4 cubos; 3 táticas) |
| `scripts/dmc/run_gates.py` | 5 gates aprovados (47 + 14 testes, 1 skip) |
| Veredicto do script | `GATE FINAL: OK` |

Cobertura na mesma configuração do CI consolidado (`coverage run --branch
--source=etl`): **TOTAL 93%** (1731 stmts, 516 branches), acima do threshold de
85% da VB-08. Por camada: extraction 81–100% (`failures.py` 81% é o menor),
transformation 93–100%, load 89–100% (`ddl.py` 100%, `duckdb_repository.py`
98%), **orchestration 88%** (`flow.py`) — o gray-box da VB-05 cobriu a camada
que a matriz registrava com 0%.

## Checklist

- [x] dependências instaladas e importáveis
- [x] ruff check sem erros
- [x] ruff format --check sem diferenças
- [x] suíte unittest completa verde (216 testes)
- [x] dmc.json válido e gates de rastreabilidade aprovados
- [x] cobertura 93% ≥ threshold de 85% do CI consolidado

## Veredito

**READY** — o gate integrado passa de ponta a ponta, na ordem de merge
recomendada, sem conflitos e sem correções adicionais.

Observações que acompanham os MRs (não bloqueiam):

1. As branches `test-205`, `test-206` e `test-207` receberam commits de
   lint/formatação durante a primeira rodada; quem tiver checkout local antigo
   delas deve fazer pull com rebase (`test-206` e `test-207` sofreram
   *force push*).
2. A cobertura da VB-08 usa `--source=etl`: `scripts/` fora do ETL
   (data_quality, dmc, governance etc.) tem testes próprios que rodam na suíte,
   mas não entram na medição.
3. Python local do gate (3.14) ≠ CI (3.12): a versão de referência declarada
   pela VB-06/VB-07 é 3.12.
