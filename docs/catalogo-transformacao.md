# Catálogo de campos da ingestão tratada

MG-02/MG-11. Contrato v1.0. Gerado de `schema.py`; valide com
`PYTHONPATH=src python scripts/transformation/render_schema.py --check`.

A coluna Regra remete aos tipos e aos critérios em [schema-transformacao.md](schema-transformacao.md).
Os testes e códigos de rejeição estão na [matriz de validação](matriz-transformacao.md).

## pesquisas

| Origem | Destino | Tipo ClickHouse | Ausência | Regra |
| --- | --- | --- | --- | --- |
| `id` | `ingestao_pesquisas.pesquisa_id` | `String` | rejeitar | id |
| `titulo` | `ingestao_pesquisas.titulo` | `Nullable(String)` | null | text |
| `status` | `ingestao_pesquisas.status` | `Nullable(String)` | null | text |
| `tipo` | `ingestao_pesquisas.tipo` | `Nullable(String)` | null | text |
| `area` | `ingestao_pesquisas.area` | `Nullable(String)` | null | text |
| `participantes` | `ingestao_pesquisas.participantes` | `Nullable(Int64)` | null | integer |
| `part_mercado` | `ingestao_pesquisas.part_mercado` | `Nullable(Decimal(18, 6))` | null | percent |
| `data_solicitacao` | `ingestao_pesquisas.data_solicitacao` | `Nullable(Date32)` | null | date |
| `data_aprov` | `ingestao_pesquisas.data_aprov` | `Nullable(Date32)` | null | date |
| `data_divulgacao` | `ingestao_pesquisas.data_divulgacao` | `Nullable(Date32)` | null | date |
| `data_limite` | `ingestao_pesquisas.data_limite` | `Nullable(Date32)` | null | date |
| `prorrogada_ate` | `ingestao_pesquisas.prorrogada_ate` | `Nullable(Date32)` | null | date |
| `data_entrega` | `ingestao_pesquisas.data_entrega` | `Nullable(Date32)` | null | date |
| `dias_uteis_para_entrega` | `ingestao_pesquisas.dias_uteis_para_entrega` | `Nullable(Int64)` | null | integer |
| `complexidade` | `ingestao_pesquisas.complexidade` | `Nullable(String)` | null | text |
| `tipo de resposta` | `ingestao_pesquisas.tipo_resposta` | `Nullable(String)` | null | text |
| `tempo_preenchimento` | `ingestao_pesquisas.tempo_preenchimento` | `Nullable(Decimal(18, 6))` | null | decimal |
| `objetivos` | `ingestao_pesquisas.objetivos` | `Nullable(String)` | null | text |
| `dia da semana de lançamento` | `ingestao_pesquisas.dia_semana_lancamento` | `Nullable(String)` | null | text |
| `dias úteis aberta` | `ingestao_pesquisas.dias_uteis_aberta` | `Nullable(Int64)` | null | integer |
| `dias entre a solicitação e a divulgação` | `ingestao_pesquisas.dias_solicitacao_divulgacao` | `Nullable(Int64)` | null | integer |
| `dias para tabulação` | `ingestao_pesquisas.dias_tabulacao` | `Nullable(Int64)` | null | integer |

## empresas

| Origem | Destino | Tipo ClickHouse | Ausência | Regra |
| --- | --- | --- | --- | --- |
| `ID` | `ingestao_empresas.empresa_id` | `String` | rejeitar | id |
| `Nome Fantasia` | `ingestao_empresas.nome_fantasia` | `Nullable(String)` | null | text |
| `% de mercado` | `ingestao_empresas.part_mercado` | `Nullable(Decimal(18, 6))` | null | percent |
| `Nacionalidade` | `ingestao_empresas.nacionalidade` | `Nullable(String)` | null | text |
| `Associado` | `ingestao_empresas.associado` | `Nullable(Bool)` | null | boolean; sentinelas: - |
| `Tipo de Associado` | `ingestao_empresas.tipo_associado` | `Nullable(String)` | null | text |
| `Cidade` | `ingestao_empresas.cidade` | `Nullable(String)` | null | text |
| `Estado` | `ingestao_empresas.estado` | `Nullable(String)` | null | text |
| `País` | `ingestao_empresas.pais` | `Nullable(String)` | null | text |

## clientes

