# Conferência do perfil de participação por área

A correção em `BE % demais por área` usa uma coorte fixa: empresas identificadas
com participação em pelo menos uma pesquisa do recorte completo das áreas
selecionadas, excluindo a empresa escolhida. Os demais filtros do usuário
(pesquisa, ano de divulgação e tipo) continuam ativos.

Para cada empresa da coorte, o numerador conta pesquisas distintas na área do
eixo; o denominador conta pesquisas distintas em todas as áreas selecionadas.
Uma empresa sem participação na área tem numerador zero. A média dá o mesmo
peso a cada empresa, independentemente de quantas pesquisas ela tem. A área da
linha do gráfico não pode reduzir a coorte. Sem empresa única selecionada ou
sem empresas comparáveis, o resultado fica vazio.

Isso não presume elegibilidade de todas as empresas cadastradas: a coorte
continua limitada às empresas observadas no recorte. O dado sintético contém
o grão necessário; os sete Parquet publicados não contêm empresa individual.
A medida do protótipo não deve ser portada para esse contrato com IDs fictícios.
RP-13/RP-14 ainda precisam redesenhar o benchmark ou homologar outro grão de acesso.

## Evidência automatizada disponível

[O teste SQL independente](../tests/analytics/test_benchmark_perfil.py) prova o
contrato para dados sintéticos de regressão:

| Cenário | Resultado esperado |
| :--- | :--- |
| Quatro empresas, cada uma em uma área diferente | 25% por área, soma 100%; nunca 100% nas quatro áreas |
| Empresa B com três pesquisas A e uma B; C com uma B | Média A 37,5% e B 62,5%, distinta do percentual agregado 60%/40% |
| Slicer somente A | Coorte formada somente nas áreas selecionadas; A 100% |
| Slicer A/C com C sem registros, mas A observada | A 100%, C zero |
| Linhas duplicadas, chave desconhecida e empresa escolhida | Não aumentam o número de pesquisas nem entram na média das demais |
| Nenhuma empresa comparável ou seleção não única | Vazio, sem zero fabricado |

Comando: `python -m unittest tests.analytics.test_benchmark_perfil`.
Os cinco testes passaram. Eles executam SQL/Python e não executam DAX.

## Aceite no Power BI Desktop pendente

1. Abrir o protótipo da mesma versão e atualizar os dois CSVs sintéticos.
2. Escolher uma empresa e registrar ID sintético, filtros e versão do modelo.
3. Executar [a consulta DAX](../tests/analytics/dax/benchmark-perfil-acceptance.dax),
   substituindo o ID, e guardar a saída. Aplicar os mesmos slicers na página.
4. Conferir a média dos percentuais individuais com os CSVs, incluindo zero
   para uma empresa observada em outra área. Repetir com área restrita, seleção
   múltipla/ausente de empresas e recorte sem registros.
5. Para áreas disjuntas que cobrem o recorte inteiro, conferir soma de 100%.
   Esse critério não é soma de participações: primeiro se calcula o percentual
   de cada empresa, depois a média entre as mesmas empresas em cada linha.
6. Guardar captura nova do Perfil de participação. A imagem histórica em
   `solucao_dashboard.md` é anterior à correção e não é evidência desse aceite.

Ainda não há saída DAX nem captura nova anexada. A correção de expressão e os
testes de referência não substituem essa execução.
