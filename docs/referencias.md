# Referências técnicas e normativas

Estas são fontes externas usadas para explicar as tecnologias e os limites do projeto. Não substituem os contratos versionados ou a execução na versão avaliada. A bibliografia do parceiro e da governança está no [documento principal, seção 7](projeto.md#7-referências).

| Fonte primária | Uso no G05 |
| :--- | :--- |
| Python Software Foundation. [Documentação Python 3.12](https://docs.python.org/3.12/), [venv](https://docs.python.org/3.12/library/venv.html) e [unittest](https://docs.python.org/3.12/library/unittest.html) | Ambiente de referência, instalação isolada e suíte em `tests/`. |
| DuckDB Foundation. [Cliente Python](https://duckdb.org/docs/stable/clients/python/overview.html), [concorrência](https://duckdb.org/docs/stable/connect/concurrency.html) e [Parquet](https://duckdb.org/docs/stable/data/parquet/overview.html) | Banco embutido, limites entre processos e publicação analítica. A documentação `stable` pode acompanhar versão posterior à versão fixada no projeto. |
| Prefect. [Flows](https://docs.prefect.io/v3/concepts/flows) e [tasks](https://docs.prefect.io/v3/concepts/tasks) | Estados de execução e fronteiras da orquestração. O encadeamento efetivo deve ser confirmado no código. |
| Docker. [Compose](https://docs.docker.com/compose/) | Serviços locais, volumes e configuração; não atesta segurança produtiva dos exemplos. |
| Microsoft. [Projetos Power BI Desktop (PBIP)](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview), [PBIR](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report) e [TMDL](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview) | Formatos versionados do relatório e do modelo semântico. Recursos em preview exigem conferência na versão do Desktop usada. |
| Microsoft. [Conector Parquet](https://learn.microsoft.com/en-us/power-query/connectors/parquet) | Consumo de agregados publicados e configuração do caminho local. |
| Brasil. [Lei nº 13.709/2018 (LGPD), texto oficial](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm) | Proteção de dados pessoais; rótulo “agregado” não equivale automaticamente a anonimização. |
| Creative Commons. [CC BY 4.0, texto jurídico](https://creativecommons.org/licenses/by/4.0/legalcode.pt) | Atribuição da documentação e do código licenciado; não autoriza redistribuir bases pessoais do parceiro. |

## Dependências e acesso

As versões executadas são as de `requirements.txt`, `requirements-transformation-dev.txt` e `Dockerfile`. Consultar uma documentação externa não comprova que um comando funciona neste projeto. Capturas e evidências de execução têm seus próprios metadados nos documentos de validação.

Não há repositório auxiliar obrigatório declarado na configuração de execução do G05. O GitLab do grupo pode exigir autenticação institucional; fontes privadas do parceiro dependem de autorização. Links de documentação pública e perfis pessoais podem mudar ou restringir acesso, portanto esta lista não declara disponibilidade permanente.
