# Solução de dashboard — implementação e validação

**Atualizado em 25/09/2026.** Este documento apresenta as páginas do report, o modelo semântico dos cubos publicados pela ETL e o roteiro de validação com usuários. As definições TMDL/JSON registram a configuração; os resultados das interações serão incorporados às fichas de sessão.

## 1. Cubos, fontes e alcance

| Artefato | Fonte e grão | Entrega documentada |
| :--- | :--- | :--- |
| [PBIP demonstrativo](../src/pbir%20dash/dashboard.Report/) e [modelo](../src/pbir%20dash/dashboard.SemanticModel/) | CSVs locais `vw_ciclo_pesquisa.csv` (pesquisa) e `vw_participacao.csv` (ocorrência) | Páginas **Produção e Volume** e **Benchmark Externo — V2**, com medidas e visuais versionados para a demonstração. |
| [Modelo de consumo](../powerbi/CentralPesquisasBI.SemanticModel/) | Sete Parquet de uma geração: C01–C04 agregados e três tabelas de qualidade | Importações, medidas e relacionamentos definidos em TMDL para o consumo analítico. |

Os cubos físicos C01 (portfólio e ciclo), C02 (participação), C03 (snapshot mensal do pipeline) e C04 (instrumento) alimentam o [publicador](../src/etl/analytics/publish.py). Os Parquet `PUB_C01_CICLO`, `PUB_C02_PARTICIPACAO`, `PUB_C03_PIPELINE_MENSAL` e `PUB_C04_INSTRUMENTO` são recortes **agregados** dos fatos. O pacote inclui também `PUB_QUALIDADE_CAMPO`, `PUB_QUALIDADE_RELACAO` e `PUB_QUALIDADE_DUPLICIDADE`; ver [acesso](acesso-cubos-bi.md) e [indicadores publicáveis](indicadores-publicaveis-bi.md). Para levar a tabela por pesquisa e o benchmark individual à publicação, a próxima etapa é definir o grão e as regras de privacidade correspondentes.

### Visuais das duas páginas demonstrativas

| Página/visual | Medida ou campo | Dimensão/filtro e ressalva |
| :--- | :--- | :--- |
| Produção: cartões de pesquisas, finalizadas e em aberto | `D01_CicloPesquisa[Pesquisas]` (`DISTINCTCOUNT` de pesquisa), `Pesquisas Finalizadas`, `Pesquisas em Aberto` | Segmentadores `ano_edicao`, `area`, `tipo`, `status`, `complexidade` da própria D01. `ano_edicao` não é hierarquia de `data_solicitacao`. |
| Produção: taxa de finalização | `Taxa de Finalização` = finalizadas / pesquisas com `DIVIDE` | Mesmo contexto D01; denominador zero gera vazio. Não é taxa de adesão. |
| Produção: ciclo e etapas por tipo | Médias de `dias_ciclo_total_corridos`, `dias_validacao_corridos`, `dias_coleta_corridos`, `dias_tabulacao_corridos` | Tipo e demais segmentadores D01. **As medidas atuais são em dias corridos.** A solicitação de dias úteis está registrada para evolução; `AVERAGE` ignora nulos. |
| Produção: volume por área/status | `Pesquisas` | `area` ou `status` da D01. |
| Produção: prorrogações e tabelas | `Pesquisas Prorrogadas`; `flag_prorrogada`, título, área, tipo, status, duração, entrega | Filtro visual de `flag_prorrogada` na tabela de prorrogações. Detalhe por pesquisa só no CSV demonstrativo. |
| Benchmark: cartões | `BE Pesquisas da empresa`, `BE Empresas observadas`, `BE Pesquisas no recorte` | `BE_Empresa[Empresa]`, `BE_Pesquisa[Pesquisa/Ano/Área/Tipo]`. Ano deriva de `data_divulgacao`, diferente do ano de edição da Produção. |
| Benchmark: perfil por área e evolução anual | `BE % empresa por área`, `BE % demais por área`, `BE Pesquisas por ano`, `BE Média demais por ano` | Área, ano e empresa. Perfil por área é fração das pesquisas observadas da empresa distribuída entre áreas; não é taxa de adesão por área. Evolução usa contagens e média dos demais. |
| Benchmark: faixa e detalhe | `BE Empresas por faixa`, `BE Selecionada por faixa`, `BE Percentual observado`, `BE Empresa participou`, `BE % observado Top 8` | Faixa, pesquisa e empresa. Percentual usa o conjunto de empresas registrado, sem universo de convidadas; não é participação de mercado. |

