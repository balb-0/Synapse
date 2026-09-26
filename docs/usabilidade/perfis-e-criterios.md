# Perfis de usuário, critérios de aceite e testes já documentados

Este levantamento consolida o que o projeto **já documentou** sobre quem usa a
solução analítica, o que cada perfil precisa responder e como isso é aceito e
testado. Nada aqui é criação nova: as seções de origem no
[`projeto.md`](../projeto.md) são indicadas antes de cada tabela. O objetivo é servir de base única para as
tarefas de usabilidade (documentos seguintes desta pasta), garantindo que toda
tarefa nasça ligada a um perfil real, a uma pergunta de negócio (PB) e a um
critério de aceite já validado.

## 1. Perfis de usuário documentados

Os perfis vêm da síntese de consumo analítico (§5.1 do `projeto.md`), onde
aparecem como públicos UC01–UC04, e da seção de governança (§6.6), que propõe
os papéis de dados.

<div align="center">
<sub>Tabela 1 - Perfis de usuário e forma de consumo documentada</sub><br>

| Perfil | Quem é | Forma de consumo documentada | Dashboards |
| :--- | :--- | :--- | :--- |
| UC01 — Central de Pesquisas | Equipe operacional que conduz as pesquisas | Acompanha o fluxo operacional com detalhe condicionado ao perfil; filtros e relatórios | D01, D02, D04 |
| UC02 — Áreas técnicas | Áreas que validam instrumentos e interpretam resultados | Validação de questionários e leitura de resultados agregados | D02, D03 |
| UC03 — Gestores | Gestão da Central/Sindusfarma | Recortes consolidados, sem drill-down pessoal presumido | D01, D02, D03 |
| UC04 — Externos | Solicitantes, participantes e público externo | Apenas resultados autorizados no acervo; sem acesso aos dashboards internos | — |

<sup>Material produzido pelos autores (2026), consolidado da síntese de consumo analítico do projeto</sup>

</div><br>

Papéis de governança (Data Owner, Data Steward, Data Custodian/TI e auditor)
são **propostos e ainda sem designação formal** (§5.1); os testes que dependem
deles usam massa de teste identificada como tal (§6.1.2).

## 2. Perfil × perguntas de negócio × requisito

Cruzamento dos perfis com as PB01–PB13 (§6.3) e os RF01–RF13 (§6.1) que as
atendem. É este mapa que as tarefas de usabilidade devem cobrir.

<div align="center">
<sub>Tabela 2 - Perfil, pergunta de negócio que ele responde e requisito correspondente</sub><br>

| Perfil | Perguntas de negócio | Requisitos | Dashboard |
| :--- | :--- | :--- | :--- |
| UC01 — Central | PB01 portfólio; PB02 ciclo/detalhe; PB03 prazos; PB04 adesão; PB12 integração | RF01, RF02, RF03, RF04, RF12 | D01, D02, D04 |
| UC02 — Áreas técnicas | PB10 distribuição de respostas; PB11 contexto agregado; PB13 questionário validado | RF10, RF11, RF13 | D03 |
| UC03 — Gestores | PB01, PB03 (consolidados); PB04–PB05 alcance e públicos | RF01, RF03, RF04, RF05 | D01, D02 |
| UC04 — Externos | PB09 publicação autorizada (consulta ao acervo) | RF09 | — |
| Governança (proposto) | PB06 qualidade; PB07 linhagem; PB08 acesso por perfil | RF06, RF07, RF08 | D04 |

<sup>Material produzido pelos autores (2026), a partir da matriz de rastreabilidade (§5.2.5) e da §6.3</sup>

</div><br>

## 3. Critérios de aceite já documentados

A §6.1.1 define critérios de aceitação por requisito, todos no formato
dado/quando/então e independentes de tecnologia. Três contratos transversais
aparecem em praticamente todos os RFs e valem como critério de aceite geral
para qualquer tela:

1. **Estados distintos** — "sem dados", "indisponível", "erro" e "acesso
   negado" nunca se confundem; recorte vazio não é falha e dado ausente não é
   zero (RF01, RF03, RF05, RF06, RF10).
2. **Denominador explícito** — nenhuma taxa é exibida sem numerador e
   denominador identificáveis; sem universo documentado, a taxa fica
   indisponível (RF04, RF05, RF10, RF11).
3. **Temporalidade rotulada** — `data_solicitacao` é o campo temporal padrão;
   qualquer outro marco só vale quando selecionado explicitamente e rotulado
   (RF01, RF03).

Critérios específicos por RF (acesso por perfil, linhagem, publicação etc.)
permanecem na §6.1.1 e são referenciados pelas tarefas quando aplicáveis.

## 4. Testes de usuário já documentados

A §6.1.2 traz um roteiro de teste por requisito (RF01–RF13), cada um com
persona, pré-condições, passos, resultado esperado, evidência e responsável
pela aprovação. Síntese do que existe:

<div align="center">
<sub>Tabela 3 - Testes de usuário documentados e perfil responsável</sub><br>

| Teste (§6.1.2) | Persona documentada | Aprovação registrada por |
| :--- | :--- | :--- |
| RF01 portfólio | Gestor ou analista da Central (UC01/UC03) | Gestor ou analista da Central |
| RF02 ciclo e detalhe | Analista da Central (UC01) | Analista da Central |
| RF03 prazos e prioridades | Gestor ou analista da Central (UC01/UC03) | Gestor ou analista da Central |
| RF04–RF05 adesão e engajamento | Analista da Central e gestor (UC01/UC03) | Central de Pesquisas |
| RF06–RF08 qualidade, linhagem e acesso | Data Steward / auditor (governança proposta) | Papel de governança indicado |
| RF09 publicação | Data Owner / Custodian (governança proposta) | Papel de governança indicado |
| RF10–RF11 resultados e contexto | Analista / auditor autorizado (UC02) | Central de Pesquisas |
| RF12 integração | Analista técnico (UC01) | Central de Pesquisas |
| RF13 questionário versionado | Área técnica revisora (UC02) | Área técnica |

<sup>Material produzido pelos autores (2026), consolidado da §6.1.2 do projeto</sup>

</div><br>

## 5. Lacunas encontradas no levantamento

Registro do que **não** está coberto pelo material existente — insumo direto
para o plano de usabilidade:

- **Os testes da §6.1.2 validam requisito, não usabilidade.** Eles conferem
  comportamento funcional (o dado certo aparece), mas não medem tempo de
  conclusão, desvio de caminho nem esforço do usuário — é exatamente o que as
  tarefas desta pasta acrescentam.
- **UC04 (externos) não tem tela própria**: o acervo público está fora do
  protótipo atual; tarefas de usabilidade para esse perfil ficam limitadas ao
  que o acervo expõe e são registradas como dependentes de publicação.
- **Papéis de governança sem titular**: os testes de RF06–RF09 pedem massa de
  teste identificada; nas sessões de usabilidade, esses papéis são exercidos
  por participante interno fazendo o papel, e isso fica anotado no registro.
- **Indicadores indisponíveis** (I06, I08, I11, I15, I21–I25 conforme §5.6):
  tarefas que passem por eles devem esperar a sinalização de "indisponível
  com motivo", nunca um valor — isso já é critério de aceite, e vira critério
  de sucesso das tarefas.
