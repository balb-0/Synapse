# ADR 0006 — Ratificação do padrão de observabilidade para a Sprint 4

- **Status:** Aceito
- **Data:** 24/09/2026
- **Responsável pela decisão:** responsável por observabilidade (Sprint 4)
- **Complementa:** [ADR 0001](0001-arquitetura-etl-python-prefect-minio-duckdb.md)
- **Depende de:** [`inventario-telemetria-observabilidade.md`](../inventario-telemetria-observabilidade.md) (OB-01)

## Contexto

O ADR 0001 já ratificou, em 11/09/2026, o padrão de observabilidade da
arquitetura: logs estruturados em JSON, correlacionados por `run_id`,
`task_id` e `event_id`, transportados pela Elastic Stack (Logstash →
Elasticsearch → Kibana), com cada etapa publicando duração, volumes,
rejeições, tentativas e latência — sem que a indisponibilidade do transporte
corrompa ou confirme uma carga incompleta.

O inventário da Sprint 4 (OB-01) confrontou esse padrão escrito com o que
existe hoje no `develop` e achou três divergências que a implementação desta
sprint (OB-03 a OB-11) precisa resolver, não redecidir:

1. **`task_id` não identifica uma execução.** Nos eventos por lote
   (`extraction.batch.emitted`, `load.batch.emitted`), `task_id` vem de
   `BatchMetadata.task_id`, preenchido com um rótulo fixo por fonte
   (`task_id=f"extract-{self.source}"`, `csv_extractors.py:357`) — o mesmo
   valor em toda execução da mesma fonte. Os cinco eventos de orquestração em
   `flow.py` não carregam `task_id` nenhum. Nenhum dos dois atende à
   correlação por `task_id` que o ADR 0001 promete.
2. **`event_id` nunca existiu como campo de log.** O único uso do termo no
   código é o parâmetro `event_id` do flow `ingest_object`, que serve para
   compor o `run_id` (`run_id = event_id or checksum[:16]`) — não é um campo
   emitido junto do log, é substituído pelo próprio `run_id`.
3. **A transformação não emite evento por lote.** Extração e carga têm cada
   uma sua classe de evento (`ExtractionBatchLogEvent`, `LoadBatchLogEvent`);
   a transformação só devolve `TransformationResult.metrics` para quem a
   chamou, e a orquestração loga apenas o total agregado (`accepted_count`)
   — rejeitados e duplicados calculados pela transformação não chegam a
   nenhum log.

A Sprint 4 exige (catálogo de tasks, OB-03/OB-04/OB-05/OB-06) logs
estruturados correlacionados nas quatro etapas, métricas de transformação
publicadas e retries/latência instrumentados com rótulos limitados. Manter o
padrão como está escrito, sem resolver essas três divergências, faria OB-03 e
OB-04 herdarem a mesma inconsistência.

## Decisão

**O padrão do ADR 0001 é ratificado sem troca de arquitetura — Elastic Stack
continua sendo o destino da telemetria, e o formato "nome do evento como
mensagem, atributos técnicos em `extra`" continua valendo para as quatro
etapas.** Três pontos do padrão são esclarecidos para a Sprint 4, resolvendo
as divergências do OB-01:

1. **`task_id` passa a significar o identificador que o Prefect atribui à
   execução daquela tarefa (`task run`), único por tentativa** — não mais um
   rótulo fixo por fonte. Este ADR fixa a semântica, não o acessor exato: cabe
   a OB-03/OB-04 confirmar, na versão instalada (`prefect>=3,<4`), o meio
   correto de ler esse identificador dentro de uma task (por exemplo, o
   módulo de runtime do Prefect) e propagá-lo tanto para os eventos por lote
   quanto para os marcos de orquestração, que hoje não carregam `task_id`
   nenhum. O rótulo `extract-{source}` deixa de ser usado como `task_id`;
   onde for útil identificar a fonte, isso já é feito pelo campo `source`,
   que continua existindo separado.
2. **`event_id` é removido do padrão como campo próprio.** O ADR 0001 o
   citava, mas ele nunca existiu como atributo de log — na prática, o
   parâmetro `event_id` do disparo por evento já vira o próprio `run_id`.
   Correlação continua feita só por `run_id` e `task_id` (com `source`,
   `batch_id` quando aplicável). Isso não é uma capacidade nova cortada — é
   reconhecer que o campo nunca foi implementado nem tem uso distinto do
   `run_id`.
3. **A transformação passa a emitir um evento por lote**, no mesmo padrão de
   `ExtractionBatchLogEvent`/`LoadBatchLogEvent` (uma classe fechada, sem
   registros, com `run_id`, `task_id`, `source`, `batch_id`,
   `accepted_count`, `rejected_count`, `duplicate_count`, `duration_ms`).
   Fica para OB-04 implementar; esta decisão só fixa que a simetria entre as
   quatro etapas exige essa classe existir — hoje a transformação é a única
   das quatro sem evento próprio.