Os JSON dos [visuais de Produção](../src/pbir%20dash/dashboard.Report/definition/pages/5d499bb7bb62646ad6e5/visuals/) e [Benchmark](../src/pbir%20dash/dashboard.Report/definition/pages/e18bd740de609936581b/visuals/) e as medidas [D01](../src/pbir%20dash/dashboard.SemanticModel/definition/tables/D01_CicloPesquisa.tmdl) e [BE](../src/pbir%20dash/dashboard.SemanticModel/definition/tables/BE_Empresa.tmdl) sustentam esse mapeamento das duas páginas apresentadas.

### Relacionamentos, segmentações e hierarquias

No report de demonstração, D01 e D02 são importações independentes. `BE_Pesquisa` deriva da D01; medidas de benchmark aplicam IDs de pesquisa e empresa à D02 com `TREATAS`. `BE_Faixa` fornece limites às medidas. `KEEPFILTERS`, `REMOVEFILTERS`, `ALLSELECTED` e `HASONEVALUE` controlam o contexto. A sincronização entre páginas será conferida durante os testes de interação.

No modelo Parquet, `DIM_AREA` filtra C01–C04; `DIM_TIPO_PESQUISA`, C01–C03; `DIM_STATUS_PESQUISA`, C01/C03; `DIM_TIPO_PERGUNTA`, C04; e `DIM_TEMPO`, o mês da resposta de C02 e o fechamento de C03. Os [relacionamentos TMDL](../powerbi/CentralPesquisasBI.SemanticModel/definition/relationships.tmdl) são muitos-para-um, com direção única da dimensão ao fato. A hierarquia de calendário atende os fatos com vínculo temporal e pode ser ampliada ao C01 quando o contrato de publicação incluir o marco de solicitação. O filtro `area` representa área de negócio. A navegação por drill-down e drill-through integra o roteiro de evolução e validação. C03 usa o último snapshot do período, preservando a semântica de estoque mensal.

No modelo publicado, a média correta é `DIVIDE(SUM(soma_dias_*), SUM(qtd_*_disponivel))`, como no [TMDL de C01](../powerbi/CentralPesquisasBI.SemanticModel/definition/tables/PUB_C01_CICLO.tmdl). Médias e taxas de grupos não são somadas; reconciliam-se seus componentes. Só contagens de grupos disjuntos no mesmo grão são diretamente aditivas.

## 2. Plano de tarefas de usabilidade

O [roteiro moderado](usabilidade/roteiro-execucao.md) define quatro perfis exercidos, ordem, cronômetro, conclusão, desvios, erros e debrief. Os 15 cenários se dividem entre [navegação/filtros](usabilidade/tarefas-navegacao-filtros.md), [detalhamento](usabilidade/tarefas-detalhamento.md) e [comparação/segmentação](usabilidade/tarefas-comparacao-segmentacao.md).

