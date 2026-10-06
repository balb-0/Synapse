# BI-02: ensaio de importação das sete tabelas no Power BI Desktop

Este ensaio usa dados **sintéticos**. A referência `synthetic-bi02-fixture` no
manifesto identifica o fixture, não uma carga conciliada de produção. A execução
local de Python valida os Parquet e o contrato do modelo; a aceitação visual no
Power BI Desktop depende de uma máquina Windows com o aplicativo instalado.

## Preparar a geração

No checkout, com as dependências de `requirements.txt` instaladas, escolha uma
pasta privada **fora de qualquer repositório Git**:

```bash
PYTHONPATH=src python scripts/analytics/gerar_fixture_bi.py \
  --output /caminho/privado/fixture-bi02
```

O comando imprime o ID da geração e as contagens. Leia `current.json` na pasta
de saída; a subpasta cujo nome é `generation` contém `manifest.json` e os sete
Parquet. Copie apenas essa subpasta para uma pasta restrita no Windows, com um
caminho curto, por exemplo `C:\BI02\g1`. Mantenha os oito arquivos juntos. Não
copie o DuckDB temporário: o gerador o remove após a publicação.

Contagens esperadas deste fixture:

| Tabela | Linhas |
| :--- | ---: |
| `PUB_C01_CICLO` | 2 |
| `PUB_C02_PARTICIPACAO` | 3 |
| `PUB_C03_PIPELINE_MENSAL` | 4 |
| `PUB_C04_INSTRUMENTO` | 2 |
| `PUB_QUALIDADE_CAMPO` | 64 |
| `PUB_QUALIDADE_RELACAO` | 8 |
| `PUB_QUALIDADE_DUPLICIDADE` | 5 |

## Abrir e atualizar o PBIP

1. Abra `powerbi/CentralPesquisasBI.pbip` no Power BI Desktop. Se o aplicativo
   pedir atualização do projeto, registre a mensagem e a versão antes de aceitar.
2. Na interface do Desktop, abra **Transformar dados > Gerenciar parâmetros**.
   Edite `PastaPublicacaoBI` para o caminho local da subpasta da geração, por
   exemplo `C:\BI02\g1`, sem barra final. A expressão M de cada uma das sete
   partições acrescenta `\NOME_DA_TABELA.parquet` a esse parâmetro.
3. Use **Fechar e aplicar** e depois **Atualizar**. Registre cada aviso ou erro
   de Power Query e indique a tabela afetada. Não grave nem comite o caminho
   específico da máquina em `expressions.tmdl`.
4. Confira as sete tabelas no modelo e compare a contagem de linhas carregadas
   com a tabela acima e com `manifest.json`. No modo de consulta DAX do Desktop,
   execute, por exemplo:

   ```dax
   EVALUATE ROW("Linhas C01", COUNTROWS(PUB_C01_CICLO))
   ```

   Repita `COUNTROWS` para as demais seis tabelas. Registre os sete resultados,
   a versão do Desktop, a data da execução e eventuais diferenças.
5. Confira os casos de semântica com consultas ou visuais temporários: em C01,
   Saúde/Ativa/Mercado tem três pesquisas, soma de validação 10 e base válida 2
   (média 5); Educação tem soma nula e base 0, então a média fica em branco.
   C02 tem janeiro no dia 1 mesmo com resposta no dia 15, março no dia 1 e
   uma linha com mês nulo. C03 tem fechamentos em 31/01 e 28/02, perfil com
   complexidade nula e entradas/saídas nulas. Nas tabelas de qualidade, confira
   `pesquisas.data_aprov = 1/2`, `clientes.empresa_id = 1/2` e duplicidade de
   `pesquisas = (3-2)/3`.

Guarde um registro de aceitação com versão do Power BI Desktop, geração,
contagens, consultas DAX, erros e capturas de tela. O teste automatizado de
BI-02 não substitui essa execução no Desktop. Até a execução em Windows, a
importação visual e o refresh das sete partições permanecem **pendentes**.
