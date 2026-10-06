# Nome do Projeto: Governança e Integração de Dados da Central de Pesquisas

## Nome do Grupo: Synapse

## Integrantes:

- <a href="https://www.linkedin.com/in/anna-riciopo/">Anna Riciopo</a>
- <a href="https://www.linkedin.com/in/karine-paixao/">Karine Paixão</a>
- <a href="https://www.linkedin.com/in/lucas-nunes-matheus/">Lucas Nunes Matheus</a>
- <a href="https://www.linkedin.com/in/marlos-do-carmo-guedes-366987250/">Marlos Guedes</a>
- <a href="https://www.linkedin.com/in/milena-castro-vieira/">Milena Castro Vieira</a>
- <a href="https://www.linkedin.com/in/otavio-vasc/">Otávio Vasconcelos</a>
- <a href="https://www.linkedin.com/in/vitor-balbo/">Vitor Balbo</a>

## Professores:

- <a href="https://www.linkedin.com/in/afonsolelis/">Afonso Lelis</a> — Programação
- <a href="https://www.linkedin.com/in/hermano-peixoto-1091796/">Hermano Peixoto</a> — Programação
- <a href="https://www.linkedin.com/in/reginaldo-arakaki-9574222b/">Reginaldo Arakaki</a> — Programação
- <a href="https://www.linkedin.com/in/bruno-grandchamp-rodilha/">Bruno Grandchamp Rodilha</a> — Design
- <a href="https://www.linkedin.com/in/filipe-gon%C3%A7alves-08a55015b/">Filipe Gonçalves</a> — Liderança
- <a href="https://www.linkedin.com/in/diogo-martins-gon%C3%A7alves-de-morais-96404732/">Diogo Martins Gonçalves de Morais</a> — Negócios
- <a href="https://www.linkedin.com/in/geraldo-magela-severino-vasconcelos-22b1b220/">Geraldo Magela Severino Vasconcelos</a> — Matemática

## Descrição

O projeto integra as fontes da Central de Pesquisas do Sindusfarma em um ETL Python com ingestão tratada no DuckDB, camada analítica e consumo no Power BI. As regras de qualidade, rastreabilidade e governança acompanham a carga. O ambiente entregue é local, com serviços em Docker Compose e banco embutido em arquivo. Implantação em nuvem, publicação no Power BI Service e operação produtiva exigem provisionamento e aceite próprios.

## Documentação

Comece pelo [portal da documentação](docs/index.md). Ele liga o [documento principal](docs/projeto.md), as [decisões arquiteturais](docs/adrs/index.md), o [runbook de execução](docs/runbook-execucao.md) e os contratos por etapa.

- [Matriz do feedback de conformidade](docs/conformidade-geral.md): evidência, correção e limite de cada critério.
- [Referências técnicas e normativas](docs/referencias.md): fontes externas e sua aplicação no projeto.

## Dashboards

A camada de apresentação usa Power BI (PBIP, PBIR e TMDL). `src/pbir dash/` contém o relatório legado de duas páginas; `powerbi/` contém o projeto de consumo dos agregados Parquet. A migração das páginas e a validação Desktop têm entregas próprias. A existência de um modelo semântico não comprova que todos os visuais já o consomem. O catálogo de dashboards prevê:

- **Dashboard Operacional**: status das pesquisas em andamento, adesão por empresa e área, e tempos do ciclo (validação, coleta, tabulação).
- **Dashboard Estratégico**: volume de pesquisas por período, evolução da adesão e representatividade de mercado das participantes.

## Estrutura de pastas

