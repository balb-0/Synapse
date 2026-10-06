# CB-16: publicação e conferência da geração Parquet

Este registro acompanha o card #309. CB-16 depende da reconciliação CB-14
(card #307) e do verificador de métricas CB-15 (card #308). O estado fechado
desses cards não comprova uma execução; a entrega precisa dos resultados da
mesma carga que produziu a publicação.

## Origem desta execução

O usuário enviou um pacote explicitamente identificado como **v3** após o
primeiro pacote desta rodada. A execução válida deste registro deve usar v3;
o SHA-256, o inventário e o ID da geração serão anexados depois da carga e
da conferência.

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
está sendo reprocessada com a regra corrigida de identificador opaco.

O adaptador conserva esse identificador como texto; não reconstrói um inteiro
nem o relaciona automaticamente a `cliente_id` ou à fonte `respondentes`.
A correção do schema de produção corresponde ao commit `894445d`, com testes
focados informados pelo responsável. O recibo final deverá identificar o
código e o adaptador efetivamente executados, além das novas contagens. Nenhum
resultado parcial desta tentativa substitui os totais da execução completa.

## Sequência de conferência

1. Concluir a ingestão e verificar `extraídas = carregadas + rejeitadas` em
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

A ingestão sobre o pacote v3 está em andamento. A publicação deve usar a
revisão corrigida do publicador, após a verificação de falhas encontradas em
`develop`. O recibo identificará o código de ingestão, carga analítica e
publicação separadamente; não reutiliza manifesto de uma execução parcial. O ID da geração,
`load_reference`, sete contagens e hashes ainda não foram anexados a este
registro. Não há declaração de conclusão ou aceite final nesta etapa.

C03 exige um fechamento mensal observado. Sem essa fonte, o estado é
`not_observed`, e um Parquet vazio não comprova estoque zero. Entradas e saídas
continuam indisponíveis sem histórico de transições. A ausência de observação
não será preenchida com data ou valores inventados.
