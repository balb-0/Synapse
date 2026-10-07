# Tarefas de usabilidade — navegação e filtros hierárquicos

Tarefas de teste de usabilidade para navegação entre as páginas finais do
relatório e uso dos filtros. Cada tarefa segue o mesmo contrato: **situação
real** (contexto que o participante recebe, sem dica de caminho), **passos
esperados** (o caminho ótimo, usado para medir desvio — não é lido para o
participante), **critério de sucesso** observável e **tempo aceitável**.
Os perfis citados vêm do [levantamento de perfis](perfis-e-criterios.md).

Na Sprint 5, as tarefas foram adequadas às três páginas do relatório
`CentralPesquisasBI` (correspondência na
[Tabela 0 do roteiro](roteiro-execucao.md#0-páginas-finais-avaliadas-sprint-5)).
Cada tarefa declara também:

- **Página/visual**: onde a resposta está no relatório final;
- **Grão disponível**: o menor recorte publicado que sustenta a resposta,
  conforme o [contrato da geração](../acesso-cubos-bi.md#contrato-da-geração-para-o-bi);
- **Estado esperado**: `valor` (há número a ler), `sem dado` (a página
  informa o motivo) ou `aviso` (o recurso não existe no grão publicado e a
  página diz isso). Ler corretamente um estado `sem dado` ou `aviso` é
  sucesso, não bloqueio.

Os recortes concretos de cada tarefa (área, tipo, status) e os valores de
referência ficam na preparação das sessões, para que o enunciado não revele
a resposta.

Convenções de medição (valem para todas as tarefas desta pasta):

- **Conclusão**: o participante atinge o critério de sucesso sem ajuda do
  moderador. Ajuda pedida = tarefa concluída com assistência (anotada).
- **Desvio de caminho**: qualquer sequência diferente dos passos esperados;
  conta-se o número de páginas/cliques fora do caminho ótimo.
- **Tempo aceitável**: cronometrado do enunciado ao critério de sucesso;
  estourar o tempo não interrompe a tarefa, mas marca "acima do aceitável".

## T-NAV-01 — Encontrar o estado geral do portfólio

- **Perfil-alvo:** UC01 (Central) ou UC03 (gestor).
- **Situação real:** "Você chegou agora e quer saber quantas pesquisas existem
  no portfólio e como elas se distribuem por status."
- **Página/visual:** Produção e Volume → cartão "Pesquisas no recorte" e
  gráfico "Pesquisas por Status".
- **Grão disponível:** área × status × tipo (`PUB_C01_CICLO`).
- **Estado esperado:** `valor`.
- **Passos esperados:** abrir o relatório → Produção e Volume → ler o total e
  a distribuição por status.
- **Critério de sucesso:** informa o total de pesquisas e aponta qual status
  concentra mais pesquisas, citando os valores exibidos e sem confundir o
  total com outro número do cartão "Indicadores principais".
- **Tempo aceitável:** 2 minutos.

## T-NAV-02 — Percorrer as páginas e voltar ao início

- **Perfil-alvo:** qualquer perfil interno (UC01–UC03).
- **Situação real:** "Antes de usar no dia a dia, você quer entender o que a
  solução oferece: passe por todas as áreas do relatório e volte para a tela
  inicial."
- **Página/visual:** as três páginas (Produção e Volume; Participação
  agregada; Estoque, Instrumento e Qualidade).
- **Grão disponível:** não se aplica (navegação).
- **Estado esperado:** `valor` nas duas primeiras páginas; `sem dado` na
  seção de estoque quando a geração não tiver fechamento mensal observado.
- **Passos esperados:** Produção e Volume → Participação agregada → Estoque,
  Instrumento e Qualidade → retorno a Produção e Volume pela navegação do
  relatório (abas de página).
- **Critério de sucesso:** visita as três páginas, nomeia com as próprias
  palavras o que cada uma mostra, retorna à primeira página e, se a seção de
  estoque estiver vazia, explica que não há fechamento publicado — e não que
  a página está quebrada.
- **Tempo aceitável:** 4 minutos.

## T-FIL-01 — Filtrar o portfólio por área e período

- **Perfil-alvo:** UC01 (analista da Central).
- **Situação real:** "Um colega pediu as pesquisas de uma área específica
  solicitadas no último ano. Encontre esse recorte."
- **Página/visual:** Produção e Volume → slicer Área → cartão "Pesquisas no
  recorte"; aviso "Ano de edição indisponível em C01".
- **Grão disponível:** área × status × tipo. **C01 não publica marco
  temporal** (nem `data_solicitacao`, nem ano de edição).
- **Estado esperado:** `valor` para a área; `aviso` para o período.
- **Passos esperados:** Produção e Volume → slicer Área → ler a contagem →
  ler o aviso de ano de edição.
- **Critério de sucesso:** obtém a contagem da área **e** declara que ela
  cobre todo o portfólio, porque o período não pode ser aplicado nesta página
  (o critério herdado do RF01 — saber qual marco temporal está em uso — passa
  a ser saber que **não há** marco temporal publicado em C01).
- **Tempo aceitável:** 3 minutos.

## T-FIL-02 — Combinar filtros e ler a distribuição resultante

- **Perfil-alvo:** UC03 (gestor).
- **Situação real:** "Você quer saber quantas pesquisas de um mesmo tipo ainda
  não foram finalizadas, para avaliar a carga da equipe."
- **Página/visual:** Produção e Volume → slicers Tipo e Status → cartão
  "Pesquisas no recorte" ou gráfico "Pesquisas por Status".
- **Grão disponível:** área × status × tipo.
- **Estado esperado:** `valor`.
- **Passos esperados:** Produção e Volume → slicer Tipo → slicer Status
  (todos os status diferentes de "finalizada") → leitura da contagem.
- **Critério de sucesso:** informa a contagem do recorte combinado,
  **considera todos os status não finalizados** publicados (não apenas "em
  andamento") e distingue a contagem filtrada do total do portfólio.
- **Tempo aceitável:** 3 minutos.

## T-FIL-03 — Limpar os filtros e restaurar o estado inicial

- **Perfil-alvo:** qualquer perfil interno.
- **Situação real:** "Depois da análise anterior, você quer voltar a ver o
  portfólio completo."
- **Página/visual:** Produção e Volume → slicers Área, Tipo e Status.
- **Grão disponível:** não se aplica.
- **Estado esperado:** `valor` (total do portfólio).
- **Passos esperados:** limpar a seleção de cada slicer ativo (o relatório
  não tem ação única de limpeza) → conferir que contagens e distribuição
  voltaram ao estado inicial.
- **Critério de sucesso:** o estado exibido volta ao inicial e o participante
  confirma isso comparando o total exibido antes/depois.
- **Tempo aceitável:** 1 minuto.

## T-FIL-04 — Distinguir recorte vazio de erro

- **Perfil-alvo:** UC01 (analista da Central).
- **Situação real:** "Procure pesquisas de uma combinação rara de área e tipo
  que provavelmente não existe."
- **Página/visual:** Produção e Volume → slicers Área e Tipo → cartões e
  gráficos.
- **Grão disponível:** área × status × tipo; combinações sem pesquisa não
  geram linha na publicação.
- **Estado esperado:** recorte vazio (cartões e gráficos sem valor).
- **Passos esperados:** Produção e Volume → aplicar a combinação sem
  correspondência → ler a resposta da página.
- **Critério de sucesso:** o participante explica, com as próprias palavras,
  que **não há pesquisas para o recorte** — e não que "a tela quebrou" ou que
  "o dado está errado". (Estados distintos são critério de aceite do RF01;
  aqui medimos se a interface comunica isso sem ajuda.)
- **Tempo aceitável:** 2 minutos.

## Dependências e limites declarados

- As tarefas usam apenas filtros existentes nas páginas finais (Área, Tipo,
  Status em Produção e Volume). Ano de edição e complexidade aparecem como
  aviso textual e não filtram C01 ([RP-16](../solucao-dashboards/filtros-hierarquias-detalhamento.md)).
- Nenhuma tarefa depende de indicador marcado `sem dado` na
  [sinalização de indicadores](../sinalizacao-indicadores-bloqueados.md);
  quando a página mostra esse estado, a leitura correta faz parte do sucesso.
- Se o relatório final alterar filtros ou títulos, a tarefa é reconferida
  contra a Tabela 0 do roteiro antes da execução.
