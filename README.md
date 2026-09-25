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

## 📝 Descrição

Construir a **espinha dorsal de dados da Central de Pesquisas do Sindusfarma** — integrando as fontes hoje dispersas (planilhas, formulários de coleta, gestão de tarefas e o repositório publicado), estruturando um banco de dados centralizado na nuvem, garantindo governança, qualidade e conformidade com a LGPD ao longo do ciclo de vida das pesquisas, e entregando um data app com dashboards operacionais e estratégicos que eliminam a dependência de atualizações manuais.

## 📝 LINKS

<a href="/docs/projeto.md">Link para a documentação geral</a> do projeto.
<br>
<a href="/docs/index.md">Índice da documentação</a> (estrutura completa e comandos de validação).

## 📊 Dashboards

O projeto prevê uma camada de visualização com dashboards que consomem o banco central, hoje em fase de protótipo:

- **Dashboard Operacional**: status das pesquisas em andamento, adesão por empresa e área, e tempos do ciclo (validação, coleta, tabulação).
- **Dashboard Estratégico**: volume de pesquisas por período, evolução da adesão e representatividade de mercado das participantes.

## 📁 Estrutura de pastas

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
│  ├─ orchestration/                                  # Entrypoints do ETL (run_ingest, run_backfill, deployment)
│  ├─ transformation/                                 # Auditoria e renderização do schema de transformação
│  ├─ load/                                           # Health check do DuckDB e renderização da DDL
│  ├─ prototipos-dashboards/                          # Geração, testes e renderização dos protótipos
│  ├─ data_quality/                                   # Validação da qualidade dos dados
│  ├─ governance/                                     # Validação de governança
│  └─ traceability/                                   # Validação de rastreabilidade às fontes
├─ docker-compose.yml                                 # Ambiente local: MinIO, Prefect e runner
├─ prefect.yaml                                       # Deployments Prefect
├─ Dockerfile                                         # Imagem do runner do ETL
├─ requirements.txt                                   # Dependências de execução (minio, prefect, duckdb)
├─ .env.example                                       # Modelo das variáveis de ambiente do ETL
├─ .gitlab/
│  └─ merge_request_templates/                        # Template de Merge Request
├─ .gitlab-ci.yml                                     # Pipeline de CI
├─ .gitignore
└─ README.md
```

## ✅ Requisitos

Para executar as validações localmente, utilize as versões abaixo (ou superiores compatíveis):

- **Git**: 2.40+
- **Python**: 3.12+ (ETL, análise quantitativa e scripts de validação)
- **Docker e Docker Compose** (ambiente local do ETL: MinIO + runner)
- **matplotlib**: 3.9+ (geração dos gráficos da análise quantitativa)
- **jq**: 1.6+ (validação estrutural do `dmc.json`)

## 💻 Configuração para desenvolvimento

```bash
git clone https://git.inteli.edu.br/graduacao/2026-2a/t13/g05
cd g05
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

> As bases brutas (CSV/XLS/XLSX) não fazem parte do repositório por conterem dados pessoais — os scripts de validação que dependem delas exigem as fontes em um diretório externo seguro.

## 🚀 Execução do ETL

O pipeline de ingestão (CSVs → MinIO → Prefect → DuckDB) sobe com Docker
Compose e é executado pelos entrypoints em `scripts/orchestration/`:

```bash
docker compose up -d
docker compose exec runner python scripts/orchestration/run_ingest.py --source empresas
PYTHONPATH=src python -m unittest discover -s tests -v   # testes
```

O passo a passo completo — variáveis de ambiente, backfill, orquestração
Prefect, logs, consulta ao DuckDB, CI e troubleshooting — está em
[docs/runbook-execucao.md](docs/runbook-execucao.md).

## 🗃 Histórico de lançamentos

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

## 📋 Licença/License

<p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/"><a property="dct:title" rel="cc:attributionURL" href="https://git.inteli.edu.br/graduacao/2026-2a/t13/g05">Governança e Integração de Dados da Central de Pesquisas</a> by <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://git.inteli.edu.br/graduacao/2026-2a/t13/g05">INTELI</a>, <a href="https://www.linkedin.com/in/anna-riciopo/">Anna Riciopo</a>, <a href="https://www.linkedin.com/in/karine-paixao/">Karine Paixão</a>, <a href="https://www.linkedin.com/in/lucas-nunes-matheus/">Lucas Nunes Matheus</a>, <a href="https://www.linkedin.com/in/marlos-do-carmo-guedes-366987250/">Marlos Guedes</a>, <a href="https://www.linkedin.com/in/milena-castro-vieira/">Milena Castro Vieira</a>, <a href="https://www.linkedin.com/in/otavio-vasc/">Otávio Vasconcelos</a>, <a href="https://www.linkedin.com/in/vitor-balbo/">Vitor Balbo</a> is licensed under <a href="http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">Attribution 4.0 International<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1"></a></p>
