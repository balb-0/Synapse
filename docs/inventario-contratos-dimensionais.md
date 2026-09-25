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
- **Traduzir tipos.** Não é necessário: o contrato de transformação declara diretamente tipos DuckDB.
- **Inventariar limites de origem e nomenclatura.** `ano_edicao` e `regiao`
  ficam indisponíveis sem coluna de origem ou derivação homologada. `cliente_id`
  é o nome canônico da origem que alimenta `DIM_PESSOA` quando conciliado; essa
  diferença de rótulo não cria uma segunda identidade.

## Contrato herdado da camada de transformação

O contrato da camada de transformação é imediatamente anterior à tabela de
ingestão no fluxo de dados. O schema executável já está incorporado nesta
branch em `src/etl/transformation/schema.py`, acompanhado por
`docs/schema-transformacao.md`; este inventário descreve o contrato corrente,
não uma proposta pendente de merge.

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
| `id` | str de dígitos normalizados | `VARCHAR` | Inteiro não negativo, sem float intermediário |
| `integer` | `int` | `BIGINT` | Sem parte fracionária |
| `decimal` | `Decimal` | `DECIMAL(18, 6)` | Máximo seis casas, sem arredondamento silencioso |
| `percent` | `Decimal` | `DECIMAL(18, 6)` | Pontos percentuais em 0..100 |
| `date` | `date` | `DATE` | Data civil, sem hora inventada |
| `datetime` | `datetime` UTC | `TIMESTAMP` | Fuso explícito obrigatório |
| `boolean` | `bool` | `BOOLEAN` | Mapa fechado sim/não, true/false |
| `text` | `str` | `VARCHAR` | Unicode NFC, sem espaços externos |
| `list` | `list[str]` | `VARCHAR` | A carga serializa a lista como JSON; ausência produz `[]`, não nulo |

A coluna "Destino declarado" é DuckDB (`duckdb_type`, literal no código) e corresponde ao schema físico de ingestão.

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

**Limite físico:** `DIM_PESQUISA.ano_edicao` não tem coluna de origem nem
derivação homologada; fica indisponível. A proposta de família por título não
homologa uma regra para extrair o ano da edição.

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

**Limite físico:** `DIM_EMPRESA.regiao` não tem coluna de origem nem mapa
estadual homologado; fica indisponível. `estado` permanece atributo geográfico
da empresa e não deve ser convertido em região sem uma regra aprovada.

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
| `pesquisa_id` | `pesquisa_id` | `FATO_PESQUISA_PERGUNTA.sk_pesquisa` |
| `pesquisa_titulo` | `pesquisa_titulo` | Insumo de fallback apenas quando o título normalizado corresponde de forma exata e única à pesquisa corrente; registrar método, ID original e alvo; ambiguidade ou ausência mantém chave desconhecida e órfão em reconciliação |
| `enunciado`, `tipo`, `qtd_alternativas` | idem | Atributos de `DIM_PERGUNTA` |
| `confianca`, `formato_arquivo`, `col_origem` | idem | `DIM_PERGUNTA.nivel_confianca`, `.formato_arquivo_origem`, `.col_origem` |

### `ingestao_respostas`

O contrato de transformação inclui a tabela de ingestão de `respostas.csv`, mas
esta fonte não tem relação analítica no contrato físico desta entrega. O C04
(`FATO_PESQUISA_PERGUNTA`) termina em `questoes.csv`; a ligação entre
`respondent_id` e a identidade de `respondentes.csv` não está comprovada. Uma
futura `FATO_RESPOSTA` depende de reconciliação e autorização.

## Fontes usadas

- `src/etl/transformation/schema.py` e `docs/schema-transformacao.md` — contrato
  de transformação já incorporado à branch corrente.
- `docs/projeto.md` §5.1–5.2 — modelo de cubos já entregue (Data Model Canvas).
- `docs/dmc.json` — mesmo modelo, em JSON.
- `docs/Governança-de-Dados-do-Projeto.md` §3.2 — padrão de nome `asset_id`
  proposto (`<camada>.<tipo>.<nome>`), ainda não incorporado a nenhum
  artefato executável; convenção distinta da nomenclatura física
  `ingestao_<fonte>` do contrato de transformação, servindo propósitos
  diferentes (catálogo documental vs. nome físico de tabela).
- `docs/adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md` — adoção do
  DuckDB no lugar do ClickHouse.
