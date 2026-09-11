# Gate Final da Sprint 3 (VB-11)

Execução real do gate em checkout limpo **integrado localmente**, em 11/09/2026.
O merge integrado existiu apenas em worktree local (`gate-final-integrado-local`)
e **não foi enviado para o `develop`**; apenas as branches de trabalho foram
atualizadas no remoto.

## Integração local

Ordem dos merges sobre `develop` (`949cbe1`):

1. `chore-208-vb-06` (ruff.toml geral + formatação) — limpo
2. `chore-209-vb-07` (CI consolidado) — **1 conflito** (ver abaixo)
3. `chore-210-vb-08` (cobertura estendida) — *Already up to date*: a branch
   **está vazia** (aponta para o próprio `develop`, local e remoto). O trabalho
   de cobertura estendida (threshold 85%) **não existe na branch**; o CI
   consolidado roda a suíte completa sem gate de cobertura.
4. `test-205-vb-03` (fixtures sintéticas) — limpo
5. `test-206-vb-04` (e2e) — limpo
6. `test-207-vb-05` (gray-box orquestração) — limpo
7. `docs-204-vb-02` (estratégia de testes) — limpo
8. `docs-211-vb-09` (runbook + README) — limpo
9. `test-212-vb-10` (auditoria) e `test-213-vb-11` (script do gate) — limpos;
   incluídos para que o gate validasse o estado final dos documentos e do
   `dmc.json`.

### Conflito de merge

`docs/matriz-rastreabilidade-sprint3.md`: `chore-208` e `chore-209` editaram as
mesmas duas linhas da tabela de pendências (versão do Python e CI não
consolidado). Resolução trivial: mantidas as duas atualizações (cada branch
registra a pendência que ela própria resolveu). Nenhum conflito em
`.gitlab/ci/transformation.yml` — a remoção do arquivo legado pela `chore-209`
não encontrou modificação concorrente.

### Correções mínimas de integração (propagadas às branches de origem)

Os testes das branches VB-03/VB-04/VB-05 foram escritos antes do `ruff.toml`
geral (VB-06) e falhavam no lint consolidado:

- `tests/fixtures/test_fixtures_sinteticas.py`: 7× E741 (variável `l`) e 1×
  E731 (lambda atribuída) — corrigido e enviado à `test-205` (`d21589c`).
- `tests/e2e/test_pipeline_ponta_a_ponta.py` e
  `tests/orchestration/test_gray_box_orquestracao.py`: divergência de
  formatação — corrigido e enviado às branches `test-206` (`bbdc8a4`) e
  `test-207` (`0eaad28`), com `line-length 100` (a primeira passada usou o
  default 88 do ruff por falta do `ruff.toml` nessas branches e foi refeita).

Sem essas correções, o job `lint` do CI consolidado falharia após o merge dos
MRs — era o único problema real de integração entre as branches.

## Resultado real do gate

Comando: `scripts/gate_final.sh` (sem `--install`; venv dedicado criado no
checkout). Ambiente local: Python 3.14.5 (o CI usa `python:3.12-slim` — o gate
foi verde nas dependências atuais, mas a diferença de versão segue registrada
como risco na matriz de rastreabilidade).

| Etapa | Resultado |
| :--- | :--- |
| Dependências (`requirements.txt` + dev) | OK |
| `ruff check src scripts tests` | OK, 0 erros |
| `ruff format --check src scripts tests` | OK, 91 arquivos formatados |
| Suíte `unittest` completa | **216 testes, 21,9 s, OK (1 skip)** |
| `scripts/dmc/validate_dmc.py` | DMC válido (schema 1; 4 cubos; 3 táticas) |
| `scripts/dmc/run_gates.py` | 5 gates aprovados (47 + 14 testes, 1 skip) |
| Veredicto do script | `GATE FINAL: OK` |

Cobertura medida fora do gate (referência, já que a VB-08 não existe na
branch): `coverage run --branch --source=etl -m unittest discover -s tests` →
**TOTAL 93%** (1731 stmts, 516 branches). Por camada: extraction 87–100%
(`failures.py` 81% é o menor), transformation 93–100%, load 89–100%
(`ddl.py` 100%, `duckdb_repository.py` 98%), **orchestration 88%** (`flow.py`) —
o gray-box da VB-05 cobriu a camada que estava documentada com 0%. Acima dos
85% previstos pela VB-08.

## Checklist

- [x] dependências instaladas e importáveis
- [x] ruff check sem erros
- [x] ruff format --check sem diferenças
- [x] suíte unittest completa verde (216 testes)
- [x] dmc.json válido e gates de rastreabilidade aprovados

## Veredito

**READY** — o gate integrado passa de ponta a ponta após as correções de
lint/formatação já propagadas às branches `test-205`, `test-206` e `test-207`.

Observações (não bloqueiam o gate, mas devem acompanhar os MRs):

1. **VB-08 (MR !173) está sem conteúdo**: a branch `chore-210` aponta para o
   `develop`. Se a cobertura estendida com threshold for exigida, a tarefa
   precisa ser refeita; a medição acima (93% total, orchestration 88%) serve de
   evidência de que o threshold de 85% é atingível hoje.
2. As branches `test-206` e `test-207` receberam *force push* com a formatação
   corrigida; quem tiver checkout local delas deve fazer pull com rebase.
3. Python local do gate (3.14) ≠ CI (3.12): sem sinal de incompatibilidade, mas
   a unificação declarada pela VB-06/VB-07 é 3.12.
