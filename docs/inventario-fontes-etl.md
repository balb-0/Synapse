# Inventário das fontes de dados do ETL

Este inventário reúne as seis bases entregues pelo Sindusfarma para a
construção do ETL. A análise considera a versão v3 dos arquivos,
disponibilizada no Drive do parceiro, e o dicionário de dados recebido.

As bases brutas não foram copiadas para o repositório, pois contêm dados de
empresas, identificadores pessoais, e-mails e respostas textuais. Neste
documento são registrados apenas a estrutura e os volumes observados.

## Fontes disponíveis

| Fonte | Conteúdo e grão | Formato | Chave(s) identificada(s) | Volume | Atualização | Autenticação | Disponibilidade |
| :--- | :--- | :--- | :--- | ---: | :--- | :--- | :--- |
| `pesquisas.csv` | Cadastro e ciclo de vida das pesquisas. Uma linha por pesquisa. | CSV separado por `;`, codificado em UTF-8 com BOM. Possui 33 colunas, das quais 22 têm nome. | Identificador: `id`. É referenciado por `respondentes.id_pesq`, `questoes.pesquisa_id` e `respostas.pesquisa_id`. | 366 registros | **Pendente** | **Pendente** | Arquivo v3 disponível; recorrência pendente |
| `empresas.csv` | Cadastro das empresas. Uma linha por empresa. | CSV separado por `;`, codificado em UTF-8 com BOM. Possui 9 colunas. | Identificador: `ID`. É referenciado por `clientes.id_empresa`, `respondentes.id_empresa` e `respostas.id_empresa`. | 779 registros | **Pendente** | **Pendente** | Arquivo v3 disponível; recorrência pendente |
| `clientes.csv` | Cadastro de contatos vinculados às empresas. Uma linha por cliente ou contato. | CSV separado por `;`, codificado em UTF-8 com BOM. Possui 5 colunas. | Chave candidata: `id_cliente`. O campo `id_empresa` referencia `empresas.ID`. | 5.430 registros | **Pendente** | **Pendente** | Arquivo v3 disponível; recorrência pendente |
| `respondentes.csv` | Participações de empresas ou clientes nas pesquisas. O grão provável é uma linha por participação. | CSV separado por `;`, codificado em UTF-8 com BOM. Possui 6 colunas. | Chave candidata composta por `id_pesq`, `id_empresa` e `id_cliente`. Os campos se relacionam, respectivamente, com pesquisas, empresas e clientes. | 18.735 registros | **Pendente** | **Pendente** | Arquivo v3 disponível; recorrência pendente |
| `questoes.csv` | Perguntas e configurações dos questionários. Uma linha por pergunta. | CSV separado por `;`, codificado em UTF-8 com BOM. Possui 13 colunas. | Identificador: `id_pergunta`. O campo `pesquisa_id` referencia a pesquisa associada. | 3.297 registros | **Pendente** | **Pendente** | Arquivo v3 disponível; recorrência pendente |
| `respostas.csv` | Respostas simples, alternativas e células de matriz. Cada linha representa um item de resposta, não um questionário completo. | CSV separado por `;`, codificado em UTF-8 com BOM. Possui 9 colunas. | Identificador: `id_resposta`. Possui referências para pesquisa, pergunta e empresa. O vínculo de `respondent_id` com a base de respondentes ainda não foi confirmado. | 281.835 registros | **Pendente** | **Pendente** | Arquivo v3 disponível; recorrência pendente |

O conjunto possui **310.442 registros**. Os volumes da versão v3 correspondem
aos números apresentados no dicionário de dados do parceiro. Em relação à
versão analisada anteriormente, `questoes.csv` passou de 231 para 3.297
registros e `respostas.csv` passou de 20.607 para 281.835. As outras quatro
bases não tiveram alteração de volume.

As colunas marcadas como pendentes têm a mesma situação nas seis fontes. Os
arquivos não informam quando ou com que frequência são atualizados. O pacote
atual foi recebido pelo Drive, mas ainda não sabemos como será feito o acesso
automatizado aos dados. Também precisamos confirmar com o parceiro se novas
versões serão disponibilizadas de forma recorrente.

## Observações sobre as chaves

Não foram encontradas duplicatas entre as chaves completas identificadas nas
seis bases. Ainda assim, foram observados dois casos que precisam ser tratados
com cuidado:

- `clientes.csv` possui um registro com `id_cliente` preenchido como `s/i`;
- `respondentes.csv` possui 857 registros em que a chave candidata está
  incompleta.

Também não há, até o momento, uma regra confirmada para relacionar
`respostas.respondent_id` a `respondentes.id_cliente`. Essa relação não deve ser
criada apenas pela semelhança dos valores. Os identificadores de pesquisa entre
as bases também precisam ser conciliados antes da integração definitiva.

## Informações a confirmar com o parceiro

| Informação pendente | Situação atual |
| :--- | :--- |
| Sistema de origem de cada arquivo | O projeto cita planilhas, SurveyMonkey, Trello, sistema interno, n8n e acervo, mas ainda não há um mapeamento entre cada sistema e cada CSV. |
| Frequência de atualização | Os arquivos não informam se a atualização é diária, semanal, mensal ou sob demanda. |
| Data de referência dos dados | Não existe um campo ou metadado que indique quando cada arquivo foi extraído. A data de download não representa a data dos dados. |
| Forma de acesso | O pacote atual foi recebido pelo Drive. Ainda precisamos confirmar se as próximas versões continuarão nesse formato ou se haverá acesso por API, banco ou diretório compartilhado. |
| Autenticação | Ainda não foram informados credenciais, conta técnica, token, VPN ou outro mecanismo para uma extração automatizada. |
| Tipo de carga | Não foi confirmado se cada entrega corresponde a uma carga completa ou incremental. |
| Identificação de alterações | As bases não apresentam uma coluna comum de criação ou atualização que possa ser usada como controle incremental. |
| Timezone | O fuso horário das datas e dos horários não está informado. |
| Identidade entre as bases | Falta confirmar a correspondência dos IDs de pesquisa e a relação entre `respondent_id` e os clientes ou participantes. |
| Participação de mercado | Falta definir qual é a referência oficial entre `part_mercado`, `% de mercado` e `market_share`. |

Esses pontos serão levantados com o parceiro. Até que sejam confirmados, a
versão v3 será tratada como um conjunto de arquivos estático, recebido por meio
do Drive, e não como uma fonte automatizada ou continuamente disponível.
