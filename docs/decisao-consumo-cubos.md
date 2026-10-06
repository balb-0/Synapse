# Decisão de consumo dos cubos no BI (CB-08)

Status: decisão para implementação em CB-09. O procedimento e a prova de acesso pertencem a essa task. Esta decisão parte do [contrato físico dos cubos](contrato-fisico-cubos.md) e do DuckDB local descrito em [ambiente-duckdb.md](ambiente-duckdb.md).

## Contexto

O ETL grava ingestão tratada, rejeições, controles, dimensões e fatos no mesmo arquivo DuckDB. O DuckDB é embutido no processo Python e protege o arquivo por permissões do sistema operacional, não por usuários e `GRANT` para cada tabela. Entregar esse arquivo a uma pessoa que só deve consultar os cubos também entrega as tabelas de ingestão. Uma conexão de leitura ao arquivo original não resolve esse limite. A carga e o BI ainda podem disputar a abertura do arquivo enquanto há escrita.

Os protótipos D01–D04 atuais leem um JSON agregado gerado diretamente dos CSVs. Eles são evidência visual e não constituem conexão dos quatro fatos da Sprint 4 ao BI. Nesta decisão, "participação" significa ocorrência observada do snapshot conciliado, não adesão ao universo convidado. C03 é estoque de um fechamento mensal observado; somar meses repete o mesmo estoque. Ausência de medida permanece `NULL`.

## Alternativas consideradas

| Caminho | Ferramenta e ligação | Acesso e atualização | Consequência |
| :--- | :--- | :--- | :--- |
| Abrir o DuckDB original | Conector/driver DuckDB no cliente BI | Exige distribuir o banco inteiro ou disponibilizar seu arquivo em rede; o leitor pode consultar ingestão, rejeições e controles. A leitura pode disputar o arquivo com a carga. | Rejeitado porque não isola os cubos. Instalar um driver não cria permissões por tabela. |
| Servir views por banco ou API separada | Um serviço autenticado publica somente consultas autorizadas; BI usa conector do serviço | Permite credencial e autorização centralizadas, mas exige hospedar, operar, atualizar e monitorar outro processo e seu armazenamento. | Viável para uso multiusuário contínuo; essa infraestrutura não existe no projeto e não cabe na entrega local da Sprint 4. |
| Publicar agregados em Parquet | A publicação escreve quatro cubos e três tabelas de qualidade; Power BI Desktop os importa pelo conector Parquet do Power Query | O BI recebe apenas os arquivos publicados. Cada nova carga exige nova publicação e atualização manual do relatório. Permissão de leitura, cópia e transporte ficam sob controle do diretório e do canal de distribuição. | Escolhido para a entrega local reproduzível, sem serviço ou segredo de banco. |

