# Inventário dos contratos dimensionais que restringem a ingestão

Este inventário reúne os contratos de fato, dimensão e cubo já existentes que
restringem nomes, tipos e metadados da tabela de ingestão. Ele cita o modelo
dimensional já entregue ([`docs/dmc.json`](dmc.json) e
[`docs/projeto.md`](projeto.md) §5.2) e o contrato da camada de
transformação como fontes dessa restrição.

## Escopo

Este documento separa a tabela de ingestão — o destino do fluxo
`Fonte → Extração → Transformações essenciais → Tabela de ingestão` — de
fato, dimensão, cubo e agregado analítico, que são camadas seguintes no
tratamento do dado. O modelo dimensional (fato, dimensão, cubo) já foi
produzido como Data Model Canvas antes desta etapa; este inventário cita esse
modelo como fonte de restrição, sem reabri-lo.

O próprio contrato da camada de transformação declara a mesma fronteira do
lado da implementação: *"Nenhum cubo, dimensão, agregação, KPI analítico ou
correspondência entre pessoas é produzido aqui"* (`schema-transformacao.md`).
A partir dessa fronteira, este documento cobre:

- o dicionário de tipos e as tabelas de destino já propostos pelo contrato de
  transformação;
- quais campos canônicos desse contrato têm consumidor confirmado num fato ou
  dimensão do modelo dimensional já entregue, pra que a implementação da
  tabela de ingestão saiba quais nomes precisa preservar.

## Fora de escopo

- **Modelar fato, dimensão ou cubo.** Esse modelo já foi entregue como Data
  Model Canvas (`docs/dmc.json` + `docs/projeto.md` §5.2). Este inventário
  cita esse material como fonte de restrição, não o reescreve.
- **Definir agregado analítico.** O termo não tem contrato em nenhum artefato
  do projeto (`Governança-de-Dados-do-Projeto.md`, `dmc.json`, `projeto.md`),
  e o contrato de transformação já declara que nenhuma agregação é produzida
  na ingestão. Propor essa definição fica pra uma etapa de modelagem
  analítica.
- **Traduzir tipo ClickHouse → DuckDB.** O contrato de transformação declara
  tipo por campo com destino ClickHouse, desatualizado desde a adoção do
  DuckDB (ADR 0001). A tradução para o tipo físico DuckDB é decisão de quem
  implementar a tabela de ingestão, não deste inventário.
- **Resolver os achados de nomenclatura e derivação** listados nas tabelas
  abaixo (`ano_edicao`, `regiao`, "cliente" vs. "pessoa"). Ficam registrados
  como constatação; a decisão acontece na implementação da tabela de
  ingestão.

## Contrato herdado da camada de transformação

O contrato da camada de transformação é imediatamente anterior à tabela de
ingestão no fluxo de dados — é isso que este inventário usa como referência
de alinhamento. O contrato executável está em `schema.py` e
`schema-transformacao.md`, disponíveis numa branch de trabalho separada
(`docs-171-mg-02-definir-o-schema-canonico-tratado`), ainda não incorporada à
branch principal do repositório.

### Tabelas de destino já propostas

| Fonte | Destino contratual | Chave |
| :--- | :--- | :--- |
| `pesquisas.csv` | `ingestao_pesquisas` | `pesquisa_id` |
| `empresas.csv` | `ingestao_empresas` | `empresa_id` |
| `clientes.csv` | `ingestao_clientes` | `cliente_id` |
| `respondentes.csv` | `ingestao_respondentes` | Origem da participação; sem colapsar pessoas ausentes |
| `questoes.csv` | `ingestao_questoes` | `pesquisa_id` + `pergunta_id` |
| `respostas.csv` | `ingestao_respostas` | `pesquisa_id` + `resposta_id` |

### Dicionário de tipos

