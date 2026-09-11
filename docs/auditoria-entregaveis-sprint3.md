# Auditoria dos Entregáveis da Sprint 3 (VB-10)

Auditoria dos dois artefatos contra o código real do `develop` (commit
`949cbe1`), executada em 11/09/2026. Artefato 1: especificação técnica do ETL
(`requisitos-operacionais-etl.md`, ADRs, cinco visões ISO/IEC 10746, diagramas
UML). Artefato 2: `dmc.json`.

Método: cada afirmação dos documentos foi confrontada com o módulo que ela cita
em `src/etl/`, com `docker-compose.yml`, `Dockerfile`, `.gitlab-ci.yml` e com a
suíte `unittest`. Divergências foram corrigidas **na documentação** (commit
`docs: corrige divergencias entre documentacao e codigo apontadas pela auditoria
VB-10`), sem alteração de código.

## Artefato 1 — Especificação técnica do ETL

### `docs/requisitos-operacionais-etl.md`

| Seção | Implementado? | Evidência | Coerente? |
| :--- | :--- | :--- | :--- |
| Fluxo orquestrado E→T→L, falha interrompe dependentes | Sim | Tasks `extract` → `transform` → `load` encadeadas por retorno em `src/etl/orchestration/flow.py` | Sim |
| Disparo por evento (`s3:ObjectCreated`) | Não (planejado) | Nenhum adaptador HTTP no `develop`; gatilhos reais são `run_ingest.py`, `deployment.py` (cron) e `run_backfill.py` | Sim, desde que lido como requisito; a execução por evento está marcada como planejada nas visões |
| Agendamento | Sim | `ingest_object.serve(name="agendado", cron="0 3 * * *")` em `scripts/orchestration/deployment.py` | Sim |
| Execução manual / backfill | Sim | Flow `backfill` e `scripts/orchestration/run_backfill.py`, com fontes, prefixo e `reprocess` como parâmetros | Sim |
| Retry com limite, transitória × permanente | Sim | `RetryExecutor`/`classify_source_failure` (`resilience.py`, `failures.py`) + `retries=2` e `_should_retry` na task `extract` | Sim |
| Timeout | Sim | `timeout_seconds=120` nas três tasks do flow | Sim |
| Retomada segura / idempotência | Sim | `_checkpoint` confirmado só após a carga; `_control_object` por SHA-256 retorna `ignored`; dedup por linha via `_loaded_identity` | Sim |
| Logs estruturados | Parcial | `log_events.py` emite JSON técnico por lote (`StandardLoggingSink`); transporte ao Logstash é planejado | Sim |
| Métricas por etapa | Parcial | `TransformationResult.metrics` e `LoadResult.as_dict()` existem; não há envio a coletor | Sim |
| Telemetria, painel, health checks, alertas (Elastic Stack) | Não (planejado) | Decisão no ADR 0001; sem código no `develop` | Sim (decisão registrada) |
| Testes de integração nos cinco cenários | Parcial | `tests/extraction` e `tests/load` cobrem resiliência, rejeição e reprocessamento; suíte ponta a ponta do flow não existe no `develop` (em trabalho nas branches VB-03 a VB-05) | Sim |
| Diagrama de sequência | Sim | `assets/uml/sequencia-ingestao-etl.plantuml` corresponde ao flow | Sim |
| Nota final de dependências | Estava **desatualizada** | Dizia "não há módulo de carga na base" e "OV-09 depende de MC-09 (ainda não entregue)" | **Corrigido**: `src/etl/load/` existe e E→T→L está fechado |

### ADRs

| ADR | Implementado? | Evidência | Coerente? |
| :--- | :--- | :--- | :--- |
| 0001 — Arquitetura (status Proposto) | Parcial, conforme os próprios critérios de aceite | Extração, transformação, carga, flow Prefect, docker-compose existem; adaptador de eventos, bronze e Elastic Stack não | Sim: o status Proposto e a tabela de critérios no índice refletem o estado real |
| 0002 — Identidade e versões | Sim, com pendência declarada | PK `idempotency_key`, UNIQUE (chave + `content_checksum`), views `_atual`, views legadas em `ddl.py`; classificação de duplicidade ainda rejeita correção (canário em `tests/load/test_identity_coupling.py`) | Sim: a pendência está registrada no próprio ADR |
| 0003 — Convergência do insert | Sim | `ON CONFLICT ("idempotency_key") DO NOTHING` em `duckdb_repository.load_batch`; `INSERT OR REPLACE` nas tabelas de controle | Sim |
| 0004 — Execução local e CI (ex-0003) | Sim como registro do que existe | `docker-compose.yml` com `minio`, `createbucket`, `runner`; CI com job único de transformação | Sim |

