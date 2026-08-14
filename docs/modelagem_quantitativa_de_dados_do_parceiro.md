# Modelagem quantitativa de dados do parceiro

## 1. Objetivo e escopo

Este relatório registra características observadas no snapshot quantitativo da
Central de Pesquisas do Sindusfarma. O objetivo é estabelecer uma linha de base
reprodutível para a documentação, sem afirmar redução de prazo, aumento de
adesão ou funcionamento de uma plataforma produtiva.

Os resultados foram calculados sobre seis bases externas, sem incorporar os
arquivos brutos ao repositório. O método reproduzível está previsto em
[`analise_quantitativa.py`](./analise_quantitativa.py), o log em
[`resultados_analise.txt`](./resultados_analise.txt) e as figuras agregadas em
[`figuras/fig1.png`](./figuras/fig1.png) a [`figuras/fig5.png`](./figuras/fig5.png).
As fontes externas precisam estar disponíveis para repetir a execução.

Os números deste relatório descrevem o snapshot recebido. Campos ausentes,
identidades não conciliadas e períodos incompletos permanecem limitações
observadas; não foram preenchidos por estimativa.

## 2. Unidades de análise e grãos

| Unidade | Grão | Registros | Representação no processo |
| :--- | :--- | ---: | :--- |
| Pesquisa | uma pesquisa | 366 | Demanda registrada, planejada, executada e entregue; referência do ciclo |
| Empresa | uma organização | 779 | Universo setorial e atributos estratégicos |
| Pessoa/cliente | um indivíduo cadastrado | 5.430, sendo 5.429 válidos | Cadastro conhecido pela Central; maior exposição à LGPD |
| Participação | pesquisa × empresa × pessoa | 18.735 | Evento observado de participação |
| Questão | uma pergunta de questionário | 231 | Estrutura do instrumento de coleta |
| Elemento de resposta | resposta de um respondente a uma pergunta de uma pesquisa | 20.607 | Conteúdo coletado; não equivale a um questionário respondido |

A **Pesquisa** é a unidade de referência principal porque é o eixo compartilhado
pelas fontes de participação, questões e respostas e porque contém os marcos que
permitem medir desempenho. Ela não é a unidade de medida de todos os indicadores:
adesão é medida por participação, e conteúdo é medido por elemento de resposta.
Além disso, o eixo não é íntegro: 17,4% dos elementos de resposta apontam para
identificadores ausentes do cadastro de pesquisas. Portanto, trata-se da unidade
pretendida de referência, não de uma ligação efetiva para todos os registros.

## 3. Handoff de outras autorias

<!-- QUANTI:UT-01:HANDOFF:3:START -->
Esta seção deve ser preenchida por outra autoria. Não preencher neste relatório.
<!-- QUANTI:UT-01:HANDOFF:3:END -->

## 4. Handoff de outras autorias

<!-- QUANTI:UT-01:HANDOFF:4:START -->
As subseções §4.1–§4.5 devem ser preenchidas por outras autorias. Não preencher
neste relatório.
<!-- QUANTI:UT-01:HANDOFF:4:END -->

## 4.6 Distribuição temporal e sazonalidade observadas

`data_divulgacao` é o eixo temporal adotado porque marca a entrada em campo e é
o único marco validado contra outra variável da mesma base: o dia da semana
registrado coincide com o dia derivado em 100% dos 358 registros datados. Há
358 de 366 pesquisas datadas (97,8%). `data_solicitacao` possui cobertura um
pouco maior, com 362 registros (98,9%), e sua série alternativa é apresentada
ao final desta seção.

### 4.6.1 Cobertura dos marcos

| Marco | Registros | Cobertura | Janela observada |
| :--- | ---: | ---: | :--- |
| `data_solicitacao` | 362 | 98,9% | 22/11/2022–07/06/2027 |
| `data_divulgacao` | 358 | 97,8% | 24/11/2022–07/06/2027 |
| `data_limite` | 358 | 97,8% | 02/12/2022–18/09/2027 |
| `data_entrega` | 334 | 91,3% | 14/10/2022–18/03/2026 |
| `prorrogada_ate` | 68 | 18,6% | 15/03/2023–23/02/2026 |
| `data_aprov` | 20 | 5,5% | 05/04/2023–16/03/2026 |

