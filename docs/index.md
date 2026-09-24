# Índice da documentação

## Produto e entregáveis

| Artefato | Papel |
| :--- | :--- |
| [`projeto.md`](projeto.md) | Documento canônico: contexto, arquitetura, modelagem dimensional, requisitos, governança e avaliação |
| [`Governança-de-Dados-do-Projeto.md`](Governança-de-Dados-do-Projeto.md) | Artefato da Sprint 2: estrutura organizacional, qualidade, metadados, classificação, segurança, ciclo de vida e maturidade |
| [`contexto_organizacional_+_requisitos_da_solução_analítica.md`](contexto_organizacional_+_requisitos_da_solução_analítica.md) | Entrada formal do Entregável A, apontando para as seções canônicas |
| [`arquitetura-de-negocio.md`](arquitetura-de-negocio.md) | Cópia local da Arquitetura de Negócio usada como fonte primária de contexto |
| [`dmc.json`](dmc.json) | Exportação do Data Model Canvas para importação na ferramenta oficial |
| [`dmc.md`](dmc.md) | Versão legível e autocontida do Data Model Canvas |
| [`revisao-final-dmc.md`](revisao-final-dmc.md) | Parecer final de completude, consistência, rastreabilidade e validação do DMC 1.1 |
| [`fontes-e-dependencias.md`](fontes-e-dependencias.md) | Mapa de fontes, limitações e dependências entre os três entregáveis da Sprint 1 |
| [`contrato-lote-extraido.md`](contrato-lote-extraido.md) | Interface comum dos extratores, contrato de lote, checkpoint e metadados |
| [`configuracao-extracao.md`](configuracao-extracao.md) | Configuração segura de caminhos, endpoints e credenciais da extração |
| [`adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md`](adrs/0001-arquitetura-etl-python-prefect-minio-duckdb.md) | ADR proposto para o ETL orientado a eventos com Python, Prefect, MinIO, DuckDB e Elastic Stack |
| [`adrs/0002-identidade-e-versoes-na-tabela-de-ingestao.md`](adrs/0002-identidade-e-versoes-na-tabela-de-ingestao.md) | ADR da identidade de registro e das versões na tabela de ingestão tratada |
| [`adrs/0004-execucao-local-e-integracao-continua.md`](adrs/0004-execucao-local-e-integracao-continua.md) | ADR do ambiente local em contêineres, do escopo do CI e da exclusão do Deploy Contínuo |
| [`extratores.md`](extratores.md) | Implementação e limites dos extratores das seis fontes; pesquisas e empresas entregues na LN-04 |
| [`testes-extracao.md`](testes-extracao.md) | Suíte unitária e de contrato dos seis extratores |
| [`inventario-fontes-etl.md`](inventario-fontes-etl.md) | Inventário técnico das seis fontes do ETL: formato, grão, chaves, volumes, integridade, acesso e disponibilidade |
| [`matriz-evidencias-problem-canvas.md`](matriz-evidencias-problem-canvas.md) | Relação entre dores, causas, impactos, necessidades, objetivos, KPIs, públicos, governança e riscos |

O conteúdo essencial permanece em `projeto.md`. O documento de governança é o
artefato específico da Sprint 2 e detalha suas políticas sem transformar
propostas em controles já implantados. Os demais arquivos auxiliares existem
para tornar matrizes extensas auditáveis e reutilizáveis, não para substituir o
documento principal.

## Transformação essencial — Sprint 3 (Marlos)

- [Inventário de regras](inventario-regras-transformacao.md): fontes, riscos e escopo MG-01.
- [Schema canônico](schema-transformacao.md) e [catálogo de campos](catalogo-transformacao.md): contrato de destino MG-02.
- [Integração da transformação](integracao-transformacao.md): chamada, referências, quarentena e confirmação pela carga.
- [Matriz regra–teste](matriz-transformacao.md): evidências, comandos e limitações MG-01 a MG-11.

## Carga e ingestão — Sprint 3 (Lucas)

- [Inventário de contratos dimensionais](inventario-contratos-dimensionais.md): contratos de fato, dimensão e cubo já existentes (Data Model Canvas) que restringem nomes, tipos e metadados da tabela de ingestão.
- [Ambiente local do DuckDB](ambiente-duckdb.md): comando que cria o arquivo do banco de ingestão, configuração aceita e health check de consulta e persistência.
- [Contrato físico das tabelas de ingestão](ddl-ingestao.md): nome, tipo, constraints, metadados técnicos e views de estado atual no DuckDB.
- [Repositório de carga](repositorio-de-carga.md): escrita em lote no DuckDB, contagens confirmadas pelo banco, serialização de escrita e convergência do lote reexecutado.
- [Compensação e retomada de execuções com falha parcial](compensacao-e-retomada-de-carga.md): o que uma falha entre lotes deixa registrado e a partir de que ponto a tentativa seguinte retoma.
- [Runbook de execução do ETL](runbook-execucao.md): pré-requisitos, variáveis de ambiente, ambiente Docker, execução do pipeline, testes, CI e troubleshooting.

## Camada analítica — Sprint 4

- [Decisão de consumo dos cubos no BI](decisao-consumo-cubos.md): comparação dos caminhos de acesso, escolha dos agregados Parquet e requisitos por máquina.

## Modelo semântico e medidas — Sprint 4 (Anna)

