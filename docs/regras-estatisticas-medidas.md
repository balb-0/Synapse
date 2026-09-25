# Regras estatísticas obrigatórias das medidas

Cumpre a DX-03: toda medida especificada em
[`docs/especificacao-medidas-bi.md`](especificacao-medidas-bi.md) (DX-02)
segue as quatro regras abaixo. As regras valem para toda medida implementada
em DX-07, DX-08 e DX-09; a DX-10 usa as mesmas regras para decidir quando uma
medida vira indicador sinalizado em vez de número.

## 1. Mediana onde a dispersão invalida a média

**Regra:** usar mediana em vez de média sempre que a distribuição subjacente
for assimétrica o bastante para a média enganar (ex.: tempos de ciclo com
cauda longa) **e o dado de origem permitir o cálculo**.

**Limitação estrutural encontrada:** os quatro cubos publicados para o Power
BI (`docs/acesso-cubos-bi.md`) chegam pré-agregados por área/status/tipo/mês,
trazendo apenas `soma_*` e `qtd_*_disponivel` por grupo — nunca o valor por
pesquisa. Mediana exige a lista de valores individuais (ou pelo menos
percentis pré-computados); soma e contagem não bastam. Isso vale para toda
medida de duração de `PUB_C01_CICLO` (validação, coleta, tabulação, ciclo
total) e para `PUB_C02_PARTICIPACAO.soma_minutos_preenchimento`.

**Regra aplicada nesta entrega:** enquanto os cubos publicados só trouxerem
soma e contagem, a medida expõe **média com o denominador ao lado** (regra 2)
e registra essa limitação no motivo do indicador
(`docs/indicadores-publicaveis-bi.md`, coluna "Motivo do bloqueio (BI)"),
em vez de apresentar a média como se fosse suficiente por si. A regra de
mediana continua valendo por princípio — se um cubo futuro publicar o valor
por pesquisa ou um percentil pré-calculado, a medida correspondente passa a
usar `MEDIAN`/`PERCENTILEX.INC` e deixa de citar a limitação.

## 2. Filtro de denominador

**Regra:** toda razão declara e filtra pelo denominador correto antes de
dividir, e nunca usa `/` puro (que devolve erro ou infinito quando o
denominador é zero).

**Aplicação:** toda medida de razão desta entrega usa `DIVIDE(numerador,
denominador)`, que devolve `BLANK()` quando o denominador é zero em vez de
erro — nunca `0`. O denominador em si é sempre uma medida própria e visível
(`Base Válida Validação`, `Base Válida Coleta` etc., já listadas em
DX-02), nunca um número embutido só dentro da fórmula da razão.

## 3. Exibição do tamanho da base

**Regra:** todo painel que mostrar uma média, taxa ou percentual mostra ao
lado o tamanho da base que sustenta o número (o denominador da regra 2), para
quem lê não confundir "média de 3 pesquisas" com "média de 300".

**Aplicação:** cada medida de razão desta entrega tem uma medida-irmã de base
(`SUM(qtd_*_disponivel)`, `SUM(qtd_preenchimento_disponivel)`,
`SUM(qtd_chaves_informadas)`, `SUM(qtd_linhas)` conforme o caso, todas
listadas em DX-02) que a DX-05/DX-06 devem posicionar no mesmo visual da
razão, não em um relatório separado.

## 4. Proibição de contar linha como respondente

**Regra:** nenhuma medida trata uma linha de fato como se fosse uma pessoa
única, a não ser que a linha realmente identifique uma pessoa distinta.

**Aplicação:**
- `PUB_C02_PARTICIPACAO.qtd_participacoes` conta **participação**
  (ocorrência), não pessoa — a mesma pessoa pode ter mais de uma linha. Toda
  medida sobre essa coluna usa o nome "Participações", nunca "Respondentes"
  ou "Pessoas".
- `PUB_C04_INSTRUMENTO.qtd_perguntas` conta associação pesquisa-pergunta, não
  resposta nem respondente.
- Nenhuma medida de qualidade (`PUB_QUALIDADE_*`, DX-09) trata uma linha de
  `ingestao_respondentes` ou `ingestao_respostas` como proxy de pessoa; elas
  medem completude, integridade e duplicidade de registro, não população.
- `I13` (respondentes distintos) permanece sem dado na camada BI justamente
  porque nenhuma das colunas publicadas sustenta uma contagem distinta de
  pessoa sem violar esta regra (ver `docs/indicadores-publicaveis-bi.md`).
