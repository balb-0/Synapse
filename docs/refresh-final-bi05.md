# BI-05: conferência da geração final

O ID da geração final CB16 e o banco DuckDB correspondente ainda precisam ser
informados pelo responsável pela carga. Não substitua essa geração pelo fixture
BI-02 nem por contagens de um snapshot histórico.

## Conferir a publicação

Use a subpasta imutável indicada por `current.json` da publicação autorizada e
o arquivo DuckDB da **mesma carga**. O comando abre o banco em modo somente leitura:

```bash
PYTHONPATH=src:. python -m scripts.analytics.conferir_geracao_bi \
  --geracao /caminho/privado/publicacao-bi/ID_DA_GERACAO \
  --database /caminho/privado/analitico.duckdb \
  > /caminho/privado/conferencia-bi05.json
```

Saída zero significa que o manifesto declara exatamente sete tabelas, os nomes
das colunas, linhas e SHA256 batem com os arquivos, e as contagens batem com as
consultas da origem. O conferidor compara os totais C01, C02 e C04 com a
contagem dos respectivos fatos. Para C03, compara o estoque em cada fechamento
mensal separadamente. Não soma estoques de meses distintos. Um resultado
`c03_observation: sem_fechamento_observado_na_publicacao` significa que a
publicação não contém fechamento observado; ele não comprova estoque zero.

Uma falha imprime JSON com `preparation.status: falha`, `error` e saída 1. O
campo `final_acceptance` continua `pendente`, mesmo quando a preparação passa.
Quando o banco contém `analytics_load_run`, o conferidor exige que
`load_reference` seja o ID da última carga analítica e confere os fingerprints
das quatro fontes correntes e o checksum da fonte de respondentes selecionada.
O JSON registra `source_control.status: confere`. Sem essa tabela, registra
`sem_controle_de_carga_disponivel`; os arquivos e cubos ainda são comparados,
mas o vínculo à execução de carga fica sem prova. O ID no manifesto, sozinho,
não comprova que a carga é a final CB16 autorizada.

## Conferir no Power BI Desktop

No Windows, abra `powerbi/CentralPesquisasBI.pbip`, aponte
`PastaPublicacaoBI` para a **mesma** subpasta de geração, aplique e atualize as
sete partições. Registre versão do Desktop, data, erros e evidência da execução.
Execute `COUNTROWS` nas sete tabelas e **ao menos um agregado por cubo**. Para
C01, C02 e C04, use o total de linhas dos fatos publicado em suas colunas de
quantidade. Para C03, filtre um único fechamento observado:

```dax
EVALUATE ROW("Total C01", SUM(PUB_C01_CICLO[qtd_pesquisas]))
EVALUATE ROW("Total C02", SUM(PUB_C02_PARTICIPACAO[qtd_participacoes]))
EVALUATE ROW("Estoque C03", CALCULATE(SUM(PUB_C03_PIPELINE_MENSAL[qtd_pesquisas_no_status]), PUB_C03_PIPELINE_MENSAL[data_fim_mes] = DATE(2026, 2, 28)))
EVALUATE ROW("Total C04", SUM(PUB_C04_INSTRUMENTO[qtd_perguntas]))
```

Substitua a data de exemplo pelo fechamento da geração. Se C03 não contiver
fechamento observado, registre estado indisponível e valor nulo. Transcreva os
resultados em um recibo JSON privado. Os textos entre `<>` são marcadores e
devem ser trocados por números reais antes da execução do conferidor:

