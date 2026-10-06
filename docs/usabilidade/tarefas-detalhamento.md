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
- **Passos esperados:** Produção e Volume → leitura do total agregado → descer para a
  distribuição por status → identificar o maior grupo.
- **Níveis:** total do portfólio (agregado) → contagem por status (1º nível
  de detalhe).
- **Critério de sucesso:** informa a contagem do maior status **e** explica
  que ela é um subconjunto do total exibido, citando o recorte ("são X das Y
  pesquisas do portfólio").
- **Tempo aceitável:** 3 minutos.

## T-DET-02 — Da comparação da empresa às faixas do benchmark

- **Perfil-alvo:** UC01 ou UC03.
- **Situação real:** "Escolha uma empresa e descubra quantas pesquisas têm
  participação dela e qual faixa de quantidade contém as demais empresas."
- **Passos esperados:** Benchmark Externo — V2 → selecionar uma empresa →
  ler Pesquisas com participação → ler Posição no benchmark e a faixa marcada
  para a selecionada, mantendo os mesmos filtros.
- **Níveis:** contagem de pesquisas distintas da empresa → distribuição das
  demais empresas por faixa. Isso não é um drill hierárquico.
- **Critério de sucesso:** explica que o cartão conta pesquisas distintas com
  registro da empresa e que o histograma conta demais empresas por faixa;
  não soma empresas como se fossem participações nem chama o valor de adesão.
- **Tempo aceitável:** 4 minutos.

## T-DET-03 — Detalhar preservando o filtro entre telas (fora da rodada)

- **Estado:** fora da rodada; exige página Resultados (D03), ausente no report entregue.

- **Perfil-alvo:** UC02 (área técnica) ou UC01.
- **Situação real:** "Você filtrou um conjunto de pesquisas na tela de
  Operação e agora quer ver os resultados de questionários desse mesmo
  conjunto."
- **Passos esperados:** D01 com filtro aplicado → navegar para D03 →
  verificar se o recorte se manteve → ler a distribuição por tipo de questão
  do recorte.
- **Níveis:** recorte filtrado em Produção e Volume → mesmo recorte em D03 (detalhamento
  entre telas).
- **Critério de sucesso:** o participante **verifica explicitamente** se o
  filtro sobreviveu à navegação e lê o número certo para o recorte; se o
  filtro não se mantiver, ele percebe e refaz — perceber é parte do sucesso,
  não perceber é o erro que esta tarefa existe para capturar.
- **Tempo aceitável:** 4 minutos.

## T-DET-04 — Chegar à regra que explica um indicador de qualidade (fora da rodada)

- **Estado:** fora da rodada; exige página Qualidade (D04), ausente no report entregue.

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

## Dependências e limites declarados

- T-DET-01 e T-DET-02 estão na rodada das duas páginas, com filtro cruzado e
  leitura de tabelas/gráficos. Nenhuma delas presume hierarquia navegável.
- T-DET-03 e T-DET-04 preservam o objetivo futuro, mas não contam no denominador
  da rodada atual nem recebem conclusão presumida. Replanejar quando existirem
  as páginas e validar os filtros e o grão antes de executá-las.
- A demonstração contém nomes sintéticos de empresas e pesquisas. A publicação
  Parquet atual não oferece esse grão. Detalhe individual e benchmark por empresa
  dependem de redesenho RP-13/RP-14 ou contrato de acesso ampliado e homologado.
