# Limitações encontradas — análise crítica e propostas

Registro das limitações que afetam o uso da solução de dashboards, no formato
exigido: **impacto** (no usuário/decisão), **causa observada** (com a
evidência que a sustenta) e **proposta de solução**. Toda proposta está
marcada como **proposta** — nenhuma é decisão tomada. Cada limitação aponta a
decisão aberta (DR01–DR06, §5.1 do [`projeto.md`](../projeto.md)) ou a tarefa
de usabilidade que a evidencia; as limitações vindas das sessões de execução
(US-06/US-07) serão acrescentadas na seção 2 quando as rodadas ocorrerem.

## 1. Limitações estruturais observadas no planejamento

### L01 — Taxas sem denominador documentado

- **Impacto:** o usuário espera "taxa de adesão" e a solução só pode exibir
  contagens; taxa apresentada sem denominador induziria decisão errada sobre
  representatividade.
- **Causa observada:** não há universo de empresas/pessoas convidadas nas
  fontes (DR01); I08 e I11 marcados indisponíveis na §5.6.
- **Proposta (não decidida):** acordar com o parceiro o registro do universo
  convidado por pesquisa; até lá, telas mantêm o rótulo "participação
  observada" e o estado "denominador indisponível" — comportamento cuja
  compreensão é testada em T-DET-02.

### L02 — Participação e resposta sem ponte de identidade

- **Impacto:** não é possível responder "quantas pessoas únicas responderam"
  nem detalhar do agregado de respostas para o respondente; soma ingênua de
  linhas superestima pessoas.
- **Causa observada:** 542 `respondent_id` distintos em `respostas.csv` sem
  conciliação com `respondentes.csv` (DR03; §5.2).
- **Proposta (não decidida):** contrato de identidade entre os dois sistemas
  de origem; enquanto não existir, o elo aparece "em reconciliação" (RF07) e
  nenhuma tela soma respostas como pessoas.

### L03 — Pipeline mensal sem histórico retroativo

- **Impacto:** comparações de fluxo mês a mês (entradas/saídas de status) só
  passam a existir do go-live em diante; o gestor não consegue comparar com
  meses anteriores à implantação.
- **Causa observada:** C03 é snapshot periódico e o histórico de transições
  de status não foi recebido (§5.2).
- **Proposta (não decidida):** iniciar a captura mensal imediatamente na
  implantação e comunicar na tela a data de início da série.

### L04 — Cobertura do instrumento de questionários

- **Impacto:** a tela de resultados (D03) representa hoje apenas 10 pesquisas
  (2,7% do acervo); leituras generalizantes a partir dela são inválidas.
- **Causa observada:** cobertura declarada do C04 (§5.2).
- **Proposta (não decidida):** ingestão completa dos questionários junto ao
  parceiro; até lá, a tela expõe a cobertura ao lado da distribuição.

### L05 — Classificação de atraso sem regra aprovada

- **Impacto:** o usuário procura "pesquisas atrasadas" e a solução não pode
  classificar atraso; ausência de regra vira frustração de navegação.
- **Causa observada:** I06 depende de regra de data de referência e
  prioridade não aprovadas (§5.6; critérios do RF03).
- **Proposta (não decidida):** aprovar com o parceiro a regra de referência
  temporal e prioridade; até lá, telas exibem prazos e prorrogações sem
  rótulo de atraso.

### L06 — Papéis de governança sem titular

- **Impacto:** fluxos de qualidade, acesso e publicação (D04) não têm dono
  real para validar; nas sessões, o papel é exercido por participante
  interno, o que limita a validade externa do teste.
- **Causa observada:** papéis propostos sem designação formal (§5.1;
  levantamento de perfis).
- **Proposta (não decidida):** designação formal pelo parceiro; os registros
  de sessão anotam "papel exercido" para não inflar a evidência.

### L07 — Validação funcional sem métricas de uso

