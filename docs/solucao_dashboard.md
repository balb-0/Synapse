# Solução de dashboard — implementação e validação

**Estado em 25/09/2026.** Este documento separa o report demonstrado com dados sintéticos, o modelo semântico que importa os agregados publicados pela ETL e os testes de usuário ainda pendentes. Definições TMDL/JSON comprovam configuração, mas não atualização, precisão dos valores exibidos ou interação no Power BI Desktop.

## 1. Cubos, fontes e alcance

| Artefato | Fonte e grão | Evidência e limite |
| :--- | :--- | :--- |
| [PBIP demonstrativo](../src/pbir%20dash/dashboard.Report/) e [modelo](../src/pbir%20dash/dashboard.SemanticModel/) | CSVs locais `vw_ciclo_pesquisa.csv` (pesquisa) e `vw_participacao.csv` (ocorrência), por caminhos absolutos externos ao Git | Duas páginas, **Produção e Volume** e **Benchmark Externo — V2**, com medidas e visuais versionados. Dados sintéticos, sem conexão comprovada à publicação oficial. |
| [Modelo de consumo](../powerbi/CentralPesquisasBI.SemanticModel/) | Sete Parquet de uma geração: C01–C04 agregados e três tabelas de qualidade | Importações, medidas e relacionamentos definidos em TMDL; não há páginas finais equivalentes nem evidência de refresh visual contra uma geração real. |

Os cubos físicos C01 (portfólio e ciclo), C02 (participação), C03 (snapshot mensal do pipeline) e C04 (instrumento) alimentam o [publicador](../src/etl/analytics/publish.py). Os Parquet `PUB_C01_CICLO`, `PUB_C02_PARTICIPACAO`, `PUB_C03_PIPELINE_MENSAL` e `PUB_C04_INSTRUMENTO` são recortes **agregados**, não cópias dos fatos físicos. O pacote inclui também `PUB_QUALIDADE_CAMPO`, `PUB_QUALIDADE_RELACAO` e `PUB_QUALIDADE_DUPLICIDADE`; ver [acesso](acesso-cubos-bi.md) e [indicadores publicáveis](indicadores-publicaveis-bi.md). A publicação não traz IDs de pesquisa ou empresa. A tabela por pesquisa e o benchmark individual demonstrados não podem ser simplesmente redirecionados a esses arquivos: exigem decisão de publicação e privacidade, contrato de grão, medidas adaptadas e nova validação.

### Visuais das duas páginas demonstrativas

| Página/visual | Medida ou campo | Dimensão/filtro e ressalva |
| :--- | :--- | :--- |
| Produção: cartões de pesquisas, finalizadas e em aberto | `D01_CicloPesquisa[Pesquisas]` (`DISTINCTCOUNT` de pesquisa), `Pesquisas Finalizadas`, `Pesquisas em Aberto` | Segmentadores `ano_edicao`, `area`, `tipo`, `status`, `complexidade` da própria D01. `ano_edicao` não é hierarquia de `data_solicitacao`. |
| Produção: taxa de finalização | `Taxa de Finalização` = finalizadas / pesquisas com `DIVIDE` | Mesmo contexto D01; denominador zero gera vazio. Não é taxa de adesão. |
| Produção: ciclo e etapas por tipo | Médias de `dias_ciclo_total_corridos`, `dias_validacao_corridos`, `dias_coleta_corridos`, `dias_tabulacao_corridos` | Tipo e demais segmentadores D01. **Todas são em dias corridos.** Não há calendário de dias úteis implementado; `AVERAGE` ignora nulos. |
| Produção: volume por área/status | `Pesquisas` | `area` ou `status` da D01. |
| Produção: prorrogações e tabelas | `Pesquisas Prorrogadas`; `flag_prorrogada`, título, área, tipo, status, duração, entrega | Filtro visual de `flag_prorrogada` na tabela de prorrogações. Detalhe por pesquisa só no CSV demonstrativo. |
| Benchmark: cartões | `BE Pesquisas da empresa`, `BE Empresas observadas`, `BE Pesquisas no recorte` | `BE_Empresa[Empresa]`, `BE_Pesquisa[Pesquisa/Ano/Área/Tipo]`. Ano deriva de `data_divulgacao`, diferente do ano de edição da Produção. |
| Benchmark: perfil por área e evolução anual | `BE % empresa por área`, `BE % demais por área`, `BE Pesquisas por ano`, `BE Média demais por ano` | Área, ano e empresa. Perfil por área é fração das pesquisas observadas da empresa distribuída entre áreas; não é taxa de adesão por área. Evolução usa contagens e média dos demais. |
| Benchmark: faixa e detalhe | `BE Empresas por faixa`, `BE Selecionada por faixa`, `BE Percentual observado`, `BE Empresa participou`, `BE % observado Top 8` | Faixa, pesquisa e empresa. Percentual usa o conjunto de empresas registrado, sem universo de convidadas; não é participação de mercado. |

