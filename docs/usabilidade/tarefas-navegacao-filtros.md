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