```
g05/
├─ docs/
│  ├─ index.md                                        # Índice da documentação
│  ├─ projeto.md                                      # Documento principal do produto
│  ├─ contexto_organizacional_+_requisitos_da_solução_analítica.md
│  │                                                   # Entrada formal do Entregável A
│  ├─ arquitetura-de-negocio.md                       # Fonte primária local de contexto
│  ├─ modelagem_quantitativa_de_dados_do_parceiro.md  # Modelagem quantitativa das bases
│  ├─ fontes-e-dependencias.md                        # Origem e limitações dos entregáveis
│  ├─ matriz-evidencias-problem-canvas.md             # Evidências (observação / inferência / proposta)
│  ├─ dmc.json                                        # Data Model Canvas exportado
│  ├─ runbook-execucao.md                             # Runbook: subir ambiente, executar ETL, testes e troubleshooting
│  ├─ estrategia-de-testes.md                         # Estratégia de testes do ETL (baseline e camadas)
│  ├─ solucao-dashboards/                             # Documentação dos dashboards
│  ├─ usabilidade/                                    # Plano e avaliação de usabilidade
│  ├─ adrs/                                           # Decisões de arquitetura do ETL
│  ├─ gestao-projeto.md                               # Sprints, riscos e post-mortem
│  ├─ gestao-configuração.md                          # Políticas de repo, branches e commits
│  ├─ dev-rules.md                                    # Padrões de código e testes
│  └─ assets/                                         # Protótipos, diagramas e figuras dos documentos
│     ├─ figuras/                                     # Figuras agregadas geradas pela análise quantitativa
│     └─ uml/                                         # Diagramas UML da solução
├─ src/etl/                                           # ETL: extração, transformação, carga e orquestração
├─ src/pbir dash/                                     # Relatório e modelo semântico Power BI
├─ powerbi/                                           # Projeto Power BI da Central de Pesquisas
├─ tests/                                             # Testes do ETL e da camada analítica
├─ sql/duckdb/                                        # DDL versionada de ingestão e análise
├─ scripts/
│  ├─ analysis/                                       # Análise quantitativa e notebooks exploratórios
│  ├─ analytics/                                      # Rotinas da camada analítica
│  ├─ architecture/                                   # Validação da documentação arquitetural
│  ├─ dmc/                                            # Validação do dmc.json
│  ├─ orchestration/                                  # Entrypoints do ETL (run_ingest, run_backfill, deployment, health_check, smoke_observabilidade)
│  ├─ transformation/                                 # Auditoria e renderização do schema de transformação
│  ├─ load/                                           # Health check do DuckDB e renderização da DDL
│  ├─ prototipos-dashboards/                          # Geração, testes e renderização dos protótipos
│  ├─ data_quality/                                   # Validação da qualidade dos dados
│  ├─ governance/                                     # Validação de governança
│  └─ traceability/                                   # Validação de rastreabilidade às fontes
├─ docker-compose.yml                                 # Ambiente local: MinIO, Prefect (server + scheduler), runner e Elastic Stack
├─ prefect.yaml                                       # Deployments Prefect
├─ observability/logstash/pipeline/                   # Pipeline do coletor (GELF → Elasticsearch, OB-07)
├─ observability/kibana/                              # Saved objects do painel operacional (OB-08)
├─ observability/prefect-logging.yml                  # Perfil de logging JSON do Prefect para o coletor
├─ Dockerfile                                         # Imagem do runner do ETL
├─ requirements.txt                                   # Dependências de execução do ETL
├─ .env.example                                       # Modelo das variáveis de ambiente do ETL
├─ .gitlab/
│  └─ merge_request_templates/                        # Template de Merge Request
├─ .gitlab-ci.yml                                     # Pipeline de CI
├─ .gitignore
└─ README.md
```

Os guias de [banco/DDL](sql/duckdb/README.md), [apresentação Power BI](powerbi/README.md) e [testes e massas sintéticas](tests/README.md) explicam como navegar e verificar cada camada.

## Requisitos

O CI e o Dockerfile usam Python 3.12. Para reproduzir esse ambiente, use Python 3.12 e instale as versões fixadas nos arquivos de dependências:

