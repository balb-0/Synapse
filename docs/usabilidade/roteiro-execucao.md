# Roteiro de execução dos testes de usabilidade

Define **quem participa**, **em que ordem as tarefas são aplicadas**, **o que
é medido** e **como a evidência é guardada** nas sessões que executam as
tarefas de [navegação e filtros](tarefas-navegacao-filtros.md),
[detalhamento](tarefas-detalhamento.md) e
[comparação e segmentação](tarefas-comparacao-segmentacao.md).

## 0. Páginas finais avaliadas (Sprint 5)

As tarefas foram escritas sobre o protótipo D01–D04. Na Sprint 5, o alvo das
sessões passa a ser o relatório
[`CentralPesquisasBI.Report`](../../powerbi/CentralPesquisasBI.Report/), que
consome a geração Parquet descrita em
[`acesso-cubos-bi.md`](../acesso-cubos-bi.md) e foi validado tecnicamente no
RP-17 ([validação das páginas finais](../solucao-dashboards/validacao-paginas-finais.md)).
A correspondência entre as telas planejadas e as páginas publicadas é:

<div align="center">
<sub>Tabela 0 - Telas do protótipo e páginas finais do relatório</sub><br>

| Tela do protótipo | Página final | Fonte publicada | Grão disponível | Filtros da página |
| :--- | :--- | :--- | :--- | :--- |
| D01 Operação | Produção e Volume | `PUB_C01_CICLO` | Área × status × tipo, sem eixo de tempo | Área, Tipo, Status (ano de edição e complexidade aparecem como aviso, sem filtrar) |
| D02 Participação | Participação agregada (C02) | `PUB_C02_PARTICIPACAO` | Área × tipo × mês de resposta, sem empresa nem pesquisa | Ano (de `DIM_TEMPO`), Área, Tipo (empresa e pesquisa aparecem como aviso) |
| D03 Resultados | Estoque, Instrumento e Qualidade | `PUB_C04_INSTRUMENTO` | Área × tipo de pergunta | Área |
| D04 Qualidade | Estoque, Instrumento e Qualidade | `PUB_QUALIDADE_*` | Tabela/campo, relação e tabela de origem | Nenhum (escopo global) |
| — (fluxo mensal) | Estoque, Instrumento e Qualidade | `PUB_C03_PIPELINE_MENSAL` | Fechamento mensal × status × área × tipo × perfil | Status, Área, Mês |

<sup>Material produzido pelos autores (2026), a partir da definição PBIR do RP-17</sup>

</div><br>

Consequências para o plano: D03 e D04 deixam de ser telas separadas e passam a
ser seções da terceira página; nenhuma página publica pesquisa, empresa ou
pessoa individual, então o detalhamento termina no menor grão agregado da
tabela correspondente.

## 1. Participantes

Perfis mapeados aos públicos do [levantamento](perfis-e-criterios.md). No
contexto acadêmico, os papéis são exercidos por integrantes do grupo e
convidados **fazendo o papel** do perfil — isso fica registrado na ficha da
sessão (nenhum resultado é apresentado como validação com usuário real do
parceiro).

<div align="center">
<sub>Tabela 1 - Participantes por perfil e tarefas atribuídas</sub><br>

| Participante | Perfil exercido | Tarefas |
| :--- | :--- | :--- |
| P1 | UC01 — analista da Central | T-NAV-01, T-FIL-01, T-FIL-04, T-DET-01, T-CMP-02, T-SEG-03 |
| P2 | UC03 — gestor | T-NAV-01, T-FIL-02, T-CMP-01, T-SEG-01, T-DET-02 |
| P3 | UC02 — área técnica | T-NAV-02, T-DET-03, T-SEG-02 |
| P4 | Governança (papel exercido) | T-FIL-03, T-DET-04 |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

Regras de alocação: cada tarefa é executada por **ao menos um participante**;
T-NAV-01 é executada por dois perfis distintos (comparação de leitura); um
participante nunca executa duas variantes que se revelam mutuamente
(ex.: T-FIL-04 e T-SEG-03 podem, pois o vazio nasce de causas diferentes).

## 2. Ordem das tarefas na sessão

Cada sessão é individual, moderada e segue esta ordem fixa — do geral ao
específico, para que uma tarefa não ensine a resposta da anterior:

1. **Aquecimento** (não medido): participante abre a solução e fala o que vê
   por 1 minuto (protocolo think-aloud ativado a partir daqui).
2. **Bloco A — navegação** (T-NAV-*): visão geral antes de qualquer filtro.
3. **Bloco B — filtros** (T-FIL-*): filtros simples antes dos combinados.
4. **Bloco C — detalhamento** (T-DET-*): exige os filtros do bloco B.
5. **Bloco D — comparação e segmentação** (T-CMP-*/T-SEG-*): os mais longos
   e cognitivamente pesados por último.
6. **Debrief** (5 min): impressões livres + as duas perguntas fixas: "o que
   foi mais difícil?" e "que número você não confiou?".

Duração prevista por sessão: **30–45 minutos** (aquecimento + 2 a 6 tarefas
por participante + debrief).

## 3. O que é medido

Por tarefa (convenções definidas em
[`tarefas-navegacao-filtros.md`](tarefas-navegacao-filtros.md)):

- **Conclusão**: sim / com assistência / não.
- **Tempo**: cronometrado do enunciado ao critério de sucesso; comparado ao
  tempo aceitável declarado na tarefa.
- **Desvio de caminho**: contagem de telas/ações fora dos passos esperados.
- **Erros**: leitura errada de número, recorte não percebido, estado
  (vazio/erro/indisponível) confundido — anotados literalmente.
- **Justificativa do número** (blocos C/D): transcrita em uma frase; correta /
  incompleta / errada.

Por sessão: observações do think-aloud e respostas do debrief.

## 4. Registro e guarda da evidência

- **Ficha de sessão**: uma tabela por participante (modelo nos documentos de
  execução), preenchida pelo moderador durante a sessão — nunca de memória
  depois.
- **Capturas**: tela ao final de cada tarefa (estado dos filtros visível).
- **Guarda**: fichas e capturas versionadas em
  `docs/usabilidade/evidencias/` no MR da execução correspondente; nenhuma
  evidência contém dado pessoal (as telas usam os agregados do protótipo,
  já conformes à LGPD).
- **Identificação**: sessões numeradas (S1–S4) com data, versão do
  protótipo/telas usada e nome do moderador; participantes aparecem só como
  P1–P4 com o perfil exercido.

## 5. Papéis na execução

- **Moderador**: apresenta a situação real de cada tarefa (sem revelar os
  passos), cronometra e preenche a ficha.
- **Observador** (quando disponível): anota think-aloud e desvios; não fala
  com o participante.
- O moderador **não ajuda** — pedido de ajuda encerra a medição da tarefa
  como "com assistência" e a sessão continua.

## 6. Critérios para considerar a execução válida

- Toda tarefa executada por ao menos um participante, com ficha completa
  (nenhuma célula vazia ou presumida).
- Tarefas dependentes das telas finais (RP-08) só executam quando as telas
  existirem; execução sobre o protótipo é registrada como **piloto** e
  identificada como tal na ficha — os dois registros não se misturam.