`data_aprov` não sustenta um indicador temporal neste snapshot. Essa é uma
restrição de disponibilidade do dado, não uma decisão de escopo.

### 4.6.2 Volume anual de divulgação

| Ano | Pesquisas divulgadas |
| ---: | ---: |
| 2022 | 3 |
| 2023 | 97 |
| 2024 | 99 |
| 2025 | 117 |
| 2026 | 39 |
| 2027 | 3 |
| Sem data | 8 |

A média dos três anos completos (2023–2025) é 104,3 pesquisas por ano. Os anos
de 2026 e 2027 misturam dados parciais e pesquisas apenas agendadas. Há 12
pesquisas com divulgação posterior a 14/08/2026, e `data_limite` chega a
18/09/2027; qualquer série temporal precisa aplicar uma data de referência.

### 4.6.3 Sazonalidade mensal

| Mês | Pesquisas |
| :--- | ---: |
| Jan | 25 |
| Fev | 30 |
| Mar | 36 |
| Abr | 34 |
| Mai | 30 |
| Jun | 32 |
| Jul | 24 |
| Ago | 30 |
| Set | 37 |
| Out | 43 |
| Nov | 28 |
| Dez | 9 |

Entre os 358 registros datados, dezembro tem 9 divulgações e outubro tem 43.
Assim, uma comparação contra o mês imediatamente anterior pode ser enganosa;
a comparação adequada é com o mesmo mês do ano anterior ou por trimestre.

### 4.6.4 Dia da semana

| Dia codificado | Interpretação | Pesquisas |
| ---: | :--- | ---: |
| 2 | Segunda-feira | 132 |
| 3 | Terça-feira | 87 |
| 4 | Quarta-feira | 77 |
| 5 | Quinta-feira | 46 |
| 6 | Sexta-feira | 16 |

O código `7` aparece em 5 pesquisas, todas sem `data_divulgacao`. Ele funciona
como sentinela implícita de “não lançada” dentro de um domínio numérico e deve
ser formalizado no catálogo antes de ser somado ou promediado. Há ainda 3
registros sem código.

### 4.6.5 Desempenho e prorrogação

| Ano | n | Mediana do ciclo | Média | Desvio-padrão | Prorrogação |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2022 | 3 | 16 | 15,00 | 2,65 | — |
| 2023 | 97 | 19 | 23,11 | 14,42 | 26,8% |
| 2024 | 99 | 19 | 21,03 | 12,60 | 25,3% |
| 2025 | 117 | 18 | 19,80 | 9,63 | 11,1% |
| 2026 | 15 | 19 | 20,07 | 11,39 | 10,3% |

No conjunto global de 331 pesquisas com ciclo calculável, a mediana é 19 dias
úteis, a média é 21,1, o desvio-padrão é 12,2 e o coeficiente de variação é
58%. A mediana é estável; a diferença observada aparece principalmente na
dispersão (14,4 para 9,6) e na taxa de prorrogação (26,8% para 11,1%). Essas
são características observadas do snapshot, não efeitos da solução proposta.

### 4.6.6 Participação ao longo do tempo

De 2024 em diante, empresas distintas se estabilizam aproximadamente entre 330
e 339, enquanto pessoas distintas continuam crescendo. O crescimento recente
de registros ocorre, portanto, principalmente pela participação de mais pessoas
nas mesmas empresas, e não pela expansão equivalente do conjunto de empresas.
Há 194 registros de participação sem ano atribuível.

### 4.6.7 Variáveis temporais não utilizáveis como eixo

