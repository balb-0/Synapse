# CB-16: publicação e conferência da geração Parquet

Este registro acompanha o card #309. CB-16 depende da reconciliação CB-14
(card #307) e do verificador de métricas CB-15 (card #308). O estado fechado
desses cards não comprova uma execução; a entrega precisa dos resultados da
mesma carga que produziu a publicação.

## Origem desta execução

O usuário enviou um pacote explicitamente identificado como **v3** após o
primeiro pacote desta rodada. A execução válida deste registro deve usar v3;
o SHA-256 confirmado é `d307d74bc81000317c74d59431cfbc71bf938bd15e41e39fcb397f699468a39e`.
O [recibo público da geração](evidencias/cb16/geracao-v3.json) registra o
inventário e o ID após a conferência da publicação.

O primeiro pacote tinha SHA-256
`d6cc8043562972659acc5a83f963a7938c91c494a754ade80c4e7e23d7648cd7` e
seis CSVs com bytes iguais ao conjunto de agosto. Essa rodada foi interrompida
antes da carga analítica e da publicação. Ela não é a geração final de CB-16.

A extração, o DuckDB e os arquivos publicados ficam fora do Git. O recibo
versionado conterá somente identificadores técnicos da carga/publicação,
contagens, esquemas, hashes e estados agregados. Não inclui registros, valores
de categorias, identificadores de pessoas/empresas/pesquisas ou credenciais.

## Correção de formato da fonte v3

A execução estrita inicial rejeitou o prefixo processado de `respostas` porque
`respondent_id` chegou em notação científica textual. Essa execução parcial
foi preservada para diagnóstico e não produziu uma geração aceita. A fonte
foi reprocessada com a regra corrigida de identificador opaco.

O adaptador conserva esse identificador como texto; não reconstrói um inteiro
nem o relaciona automaticamente a `cliente_id` ou à fonte `respondentes`.
A correção do schema de produção corresponde ao commit `894445d`. A ingestão
desta geração executou o código de `fd6864e` com adaptador privado de
`respondent_id` opaco (SHA-256
`b9702c67f926bf360db40b19ca3164b027e2449ebb819058142882e82e4aeec0`).
A carga analítica e a publicação executaram `894445d`. O recibo distingue esses
componentes e não atribui o adaptador privado ao commit de produção.

## Ingestão concluída

| Fonte | Extraídas | Carregadas | Rejeitadas | Duplicadas |
| --- | ---: | ---: | ---: | ---: |
| pesquisas | 366 | 366 | 0 | 0 |
| empresas | 779 | 779 | 0 | 0 |
| clientes | 5430 | 5429 | 1 | 0 |
| questoes | 3297 | 3186 | 111 | 0 |
| respondentes | 18735 | 17740 | 995 | 0 |
| respostas | 281835 | 266080 | 15755 | 0 |

As seis fontes têm equação balanceada e objeto marcado como carregado.
Cinco CSVs têm bytes iguais ao pacote de agosto; a execução leu esses arquivos
do pacote v3 e carregou um DuckDB novo. O prefixo `august_` em alguns IDs de
execução é um rótulo legado do script derivado do hash da fonte, sem reaproveitar
as tabelas de uma execução antiga.

A rotina privada de respostas conservou a regra de texto opaco e usou escrita
em blocos parametrizados de 128 linhas na retomada, com uma thread DuckDB.
O recibo registra os hashes do adaptador inicial e dessa rotina de retomada,
além do commit do ETL; não atribui o runtime privado ao código versionado.

## Conferência da geração publicada

A geração imutável é `6b1eaa686aac43b18b6d6545e1c2c5f1`, com
`load_reference` `afcde424-45e8-457b-8793-bf0866d142b2`. O manifesto e os
sete Parquet têm hashes, esquemas e contagens conferidos no recibo público.

| Publicação | Linhas | Resultado |
| --- | ---: | --- |
| C01 ciclo | 57 grupos, 366 pesquisas | métricas conferidas |
| C02 participação | 32 grupos, 17.740 participações | métricas conferidas |
| C03 pipeline mensal | 0 | `not_observed`, sem fechamento mensal |
| C04 instrumento | 45 grupos, 3.186 perguntas | métricas conferidas |
| Qualidade campo | 64 | contagens conferidas |
| Qualidade relação | 8 | contagens conferidas |
| Qualidade duplicidade | 5 | contagens conferidas |

O verificador independente reconstruiu os grupos C01, C02 e C04 a partir da
ingestão tratada. Comparou contagens, somas e denominadores com a publicação;
houve zero grupos divergentes. A reconciliação da carga aponta zero descartes
analíticos e zero diferenças nesses três cubos. Em C02, o tempo de
preenchimento não está disponível para nenhuma das 17.740 participações;
nenhuma média foi inferida. C03 continua sem observação de fechamento.

## Sequência de conferência

1. Concluir a ingestão e verificar
   `extraídas = carregadas + rejeitadas + duplicadas` em
   cada fonte. Rejeição de ingestão não é descarte analítico.
2. Executar a carga analítica e guardar seu `load_id`, sem criar um instante
   de fechamento mensal para fontes que não fornecem essa observação.
3. Executar `etl.analytics.reconcile` no banco estável. Conferir C01, C02 e
   C04, identidades e órfãos, e interpretar o estado C03 separadamente.
4. Conferir métricas, denominadores e indisponibilidade contra a ingestão
   tratada da mesma carga. Referências históricas de outra geração não
   substituem essa comparação.
5. Executar `etl.analytics.publish` com o `load_id` em `--load-reference`.
   Conferir os sete Parquet contra as consultas dos fatos e das tabelas de
   qualidade, além dos esquemas e SHA-256 do manifesto.
6. Entregar somente a subpasta imutável da geração aos consumidores autorizados.
   O refresh e as consultas DAX no Desktop pertencem a BI-02/BI-05/BI-06.

O [procedimento de acesso](acesso-cubos-bi.md) descreve os sete nomes de arquivo,
a publicação com conexão somente de leitura e os limites de distribuição.

## Evidência e estado

A ingestão, carga analítica, reconciliação, publicação e conferência de métricas
da geração v3 terminaram. O [recibo](evidencias/cb16/geracao-v3.json) limita a
aceitação à integridade dos sete arquivos e às métricas observáveis. O refresh
e a validação DAX no Desktop continuam pendentes nas tarefas BI. O recibo não
afirma a implementação de CB-15 nem a observação dos quatro cubos.

C03 exige um fechamento mensal observado. Sem essa fonte, o estado é
`not_observed`, e um Parquet vazio não comprova estoque zero. Entradas e saídas
continuam indisponíveis sem histórico de transições. A ausência de observação
não será preenchida com data ou valores inventados.
