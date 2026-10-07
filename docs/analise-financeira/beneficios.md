# FN-04 — Benefícios financeiros condicionais

**Data-base:** 06/10/2026. **Moeda:** BRL. **Natureza:** cenários de capacidade de trabalho potencialmente liberada, sem medição do parceiro e sem economia de caixa confirmada.

## Base factual e limite

`docs/projeto.md` e `docs/matriz-evidencias-problem-canvas.md` registram trabalho manual, cruzamentos e retrabalho como problemas, mas também afirmam que horas, custos e retrabalho não foram medidos. Portanto, nenhuma quantidade de relatório, hora economizada ou erro evitado abaixo é observação. A existência dos quatro cubos e reports tampouco prova adoção ou substituição de trabalho manual.

Como valor da hora de análise, usamos o perfil ABI-02 do [Anexo II vigente da Portaria SGD/MGI nº 750/2023](https://www.gov.br/governodigital/pt-br/contratacoes-de-tic/legislacao/modelo-de-contratacao-de-servicos-de-desenvolvimento-manutencao-e-sustentacao-de-software/portaria-sgd-mgi-no-750-de-20-de-marco-de-2023): `R$ 11.071,12 × 2,02 ÷ 160 h = R$ 139,77289/h`. É custo de referência de capacidade, não remuneração do parceiro. O benefício econômico depende de a hora liberada ser efetivamente realocada a trabalho de valor equivalente; economia de caixa depende de despesa evitada ou reduzida.

## Hipóteses mensais por cenário

As três parcelas são mutuamente exclusivas: **preparação** é montar e atualizar o relatório normal; **retrabalho** é refazer uma entrega por mudança ou inconsistência operacional; **erro** é corrigir um defeito detectado após a entrega. Um evento classificado como erro não pode reaparecer como retrabalho. O cenário considera apenas tarefas que a solução poderia reduzir após adoção e treinamento; não supõe eliminação de todo o trabalho de análise.

| Entrada hipotética | Cauteloso | Base | Alto | Como confirmar |
| :--- | ---: | ---: | ---: | :--- |
| Relatórios ou atualizações por mês | 4 | 8 | 16 | Contar entregas comparáveis em três meses. |
| Horas de preparação liberadas por relatório | 2 | 4 | 6 | Cronometrar antes/depois, excluindo análise que permanece humana. |
| Casos de retrabalho evitáveis por mês | 1 | 2 | 4 | Registrar causa e evitar contar o mesmo caso como erro. |
| Horas por caso de retrabalho | 1 | 1 | 1 | Apontamento de trabalho. |
| Erros pós-entrega evitáveis por mês | 1 | 1 | 2 | Registro de incidentes e causa raiz. |
| Horas por erro | 1 | 2 | 2 | Apontamento de correção. |
| **Horas potencialmente liberadas/mês** | **10** | **36** | **104** | `relatórios×horas + casos×horas + erros×horas`. |

Os números são deliberadamente testáveis e não são estimativas estatísticas de um conjunto observado. O cenário alto exige 16 entregas mensais e 104 horas liberáveis; sem esse volume, ele não deve ser usado como previsão central.

## Valoração por período

| Parcela de capacidade liberada | Cauteloso (R$/mês) | Base (R$/mês) | Alto (R$/mês) |
| :--- | ---: | ---: | ---: |
| Preparação de relatório | 1.118,18 | 4.472,73 | 13.418,20 |
| Retrabalho | 139,77 | 279,55 | 559,09 |
| Correção de erros | 139,77 | 279,55 | 559,09 |
| **Benefício econômico potencial/mês** | **1.397,73** | **5.031,82** | **14.536,38** |
| **Em 12 meses, sem rampa de adoção** | **16.772,75** | **60.381,89** | **174.436,57** |

Fórmula por mês: `(N_rel×h_rel + N_retrabalho×h_retrabalho + N_erros×h_erro) × R$ 139,77289/h`. Exemplo base: `(8×4 + 2×1 + 1×2)×139,77289 = R$ 5.031,82/mês`. Os valores anuais são o resultado de 12 vezes o valor mensal **antes** do arredondamento e representam capacidade, não receita nem redução comprovada de desembolso.

As parcelas da tabela são arredondadas individualmente para exibição. Por isso, somá-las depois de arredondadas pode diferir em R$ 0,01 do total, que usa as horas agregadas e a tarifa com precisão integral.

## Validação de ganho e dinheiro

**Economia de caixa confirmada: indisponível.** O modelo não afirma redução de folha ou contrato. Para reconhecer uma economia de caixa, identificar a despesa específica evitada, período, aprovação e prova contábil. Para reconhecer benefício de capacidade, identificar a tarefa de destino e seu valor; não somar essa mesma hora novamente como despesa evitada.

No piloto, comparar grupos de relatórios equivalentes antes e depois: registrar identificador, complexidade, responsável, início/fim de preparação, revisões e erros pós-entrega. Medir a taxa de adoção e descontar relatórios que continuem manuais. Se a adoção efetiva for `a` (0 a 1), `benefício realizado elegível = benefício bruto × a`, desde que as horas por entrega também sejam verificadas. FN-05 usa 100% apenas como limite superior de cenário; uma rampa de adoção desloca o ponto de equilíbrio.

Benefícios de qualidade, transparência e decisão melhor podem ser relevantes, mas ficam **não monetizados** enquanto não houver método de atribuição e evidência. Não adicionamos receita hipotética por decisões melhores nem valor financeiro por erros sem custo conhecido além das horas de correção explicitadas.
