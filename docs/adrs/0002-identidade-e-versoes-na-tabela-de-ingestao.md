# ADR 0002 — Identidade e versões na tabela de ingestão tratada

- **Status:** Aceito para a camada de carga em 10/09/2026; pendente de
  ratificação pelo grupo
- **Data:** 10/09/2026
- **Responsável pela decisão:** responsável pela camada de carga
- **Complementa:** [ADR 0001](0001-arquitetura-etl-python-prefect-minio-duckdb.md)

## Contexto

As seis fontes do projeto são snapshots que o parceiro reexporta. Não há
frequência de publicação confirmada, e uma reexportação pode trazer o mesmo
registro com um campo corrigido.

Ao declarar as constraints das tabelas de ingestão, a pergunta que estava
implícita precisou de resposta: **o que é uma linha da tabela de ingestão?**
Duas partes do projeto já respondiam de formas diferentes, sem que a divergência
tivesse sido notada:

- o contrato canônico da transformação e o inventário de contratos dimensionais
  declaram uma chave por fonte, como se cada chave ocupasse uma linha;
- a classificação de duplicidade da transformação trata "mesma chave, conteúdo
  diferente" como conflito de identidade e rejeita o registro, de modo que a
  primeira versão de cada registro permanece para sempre;
- a fonte de participação, que não tem chave declarada, usa como identidade a
  ocorrência física (arquivo e linha) e por isso é reingerida por inteiro a cada
  reexportação — comportamento oposto ao das outras cinco.

## Decisão

**Uma linha da tabela de ingestão corresponde a uma linha da fonte, e o mesmo
registro pode ocupar mais de uma linha, uma por versão de conteúdo.**

Decorrem daí:

1. A chave primária de cada tabela de ingestão é a identidade de idempotência
   (`idempotency_key`), que combina chave de negócio e conteúdo. Não é a chave
   de negócio: essa escolha exigiria sobrescrever a versão anterior.
2. A unicidade declarada é chave de negócio mais `content_checksum`. A chave
   fica registrada no banco sem proibir versão nova do mesmo registro.
3. Cada linha carrega a proveniência completa — qual arquivo, qual linha, qual
   execução, qual lote, quando e qual versão do contrato.
4. Cada fonte com chave de negócio tem uma view `ingestao_<fonte>_atual` com a
   linha mais recente por chave e as mesmas colunas da tabela. Quem quer o
   estado corrente consulta a view; quem quer o histórico consulta a tabela.
5. A fonte de participação continua sem chave de negócio e sem view de estado
   atual, com a identidade na ocorrência física.

### Por que preservar versões

- O modelo dimensional já registra o versionamento de dimensão (SCD Tipo 2)
  como evolução prevista, e atribui a responsabilidade ao processo de carga. Sem
  as versões na camada de ingestão, adotá-lo exigiria reprocessar todos os
  snapshots.
- A reconciliação da carga precisa que "rejeitado" signifique defeito de dado.
  Contar correção do parceiro como rejeição faz o relatório de qualidade acusar
  problema onde houve conserto.
- Os arquivos brutos permanecem imutáveis no armazenamento de objetos, então o
  histórico existe de qualquer forma. O que a decisão evita é depender de
  reprocessamento para recuperá-lo.

## O que ainda não está feito

A camada anterior **continua rejeitando a correção** como conflito de
identidade. O destino está preparado para versões e recebe uma só. A mudança na
classificação de duplicidade é acompanhada em issue própria no board.

**Acoplamento que precisa ser respeitado quando essa mudança acontecer:** a
tabela de controle `_loaded_identity` guarda hoje uma linha por chave de
negócio, com o último conteúdo visto. Se a classificação passar a aceitar
versões sem que essa tabela passe a ser chaveada pela identidade de
idempotência, o reprocessamento explícito (a execução de backfill que ignora o
controle por objeto de propósito) classifica uma versão antiga como aceita e a
carga viola a chave primária, derrubando o lote inteiro.

Antes desta ADR o mesmo cenário inseria linha duplicada em silêncio. A
constraint transformou corrupção silenciosa em falha visível, e é por isso que
as duas mudanças precisam andar juntas.

Dois testes em `tests/load/test_identity_coupling.py` servem de canário: um
falha se a classificação mudar, o outro falha se a tabela de controle mudar.
Cada um aponta para esta ADR na mensagem de falha.

## Consequências

### Positivas

- Correção do parceiro deixa de ser tratada como defeito de dado.
- O histórico necessário ao versionamento de dimensão passa a existir na camada
  de carga.
- Constraint no banco recusa carga duplicada mesmo que a deduplicação anterior
  falhe.
- As views de estado atual evitam que cada consumidor escreva sua própria
  janela de ordenação e erre a contagem.

### Negativas e riscos

- A tabela de ingestão cresce com as versões. Não há política de retenção
  definida para elas.
- Quem consultar a tabela em vez da view precisa saber que há mais de uma linha
  por chave. As views existem para tornar isso improvável, não impossível.
- A fonte de participação continua sendo reingerida por inteiro a cada
  reexportação. Resolver exige uma chave para a participação, que é pergunta ao
  parceiro.
- A renomeação das tabelas para `ingestao_<fonte>` alcança leitores escritos
  antes dela.

## Compatibilidade com o nome anterior

As tabelas passaram a se chamar `ingestao_<fonte>`, alinhadas ao que o contrato
da transformação e o inventário de contratos dimensionais já declaravam. Para
que leitores anteriores continuem funcionando sem alteração, o contrato cria uma
view com o nome sem prefixo apontando para a tabela nova, com
`CREATE VIEW IF NOT EXISTS` — seguro também em banco antigo, onde o nome ainda
pertence a uma tabela.

Essas views são **transitórias**. Podem ser removidas quando nenhum leitor usar
mais o nome sem prefixo. O leitor conhecido é o teste de integração do fluxo
orquestrado, que consulta `empresas` pelo nome antigo.

## Alternativas consideradas

| Alternativa | Avaliação |
| :--- | :--- |
| Uma linha por chave, correção recusada | É o comportamento anterior à ADR. Não foi selecionada porque congela a primeira versão de cada registro e classifica correção como defeito, e porque não é coerente entre as fontes: a participação já duplica. |
| Uma linha por chave, correção substitui (upsert) | Mantém a tabela no estado corrente e dispensa as views. Não foi selecionada porque descarta o histórico que o versionamento de dimensão previsto exige, e porque a substituição pertence à etapa de idempotência e reprocessamento. |
| Uma linha por chave e versão, com proveniência | Selecionada. Preserva o histórico, mantém a idempotência por conteúdo e permite derivar o estado corrente por view. |

## Critérios para ratificar a decisão

- o grupo aprovar a semântica de versões na camada de ingestão;
- a classificação de duplicidade aceitar correção como versão nova, com a
  tabela de controle chaveada pela identidade de idempotência;
- a matriz regra–teste da transformação registrar a nova classificação;
- uma execução com reprocessamento explícito concluir sem violar constraint;
- a política de retenção das versões ser definida ou registrada como pendência
  aceita.
