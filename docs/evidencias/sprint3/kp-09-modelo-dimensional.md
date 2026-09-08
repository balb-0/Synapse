# KP-09 — revisão do Modelo Dimensional dos quatro cubos

## Escopo

A revisão confrontou `docs/dmc.json` com a seção 5.2 de `docs/projeto.md`, sem
incorporar modelos alternativos ou criar um quinto cubo.

| Cubo | Grão | Tipo de fato | Resultado da revisão |
|---|---|---|---|
| C01 — Portfólio e Ciclo | Uma linha por pesquisa | Snapshot acumulativo | Cobertura de aprovação corrigida para 5,5%; contagem declarada separada da contagem observada |
| C02 — Participação e Representatividade | Uma linha por registro de participação | Transação | Participação diferenciada de resposta a questão; I09 bloqueado até homologar a fonte de mercado |
| C03 — Pipeline Mensal | Mês × status × área × tipo × perfil | Snapshot periódico | Estoque não soma no tempo; entradas e saídas exigem histórico de transições |
| C04 — Resultados e Questionários | Uma associação pesquisa × pergunta | Fato de associação | Contagens derivadas; `qtd_alternativas` mantida na dimensão; resposta por pessoa aguarda reconciliação |

## Dimensões conformadas

- `DIM_TEMPO`: C01, C02, C03 e C04.
- `DIM_PESQUISA`: C01, C02 e C04.
- `DIM_STATUS_PESQUISA`, `DIM_AREA`, `DIM_TIPO_PESQUISA` e
  `DIM_PERFIL_PESQUISA`: C01 e C03.

Empresa e Pessoa são próprias do C02; Pergunta é própria do C04; Família,
Fonte de Dado e Execução de Carga aparecem apenas no C01 no recorte atual. A
classificação não antecipa compartilhamentos futuros.

## Limitações preservadas

- `data_aprov` possui 20 valores válidos em 366 pesquisas; não sustenta leitura
  geral do ciclo.
- O universo elegível não existe, portanto adesão e engajamento não recebem
  denominador inventado.
- `market_share` e `% de mercado` divergem e nenhuma fonte recebe precedência
  sem homologação.
- O snapshot atual não reconstrói status históricos nem todas as transições
  ocorridas dentro de um mês.
- `respostas.csv` não possui ponte comprovada entre `respondent_id` e a
  identidade de `respondentes.csv`; não há união por similaridade.

## Gates reproduzíveis

```bash
python -m json.tool docs/dmc.json
python scripts/dmc/validate_dmc.py docs/dmc.json
python scripts/traceability/validate_traceability.py \
  --manifest scripts/traceability/manifest.json \
  --dmc docs/dmc.json \
  --project docs/projeto.md
python -m unittest discover -s scripts/dmc -p "test_*.py"
python -m unittest discover -s scripts/traceability -p "test_*.py"
```