| Bloco | Interação e critério observável | Condição no alvo atual |
| :--- | :--- | :--- |
| T-NAV/T-FIL | Abrir página, aplicar ano/área/tipo/status, combinar cortes, limpar filtro e distinguir vazio de erro; conferir cartões, gráficos e tabela no mesmo recorte | Anunciar que Produção usa ano de edição e Benchmark usa ano de divulgação. |
| T-DET | Sair do agregado e localizar a pesquisa na tabela; explicar o valor | As tabelas das duas páginas permitem avaliar a leitura do detalhe; o roteiro inclui a evolução para drill-down temporal e drill-through entre páginas. |
| T-CMP | Comparar períodos equivalentes e explicar medida temporal | A comparação por `data_solicitacao` será aplicada quando esse marco integrar a publicação; médias serão recalculadas com bases válidas. |
| T-SEG | Aplicar dois ou três filtros e cruzar leitura entre cartões, gráficos e tabela | Registrar filtros, valor exibido, referência no mesmo recorte e tempo de resposta. Cruzamento **entre páginas** exige evidência própria. |

Os roteiros abrangem a evolução prevista de D01–D04. Antes de cada sessão, o moderador identifica a versão do report e seleciona as tarefas correspondentes aos recursos disponíveis. As páginas de demonstração permitem avaliar a leitura da interface; a conferência dos cubos publicados usará páginas ligadas à mesma geração Parquet, o manifesto e consultas ao DuckDB no mesmo recorte.

## 3. Execução e resultados

**Rodada 0, 25/09/2026:** as [fichas de navegação](usabilidade/execucao-navegacao-detalhamento.md) e [comparação](usabilidade/execucao-comparacao-segmentacao.md) registram a demonstração ao parceiro com dados de exemplo. O parceiro elogiou a expansão das tabelas e a leitura por tipo e sugeriu apresentar o ciclo em **dias úteis** e dar maior destaque à duração média. Esses achados orientam a evolução dos reports e as sessões moderadas.

**Sessões S1–S4:** o roteiro e as fichas estão preparados para registrar conclusão, valores versus referência, filtros, estabilidade, latência e navegação no Power BI Desktop. As sessões constam como **próxima etapa de validação**. O [diretório de evidências](usabilidade/evidencias/) receberá capturas identificadas por sessão e recorte.

Para cada tarefa executada, registrar ID e conclusão (sim/com assistência/não), tempo, filtros e marco temporal, valor exibido, referência, reconciliação por grão, resposta dos visuais, erro/lentidão e captura. Para média ou taxa, comparar numerador e denominador, não a soma das médias ou taxas detalhadas. Falhas recebem impacto, causa sustentada por evidência e proposta no [registro de limitações](usabilidade/limitacoes-e-propostas.md).

## 4. Avaliação técnica, visual e pendências

| Critério | Evidência atual | Estado |
| :--- | :--- | :--- |
| Cubos, dimensões e medidas | Medidas DAX nas páginas e modelo de consumo dos cubos publicado em TMDL | **Implementado nos respectivos modelos**; integração das páginas é a próxima etapa |
| Plano de usabilidade | Roteiro, perfis, 15 cenários e fichas | **Preparado para execução** |
| Precisão e validação funcional | Demonstração ao parceiro e roteiro de conferência por recorte | **Sessões moderadas e conciliação previstas no plano** |
| Clareza visual e interação | Duas páginas e [capturas](assets/dashboard/); retorno positivo sobre tabelas e leitura por tipo | **Apresentado ao parceiro**; critérios de acessibilidade integram o roteiro |
| Arquitetura analítica | Modelo Parquet com dimensões conformadas e report de demonstração | **Contratos e modelos definidos**; integração visual é a próxima etapa |

**Próximas etapas:** conectar páginas finais à mesma geração Parquet e adaptar os visuais ao grão publicado, ou aprovar publicação detalhada com os controles de privacidade correspondentes; definir calendário de dias úteis e feriados; ampliar a navegação temporal e por detalhe; executar S1–S4, conferir valores e verificar a interação no Power BI Desktop.

**Evidências a registrar na próxima rodada:** geração Parquet e manifesto usados pelas páginas; regra de divulgação por pesquisa/empresa; convenção de dias úteis; fichas S1–S4 com precisão, granularidade, filtros, desempenho e erros; resultados das telas de instrumento e qualidade conforme o escopo de D03–D04. O planejamento das quatro telas está em [`solucao-dashboards/`](solucao-dashboards/).
