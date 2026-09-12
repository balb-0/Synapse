# Schema canônico tratado

MG-02, relacionado ao card #171. O contrato executável está em
[`schema.py`](../src/etl/transformation/schema.py), versão `1.0`. Cada `Field`
declara nome recebido, nome canônico, tipo, obrigatoriedade e sentinelas.
`duckdb_type` especifica o tipo da tabela de ingestão no DuckDB.

## Contrato de tipos

| Tipo | Representação Python | Destino DuckDB | Regra |
| --- | --- | --- | --- |
| id | str de dígitos normalizados | VARCHAR | Inteiro não negativo, sem float intermediário; não interpretar como medida |
| integer | int | BIGINT | Sem parte fracionária; intervalo do destino |
| decimal | Decimal | DECIMAL(18, 6) | Finito, no máximo seis casas; não arredondar silenciosamente |
| percent | Decimal | DECIMAL(18, 6) | Pontos percentuais em 0..100, inclusive |
| date | date | DATE | Data civil preservada, sem inventar hora; 1900..2299 |
| datetime | datetime UTC | TIMESTAMP | Offset explícito ou fuso de origem configurado; rejeitar horário ambíguo/inexistente |
| boolean | bool | BOOLEAN | Mapa fechado de sim/não e true/false |
| text | str | VARCHAR | Unicode NFC e espaços externos removidos; conteúdo interno preservado |
| list | list[str] | VARCHAR (JSON) | JSON array ou lista legada separada por `|`; ausência produz [] |

O DuckDB aceita nulos nas colunas opcionais; listas são serializadas como JSON
em `VARCHAR`. A origem permite distinguir lista ausente de lista vazia na
auditoria protegida. Campo obrigatório ausente impede a aceitação do registro.
Ausências opcionais não recebem zero, string vazia ou data corrente.

## Destinos e grão

| Fonte | Destino contratual MC-03 | Identidade |
| --- | --- | --- |
| pesquisas | ingestao_pesquisas | pesquisa_id |
| empresas | ingestao_empresas | empresa_id |
| clientes | ingestao_clientes | cliente_id |
| respondentes | ingestao_respondentes | Origem da participação; sem colapsar pessoas ausentes |
| questoes | ingestao_questoes | pesquisa_id + pergunta_id |
| respostas | ingestao_respostas | pesquisa_id + resposta_id |

Os nomes das tabelas são o contrato proposto para MC-03, não evidência de tabelas
já implantadas. Dados aceitos devem ter exatamente os campos canônicos mais
metadados técnicos; não devem incluir o payload bruto. Nenhum cubo, dimensão,
agregação, KPI analítico ou correspondência entre pessoas é produzido aqui.

## Regras por fonte

Todas as colunas recebidas estão enumeradas no contrato executável. Valores
inesperados em colunas desconhecidas, inclusive resíduos de exportação,
devem gerar rejeição. Colunas vazias sem nome em pesquisas podem ser removidas
somente se seus valores forem vazios. Nomes canônicos também são aceitos para
adaptadores; dois nomes que convergem ao mesmo campo causam rejeição.

Percentuais mantêm suas três origens separadas. Não escolher uma delas como
participação oficial de mercado. Datas civis do portfólio permanecem datas;
horários das participações exigem fuso explícito. `data_aprov` histórica é
opcional: não aplicar retrospectivamente uma meta de novas pesquisas.

Questões usam chave composta. Respostas consultam essa chave para obrigatoriedade
condicional e integridade, sem cruzamento analítico. Aberta/numérica exigem
valor, seleção exige alternativa e matriz exige linha e coluna. Escolha única
aceita a alternativa em `alternativa` ou `valor`, conforme formato de exportação.

Países, status e demais categorias sem domínio homologado não terão uma lista
fechada inventada a partir de um snapshot. Normalizações semânticas ficam
restritas a mapas explícitos; valores novos devem ser preservados ou sinalizados.

## Critérios de aceite

- Seis fontes, sem limite fixo de quantidade de linhas.
- Cada campo tem origem, destino, tipo, nulabilidade e regra verificáveis.
- Fonte desconhecida e colisão de nomes falham explicitamente.
- Nenhum identificador é convertido por float nem associado por similaridade.
- Evolução de schema exige nova versão e teste de compatibilidade.
- O futuro consumidor de carga recebe somente registros aceitos; checkpoint
  continua candidato até confirmação durável de aceitos e rejeitados.
