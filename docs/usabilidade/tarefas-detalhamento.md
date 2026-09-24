# Tarefas de usabilidade — detalhamento entre níveis e entre telas

Tarefas que percorrem o caminho do **agregado ao detalhe** e a navegação de
detalhamento **entre telas**. O contrato de cada tarefa e as convenções de
medição (conclusão, desvio, tempo) são os definidos em
[`tarefas-navegacao-filtros.md`](tarefas-navegacao-filtros.md). A regra
distintiva deste grupo, exigida pelo card: **toda tarefa termina com o
participante justificando o número encontrado** — dizendo de onde ele vem
(recorte, origem e, quando houver taxa, numerador e denominador). Um número
certo que o participante não sabe explicar conta como falha de usabilidade,
não como sucesso.

## T-DET-01 — Do total do portfólio ao grupo por status

- **Perfil-alvo:** UC01 (analista da Central).
- **Situação real:** "O portfólio tem um total de pesquisas. Descubra quantas
  estão no status mais numeroso e diga o que esse número representa."
- **Passos esperados:** D01 → leitura do total agregado → descer para a
  distribuição por status → identificar o maior grupo.
- **Níveis:** total do portfólio (agregado) → contagem por status (1º nível
  de detalhe).
- **Critério de sucesso:** informa a contagem do maior status **e** explica
  que ela é um subconjunto do total exibido, citando o recorte ("são X das Y
  pesquisas do portfólio").
- **Tempo aceitável:** 3 minutos.

## T-DET-02 — Da participação agregada à distribuição por empresa

- **Perfil-alvo:** UC01 ou UC03.
- **Situação real:** "A solução mostra o total de participações observadas.
  Verifique como esse total se distribui pelas empresas participantes e
  aponte a maior concentração."
- **Passos esperados:** D02 → total de participações observadas → abrir a
  distribuição por empresa → apontar a faixa/grupo de maior concentração.
- **Níveis:** participações observadas (agregado) → distribuição por empresa
  (detalhe agregado, sem identificar empresa nominalmente — limite LGPD do
  protótipo).
- **Critério de sucesso:** aponta a concentração **e** justifica usando o
  rótulo correto ("participações observadas", não "adesão") — a distinção é
  contrato do protótipo e critério do RF04.
- **Tempo aceitável:** 4 minutos.

## T-DET-03 — Detalhar preservando o filtro entre telas

- **Perfil-alvo:** UC02 (área técnica) ou UC01.
- **Situação real:** "Você filtrou um conjunto de pesquisas na tela de
  Operação e agora quer ver os resultados de questionários desse mesmo
  conjunto."
- **Passos esperados:** D01 com filtro aplicado → navegar para D03 →
  verificar se o recorte se manteve → ler a distribuição por tipo de questão
  do recorte.
- **Níveis:** recorte filtrado em D01 → mesmo recorte em D03 (detalhamento
  entre telas).
- **Critério de sucesso:** o participante **verifica explicitamente** se o
  filtro sobreviveu à navegação e lê o número certo para o recorte; se o
  filtro não se mantiver, ele percebe e refaz — perceber é parte do sucesso,
  não perceber é o erro que esta tarefa existe para capturar.
- **Tempo aceitável:** 4 minutos.

## T-DET-04 — Chegar à regra que explica um indicador de qualidade

- **Perfil-alvo:** papel de governança (participante interno exercendo o
  papel, conforme registro do levantamento de perfis).
- **Situação real:** "Um campo aparece com completude abaixo de 100% na tela
  de qualidade. Descubra qual regra foi avaliada e quantos registros são
  afetados."
- **Passos esperados:** D04 → matriz/lista de regras → localizar o campo →
  ler regra avaliada, numerador e denominador da completude.
- **Níveis:** indicador agregado de qualidade → regra e contagem por campo.
- **Critério de sucesso:** cita a regra, o número de registros afetados e o
  denominador usado — sem confundir "ausência permitida" com "lacuna a
  investigar" quando a tela distinguir os dois (critério do RF06).
- **Tempo aceitável:** 4 minutos.

