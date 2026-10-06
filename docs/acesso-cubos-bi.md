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

Não entregue o DuckDB, outras gerações, `current.json` ou CSVs. A cópia da
geração precisa ficar em pasta restrita fora do Git. Uma nova carga não atualiza
automaticamente a publicação: execute o comando de novo, distribua a nova
geração e atualize o relatório. A limpeza de gerações antigas segue a política
de retenção do projeto.

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
  copiada para a máquina Windows e selecione os arquivos locais da subpasta.
  Uma nova geração tem outro caminho; atualize a origem dos sete arquivos.
- Se o relatório somar meses de C03 ou mostrar zero para duração ausente,
  corrija a medida do relatório conforme a tabela acima.

## Registro da execução CB-16

A geração v3 `6b1eaa686aac43b18b6d6545e1c2c5f1` foi publicada com
`load_reference` `afcde424-45e8-457b-8793-bf0866d142b2`. O manifesto tem
SHA-256 `7593530089355c139f50529e9600d496e11a8262e00064364fe4fde378efc4e4`.
O [recibo público](evidencias/cb16/geracao-v3.json) contém esquemas, hashes e
as comparações independentes com a ingestão tratada.

| Arquivo Parquet | Linhas | SHA-256 |
| --- | ---: | --- |
| `PUB_C01_CICLO.parquet` | 57 | `4bbab9a2e9a1d9c4c8b7c59c5e3cdccf9f684cdd677d9d01da0a66ecb6f1e353` |
| `PUB_C02_PARTICIPACAO.parquet` | 32 | `98056ac1e8ac1d9be3bb3448f86cd82bc670f6b98f17dbce87a4b1339a142b0c` |
| `PUB_C03_PIPELINE_MENSAL.parquet` | 0 | `80c89f635056f98e64f8289ed38507fc0d514d206307d5755630a1ab6d993f87` |
| `PUB_C04_INSTRUMENTO.parquet` | 45 | `7b6153d16e7b873960cd628917bb14a43346b9c820bf2aec159433c0faa91818` |
| `PUB_QUALIDADE_CAMPO.parquet` | 64 | `a27e660d3accad8d97809a74bb5c1e5840058cad2ea3174e757a981249138d41` |
| `PUB_QUALIDADE_RELACAO.parquet` | 8 | `de9a591d805abf032fd5f8aac214ae7214c1f5fd71ad1e55e6f578d61d64a96d` |
| `PUB_QUALIDADE_DUPLICIDADE.parquet` | 5 | `e23c1db03d6f66546937ff6d826f67de6c31330a86d7d83bcd0a073b3833e764` |

As somas de C01, em dias, são validação 171 (20 durações disponíveis), coleta
4.960 (358), tabulação 3.020 (330) e ciclo total 9.468 (331), sobre 366
pesquisas. C02 soma 17.740 participações; a soma de minutos de preenchimento
é `NULL` e o denominador disponível é zero. C04 soma 3.186 perguntas. O
verificador independente encontrou zero grupos divergentes em C01, C02 e C04
e zero contagens divergentes nas três tabelas de qualidade. C03 não possui
fechamento mensal observado: as zero linhas publicadas não representam estoque
zero, e entradas e saídas permanecem indisponíveis.

A [conferência CB-16](publicacao-cb16.md) registra a origem e a reconciliação
da carga. A ingestão executou `fd6864e` com adaptador privado de
`respondent_id` opaco; a carga analítica e a publicação executaram `894445d`.
O refresh no Power BI Desktop pertence às tarefas BI.
