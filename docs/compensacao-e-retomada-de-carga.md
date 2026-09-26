# Compensação e retomada de execuções com falha parcial

Quando a carga de um objeto falha no meio — um lote gravou, o seguinte não —
alguém precisa decidir o que a próxima tentativa deve refazer. Este documento
registra essa decisão no fluxo orquestrado: o que uma falha parcial deixa
registrado, e a partir de que ponto exato a tentativa seguinte retoma.

A implementação está em
[`src/etl/orchestration/flow.py`](../src/etl/orchestration/flow.py) — nas
tarefas `transform` e `load` e no flow `ingest_object`. A decisão está
registrada em
[ADR 0005](adrs/0005-checkpoint-confirmado-lote-a-lote-na-retomada.md).

## Escopo

Este documento cobre a retomada de um objeto cuja carga falhou entre lotes:

- como a extração já resumia a leitura a partir de um checkpoint de posição
  antes desta decisão, e por que a confirmação desse checkpoint só ao final
  de todos os lotes não bastava para uma falha parcial;
- como o checkpoint de cada lote passa a ser confirmado assim que aquele lote
  termina de carregar, em vez de só depois que o objeto inteiro tiver
  passado;
- o que uma falha parcial deixa registrado — o lote perdido com status de
  falha, e o checkpoint no último lote confirmado antes dela;
- o que a tentativa seguinte do mesmo objeto faz a partir disso.

## Fora de escopo

- **Decidir quando reagendar uma nova tentativa.** Este documento cobre o que
  a tentativa seguinte encontra e retoma, não quando ou com que política de
  espera ela é disparada — isso é parametrização de retry e timeout do
  próprio fluxo orquestrado, já registrada em código à parte desta decisão.
- **A convergência do insert de um lote reexecutado com o mesmo `run_id` e
  `batch_id`.** Já resolvida antes desta decisão — ver
  [ADR 0003](adrs/0003-convergencia-do-insert-no-reprocessamento-do-lote.md)
  e [`repositorio-de-carga.md`](repositorio-de-carga.md).
- **Deduplicação de linha e identidade de idempotência.** Assunto da
  transformação e do [ADR 0002](adrs/0002-identidade-e-versoes-na-tabela-de-ingestao.md);
  este documento não muda o que conta como duplicata.
- **Uma identidade repetida em dois lotes diferentes da mesma leitura (não
  entre tentativas).** Tratada à parte na Sprint 4 por `transform_object` e
  pela conferência contra o estado persistido na carga — ver a seção
  "Negativas e riscos" do ADR 0005.
- **Testes gray-box de ponta a ponta contra uma instância real.** Este
  documento descreve o comportamento por trás dos testes da tarefa `load`; um
  roteiro de integração mais amplo é um documento à parte.

## Por que confirmar o checkpoint só ao final de todos os lotes não bastava

A extração já sabia continuar de onde parou: um checkpoint guarda a posição
(linha) e a versão do objeto lido, e o extrator pula o que já foi confirmado
antes de retomar a leitura. O que faltava era o momento certo de confirmar
essa posição.

Antes desta decisão, o checkpoint só era confirmado depois que **todos** os
lotes extraídos de uma chamada tivessem carregado com sucesso. Uma falha no
lote 2 de um objeto com 3 lotes não deixava nenhum checkpoint confirmado —
nem o do lote 1, que já tinha terminado. A tentativa seguinte reextraía e
retransformava o objeto inteiro, incluindo o lote 1.

Isso não duplicava a linha do lote 1: o insert principal já converge ao
reexecutar o mesmo `run_id`/`batch_id` (ADR 0003). O problema era outro — a
identidade já carregada é lida uma única vez, no início da chamada, então
retransformar o lote 1 nessa segunda tentativa o reclassifica como
duplicado, não mais como aceito. A linha continua lá, mas o registro de
execução do lote 1 é sobrescrito para refletir essa reclassificação da
retomada, apagando o que de fato tinha acontecido na tentativa original.

## Confirmação lote a lote

O checkpoint de cada lote extraído passa a acompanhar o resultado
transformado do início ao fim — da extração até a carga —, em vez de ser
descartado logo depois da extração. A carga confirma esse checkpoint assim
que grava o lote correspondente, antes de seguir para o próximo:

```python
for result, metadata, checkpoint in results:
    outcome = repo.load_batch(result, metadata)
    repo.commit(checkpoint)
    ...
```

Uma falha em `load_batch` interrompe o laço antes do `commit` daquele lote:
o checkpoint dele não avança, e os lotes seguintes nem chegam a ser
tentados. Os checkpoints dos lotes anteriores, já confirmados
individualmente, permanecem.

## O que uma falha parcial deixa registrado

Depois de uma falha entre lotes, o estado gravado é:

- o lote que falhou aparece em `_batch_metadata` com status de falha e
  contagens zeradas (mecanismo já existente, ver
  [`ddl-ingestao.md`](ddl-ingestao.md));
- o checkpoint da fonte aponta para o último lote que terminou de carregar
  antes da falha — não para o início do objeto, nem para o lote que falhou.

## O que a tentativa seguinte retoma

Ao reprocessar o mesmo objeto (mesma referência, mesmo conteúdo), o flow lê o
checkpoint confirmado e o repassa à extração. Como a versão do objeto não
mudou, o checkpoint continua válido e a extração pula as linhas já
confirmadas, emitindo somente os lotes a partir do que ficou pendente — cada
um com a posição absoluta (`source_offset`) que tinha na fonte inteira, e não
uma posição reiniciada em zero. Esses
lotes são os únicos retransformados e recarregados: os que já tinham sido
confirmados não voltam a ser lidos, então seu registro de execução não é
tocado de novo.

Se a falha aconteceu antes de qualquer lote confirmar, o checkpoint continua
inexistente para este objeto e a tentativa seguinte lê do início — mesmo
comportamento de sempre, sem lote nenhum para preservar.

## Testes

```bash
python -m unittest discover -s tests/orchestration -t .
```

A suíte cobre: que uma sequência de lotes bem-sucedidos avança o checkpoint
até o último; que um lote que falha não avança o checkpoint além do último
lote confirmado antes dele, e que o lote que falhou não grava nada; e que
retomar com apenas o lote pendente completa a carga sem perder nem duplicar
registro algum. `tests/orchestration/test_integridade_entre_lotes.py` cobre a
retomada de participações repetidas legitimamente (identidade por posição) e
duplicatas e conflitos atravessando a fronteira entre lotes.