**Divergência estrutural corrigida:** existiam dois ADRs numerados **0003**
(`0003-convergencia-do-insert-no-reprocessamento-do-lote.md`, referenciado como
"ADR 0003" por `duckdb_repository.py` e `repositorio-de-carga.md`, e
`0003-execucao-local-e-integracao-continua.md`, referenciado pelo índice e pelas
visões). O ADR de convergência também estava **ausente do índice**. Resolução:
o ADR de execução local foi renumerado para **0004** (referências atualizadas em
`adrs/index.md`, `index.md`, `projeto.md`, `visao-negocio-etl.md`,
`visao-engenharia-etl.md`, `matriz-rastreabilidade-sprint3.md`), e o índice
ganhou a linha do ADR 0003 com a nota de numeração. Nenhuma referência em
código foi tocada.

### Visões ISO/IEC 10746

| Visão | Implementado conforme descrito? | Evidência | Coerente com as demais? |
| :--- | :--- | :--- | :--- |
| Negócio (AN-04) | Sim | Escopo termina na tabela de ingestão; restrições batem com o schema (`clientes` com e-mail/cargo/departamento; `respondentes` sem chave) | Sim |
| Informação (AN-05) | Sim | Cadeia objeto → `ExtractedBatch` → `Accepted/RejectedRecord` → DuckDB confirmada em `contracts.py`, `pipeline.py`, `ddl.py`; sentinelas conferem com `schema.py` (`s/i`, `-`, `na`/`n/a`); `SCHEMA_VERSION = "1.0"` | Sim |
| Computacional (AN-06) | Sim | Assinaturas conferem (`transform_batch`, `load_batch`, `load_extraction_settings` etc.); divergências reais já documentadas (`MetadataSink` sem implementação, `QuarantineStore` fora do caminho produtivo, `repo._conn`, `DUCKDB_PATH` × `ETL_DUCKDB_PATH`) | Sim |
| Engenharia (AN-07) | Sim | Serviços do compose, variáveis e padrões conferem com `docker-compose.yml`, `config.py` e `load/config.py` (30 s, 1000, 3, 0,5/5 s, 300 s); ordem de confirmação carga→reconciliação→checkpoint/hash bate com o flow | Sim |
| Tecnologia (AN-08) | Sim | Versões conferem com `Dockerfile` (3.12), `requirements.txt`, `requirements-transformation-dev.txt` (ruff 0.16.6, coverage 7.16.0) e `.gitlab/ci/transformation.yml`; divergência de versão do Python já registrada | Sim |

As cinco visões conversam entre si: negócio fixa o limite (tabela de ingestão),
informação descreve as representações, computacional nomeia os componentes que
engenharia executa, e tecnologia lista as versões. Referências cruzadas entre
elas e para os ADRs foram verificadas e estão corretas após a renumeração do
ADR 0004.

### Diagramas UML (`docs/assets/uml/`)

| Diagrama | Representa o fluxo real? | Observação |
| :--- | :--- | :--- |
| `casos-de-uso-etl.plantuml` | Sim | UC02 (evento) e UC17 (monitoramento) marcados `<<planejado>>`, condizente com o `develop` |
| `componentes-etl.plantuml` | Sim | Adaptador de eventos, área bronze e Elastic Stack marcados `<<planejado>>`; interfaces batem com os protocolos de `contracts.py`/`log_events.py`; nenhum componente inexistente aparece como implementado |
| `sequencia-ingestao-etl.plantuml` | Sim | Execução normal, retry limitado, falha permanente e reenvio conferem com `flow.py`, `resilience.py` e `duckdb_repository.py`, inclusive a confirmação tardia de checkpoint e hash |

O fluxo Fonte → Extração → Transformação → Validação → Carga → DuckDB está
corretamente representado nos três diagramas; a validação aparece dentro da
transformação (`normalize_record`, `validate_consistency`), como no código.

## Artefato 2 — `docs/dmc.json`

Validação executada: `json.load` OK; `scripts/dmc/validate_dmc.py` → "DMC
válido: schema 1; 4 cubos; 3 táticas; ETL, Modelo, Dados e Governança
preenchidos"; `scripts/dmc/run_gates.py` → 5 gates aprovados (14 testes,
1 skip).

### Grãos dos quatro cubos