- **Git**: 2.40+
- **Python**: 3.12 para o ambiente de referência; versões posteriores precisam passar pelos mesmos gates. `requirements.txt` fixa as dependências de execução e `requirements-transformation-dev.txt` fixa lint, cobertura e JUnit.
- **Docker Engine e Compose v2** (`docker compose`; ambiente local com MinIO, Prefect, runner e Elastic Stack). O Compose não representa um ambiente produtivo endurecido; imagens `latest` do MinIO e credenciais locais de exemplo exigem revisão antes de implantação.
- **matplotlib**: 3.9+ somente para os scripts exploratórios de análise quantitativa; não é dependência do ETL em `requirements.txt`.
- **jq**: 1.6+ para os comandos de validação estrutural do `dmc.json`.
- **Power BI Desktop em Windows** para abrir e atualizar o PBIP. Versão e procedimento estão em [validação de acesso ao BI](docs/validacao-acesso-bi.md); Linux executa ETL e consultas, mas não substitui a prova no Desktop.

## Configuração para desenvolvimento

```bash
git clone https://git.inteli.edu.br/graduacao/2026-2a/t13/g05
cd g05
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-transformation-dev.txt
```

> As bases reais do parceiro, bancos DuckDB e gerações Parquet ficam em diretório externo restrito e não devem entrar no Git. Os CSVs de `tests/fixtures/` são sintéticos e versionados para os testes. Excluir dados brutos não prova sozinho a ausência de dados pessoais em capturas, PDF ou caches do Power BI; revise os artefatos antes de publicá-los, conforme [gestão de configuração](docs/gestao-configuração.md).

## Execução do ETL

Verifique `python --version`, `git --version`, `docker compose version` e `jq --version` antes de seguir o runbook. `jq` é um executável do sistema; instale-o pelo gerenciador da sua plataforma. Se quiser apenas verificar a sintaxe JSON sem ele, use `python -m json.tool docs/dmc.json > /dev/null`; isso não substitui o validador de domínio.

Para gerar os gráficos da análise quantitativa, instale a dependência opcional separadamente no ambiente virtual:

```bash
python -m pip install 'matplotlib==3.9.4'
```

O pipeline de ingestão (CSVs → MinIO → Prefect → DuckDB) sobe com Docker
Compose e é executado pelos entrypoints em `scripts/orchestration/`:

```bash
docker compose up -d
docker compose run --rm --no-deps runner python scripts/orchestration/run_ingest.py --source empresas
PYTHONPATH=src python -m unittest discover -s tests -v   # testes
```

O passo a passo completo — variáveis de ambiente, backfill, orquestração
Prefect, logs, consulta ao DuckDB, CI e troubleshooting — está em
[docs/runbook-execucao.md](docs/runbook-execucao.md).

## Referências e repositórios complementares

As [referências](docs/referencias.md) incluem documentação oficial do Python, DuckDB, Prefect, Docker e Power BI, além da LGPD e da licença CC BY 4.0. O [documento principal, seção 7](docs/projeto.md#7-referências), contém a bibliografia do contexto e da governança.

O código e os artefatos entregues pela equipe estão neste repositório G05. Não há repositório auxiliar necessário declarado nos arquivos de execução ou na documentação de configuração. Ferramentas de terceiros são dependências externas, listadas nas referências; fontes restritas do parceiro não são repositórios públicos.

## Histórico de lançamentos

* 0.1.0 - Sprint 1 - 14/08/2026
    * Contexto Organizacional, Modelagem Quantitativa dos Dados e Data Model Canvas
* 0.2.0 - Sprint 2 - 28/08/2026
    * Governança de dados e contratos iniciais do ETL
* 0.3.0 - Sprint 3 - 11/09/2026
    * ETL, testes e documentação de execução e rastreabilidade
* 0.4.0 - Sprint 4 - 25/09/2026
    * Camada analítica, modelo semântico Power BI, dashboards e observabilidade
* 0.5.0 - Sprint 5 - 07/10/2026
    * Em andamento; entregas ainda não registradas neste histórico

## Licença/License

O projeto **Governança e Integração de Dados da Central de Pesquisas**, do grupo **Synapse (G05)** no [Inteli](https://www.inteli.edu.br/), usa a licença [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

A atribuição inclui Synapse, Inteli e os sete integrantes identificados com seus perfis na [seção Integrantes](#integrantes). A licença do repositório não autoriza divulgar dados pessoais ou bases restritas recebidas do parceiro.