```json
{
  "generation": "ID_DA_GERACAO",
  "load_reference": "ID_DA_CARGA_NO_MANIFESTO",
  "project_source_commit": "SHA_GIT_COMPLETO_DO_PACOTE_PBIP",
  "package_sha256": "SHA256_DO_ZIP_CONFERIDO_NO_WINDOWS",
  "model_inventory_sha256": "SHA256_DO_INVENTARIO_CONFERIDO_NO_WINDOWS",
  "verified_model_files": "<número de arquivos conferidos>",
  "tables": {
    "PUB_C01_CICLO": "<contagem C01>",
    "PUB_C02_PARTICIPACAO": "<contagem C02>",
    "PUB_C03_PIPELINE_MENSAL": "<contagem C03>",
    "PUB_C04_INSTRUMENTO": "<contagem C04>",
    "PUB_QUALIDADE_CAMPO": "<contagem qualidade campo>",
    "PUB_QUALIDADE_RELACAO": "<contagem qualidade relação>",
    "PUB_QUALIDADE_DUPLICIDADE": "<contagem qualidade duplicidade>"
  },
  "aggregates": {
    "PUB_C01_CICLO": {"column": "qtd_pesquisas", "value": "<total C01>"},
    "PUB_C02_PARTICIPACAO": {"column": "qtd_participacoes", "value": "<total C02>"},
    "PUB_C03_PIPELINE_MENSAL": {"column": "qtd_pesquisas_no_status", "month_end": "<AAAA-MM-DD>", "value": "<estoque do mês>"},
    "PUB_C04_INSTRUMENTO": {"column": "qtd_perguntas", "value": "<total C04>"}
  }
}
```

Para C03 sem fechamento, substitua sua entrada por
`{"column":"qtd_pesquisas_no_status","state":"sem_fechamento_observado","value":null}`.
Execute novamente com o recibo e a revisão esperada do pacote:

```bash
PYTHONPATH=src:. python -m scripts.analytics.conferir_geracao_bi \
  --geracao /caminho/privado/publicacao-bi/ID_DA_GERACAO \
  --database /caminho/privado/analitico.duckdb \
  --desktop /caminho/privado/recibo-desktop.json \
  --model-source-commit SHA_GIT_COMPLETO_DO_PACOTE_PBIP \
  --package-receipt /caminho/privado/package-receipt.json
```

O resultado `desktop.status: recibo_confere` compara os sete números e os
quatro agregados com a publicação e o banco. O recibo deve informar `load_reference`
exatamente igual ao manifesto; referência ausente ou diferente causa falha,
mesmo quando as contagens coincidem. `project_source_commit` deve coincidir
com o SHA completo informado em `--model-source-commit`.

`--package-receipt` recebe o inventário independente preparado antes de copiar
o pacote para Windows, com `version: 1`, `source_commit`, `package_sha256`,
`model_file_count`, `model_file_sha256` e `model_inventory_sha256`. O hash do
inventário usa as linhas `caminho SHA256\n` em ordem lexicográfica, codificadas
em UTF-8. A consulta no Windows confere o ZIP e cada arquivo extraído e registra
o hash do pacote, hash do inventário e quantidade de arquivos no recibo Desktop.
O conferidor exige que esses valores coincidam com o inventário independente.
Não preencha esses campos apenas copiando o recibo esperado: conserve a
evidência da conferência efetiva dos arquivos no Windows.

Sem a revisão esperada ou sem o inventário independente, as contagens podem
conferir, mas `desktop.status` fica
`metricas_conferem_proveniencia_pendente`. O resultado registra separadamente
a comparação dos arquivos de origem em `desktop.provenance`. A revisão
carregada pelo engine continua `nao_comprovada`: ADOMD não expõe o SHA do código
carregado. O recibo, isoladamente, não prova o refresh no aplicativo; mantenha
a evidência da execução e abertura do pacote conferido junto dele.

Quando a consulta Windows também compara o TMDL conferido com o modelo ativo
via TOM, registre `engine_semantic_projection_verified: true` e
`engine_model_verification`. O conferidor exige `status: matched`, SHA256 de
origem e engine iguais, contagens positivas e iguais de itens, zero diferenças,
lista vazia de diferenças e escopo descrito. Esse resultado fica separado em
`desktop.provenance.engine_semantic_projection: recibo_confere`. A igualdade
da projeção semântica declarada não identifica o commit exato dentro do engine.
Sem essa evidência, o campo fica `nao_conferida`; um flag sozinho não comprova
a comparação. A conferência dos recibos continua exigindo evidência da
execução efetiva das consultas e do refresh.

Para ensaio local com o fixture, use `--sintetico`. Essa opção apenas permite
conferir um `load_reference` iniciado por `synthetic`; o resultado mantém
`synthetic: true` e `final_acceptance: pendente`. A aceitação final exige a
geração CB16 autorizada, a conferência da publicação, o refresh real no Desktop
e a evidência de que ambos usaram a mesma carga.
