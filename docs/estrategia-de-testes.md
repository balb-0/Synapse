# Estratégia de testes

Este documento registra como o ETL é testado hoje: o que já existe, onde está e
o que falta. Ele descreve o estado real do repositório — cada categoria aponta
arquivos existentes em `tests/`; o que ainda não existe está marcado como
lacuna, não como intenção.

## Baseline

- Framework: `unittest` da biblioteca padrão (sem pytest).
- Comando: `python -m unittest discover -s tests -v`, com `PYTHONPATH=src`.
- Localização: `tests/`, espelhando as camadas de `src/etl/` —
  `tests/extraction/`, `tests/transformation/` e `tests/load/`.
- Volume atual: 216 testes (`grep -rc "def test" tests/` em 11/09/2026).
- Dependências de teste: `requirements-transformation-dev.txt` (ruff e
  coverage) para lint e cobertura locais, iguais ao CI; os demais testes rodam
  com as dependências de `requirements.txt`.
- Gate de CI: o pipeline consolidado (`.gitlab-ci.yml`) roda `ruff check` e
  `ruff format --check` sobre `src`, `scripts` e `tests` (job `lint`) e a
  suíte inteira por `unittest discover` com verificação de schema e cobertura
  `coverage --branch --source=etl --fail-under=85` sobre todo o pacote `etl`
  (job `test`).

Documentos relacionados: [`testes-extracao.md`](testes-extracao.md) (suíte de
extração) e [`smoke-test-extracao.md`](smoke-test-extracao.md) (resultado do
smoke test).

## Camadas de teste

### Black-box — comportamento externo do pipeline

Testa o sistema como caixa opaca: uma entrada nas fontes deve produzir a saída
correta nas tabelas de destino, sem conhecimento do código interno.

- **Existe hoje:** `tests/extraction/test_smoke_extraction.py` — smoke test que
  executa os seis extratores sobre fixtures sintéticas em memória e compara
  contagens de registros e lotes com valores esperados (resultado registrado em
  [`smoke-test-extracao.md`](smoke-test-extracao.md)).
- **Existe hoje:** `tests/e2e/test_pipeline_ponta_a_ponta.py` — teste black-box
  ponta a ponta do pipeline orquestrado (fixture → flow `ingest_object` →
  linhas consultadas no DuckDB), adicionado na Sprint 3 (VB-04) sobre as
  fixtures sintéticas versionadas de `tests/fixtures/`.

### Gray-box — integração e contratos entre camadas

Testa as fronteiras entre extração, transformação, carga e orquestração,
exercitando os contratos internos sem reexecutar a lógica inteira de cada
lado.

- **Contrato comum dos extratores:** `tests/extraction/test_contracts.py` e
  `tests/extraction/test_extractor_contract_suite.py` instanciam os seis
  extratores pelo mesmo protocolo e validam lote, checkpoint e metadados
  entregues à transformação (contrato em
  [`contrato-lote-extraido.md`](contrato-lote-extraido.md)).
- **Orquestração (camadas ↔ flow):**
  `tests/orchestration/test_gray_box_orquestracao.py` exercita o flow
  `ingest_object` com camadas instrumentadas, cobrindo idempotência, retry,
  retomada e reconciliação no nível da orquestração (VB-05).
- **Reprocessamento (transformação → carga):**
  `tests/load/test_reprocessing.py` reexecuta o mesmo lote pelo pipeline de
  transformação e pela carga real em um DuckDB temporário, verificando que a
  segunda execução converge em vez de violar a chave primária (ver ADR
  [`adrs/0003-convergencia-do-insert-no-reprocessamento-do-lote.md`](adrs/0003-convergencia-do-insert-no-reprocessamento-do-lote.md)).
- **Acoplamento deduplicação ↔ contrato físico:**
  `tests/load/test_identity_coupling.py` é um canário entre a classificação de
  duplicidade da transformação e a tabela de controle `_loaded_identity` da
  carga (ver ADR
  [`adrs/0002-identidade-e-versoes-na-tabela-de-ingestao.md`](adrs/0002-identidade-e-versoes-na-tabela-de-ingestao.md)).
- **Contrato físico de destino (opt-in):**
  `tests/transformation/test_clickhouse_contract.py` insere linhas
  transformadas em um ClickHouse real via Docker e confere os seis schemas.
  Está desabilitado por padrão (`skipUnless`) e roda somente com
  `ETL_TEST_CLICKHOUSE=1` e Docker local disponível.
- **DDL, tabelas de controle e ambiente de carga:** `tests/load/test_ddl.py`,
  `tests/load/test_control_tables.py`, `tests/load/test_config.py`,
  `tests/load/test_connection_tuning.py` e `tests/load/test_environment.py`
  verificam o contrato das tabelas e a configuração da carga. O teste de
  contenção de escrita entre processos está em `tests/load/test_write_lock.py`.

### White-box — regras internas de transformação e validação

Testa as regras de negócio e os algoritmos internos com conhecimento da
implementação: conversão de tipos, normalização, validação de campos e domínio,
consistência referencial, deduplicação e quarentena.

- `tests/transformation/test_transformation.py` (35 testes) cobre as regras
  das seis fontes, implementadas em `src/etl/transformation/`
  (`conversion.py`, `normalization.py`, `validation.py`, `consistency.py`,
  `identity.py`, `quarantine.py`, `pipeline.py`). A matriz regra ↔ teste está
  em [`matriz-transformacao.md`](matriz-transformacao.md) e o catálogo de
  regras em [`catalogo-transformacao.md`](catalogo-transformacao.md).
- Na extração, os testes unitários por fonte
  (`test_csv_extractors.py`, `test_clientes_respondentes_extractors.py`,
  `test_questoes_respostas_extractors.py`), de paginação e retomada
  (`test_batching_checkpoints.py`), de resiliência (`test_resilience.py`), de
  configuração (`test_config.py`) e de logs (`test_extraction_logs.py`) são
  white-box: exercitam timeouts, retries, checkpoints e formato dos eventos de
  log com leitores em memória.

## Lacunas registradas

| Lacuna | Impacto |
| :--- | :--- |
| Contrato ClickHouse desligado por padrão | Divergência de schema com o destino final só aparece em execução opt-in |

Lacunas resolvidas na Sprint 3: o teste E2E automatizado do flow passou a
existir em `tests/e2e/` (VB-04) e o gate de cobertura do CI consolidado
(`--fail-under=85` sobre todo o pacote `etl`, VB-08) cobre extração, carga e
orquestração, não só `etl.transformation`.
