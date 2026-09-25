# DDL v1 das dimensões analíticas

O contrato executável está em `src/etl/analytics/dimensions_ddl.py` e sua
representação versionada em `sql/duckdb/002_dimensoes.sql`. Aplique o arquivo
após `001_ingestao_tratada.sql` e antes das DDLs dos fatos. Para conferir a
simetria, execute `PYTHONPATH=src python -m etl.analytics.dimensions_ddl --check`.
`dimension_statements()` devolve os comandos na ordem de aplicação.

| Dimensão | Identidade de origem ou valor canônico | Chave substituta |
| :--- | :--- | :--- |
| `DIM_TEMPO` | data civil ISO | `sk_tempo` |
| `DIM_PESQUISA` | `pesquisa_id` | `sk_pesquisa` |
| `DIM_STATUS_PESQUISA` | status normalizado | `sk_status` |
| `DIM_AREA` | área normalizada | `sk_area` |
| `DIM_TIPO_PESQUISA` | tipo normalizado | `sk_tipo` |
| `DIM_PERFIL_PESQUISA` | (`complexidade`, `tipo_resposta`) normalizados | `sk_perfil` |
| `DIM_EMPRESA` | `empresa_id` | `sk_empresa` |
| `DIM_PESSOA` | `cliente_id` | `sk_pessoa` |
| `DIM_PERGUNTA` | (`pesquisa_id`, `pergunta_id`) | `sk_pergunta` |
| `DIM_FAMILIA_PESQUISA` | título normalizado proposto | `sk_familia` |
| `DIM_FONTE_DADO` | `source` da ingestão | `sk_fonte` |
| `DIM_EXECUCAO_CARGA` | (`source`, `run_id`) | `sk_carga` |

Todas as chaves substitutas são `VARCHAR` com SHA-256 hexadecimal. A carga
deve normalizar cada parte conforme o schema de transformação antes de chamar
`canonical_key(*parts)` e `surrogate_key(nome_da_dimensao, *parts)`. A
codificação de cada parte é `-1:` para `NULL`, ou comprimento em caracteres,
dois pontos e o valor para texto. O material do hash é
`v1|<nome_da_dimensao>|K|<natural_key>`. Essa codificação distingue tuplas
como (`1`, `23`) e (`12`, `3`), assim como ausência e texto vazio. A tabela
guarda `natural_key` com `UNIQUE`, a chave substituta é `PRIMARY KEY`, e os
`CHECK`s recalculam a chave canônica a partir das colunas de identidade e o
hash a partir dela. Para `DIM_TEMPO`, a identidade é a data civil em formato
ISO. Para `DIM_PERFIL_PESQUISA`, as duas partes integram a identidade, inclusive
quando uma delas é nula. Uma colisão de SHA-256, uma chave canônica divergente
dos atributos ou uma segunda identidade natural para a mesma chave falha na
inserção, em vez de sobrescrever uma linha.

Cada dimensão recebe uma linha `is_unknown = TRUE` de chave
`unknown_key(nome_da_dimensao)`, calculada com domínio separado
`v1|<nome_da_dimensao>|U`. Sua `natural_key` e identidade de origem são nulas.
Uma FK opcional por ausência estrutural fica `NULL`; uma FK órfã usa essa chave
somente com registro da identidade original e do motivo na reconciliação.
Reaplicar a DDL conserva linhas existentes e não duplica sentinelas. A DDL
cria estruturas e sentinelas; não carrega dimensões a partir da ingestão.

O carregador deve normalizar a tupla antes do insert ou upsert; as constraints
do banco verificam sua correspondência com os atributos gravados. Para
`DIM_PERGUNTA`, o mesmo `pergunta_id` em outra
pesquisa gera chave diferente. Para `DIM_PERFIL_PESQUISA`, uma parte ausente
permanece `NULL` na tupla, sem confundir a ausência com string vazia. Se ambas
as partes estiverem ausentes, a carga usa `unknown_key("DIM_PERFIL_PESQUISA")`;
não insere perfil conhecido com duas partes nulas. `DIM_TEMPO` exige ano,
trimestre, mês, dia, dia da semana ISO (1 a 7) e indicador de fim de mês
coerentes com a data civil; esses atributos ficam nulos na sentinela. Valores
de status, área, tipo e perfil devem usar a mesma normalização em todos os
cubos. Um valor de status não reconhecido mantém as três flags nulas. Não se
preenchem `ano_edicao` ou `regiao`: não há fonte ou regra homologada. Família
de pesquisa é proposta por título normalizado e seu estado de homologação
deve ser registrado; não se publica como classificação aprovada por padrão.
`nivel_hierarquico` e `agrupamento_departamento` ficam nulos até haver regra
aprovada. `cargo` e `departamento` são restritos; e-mail não integra
`DIM_PESSOA`.
