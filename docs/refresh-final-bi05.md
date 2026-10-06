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
O `load_reference` e o ID no manifesto ajudam a identificar a geração, mas não
comprovam, sozinhos, que o banco e os arquivos vieram da carga final CB16.

## Conferir no Power BI Desktop

No Windows, abra `powerbi/CentralPesquisasBI.pbip`, aponte
`PastaPublicacaoBI` para a **mesma** subpasta de geração, aplique e atualize as
sete partições. Registre versão do Desktop, data, erros e evidência da execução.
Execute `COUNTROWS` nas sete tabelas. Execute pelo menos uma consulta DAX de
agregado, por exemplo:

```dax
EVALUATE ROW("Total C01", SUM(PUB_C01_CICLO[qtd_pesquisas]))
```

Transcreva os resultados em um recibo JSON privado:

```json
{
  "generation": "ID_DA_GERACAO",
  "tables": {
    "PUB_C01_CICLO": 0,
    "PUB_C02_PARTICIPACAO": 0,
    "PUB_C03_PIPELINE_MENSAL": 0,
    "PUB_C04_INSTRUMENTO": 0,
    "PUB_QUALIDADE_CAMPO": 0,
    "PUB_QUALIDADE_RELACAO": 0,
    "PUB_QUALIDADE_DUPLICIDADE": 0
  },
  "aggregate": {
    "table": "PUB_C01_CICLO",
    "column": "qtd_pesquisas",
    "value": 0
  }
}
```

Os zeros acima são marcadores: substitua todos pelos valores obtidos no
Desktop. Para conferir C03 como agregado, use `table` igual a
`PUB_C03_PIPELINE_MENSAL`, `column` igual a `qtd_pesquisas_no_status` e inclua
`month_end` (`AAAA-MM-DD`). Filtre a consulta DAX ao fechamento escolhido.
Execute novamente com `--desktop /caminho/privado/recibo-desktop.json`. O
resultado `desktop.status: recibo_confere` compara os sete números e o agregado
com a publicação e o banco. O recibo, isoladamente, não prova que o refresh
ocorreu no aplicativo; mantenha a evidência da execução junto dele.

Para ensaio local com o fixture, use `--sintetico`. Essa opção apenas permite
conferir um `load_reference` iniciado por `synthetic`; o resultado mantém
`synthetic: true` e `final_acceptance: pendente`. A aceitação final exige a
geração CB16 autorizada, a conferência da publicação, o refresh real no Desktop
e a evidência de que ambos usaram a mesma carga.
