# ADR 0006 — Observabilidade estruturada do ETL

- **Status:** Proposto
- **Data:** 24/09/2026
- **Responsável pela decisão:** equipe de dados
- **Complementa:** [ADR 0001](0001-arquitetura-etl-python-prefect-minio-duckdb.md)

## Contexto

O ETL já produz estados de execução no Prefect, registros de carga no DuckDB e
eventos estruturados por lote. Esses sinais são suficientes para diagnóstico
local, mas ainda não existe transporte para um coletor, índice central,
painel ou alerta no ambiente versionado. A Sprint 4 precisa definir como esses
sinais serão correlacionados sem transformar a telemetria em requisito para a
confirmação de uma carga válida.

A decisão deve preservar a separação entre o plano de controle do Prefect, os
dados de negócio no DuckDB e os eventos operacionais. Também deve evitar dados
pessoais e conteúdo bruto nos logs.

## Alternativas consideradas

| Alternativa | Avaliação |
| :--- | :--- |
| Usar somente o histórico do Prefect e os registros do DuckDB | Tem baixo custo operacional, mas fragmenta o diagnóstico e não oferece consulta, painel e alertas centralizados. |
| Prometheus e Grafana para métricas, mantendo logs locais | É uma combinação válida, porém cria dois caminhos de investigação e diverge do padrão Elastic Stack já ratificado no ADR 0001. |
| Logstash, Elasticsearch e Kibana para eventos operacionais estruturados | Selecionada por concentrar transporte, pesquisa, painéis e alertas no padrão já adotado pelo projeto. |

## Decisão

Adotar a **Elastic Stack** como destino da observabilidade centralizada, com o
seguinte fluxo lógico:

1. cada etapa emite evento JSON estruturado para uma interface de telemetria;
2. o Logstash recebe e normaliza os eventos;
3. o Elasticsearch indexa os eventos operacionais;
4. o Kibana oferece consultas, painel e regras de alerta.

Os sinais mínimos são:

- identidade: `run_id`, `batch_id`, fonte e objeto;
- execução: etapa, tentativa, instante, duração e estado final;
- volume: linhas lidas, aceitas, rejeitadas e duplicadas;
- resiliência: tipo de falha, retentativa e esgotamento de tentativas;
- reconciliação: resultado e divergências, sem copiar registros de negócio.

O transporte é **assíncrono em relação à confirmação da carga**. Uma falha no
coletor deve ser registrada localmente, mas não desfaz uma transação válida nem
confirma uma transação inválida. O checkpoint continua condicionado ao commit
e à reconciliação do lote, nunca à disponibilidade da Elastic Stack.

Os eventos não incluem payload bruto, e-mail, resposta individual ou segredo.
A retenção e os perfis de acesso precisam ser parametrizados antes de qualquer
implantação fora do ambiente controlado.

## Justificativa

A escolha mantém um único caminho de consulta para logs e indicadores
operacionais, preserva a correlação já fornecida por `run_id` e `batch_id` e
ratifica a tecnologia registrada no ADR 0001. O desacoplamento impede que uma
indisponibilidade observacional altere a consistência do dado tratado.

## Consequências

### Positivas

- falhas, retentativas, volumes e duração podem ser correlacionados por lote;
- painéis e alertas usam o mesmo conjunto de eventos consultável;
- o contrato de telemetria pode ser testado sem executar toda a infraestrutura.

### Negativas e riscos

- a pilha aumenta consumo de memória, armazenamento e manutenção;
- eventos podem ser perdidos enquanto o coletor estiver indisponível, pois esta
  decisão não introduz uma fila durável;
- campos e retenção precisam de governança para evitar exposição indevida ou
  crescimento ilimitado do índice.

## Limite de implantação

Esta ADR define o contrato e a topologia-alvo. Ela **não afirma que Logstash,
Elasticsearch, Kibana, painéis ou alertas estejam implantados**, nem autoriza
publicação automática em produção. O repositório continua representando um
ambiente local/versionado; implantação produtiva exige configuração, segredos,
capacidade, retenção, controles de acesso e aprovação operacional próprios.
