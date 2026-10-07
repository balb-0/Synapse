# Publicação e acesso aos cubos no BI

Este procedimento implementa a [decisão de consumo](decisao-consumo-cubos.md). O
arquivo DuckDB usado pela carga contém ingestão e controles; somente a pessoa
que publica precisa abri-lo. O consumidor recebe quatro recortes agregados
dos cubos e três tabelas de qualidade em Parquet. Eles continuam restritos
aos integrantes autorizados do projeto:
grupos pequenos podem permitir inferências e esta entrega não afirma anonimização.

## Publicar após uma carga conciliada

Na máquina que executa a carga, instale `requirements.txt` em um ambiente
Python e confirme o caminho do DuckDB analítico. Escolha um diretório **fora de
qualquer repositório Git** e com espaço para uma geração nova. Registre no
argumento `--load-reference` o identificador não sensível da execução de carga
que acabou de ser conciliada. O publicador registra o valor fornecido; ele não
comprova por si só que a reconciliação foi concluída.

```bash
PYTHONPATH=src python -m etl.analytics.publish \
  --database /caminho/privado/ingestao.duckdb \
  --output /caminho/privado/publicacao-bi \
  --load-reference run-2026-09-23-01
```

O programa usa uma conexão DuckDB somente para leitura. Ele escreve cada
Parquet em uma geração nova, confere contagem e nomes de colunas no arquivo e
calcula SHA-256. Depois grava `manifest.json` e troca `current.json` com
`os.replace`. Uma falha anterior à troca deixa a geração anterior como atual.
O processo cria o diretório de publicação com modo `0700` e os arquivos com
`0600` em sistemas POSIX. O controle de compartilhamento depende também das
permissões e do canal aprovado pela equipe; o código não concede acesso remoto.

Leia `current.json`, abra a subpasta indicada por `generation` e entregue
**somente esta subpasta** aos consumidores autorizados. Ela contém
`manifest.json` e sete arquivos:

```text
PUB_C01_CICLO.parquet
PUB_C02_PARTICIPACAO.parquet
PUB_C03_PIPELINE_MENSAL.parquet
PUB_C04_INSTRUMENTO.parquet
PUB_QUALIDADE_CAMPO.parquet
PUB_QUALIDADE_RELACAO.parquet
PUB_QUALIDADE_DUPLICIDADE.parquet
```

## Contrato da geração para o BI

Os nomes e as colunas abaixo são os selecionados por
[`etl.analytics.publish`](../src/etl/analytics/publish.py). Cada linha representa
um grupo no grão indicado; os arquivos não preservam o identificador de uma
pesquisa, empresa, pessoa ou pergunta. `manifest.json` registra, para cada
arquivo, `file`, `rows`, `columns` na ordem publicada e `sha256`.

| Arquivo | Grão de uma linha | Colunas publicadas, na ordem |
| :--- | :--- | :--- |
| `PUB_C01_CICLO.parquet` | `area`, `status`, `tipo` | `area`, `status`, `tipo`, `qtd_pesquisas`, `soma_dias_validacao`, `qtd_validacao_disponivel`, `soma_dias_coleta`, `qtd_coleta_disponivel`, `soma_dias_tabulacao`, `qtd_tabulacao_disponivel`, `soma_dias_ciclo_total`, `qtd_ciclo_total_disponivel` |
| `PUB_C02_PARTICIPACAO.parquet` | `area`, `tipo`, `mes_resposta` (primeiro dia do mês) | `area`, `tipo`, `mes_resposta`, `qtd_participacoes`, `soma_minutos_preenchimento`, `qtd_preenchimento_disponivel` |
| `PUB_C03_PIPELINE_MENSAL.parquet` | `data_fim_mes` observada, `status`, `area`, `tipo`, `complexidade`, `tipo_resposta` | `data_fim_mes`, `status`, `area`, `tipo`, `complexidade`, `tipo_resposta`, `qtd_pesquisas_no_status`, `qtd_entradas_no_mes`, `qtd_saidas_no_mes` |
| `PUB_C04_INSTRUMENTO.parquet` | `area`, `tipo_pergunta` | `area`, `tipo_pergunta`, `qtd_perguntas` |
| `PUB_QUALIDADE_CAMPO.parquet` | `tabela`, `campo` da fonte tratada corrente | `tabela`, `campo`, `qtd_linhas`, `qtd_preenchidas` |
| `PUB_QUALIDADE_RELACAO.parquet` | `relacao` (tabela filha e coluna de chave) | `relacao`, `qtd_chaves_informadas`, `qtd_chaves_correspondentes` |
| `PUB_QUALIDADE_DUPLICIDADE.parquet` | `tabela` da ingestão usada na conferência de chaves | `tabela`, `qtd_linhas`, `qtd_chaves_distintas` |

