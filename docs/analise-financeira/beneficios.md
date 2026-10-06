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
