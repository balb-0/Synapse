# ADR 0005 — Checkpoint confirmado lote a lote na retomada após falha parcial

- **Status:** Aceito
- **Data:** 10/09/2026
- **Responsável pela decisão:** responsável pela camada de carga
- **Complementa:** [ADR 0003](0003-convergencia-do-insert-no-reprocessamento-do-lote.md)

## Contexto

O fluxo orquestrado já sabia retomar a extração de uma fonte a partir de um
checkpoint de posição (linha) dentro do mesmo objeto, quando uma tentativa
anterior não tinha ido até o fim. Esse checkpoint, porém, só era confirmado
depois que **todos** os lotes extraídos daquela chamada tivessem carregado
com sucesso — nunca lote a lote.

Isso aparece quando a carga falha no meio de um objeto com vários lotes: por
exemplo, o lote 1 termina, grava sua linha e seu registro de execução, e o
lote 2 falha (erro transitório de escrita, tabela de destino indisponível,
etc.). Como o checkpoint só seria confirmado ao final de todos os lotes, essa
falha não deixa nenhum checkpoint gravado — nem o do lote 1, que já tinha
terminado. A próxima tentativa do mesmo objeto recomeça a extração do início,
reextraindo e retransformando também o lote 1.

O insert principal já converge ao reexecutar um lote com o mesmo `run_id` e
`batch_id` (ADR 0003): a linha do lote 1 não é duplicada. O problema é outro —
a identidade já carregada é lida uma única vez, no início da chamada, e por
isso a retransformação do lote 1 nessa segunda tentativa o reclassifica como
duplicado, não mais como aceito. A linha em si não se perde nem duplica, mas o
registro de execução do lote 1 é sobrescrito para refletir essa reclassificação
da retomada, não o que de fato tinha acontecido na tentativa original — o
histórico de quanto foi de fato aceito por lote deixa de ser confiável a cada
retomada.

## Decisão

**O checkpoint de cada lote passa a ser confirmado assim que aquele lote
específico termina de carregar, não apenas depois que todos os lotes de uma
chamada tiverem passado.**

- O checkpoint de cada lote extraído passa a acompanhar o resultado
  transformado do início ao fim (extração, transformação e carga), em vez de
  ser descartado depois da extração.
- A carga confirma o checkpoint de um lote logo após gravá-lo, antes de seguir
  para o próximo. Uma falha em um lote interrompe a sequência sem confirmar o
  checkpoint dele nem dos que viriam depois; os checkpoints dos lotes
  anteriores, já confirmados individualmente, permanecem.
- A próxima tentativa do mesmo objeto retoma a extração exatamente de onde o
  último lote confirmado parou: os lotes já confirmados não são reextraídos
  nem retransformados, só o que ficou pendente é tentado de novo.

Não foi criada nenhuma tabela nova nem contrato novo: o checkpoint por fonte e
o método que o confirma já existiam; a mudança é só o momento em que a
confirmação acontece.

## Consequências

### Positivas

- Uma falha parcial não obriga a repetir trabalho já confirmado: só o que
  ficou pendente é reextraído, retransformado e recarregado.
- O registro de execução de um lote já confirmado deixa de ser sobrescrito por
  uma retomada: como ele não volta a ser reextraído, nenhuma nova tentativa de
  carga é feita para ele, e seu registro original permanece.

### Negativas e riscos

- A confirmação do checkpoint de um lote é uma escrita separada da transação
  que grava esse mesmo lote. Uma falha exatamente entre as duas (janela
  mínima, sem operação de rede no meio) deixaria o lote gravado sem o
  checkpoint correspondente; a próxima tentativa reextrai esse lote
  específico, que converge sem duplicar linha, mas volta a sofrer o mesmo
  efeito colateral no registro de execução que esta decisão busca evitar.
  Risco aceito: a janela é interna a uma única conexão do processo. Desde a
  Sprint 4, a carga reconhece as linhas que o próprio `run_id`+`batch_id` já
  gravou e as conta como carregadas, então essa reexecução também reconcilia
  sem reclassificar contagem.
- Uma identidade repetida em dois lotes diferentes de uma mesma leitura ficava
  fora desta decisão. **Resolvido na Sprint 4:** `transform_object` decide a
  identidade sobre todos os lotes do objeto e a carga confere contra o estado
  persistido (ver a atualização do ADR 0003). A retomada também preserva a
  posição absoluta de cada ocorrência (`BatchMetadata.source_offset`), para que
  participações identificadas por checksum+posição não colidam após um
  checkpoint.
- O checkpoint continua identificado por fonte, não por execução: se duas
  versões diferentes do mesmo objeto pudessem ser processadas
  concorrentemente, a confirmação mais recente prevaleceria independente de
  qual delas é a mais nova. Não é um cenário novo introduzido aqui — é uma
  característica do contrato de checkpoint já existente.

## Alternativas consideradas

| Alternativa | Avaliação |
| :--- | :--- |
| Manter a confirmação só ao final de todos os lotes, aceitando a reextração completa numa retomada | Não selecionada: a reextração reclassifica lotes já confirmados como duplicados, corrompendo o registro de execução deles a cada retomada. |
| Confirmar o checkpoint só ao final, mas gravar à parte quais lotes já tinham sido aceitos, para a retomada evitar a reclassificação sem mudar o checkpoint | Precisaria de uma tabela nova mantida em sincronia com o checkpoint existente, para resolver o mesmo problema que confirmar lote a lote já resolve com a estrutura atual. Não selecionada. |
| Confirmar o checkpoint lote a lote, dentro do laço de carga | Selecionada. Reaproveita o contrato de checkpoint já existente; muda só o momento da confirmação. |
