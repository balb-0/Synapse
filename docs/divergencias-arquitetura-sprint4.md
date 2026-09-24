# Divergências entre arquitetura e implementação — Sprint 4

Este inventário compara as cinco visões ISO/IEC 10746, os diagramas UML e o
código executável no início da Sprint 4. O objetivo é localizar diferenças; a
correção de cada visão pertence aos cards AR-02 a AR-08.

## Método e escopo

Foram confrontados os documentos `visao-*-etl.md`, os três fontes PlantUML em
`docs/assets/uml/`, os módulos em `src/etl/`, os scripts de orquestração, o
`docker-compose.yml`, os arquivos de dependências e a configuração de CI.

As classificações usadas são:

- **defasagem documental**: o código já existe, mas o documento ainda descreve
  estado anterior ou planejado;
- **lacuna de implementação**: a documentação ou o desenho prevê uma capacidade
  que não está presente no código/configuração da base `develop`;
- **inconsistência interna**: dois artefatos documentais descrevem o mesmo
  elemento de formas incompatíveis.

## Inventário das divergências

| ID | Artefato e afirmação | Evidência no código/configuração | Classificação | Encaminhamento |
| :--- | :--- | :--- | :--- | :--- |
| D01 | `visao-informacao-etl.md` encerra a cadeia na ingestão tratada e declara que cubos não são construídos. | A base `develop` contém apenas `sql/duckdb/001_ingestao_tratada.sql`; não há DDL analítica integrada. | Lacuna de implementação dependente de CB-02 a CB-06. | AR-02 deve representar a camada analítica como dependência e distinguir contrato de artefato executável. |
| D02 | `visao-computacional-etl.md` marca adaptador de eventos e Elastic Stack como planejados. | `docker-compose.yml` possui somente MinIO, criação de bucket e runner; `src/etl/` não contém adaptador HTTP nem exportador Elastic. | Lacuna de implementação. | AR-03 deve manter esses itens fora do conjunto implementado até OB-07 e OQ-06 entrarem na base. |
| D03 | A visão computacional atribui ao repositório a confirmação do checkpoint após o fluxo completo. | `DuckDbLoadRepository.commit()` grava `_checkpoint`; `ingest_object()` chama a confirmação no controle da orquestração. | Defasagem de responsabilidade na documentação/diagrama. | AR-03 deve separar persistência do checkpoint da decisão de confirmá-lo. |
| D04 | `visao-engenharia-etl.md` descreve execução local e não apresenta servidor Prefect servido. | `scripts/orchestration/deployment.py` usa `ingest_object.serve()` com cron `0 3 * * *`; o Compose não inicia esse script automaticamente. | Defasagem documental com limite operacional. | AR-04 deve registrar o modo servido e explicitar que o operador ainda o inicia. |
| D05 | A visão de engenharia trata telemetria centralizada como planejada. | Há eventos estruturados em `extraction/log_events.py` e `load/log_events.py`, mas nenhum coletor está configurado no Compose. | Implementação parcial. | AR-04 deve separar emissão local de coleta, painel e alertas. |
| D06 | A visão de tecnologia registra intervalos de versão como se fossem uma pilha reprodutível. | `requirements.txt` usa `minio>=7.2,<8`, `prefect>=3,<4` e `duckdb>=1.1`. | Lacuna de reprodutibilidade dependente de OQ-09. | AR-05 deve citar a política real e não declarar versões exatas antes da fixação. |
| D07 | `visao-negocio-etl.md` limita o resultado à ingestão tratada e não descreve o consumo por BI. | Não há adaptador de publicação analítica na base; os cubos existem como contrato em `docs/dmc.json`. | Lacuna de implementação dependente de CB-08/CB-09. | AR-06 deve separar valor pretendido, indicador publicável e dado ainda indisponível. |
| D08 | `casos-de-uso-etl.plantuml` não contém acompanhamento de execução servida nem consumo analítico. | `deployment.py` expõe execução agendada/manual; não existe consumo BI executável em `develop`. | Defasagem documental e lacuna parcial. | AR-07 deve acrescentar a operação servida e representar BI com a condição correta. |
| D09 | `componentes-etl.plantuml` não evidencia o sink de logs da carga nem a fronteira do deployment servido. | `DuckDbLoadRepository` aceita `LoadLogSink`; `deployment.py` serve `ingest_object`. | Defasagem documental. | AR-07 deve mostrar interfaces de telemetria e a entrada do servidor Prefect. |
| D10 | `sequencia-ingestao-etl.plantuml` confirma o checkpoint apenas ao fim do objeto, sem explicitar a relação com cada lote persistido. | O fluxo chama `load_batch()` por lote e somente depois `repository.commit(batch.checkpoint)`; falhas impedem a confirmação do lote atual. | Defasagem de granularidade do diagrama. | AR-08 deve mostrar o ciclo carregar → reconciliar → confirmar para cada lote. |
| D11 | Os diagramas são referenciados apenas como fontes PlantUML. | `docs/assets/uml/` não contém renderizações PNG ou SVG dos três diagramas. | Lacuna de publicação. | AR-07/AR-08 devem versionar imagens renderizadas e manter os fontes. |
| D12 | A visão computacional afirma “19 suítes de testes”. | A árvore `tests/` muda ao longo da sprint e a contagem não é derivada automaticamente. | Defasagem documental recorrente. | AR-03 deve evitar contagem volátil ou vinculá-la a um comando reproduzível. |

## Itens coerentes verificados

- A separação `extraction` → `transformation` → `load` → `orchestration`
  corresponde à estrutura real de pacotes em `src/etl/`.
- O destino operacional é DuckDB e o repositório grava aceitos, rejeitados,
  metadados de lote e checkpoint em transações explícitas.
- O fluxo ignora objeto já concluído pelo checksum, salvo quando `reprocess` é
  verdadeiro, de acordo com `_control_object`.
- O agendamento documentado no script é diário às 03:00; ele não deve ser
  confundido com um serviço já iniciado pelo Compose.
