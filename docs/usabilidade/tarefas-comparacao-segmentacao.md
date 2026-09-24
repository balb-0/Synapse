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

