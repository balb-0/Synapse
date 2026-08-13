# Protótipos de Dashboards (D01-D04) — Sindusfarma / Central de Pesquisas

Este diretório contém a suíte autocontida dos protótipos institucionais (D01 Operação, D02 Participação Observada, D03 Resultados e Questionários, D04 Qualidade e Governança), o gerador determinístico de agregados, os testes e o script de renderização.

---

## Estrutura de arquivos

```
docs/assets/prototipos-dashboards/
├── gerar-dados-prototipos.py       # Gerador determinístico em Python stdlib
├── test_gerar_dados_prototipos.py  # Suíte de testes unitários (unittest)
├── dados-dashboard.json            # JSON de dados agregados gerado pelo pipeline
├── index.html                      # Aplicação web autocontida (HTML/CSS/JS)
├── renderizar-prototipos.mjs       # Script Playwright para captura de imagens
├── README.md                       # Documentação técnica e guia de execução
└── imagens/                        # Capturas desktop e mobile para QA
```

---

## Diretrizes e regras de negócio implementadas

0. **Privacidade e proteção de dados (LGPD)**:
   - Nenhum e-mail, nome de empresa, `id_cliente`, `respondent_id`, `id_resposta` ou lista de empresas é exposto no JSON ou na interface.
   - Respostas abertas e texto livre foram omitidos.
   - Na view D03, somente **dois exemplos fechados selecionados internamente** são exibidos com rótulos neutros, sem IDs de pesquisa ou questão. Essa seleção não representa autorização de publicação.
0. **Denominadores e taxas percentuais**:
   - Toda taxa percentual possui **numerador e denominador explícitos**.
   - Ausência de dado ou denominador zero resulta estritamente em `null` (nunca `0%`).
   - Todos os percentuais são arredondados com 1 casa decimal via `ROUND_HALF_UP` (ex: `19,0%`, `21,8%`).
0. **Identificação de participação e adesão**:
   - A contagem em `respondentes.csv` é denominada estritamente como **Participações Observadas** (18.735), evitando a rotulagem indevida como "adesão" (já que o universo de empresas contratadas não é informado na fonte).
0. **Respostas atômicas e respondentes**:
   - Cada linha do arquivo recebido como `teste.csv`, nomeado conceitualmente `respostas.csv`, é tratada como **elemento atômico de resposta**, não como respondente individual.
0. **Autocontido e acessível (WCAG AA)**:
   - Sem dependências de CDN, bibliotecas remotas ou backend.
   - Reflow até **320px** e suporte a **zoom de 400%** sem transbordo global.
   - Skip link, foco visível de 3px, navegação por teclado e suporte a `prefers-reduced-motion`.

---

## Comandos de execução

### 1. Execução do gerador de dados determinístico

Gera o arquivo `dados-dashboard.json` a partir do diretório informado. O diretório deve conter os seis CSVs recebidos; `teste.csv` também pode estar normalizado fisicamente como `respostas.csv`:

```bash
cd docs/assets/prototipos-dashboards
python3 gerar-dados-prototipos.py --input-dir <diretorio-das-fontes> --output dados-dashboard.json
```

Para garantir reprodução byte a byte determinística via timestamp fixo:
```bash
python3 gerar-dados-prototipos.py --input-dir <diretorio-das-fontes> --output dados-dashboard.json --processado-em "2026-08-13T00:00:00Z"
```

### 2. Execução da suíte de testes

Valida esquemas, invariantes numéricas, valores de referência (D01–D04), regras de privacidade e determinismo. Por padrão, a suíte procura `context/csv` na estrutura do workspace; em outro ambiente, informe o diretório sem alterar o teste:

```bash
SINDUSFARMA_CSV_DIR=<diretorio-das-fontes> python3 -m unittest test_gerar_dados_prototipos.py
```

### 3. Servidor HTTP local simples
Para visualizar o dashboard interativo `index.html` em qualquer navegador:

```bash
python3 -m http.server 8000
```
Acesse no navegador: `http://localhost:8000/index.html` (ou com hash `#d01`, `#d02`, `#d03`, `#d04`).

### 4. Renderização automatizada das imagens

Gera as capturas desktop (`1600×1000`, escala 2) e mobile (`390×844`, escala 2) na pasta `imagens/` e falha se o console emitir erros. Instale o Playwright fora do repositório e informe seu diretório ao script:

```bash
diretorio_playwright=$(mktemp -d)
npm install --prefix "$diretorio_playwright" playwright
PLAYWRIGHT_MODULE="$diretorio_playwright/node_modules/playwright" node renderizar-prototipos.mjs
```

Se o navegador do Playwright não estiver instalado, informe um Chromium já disponível no ambiente com `CHROMIUM_EXECUTABLE=<caminho-do-chromium>`.

---

## Metodologia e fontes de dados utilizadas

| ID | Nome do Arquivo | Descrição da Fonte | Contagem Auditada |
|---|---|---|---|
| `pesquisas` | `pesquisas.csv` | Cadastro de pesquisas do portfólio | 366 linhas |
| `empresas` | `empresas.csv` | Cadastro institucional de empresas | 779 linhas |
| `clientes` | `clientes.csv` | Mapeamento de contatos/clientes | 5.430 linhas |
| `respondentes` | `respondentes.csv` | Participações registradas por pesquisa/empresa | 18.735 linhas |
| `questoes` | `questoes.csv` | Estrutura de perguntas dos questionários | 231 linhas |
| `respostas` | recebido como `teste.csv`; nome canônico `respostas.csv` | Respostas atômicas registradas | 20.607 linhas |
| **TOTAL** | — | **Linhas totais auditadas nas fontes** | **46.148 linhas** |

---

## Limitações identificadas e indicadores indisponíveis

- **I06 (Pesquisas atrasadas ou prioritárias)**: indisponível sem data de referência, elegibilidade de atraso e regra de prioridade aprovadas.
- **I08 (Taxa de Adesão por Pesquisa)**: Indisponível por falta do universo de contratadas por pesquisa.
- **I11 (Taxa de engajamento do público)**: indisponível sem o universo elegível por área, cargo ou departamento.
- **I09 (Participação de mercado observada)**: fica bloqueado porque `market_share` e `% de mercado` divergem entre fontes e ainda não há fonte autoritativa homologada.
- **I21, I23, I24, I25**: Indisponíveis por ausência de logs de sistema, controle de acessos ou histórico de versões de regras nas cargas legadas.
