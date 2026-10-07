# Smoke operacional do pipeline completo — ponta a ponta no ambiente real

Registro da execução do comando único (backfill → carga analítica →
reconciliação → publicação) no ambiente declarado em `docker-compose.yml`,
executado em 05/10/2026. Cobre fonte, execução, `load_id`, reconciliação,
geração publicada e as sete contagens, além das falhas encontradas e
corrigidas. Nenhum dado sensível: todas as fontes são fixtures sintéticas
versionadas no repositório, e as credenciais citadas são as padrões do
ambiente local de desenvolvimento já documentadas no
[`runbook-execucao.md`](runbook-execucao.md).

## Fonte

Fixtures sintéticas das seis fontes em `scripts/orchestration/fixtures/`
(`pesquisas`, `empresas`, `clientes`, `questoes`, `respondentes`,
`respostas`), geradas a partir de `tests/fixtures` — os mesmos conjuntos da
suíte, que incluem registros inválidos e duplicados de propósito para
exercitar rejeição e deduplicação. Semeadas na área de entrada do MinIO
(`landing/<fonte>.csv`) pelo `run_backfill.py`.

## Execução

Ambiente limpo (volume `duck-data` recém-criado) com MinIO, bucket e
Prefect Server saudáveis:

```bash
docker compose up -d minio createbucket prefect-server

# 1) semeia as seis fixtures e ingere na ordem de dependência (pais antes de filhos)
docker compose run --rm --no-deps runner python scripts/orchestration/run_backfill.py \
  --sources pesquisas empresas clientes questoes respondentes respostas
# BACKFILL: ... todas as seis fontes com status "loaded"

# 2) comando único completo, sem argumentos (destino: ETL_PUBLISH_DIR=/data/publicacao)
docker compose run --rm --no-deps runner python scripts/orchestration/run_pipeline.py
```

A segunda execução demonstra a idempotência por objeto: o backfill interno
reporta as seis fontes como `ignored` (já concluídas no passo 1) e segue
para a carga analítica — nenhum registro é reprocessado.

## Resultado por etapa

| Etapa | Evidência |
| :--- | :--- |
| Backfill | 6/6 fontes concluídas (`loaded` no passo 1; `ignored` na reexecução) |
| Carga analítica | `load_id = e4822482-9a74-4c66-b489-ff5a0e9cec46` — 3 pesquisas, 0 participações, 2 perguntas, 0 órfãos |
| Reconciliação | `reconciled = true`, apontando o mesmo `load_id` da carga |
| Publicação | geração `a90ffbb6ca244e039e4efb94b68d6f25`, `manifest.json` com `load_reference` = `load_id` efetivo e SHA-256 por arquivo; `current.json` trocado atomicamente ao final |

As sete contagens publicadas (linhas por Parquet, conferidas contra o
manifesto):

| Tabela | Linhas |
| :--- | ---: |
| `PUB_C01_CICLO` | 2 |
| `PUB_C02_PARTICIPACAO` | 0 |
| `PUB_C03_PIPELINE_MENSAL` | 0 |
| `PUB_C04_INSTRUMENTO` | 2 |
| `PUB_QUALIDADE_CAMPO` | 64 |
| `PUB_QUALIDADE_RELACAO` | 8 |
| `PUB_QUALIDADE_DUPLICIDADE` | 5 |

`PUB_C02` e `PUB_C03` saem vazios por natureza da fixture, não por falha: o
conjunto sintético aceita uma única resposta (as demais são rejeitadas de
propósito pelas regras de consistência) e nenhum respondente reconciliado,
e o C03 só materializa fechamento mensal quando `--observed-at` informa um
fim de mês observado. A reconciliação valida exatamente esse resultado nas
duas direções (`eligible` = `loaded` em todos os cubos, zero órfãos).

## Falha controlada e reexecução

Com o MinIO parado (`docker compose stop minio`), o mesmo comando termina
com código de saída 1 e a etapa identificada:

```text
PIPELINE FALHOU na etapa backfill: [backfill] HTTPConnectionPool(host='minio', port=9000): ...
```

O marco JSON `orchestration.pipeline.emitted` registra `status=failed` e
`stage=backfill` — observável no coletor como qualquer outro evento. Nada
foi publicado: `current.json` seguiu apontando a geração anterior.

Religado o MinIO, a reexecução do mesmo comando completou normalmente:
`load_id = f7a8da30-cad9-4d3e-8948-66d81862e00a`, `reconciled = true`,
geração nova `3192919a67ff45f58776a65c11cb186d` com **as mesmas sete
contagens** da tabela acima — a reexecução não duplicou fato nenhum
(ingestão idempotente, fatos substituídos na mesma transação). As duas
gerações permanecem íntegras no destino, e `current.json` aponta a mais
recente:

```text
/data/publicacao/
├── a90ffbb6ca244e039e4efb94b68d6f25/   # geração do smoke
├── 3192919a67ff45f58776a65c11cb186d/   # geração da reexecução pós-falha
└── current.json                        # -> 3192919a67ff45f58776a65c11cb186d
```

## Falhas encontradas e corrigidas

1. **Fixtures incompletas para o fluxo ponta a ponta** — o runner só
   versionava `empresas.csv` e `pesquisas.csv`; o smoke das seis fontes não
   tinha insumo para `clientes`, `questoes`, `respondentes` e `respostas`.
   Correção: os quatro CSVs sintéticos foram gerados de `tests/fixtures` e
   versionados em `scripts/orchestration/fixtures/`, alinhando o runner à
   suíte.
2. **Indisponibilidade do MinIO durante a execução** (induzida para o
   teste): tratada pelo próprio comando — falha rápida com etapa
   identificada, código de saída 1, evento de observabilidade e reexecução
   segura após a correção, como registrado acima. Nenhum ajuste de código
   foi necessário.