Os JSON dos [visuais de Produção](../src/pbir%20dash/dashboard.Report/definition/pages/5d499bb7bb62646ad6e5/visuals/) e [Benchmark](../src/pbir%20dash/dashboard.Report/definition/pages/e18bd740de609936581b/visuals/) e as medidas [D01](../src/pbir%20dash/dashboard.SemanticModel/definition/tables/D01_CicloPesquisa.tmdl) e [BE](../src/pbir%20dash/dashboard.SemanticModel/definition/tables/BE_Empresa.tmdl) sustentam o mapeamento. Não há terceira ou quarta página nesse PBIP.

### Relacionamentos, segmentações e hierarquias

No demonstrativo, D01 e D02 são importações independentes, sem relacionamento físico fato–fato. `BE_Pesquisa` deriva da D01; medidas de benchmark aplicam IDs de pesquisa e empresa à D02 com `TREATAS`. `BE_Faixa` é desconectada e fornece limites às medidas. `KEEPFILTERS`, `REMOVEFILTERS`, `ALLSELECTED` e `HASONEVALUE` controlam o contexto. Isso permite o recorte do benchmark sintético, mas não forma uma dimensão conformada publicada pela ETL. A seleção numa página não comprova sincronização com a outra.

No modelo Parquet, `DIM_AREA` filtra C01–C04; `DIM_TIPO_PESQUISA`, C01–C03; `DIM_STATUS_PESQUISA`, C01/C03; `DIM_TIPO_PERGUNTA`, C04; e `DIM_TEMPO`, o mês da resposta de C02 e o fechamento de C03. Os [relacionamentos TMDL](../powerbi/CentralPesquisasBI.SemanticModel/definition/relationships.tmdl) são muitos-para-um, com direção única da dimensão ao fato. C01 publicado não possui chave temporal nesse modelo: **ano → trimestre → mês de solicitações em C01 não está disponível**. `area` é área de negócio, não região. Os segmentadores das páginas são cortes simples; não há prova de drill-down hierárquico ou página de drill-through configurada. C03 usa o último snapshot do período: somar estoques de meses distintos repete o mesmo estoque.

No modelo publicado, a média correta é `DIVIDE(SUM(soma_dias_*), SUM(qtd_*_disponivel))`, como no [TMDL de C01](../powerbi/CentralPesquisasBI.SemanticModel/definition/tables/PUB_C01_CICLO.tmdl). Médias e taxas de grupos não são somadas; reconciliam-se seus componentes. Só contagens de grupos disjuntos no mesmo grão são diretamente aditivas.

## 2. Plano de tarefas de usabilidade

O [roteiro moderado](usabilidade/roteiro-execucao.md) define quatro perfis exercidos, ordem, cronômetro, conclusão, desvios, erros e debrief. Os 15 cenários se dividem entre [navegação/filtros](usabilidade/tarefas-navegacao-filtros.md), [detalhamento](usabilidade/tarefas-detalhamento.md) e [comparação/segmentação](usabilidade/tarefas-comparacao-segmentacao.md).

| Bloco | Interação e critério observável | Condição no alvo atual |
| :--- | :--- | :--- |
| T-NAV/T-FIL | Abrir página, aplicar ano/área/tipo/status, combinar cortes, limpar filtro e distinguir vazio de erro; conferir cartões, gráficos e tabela no mesmo recorte | Anunciar que Produção usa ano de edição e Benchmark usa ano de divulgação. |
| T-DET | Sair do agregado e localizar a pesquisa na tabela; explicar o valor | Expansão/filtragem de tabela pode ser testada nos CSVs. Drill-down temporal e drill-through entre páginas exigem implementação e observação específicas. |
| T-CMP | Comparar períodos equivalentes e explicar medida temporal | Produção não tem filtro por `data_solicitacao`; tarefa nesse marco requer implementação. Recalcular médias com bases válidas. |
| T-SEG | Aplicar dois ou três filtros e cruzar leitura entre cartões, gráficos e tabela | Registrar filtros, valor exibido, referência no mesmo recorte e tempo de resposta. Cruzamento **entre páginas** exige evidência própria. |

