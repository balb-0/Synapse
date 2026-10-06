# Sinalização dos indicadores sem dado disponível

Cumpre a DX-10: garante que todo indicador sem dado disponível aparece como
indisponível com o motivo textual, nunca como zero, e reúne esses indicadores
em uma tabela navegável dentro do próprio modelo.

## Duas frentes de sinalização

### 1. Medida bloqueada por completo (sem nenhum dado de origem)

`Taxa de Prorrogacao` (`PUB_C01_CICLO`, DX-07) e `Representatividade`
(`PUB_C02_PARTICIPACAO`, DX-08) são medidas que devolvem **texto**, não
número — a fórmula é o próprio motivo do bloqueio, não um `DIVIDE` que
poderia resultar em `BLANK()` ou, pior, ser mal implementado como `0`
diretamente. Uma medida de texto nunca é confundida com um valor numérico
zero em nenhum visual, incluindo cartão e tabela.

### 2. Medida parcialmente bloqueada por denominador vazio

Toda medida de razão implementada em DX-07, DX-08 e DX-09 usa `DIVIDE`, que
devolve `BLANK()` — nunca `0` — quando o denominador (a base válida) é zero
no contexto de filtro atual. Isso cobre o caso em que a medida é calculável
em geral, mas fica sem base num recorte específico (ex.: filtrar por uma
área/mês sem nenhuma pesquisa com par de datas válido).

### 3. Disponibilidade condicional das medidas C03

As entradas e saídas de status têm medidas numéricas próprias, que preservam
`BLANK()` quando o Parquet contém apenas `NULL`, e medidas textuais separadas
com o motivo (`histórico de transições de status não publicado`). O estoque
também tem uma medida de estado: sem linha C03 no período selecionado, o valor
numérico permanece vazio e o texto informa a ausência da linha. As medidas de
estado não retornam zero nem misturam texto e número na mesma expressão DAX.

Esses estados operacionais C03 não são indicadores I01–I25 e não entram na
contagem `Qtd Indicadores Sem Dado` (17). A geração publicada não contém o
marcador de fechamento mensal: por isso um fechamento observado com estoque
zero e um mês sem fechamento são indistinguíveis no modelo. O estado atual
declara apenas que não existe linha C03 na geração; a correção depende de o
contrato de publicação expor a observação do fechamento. Não inserir linha
sentinela nem inferir zero.

## Catálogo navegável — `DIM_INDICADORES_BLOQUEADOS`

Tabela calculada (`DATATABLE`, sem fonte externa) com um total de 18 linhas:
os 17 indicadores do catálogo I01–I25 que
[`docs/indicadores-publicaveis-bi.md`](indicadores-publicaveis-bi.md) (DX-01)
classifica como "Sem dado" na camada BI, mais I03, classificado como
"Parcial". Colunas: `indicador` (ID), `medida` (nome), `status` ("Sem dado"
ou "Parcial") e `motivo` — o mesmo texto-base já registrado em DX-01, para
não ter duas versões do motivo divergindo com o tempo. A medida `Qtd
Indicadores Sem Dado` conta quantos têm `status = "Sem dado"` (17, sem
contar o parcial).

Esta tabela não substitui as medidas de texto de DX-07/DX-08: ela é a visão
consolidada para um card de resumo ("N indicadores sem dado nesta versão") ou
uma tabela de exceções no relatório; as medidas de texto são o que aparece no
lugar do número quando alguém tenta consumir o indicador específico.

## Verificação

Para cada medida de razão (DX-07, DX-08, DX-09), testar no Power BI Desktop
com um filtro que esvazia a base (ex.: um `Status` sem nenhuma pesquisa com
`data_aprov` preenchida) e confirmar que o resultado é `BLANK()` (célula
vazia no visual), nunca `0`. Para `Taxa de Prorrogacao` e
`Representatividade`, confirmar que o texto aparece em qualquer contexto de
filtro, já que a medida nunca depende de dado ausente para decidir o que
mostrar — é sempre o mesmo texto, por construção.

Para C03, executar as consultas em
[`tests/analytics/dax/bi04-acceptance-queries.dax`](../tests/analytics/dax/bi04-acceptance-queries.dax)
no Power BI Desktop: estoque em um mês, estoque em um período com vários
fechamentos, período sem linha C03 e fluxos `NULL`. Esperar estoque somado
somente no último mês observado do período, `BLANK()` com motivo quando não há
linha e `BLANK()` com motivo de transições para entradas/saídas. Um fechamento
observado sem grupos não pode ser validado pela publicação atual; o Parquet não
traz seu marcador.
