# BI-05: conferência da geração final

As consultas e capturas Desktop deste registro são do snapshot anterior ao
CF-05. Seus resultados históricos 18 entradas/17 estados "Sem dado" não
representam o catálogo atual: 19 entradas/18 "Sem dado", com I16 bloqueado.
A execução Desktop após CF-04/CF-05 e o aceite final permanecem pendentes.

CB-16 publicou a geração `6b1eaa686aac43b18b6d6545e1c2c5f1` da fonte v3,
com `load_reference` `afcde424-45e8-457b-8793-bf0866d142b2`.
A publicação foi conferida contra o DuckDB e a geração v3 foi atualizada e
consultada no Desktop. Os recibos históricos e o ensaio do pacote corrigido estão registrados
abaixo, com a revisão executada identificada em cada rodada. O fixture BI-02 e snapshots
históricos têm evidências separadas.

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

## Atualização do verificador em CF-07

O conferidor e o publicador passam a compartilhar `publication_report` e
`publication_specification` para contexto, consultas efetivas e escopo de
qualidade. O conferidor continua validando arquivos, hashes, colunas,
contagens, metadados e recibos; a consulta de referência das tabelas de
qualidade é compartilhada com o publicador. Os testes diretos de duas cargas
calculam os resultados esperados de cada população sem usar essa consulta
como oráculo. Consulte [populações de qualidade](qualidade-snapshot-respondentes.md).

As capturas e os recibos históricos abaixo conservam a revisão e a geração
originalmente executadas. Os testes de CF-07 não constituem uma nova atualização
nem execução no Desktop.

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

## Publicação v3 conferida contra a origem

O [recibo de preparação](evidencias/bi05/publicacao-v3-conferida.json) registra
a comparação da geração CB-16 com o banco estável da mesma carga. O
conferidor executado corresponde ao código de `3d926e0`. A conferência inclui
esquemas, hashes, sete contagens e os fingerprints da última carga analítica.

| Tabela | Linhas publicadas | Total da métrica ou estado |
| --- | ---: | --- |
| `PUB_C01_CICLO` | 57 | 366 pesquisas |
| `PUB_C02_PARTICIPACAO` | 32 | 17740 participações |
| `PUB_C03_PIPELINE_MENSAL` | 0 | Sem fechamento observado, estoque indisponível |
| `PUB_C04_INSTRUMENTO` | 45 | 3186 associações pesquisa-pergunta |
| `PUB_QUALIDADE_CAMPO` | 64 | Contagens conferidas |
| `PUB_QUALIDADE_RELACAO` | 8 | Contagens conferidas |
| `PUB_QUALIDADE_DUPLICIDADE` | 5 | Contagens conferidas |

A [entrega CB-16](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/merge_requests/293)
inclui a reconciliação e a verificação independente de métricas da ingestão,
sem usar a consulta do publicador. Este recibo de preparação não incorpora
uma execução Desktop. O recibo adicional abaixo registra essa consulta
separadamente.

## Refresh v3 executado, antes dos ajustes do relatório

O [recibo Desktop v3](evidencias/bi05/desktop-v3-antes-ajustes-relatorio.json)
registra a consulta às 14:15:30 UTC de 06/10/2026, no Desktop `2.158.1177.0`,
Windows `10.0.26200.0`. As sete contagens e totais coincidem com a tabela
anterior; C03 retornou estado sem fechamento observado e valor nulo.
Validação teve média 8,55 dias com base 20; preenchimento ficou nulo com
base 0. O catálogo do snapshot anterior ao CF-05 manteve 18 linhas e 17 estados sem dado.

A [conferência do recibo](evidencias/bi05/conferencia-desktop-v3.json) passou
contra o DuckDB e o manifesto da mesma carga, a revisão esperada `f068a01`
e o inventário independente do pacote. O engine e o TMDL conferido tiveram
128 itens de projeção semântica iguais, sem diferenças. O parâmetro local foi
conferido à parte do hash de arquivos; sua expressão integra a projeção TOM.

Esta execução antecede a correção dos títulos e a aceitação visual do
relatório integrado. Ela comprova o refresh e as consultas do modelo
registrado; não aceita uma revisão futura ainda não executada. O campo
`final_acceptance` do conferidor continua pendente porque não decide o
aceite global do relatório nem expõe um commit exato dentro do engine.

## Execução final do pacote integrado

A revisão executada foi `ff760d6552a1d5d2d3d9d9da1f3467e2c913416a`, pacote SHA256
`a9b087e5a9e4e0d56af8d7b36fe0a687857b205e7c59b6dbd44c9dd7c2358cea`, inventário SHA256
`1624eef9ad87a61af4146cc0c67e469014cb830829bc9562a04ba70eaeca8ac6`, com 98 arquivos conferidos no Windows.
O fixture corrigido foi consultado em `2026-10-06T15:44:25.2528117Z` e a v3 em
`2026-10-06T15:49:13.5533810Z`, no Desktop real `2.158.1177.0`, Windows
`10.0.26200.0`, por automação em VM. O parâmetro local foi conferido
por arquivo e pela expressão no modelo ativo. As 13 partições do projeto
e duas automáticas de data estavam processadas sem erro. A comparação TOM
teve 128 itens e zero diferenças. Ela compara a projeção semântica
declarada; não fornece um marcador do commit exato dentro do engine.
O SHA do pacote executado permanece distinto dos commits documentais
posteriores anexados às MRs.

### Reproduzir a fonte do PBIP

A revisão executada está [no GitLab](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/tree/ff760d6552a1d5d2d3d9d9da1f3467e2c913416a).
Busque a branch de validação e abra essa revisão em uma pasta ainda
inexistente, preservando o checkout de trabalho:

```bash
git fetch origin test/bi-desktop-integrated
git worktree add --detach ../bi-pacote-conferido ff760d6552a1d5d2d3d9d9da1f3467e2c913416a
```

O inventário compara os arquivos versionados de `powerbi/`, exceto
`powerbi/CentralPesquisasBI.SemanticModel/definition/expressions.tmdl`,
cujo parâmetro foi adaptado somente na cópia privada Windows. O parâmetro
tem conferência própria por arquivo e expressão no modelo ativo.
Esse checkout reproduz a fonte PBIP e seu inventário; a geração Parquet
autorizada e o ZIP conferido permanecem privados.

O [recibo final v3](evidencias/bi05/desktop-v3-final.json) registra
57/32/0/45/64/8/5 linhas e totais C01/C02/C04 de 366/17740/3186,
iguais ao manifesto e ao DuckDB autorizado da mesma carga. C03 tem
estado sem fechamento observado, estoque e fluxos indisponíveis.
A [conferência final](evidencias/bi05/conferencia-desktop-v3-final.json)
usa a revisão esperada e o inventário independente acima. O campo
`final_acceptance: pendente` é mantido porque o conferidor não decide
o aceite global do relatório; as verificações de runtime e proveniência
registradas passaram separadamente.
