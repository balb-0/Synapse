# Manual de implementação e reprodução

Este manual permite a uma pessoa parceira instalar e validar a solução em um ambiente novo. Ele cobre o fluxo completo de ETL, os cubos publicados para BI e a atualização do relatório. Todos os comandos devem ser executados a partir da raiz do repositório, salvo indicação contrária.

> **Limite de acesso.** O repositório contém código e fixtures sintéticas, não dados privados. A execução com dados autorizados exige credenciais do MinIO, acesso aprovado ao ambiente e uma pasta privada fora de qualquer repositório Git. Não copie CSVs privados, o DuckDB, `.env` ou uma geração publicada para o Git, chat ou canal não autorizado.

## 1. Pré-requisitos e clonagem

O procedimento destina-se a quem administra a carga ou consome o relatório. A máquina de carga requer Git 2.40+, Python 3.12+, Docker com Docker Compose e espaço para o volume do DuckDB. Para executar os comandos de verificação que usam `jq`, instale também `jq` 1.6+. Para atualizar o relatório, use Windows com Power BI Desktop e acesso de leitura à pasta privada da geração Parquet.

Solicite antes: URL e permissão do repositório, credenciais de menor privilégio para o bucket MinIO, os CSVs autorizados, um local privado para o DuckDB e a geração BI. A conta que atualiza o Power BI não precisa receber o DuckDB nem os CSVs de origem.

```bash
git clone https://git.inteli.edu.br/graduacao/2026-2a/t13/g05.git
cd g05
git checkout develop
git pull --ff-only

python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Para desenvolvimento e execução dos testes locais, instale também `requirements-transformation-dev.txt`. Os arquivos em `tests/fixtures/` são sintéticos e podem ser usados em testes; nunca devem ser confundidos com a base autorizada.

## 2. Configurar e verificar o ETL

Crie a configuração local sem versioná-la. Preencha as chaves reais recebidas da equipe; não substitua credenciais de produção por valores de exemplo.

```bash
cp .env.example .env
# edite .env em editor local e restrito
mkdir -p /caminho/privado/publicacao-bi
```

Configure ao menos `ETL_MINIO_ENDPOINT`, `ETL_MINIO_BUCKET`, `ETL_MINIO_ACCESS_KEY`, `ETL_MINIO_SECRET_KEY` e, quando a carga não usar o volume padrão do Compose, `ETL_DUCKDB_PATH`. Defina `ETL_PUBLISH_DIR` como uma pasta privada fora do checkout; no runner do Compose o padrão é `/data/publicacao`. O banco do runner fica em `/data/warehouse.duckdb`, no volume persistente `duck-data`.

Suba os serviços locais e confira sua saúde:

```bash
docker compose up -d
curl -fsS http://localhost:4200/api/health
docker compose run --rm --no-deps runner \
  python scripts/orchestration/health_check.py
```

O primeiro comando cria, entre outros, MinIO e Prefect. O health check deve encerrar com código zero. Se falhar, corrija endpoint, credenciais, volume ou a indisponibilidade do Prefect antes de processar dados. Consulte [`runbook-execucao.md`](runbook-execucao.md) para diagnóstico e logs.

## 3. Executar a carga, gerar cubos e publicar

O comando abaixo é o caminho operacional padrão: executa backfill, carga analítica, reconciliação e publicação no mesmo banco. A publicação só ocorre quando a reconciliação retornar `reconciled=true`.

```bash
docker compose run --rm --no-deps runner \
  python scripts/orchestration/run_pipeline.py
```

Para uma execução controlada, informe as fontes e o destino de publicação:

```bash
docker compose run --rm --no-deps runner \
  python scripts/orchestration/run_pipeline.py \
  --sources empresas pesquisas \
  --publish-dir /data/publicacao \
  --observed-at 2026-10-31
