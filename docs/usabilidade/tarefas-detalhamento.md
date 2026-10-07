# Tarefas de usabilidade — detalhamento entre níveis e entre telas

Tarefas que percorrem o caminho do **agregado ao detalhe** e a navegação de
detalhamento **entre páginas**. O contrato de cada tarefa, os campos
**Página/visual**, **Grão disponível** e **Estado esperado** e as convenções
de medição (conclusão, desvio, tempo) são os definidos em
[`tarefas-navegacao-filtros.md`](tarefas-navegacao-filtros.md). A regra
distintiva deste grupo, exigida pelo card: **toda tarefa termina com o
participante justificando o número encontrado** — dizendo de onde ele vem
(recorte, origem e, quando houver taxa ou média, numerador e denominador).
Um número certo que o participante não sabe explicar conta como falha de
usabilidade, não como sucesso.

**Drill suportado na Sprint 5.** O detalhamento desce somente até o grão
publicado: área → tipo (C01 e C02), área → tipo → perfil (C03) e ano →
trimestre → mês (C02 e C03), conforme
[filtros, hierarquias e detalhamento](../solucao-dashboards/filtros-hierarquias-detalhamento.md).
O participante pode chegar ao nível seguinte por drill-down no visual, por
seleção cruzada (clicar numa barra filtra os demais visuais) ou por slicer;
os três caminhos são aceitos, e o caminho usado é registrado como desvio
quando diferir do drill.

## T-DET-01 — Do total do portfólio ao grupo por status e tipo

- **Perfil-alvo:** UC01 (analista da Central).
- **Situação real:** "O portfólio tem um total de pesquisas. Descubra quantas
  estão no status mais numeroso, como esse grupo se divide por tipo e diga o
  que esses números representam."
- **Página/visual:** Produção e Volume → cartão "Pesquisas no recorte" →
  "Pesquisas por Status" → "Volume por Área"/"Acompanhamento das Pesquisas"
  (por tipo).
- **Níveis:** total do portfólio (agregado) → contagem por status (1º nível)
  → divisão por tipo dentro do status (2º nível).
- **Grão disponível:** área × status × tipo.
- **Estado esperado:** `valor`; média de ciclo pode ficar sem valor para
  status sem ciclo concluído.
- **Passos esperados:** ler o total → selecionar o maior status no gráfico
  (seleção cruzada) → descer para tipo (drill ou tabela filtrada).
- **Critério de sucesso:** informa a contagem do maior status e a do tipo
  mais frequente dentro dele **e** explica que são subconjuntos do total
  exibido, citando o recorte ("são X das Y pesquisas do portfólio").
- **Tempo aceitável:** 3 minutos.

## T-DET-02 — Da participação agregada à distribuição por área

- **Perfil-alvo:** UC01 ou UC03.
- **Situação real:** "A solução mostra o total de participações observadas.
  Verifique como esse total se distribui e aponte onde está a maior
  concentração. Se possível, diga quais empresas mais participaram."
- **Página/visual:** Participação agregada (C02) → cartão de participações →
  "Participações por área"; aviso de empresa distinta por pesquisa (I07).
- **Níveis:** participações observadas (agregado) → distribuição por área
  (detalhe agregado). Empresa e pesquisa individual **não são publicadas**.
- **Grão disponível:** área × tipo × mês de resposta.
- **Estado esperado:** `valor` por área; `aviso` para empresa.
- **Critério de sucesso:** aponta a área de maior concentração, justifica
  usando o rótulo correto ("participações observadas"/"ocorrências", não
  "adesão" nem "pessoas") **e** reconhece que o recorte por empresa não está
  disponível, sem concluir que o filtro está quebrado.
- **Tempo aceitável:** 4 minutos.

## T-DET-03 — Detalhar preservando o filtro entre páginas

- **Perfil-alvo:** UC02 (área técnica) ou UC01.
- **Situação real:** "Você filtrou uma área na página de produção e agora quer
  ver, para essa mesma área, como as perguntas dos questionários se
  distribuem por tipo."
- **Página/visual:** Produção e Volume (slicer Área) → Estoque, Instrumento e
  Qualidade → "Perguntas por tipo".
