# Tarefas de usabilidade — navegação e filtros hierárquicos

A rodada usa as duas páginas PBIR entregues: Produção e Volume e Benchmark
Externo — V2, em `src/pbir dash/dashboard.Report/`. Cada tarefa define situação
real, passos esperados (não lidos ao participante), critério de sucesso e tempo
aceitável. Os perfis vêm do [levantamento](perfis-e-criterios.md).

Produção filtra `D01_CicloPesquisa[ano_edicao]`; Benchmark usa
`BE_Pesquisa[Ano]`, derivado de `data_divulgacao`. Não há filtro de solicitação,
evolução mensal nem drill hierárquico nessas páginas. Os dados do protótipo são
sintéticos. Uma sessão nesse alvo não valida o DW nem substitui RP-13/RP-14.

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
- **Passos esperados:** abrir a solução → página Produção e Volume → identificar
  o total do portfólio e a distribuição por status.
- **Critério de sucesso:** informa o total de pesquisas e aponta qual status
  concentra mais pesquisas, citando os valores exibidos na tela.
- **Tempo aceitável:** 2 minutos.

## T-NAV-02 — Percorrer as duas páginas e voltar à primeira

- **Perfil-alvo:** qualquer perfil interno (UC01–UC03).
- **Situação real:** "Você quer conhecer as duas páginas disponíveis e voltar
  para a visão do portfólio."
- **Passos esperados:** Produção e Volume → Benchmark Externo — V2 → retorno
  a Produção e Volume pelas abas de páginas do report.
- **Critério de sucesso:** visita as duas páginas, descreve a finalidade de
  cada uma e retorna à primeira pelas abas, sem usar voltar do navegador.
- **Tempo aceitável:** 3 minutos.

## T-FIL-01 — Filtrar o portfólio por período e área

- **Perfil-alvo:** UC01 (analista da Central).
- **Situação real:** "Um colega pediu as pesquisas de uma área específica
  de uma edição anual. Encontre esse recorte e diga qual ano está filtrando."
- **Passos esperados:** Produção e Volume → filtro Ano (`ano_edicao`) →
  filtro Área → leitura da lista/distribuição filtrada.
- **Critério de sucesso:** obtém o recorte e identifica o ano da edição;
  não interpreta o filtro como data de solicitação nem data de divulgação.
- **Tempo aceitável:** 3 minutos.

## T-FIL-02 — Combinar filtros e ler a distribuição resultante

- **Perfil-alvo:** UC03 (gestor).
- **Situação real:** "Você quer saber quantas pesquisas de um mesmo tipo ainda
  estão em andamento, para avaliar a carga da equipe."
- **Passos esperados:** Produção e Volume → filtro de tipo → filtro de status → leitura da
  contagem resultante.
- **Critério de sucesso:** informa a contagem do recorte combinado e distingue
  a contagem filtrada do total do portfólio (não confunde as duas).
- **Tempo aceitável:** 3 minutos.

## T-FIL-03 — Limpar os filtros e restaurar o estado inicial

- **Perfil-alvo:** qualquer perfil interno.
- **Situação real:** "Depois da análise anterior, você quer voltar a ver o
  portfólio completo."
- **Passos esperados:** limpar cada slicer ativo pelo controle do próprio slicer → conferir que contagens e distribuição voltaram ao estado
  inicial.
- **Critério de sucesso:** o estado exibido volta ao inicial e o participante
  confirma isso comparando o total exibido antes/depois.
- **Tempo aceitável:** 1 minuto.

## T-FIL-04 — Distinguir recorte vazio de erro

- **Perfil-alvo:** UC01 (analista da Central).
- **Situação real:** "Procure pesquisas de uma combinação rara (área + tipo +
  ano de edição) que provavelmente não existe."
- **Passos esperados:** Produção e Volume → aplicar a combinação sem correspondência →
  ler a resposta da tela.
- **Critério de sucesso:** o participante explica, com as próprias palavras,
  que **não há pesquisas para o recorte** — e não que "a tela quebrou" ou que
  "o dado está errado". (Estados distintos são critério de aceite do RF01;
  aqui medimos se a interface comunica isso sem ajuda.)
- **Tempo aceitável:** 2 minutos.

## Dependências e limites declarados

- Os filtros existentes em Produção são Ano, Área, Tipo, Status e Complexidade.
- As seis tarefas deste documento estão na rodada. Os valores de referência
  devem vir dos CSVs sintéticos da mesma versão; isso não comprova precisão
  contra os cubos publicados.
- Não se pressupõe que os filtros sejam sincronizados entre as duas páginas.
- O teste registra ausência de rótulo temporal e confusão de estado como
  achados, sem trocar a semântica do filtro para fazer a tarefa passar.