As três tabelas de qualidade fornecem, respectivamente, base para completude
(`qtd_preenchidas / qtd_linhas`), integridade referencial
(`qtd_chaves_correspondentes / qtd_chaves_informadas`) e duplicidade
(`(qtd_linhas - qtd_chaves_distintas) / qtd_linhas`). Só calcule a razão com
denominador positivo; denominador zero significa ausência de base.

Não entregue o DuckDB, outras gerações, `current.json` ou CSVs. A cópia da
geração precisa ficar em pasta restrita fora do Git. Uma nova carga não atualiza
automaticamente a publicação: execute o comando de novo, distribua a nova
geração e atualize o relatório. A limpeza de gerações antigas segue a política
de retenção do projeto.

## Pasta da geração no Power BI

O projeto [`CentralPesquisasBI.pbip`](../powerbi/CentralPesquisasBI.pbip) usa o
parâmetro de texto obrigatório `PastaPublicacaoBI`, definido em
[`expressions.tmdl`](../powerbi/CentralPesquisasBI.SemanticModel/definition/expressions.tmdl).
No Power BI Desktop, configure seu valor com o caminho **da subpasta da geração
copiada**, sem barra final, por exemplo
`C:\dados-privados\publicacao-bi\<generation>`. As sete consultas acrescentam
`\NOME_DO_ARQUIVO.parquet` ao parâmetro. Apontar para o diretório que contém
`current.json` não encontra os arquivos. Ao receber outra geração, altere o
parâmetro para a nova subpasta e atualize as sete tabelas; compare as contagens
carregadas com `manifest.json` da mesma geração.

Para desenvolvimento local com **dados exclusivamente sintéticos**, mantenha a
geração de trabalho em uma pasta privada fora do repositório. No Windows, uma
convenção é `%TEMP%\g05-cb12-publicacao-sintetica\<generation>`; em outro
ambiente, escolha um diretório equivalente fora do Git. A pasta pai contém
`current.json`, que indica a subpasta da geração vigente. Essa subpasta contém
`manifest.json` e os sete Parquet e é o valor a informar em
`PastaPublicacaoBI`. A fixture versionada em
[`tests/analytics/test_publish.py`](../tests/analytics/test_publish.py) pode
servir de fonte para gerar a amostra, com um `load_reference` que identifique
seu caráter sintético, como `synthetic-cb12`.

A geração de trabalho é local, pode ser removida do diretório temporário e
**não** é evidência de carga ou publicação do conjunto autorizado. Cada pessoa
deve gerar ou receber uma cópia sintética em sua própria pasta privada.

Se a implementação do publicador ou a regra de integridade referencial mudar,
gere outra amostra e confira seu manifesto antes de usá-la para validar I18.

## Conferir o pacote na máquina consumidora

No Windows com Power BI Desktop, escolha **Obter dados → Parquet** para cada um
dos sete arquivos da geração recebida. Confira o total de linhas de cada
arquivo contra `manifest.json` antes de atualizar o relatório. Os arquivos
recebidos são a única fonte do relatório. O conector local citado no ADR é
documentado pela Microsoft; esta entrega não afirma uma execução visual no
Power BI Desktop sem uma máquina Windows de teste.

Em Linux ou macOS, uma pessoa pode conferir os arquivos com Python e DuckDB,
sem acesso ao banco original. Exemplo a partir da pasta da geração recebida:

```python
import duckdb

con = duckdb.connect(":memory:")
print(con.execute("SELECT COUNT(*) FROM read_parquet('PUB_C02_PARTICIPACAO.parquet')").fetchone())
```

