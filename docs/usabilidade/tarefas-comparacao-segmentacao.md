# Tarefas de usabilidade — comparação temporal e segmentação simultânea

Tarefas que exercitam **comparação entre períodos equivalentes** e **mais de
um filtro aplicado ao mesmo tempo**. Contrato, campos (**Página/visual**,
**Grão disponível**, **Estado esperado**) e convenções de medição são os de
[`tarefas-navegacao-filtros.md`](tarefas-navegacao-filtros.md). Duas regras
específicas deste grupo, herdadas dos critérios de aceite (§6.1.1, RF01 e
RF03):

- **Períodos equivalentes e marco rotulado**: comparação temporal só vale
  entre janelas comparáveis (mesmo tamanho, mesmo marco), e o participante
  precisa **identificar o marco temporal** em uso. Na publicação da Sprint 5
  há apenas dois marcos: o **mês de resposta** de C02 e o **fechamento
  mensal** de C03, ambos reunidos em `DIM_TEMPO` (Ano → Trimestre → Mês).
  C01 não publica data; `data_solicitacao` deixa de ser o marco padrão das
  páginas.
- **Segmentação simultânea**: com dois ou mais filtros ativos, o participante
  precisa saber dizer **qual recorte está vendo** — filtros acumulados sem
  consciência do recorte são a principal fonte de leitura errada.

Quando a geração não contém meses observados, a comparação temporal fica
`sem dado`. Ler esse estado e explicar o motivo é o comportamento esperado;
o participante não deve inventar uma comparação a partir de outro número.

## T-CMP-01 — Comparar dois períodos equivalentes

- **Perfil-alvo:** UC03 (gestor).
- **Situação real:** "A diretoria perguntou se o volume de participações
  cresceu em relação ao ano anterior. Responda com os números da solução."
- **Página/visual:** Participação agregada (C02) → slicer Ano → cartão de
  participações e "Participações por mês".
- **Grão disponível:** área × tipo × mês de resposta; o ano deriva do mês
  observado em C02.
- **Estado esperado:** `valor` se houver dois anos observados; `sem dado`
  se o mês de resposta não estiver preenchido na geração.
- **Passos esperados:** Participação agregada → selecionar o ano A →
  registrar a contagem → selecionar o ano B → comparar.
- **Critério de sucesso:** apresenta as duas contagens e diz qual ano teve
  mais participações **identificando o marco** (mês de resposta); ou, se a
  geração não tiver anos observados, declara que a comparação não é possível
  e por quê.
- **Tempo aceitável:** 4 minutos.

## T-CMP-02 — Ler a evolução mensal sem misturar marcos temporais

- **Perfil-alvo:** UC01 (analista da Central).
- **Situação real:** "Aponte em qual mês houve mais participações e confirme
  qual data define o mês nesse gráfico."
- **Página/visual:** Participação agregada (C02) → "Participações por mês".
- **Grão disponível:** mês de resposta (primeiro dia do mês).
- **Estado esperado:** `valor` ou `sem dado` (mesma regra da T-CMP-01).
- **Passos esperados:** Participação agregada → gráfico mensal → identificar
  o pico → conferir o rótulo do eixo (mês de resposta).
- **Critério de sucesso:** aponta o mês de pico e nomeia o marco temporal do
  visual; se o participante presumir outro marco ("é a data de solicitação?")
  ou ler uma categoria sem mês como um mês, a dúvida registrada vira achado
  sobre a rotulagem.
- **Tempo aceitável:** 3 minutos.

## T-SEG-01 — Dois filtros simultâneos e leitura do recorte

- **Perfil-alvo:** UC01 ou UC03.
- **Situação real:** "Quantas pesquisas de uma mesma área e de um mesmo tipo
  existem no portfólio? Ao final, descreva exatamente o que o número
  representa."
- **Página/visual:** Produção e Volume → slicers Área e Tipo → cartão
  "Pesquisas no recorte".
- **Grão disponível:** área × status × tipo, sem período.
- **Estado esperado:** `valor`.
- **Passos esperados:** Produção e Volume → filtro de área → filtro de tipo
  (mantendo o de área) → leitura da contagem.
- **Critério de sucesso:** informa a contagem **e enuncia o recorte completo**
  ("pesquisas da área X e do tipo Y, em todos os status e sem recorte de
  período") sem omitir nenhum filtro ativo nem inventar um período.
- **Tempo aceitável:** 3 minutos.

## T-SEG-02 — Três filtros simultâneos cruzando páginas

- **Perfil-alvo:** UC02 (área técnica).
- **Situação real:** "Para um conjunto filtrado por área, tipo e status,
  verifique como as perguntas dos questionários se distribuem por tipo de
  pergunta."
- **Página/visual:** Produção e Volume (Área, Tipo, Status) → Estoque,
  Instrumento e Qualidade → "Perguntas por tipo".
- **Grão disponível:** C04 só é filtrável por **área** e tipo de pergunta;
  tipo de pesquisa e status não chegam a C04.
- **Estado esperado:** `valor` para a área; `aviso` implícito para tipo e
  status (sem relacionamento com C04).
- **Passos esperados:** Produção e Volume → aplicar os três filtros →
  navegar à terceira página → conferir quais filtros se mantiveram → aplicar
  a área, se necessário → ler a distribuição por tipo de pergunta.
- **Critério de sucesso:** lê a distribuição para o recorte certo e confirma
  quais dos três filtros permaneceram ativos e quais **não se aplicam** a C04
  (perceber perda ou inaplicabilidade de filtro é sucesso; não perceber é o
  erro-alvo).
- **Tempo aceitável:** 5 minutos.

## T-SEG-03 — Segmentação que zera: recorte vazio consciente

- **Perfil-alvo:** UC01 (analista da Central).
- **Situação real:** "Empilhe filtros até obter um recorte sem pesquisas e
  explique o que a tela está dizendo."
- **Página/visual:** Produção e Volume → slicers Área, Tipo e Status.
- **Grão disponível:** área × status × tipo.
- **Estado esperado:** recorte vazio e, ao remover um filtro, `valor`.
- **Passos esperados:** Produção e Volume → acumular área + tipo + status até
  zerar → ler o estado exibido → remover UM filtro e observar o retorno de
  resultados.
- **Critério de sucesso:** distingue "recorte sem correspondência" de erro,
  identifica qual filtro removeu para voltar a ter dados e explica por quê.
  (Complementa a T-FIL-04: aqui o vazio nasce da **combinação**, e o
  participante precisa raciocinar sobre qual segmento o causou.)
- **Tempo aceitável:** 4 minutos.

## Dependências e limites declarados

- As comparações usam apenas contagens publicadas (I01, I02 em C01; contagem
  de participações em C02); nenhuma tarefa pede taxa que dependa de
  denominador indisponível (I08, I11) — se a página exibir "sem dado", ler
  esse estado corretamente é o comportamento esperado, não um bloqueio.
- Comparação entre períodos usa somente o mês de resposta (C02) ou o
  fechamento mensal (C03); tarefas não pedem "período" solto sem marco
  definido (regra do RF03 contra referência temporal ambígua).