`hora_inicio` e `hora_termino` estão preenchidos em 807 de 18.735 registros
(4,3%), concentrados em 15 pesquisas entre 12/01/2026 e 17/03/2026. A duração
derivada tem mediana de 3 minutos e máximo de 19.918 minutos; ela mede intervalo
entre acessos, não tempo ativo. Não deve ser comparada diretamente com
`tempo_preenchimento`, cuja mediana declarada é de 5 minutos.

### 4.6.8 Série alternativa por data de solicitação

| Ano | `data_solicitacao` | `data_divulgacao` |
| ---: | ---: | ---: |
| 2022 | 5 | 3 |
| 2023 | 95 | 97 |
| 2024 | 99 | 99 |
| 2025 | 119 | 117 |
| 2026 | 41 | 39 |
| 2027 | 3 | 3 |
| Sem data | 4 | 8 |
| **Total datado** | **362** | **358** |

A média dos três anos completos coincide nos dois eixos: 104,3. A escolha do
eixo altera a atribuição anual de pesquisas individuais, não a ordem de grandeza.

## 5. Linha de base quantitativa

Os valores abaixo são observações do snapshot. Eles não medem desempenho de uma
solução produtiva.

| Tema | Resultado observado |
| :--- | :--- |
| Adesão por pesquisa | Mediana de 54 empresas distintas; média 57,3; mínimo 7; máximo 187 |
| Alcance acumulado do cadastro | 419 de 779 empresas com participação (53,8%); 360 sem participação |
| Representatividade declarada | Mediana de 51% em 322 registros; 74 abaixo de 40% |
| Completude operacional | Média de 94,2% em seis campos; `data_aprov` em 5,5% e `complexidade` em 24,6% |
| Integridade referencial | 17,4% dos elementos de resposta, 18,6% das questões e 0,29% das participações sem correspondência de pesquisa |
| Densidade de respostas | 20.607 elementos para 542 respondentes distintos: 38,0 linhas por respondente |
| Consistência declarado × observado | Coincidência em 290 de 326 pesquisas (89,0%); divergência média de 3,10 empresas |

Na matriz, o número de elementos por par respondente–pergunta tem mediana 23 e
máximo 96. Esses valores reforçam que uma linha de resposta não deve ser tratada
como uma pessoa ou como um questionário respondido.

## 6. Cuidados matemáticos antes da automatização

1. Declarar sempre a granularidade e o denominador. A adesão sobre associados
   resulta em 8,8%, enquanto o alcance acumulado do cadastro resulta em 53,8%;
   são leituras diferentes dos mesmos dados.
2. Não contar linhas como entidades. A quantidade de perguntas de matriz pode
   inflar artificialmente o número aparente de respondentes.
3. Aplicar completude por tipo de informação: vazio em `linha_matriz` pode ser
   correto para pergunta aberta, enquanto vazio em `prorrogada_ate` significa
   ausência de prorrogação observada.
4. Excluir períodos incompletos e registros futuros antes de comparar séries.
5. Reportar dispersão junto com posição: o CV é 58% no ciclo de entrega e 190%
   em `dias úteis aberta`.
6. Preferir mediana em distribuições concentradas: participações por empresa
   têm mediana 6, terceiro quartil 58, máximo 266 e média 44,7.
7. Não tratar identificadores como números. O identificador externo de respondente
   e o código ordinal cíclico de dia da semana têm semânticas distintas.
8. Usar redundâncias internas como testes: participantes coincide com a contagem
   observada em 290 de 326 pesquisas (89,0%), o dia da semana coincide em 100%
   dos registros datados e o ciclo declarado tem correlação 0,996 com o derivado.
9. Não substituir uma variável por outra parecida: `tempo_preenchimento` é
   declarado, enquanto a duração derivada dos horários é medida.

As definições de grão e de respostas devem permanecer alinhadas às seções §5.2
e §5.3 do documento canônico quando forem integradas.

## 7. Handoff de outras autorias

<!-- QUANTI:UT-01:HANDOFF:7:START -->
Referências bibliográficas e mapa completo de auditabilidade pertencem à
integração posterior no documento canônico. Não preencher neste MR.
<!-- QUANTI:UT-01:HANDOFF:7:END -->
