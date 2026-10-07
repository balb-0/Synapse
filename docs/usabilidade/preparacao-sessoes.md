# Preparação das sessões S1–S4 (rodada final)

Preparação da rodada final de usabilidade sobre as páginas do relatório
`CentralPesquisasBI`, conforme o [roteiro](roteiro-execucao.md). Este
documento fixa quem participa, o que é usado em cada sessão e como a
evidência é capturada, para que as fichas de execução possam ser comparadas
entre si e reproduzidas depois.

## 1. Participantes e perfis

Os participantes são integrantes do grupo e convidados internos **exercendo o
papel** do perfil (regra do roteiro, §1). Aparecem apenas pelo código da
sessão; nenhum nome, e-mail ou imagem do participante é registrado.

<div align="center">
<sub>Tabela 1 - Sessões, participantes e perfis exercidos</sub><br>

| Sessão | Participante | Perfil exercido | Familiaridade prévia com o relatório | Tarefas |
| :--- | :--- | :--- | :--- | :--- |
| S1 | P1 | UC01 — analista da Central | Viu as páginas de demonstração na Sprint 4 | T-NAV-01, T-NAV-02, T-FIL-01, T-FIL-04, T-DET-01, T-DET-05 |
| S2 | P2 | UC02 — área técnica, exercendo também o papel de governança | Nenhuma | T-FIL-02, T-FIL-03, T-DET-02, T-DET-03, T-DET-04 |
| S3 | P3 | UC03 — gestor | Assistiu à Rodada 0 com o parceiro | T-NAV-01, T-CMP-01, T-CMP-02, T-SEG-01 |
| S4 | P4 | UC01 — analista da Central | Nenhuma | T-SEG-02, T-SEG-03 |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

A familiaridade prévia é registrada porque quem conheceu as páginas de
demonstração (com empresa, pesquisa e prorrogação) tende a procurar recursos
que a publicação agregada não oferece; essa expectativa é parte do que as
sessões medem.

## 2. Papéis e agenda

| Papel | Responsável |
| :--- | :--- |
| Moderadora (apresenta as tarefas, cronometra, preenche a ficha) | Anna |
| Observador (anota think-aloud e desvios; não fala com o participante) | Integrante do grupo que não participa como P1–P4 |

<div align="center">
<sub>Tabela 2 - Agenda da rodada final</sub><br>

| Sessão | Data | Duração prevista | Ficha |
| :--- | :--- | :--- | :--- |
| S1 | 06/10/2026 | 45 min | [`execucao-navegacao-detalhamento.md`](execucao-navegacao-detalhamento.md) |
| S2 | 06/10/2026 | 45 min | [`execucao-navegacao-detalhamento.md`](execucao-navegacao-detalhamento.md) |
| S3 | 06/10/2026 | 35 min | [`execucao-comparacao-segmentacao.md`](execucao-comparacao-segmentacao.md) |
| S4 | 06/10/2026 | 30 min | [`execucao-comparacao-segmentacao.md`](execucao-comparacao-segmentacao.md) |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

Cada sessão segue a ordem fixa do roteiro (§2): aquecimento de 1 minuto,
blocos A–D nas tarefas atribuídas e debrief com as duas perguntas fixas.

## 3. Versão do relatório e geração usadas

Todas as sessões usam **o mesmo relatório e a mesma geração**. Trocar
qualquer um dos dois exige uma nova rodada.

<div align="center">
<sub>Tabela 3 - Alvo das sessões</sub><br>

| Item | Valor |
| :--- | :--- |
| Relatório | `powerbi/CentralPesquisasBI.pbip`, páginas Produção e Volume; Participação agregada (C02); Estoque, Instrumento e Qualidade |
| Versão do relatório | Tip do RP-17 `94e91ef5e9c009a162b02c1986a8ce8b60628e8b`, pacote integrado com SHA-256 `a9b087e5a9e4e0d56af8d7b36fe0a687857b205e7c59b6dbd44c9dd7c2358cea` ([validação RP-17](../solucao-dashboards/validacao-paginas-finais.md)) |
| Geração Parquet | v3 `6b1eaa686aac43b18b6d6545e1c2c5f1`, `load_reference` `afcde424-45e8-457b-8793-bf0866d142b2` ([publicação CB-16](../acesso-cubos-bi.md)) |
| Linhas esperadas por tabela (manifesto) | `PUB_C01_CICLO` 57; `PUB_C02_PARTICIPACAO` 32; `PUB_C03_PIPELINE_MENSAL` 0; `PUB_C04_INSTRUMENTO` 45 |
| Parâmetro do modelo | `PastaPublicacaoBI` apontando para a subpasta local da geração v3, fora do repositório |
| Ambiente | Power BI Desktop em Windows, modo de leitura (sem painel de edição aberto) |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

A geração v3 não tem fechamento mensal observado em C03 (0 linhas). Isso é
estado `sem dado` da publicação, não falha de carga, e as tarefas que passam
pela seção de estoque medem justamente se a página comunica esse estado.
