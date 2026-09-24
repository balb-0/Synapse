# Perfis de usuário, critérios de aceite e testes já documentados

Este levantamento consolida o que o projeto **já documentou** sobre quem usa a
solução analítica, o que cada perfil precisa responder e como isso é aceito e
testado. Nada aqui é criação nova: cada linha cita a seção de origem no
[`projeto.md`](../projeto.md). O objetivo é servir de base única para as
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

