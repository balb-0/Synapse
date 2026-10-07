# Valores de referência — geração v3

Resultado de [`consultas-referencia.sql`](consultas-referencia.sql) sobre a
geração `6b1eaa686aac43b18b6d6545e1c2c5f1` (`load_reference`
`afcde424-45e8-457b-8793-bf0866d142b2`), a mesma usada nas sessões S1–S4.
Somente agregados da publicação; nenhum identificador de pesquisa, empresa
ou pessoa. O moderador usa esta tabela para conferir cada número lido pelo
participante no mesmo recorte. Valores com uma casa decimal seguem o
arredondamento da medida no relatório (`#,0.0`).

## 1. Recortes das tarefas

<div align="center">
<sub>Tabela 1 - Recorte aplicado e valor de referência por tarefa</sub><br>

| Recorte | Tarefa | Página | Filtros aplicados | Valor de referência |
| :--- | :--- | :--- | :--- | :--- |
| R-NAV-01 | T-NAV-01 | Produção e Volume | nenhum | 366 pesquisas; maior status `finalizada` = 332 |
| R-NAV-01 | T-NAV-01 | Produção e Volume | nenhum (cartão "Indicadores principais") | 366 pesquisas; média de ciclo total 28,6 dias; base válida de ciclo total 331; média de coleta 13,9 dias |
| R-FIL-01 | T-FIL-01 | Produção e Volume | Área = assuntos regulatórios | 88 pesquisas, sem recorte de período |
| R-FIL-02 | T-FIL-02 | Produção e Volume | Tipo = pesquisa fixa anual; Status ≠ finalizada | 17 (aguardando data predefinida 14; em andamento 2; em análise da área técnica 1) |
| R-FIL-03 | T-FIL-03 | Produção e Volume | filtros limpos | 366 |
| R-FIL-04 | T-FIL-04 | Produção e Volume | Área = inovação; Tipo = pesquisa fixa anual | recorte vazio (0 linhas publicadas) |
| R-DET-01 | T-DET-01 | Produção e Volume | Status = finalizada | 332 de 366; tipo mais frequente `solicitação de associado` = 163 |
| R-DET-02 | T-DET-02 | Participação agregada (C02) | nenhum | 17.740 participações; maior área `sindical trabalhista e rh` = 6.507; empresa: aviso |
| R-DET-03 | T-DET-03 | Estoque, Instrumento e Qualidade | Área = assuntos regulatórios | 682 associações (múltipla escolha 400; caixas de seleção 200; aberta 43; numérica 38; matriz 1) |
| R-DET-04 | T-DET-04 | Estoque, Instrumento e Qualidade | nenhum | completude global 71,4%; `pesquisas.prorrogada_ate` 68 de 366 (298 sem valor, 18,6%) |
| R-DET-05 | T-DET-05 | Produção e Volume | linha assuntos regulatórios × finalizada × solicitação de associado | 37 pesquisas no grupo; média de ciclo 30,4 dias; sem drill-through |
| R-CMP-01 | T-CMP-01 | Participação agregada (C02) | Ano | nenhum ano observado: `mes_resposta` vazio nas 32 linhas → comparação `sem dado` |
| R-CMP-02 | T-CMP-02 | Participação agregada (C02) | nenhum | uma única categoria sem mês, com 17.740 participações → evolução mensal `sem dado` |
| R-SEG-01 | T-SEG-01 | Produção e Volume | Área = sindical trabalhista e rh; Tipo = pesquisa fixa anual | 44 |
| R-SEG-02 | T-SEG-02 | Produção e Volume → Estoque, Instrumento e Qualidade | Área = assuntos regulatórios; Tipo = solicitação de associado; Status = finalizada | 37 em C01; em C04, só Área se aplica: 682 associações |
| R-SEG-03 | T-SEG-03 | Produção e Volume | Área = sindical trabalhista e rh; Tipo = pesquisa fixa anual; Status = em tabulação | recorte vazio; sem o Status volta a 44 |

<sup>Material produzido pelos autores (2026), a partir da geração v3</sup>

</div><br>

## 2. Distribuição por status (C01)

| Status | Pesquisas | Base válida de ciclo total | Média de ciclo total (dias corridos) |
| :--- | ---: | ---: | ---: |
| finalizada | 332 | 329 | 28,7 |
| aguardando data predefinida | 19 | 0 | sem valor |
| em andamento | 5 | 0 | sem valor |
| em análise da central de pesquisas | 3 | 0 | sem valor |
| em análise da área técnica | 3 | 0 | sem valor |
| em tabulação | 3 | 2 | 19,0 |
| em desenvolvimento | 1 | 0 | sem valor |
| **Total** | **366** | **331** | **28,6** |

A média total é ponderada pela base: (28,7 × 329 + 19,0 × 2) / 331 ≈ 28,6.
Não é a média simples das linhas.

## 3. Tempo por etapa e tipo (C01), com a base de cada média

| Tipo | Validação (base) | Coleta (base) | Tabulação (base) |
| :--- | :--- | :--- | :--- |
| solicitação de associado | 10,3 (16) | 7,8 (167) | 6,8 (165) |
| pesquisa fixa anual | 0,0 (1) | 27,0 (80) | 20,3 (64) |
| solicitação da área técnica | 0,0 (1) | 14,6 (49) | 5,6 (47) |
| uso interno | 3,0 (2) | 11,1 (24) | 6,6 (20) |
| pública | sem valor (0) | 12,3 (25) | 4,8 (25) |
| solicitação de parceiro | sem valor (0) | 19,0 (8) | 7,4 (8) |
| pesquisa fixa bianual | sem valor (0) | 14,5 (4) | sem valor (0) |
| errata | sem valor (0) | 7,0 (1) | 21,0 (1) |

A validação tem base total de 20 pesquisas, coerente com a completude de
`pesquisas.data_aprov` (20 de 366, 5,5%) na tabela de qualidade.

## 4. Participação (C02), instrumento (C04) e estoque (C03)

| Item | Valor |
| :--- | :--- |
| Participações observadas | 17.740 (soma das 12 áreas confere) |
| Base de tempo de preenchimento | 0 → média de minutos `sem dado` |
| Meses de resposta observados | nenhum (`mes_resposta` vazio; `respondentes.hora_inicio` com 0% de completude) |
| Associações pesquisa-pergunta | 3.186 (múltipla escolha 1.551; caixas de seleção 1.102; aberta 225; numérica 216; matriz 92) |
| Fechamentos mensais de C03 | 0 linhas → estoque `sem dado` |
| Indicadores no catálogo com estado "Sem dado" | 17 |
