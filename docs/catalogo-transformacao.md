# Catálogo de campos da ingestão tratada

MG-02/MG-11. Contrato v1.0. Gerado de `schema.py`; valide com
`PYTHONPATH=src python scripts/transformation/render_schema.py --check`.

A coluna Regra remete aos tipos e aos critérios em [schema-transformacao.md](schema-transformacao.md).
Os testes e códigos de rejeição estão na [matriz de validação](matriz-transformacao.md).

## pesquisas

| Origem | Destino | Tipo DuckDB | Ausência | Regra |
| --- | --- | --- | --- | --- |
| `id` | `ingestao_pesquisas.pesquisa_id` | `VARCHAR` | rejeitar | id |
| `titulo` | `ingestao_pesquisas.titulo` | `VARCHAR` | null | text |
| `status` | `ingestao_pesquisas.status` | `VARCHAR` | null | text |
| `tipo` | `ingestao_pesquisas.tipo` | `VARCHAR` | null | text |
| `area` | `ingestao_pesquisas.area` | `VARCHAR` | null | text |
| `participantes` | `ingestao_pesquisas.participantes` | `BIGINT` | null | integer |
| `part_mercado` | `ingestao_pesquisas.part_mercado` | `DECIMAL(18, 6)` | null | percent |
| `data_solicitacao` | `ingestao_pesquisas.data_solicitacao` | `DATE` | null | date |
| `data_aprov` | `ingestao_pesquisas.data_aprov` | `DATE` | null | date |
| `data_divulgacao` | `ingestao_pesquisas.data_divulgacao` | `DATE` | null | date |
| `data_limite` | `ingestao_pesquisas.data_limite` | `DATE` | null | date |
| `prorrogada_ate` | `ingestao_pesquisas.prorrogada_ate` | `DATE` | null | date |
| `data_entrega` | `ingestao_pesquisas.data_entrega` | `DATE` | null | date |
| `dias_uteis_para_entrega` | `ingestao_pesquisas.dias_uteis_para_entrega` | `BIGINT` | null | integer |
| `complexidade` | `ingestao_pesquisas.complexidade` | `VARCHAR` | null | text |
| `tipo de resposta` | `ingestao_pesquisas.tipo_resposta` | `VARCHAR` | null | text |
| `tempo_preenchimento` | `ingestao_pesquisas.tempo_preenchimento` | `DECIMAL(18, 6)` | null | decimal |
| `objetivos` | `ingestao_pesquisas.objetivos` | `VARCHAR` | null | text |
| `dia da semana de lançamento` | `ingestao_pesquisas.dia_semana_lancamento` | `VARCHAR` | null | text |
| `dias úteis aberta` | `ingestao_pesquisas.dias_uteis_aberta` | `BIGINT` | null | integer |
| `dias entre a solicitação e a divulgação` | `ingestao_pesquisas.dias_solicitacao_divulgacao` | `BIGINT` | null | integer |
| `dias para tabulação` | `ingestao_pesquisas.dias_tabulacao` | `BIGINT` | null | integer |

## empresas

| Origem | Destino | Tipo DuckDB | Ausência | Regra |
| --- | --- | --- | --- | --- |
| `ID` | `ingestao_empresas.empresa_id` | `VARCHAR` | rejeitar | id |
| `Nome Fantasia` | `ingestao_empresas.nome_fantasia` | `VARCHAR` | null | text |
| `% de mercado` | `ingestao_empresas.part_mercado` | `DECIMAL(18, 6)` | null | percent |
| `Nacionalidade` | `ingestao_empresas.nacionalidade` | `VARCHAR` | null | text |
| `Associado` | `ingestao_empresas.associado` | `BOOLEAN` | null | boolean; sentinelas: - |
| `Tipo de Associado` | `ingestao_empresas.tipo_associado` | `VARCHAR` | null | text |
| `Cidade` | `ingestao_empresas.cidade` | `VARCHAR` | null | text |
| `Estado` | `ingestao_empresas.estado` | `VARCHAR` | null | text |
| `País` | `ingestao_empresas.pais` | `VARCHAR` | null | text |

## clientes

