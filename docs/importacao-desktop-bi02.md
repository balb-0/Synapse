# BI-02: ensaio de importação das sete tabelas no Power BI Desktop

Este ensaio usa dados **sintéticos**. A referência `synthetic-bi02-fixture` no
manifesto identifica o fixture, não uma carga conciliada de produção. A execução
local de Python valida os Parquet e o contrato do modelo. A execução no
Desktop real em VM Windows foi registrada abaixo; a aceitação visual do
relatório e a geração final têm evidências próprias.

## Preparar a geração

Use o publicador corrigido da camada analítica, commit
`894445ddc92a7fce172b4f90c09b52f5650f354e`, incluído no
[MR !289](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/merge_requests/289),
para gerar o fixture. A revisão integrada `be132f1` usada na regeneração
contém essa correção; o script do fixture não foi alterado para a execução. Um checkout anterior à correção
da chave composta de respostas/questões reproduz a divergência histórica
de I18 descrita no fim desta página. Com as dependências de
`requirements.txt` instaladas, escolha uma
pasta privada **fora de qualquer repositório Git**:

Antes de executar, use um checkout que contenha o script BI-02 e esse commit
upstream. Confira a ancestralidade:

```bash
git merge-base --is-ancestor 894445ddc92a7fce172b4f90c09b52f5650f354e HEAD
```

Saída diferente de zero não satisfaz o pré-requisito: integre o upstream
corrigido antes de gerar. Confira ainda que a publicação de relações usa
`EXISTS` e que respostas/questões compara pesquisa e pergunta juntas. A
branch isolada de BI-02, sem essa integração, não foi declarada validada com
o publicador corrigido. O recibo de Desktop sempre identifica a revisão do
pacote integrado efetivamente executado.

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
BI-02 não substitui essa execução no Desktop. A conferência registrada abaixo
prova a importação e as consultas do fixture; não substitui o refresh final
em BI-05 nem a validação visual das páginas migradas.

## Execução registrada em Windows

O [recibo sanitizado](evidencias/bi02/desktop-fixture.json) registra consultas
reais no Analysis Services local do Power BI Desktop em
2026-10-06 às 14:08:45 UTC, depois da sincronização do relógio da VM.
A execução foi automatizada; não há declaração de operação por uma pessoa.
A geração `665cb490f85d49529488b4910e094923` usa a referência
`synthetic-bi02-fixture`, com as sete contagens iguais à tabela acima.

As 13 partições do projeto e duas partições automáticas de data estavam
processadas sem erro. O pacote PBIP integrado de origem `f068a01` teve 98 arquivos
conferidos por hash; a projeção semântica via TOM comparou 128 itens de origem
e do engine, com zero diferenças. O caminho local do parâmetro foi conferido
separadamente, pois sua adaptação para Windows não integra o hash do modelo.
TOM não fornece um marcador do commit exato dentro do engine.

As consultas retornaram totais C01/C02/C04 de 4/4/3, validação ponderada de
5 dias com base 2 e preenchimento ponderado de 10 minutos com base 2. Para
C03, o fechamento de 28/02/2026 e estoque 4 coincidem na soma direta e na
medida BI-04. Entradas/saídas continuam nulas e o catálogo tem 18 entradas,
17 sem dado. A fonte CB-16 v3 e o aspecto visual do relatório não são
aceitos por este ensaio sintético.

O recibo desta rodada histórica é do pacote integrado `f068a01`, SHA256
`88a33f4963e9f2912794ad165c003d03822d24986817c2ce5909c8551207f89e`,
consultado em Power BI Desktop `2.158.1177.0` no Windows `10.0.26200.0`.
O recibo inicial do pacote `9726fd6` permanece no mesmo diretório de
evidências com sufixo `-inicial`; ele é histórico e usa o relógio já
sincronizado. Ambos usam o fixture, não a fonte final CB-16.

## Limite identificado no fixture histórico

A geração sintética `665cb490f85d49529488b4910e094923` antecede a correção
da identidade composta de respostas para questões. A publicação de
qualidade somava 11 correspondências em 13 chaves informadas; a consulta
independente com `(pesquisa_id, pergunta_id)` produz 10/13. A quantidade de
linhas das sete tabelas não muda, por isso as contagens sozinhas não
detectaram essa divergência. Os recibos dessa geração são históricos e
marcados `historical_stale_publication`; não aceitam o KPI I18.

O fixture foi regenerado com o publicador corrigido, na geração
`2c699f0b066847ee8559f1e31d88f49d`, conservando as sete contagens e
publicando 10/13. Sua nova execução Desktop ainda precisa do recibo próprio.
A fonte v3 tem todas as relações de qualidade conferidas contra a ingestão
sem divergências; este problema é da publicação sintética antiga.
