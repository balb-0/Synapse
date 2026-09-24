# Tarefas de usabilidade — navegação e filtros hierárquicos

Tarefas de teste de usabilidade para navegação entre as telas (D01–D04) e uso
dos filtros hierárquicos. Cada tarefa segue o mesmo contrato: **situação
real** (contexto que o participante recebe, sem dica de caminho), **passos
esperados** (o caminho ótimo, usado para medir desvio — não é lido para o
participante), **critério de sucesso** observável e **tempo aceitável**.
Os perfis citados vêm do [levantamento de perfis](perfis-e-criterios.md); os
filtros e telas são os do protótipo D01–D04
([`docs/assets/prototipos-dashboards/`](../assets/prototipos-dashboards/README.md)).

Convenções de medição (valem para todas as tarefas desta pasta):

- **Conclusão**: o participante atinge o critério de sucesso sem ajuda do
  moderador. Ajuda pedida = tarefa concluída com assistência (anotada).
- **Desvio de caminho**: qualquer sequência diferente dos passos esperados;
  conta-se o número de telas/cliques fora do caminho ótimo.
- **Tempo aceitável**: cronometrado do enunciado ao critério de sucesso;
  estourar o tempo não interrompe a tarefa, mas marca "acima do aceitável".

## T-NAV-01 — Encontrar o estado geral do portfólio

- **Perfil-alvo:** UC01 (Central) ou UC03 (gestor).
- **Situação real:** "Você chegou agora e quer saber quantas pesquisas existem
  no portfólio e como elas se distribuem por status."
- **Passos esperados:** abrir a solução → tela de Operação (D01) → identificar
  o total do portfólio e a distribuição por status.
- **Critério de sucesso:** informa o total de pesquisas e aponta qual status
  concentra mais pesquisas, citando os valores exibidos na tela.
- **Tempo aceitável:** 2 minutos.

## T-NAV-02 — Percorrer as quatro telas e voltar ao início

- **Perfil-alvo:** qualquer perfil interno (UC01–UC03).
- **Situação real:** "Antes de usar no dia a dia, você quer entender o que a
  solução oferece: passe pelas quatro áreas e volte para a tela inicial."
- **Passos esperados:** D01 Operação → D02 Participação → D03 Resultados →
  D04 Qualidade → retorno a D01 pela navegação principal (sem usar voltar do
  navegador).
- **Critério de sucesso:** visita as quatro telas, nomeia com as próprias
  palavras o que cada uma mostra e retorna a D01 pela navegação da solução.
- **Tempo aceitável:** 4 minutos.

## T-FIL-01 — Filtrar o portfólio por período e área

- **Perfil-alvo:** UC01 (analista da Central).
- **Situação real:** "Um colega pediu as pesquisas de uma área específica
  solicitadas no último ano. Encontre esse recorte."
- **Passos esperados:** D01 → filtro de período (campo padrão
  `data_solicitacao`) → filtro de área → leitura da lista/distribuição
  filtrada.
- **Critério de sucesso:** obtém a lista filtrada e **identifica qual campo de
  data** o período está usando (o rótulo do campo temporal é parte da
  resposta — critério herdado do RF01).
- **Tempo aceitável:** 3 minutos.

## T-FIL-02 — Combinar filtros e ler a distribuição resultante

- **Perfil-alvo:** UC03 (gestor).
- **Situação real:** "Você quer saber quantas pesquisas de um mesmo tipo ainda
  estão em andamento, para avaliar a carga da equipe."
- **Passos esperados:** D01 → filtro de tipo → filtro de status → leitura da
  contagem resultante.
- **Critério de sucesso:** informa a contagem do recorte combinado e distingue
  a contagem filtrada do total do portfólio (não confunde as duas).
- **Tempo aceitável:** 3 minutos.

## T-FIL-03 — Limpar os filtros e restaurar o estado inicial

- **Perfil-alvo:** qualquer perfil interno.
- **Situação real:** "Depois da análise anterior, você quer voltar a ver o
  portfólio completo."
- **Passos esperados:** acionar a limpeza de filtros (ação única, quando
  disponível) → conferir que contagens e distribuição voltaram ao estado
  inicial.
- **Critério de sucesso:** o estado exibido volta ao inicial e o participante
  confirma isso comparando o total exibido antes/depois.
- **Tempo aceitável:** 1 minuto.

## T-FIL-04 — Distinguir recorte vazio de erro

- **Perfil-alvo:** UC01 (analista da Central).
- **Situação real:** "Procure pesquisas de uma combinação rara (área + tipo +
  período curto) que provavelmente não existe."
- **Passos esperados:** D01 → aplicar a combinação sem correspondência →
  ler a resposta da tela.
- **Critério de sucesso:** o participante explica, com as próprias palavras,
  que **não há pesquisas para o recorte** — e não que "a tela quebrou" ou que
  "o dado está errado". (Estados distintos são critério de aceite do RF01;
  aqui medimos se a interface comunica isso sem ajuda.)
- **Tempo aceitável:** 2 minutos.

## Dependências e limites declarados

- As tarefas usam apenas filtros existentes no protótipo (período por
  `data_solicitacao`, tipo, área, complexidade, status). Nenhuma tarefa
  depende de indicador marcado indisponível na §5.6 do `projeto.md`.
- T-FIL-01 herda do RF01 a exigência de rótulo do campo temporal; se a tela
  final (RP) alterar os filtros disponíveis, a tarefa deve ser reconferida
  contra o mapa de visualizações antes da execução.