```

`--sources` aceita um subconjunto na ordem de dependência (pais antes de filhos); sem ele, o runner usa as seis fontes. `--reprocess` ignora o controle de idempotência do objeto para uma recarga planejada. `--observed-at` registra o fechamento observado de C03 e deve ser o último dia do mês.

Em sucesso, o processo retorna código `0` e a última linha de stdout contém `PIPELINE: {"status":"completed", ...}` com status das fontes, `load_id`, reconciliação, geração e linhas publicadas. Em falha, retorna `1`, identifica `backfill`, `load_analytics`, `reconciliation` ou `publication` no stderr e preserva o `current.json` anterior. Corrija a causa e execute o mesmo comando: a ingestão é idempotente, os fatos são substituídos e uma publicação incompleta não troca a geração vigente. Erro de parâmetro retorna `2`.

Após uma execução válida, leia `current.json` em `ETL_PUBLISH_DIR` e use a subpasta indicada por `generation`. Ela deve conter `manifest.json` e estes sete arquivos:

```text
PUB_C01_CICLO.parquet              PUB_C02_PARTICIPACAO.parquet
PUB_C03_PIPELINE_MENSAL.parquet    PUB_C04_INSTRUMENTO.parquet
PUB_QUALIDADE_CAMPO.parquet        PUB_QUALIDADE_RELACAO.parquet
PUB_QUALIDADE_DUPLICIDADE.parquet
```

Confira no manifesto sete entradas, SHA-256 de 64 caracteres e as contagens esperadas. Entregue ao consumidor autorizado somente a subpasta da geração; não entregue DuckDB, CSVs, outras gerações nem `current.json`. O publicador cria a pasta com permissões restritas em sistemas POSIX. As regras de grão, métricas e conferência estão em [`acesso-cubos-bi.md`](acesso-cubos-bi.md).

O DuckDB é um arquivo embutido: o pipeline cria e evolui as estruturas idempotentes necessárias no caminho configurado. Antes de uma alteração de schema, confira que o contrato de ingestão versionado corresponde ao código:

```bash
PYTHONPATH=src python scripts/load/render_ddl.py --check
```

O comando apenas valida o SQL versionado; não substitui a carga analítica nem a reconciliação do pipeline completo.

## 4. Agendar e observar a operação

O serviço `scheduler` mantém `ingest-object/agendado` no Prefect, diariamente às 03:00 no fuso do servidor. Com a stack em execução, publique e confira os deployments manuais se necessário:

```bash
export PREFECT_API_URL=http://localhost:4200/api
prefect work-pool create default --type process
prefect deploy --all
prefect deployment ls
```

A UI do Prefect está em `http://localhost:4200`. Uma execução manual pode ser disparada nela ou pela CLI:

```bash
prefect deployment run 'ingest-object/agendado' \
  -p source=empresas -p bucket=sindusfarma \
  -p key=landing/empresas.csv -p reprocess=true
```

Verifique o resultado pelo código de saída, pelo JSON final e pelo histórico do Prefect. Reexecute somente depois de corrigir uma falha explícita; não apague a geração anterior para "forçar" uma publicação. O histórico e os agendamentos persistem no volume `prefect-data`.

## 5. Atualizar o Power BI em outro ambiente

1. Copie somente a subpasta da geração indicada por `current.json` para uma pasta privada no Windows, por exemplo `C:\dados-privados\publicacao-bi\<generation>`.
2. Abra `powerbi/CentralPesquisasBI.pbip` no Power BI Desktop.
3. Em **Transformar dados → Gerenciar parâmetros**, altere `PastaPublicacaoBI` para o caminho da **subpasta da geração**, sem barra final. Não aponte para a pasta que contém `current.json`.
4. Atualize as consultas e confirme que as sete tabelas foram carregadas. Compare as linhas de cada uma com `manifest.json` da mesma geração e confira pelo menos um agregado por cubo contra a evidência da carga.
5. Ao receber outra geração, copie-a para uma nova subpasta, altere o mesmo parâmetro, atualize e repita as conferências. Não reutilize números do manifesto anterior.

Se o refresh não localizar arquivos, confirme o caminho de `PastaPublicacaoBI`, as permissões da pasta e se a cópia contém os sete Parquet. Indicadores sem dados publicados devem permanecer indisponíveis, não ser exibidos como zero. Consulte [`validacao-acesso-bi.md`](validacao-acesso-bi.md) para o checklist detalhado de totais e limitações do modelo.

## 6. Registro do ensaio independente (MN-06)

Uma pessoa diferente da autora executará esta seção em Windows limpo, sem orientação oral e usando apenas este manual. Preencha os campos abaixo no MR após o ensaio; não inclua credenciais, caminhos privados completos, dados ou identificadores sensíveis.

| Item | Evidência do ensaio |
| :--- | :--- |
| Data, responsável e ambiente | _Pendente de ensaio independente_ |
| Commit/ref reproduzido | _Pendente_ |
| Health check e comando do pipeline | _Pendente_ |
| `load_id` e geração (não sensíveis) | _Pendente_ |
| Sete contagens versus manifesto | _Pendente_ |
| Refresh no Power BI e total por cubo | _Pendente_ |
| Divergências encontradas e correções | _Pendente_ |
| Resultado final | _Pendente_ |

Se houver passo ausente, ambíguo ou não reproduzível, registre a divergência, corrija este manual no mesmo MR e repita somente as etapas afetadas. MN-06 só é concluída quando o ensaio registrar resultado reproduzível e o relatório for atualizado com uma geração autorizada ou, quando aplicável, sintética explicitamente identificada.