Uma consulta `SELECT * FROM ingestao_pesquisas` nessa conexão falha porque a
tabela não existe no material entregue. Isso verifica o limite **desse caminho
de distribuição**; não revoga acesso que uma pessoa já tenha ao DuckDB por
outros meios.

## Semântica dos recortes

| Arquivo | Grão publicado | Uso correto |
| :--- | :--- | :--- |
| `PUB_C01_CICLO` | Área, status e tipo | `soma_dias_* / qtd_*_disponivel` calcula média só onde a duração existe. A soma `NULL` com contagem 0 indica indisponibilidade no grupo. `qtd_pesquisas` conta pesquisas correntes. |
| `PUB_C02_PARTICIPACAO` | Área, tipo e mês da resposta | `qtd_participacoes` conta ocorrências do snapshot selecionado, não pessoas distintas nem taxa de adesão. `soma_minutos_preenchimento / qtd_preenchimento_disponivel` só vale com denominador positivo. |
| `PUB_C03_PIPELINE_MENSAL` | Mês observado, status, área, tipo e perfil | Some `qtd_pesquisas_no_status` apenas entre grupos disjuntos do mesmo mês. `qtd_entradas_no_mes` e `qtd_saidas_no_mes` ficam `NULL` sem histórico de transições. Meses não observados não viram linhas zero. |
| `PUB_C04_INSTRUMENTO` | Área e tipo de pergunta | `qtd_perguntas` conta associações pesquisa-pergunta, não respostas. |

### Métricas sem fonte na publicação

O catálogo completo e os motivos por indicador estão em
[`indicadores-publicaveis-bi.md`](indicadores-publicaveis-bi.md). Nesta geração,
o BI deve apresentar **sem dado** com motivo textual, nunca zero, para:

| Indicadores | Limite do contrato publicado |
| :--- | :--- |
| I05, I07, I09, I12, I13, I19, I20 | Há dado ou cálculo possível em outra camada, mas falta a coluna ou o grão necessário nos sete arquivos: prorrogação, empresas distintas por pesquisa, mercado, respostas, respondentes, parseabilidade e divergência de título. |
| I06, I08, I10, I11, I15, I21–I25 | Falta fonte, regra homologada, reconciliação ou mapeamento para atraso/prioridade, adesão, engajamento, validação/versão, frescor, linhagem, publicação autorizada, cobertura de processamento e conformidade de acesso. |

I03 cobre somente os quatro pares de datas das durações de C01; marcos isolados
não estão publicados. I04 permite média ponderada, mas não mediana. Em C03,
`qtd_entradas_no_mes` e `qtd_saidas_no_mes` existem no schema e permanecem
`NULL` enquanto não houver histórico de transições. Nenhuma dessas lacunas
autoriza inferir valores a partir de `qtd_participacoes` ou preencher `NULL`
com zero.

Categorias sem vínculo comprovado permanecem `NULL`. O publicador usa colunas
explícitas e não exporta chaves substitutas, IDs de pessoa, empresa, pergunta
ou pesquisa, `source_checksum`, `source_offset`, enunciado, alternativas,
respostas, e-mail ou tabelas `ingestao_*`. A ausência dessas colunas e do
arquivo DuckDB é a fronteira técnica do acesso publicado.

## Diagnóstico

- Se o comando disser que falta uma tabela ou coluna, execute a carga das
  dimensões e dos quatro fatos no mesmo banco antes da publicação; não copie o
  arquivo de ingestão para a pessoa do BI.
- Se a contagem ou o schema do Parquet divergir da consulta, a publicação falha
  e `current.json` continua na geração anterior. Investigue espaço em disco,
  permissão e estado da carga, depois execute novamente.
- Se o Power BI não encontrar o arquivo, confirme que a geração inteira foi
  copiada para a máquina Windows e ajuste `PastaPublicacaoBI` para a subpasta
  local. Uma nova geração tem outro caminho; atualize o parâmetro e as sete
  tabelas.
- Se o relatório somar meses de C03 ou mostrar zero para duração ausente,
  corrija a medida do relatório conforme a tabela acima.