O [conector Parquet do Power Query](https://learn.microsoft.com/en-us/power-query/connectors/parquet) aceita arquivo local. A documentação consultada em 23/09/2026 lista Windows para arquivo local e exige gateway para atualização de fonte local no Power Query Online. Não presumimos conector nativo do Power BI para o arquivo DuckDB nem atualização automática do relatório.

## Contrato da publicação

A publicação atual gera um diretório de snapshot com sete arquivos Parquet e `manifest.json`: os quatro cubos `PUB_C01_CICLO`, `PUB_C02_PARTICIPACAO`, `PUB_C03_PIPELINE_MENSAL` e `PUB_C04_INSTRUMENTO`, mais `PUB_QUALIDADE_CAMPO`, `PUB_QUALIDADE_RELACAO` e `PUB_QUALIDADE_DUPLICIDADE`. O contrato inicial de CB-09 contemplava os quatro cubos; as tabelas de qualidade ampliaram o pacote consumido pelo modelo semântico. Essas relações são saídas **agregadas para BI**, não novos nomes dos fatos físicos. Uma publicação substitui o conjunto inteiro; não mistura arquivos de cargas distintas. O manifesto do snapshot deve registrar versão, horário, origem da carga e contagens agregadas, sem credencial, linha individual ou identificador de pessoa.

| Publicação | Grão de BI e conteúdo permitido | Regra que o leitor deve respeitar |
| :--- | :--- | :--- |
| `PUB_C01_CICLO` | Área, status e tipo; contagem de pesquisas, soma e contagem de valores presentes para cada duração disponível | Média usa a contagem própria da medida como denominador. Não transformar duração ausente em zero. |
| `PUB_C02_PARTICIPACAO` | Área, tipo e mês da resposta; contagem de ocorrências observadas, soma e contagem válida de minutos de preenchimento | Não chamar a contagem de taxa de adesão. Não incluir pessoa, empresa, checksum ou offset da linha de origem. |
| `PUB_C03_PIPELINE_MENSAL` | Fechamento mensal observado, status, área, tipo e perfil; estoque e entradas/saídas anuláveis | O estoque só pode ser somado entre grupos disjuntos **do mesmo mês**. Sem observação de fechamento, não publicar mês fictício nem zero. |
| `PUB_C04_INSTRUMENTO` | Área e tipo de pergunta; contagem de associações pesquisa-pergunta | Não incluir enunciado, alternativas, respostas individuais ou texto livre. |

Rótulos de categoria podem ter origem na dimensão conformada, mas o exportador deve usar uma lista explícita de colunas. Não exportar `DIM_PESSOA`, `DIM_EMPRESA`, `DIM_PERGUNTA`, fatos físicos integrais, IDs de cliente, empresa ou pergunta, `source_checksum`, `source_offset`, e-mail, resposta individual ou tabelas `ingestao_*`. Uma chave hash ou substituta ainda pode permitir ligação entre registros; sua aparência opaca não é prova de anonimização. Grupos raros também podem revelar informação. Até haver regra de publicação e limiar de pequeno grupo aprovados, a distribuição é restrita aos integrantes autorizados do projeto e não deve ser tratada como divulgação pública ou dado anonimizado.

Um arquivo Parquet entregue ao leitor pode ser copiado. A restrição é a seleção de dados no exportador, mais permissões e distribuição do diretório. Ela não revoga cópias já distribuídas e não equivale a controle de acesso por linha ou tabela dentro do BI. O diretório de saída fica fora do Git; o mesmo vale para qualquer banco e fonte local. Não inserir credencial em código, manifesto, relatório ou documentação.

## Operação em cada máquina

1. A máquina que executa a carga precisa de Python, das dependências do projeto, de acesso autorizado ao DuckDB de ingestão e espaço para criar e validar o snapshot Parquet. Só esse processo abre o banco original. Executar a publicação após uma carga analítica conciliada e ler de volta os sete arquivos antes da entrega.
2. Quem desenvolve o relatório precisa de Windows com Power BI Desktop e acesso de leitura ao diretório publicado. Importa os sete arquivos por **Obter dados → Parquet**, confere as contagens do manifesto e atualiza o relatório manualmente após receber outro snapshot. Uma cópia local deve permanecer em pasta restrita e fora do repositório.
3. Em Linux ou macOS, a pessoa pode produzir e conferir os arquivos com Python/DuckDB, mas o Power BI Desktop local não é o caminho escolhido. Para editar o relatório deve usar uma máquina Windows autorizada. O navegador dos protótipos atuais não passa a ler estes Parquets automaticamente.
4. O responsável pela distribuição entrega somente o diretório publicado por canal já autorizado pela equipe, registra a versão recebida e remove cópias antigas conforme a política do projeto. Esta decisão não cria um servidor, gateway, conta ou canal de compartilhamento novo.

## Aceite verificável

CB-09 deve provar em ambiente limpo que a exportação gera exatamente os sete arquivos e um manifesto coerente com a mesma carga; que um leitor sem o DuckDB original consulta os Parquets; e que nenhum arquivo publicado contém coluna ou relação de ingestão. Também deve tentar consultar uma tabela `ingestao_*` a partir do material entregue e registrar que ela não existe nesse material. Conferir os nomes e tipos das colunas publicadas e testar `NULL`, grupo desconhecido, recarga e falha durante a publicação. A conexão visual no Power BI Desktop depende de uma máquina Windows disponível; até essa prova, a compatibilidade citada acima é documental, não uma execução observada neste repositório.
