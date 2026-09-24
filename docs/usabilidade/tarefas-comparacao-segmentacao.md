# Tarefas de usabilidade — comparação temporal e segmentação simultânea

Tarefas que exercitam **comparação entre períodos equivalentes** e **mais de
um filtro aplicado ao mesmo tempo**. Contrato e convenções de medição são os
de [`tarefas-navegacao-filtros.md`](tarefas-navegacao-filtros.md). Duas regras
específicas deste grupo, herdadas dos critérios de aceite (§6.1.1, RF01 e
RF03):

- **Períodos equivalentes**: comparação temporal só vale entre janelas
  comparáveis (mesmo tamanho, mesmo marco); o critério de sucesso sempre
  exige que o participante **identifique o campo de data** em uso —
  `data_solicitacao` é o padrão e qualquer outro marco precisa aparecer
  rotulado.
- **Segmentação simultânea**: com dois ou mais filtros ativos, o participante
  precisa saber dizer **qual recorte está vendo** — filtros acumulados sem
  consciência do recorte são a principal fonte de leitura errada.

## T-CMP-01 — Comparar dois períodos equivalentes do portfólio

- **Perfil-alvo:** UC03 (gestor).
- **Situação real:** "A diretoria perguntou se o volume de pesquisas
  solicitadas cresceu em relação ao período anterior. Responda com os números
  da solução."
- **Passos esperados:** D01 → aplicar período A (janela padrão por
  `data_solicitacao`) → registrar a contagem → aplicar o período B
  equivalente → comparar.
- **Critério de sucesso:** apresenta as duas contagens, diz qual período teve
  mais solicitações **e identifica o campo de data usado** na comparação.
- **Tempo aceitável:** 4 minutos.

## T-CMP-02 — Ler a evolução mensal sem misturar marcos temporais

- **Perfil-alvo:** UC01 (analista da Central).
- **Situação real:** "Aponte em qual mês houve mais entradas de pesquisas e
  confirme qual data define 'entrada' nesse gráfico."
- **Passos esperados:** D01 → visual de evolução temporal → identificar o
  pico → conferir o rótulo/legenda do marco temporal.
- **Critério de sucesso:** aponta o mês de pico e nomeia o marco temporal do
  visual; se o participante presumir outro marco ("é a data de entrega?"),
  a dúvida registrada vira achado sobre a rotulagem.
- **Tempo aceitável:** 3 minutos.

## T-SEG-01 — Dois filtros simultâneos e leitura do recorte

- **Perfil-alvo:** UC01 ou UC03.
- **Situação real:** "Quantas pesquisas de uma mesma área e de um mesmo tipo
  existem no portfólio? Ao final, descreva exatamente o que o número
  representa."
- **Passos esperados:** D01 → filtro de área → filtro de tipo (mantendo o de
  área) → leitura da contagem.
- **Critério de sucesso:** informa a contagem **e enuncia o recorte completo**
  ("pesquisas da área X e do tipo Y, no período padrão") sem omitir nenhum
  filtro ativo.
- **Tempo aceitável:** 3 minutos.

## T-SEG-02 — Três filtros simultâneos cruzando telas

- **Perfil-alvo:** UC02 (área técnica).
- **Situação real:** "Para um conjunto filtrado por área, tipo e status,
  verifique a distribuição por tipo de questão nos resultados."
- **Passos esperados:** D01 → aplicar os três filtros → navegar a D03 →
  conferir se o recorte se manteve → ler a distribuição por tipo de questão.
- **Critério de sucesso:** lê a distribuição para o recorte certo e confirma
  quais dos três filtros permaneceram ativos após a navegação (perceber
  perda de filtro é sucesso; não perceber é o erro-alvo).
- **Tempo aceitável:** 5 minutos.

## T-SEG-03 — Segmentação que zera: recorte vazio consciente

- **Perfil-alvo:** UC01 (analista da Central).
- **Situação real:** "Empilhe filtros até obter um recorte sem pesquisas e
  explique o que a tela está dizendo."
- **Passos esperados:** D01 → acumular período curto + área + tipo + status
  até zerar → ler o estado exibido → remover UM filtro e observar o retorno
  de resultados.
- **Critério de sucesso:** distingue "recorte sem correspondência" de erro,
  identifica qual filtro removeu para voltar a ter dados e explica por quê.
  (Complementa a T-FIL-04: aqui o vazio nasce da **combinação**, e o
  participante precisa raciocinar sobre qual segmento o causou.)
- **Tempo aceitável:** 4 minutos.

## Dependências e limites declarados

- As comparações usam apenas contagens calculáveis do snapshot (I01–I05);
  nenhuma tarefa pede taxa que dependa de denominador indisponível (I08,
  I11) — se a tela exibir "indisponível", ler esse estado corretamente é o
  comportamento esperado, não um bloqueio da tarefa.
- Comparação entre períodos usa janelas equivalentes por `data_solicitacao`;
  tarefas não pedem "período" solto sem marco definido (regra do RF03 contra
  referência temporal ambígua).