- **Impacto:** os testes já documentados (§6.1.2) provam que o dado certo
  aparece, mas não medem se o usuário **chega** a ele em tempo aceitável —
  risco de aprovar telas corretas e inutilizáveis.
- **Causa observada:** lacuna registrada no
  [levantamento](perfis-e-criterios.md) (testes validam requisito, não
  usabilidade).
- **Proposta (não decidida):** manter o plano desta pasta como etapa
  obrigatória de validação, com as métricas de conclusão/tempo/desvio/erro do
  [roteiro](roteiro-execucao.md).

### L08 — Janela de execução dependente das telas finais

- **Impacto:** as sessões de usabilidade dependem das telas dos reports
  (RP-08); indisponibilidade delas na janela da sprint empurra a execução
  para piloto sobre o protótipo, com menor fidelidade.
- **Causa observada:** dependência declarada nos cards US-06/US-07 e estado
  das entregas RP na sprint.
- **Proposta (não decidida):** executar o piloto no protótipo navegável para
  não perder a janela e **reexecutar** nas telas finais, mantendo os dois
  registros separados (regra já fixada no roteiro, §6).

## 2. Resultados das sessões S1–S4

Consolidação das fichas de
[navegação e detalhamento](execucao-navegacao-detalhamento.md) (S1–S2) e de
[comparação e segmentação](execucao-comparacao-segmentacao.md) (S3–S4),
executadas sobre as páginas finais do RP-17 e a geração v3
([preparação](preparacao-sessoes.md)). Foram 17 execuções de tarefa
(16 tarefas; T-NAV-01 executada por dois perfis).

**Taxa de sucesso** = tarefas concluídas sem ajuda ÷ tarefas executadas.
**Taxa de conclusão** = (sem ajuda + com assistência) ÷ tarefas executadas.
**Tempo médio** = média simples dos tempos cronometrados, comparada com a
média dos tempos aceitáveis das mesmas tarefas.

<div align="center">
<sub>Tabela 1 - Sucesso e tempo por bloco do roteiro</sub><br>

| Bloco | Execuções | Sem ajuda | Com assistência | Não concluída | Taxa de sucesso | Taxa de conclusão | Acima do tempo | Tempo médio | Tempo aceitável médio |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A — navegação | 3 | 2 | 1 | 0 | 67% | 100% | 1 | 02:27 | 02:40 |
| B — filtros | 4 | 3 | 1 | 0 | 75% | 100% | 3 | 02:41 | 02:15 |
| C — detalhamento | 5 | 3 | 1 | 1 | 60% | 80% | 1 | 03:09 | 03:36 |
| D — comparação e segmentação | 5 | 2 | 2 | 1 | 40% | 80% | 2 | 03:49 | 03:48 |
| **Total** | **17** | **10** | **5** | **2** | **59%** | **88%** | **7 (41%)** | **03:07** | **03:11** |

<sup>Material produzido pelos autores (2026), a partir das fichas S1–S4</sup>

</div><br>

<div align="center">
<sub>Tabela 2 - Sucesso e tempo por sessão</sub><br>

| Sessão | Perfil | Execuções | Sem ajuda | Com assistência | Não concluída | Tempo médio |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| S1 | UC01 — analista | 6 | 5 | 1 | 0 | 02:47 |
| S2 | UC02 — área técnica/governança | 5 | 2 | 2 | 1 | 03:13 |
| S3 | UC03 — gestor | 4 | 2 | 1 | 1 | 02:40 |
| S4 | UC01 — analista | 2 | 1 | 1 | 0 | 04:45 |

<sup>Material produzido pelos autores (2026), a partir das fichas S1–S4</sup>

</div><br>

Indicadores de qualidade técnica medidos nas mesmas sessões:

