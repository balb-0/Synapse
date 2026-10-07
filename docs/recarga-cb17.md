# CB-17: validação de recarga e troca da geração

Esta evidência usa exclusivamente a fixture sintética dos testes de analytics.
Os identificadores abaixo (`run-test-1`, `run-test-2` e `fixture-cb17`) não
identificam cargas reais nem pessoas.

## Resultado antes/depois

| Etapa | Identificador | Resultado observado |
| --- | --- | --- |
| Geração vigente antes da recarga | `run-test-1` | Publicação completa; `current.json` aponta para a primeira geração |
| Recarga/publicação de teste | `run-test-2` | Sete tabelas publicadas, com as mesmas linhas e esquemas da fixture |
| Geração vigente depois da recarga | `run-test-2` | `current.json` troca para a nova geração somente ao final |
| Falha injetada durante a publicação | `fixture-cb17-falha-digest` | A geração anterior continua vigente; não sobra diretório pendente |

## Convergência dos cubos

O cenário de recarga analítica carrega novamente os fatos a partir da fixture,
reconcilia C01–C04 e confirma que a carga substitui os fatos da execução
anterior, sem acumular linhas. Também foi verificado que uma alteração de
origem durante a recarga produz divergência explícita na reconciliação, em vez
de ser aceita como cubo vazio.

## Critérios confirmados

- a publicação seguinte gera uma pasta imutável distinta e troca o ponteiro
  `current.json` atomicamente;
- o manifesto da geração anterior permanece íntegro após a troca;
- falha antes da troca preserva a geração anterior e remove o estado pendente;
- recarga convergente e falha de origem são estados diferentes e observáveis.

O recibo estruturado está em
[`docs/evidencias/cb17/recarga-fixture.json`](evidencias/cb17/recarga-fixture.json).