Os roteiros pressupõem D01–D04 e recursos ausentes no PBIP demonstrativo. Antes da sessão, cada tarefa deve ser marcada como **executável**, **piloto parcial** ou **bloqueada** para o alvo usado. Tarefa bloqueada não recebe sucesso. Para validar a arquitetura oficial, repetir em páginas ligadas à mesma geração Parquet e usar o manifesto e consultas ao DuckDB no mesmo recorte como referência. Piloto sintético mede leitura da interface, não integridade dos cubos oficiais.

## 3. Execução e resultados

**Rodada 0, 25/09/2026:** as [fichas de navegação](usabilidade/execucao-navegacao-detalhamento.md) e [comparação](usabilidade/execucao-comparacao-segmentacao.md) registram demonstração ao parceiro com dados sintéticos. Houve elogio à expansão das tabelas e à leitura por tipo; o parceiro pediu ciclo em **dias úteis** e maior destaque à duração média. A demonstração não seguiu as 15 tarefas moderadas nem mediu tempo, precisão ou falhas, e não valida os Parquet.

**Sessões S1–S4:** fichas vazias; nenhuma evidência versionada de conclusão, valores versus referência, filtros, estabilidade, latência, drill-down ou drill-through no Power BI Desktop. A execução exigida pelo barema está **pendente**. A verificação estática comprova duas páginas, visuais, segmentadores e medidas, apenas. O [diretório de evidências](usabilidade/evidencias/) deve receber capturas identificadas por sessão e recorte.

Para cada tarefa executada, registrar ID e conclusão (sim/com assistência/não), tempo, filtros e marco temporal, valor exibido, referência, reconciliação por grão, resposta dos visuais, erro/lentidão e captura. Para média ou taxa, comparar numerador e denominador, não a soma das médias ou taxas detalhadas. Falhas recebem impacto, causa sustentada por evidência e proposta no [registro de limitações](usabilidade/limitacoes-e-propostas.md).

## 4. Avaliação técnica, visual e pendências

| Critério | Evidência atual | Estado |
| :--- | :--- | :--- |
| Cubos, dimensões e medidas | Dois modelos acima; publicação agregada não sustenta benchmark individual ou tabela por pesquisa | **Parcial** |
| Plano de usabilidade | Roteiro, perfis, 15 cenários e fichas | **Atendido como plano**; adequação ao alvo por tarefa pendente |
| Precisão e validação funcional | Demonstração qualitativa; sessões e conciliação de valores vazias | **Não comprovada** |
| Clareza visual e interação | Duas páginas e [capturas](assets/dashboard/); feedback sobre tabelas e leitura por tipo | **Parcial**; foco, contraste, teclado, fluidez e cruzamentos não medidos |
| Arquitetura analítica | Modelo Parquet com dimensões conformadas; report demonstrado ainda importa CSVs sintéticos | **Parcial** |

**Propostas prioritárias:** conectar páginas finais à mesma geração Parquet e redesenhar visuais incompatíveis com o grão, ou aprovar publicação detalhada e seus controles de privacidade; definir calendário de dias úteis e feriados antes de alterar medida/rótulo; implementar hierarquia temporal e drill-through onde o contrato permitir; executar S1–S4 e conferência de valores; verificar renderização e interação no Power BI Desktop. São propostas, não resultados alcançados.

**Pendências para concluir a validação:** geração Parquet real com manifesto e prova de refresh; decisão aprovada sobre grão e divulgação por pesquisa/empresa; regra de dias úteis; fichas S1–S4 e testes de precisão, granularidade, filtros, desempenho e erros; páginas/resultados de instrumento e qualidade caso o escopo final inclua C03, C04 e qualidade. O planejamento de quatro telas está em [`solucao-dashboards/`](solucao-dashboards/); o estado implementado está descrito neste documento.