| Verificação | Resultado |
| :--- | :--- |
| Precisão (valor exibido × referência no recorte aplicado) | 17 de 17 conferem; nenhuma discrepância de dado |
| Coerência entre granularidades | 9 de 9 verificações coerentes (somas aditivas e médias/completude recompostas por numerador e denominador) |
| Tempo de resposta | 7 de 7 interações medidas abaixo de 2 s (máximo 1,1 s) |
| Justificativa do número (bloco C) | 2 de 5 corretas, 1 incompleta, 2 erradas |
| Recorte enunciado corretamente (bloco D) | 3 de 6 (2 parciais, 1 errado) |

Leitura: o relatório **calcula certo e responde rápido**; a perda está em
**comunicação**. As médias de tempo ficam dentro do aceitável, mas 7 das 17
execuções o ultrapassaram, e os blocos que dependem de saber qual recorte
está ativo (C e D) concentram as duas falhas e três das cinco ajudas.

## 3. Achados das sessões — classificação

Cada achado aponta a ficha que o evidencia e a causa observada na definição
do relatório ou na geração. **Tipo**: *técnico* (a causa está no dado, no
modelo ou na configuração do relatório) ou *compreensão* (o dado e a
configuração estão corretos, mas a página induz leitura errada).
**Severidade** (escala de Nielsen): 4 = impeditivo (impede a tarefa ou leva a
conclusão errada sem saída), 3 = grave, 2 = moderado, 1 = leve.

<div align="center">
<sub>Tabela 3 - Achados, evidência, causa, tipo e severidade</sub><br>

