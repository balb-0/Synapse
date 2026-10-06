# Validação de acesso ponta a ponta ao BI

Cumpre a DX-04: conectar o Power BI aos cubos publicados e confirmar que uma
máquina nova, seguindo só o procedimento documentado, chega às mesmas
contagens do repositório analítico. O procedimento de publicação e conexão já
está em [`docs/acesso-cubos-bi.md`](acesso-cubos-bi.md) (CB-09); este
documento é o checklist de validação e o gap-check entre o que o catálogo de
indicadores espera e o que a publicação realmente entrega, depois da extensão
de qualidade da DX-09.

## O que mudou desde `acesso-cubos-bi.md`

A DX-09 acrescentou três arquivos à publicação (`PUB_QUALIDADE_CAMPO`,
`PUB_QUALIDADE_RELACAO`, `PUB_QUALIDADE_DUPLICIDADE`) ao lado dos quatro
cubos originais. `src/etl/analytics/publish.py` já os publica automaticamente
— o comando de publicação não muda, só a contagem de arquivos gerados passa
de 4 para 7:

```bash
PYTHONPATH=src python -m etl.analytics.publish \
  --database /caminho/privado/ingestao.duckdb \
  --output /caminho/privado/publicacao-bi \
  --load-reference run-YYYY-MM-DD-NN
```

## Checklist de validação ponta a ponta

Execute em uma máquina que **não** participou da carga (ou em uma pasta
limpa), só com o pacote de geração recebido, conforme
`docs/acesso-cubos-bi.md`:

1. **Publicar** (na máquina de carga): rodar o comando acima após uma carga
   conciliada; confirmar que `manifest.json` lista sete entradas em
   `"tables"` (as quatro de `docs/acesso-cubos-bi.md` mais as três de
   qualidade) e que cada uma tem `sha256` de 64 caracteres.
2. **Copiar só a subpasta da geração** (indicada por `current.json`) para a
   máquina de teste — nunca o DuckDB, nunca `current.json` sozinho.
3. **Abrir os sete Parquet no Power BI Desktop** via *Obter dados → Parquet*,
   um a um.
4. **Conferir linhas contra o manifesto**: para cada arquivo, o número de
   linhas carregado no Power BI bate com `manifest.json → tables → <nome> →
   rows`. Divergência aqui é falha de cópia ou de versão, não do modelo.
5. **Conferir totais contra o repositório analítico** (passo que
   `acesso-cubos-bi.md` não cobria): comparar pelo menos um total de cada
   cubo com uma consulta direta no DuckDB de origem (ou com
   `docs/resultados_analise.txt`, quando o recorte coincidir) — não basta a
   contagem de linhas do Parquet bater, o **valor agregado** também precisa
   bater. Exemplo: `SUM(qtd_pesquisas)` de `PUB_C01_CICLO` sem filtro deve
   igualar a contagem de pesquisas correntes em `ingestao_pesquisas_atual`.
6. **Registrar o resultado** (data, geração, máquina, sete contagens e o
   total conferido) no mesmo lugar onde a equipe já guarda evidência de
   validação (`docs/gate-final-sprint3.md` é o precedente de formato).

## Gap-check: indicador esperado × coluna publicada

Este é o resumo executável de
[`docs/indicadores-publicaveis-bi.md`](indicadores-publicaveis-bi.md) (DX-01)
para quem só quer saber, antes de montar relacionamento ou medida (DX-05 em
diante), o que a publicação atual sustenta:

| Cubo publicado | Sustenta hoje | Não sustenta hoje |
| :-- | :-- | :-- |
| `PUB_C01_CICLO` | Portfólio, distribuição, média de duração por fase | Taxa de prorrogação (I05) — falta `flag_prorrogada` |
| `PUB_C02_PARTICIPACAO` | Contagem de participações, média de preenchimento | Empresas distintas por pesquisa (I07), representatividade/participação de mercado (I09) |
| `PUB_C03_PIPELINE_MENSAL` | Estoque mensal por status/área/tipo/perfil | Entradas e saídas do mês (I05x) — coluna existe mas está sempre `NULL` sem histórico de transições |
| `PUB_C04_INSTRUMENTO` | Perguntas por área e tipo | Distribuição de respostas (I12), respondentes distintos (I13) |
| `PUB_QUALIDADE_CAMPO` | Completude de preenchimento (todas as linhas por campo) | Completude aplicável (I16) — regras homologadas não publicadas |
| `PUB_QUALIDADE_RELACAO` | Integridade referencial (I18) | — |
| `PUB_QUALIDADE_DUPLICIDADE` | Taxa de duplicidade (I17) | — |
| *(nenhum arquivo)* | — | Parseabilidade (I19), divergência de título (I20) — sem consulta publicada nesta rodada |

Todo indicador da coluna "Não sustenta hoje" precisa entrar no Power BI pelo
mecanismo de sinalização da DX-10 (motivo textual, nunca zero), não por uma
estimativa.