| Origem | Destino | Tipo ClickHouse | Ausência | Regra |
| --- | --- | --- | --- | --- |
| `id_cliente` | `ingestao_clientes.cliente_id` | `String` | rejeitar | id; sentinelas: s/i |
| `id_empresa` | `ingestao_clientes.empresa_id` | `String` | rejeitar | id |
| `cargo` | `ingestao_clientes.cargo` | `Nullable(String)` | null | text |
| `departamento` | `ingestao_clientes.departamento` | `Nullable(String)` | null | text |
| `e-mail` | `ingestao_clientes.email` | `Nullable(String)` | null | text |

## respondentes

| Origem | Destino | Tipo ClickHouse | Ausência | Regra |
| --- | --- | --- | --- | --- |
| `id_pesq` | `ingestao_respondentes.pesquisa_id` | `String` | rejeitar | id |
| `hora_inicio` | `ingestao_respondentes.hora_inicio` | `Nullable(DateTime64(6, 'UTC'))` | null | datetime |
| `hora_termino` | `ingestao_respondentes.hora_termino` | `Nullable(DateTime64(6, 'UTC'))` | null | datetime |
| `id_empresa` | `ingestao_respondentes.empresa_id` | `String` | rejeitar | id |
| `market_share` | `ingestao_respondentes.market_share` | `Nullable(Decimal(18, 6))` | null | percent; sentinelas: na, n/a |
| `id_cliente` | `ingestao_respondentes.cliente_id` | `Nullable(String)` | null | id; sentinelas: s/i |

## questoes

| Origem | Destino | Tipo ClickHouse | Ausência | Regra |
| --- | --- | --- | --- | --- |
| `id_pergunta` | `ingestao_questoes.pergunta_id` | `String` | rejeitar | id |
| `pesquisa_id` | `ingestao_questoes.pesquisa_id` | `String` | rejeitar | id |
| `pesquisa_titulo` | `ingestao_questoes.pesquisa_titulo` | `Nullable(String)` | null | text |
| `enunciado` | `ingestao_questoes.enunciado` | `Nullable(String)` | null | text |
| `tipo` | `ingestao_questoes.tipo` | `String` | rejeitar | text |
| `qtd_alternativas` | `ingestao_questoes.qtd_alternativas` | `Nullable(Int64)` | null | integer |
| `alternativas` | `ingestao_questoes.alternativas` | `Array(String)` | [] | list |
| `linhas_matriz` | `ingestao_questoes.linhas_matriz` | `Array(String)` | [] | list |
| `colunas_matriz` | `ingestao_questoes.colunas_matriz` | `Array(String)` | [] | list |
| `confianca` | `ingestao_questoes.confianca` | `Nullable(String)` | null | text |
| `formato_arquivo` | `ingestao_questoes.formato_arquivo` | `Nullable(String)` | null | text |
| `col_origem` | `ingestao_questoes.col_origem` | `Nullable(String)` | null | text |
| `observacoes` | `ingestao_questoes.observacoes` | `Nullable(String)` | null | text |

## respostas

| Origem | Destino | Tipo ClickHouse | Ausência | Regra |
| --- | --- | --- | --- | --- |
| `id_resposta` | `ingestao_respostas.resposta_id` | `String` | rejeitar | id |
| `pesquisa_id` | `ingestao_respostas.pesquisa_id` | `String` | rejeitar | id |
| `id_pergunta` | `ingestao_respostas.pergunta_id` | `String` | rejeitar | id |
| `respondent_id` | `ingestao_respostas.respondent_id` | `String` | rejeitar | id |
| `id_empresa` | `ingestao_respostas.empresa_id` | `Nullable(String)` | null | id |
| `alternativa` | `ingestao_respostas.alternativa` | `Nullable(String)` | null | text |
| `linha_matriz` | `ingestao_respostas.linha_matriz` | `Nullable(String)` | null | text |
| `coluna_matriz` | `ingestao_respostas.coluna_matriz` | `Nullable(String)` | null | text |
| `valor` | `ingestao_respostas.valor` | `Nullable(String)` | null | text; sentinelas: na, n/a |

## Metadados comuns

| Campo | Tipo |
| --- | --- |
| `source` | `String` |
| `run_id` | `String` |
| `task_id` | `String` |
| `batch_id` | `String` |
| `source_checksum` | `FixedString(64)` |
| `source_offset` | `UInt64` |
| `content_checksum` | `FixedString(64)` |
| `record_identity` | `FixedString(64)` |
| `idempotency_key` | `FixedString(64)` |
| `ingested_at` | `DateTime64(6, 'UTC')` |
| `schema_version` | `String` |