| Tipo lógico | Representação Python | Destino declarado | Regra |
| :--- | :--- | :--- | :--- |
| `id` | str de dígitos normalizados | `String` | Inteiro não negativo, sem float intermediário |
| `integer` | `int` | `Int64` | Sem parte fracionária |
| `decimal` | `Decimal` | `Decimal(18, 6)` | Máximo seis casas, sem arredondamento silencioso |
| `percent` | `Decimal` | `Decimal(18, 6)` | Pontos percentuais em 0..100 |
| `date` | `date` | `Date32` | Data civil, sem hora inventada |
| `datetime` | `datetime` UTC | `DateTime64(6, 'UTC')` | Fuso explícito obrigatório |
| `boolean` | `bool` | `Bool` | Mapa fechado sim/não, true/false |
| `text` | `str` | `String` | Unicode NFC, sem espaços externos |
| `list` | `list[str]` | `Array(String)` | Ausência produz `[]`, não nulo |

A coluna "Destino declarado" é ClickHouse (`clickhouse_type`, literal no
código), desatualizado desde a ADR 0001. A tradução está listada em "Fora de
escopo" acima.

## Nomes que a ingestão precisa preservar

Cada linha abaixo é um campo canônico do contrato de transformação
(`schema.py`) com consumidor confirmado em `docs/projeto.md` §5.2 — ou seja,
a implementação da tabela de ingestão preserva esse nome porque um fato ou
dimensão já proposto depende dele. Campos sem consumidor listado não estão
"errados"; só não têm, até este inventário, um uso downstream documentado.

### `ingestao_pesquisas`

| Campo canônico | Coluna recebida | Consumidor downstream |
| :--- | :--- | :--- |
| `pesquisa_id` | `id` | Chave de `DIM_PESQUISA` (`sk_pesquisa`); referenciada por `respondentes`, `questoes`, `respostas` |
| `titulo` | `titulo` | `DIM_PESQUISA.titulo`; base da derivação de `DIM_FAMILIA_PESQUISA` |
| `objetivos` | `objetivos` | `DIM_PESQUISA.objetivos` |
| `area` | `area` | `DIM_AREA`, via `sk_area` |
| `status` | `status` | `DIM_STATUS_PESQUISA`, via `sk_status` |
| `tipo` | `tipo` | `DIM_TIPO_PESQUISA`, via `sk_tipo` |
| `participantes` | `participantes` | Medida `qtd_empresas_na_pesquisa` (`FATO_CICLO_PESQUISA`) |
| `data_solicitacao` … `data_entrega` (6 campos) | idem | Papéis de `DIM_TEMPO` no `FATO_CICLO_PESQUISA` (`sk_data_*`); `data_divulgacao` também alimenta `sk_data_pesquisa` em C02 e C04 |

**Achado:** `DIM_PESQUISA` (diagramas e §5.2.1) tem atributo `ano_edicao`,
sem campo `ano`/`ano_edicao` correspondente no contrato de transformação para
`pesquisas`. Candidato a derivação do `titulo`, no mesmo padrão de
`DIM_FAMILIA_PESQUISA` (normalização de título).

### `ingestao_respondentes`

| Campo canônico | Coluna recebida | Consumidor downstream |
| :--- | :--- | :--- |
| `pesquisa_id` | `id_pesq` | `FATO_PARTICIPACAO.sk_pesquisa` |
| `empresa_id` | `id_empresa` | `FATO_PARTICIPACAO.sk_empresa` |
| `cliente_id` | `id_cliente` | `FATO_PARTICIPACAO.sk_pessoa` — ver achado de nomenclatura abaixo |
| `hora_inicio` | `hora_inicio` | `sk_data_resposta` (papel de `DIM_TEMPO`); insumo de `minutos_preenchimento` |
| `hora_termino` | `hora_termino` | Insumo de `minutos_preenchimento` |
| `market_share` | `market_share` | Medida `pct_mercado_na_participacao` |

**Achado de nomenclatura:** o contrato de transformação chama a entidade de
"cliente" (`cliente_id`), a governança de dados e os diagramas chamam de
"pessoa" (`DIM_PESSOA`, `sk_pessoa`). É o mesmo dado com rótulo diferente em
cada camada, não fontes conflitantes.

### `ingestao_empresas`