| Cubo | Grão declarado | Avaliação |
| :--- | :--- | :--- |
| C01 Portfólio e Ciclo | Uma linha por pesquisa (fato acumulador, marcos do ciclo) | Coerente com `pesquisas.csv` e com a chave `pesquisa_id` do schema |
| C02 Participação e Representatividade | Uma linha por **participação** (`respondentes.csv`), com `seq_ocorrencia` para duplicatas pessoa×pesquisa | Correto: não confunde participação com resposta nem com pessoa; a ponte pessoa↔participação↔resposta permanece pendente (DR03) |
| C03 Pipeline Mensal | Uma linha por combinação mês × status × área × tipo × perfil (snapshot periódico derivado do C01) | Coerente; proíbe backfill inferido, condizente com a ausência de histórico |
| C04 Resultados e Questionários | Uma linha por pergunta em uma pesquisa (fato de associação) | Coerente com `questoes.csv` (chave `pesquisa_id` + `pergunta_id`); respostas individuais ficam fora até reconciliação, respeitando a distinção Pessoa→Participação→Resposta |

Nenhum cubo assume "uma linha de resposta = um respondente": `respondent_id` é
explicitamente não conciliado (DR03, I13, transformações do C04). Decisões não
informadas pelo parceiro estão marcadas como proposta/pendência (DR01–DR06,
campos de governança como "baseline documental sujeito a homologação").

### Incoerências encontradas e corrigidas

1. **Tática 2 citava o `QuarantineStore` como destino produtivo das rejeições.**
   No código, rejeições vão para `rejected`/`rejected_reason` no DuckDB; o
   `QuarantineStore` (SQLite) só existe em testes — divergência já registrada
   na visão computacional. Texto da tática corrigido.
2. **Volumes do cubo 4 em versão diferente do restante do DMC.** O cubo 4 usa o
   snapshot antigo de `questoes.csv` (231 linhas, cobertura de 10 pesquisas,
   vínculo direto de 188/231), enquanto o cubo 1 e o inventário de fontes usam
   a v3 (366 pesquisas; `questoes.csv` v3 tem 3.297 registros). Adicionada ao
   grão do cubo 4 uma observação datada marcando a versão do snapshot e a
   necessidade de recálculo antes do uso oficial. A modelagem da Sprint 2 não
   foi alterada.

## Correções feitas nesta auditoria (resumo)

| # | Onde | Correção |
| :--- | :--- | :--- |
| 1 | `docs/adrs/0003-execucao-local…` → `0004-execucao-local…` | Renumeração por colisão de número; referências atualizadas em 6 documentos |
| 2 | `docs/adrs/index.md` | Incluído o ADR 0003 (convergência) e nota de numeração |
| 3 | `docs/requisitos-operacionais-etl.md` | Nota de dependências atualizada: módulo de carga existe; pendências reais listadas |
| 4 | `docs/dmc.json` | Tática 2 alinhada às tabelas de rejeição do DuckDB |
| 5 | `docs/dmc.json` | Cubo 4 marcado com a versão do snapshot de seus volumes |

## Gaps restantes

| Prioridade | Gap | Onde |
| :--- | :--- | :--- |
| P0 | Nenhum bloqueador de auditoria restante | — |
| P1 | Disparo por evento (adaptador HTTP) não implementado; critério de aceite do ADR 0001 segue não cumprido | ADR 0001, OV-02 |
| P1 | Elastic Stack decidida e não integrada; observabilidade limitada a logs locais e views de reconciliação | ADR 0001, OV-05 a OV-08 |
| P1 | Estimativa de custos exigida pelo ADR 0001 ainda não existe | ADR 0001, `dmc.json` (`custoEstimado`) |
| P2 | Classificação de duplicidade ainda rejeita correção do parceiro como conflito de identidade (ADR 0002 aguarda ratificação) | `identity.py`, ADR 0002 |
| P2 | Volumes e coberturas do cubo 4 precisam ser recalculados sobre a v3 | `dmc.json` |
| P2 | Divergência de versão do Python (3.12 no Dockerfile, 3.11 no CI/ruff) e dependências sem pin | ADR 0004, visão de tecnologia |
| P3 | `MetadataSink` sem implementação; `QuarantineStore` fora do caminho produtivo; acesso a `repo._conn` pelo flow; `DUCKDB_PATH` × `ETL_DUCKDB_PATH`; `ETL_MINIO_SECURE` não lida | Visão computacional/engenharia (já documentadas) |
| P3 | Os CSVs versionados na raiz não são a v3 analisada nos documentos (ex.: `pesquisas.csv` com 402 linhas vs. 366 da v3); volumes "observados (v3)" não são verificáveis contra o repositório | `inventario-fontes-etl.md`, visão de informação |
| P4 | Política de retenção das versões da tabela de ingestão indefinida (pendência aceita no ADR 0002) | ADR 0002 |