- **Níveis:** recorte por área em C01 → mesmo recorte em C04 (detalhamento
  entre páginas).
- **Grão disponível:** área × tipo de pergunta (C04).
- **Estado esperado:** `valor`.
- **Passos esperados:** Produção e Volume com Área aplicada → navegar para a
  terceira página → verificar se o slicer Área manteve a seleção → aplicar a
  área novamente, se necessário → ler a distribuição por tipo de pergunta.
- **Critério de sucesso:** o participante **verifica explicitamente** se o
  filtro sobreviveu à navegação e lê o número certo para o recorte; se o
  filtro não se mantiver, ele percebe e refaz — perceber é parte do sucesso,
  não perceber é o erro que esta tarefa existe para capturar.
- **Tempo aceitável:** 4 minutos.

## T-DET-04 — Chegar à regra que explica um indicador de qualidade (fora da rodada)

- **Estado:** fora da rodada; exige página Qualidade (D04), ausente no report entregue.

- **Perfil-alvo:** papel de governança (participante interno exercendo o
  papel, conforme registro do levantamento de perfis).
- **Situação real:** "Um campo aparece com completude abaixo de 100%.
  Descubra qual campo é, quantos registros são afetados e se isso é um
  problema."
- **Página/visual:** Estoque, Instrumento e Qualidade → cartão "Completude
  aplicável (I16)" → tabela "Completude por tabela e campo".
- **Níveis:** completude agregada → completude por tabela e campo.
- **Grão disponível:** tabela × campo (`PUB_QUALIDADE_CAMPO`, com
  `qtd_linhas` e `qtd_preenchidas`).
- **Estado esperado:** `valor`.
- **Critério de sucesso:** cita o campo, a quantidade de registros afetados e
  o denominador usado — sem confundir "ausência permitida" (campo que só
  existe em parte dos casos) com "lacuna a investigar". Se a página não
  expuser numerador, denominador ou natureza do nulo, a tarefa é executada
  mesmo assim e a ausência vira achado (critério do RF06).
- **Tempo aceitável:** 4 minutos.

## T-DET-05 — Tentar o drill-through até a pesquisa individual

- **Perfil-alvo:** UC01 (analista da Central).
- **Situação real:** "Na tabela de acompanhamento, escolha uma linha com
  pesquisas finalizadas e abra o detalhe de uma dessas pesquisas para ver o
  título e a data de entrega."
- **Página/visual:** Produção e Volume → tabela "Acompanhamento das
  Pesquisas" → menu de contexto da linha (Detalhar / Drill-through).
- **Níveis:** linha agregada (área × status × tipo) → página de detalhe por
  pesquisa (**não publicada**).
- **Grão disponível:** área × status × tipo; título, data de entrega e
  identificador da pesquisa não fazem parte dos sete Parquet.
- **Estado esperado:** `aviso` — não há página de drill-through, por desenho
  ([RP-16](../solucao-dashboards/filtros-hierarquias-detalhamento.md)).
- **Passos esperados:** localizar a linha → abrir o menu de contexto →
  constatar a ausência de drill-through → ler o grão da tabela (colunas área,
  status, tipo) e concluir que cada linha já é um grupo de pesquisas.
- **Critério de sucesso:** explica que a linha representa **um grupo** de
  pesquisas (citando quantas) e que o detalhe individual não está disponível
  na publicação — sem concluir que o recurso falhou. Procurar o detalhe em
  outra página antes de concluir conta como desvio, não como falha.
- **Tempo aceitável:** 3 minutos.

## Dependências e limites declarados

- T-DET-02 e T-DET-04 dependem de rótulos e distinções que são contrato das
  páginas (participação observada; nulos condicionais). Se a página final não
  expuser a distinção, a tarefa é executada mesmo assim e a ausência vira
  achado de usabilidade — não se ajusta a tarefa para a página passar.
- O detalhamento até registro individual **não** faz parte destas tarefas:
  a publicação não contém pesquisa, empresa nem pessoa
  ([contrato](../acesso-cubos-bi.md#contrato-da-geração-para-o-bi)), e os
  perfis testados consomem agregados.
