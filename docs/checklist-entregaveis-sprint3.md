# Checklist dos entregáveis da Sprint 3 (AN-01)

Checklist do enunciado da Sprint 3, separando o que é **obrigação**, o que é
**exclusão explícita** e o que é **critério de avaliação**. O documento não
acrescenta escopo: ele apenas organiza o que já foi pedido, para que a matriz de
rastreabilidade ([`matriz-rastreabilidade-sprint3.md`](matriz-rastreabilidade-sprint3.md))
possa apontar cada obrigação para uma tarefa e uma evidência.

A Sprint 3 tem dois entregáveis avaliados de forma independente: o **pipeline
ETL** e o **Data Model Canvas**. Onde o enunciado cita ClickHouse como destino,
o alvo desta entrega é o **DuckDB**, conforme a autorização registrada no
[ADR 0001](adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md).

## Entregável 1 — Pipeline ETL

### Obrigatório

| Item | O que o enunciado exige |
| :--- | :--- |
| Extração | Ler as fontes definidas para o projeto |
| Transformações essenciais | Tratar os dados durante a coleta, antes da persistência |
| Validação e tratamento | Validar e tratar os dados antes da carga |
| Carga na tabela de ingestão | Persistir o resultado na tabela de ingestão, que não pode ser uma cópia bruta das fontes |
| Orquestração | Coordenar os pipelines com dependências, agendamento e execução manual |
| Integração Contínua | Manter um pipeline de CI para o repositório |
| Observabilidade | Expor logs, métricas e acompanhamento da execução |
| Testes automatizados | Cobrir o comportamento do pipeline com testes |
| Documentação arquitetural | Produzir as visões da ISO/IEC 10746 |
| Diagramas UML | Entregar casos de uso, componentes e sequência |
| Boas práticas de engenharia | Modularidade, separação de responsabilidades e legibilidade |

### Fora de escopo

| Item | Observação |
| :--- | :--- |
| Enriquecimentos analíticos | Não fazem parte da entrega da tabela de ingestão |
| Consolidações de negócio | Pertencem à camada dimensional, não à ingestão |
| Cruzamentos avançados entre fontes | Somente a integridade referencial técnica é exigida |
| Indicadores e métricas analíticas | Permanecem no Data Model Canvas, não no pipeline |
| Agregações | Não devem ser calculadas nesta entrega |
| Estruturas de consumo analítico final | Cubos, dashboards e views de consumo ficam para depois |
| Deploy Contínuo (CD) | Excluído explicitamente; o enunciado pede apenas CI |

### Evidências esperadas (critérios de avaliação)

| Critério | O que é avaliado |
| :--- | :--- |
| Arquitetura e modularidade | Separação de responsabilidades e baixo acoplamento entre as camadas |
| Qualidade do ETL | Robustez do fluxo de extração, transformação e carga |
| Transformação | Tratamento efetivo dos dados antes da persistência |
| Ingestão | Tabela de ingestão tratada, com metadados técnicos e não apenas cópia da origem |
| Observabilidade | Logs, métricas e visibilidade da execução |
| Orquestração | Dependências declaradas, agendamento, execução manual e histórico |
| Integração Contínua | Pipeline de CI executando verificações automáticas |
| Testes | Cobertura automatizada das regras e dos contratos |
| Documentação | Visões da ISO/IEC 10746 e diagramas UML atualizados |
| Decisões técnicas | Justificativa de linguagem, arquitetura, frameworks e ferramentas |

## Entregável 2 — Data Model Canvas

### Obrigatório

| Item | O que o enunciado exige |
| :--- | :--- |
| Preenchimento | Completar o Data Model Canvas na ferramenta oficial |
| Exportação | Exportar o arquivo `dmc.json` |
| Versionamento | Salvar em [`dmc.json`](dmc.json) com todas as seções preenchidas |

### Evidências esperadas (critérios de avaliação)

| Critério | O que é avaliado |
| :--- | :--- |
| Coerência | Aderência ao documento de contexto e aos requisitos |
| Negócio e consumo analítico | Qualidade das seções de negócio, consumo e governança corporativa |
| Modelagem dimensional | Consistência da modelagem por cubo |
| Grão, fatos, métricas e dimensões | Adequação e clareza de cada elemento declarado |
| Correspondência cubo–requisito | Ligação entre cada cubo e o requisito funcional que ele atende |
| Organização do JSON | Completude e organização do arquivo exportado |

## Fronteira entre os dois entregáveis

O pipeline termina na tabela de ingestão tratada do DuckDB. Os cubos, fatos,
dimensões e indicadores descritos no Data Model Canvas **não** são construídos
nesta sprint: eles permanecem como contrato de destino que restringe nomes,
tipos e metadados da ingestão, conforme
[`inventario-contratos-dimensionais.md`](inventario-contratos-dimensionais.md).
Nenhuma visão de arquitetura ou diagrama desta entrega deve descrever
agregação, indicador ou estrutura de consumo como parte do escopo implementado.