- [Indicadores publicáveis, bloqueados e motivo](indicadores-publicaveis-bi.md): reclassifica o catálogo I01–I25 de `dmc.md` contra o que realmente chega ao Power BI (DX-01).
- [Especificação das medidas](especificacao-medidas-bi.md): numerador, denominador, grão e tratamento de nulo e duplicata de cada medida (DX-02).
- [Regras estatísticas obrigatórias](regras-estatisticas-medidas.md): mediana vs. média, filtro de denominador, tamanho da base e proibição de contar linha como respondente (DX-03).
- [Validação de acesso ponta a ponta ao BI](validacao-acesso-bi.md): checklist de conexão em máquina nova e gap-check indicador × coluna publicada (DX-04).
- [Relacionamentos do modelo semântico](relacionamentos-modelo-bi.md): dimensões conformadas, cardinalidade e direção de filtro do projeto `powerbi/CentralPesquisasBI` (DX-05).
- [Hierarquias do modelo semântico](hierarquias-modelo-bi.md): hierarquia de tempo (Ano-Trimestre-Mês) e de área, tipo e perfil, e como conferir o total por nível (DX-06).
- [Medidas de portfólio, ciclo e prorrogação](medidas-portfolio-ciclo.md): medidas de `PUB_C01_CICLO`, regra aplicada e conferência contra a apuração de referência (DX-07).

## Arquitetura, decisões e UML — Sprint 3 (Anna)

- [Checklist dos entregáveis](checklist-entregaveis-sprint3.md): obrigações, exclusões e critérios de avaliação do enunciado (AN-01).
- [Matriz de rastreabilidade](matriz-rastreabilidade-sprint3.md): cada requisito ligado a tarefa, evidência e estado observado no repositório (AN-02).
- [Índice das ADRs](adrs/index.md): status verbatim das três decisões e o que falta para cada uma ser aceita (AN-03).
- Visões ISO/IEC 10746: [negócio](visao-negocio-etl.md) (AN-04), [informação](visao-informacao-etl.md) (AN-05), [computacional](visao-computacional-etl.md) (AN-06), [engenharia](visao-engenharia-etl.md) (AN-07) e [tecnologia](visao-tecnologia-etl.md) (AN-08).
- Diagramas UML em [`assets/uml/`](assets/uml/): [casos de uso](assets/uml/casos-de-uso-etl.plantuml) (AN-09), [componentes](assets/uml/componentes-etl.plantuml) (AN-10) e [sequência da ingestão](assets/uml/sequencia-ingestao-etl.plantuml) (AN-11).

As visões descrevem o estado observado no repositório. Capacidade decidida e
ainda não integrada — observabilidade, adaptador de eventos e consolidação do
CI — aparece marcada como planejada, nunca como implementada.

## Evidências e protótipos

| Diretório | Conteúdo |
| :--- | :--- |
| [`assets/prototipos-dashboards/`](assets/prototipos-dashboards/) | interface autocontida, agregado sem identificação, testes e capturas dos dashboards D01–D04 |
| [`../scripts/data_quality/`](../scripts/data_quality/) | manifesto, perfilador, testes e contrato das saídas agregadas |
| [`../scripts/governance/`](../scripts/governance/) | validação reproduzível da classificação, do TAPI e da matriz de acesso |
| [`../scripts/traceability/`](../scripts/traceability/) | contrato executável PB–RF–indicador–cubo/dashboard e validação das extensões futuras de resposta conciliada |
| [`smoke-test-extracao.md`](smoke-test-extracao.md) | Resultado reproduzível da extração das seis fontes com fixtures sintéticas |

## Documentos de gestão

- [`gestao-configuração.md`](gestao-configuração.md): política de branches, commits, dados sensíveis e configuração.
- [`gestao-projeto.md`](gestao-projeto.md): acompanhamento e avaliação das sprints.
- [`dev-rules.md`](dev-rules.md): regras gerais de desenvolvimento.

Esses documentos registram práticas internas do projeto e não são fonte
primária de requisitos do parceiro.

## Bases e insumos locais

Os seis CSVs usados na análise ficam fora do Git. A raiz pode conter cópias
locais ignoradas, mas elas não devem ser movidas para `docs/` nem forçadas para
versionamento. O perfilador recebe o diretório por argumento, gera somente
agregados e não modifica a origem.

```bash
python3 scripts/data_quality/profile_csv.py \
  --input-dir /caminho/seguro/das-fontes \
  --output-dir /tmp/perfil-g05 \
  --dictionary "/caminho/seguro/dicionario.csv"
```

O dicionário e as fontes são obrigatórios para uma reprodução integral. Na
ausência deles, uma referência documental não deve ser apresentada como teste
executado.

## Checks

```bash
jq empty docs/dmc.json
python3 scripts/dmc/validate_dmc.py docs/dmc.json
python3 -m unittest discover -s scripts/dmc -p 'test_*.py'
python3 -m unittest discover -s scripts/data_quality -p 'test_*.py'
python3 -m unittest discover -s scripts/governance -p 'test_*.py'
python3 scripts/traceability/validate_traceability.py
python3 -m unittest discover -s scripts/traceability -p 'test_*.py'
git diff --check
```

A validação completa de governança também confere o TAPI externo sem exibir seu
conteúdo:

```bash
python3 scripts/governance/validate_governance.py \
  --document docs/Governança-de-Dados-do-Projeto.md \
  --tapi /caminho/seguro/Tapi-sinduspharma.txt \
  --repository-root .
```

Para conferir também a identidade e os trechos usados das duas fontes
primárias externas, execute:

```bash
python3 scripts/traceability/validate_traceability.py \
  --sources-dir /caminho/seguro/das-fontes
```

Os protótipos possuem instruções próprias em
[`assets/prototipos-dashboards/README.md`](assets/prototipos-dashboards/README.md).
A suíte de integração depende dos seis CSVs externos e deve receber o diretório
por `SINDUSFARMA_CSV_DIR`; ausência das fontes produz `skip`, não aprovação do
gate completo.
