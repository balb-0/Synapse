# ADR 0003 — Execução local e integração contínua do ETL

- **Status:** Proposto
- **Data:** 10/09/2026
- **Responsáveis pela decisão:** equipe do projeto
- **Complementa:** [ADR 0001](0001-arquitetura-etl-python-prefect-minio-duckdb.md)

## Contexto

O [ADR 0001](0001-arquitetura-etl-python-prefect-minio-duckdb.md) define as
tecnologias do pipeline, mas não registra como o fluxo é executado no ambiente
local nem o que a integração contínua verifica. O enunciado da Sprint 3 exige
Integração Contínua e exclui explicitamente o Deploy Contínuo, de modo que a
ausência de uma decisão registrada deixaria o item sem justificativa.

O repositório já contém as duas respostas na prática, sem que elas tivessem sido
declaradas como decisão:

- a execução local acontece por `docker-compose.yml`, com MinIO e um runner
  Python, e o agendamento é servido em processo por `flow.serve()`, não por um
  servidor Prefect;
- a integração contínua é do GitLab, com um único job declarado em
  `.gitlab/ci/transformation.yml`, cujo próprio cabeçalho registra que é o gate
  da tarefa MG-10 e que a consolidação pertence à VB-07.

Registrar essa situação é necessário porque ela tem consequências que a equipe
precisa aceitar conscientemente: três das quatro camadas do ETL não passam por
nenhuma verificação automática, e a versão do Python usada para verificar o
código não é a mesma usada para executá-lo.

## Decisão

**A execução local do ETL é feita por contêineres declarados no repositório, e a
integração contínua é o pipeline do GitLab, sem qualquer etapa de entrega ou
implantação automática.**

Decorrem daí:

1. O ambiente local é definido por `docker-compose.yml`, com três serviços:
   `minio` (armazenamento de objetos e console), `createbucket` (criação do
   bucket `sindusfarma`) e `runner` (imagem construída pelo `Dockerfile`, com o
   código montado em volume).
2. O agendamento usa `ingest_object.serve(...)` em
   `scripts/orchestration/deployment.py`, com cron `0 3 * * *`. Não há servidor
   Prefect, agente nem worker remoto no ambiente declarado.
3. A execução sob demanda usa `scripts/orchestration/run_ingest.py` e
   `scripts/orchestration/run_backfill.py`, que semeiam fixtures no MinIO e
   chamam os flows com parâmetros explícitos.
4. A integração contínua é o GitLab CI, incluída por `.gitlab-ci.yml` a partir de
   `.gitlab/ci/transformation.yml`, e executa, em `python:3.11-slim`: `ruff
   check`, `ruff format --check`, `render_schema.py --check`, `coverage run` sobre
   `unittest discover` e `coverage report --fail-under=90`.
5. Os testes são escritos com `unittest` da biblioteca padrão e executados por
   `python -m unittest discover -s tests`, com `PYTHONPATH=src`. O projeto não
   adota `pytest`.
6. **Deploy Contínuo fica fora do escopo.** Nenhum job publica imagem, aplica
   migração, sobe ambiente ou promove versão. A entrega da sprint é o pipeline
   executado localmente, com evidência versionada.

## O que ainda não está feito

O job de CI cobre exclusivamente `etl.transformation`. As camadas de extração,
carga e orquestração não são verificadas por lint nem por cobertura, embora
tenham testes que passam quando executados localmente. Consolidar o pipeline é a
tarefa VB-07, que ainda não tem trabalho no repositório.

A versão do Python está declarada em quatro lugares e diverge: `Dockerfile` usa
`python:3.12-slim`, o job de CI usa `python:3.11-slim`, `ruff-transformation.toml`
declara `target-version = "py311"` e o `README.md` registra 3.12+. As
dependências de runtime em `requirements.txt` são faixas, não versões fixas, o
que impede reproduzir exatamente o ambiente de uma execução anterior.

Não existe verificação automática que impeça o versionamento de dado pessoal ou
de segredo, apesar de a regra estar registrada em
[`dev-rules.md`](../dev-rules.md) e em [`gestao-configuração.md`](../gestao-configuração.md).

## Consequências

### Positivas

- O ambiente local sobe com um comando e não depende de serviço hospedado nem
  de credencial do parceiro.
- O gate de transformação já impede regressão na camada com mais regras de
  negócio, com limite de cobertura declarado.
- A ausência de servidor Prefect reduz o custo operacional da entrega
  acadêmica e mantém o histórico de runs disponível localmente.
- Excluir o Deploy Contínuo evita apresentar como capacidade algo que o
  enunciado não pede e que a equipe não tem ambiente para sustentar.

### Negativas e riscos

- Três das quatro camadas do ETL podem regredir sem que o CI perceba.
- Verificar o código em Python 3.11 e executá-lo em 3.12 permite que uma
  incompatibilidade apareça apenas em execução.
- Sem pin de dependência, uma atualização de `prefect`, `duckdb` ou `minio`
  pode alterar o comportamento do pipeline sem nenhuma mudança no repositório.
- `flow.serve()` mantém o agendamento apenas enquanto o processo estiver vivo;
  não há recuperação automática do agendamento após uma parada.
- O ambiente declarado não inclui a Elastic Stack, então a observabilidade
  prevista no ADR 0001 não pode ser exercitada por ele.

## Alternativas consideradas

| Alternativa | Avaliação |
| :--- | :--- |
| Servidor Prefect em contêiner, com worker e fila | Aproxima o ambiente local de uma implantação real e preserva o agendamento entre reinícios. Não foi selecionada nesta entrega por acrescentar serviço, banco de estado e configuração sem que o enunciado exija implantação. |
| Pipeline de CI único cobrindo as quatro camadas | É o destino desejado e permanece como VB-07. Não foi registrada como decisão já tomada porque o job correspondente não existe no repositório, e declará-lo aqui criaria evidência inexistente. |
| Adotar `pytest` no lugar de `unittest` | Traria fixtures e parametrização mais expressivas. Não foi selecionada porque os 19 módulos existentes usam `unittest`, o CI já o invoca, e a troca criaria migração sem ganho para o escopo da sprint. |
| Incluir Deploy Contínuo | Rejeitada: o enunciado exclui o CD do escopo da sprint. |

## Critérios para ratificar a decisão

- o grupo aprovar o ambiente local declarado como ambiente de referência da
  entrega;
- o pipeline de CI passar a cobrir `extraction`, `load` e `orchestration`
  (VB-07), ou a cobertura parcial ser aceita explicitamente como limitação;
- a versão do Python ser unificada entre `Dockerfile`, CI, configuração do ruff
  e `README.md`;
- as dependências de runtime receberem versão fixa ou a faixa ser aceita de
  forma explícita;
- nenhum job do pipeline realizar entrega, publicação ou implantação.
