# Camada de apresentação Power BI

O frontend aplicável ao G05 é o relatório Power BI. Não há aplicação React/Vue nem servidor web desta camada. Os arquivos PBIP, PBIR e TMDL permitem versionar a apresentação e o modelo semântico; o Desktop em Windows executa a importação, as medidas e os visuais.

## Projetos e estado da integração

| Caminho | Papel |
| :--- | :--- |
| [`CentralPesquisasBI.pbip`](CentralPesquisasBI.pbip) | Entrada do projeto de consumo analítico. |
| [`CentralPesquisasBI.Report/`](CentralPesquisasBI.Report/) | Definição de relatório; `definition.pbir` aponta para o modelo semântico irmão. Migração de páginas e adaptação de vínculos são entregas BI-01/RP-13/RP-14. |
| [`CentralPesquisasBI.SemanticModel/`](CentralPesquisasBI.SemanticModel/) | Modelo TMDL com tabelas, relações, hierarquias, medidas e parâmetro de publicação. |
| [`../src/pbir dash/`](../src/pbir%20dash/) | Relatório legado de duas páginas (Produção e Volume e Benchmark), com fonte simulada própria. Não usá-lo como evidência de conexão ao DW. |

A existência das definições do modelo ou do vínculo em `definition.pbir` não comprova que cada visual foi migrado, que o projeto abriu ou que o refresh terminou no Desktop. Consulte a [validação de acesso](../docs/validacao-acesso-bi.md) e a MR da versão avaliada para as capturas e os resultados de BI-02/BI-05/BI-06.

## Conexão e tabelas

O parâmetro `PastaPublicacaoBI`, em [`definition/expressions.tmdl`](CentralPesquisasBI.SemanticModel/definition/expressions.tmdl), identifica uma geração autorizada. Ela contém `manifest.json` e sete Parquet: quatro cubos (`PUB_C01_CICLO`, `PUB_C02_PARTICIPACAO`, `PUB_C03_PIPELINE_MENSAL`, `PUB_C04_INSTRUMENTO`) e três tabelas de qualidade (`PUB_QUALIDADE_CAMPO`, `PUB_QUALIDADE_RELACAO`, `PUB_QUALIDADE_DUPLICIDADE`).

Sete arquivos de entrada não significam sete tabelas no modelo. As dimensões de área, tipo de pesquisa, tipo de pergunta, status e tempo são derivadas no Power Query; `DIM_INDICADORES_BLOQUEADOS` registra indisponibilidades. Confira [`definition/model.tmdl`](CentralPesquisasBI.SemanticModel/definition/model.tmdl) para a lista efetiva de tabelas.

1. Obtenha a geração por canal autorizado, fora do Git. Confira o manifesto e os hashes, não apenas o nome da pasta.
2. Em Windows, abra `CentralPesquisasBI.pbip` no Power BI Desktop compatível com os formatos do projeto. Registre a versão usada.
3. Ajuste `PastaPublicacaoBI` para a pasta da geração; preserve a separação entre definição e dados locais. Não versione seu caminho privado ou credenciais.
4. Atualize e registre erros de consulta, linhas importadas e a geração usada. Compare as contagens e agregados com o manifesto e as consultas DuckDB da mesma geração.
5. Confira relações, medidas, filtros e estados indisponíveis. Não transforme nulo em zero ou soma de estoques entre meses.
6. Registre captura sem identificadores pessoais, versão, data e comportamento ao trocar de geração na documentação de validação. Falha impeditiva exige correção antes do aceite.

## Limites do contrato

C01 publicado não oferece pesquisa individual/complexidade e C02 não oferece empresa identificável. Os detalhes por pesquisa e a comparação por empresa do legado exigem redesenho para consumir os agregados. A dimensão tempo aplica-se às publicações que têm período; não invente data de solicitação em C01. C03 só tem estoque quando há fechamento observado.

Arquivo PBIX, cache `.pbi`, fontes reais, banco e Parquet não devem entrar no Git. Capturas precisam de revisão de conteúdo; nomes de pasta ou dados aparentemente agregados não garantem anonimização.

## Fontes

- [Portal documental](../docs/index.md) e [solução dos dashboards](../docs/solucao_dashboard.md).
- [Decisão de consumo](../docs/decisao-consumo-cubos.md), [relações](../docs/relacionamentos-modelo-bi.md), [hierarquias](../docs/hierarquias-modelo-bi.md) e [medidas](../docs/especificacao-medidas-bi.md).
- [Documentação oficial Microsoft e demais referências](../docs/referencias.md).