| Campo canônico | Coluna recebida | Consumidor downstream |
| :--- | :--- | :--- |
| `empresa_id` | `ID` | Chave de `DIM_EMPRESA`; `FATO_PARTICIPACAO.sk_empresa` |
| `nome_fantasia` | `Nome Fantasia` | `DIM_EMPRESA.nome_fantasia` |
| `part_mercado` | `% de mercado` | `DIM_EMPRESA` (campo de share) |
| `nacionalidade`, `cidade`, `estado`, `pais` | idem | Atributos geográficos de `DIM_EMPRESA` |
| `associado`, `tipo_associado` | `Associado`, `Tipo de Associado` | `DIM_EMPRESA.flag_associado`, `.tipo_associado` |

`projeto.md` §5.2.2 já registra que `empresas.% de mercado` (`part_mercado`)
e `respondentes.market_share` divergem, sem precedência presumida — "a fonte
autoritativa deve ser homologada antes de calcular I09". A tabela de
ingestão preserva as duas colunas separadas.

**Achado:** `DIM_EMPRESA` tem atributo `regiao` (diagrama de cubo-02), sem
coluna correspondente no contrato de transformação para `empresas` —
candidato a derivação de `estado`, mesmo padrão do achado de `ano_edicao`
acima.

### `ingestao_clientes`

| Campo canônico | Coluna recebida | Consumidor downstream |
| :--- | :--- | :--- |
| `cliente_id` | `id_cliente` | Chave de `DIM_PESSOA` |
| `empresa_id` | `id_empresa` | FK para `DIM_EMPRESA` |
| `cargo`, `departamento` | idem | Base de `DIM_PESSOA` (nível hierárquico e agrupamento de departamento são derivados destes dois) |
| `email` | `e-mail` | A ingestão preserva o campo para rastreabilidade/LGPD; `projeto.md` §5.2.2 já decidiu removê-lo de `DIM_PESSOA` por ser pseudônimo reversível |

### `ingestao_questoes`

| Campo canônico | Coluna recebida | Consumidor downstream |
| :--- | :--- | :--- |
| `pergunta_id` | `id_pergunta` | Chave de `DIM_PERGUNTA` |
| `pesquisa_id` | `pesquisa_id` | `FATO_INSTRUMENTO.sk_pesquisa` |
| `pesquisa_titulo` | `pesquisa_titulo` | Sustenta o fallback por título pros 4 `pesquisa_id` órfãos (424, 1116, 1139, 1147) descrito em `projeto.md` §5.2.4 |
| `enunciado`, `tipo`, `qtd_alternativas` | idem | Atributos de `DIM_PERGUNTA` |
| `confianca`, `formato_arquivo`, `col_origem` | idem | `DIM_PERGUNTA.nivel_confianca`, `.formato_arquivo_origem`, `.col_origem` |

### `ingestao_respostas`

O modelo dimensional já entregue (`projeto.md` §5.2) cobre `respostas.csv` só
como ponto de extensão futuro: o C04 (`FATO_INSTRUMENTO`) para em
`questoes.csv`, e a ligação entre `respondent_id` e a identidade de
`respondentes.csv` está explicitamente "não comprovada" (§5.2.4) — o próprio
documento reserva essa fonte pra um futuro `FATO_RESPOSTA`. A ingestão desta
fonte segue o contrato de transformação sem restrição adicional de um fato ou
dimensão ainda inexistente.

## Fontes usadas

- `schema.py` e `schema-transformacao.md` — contrato de transformação, numa
  branch de trabalho ainda não incorporada à branch principal.
- `docs/projeto.md` §5.1–5.2 — modelo de cubos já entregue (Data Model Canvas).
- `docs/dmc.json` — mesmo modelo, em JSON.
- `docs/Governança-de-Dados-do-Projeto.md` §3.2 — padrão de nome `asset_id`
  proposto (`<camada>.<tipo>.<nome>`), ainda não incorporado a nenhum
  artefato executável; convenção distinta da nomenclatura física
  `ingestao_<fonte>` do contrato de transformação, servindo propósitos
  diferentes (catálogo documental vs. nome físico de tabela).
- `docs/adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md` — adoção do
  DuckDB no lugar do ClickHouse.
