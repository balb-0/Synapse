# Protótipos de Dashboards (D01-D04) — Sindusfarma / Central de Pesquisas

Este repositório contém a suíte completa autocontida de protótipos de dashboards institucionais (D01 Operação, D02 Adesão e Representatividade, D03 Resultados e Questionários, D04 Qualidade e Governança), gerador determinístico de dados agregados, suíte de testes unitários e script de renderização visual automatizada.

---

## 📁 Estrutura de Arquivos

```
docs/assets/prototipos-dashboards/
├── gerar-dados-prototipos.py       # Gerador determinístico em Python stdlib
├── test_gerar_dados_prototipos.py  # Suíte de testes unitários (unittest)
├── dados-dashboard.json            # JSON de dados agregados gerado pelo pipeline
├── index.html                      # Aplicação web autocontida (HTML/CSS/JS)
├── renderizar-prototipos.mjs       # Script Playwright para captura de imagens
├── README.md                       # Documentação técnica e guia de execução
└── imagens/                        # Diretório de screenshots (Desktop e Mobile QA)
```

---

## ⚙️ Diretrizes e Regras de Negócio Implementadas

1. **Privacidade e Proteção de Dados (LGPD/PGI)**:
   - Nenhum e-mail, nome de empresa, `id_cliente`, `respondent_id`, `id_resposta` ou lista de empresas é exposto no JSON ou na interface.
   - Respostas abertas e texto livre foram 100% omitidos.
   - Na View D03, apenas **dois exemplos fechados allowlisted da Pesquisa 238** (Questão 110 Múltipla Escolha e Questão 104 Checkbox) são exibidos.
2. **Denominadores e Taxas Percentuais**:
   - Toda taxa percentual possui **numerador e denominador explícitos**.
   - Ausência de dado ou denominador zero resulta estritamente em `null` (nunca `0%`).
   - Todos os percentuais são arredondados com 1 casa decimal via `ROUND_HALF_UP` (ex: `19,0%`, `21,8%`).
3. **Identificação de Participação x Adesão**:
   - A contagem em `respondentes.csv` é denominada estritamente como **Participações Observadas** (18.735), evitando a rotulagem indevida como "adesão" (já que o universo de empresas contratadas não é informado na fonte).
4. **Respostas Atômicas x Respondentes**:
   - Cada linha em `teste.csv` (`respostas.csv`) é tratada como um **elemento atômico de resposta**, não como um respondente individual.
5. **Autocontido e Acessível (WCAG AA)**:
   - Sem dependências de CDN, bibliotecas remotas ou backend.
   - Reflow até **320px** e suporte a **zoom de 400%** sem transbordo global.
   - Skip link, foco visível de 3px, navegação por teclado e suporte a `prefers-reduced-motion`.

---

## 🚀 Comandos de Execução (Relativos à Pasta do Módulo)

### 1. Execução do Gerador de Dados Determinístico
Gera o arquivo `dados-dashboard.json` a partir das fontes CSV em `/home/marlos/projects/ultimo/context/csv`:

```bash
cd docs/assets/prototipos-dashboards
python3 gerar-dados-prototipos.py --input-dir /home/marlos/projects/ultimo/context/csv --output dados-dashboard.json
```

Para garantir reprodução byte a byte determinística via timestamp fixo:
```bash
python3 gerar-dados-prototipos.py --processado-em "2026-08-13T00:00:00Z"
```

### 2. Execução da Suíte de Testes Unitários
Valida esquemas, invariantes numéricas, golden numbers (D01-D04), regras de privacidade denylist/allowlist e determinismo:

```bash
python3 -m unittest test_gerar_dados_prototipos.py
```

### 3. Servidor HTTP Local Simples
Para visualizar o dashboard interativo `index.html` em qualquer navegador:

```bash
python3 -m http.server 8000
```
Acesse no navegador: `http://localhost:8000/index.html` (ou com hash `#d01`, `#d02`, `#d03`, `#d04`).

### 4. Renderização Automatizada de Screenshots (Playwright)
Gera as capturas de tela Desktop (`1600x1000 @ dsf 2`) e Mobile QA (`390x844 @ dsf 2`) na pasta `imagens/` e valida se o console não emitiu erros:

```bash
node renderizar-prototipos.mjs
```

---

## 📊 Metodologia e Fontes de Dados Utilizadas

| ID | Nome do Arquivo | Descrição da Fonte | Contagem Auditada |
|---|---|---|---|
| `pesquisas` | `pesquisas.csv` | Cadastro de pesquisas do portfólio | 366 linhas |
| `empresas` | `empresas.csv` | Cadastro institucional de empresas | 779 linhas |
| `clientes` | `clientes.csv` | Mapeamento de contatos/clientes | 5.430 linhas |
| `respondentes` | `respondentes.csv` | Participações registradas por pesquisa/empresa | 18.735 linhas |
| `questoes` | `questoes.csv` | Estrutura de perguntas dos questionários | 231 linhas |
| `teste` | `teste.csv` (`respostas.csv`) | Respostas atômicas registradas | 20.607 linhas |
| **TOTAL** | — | **Linhas totais auditadas nas fontes** | **46.148 linhas** |

---

## ⚠️ Limitações Identificadas e Indicadores Indisponíveis

- **I06 (Cumprimento de Prazo)**: Indisponível devido à ausência de dados sistemáticos de entrega no histórico.
- **I08 (Taxa de Adesão por Pesquisa)**: Indisponível por falta do universo de contratadas por pesquisa.
- **I11 (Representatividade de Mercado)**: Indisponível sem dados do mercado total por segmento.
- **I09 (Conflito de Identificação)**: Registra conflito entre `id_cliente` e `id_empresa` em 857 participações, tratado como diagnóstico aberto sem precedência artificial.
- **I21, I23, I24, I25**: Indisponíveis por ausência de logs de sistema, controle de acessos ou histórico de versões de regras nas cargas legadas.