| ID | Achado | Evidência | Causa observada | Tipo | Sev. |
| :--- | :--- | :--- | :--- | :--- | :---: |
| A15 | Estoque aparece em branco, sem motivo; o usuário não distingue "sem fechamento" de erro | S1 T-NAV-02 (assist.); S4 think-aloud; debrief P4 | C03 tem 0 linhas na v3; o cartão `qkpiestoque00001` usa `Estoque no Status`, e a medida `Estado do Estoque`, que tem o motivo textual, não é exibida | técnico (relatório) | 4 |
| A17 | Comparação temporal impossível: slicer Ano só com "(Em branco)" e gráfico mensal com uma barra sem mês | S3 T-CMP-01 (assist.), T-CMP-02 (não); debrief P3 | `mes_resposta` vazio nas 32 linhas de C02; `DIM_TEMPO` é calculada de C02 e C03 e fica só com o vazio | técnico (dado de origem) | 4 |
| A12 | Filtro de Área não acompanha a troca de página; o total global é lido como sendo da área | S2 T-DET-03 (não); S4 T-SEG-02 | Nenhum slicer do relatório tem grupo de sincronização (`syncGroup`) | técnico (relatório) | 3 |
| A06 | Drill-down Área → Tipo não existe nos visuais, embora documentado | S1 T-DET-01 (2 desvios) | `Volume por Área` e `Participações por área` têm um único campo no eixo; a tabela de estoque é plana e os eixos de tempo usam a coluna, não a hierarquia `Calendario` | técnico (relatório) | 3 |
| A10 | Texto "DADOS SIMULADOS" na página C02 faz o usuário desconfiar de todos os números | S2 debrief | Texto fixo no visual `v2_status`, herdado da página de demonstração | técnico (relatório) | 3 |
| A13 | Completude sem registros afetados nem natureza do nulo; ausência permitida lida como falha | S2 T-DET-04 (assist.; justificativa errada) | A tabela mostra só `Completude`; `qtd_linhas` e `qtd_preenchidas` existem em `PUB_QUALIDADE_CAMPO`, mas não estão no visual | técnico (relatório) | 3 |
| A18 | Produção e Volume não tem período: "quando foram pedidas?" não tem resposta | S1 T-FIL-01; S3 T-SEG-01 | C01 não publica data nem ano de edição (contrato CB-12) | técnico (contrato da publicação) | 3 |
| A09 | Participações lidas como pessoas; recorte por empresa procurado e ausente | S2 T-DET-02 (justificativa incompleta); S3 think-aloud | O aviso "conta ocorrências, não pessoas" está no rodapé; empresa não é publicada em C02 | compreensão | 3 |
| A05 | Recorte vazio aparece como cartões em branco, sem mensagem | S1 T-FIL-04; S4 T-SEG-03 | As medidas retornam vazio, sem texto alternativo para recorte sem linha | técnico (relatório) | 2 |
| A11 | Média de preenchimento em branco sem motivo; cartão "Indicadores sem dado" em destaque e sem contexto | S2 T-DET-02 | Base de preenchimento 0 na v3; o cartão `v2_kpi2` ocupa a posição de indicador principal | técnico (relatório) | 2 |
| A19 | Médias exibidas sem a base: 0,0 dia de validação calculado sobre uma única pesquisa | S1 think-aloud; debrief P1 | O gráfico de etapas não mostra `Base Valida *`; a validação tem base de 20 pesquisas (`data_aprov` com 5,5% de completude) | técnico (relatório e dado) | 2 |
| A20 | Durações em dias corridos; a Central raciocina em dias úteis | S1 e S3 think-aloud; Rodada 0 | C01 publica só dias corridos; a origem tem `dias_uteis_para_entrega` com 90,4% de preenchimento | técnico (contrato da publicação) | 2 |
| A01 | Avisos de ano de edição e complexidade têm o formato dos slicers e são clicados como filtro | S1 T-FIL-01 (3 desvios) | Caixas de texto no mesmo tamanho e posição dos slicers retirados | compreensão | 2 |
| A03 | "Base válida ciclo total" (331) confundida com finalizadas (332); total repetido em dois cartões | S1 T-NAV-01 | Rótulo técnico da medida; `Qtd Pesquisas` aparece em "Pesquisas no recorte" e em "Indicadores principais" | compreensão | 2 |
| A04 | Não há ação única para limpar filtros; um slicer fica ativo sem ser notado | S2 T-FIL-03 (assist.) | O relatório não tem botão de redefinição nem resumo dos filtros ativos | compreensão | 2 |
| A07 | "Acompanhamento das Pesquisas" sugere lista de pesquisas, mas é agregado | S1 T-DET-05 | Título herdado da página de demonstração | compreensão | 2 |
| A14 | Não fica claro que Status e Mês da terceira página filtram só o estoque | S2 T-DET-04; S4 T-SEG-02 (assist.) | Sem relacionamento de C04 e qualidade com status e tempo (por desenho); a página não indica o escopo dos filtros | compreensão | 2 |
| A23 | Sete status sem agrupamento "não finalizada"; o usuário filtra só "em andamento" | S2 T-FIL-02 | Os status de origem aparecem como estão, sem categoria de agrupamento | compreensão | 2 |
| A02 | Sem navegação dentro do relatório; o usuário procura um menu na faixa lateral | S1 T-NAV-02 | Navegação só pelas abas de página | compreensão | 1 |
| A08 | Média de ciclo em branco nas linhas não finalizadas lida como zero | S1 T-DET-01 | Base válida 0 nesses grupos; a célula fica vazia sem rótulo | compreensão | 1 |
| A16 | Tipos de pergunta exibidos com nomes técnicos (`multipla_escolha`) | S2 e S4 think-aloud | Valores de origem sem coluna de rótulo em `DIM_TIPO_PERGUNTA` | compreensão | 1 |
| A21 | Três visuais fora da área visível consultam o modelo e recebem foco por teclado | Medição de tempo de resposta (S3–S4) | `v2_area`, `v2_detail` e `v2_time` posicionados em (-100, -100) com 1 × 1 px | técnico (relatório) | 1 |
| A22 | Códigos (I05, I07, I16, C02) nos títulos e avisos; nome da aba difere do título da página | S1 think-aloud | Rótulos de catálogo usados na interface; aba "Estoque e Qualidade (C03/C04)" × título "Estoque, Instrumento e Qualidade" | compreensão | 1 |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

