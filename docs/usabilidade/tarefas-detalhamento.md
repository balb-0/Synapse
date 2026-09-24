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

