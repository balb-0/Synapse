# Tarefas de usabilidade — comparação temporal e segmentação simultânea

Tarefas que exercitam **comparação entre períodos equivalentes** e **mais de
um filtro aplicado ao mesmo tempo**. Contrato e convenções de medição são os
de [`tarefas-navegacao-filtros.md`](tarefas-navegacao-filtros.md). Duas regras
específicas deste grupo, herdadas dos critérios de aceite (§6.1.1, RF01 e
RF03):

- Comparação em Produção usa anos de edição completos (`ano_edicao`), mantendo
  os demais filtros. Não mede entradas por solicitação.
- Evolução no Benchmark usa ano de divulgação (`BE_Pesquisa[Ano]`), com empresa
  selecionada. Não se compara esse ano ao de edição como se fossem o mesmo marco.
- Com dois ou mais filtros ativos, o participante deve enunciar o recorte.

## T-CMP-01 — Comparar dois anos de edição do portfólio

- **Perfil-alvo:** UC03 (gestor).
- **Situação real:** "A diretoria perguntou se o volume de pesquisas
  por edição cresceu de um ano para outro. Responda com os números
  da solução."
- **Passos esperados:** Produção e Volume → selecionar ano de edição A → registrar a
  contagem → selecionar ano de edição B, mantendo área/tipo/status iguais → comparar.
- **Critério de sucesso:** apresenta as duas contagens, diz qual período teve
  mais pesquisas **e identifica `ano_edicao`** como marco, sem afirmar
  crescimento das solicitações.
- **Tempo aceitável:** 4 minutos.

## T-CMP-02 — Ler a evolução anual da participação

- **Perfil-alvo:** UC01 (analista da Central).
- **Situação real:** "Para uma empresa, aponte o ano com mais pesquisas em que
  há participação observada e explique qual data define o ano."
- **Passos esperados:** Benchmark Externo — V2 → selecionar uma empresa →
  visual Evolução da participação → identificar pico → conferir o ano de
  divulgação (`BE_Pesquisa[Ano]`, derivado de `data_divulgacao`).
- **Critério de sucesso:** aponta o ano e a contagem de pesquisas distintas,
  distingue a série da selecionada da média das demais e nomeia o marco.
  A ausência de rótulo claro deve ser registrada como achado; não pressupor
  uma evolução mensal ou uma data de entrada que a página não oferece.
- **Tempo aceitável:** 3 minutos.

## T-SEG-01 — Dois filtros simultâneos e leitura do recorte

- **Perfil-alvo:** UC01 ou UC03.
- **Situação real:** "Quantas pesquisas de uma mesma área e de um mesmo tipo
  existem no portfólio? Ao final, descreva exatamente o que o número
  representa."
- **Passos esperados:** Produção e Volume → filtro de área → filtro de tipo (mantendo o de
  área) → leitura da contagem.
- **Critério de sucesso:** informa a contagem **e enuncia o recorte completo**
  ("pesquisas da área X e do tipo Y, nos anos de edição selecionados") sem omitir nenhum
  filtro ativo.
- **Tempo aceitável:** 3 minutos.

## T-SEG-02 — Três filtros simultâneos cruzando telas (fora da rodada)

- **Estado:** fora da rodada; exige Resultados (D03), ausente no report entregue.

- **Perfil-alvo:** UC02 (área técnica).
- **Situação real:** "Para um conjunto filtrado por área, tipo e status,
  verifique a distribuição por tipo de questão nos resultados."
- **Passos esperados:** Produção e Volume → aplicar os três filtros → navegar a D03 →
  conferir se o recorte se manteve → ler a distribuição por tipo de questão.
- **Critério de sucesso:** lê a distribuição para o recorte certo e confirma
  quais dos três filtros permaneceram ativos após a navegação (perceber
  perda de filtro é sucesso; não perceber é o erro-alvo).
- **Tempo aceitável:** 5 minutos.

## T-SEG-03 — Segmentação que zera: recorte vazio consciente

- **Perfil-alvo:** UC01 (analista da Central).
- **Situação real:** "Empilhe filtros até obter um recorte sem pesquisas e
  explique o que a tela está dizendo."
- **Passos esperados:** Produção e Volume → acumular ano de edição + área + tipo + status
  até zerar → ler o estado exibido → remover UM filtro e observar o retorno
  de resultados.
- **Critério de sucesso:** distingue "recorte sem correspondência" de erro,
  identifica qual filtro removeu para voltar a ter dados e explica por quê.
  (Complementa a T-FIL-04: aqui o vazio nasce da **combinação**, e o
  participante precisa raciocinar sobre qual segmento o causou.)
- **Tempo aceitável:** 4 minutos.

## Dependências e limites declarados

- T-CMP-01, T-CMP-02, T-SEG-01 e T-SEG-03 estão na rodada; T-SEG-02 permanece
  fora por falta de página. O registro não converte bloqueio em execução.
- Os números da demonstração vêm de CSVs sintéticos e devem ser conferidos
  contra a mesma versão desses arquivos. A precisão contra o DW só pode ser
  aceita após a integração e o redesenho dos visuais em RP-13/RP-14.
- Ano de edição e ano de divulgação não são janelas de solicitação nem mês
  de resposta dos cubos. O moderador registra o campo correto em cada tarefa.