| Origem | Destino | Tipo DuckDB | Ausência | Regra |
| --- | --- | --- | --- | --- |
| `id_cliente` | `ingestao_clientes.cliente_id` | `VARCHAR` | rejeitar | id; sentinelas: s/i |
| `id_empresa` | `ingestao_clientes.empresa_id` | `VARCHAR` | rejeitar | id |
| `cargo` | `ingestao_clientes.cargo` | `VARCHAR` | null | text |
| `departamento` | `ingestao_clientes.departamento` | `VARCHAR` | null | text |
| `e-mail` | `ingestao_clientes.email` | `VARCHAR` | null | text |

## respondentes

| Origem | Destino | Tipo DuckDB | Ausência | Regra |
| --- | --- | --- | --- | --- |
| `id_pesq` | `ingestao_respondentes.pesquisa_id` | `VARCHAR` | rejeitar | id |
| `hora_inicio` | `ingestao_respondentes.hora_inicio` | `TIMESTAMP` | null | datetime |
| `hora_termino` | `ingestao_respondentes.hora_termino` | `TIMESTAMP` | null | datetime |
| `id_empresa` | `ingestao_respondentes.empresa_id` | `VARCHAR` | rejeitar | id |
| `market_share` | `ingestao_respondentes.market_share` | `DECIMAL(18, 6)` | null | percent; sentinelas: na, n/a |
| `id_cliente` | `ingestao_respondentes.cliente_id` | `VARCHAR` | null | id; sentinelas: s/i |

## questoes

| Origem | Destino | Tipo DuckDB | Ausência | Regra |
| --- | --- | --- | --- | --- |
| `id_pergunta` | `ingestao_questoes.pergunta_id` | `VARCHAR` | rejeitar | id |
| `pesquisa_id` | `ingestao_questoes.pesquisa_id` | `VARCHAR` | rejeitar | id |
| `pesquisa_titulo` | `ingestao_questoes.pesquisa_titulo` | `VARCHAR` | null | text |
| `enunciado` | `ingestao_questoes.enunciado` | `VARCHAR` | null | text |
| `tipo` | `ingestao_questoes.tipo` | `VARCHAR` | rejeitar | text |
| `qtd_alternativas` | `ingestao_questoes.qtd_alternativas` | `BIGINT` | null | integer |
| `alternativas` | `ingestao_questoes.alternativas` | `VARCHAR` | [] | list |
| `linhas_matriz` | `ingestao_questoes.linhas_matriz` | `VARCHAR` | [] | list |
| `colunas_matriz` | `ingestao_questoes.colunas_matriz` | `VARCHAR` | [] | list |
| `confianca` | `ingestao_questoes.confianca` | `VARCHAR` | null | text |
| `formato_arquivo` | `ingestao_questoes.formato_arquivo` | `VARCHAR` | null | text |
| `col_origem` | `ingestao_questoes.col_origem` | `VARCHAR` | null | text |
| `observacoes` | `ingestao_questoes.observacoes` | `VARCHAR` | null | text |

## respostas

| Origem | Destino | Tipo DuckDB | Ausência | Regra |
| --- | --- | --- | --- | --- |
| `id_resposta` | `ingestao_respostas.resposta_id` | `VARCHAR` | rejeitar | id |
| `pesquisa_id` | `ingestao_respostas.pesquisa_id` | `VARCHAR` | rejeitar | id |
| `id_pergunta` | `ingestao_respostas.pergunta_id` | `VARCHAR` | rejeitar | id |
| `respondent_id` | `ingestao_respostas.respondent_id` | `VARCHAR` | rejeitar | id |
| `id_empresa` | `ingestao_respostas.empresa_id` | `VARCHAR` | null | id |
| `alternativa` | `ingestao_respostas.alternativa` | `VARCHAR` | null | text |
| `linha_matriz` | `ingestao_respostas.linha_matriz` | `VARCHAR` | null | text |
| `coluna_matriz` | `ingestao_respostas.coluna_matriz` | `VARCHAR` | null | text |
| `valor` | `ingestao_respostas.valor` | `VARCHAR` | null | text; sentinelas: na, n/a |

## Metadados comuns

| Campo | Tipo |
| --- | --- |
| `source` | `VARCHAR` |
| `run_id` | `VARCHAR` |
| `task_id` | `VARCHAR` |
| `batch_id` | `VARCHAR` |
| `source_checksum` | `VARCHAR` |
| `source_offset` | `UBIGINT` |
| `content_checksum` | `VARCHAR` |
| `record_identity` | `VARCHAR` |
| `idempotency_key` | `VARCHAR` |
| `ingested_at` | `TIMESTAMP` |
| `schema_version` | `VARCHAR` |