Distribuição: 23 achados — 12 técnicos e 11 de compreensão; 2 impeditivos,
6 graves, 10 moderados e 5 leves. **Nenhum achado é erro de cálculo**: os
dois impeditivos vêm da falta de dado na geração (A17) e da forma de exibir
um estado `sem dado` (A15).

## 4. Propostas e destino de cada achado

Todas as propostas estão marcadas como **proposta** — a decisão é de quem
responde pela frente de destino. **RP** = páginas do relatório
(`powerbi/CentralPesquisasBI.Report/`); **BI** = modelo semântico
(`powerbi/CentralPesquisasBI.SemanticModel/`); **CB** = carga e publicação
dos cubos (`src/etl/analytics/`).

<div align="center">
<sub>Tabela 4 - Proposta, destino e critério de reteste</sub><br>

| ID | Proposta (não decidida) | Destino | Reteste |
| :--- | :--- | :--- | :--- |
| A15 | Exibir `Estado do Estoque` no cartão de estoque (valor textual quando não há fechamento) e no subtítulo do gráfico mensal | RP (`qkpiestoque00001`, `qestoque000000004`) | T-NAV-02 |
| A17 | Investigar a data de resposta na origem e na carga de C02; enquanto faltar, substituir a barra vazia por aviso "mês de resposta indisponível nesta geração" e ocultar o slicer Ano quando ele só tiver vazio | CB (C02) e RP (`v2_absent`, `3307368b9b0eb3020a56`) | T-CMP-01, T-CMP-02 |
| A12 | Sincronizar os slicers Área, Tipo e Status entre as páginas em que se aplicam (mesmo grupo de sincronização) | RP (slicers das três páginas) | T-DET-03, T-SEG-02 |
| A06 | Colocar `tipo` como segundo nível nos eixos de área e usar a hierarquia `Calendario` nos eixos de tempo; trocar a tabela de estoque por matriz com `Area, Tipo e Perfil` | RP (`pvarea000000000010`, `v2_frequent`, `v2_absent`, `qtabestoque000006`) | T-DET-01 |
| A10 | Remover o texto fixo "DADOS SIMULADOS" ou trocá-lo por medida com a geração e o `load_reference` carregados | RP (`v2_status`) e BI (medida de identificação da geração) | Debrief |
| A13 | Acrescentar `qtd_linhas`, `qtd_preenchidas` e registros sem valor à tabela de completude; distinguir campos de preenchimento condicional (ex.: `prorrogada_ate`) | RP (`qtabcompletud00007`) e BI (classificação do nulo) | T-DET-04 |
| A18 | Publicar o ano/mês de solicitação no grão de C01 para permitir período na página de produção | CB (contrato de C01) e BI | T-FIL-01, T-CMP-01 |
| A09 | Levar "conta ocorrências, não pessoas" para o subtítulo do cartão de participações; manter a explicação de empresa indisponível ao lado dos filtros | RP (`v2_kpi1`, `v2_privacy`) | T-DET-02 |
| A05 | Medida-texto de recorte vazio ("Nenhuma pesquisa no recorte selecionado") nos cartões de contagem | BI e RP | T-FIL-04, T-SEG-03 |
| A11 | Medida-texto de estado para a média de preenchimento; mover o cartão "Indicadores sem dado" para junto do gráfico de motivos | BI e RP (`v2_kpi2`, `v2_kpi3`) | T-DET-02 |
| A19 | Mostrar a base válida de cada etapa na dica do gráfico e marcar médias com base inferior a 5 pesquisas | RP (`e1943eaed82275129d4e`) | T-DET-01 |
| A20 | Publicar a duração em dias úteis a partir de `dias_uteis_para_entrega` e rotular a unidade em cada visual | CB (C01), BI e RP | T-NAV-01 |
| A01 | Diferenciar visualmente os avisos dos slicers (ícone, fundo neutro, texto em itálico) ou agrupá-los num bloco "Não disponível neste cubo" | RP (faixa lateral das páginas 1 e 2) | T-FIL-01 |
| A03 | Renomear "Base válida ciclo total" para "Pesquisas com ciclo medido" e retirar a repetição do total | RP (`655b60cbe268a86e200c`) | T-NAV-01 |
| A04 | Botão "Limpar filtros" (indicador de estado) e linha de resumo dos filtros ativos | RP | T-FIL-03 |
| A07 | Renomear para "Pesquisas por área, status e tipo" e indicar o grão no subtítulo | RP (`7ca374f79a7cd6921a48`) | T-DET-05 |
| A14 | Separar os filtros da terceira página por seção, com o rótulo "filtra só o estoque" | RP (página 3) | T-SEG-02 |
| A23 | Coluna de agrupamento de status (finalizada / não finalizada) em `DIM_STATUS_PESQUISA` | BI | T-FIL-02 |
| A02 | Botões de navegação entre páginas na faixa lateral | RP | T-NAV-02 |
| A08 | Formatar a média vazia como "sem ciclo concluído" | BI | T-DET-01 |
| A16 | Coluna de rótulo legível em `DIM_TIPO_PERGUNTA` | BI | T-SEG-02 |
| A21 | Excluir os três visuais fora da área visível | RP (`v2_area`, `v2_detail`, `v2_time`) | Medição de resposta |
| A22 | Substituir códigos por nomes na interface (código na dica) e alinhar nome da aba e título | RP | T-NAV-02 |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