## O que esta decisão não entrega

- **Não troca Elastic Stack por Prometheus/OpenTelemetry/Grafana.** Essa
  comparação já foi feita e decidida no ADR 0001 e em
  `visao-tecnologia-etl.md`; nenhum fato novo do OB-01 justifica reabri-la.
- **Não implementa tracing distribuído (spans).** "Traces" em OB-07
  significa eventos de log correlacionados por `run_id`/`task_id`
  consultáveis no Kibana, não instrumentação de spans (APM). Se o grupo
  quiser tracing de verdade, é uma decisão nova, fora desta sprint.
- **Não define política de retenção nem alertas além do mínimo.** OB-08 cobre
  só uma regra de alerta em falha ou fila parada; dimensionamento,
  retenção do Elasticsearch e canais de notificação (e-mail, Slack, etc.)
  ficam fora do que esta decisão cobre.
- **Não corrige o acoplamento de identidade do ADR 0002** nem qualquer outro
  item pendente de sprints anteriores — esta decisão é só sobre os três
  pontos do padrão de observabilidade listados acima.
- **Não garante que `task_id` do Prefect sobrevive a execução fora do
  Prefect.** Os testes/smoke que rodam fora de um flow (chamando extratores
  diretamente) precisam de um `task_id` de substituição documentado por
  OB-10/OB-11 quando não houver contexto de execução do Prefect.

## Consequências

### Positivas

- OB-03/OB-04 têm uma definição única de `task_id` para implementar, em vez
  de decidir isso durante o código.
- A simetria entre as quatro etapas (mesmo formato de evento) deixa de ser um
  objetivo vago de OB-04 e vira um contrato concreto (`TransformationBatchLogEvent`
  espelhando as duas classes já existentes).
- Remover `event_id` do padrão evita manter documentação prometendo um campo
  que nunca existiu no código, o que já causava divergência entre o ADR 0001
  e a implementação real (achado do OB-01).

### Negativas e riscos

- Trocar o `task_id` de um rótulo estável (por fonte) para um identificador
  de execução do Prefect (por tentativa) muda o que já está gravado nos
  testes e fixtures que hoje comparam `task_id` literal
  (`task_id=f"extract-{self.source}"`); OB-03/OB-04 precisam atualizar essas
  asserções, não só adicionar código novo.
- `task_run.id` do Prefect só existe dentro de uma execução orquestrada; código
  chamado fora de uma task (testes unitários diretos, scripts de smoke sem
  flow) não tem esse valor disponível e precisa de um `task_id` alternativo —
  ponto que fica registrado como pendência para OB-10/OB-11, não resolvido
  aqui.
- Ratificar sem reabrir a escolha de stack não resolve o fato de que nenhuma
  dependência de Elastic Stack está no `requirements.txt` nem no
  `docker-compose.yml` — essa lacuna continua sendo trabalho de OB-07, não
  desta decisão.

## Alternativas consideradas

| Alternativa | Avaliação |
| :--- | :--- |
| Reabrir a escolha de stack (Prometheus/OpenTelemetry vs. Elastic Stack) | Não selecionada: nenhum achado do OB-01 aponta limitação da Elastic Stack em si — as três divergências são de implementação do padrão já decidido, não da tecnologia escolhida. Reabrir gastaria a Sprint 4 redecidindo o que a Sprint 3 já fechou. |
| Manter `task_id` como rótulo fixo por fonte e criar um campo novo (`attempt_id`) para identificar a tentativa | Adicionaria um quarto identificador de correlação além de `run_id`/`task_id`/`batch_id`, sem eliminar a ambiguidade do nome `task_id` já usado em toda a base e nos requisitos (`requisitos-operacionais-etl.md` já promete correlação por `task_id`, no singular). Não selecionada. |
| Redefinir `task_id` como o `task_run.id` do Prefect | Selecionada: reaproveita um identificador que o próprio orquestrador já gera por tentativa, sem inventar um mecanismo novo de geração ou persistência. |
| Manter `event_id` no padrão e implementá-lo como campo separado do `run_id` | Seria trabalho novo para formalizar uma distinção que a implementação atual já resolve fundindo os dois. Não selecionada — sem caso de uso que `run_id` sozinho não cubra. |
| Adiar o evento de transformação para uma sprint futura, mantendo só o agregado no log de orquestração | Deixaria rejeitados/duplicados da transformação sem nenhum destino, o que contraria diretamente o requisito de métricas por etapa (OB-05) e o critério de simetria de OB-04. Não selecionada. |