## 5. Tratamento dos impeditivos

Os dois achados de severidade 4 foram encaminhados na síntese de S3–S4
([E2 e E3](execucao-comparacao-segmentacao.md#encaminhamentos-para-rp-17-e-bi-04)).
Nenhum deles é erro de cálculo, por isso o aceite de dado das páginas não
volta para BI-04; o que fica condicionado é o **aceite de usabilidade** das
tarefas afetadas.

### A15 — estoque em branco sem motivo

- **Correção especificada:** o modelo entregue no BI-06 já contém a medida
  `Estado do Estoque` (`PUB_C03_PIPELINE_MENSAL`; ainda ausente da definição
  da branch do RP-17), que devolve
  "Indisponível: a geração publicada não contém linha C03 para o período
  selecionado." quando não há fechamento, e "Disponível no fechamento de
  dd/MM/aaaa" quando há. Depois da integração BI-06 + RP-17, a correção é de
  vínculo, sem DAX novo: incluir essa
  medida como valor de referência (subtítulo) do cartão `qkpiestoque00001` e
  como subtítulo do gráfico `qestoque000000004`.
- **Destino:** RP (páginas finais), com conferência em BI-04.
- **Critério de fechamento:** com a geração v3, o cartão mostra o motivo
  textual; com a fixture que tem fechamento (estoque 3 em 31/01/2026 e 4 em
  28/02/2026, [RP-17](../solucao-dashboards/validacao-paginas-finais.md)), o
  cartão mostra o valor e a data. T-NAV-02 é reexecutada.
- **Estado:** encaminhado.

### A17 — comparação temporal sem mês de resposta

- **Correção especificada:** a causa está no dado, não no relatório:
  `mes_resposta` chega vazio às 32 linhas de C02, coerente com
  `respondentes.hora_inicio` a 0% de completude na tabela de qualidade. A
  correção definitiva depende de a origem fornecer a data de resposta e de a
  carga de C02 derivá-la (CB). Mitigação no relatório: substituir a barra
  "(Em branco)" por aviso textual e ocultar o slicer Ano quando ele só
  contiver vazio, para que a página declare o `sem dado` em vez de
  apresentá-lo como categoria.
- **Destino:** CB (dado e publicação de C02) e RP (mitigação).
- **Critério de fechamento:** nova geração com `mes_resposta` preenchido e
  T-CMP-01/T-CMP-02 reexecutadas com sucesso; até lá, a mitigação é
  verificada lendo a página com a v3.
- **Estado:** encaminhado; permanece como limitação efetiva da geração v3.
