# Inventário de divergências entre os cubos C01–C04 e a ingestão tratada

**Escopo.** CB-01: comparar todos os grãos/fatos, dimensões, atributos e métricas de C01–C04 em `docs/projeto.md` §5.2, `docs/dmc.json`, espelhos textuais/diagramas e colunas executáveis da ingestão. Este inventário registra fatos e pendências; não fecha o contrato físico de CB-02.

**Conclusão de implementação.** Os quatro cubos ainda são contratos propostos. O esquema executável e o DDL versionado definem as seis tabelas `ingestao_*`, com colunas de origem normalizadas e metadados de carga; não há DDL executável para `FATO_*` ou `DIM_*`. Referências: `src/etl/transformation/schema.py:56-138`, `src/etl/load/ddl.py:31-40,224-261`, `sql/duckdb/001_ingestao_tratada.sql:17-175` e `docs/schema-transformacao.md:38-43`.

> **Situação em 25/09/2026:** este inventário é a fotografia de abertura da
> Sprint 4 (CB-01). Os quatro cubos foram materializados em seguida:
> `src/etl/analytics/` (`dimensions_ddl.py`, `facts_cycle_participation.py`,
> `facts_pipeline_instrument.py`, `load.py`, `reconcile.py`) cria `DIM_*` e
> `FATO_*` no DuckDB a partir da ingestão conciliada, e `publish.py` gera os 7
> Parquet consumidos pelo modelo semântico. O contrato físico vigente está em
> [`contrato-fisico-cubos.md`](contrato-fisico-cubos.md) e
> [`ddl-dimensoes.md`](ddl-dimensoes.md); as colunas "sem origem" desta matriz
> continuam sem origem e são publicadas como indisponíveis.

## Como ler a matriz

Cada linha é um item ou grupo homogêneo de itens do contrato dimensional. O estado descreve a ligação entre o nome/semântica alvo e o contrato de ingestão atual:

- **direto**: coluna presente com a mesma semântica observada;
- **renomeado**: coluna presente sob outro nome canônico;
- **derivável com regra**: deriva deterministicamente de colunas presentes, mas não é uma coluna/fato atualmente materializado;
- **sem origem**: falta coluna ou evento requerido; não se preenche com zero nem com uma aproximação presumida;
- **dependente de homologação**: existe fonte ou candidato, mas a identidade, regra, domínio, calendário, vínculo ou autoridade ainda precisa ser aprovado.

`schema.py` define o contrato da transformação. `001_ingestao_tratada.sql` é o DDL físico gerado dele. Chaves substitutas e fatos dos diagramas não devem ser entendidos como implementados por existirem nesses documentos.

## Resultado por cubo

| Cubo | Grão/fato proposto no DMC | Métricas nomeadas no DMC | Disponibilidade real sob as fontes atuais |
| :--- | :--- | :--- | :--- |
| C01 — Portfólio e Ciclo | Uma linha por pesquisa, snapshot acumulativo | 4 durações; quantidade declarada `participantes`; `flag_prorrogada`; `qtd_respondentes_na_pesquisa` consta como removida | Marcos, áreas e categorias têm fonte; durações dependem da convenção de calendário. A contagem de respondentes removida não equivale a contagem de participações nem de pessoas. |
| C02 — Participação e Representatividade | Uma linha por registro/ocorrência em `respondentes.csv`, transação | `qtd_participacao`, `seq_ocorrencia`, `minutos_preenchimento`, `pct_mercado_na_participacao` | Linha física e campos de empresa/horário/share existem. Pessoa e deduplicação por pessoa dependem de identidade conciliada; adesão não tem denominador de convidados; I09 depende da fonte autorizada. |
| C03 — Pipeline Mensal | Uma linha por mês, status, área, tipo e perfil, snapshot periódico | Estoque `qtd_pesquisas_no_status`; fluxos `qtd_entradas_no_mes` e `qtd_saidas_no_mes` | Estoque começa em snapshots produzidos após go-live. Histórico de transições não existe nas fontes atuais, então entradas/saídas ficam indisponíveis até integração. |
| C04 — Resultados e Questionários | Uma associação pesquisa–pergunta, fato sem medidas somáveis | `qtd_pergunta` derivada por contagem; `qtd_alternativas` é atributo de pergunta | Colunas de questões existem. Os números 231/10 são do snapshot anterior à versão v3; o inventário de fontes registra 3.297 questões na v3. Cobertura e vínculos precisam ser recalculados. |

As definições das medidas e dimensões vêm das listas DMC, não de colunas de fatos existentes: `docs/dmc.json` (C01 `:134-171`; C02 `:232-278`; C03 `:320-359`; C04 `:404-446`) e `docs/projeto.md:812-831`. C01–C04 ainda não têm contrato físico único.

## Matriz item a item

### C01 — Portfólio e Ciclo

**Fato e grão.** O DMC propõe `FATO_CICLO_PESQUISA`, uma linha acumulada por pesquisa (`docs/dmc.json:132,135-146`; diagrama renderizado `docs/assets/prototipos-dashboards/imagens/cubo-01.png`). `pesquisas.id` é normalizado para `pesquisa_id` e tem chave de negócio declarada (`schema.py:57-60,140-145`); a view `ingestao_pesquisas_atual` permite selecionar a versão atual. A tabela física mantém versões corrigidas por conteúdo (`001_ingestao_tratada.sql:17-53`). **Estado do fato:** derivável com regra de seleção da versão atual; a tabela fato ainda não existe.

| Item de C01 | Origem executável e regra disponível | Estado | Evidência e divergência |
| :--- | :--- | :--- | :--- |
| `pesquisa_id` / chave de origem da pesquisa | `pesquisas.id` → `ingestao_pesquisas.pesquisa_id` | renomeado | `schema.py:57-60`; DDL `:17-19`. DMC chama o atributo de `id_origem_planilha` no diagrama PNG; §5.2 usa chave de pesquisa. |
| `titulo`, `objetivos` | `pesquisas.titulo`, `pesquisas.objetivos` | direto | `schema.py:59,80`; DDL `:19,35`. |
| `ano_edicao` em `DIM_PESQUISA` | Nenhuma coluna de ano/edição; `titulo` existe | dependente de homologação | O atributo aparece em §5.2.1 (`projeto.md:894-896`) e na imagem C01; DMC o mantém (`dmc.json:157-164`). Ano extraído do título é só candidato; não há regra validada e `data_divulgacao` não é sinônimo de edição. |
| Papéis `sk_data_solicitacao`, `sk_data_aprovacao`, `sk_data_divulgacao`, `sk_data_limite_coleta`, `sk_data_prorrogacao`, `sk_data_entrega` | Respectivamente `data_solicitacao`, `data_aprov`, `data_divulgacao`, `data_limite`, `prorrogada_ate`, `data_entrega` | direto | Os seis campos `DATE` existem (`schema.py:65-75`, DDL `:25-30`); mesmos seis papéis estão na lista DMC `:159-164` e em `projeto.md:898-920`. |
| Número de papéis de `DIM_TEMPO` | Os seis campos de marco acima | dependente de homologação | A string Mermaid do DMC declara “7 papeis” (`dmc.json:132`), mas lista seis chaves de data (`:159-164`) e a imagem C01 mostra seis FKs de data. Definir/corrigir o sétimo papel antes de fechar o contrato. |
| Calendário `data`, `ano`, `mes`, `trimestre`, `flag_dia_util` | Gerado a partir das datas, não recebido como fonte | derivável com regra | Aparece na imagem C01. Ano/mês/trimestre são derivados de data; dia útil exige calendário local homologado. O DMC restringe rótulo de duração a dias corridos até homologar calendário (`dmc.json:149-152,177-179`). |
| `sk_area` / nome da área | `pesquisas.area` | direto | `schema.py:62`, DDL `:22`; `projeto.md:922-924`; DMC `:165`. Chave substituta é futura. |
| `sk_status` / nome do status | `pesquisas.status` | direto | `schema.py:60`, DDL `:20`; `projeto.md:926-928`; DMC `:166`. |
| `sk_tipo` / nome do tipo | `pesquisas.tipo` | direto | `schema.py:61`, DDL `:21`; `projeto.md:930-932`; DMC `:167`. |
| `DIM_PERFIL_PESQUISA.complexidade` | `pesquisas.complexidade` | direto | `schema.py:77`, DDL `:32`; `projeto.md:934-936`; DMC `:168`. |
| `DIM_PERFIL_PESQUISA.tipo_resposta` | `pesquisas."tipo de resposta"` → `tipo_resposta` | renomeado | `schema.py:78`, DDL `:33`; `projeto.md:934-936`; DMC `:168`. |
| `DIM_FAMILIA_PESQUISA` / `sk_familia` | `titulo` | dependente de homologação | A família é derivada por normalização do título e precisa de validação do parceiro (`projeto.md:938-940,956`; DMC `:169,180,186`). O título é fonte; a classificação não é direta nem oficial ainda. |
| Família `titulo_familia`, `qtd_edicoes`, `flag_recorrente` do diagrama | Títulos e linhas do fato, após regra de agrupamento | dependente de homologação | A imagem C01 inclui os três atributos; contagem/recorrência podem ser calculadas só depois de aprovada a família e o tratamento de versões. |
| `DIM_FONTE_DADO` / `sk_fonte` | Coluna técnica `source` identifica a entrada; não há coluna de sistema externo de origem | dependente de homologação | DMC descreve linhagem/sistema de origem (`projeto.md:942-944`; JSON `:125,170`). `source` está no DDL (`:40`) e identifica a fonte de ingestão; não prova qual sistema originou o arquivo. |
| `DIM_EXECUCAO_CARGA` / `sk_carga` | `run_id`, `task_id`, `batch_id`, `ingested_at`, `schema_version` | direto | Metadados técnicos existem (`001_ingestao_tratada.sql:40-50`). Mapeá-los a `data_execucao`/`versao_etl` dos diagramas (`cubo-01.png`) requer fixar os significados e a granularidade da dimensão. |
| `dias_uteis_validacao`, `dias_uteis_coleta`, `dias_uteis_tabulacao`, `dias_uteis_ciclo_total` | Diferenças entre pares de `DATE`; pares incompletos devem resultar em `NULL` | dependente de homologação | Fórmulas constam em `projeto.md:849-870`; DMC determina dias corridos até existir calendário homologado (`dmc.json:149-152,177-179`). A nomenclatura atual `dias_uteis_*` não pode rotular diferença civil como dia útil. |
| Campos de duração recebidos `dias_uteis_para_entrega`, `dias_uteis_aberta`, `dias_solicitacao_divulgacao`, `dias_tabulacao` | Quatro colunas executáveis (a última renomeia “dias para tabulação”) | direto | `schema.py:76-84`; DDL `:31-39`. Nenhuma lista de métricas do DMC define equivalência entre estes valores declarados e as quatro diferenças de datas acima. Preservar campos separadamente; não substituir uma regra pela outra sem decisão. |
| `qtd_empresas_na_pesquisa` | `pesquisas.participantes` | direto | Campo inteiro recebido (`schema.py:63`, DDL `:23`); DMC `:153`, projeto `:872-876`. É contagem declarada e não aditiva; não equivale às empresas distintas observadas no C02. |
| `qtd_respondentes_na_pesquisa` | Não existe em `pesquisas.csv`; C02 tem registros de participação | sem origem | DMC afirma que a métrica foi removida (`dmc.json:154`); projeto repete a decisão (`projeto.md:878-882`). Contar linhas de participação gera outra unidade e não comprova pessoas distintas. **A imagem C01 ainda exibe essa medida**, portanto está obsoleta frente ao texto e DMC. |
| `flag_prorrogada` | Presença de `prorrogada_ate` | derivável com regra | DMC define flag 1/não nulo (`dmc.json:155,180`); campo de data existe (`schema.py:72`). A coluna booleana não existe no DDL de ingestão. |
| `part_mercado` em `pesquisas.csv` | Campo presente na fonte e convertido para decimal | direto | `schema.py:64`, DDL `:24`. Não foi declarado como métrica do C01; não misturar com `participantes` ou com os dois valores do C02. |

**Conflito de nome do cubo:** tabela-resumo chama C01 “Ciclo de Vida das Pesquisas”, enquanto o heading §5.2.1 e DMC chamam “Portfólio e Ciclo” (`projeto.md:814,833`; `dmc.json:101`). Fixar um rótulo único em CB-02.

### C02 — Participação e Representatividade

**Fato e grão.** O DMC descreve uma linha por registro de `respondentes.csv`, sem presumir pessoa única (`dmc.json:232-244`; `projeto.md:815,964-966`). O esquema não declara chave de negócio para `respondentes`; a identidade de ingestão é a ocorrência física `(source_checksum, source_offset)` (`src/etl/load/ddl.py:38-40,224-233`; DDL `:101-120`). Isso sustenta preservar cada linha, não deduplicar pessoas. `respondentes` não possui coluna `respondent_id`; esse nome pertence a `respostas` (`schema.py:104-110,127-136`).

| Item de C02 | Origem executável e regra disponível | Estado | Evidência e divergência |
| :--- | :--- | :--- | :--- |
| Uma linha por registro/participação; `qtd_participacao` | Linha física em `respondentes.csv`; derivar 1 por linha | derivável com regra | DMC `:232-244`; `projeto.md:978-982`. A contagem é de ocorrências, não de respostas a perguntas nem de pessoas. |
| Identidade de ocorrência do fato | `source_checksum` + `source_offset` (técnico) | direto | DDL `:112-120`; `ddl.py:38-40`. A posição preserva ocorrência, mas não é chave de negócio portável entre arquivos/snapshots. |
| `sk_pesquisa` / pesquisa da participação | `respondentes.id_pesq` → `pesquisa_id` | renomeado | `schema.py:104-105`, DDL `:101-103`; DMC C02; existem 55 ocorrências documentadas com pesquisa 304 sem correspondência (`projeto.md:1506,1969`). O elo órfão permanece em reconciliação. |
| `sk_empresa` / empresa | `respondentes.id_empresa` → `empresa_id`; dimensão de `empresas.ID` → `empresa_id` | renomeado | `schema.py:86-95,108`; DDL `:55-64,101-107`. A chave recebida é preservada; vínculo sem FK analítica criada. |
| `sk_pessoa` / `DIM_PESSOA` / `cliente_id` | `respondentes.id_cliente` → `cliente_id`, comparado a `clientes.id_cliente` → `cliente_id` | renomeado | O alias de coluna está implementado (`schema.py:97-110`; DDL `:80-85,101-107`). Isso é divergência de nome, não coluna ausente. Entretanto, chamar todo `cliente` de pessoa e tratá-lo como identidade conciliada ainda depende de contrato semântico; projeto diz “Cliente/Pessoa somente após conciliação” (`:815,1014-1016`). |
| `id_pessoa_durable` / unicidade pessoa | Nenhuma chave `id_pessoa_durable`; candidato é `cliente_id` reconciliado | dependente de homologação | Diagrama C02 declara `id_pessoa_durable` e `sk_pessoa` (`cubo02.plantuml:48-62,64-81`). Não gerar identidade de pessoa para cliente ausente/sentinela nem supor equivalência com `respostas.respondent_id`. |
| `DIM_PESSOA.cargo`, `departamento` | `clientes.cargo`, `clientes.departamento`, ligados por `cliente_id` | direto | `schema.py:97-103`; DDL `:80-85`; dimensões em `projeto.md:1014-1016`. A presença da coluna não resolve linhas de participação sem cliente conciliado. |
| `email` da origem | `clientes."e-mail"` → `email` | renomeado | `schema.py:102`, DDL `:85`. DMC/projeto excluem e-mail da dimensão analítica por risco de identificação (`projeto.md:1014-1016,1036`); coluna de ingestão existente não autoriza projetá-la no cubo. |
| `nivel_hierarquico`, `agrupamento_departamento` | Candidatos derivados de `cargo` e `departamento` | dependente de homologação | Campos constam no modelo/diagrama (`projeto.md:1014-1016`; `cubo02.plantuml:52-55`), mas não há tabela de mapeamento ou regra executável. |
| `data_inclusao`, `base_legal_finalidade`, `flag_titular_anonimizado`, `data_anonimizacao` | Sem campos nas fontes CSV tratadas | sem origem | Atributos aparecem apenas no diagrama `cubo02.plantuml:58-61`; não são derivados de campos de cadastro atuais. Requerem sistema de governança/identidade futuro. |
| `sk_data_pesquisa` | `pesquisas.data_divulgacao`, ligada por `pesquisa_id` | derivável com regra | Regra explícita em `projeto.md:1018-1020` e DMC. A data existe em `schema.py:68-75`; é uma data herdada da pesquisa, não da ocorrência de participação. Para chaves órfãs, fica indisponível. |
| `sk_data_resposta` | `respondentes.hora_inicio` → calendário | derivável com regra | Timestamp existe (`schema.py:106`, DDL `:103`). Converter em papel diário de `DIM_TEMPO`; cobertura declarada baixa em `projeto.md:1022-1024`. |
| `minutos_preenchimento` | `hora_termino - hora_inicio` | derivável com regra | Regra em `projeto.md:990-994`; ambas as colunas existem. Exige par válido e produzir `NULL` quando faltar qualquer ponta. |
| `pct_mercado_na_participacao` | `respondentes.market_share` | direto | Campo presente/decimal (`schema.py:109`, DDL `:106`). O valor da participação pode ser preservado no seu grão. |
| I09 / participação de mercado agregada | `respondentes.market_share` conflita com `empresas."% de mercado"` → `part_mercado` | dependente de homologação | `projeto.md:996-1000,1034`; ambos os campos físicos existem (`schema.py:64,89,109`; DDL `:24,58,106`). Normalização, autoridade e regra de uma contribuição por empresa distinta não estão aprovadas; não somar registros repetidos. |
| `seq_ocorrencia` para `(pesquisa, pessoa)` | Derivação exige pessoa identificável/reconciliada e chave de agrupamento | dependente de homologação | DMC/projeto definem sequência e dizem haver duplicatas (`dmc.json:241-265`; `projeto.md:984-988,1028`). `seq_ocorrencia` não existe na ingestão. Para `cliente_id` ausente ou sentinela, só há identidade de ocorrência, não de pessoa. |
| `DIM_EMPRESA.nome_fantasia`, `nacionalidade`, `cidade`, `estado`, `pais`, `tipo_associado` | `empresas` mesmas colunas (IDs normalizados); `associado` → `flag_associado` | direto / renomeado | Fontes/campos em `schema.py:86-95`; DDL `:55-64`. `flag_associado` renomeia `associado` (`schema.py:91`; diagrama `cubo02.plantuml:31-40`). |
| `DIM_EMPRESA.pct_mercado` | `empresas."% de mercado"` → `part_mercado` | renomeado | `schema.py:89`, DDL `:58`; não selecionar sobre `market_share` sem homologar I09. |
| `DIM_EMPRESA.regiao` | Nenhuma coluna `regiao`; existe `estado` | dependente de homologação | Atributo aparece no diagrama C02 (`cubo02.plantuml:28-46`), não na lista de dimensões do DMC nem no schema `empresas` (`schema.py:86-95`). Estado → região precisa de tabela/regra geográfica definida; não é renomeação. |
| `faixa_share`, `flag_ja_participou`, `qtd_participacoes`, datas de primeira/última participação, `faixa_engajamento` | Agregações/classificações sobre empresa e fato C02 | dependente de homologação | Atributos extras do diagrama (`cubo02.plantuml:32-45`); não há regras de faixa, janela temporal ou status no DMC/projeto. Alguns podem ser derivados após o fato, mas domínios e semântica precisam aprovação. |

**Identidade: limites de contagem.** A quantidade de linhas de C02 pode ser calculada como ocorrências. A contagem distinta por `empresa_id` pode ser feita após tratar chaves de pesquisa órfãs e define empresa, não pessoa. A contagem distinta por pessoa requer `cliente_id` presente e conciliado. `respondent_id` de `respostas.csv` é outro domínio de ID e o projeto proíbe ponte presumida (`projeto.md:821,1163`; DMC `:434`).

### C03 — Pipeline Mensal

**Fato e grão.** `FATO_PIPELINE_MENSAL` propõe snapshot mensal por competência, status, área, tipo e perfil (`dmc.json:318,321-342`; `projeto.md:816,1041-1045`). Não há histórico de transições nem fotografia histórica antes do go-live.

| Item de C03 | Origem executável e regra disponível | Estado | Evidência e divergência |
| :--- | :--- | :--- | :--- |
| Grão mês × status × área × tipo × perfil | `pesquisas` atual agrupada e congelada no fechamento mensal futuro | derivável com regra | DMC e projeto definem o grão; DDL analítico inexiste. Cada linha precisa da competência e da versão/regra do fechamento. |
| `qtd_pesquisas_no_status` (estoque) | Contar pesquisas no status vigente no fechamento | derivável com regra | DMC define estoque semi-aditivo (`dmc.json:333,357`); fonte fornece status/área/tipo/perfil. Só existe a partir dos snapshots de go-live (`:356`). Nunca somar entre meses. |
| `qtd_entradas_no_mes` | Evento de transição para status durante o mês | sem origem | Não há tabela/evento de transição nas seis fontes. DMC diz que diferenças entre snapshots capturam apenas mudança líquida (`dmc.json:334,352,358`). Disponível somente após integrar histórico de eventos. |
| `qtd_saidas_no_mes` | Evento de transição para fora do status durante o mês | sem origem | Mesmo limite das entradas; DMC declara indisponível sem histórico (`dmc.json:335,352,358`). Não inferir saída individual pelo delta de snapshots. |
| `sk_data_fim_mes`, instante de fechamento, ano/mês/trimestre/flags do calendário | Competência e execução geradas pelo processo de snapshot | derivável com regra | Não são colunas das fontes; o DMC exige fechamento/competência e execução (`dmc.json:315,350-351`). Calendário de dia útil depende de aprovação. |
| `sk_status` / `nome_status` | `pesquisas.status` | direto | Campo na fonte (`schema.py:60`, DDL `:20`); perfil de destino em `cubo-03.plantuml:21-29`. |
| `etapa_ciclo`, `ordem_fluxo`, `flag_em_aberto`, `flag_conta_como_a_finalizar`, `flag_terminal` | Mapeamento governado dos valores de status | dependente de homologação | Atributos do diagrama (`cubo-03.plantuml:21-29`) e DMC `:359`; não existem na ingestão e precisam catálogo de status aprovado/versionado. |
| `sk_area` / `nome_area` | `pesquisas.area` | direto | `schema.py:62`, DDL `:22`; diagrama `cubo-03.plantuml:31-35`. |
| `agrupamento_macro` da área | Mapeamento de área para grupo macro | dependente de homologação | Só no diagrama (`cubo-03.plantuml:31-35`); sem coluna/regra aprovada. |
| `sk_tipo` / `nome_tipo` | `pesquisas.tipo` | direto | `schema.py:61`, DDL `:21`; diagrama `cubo-03.plantuml:37-41`. |
| `natureza_origem` do tipo | Catálogo de tipos ou regra de classificação | dependente de homologação | Só no diagrama (`cubo-03.plantuml:37-41`); não existe como campo na fonte. |
| `sk_perfil.complexidade` | `pesquisas.complexidade` | direto | `schema.py:77`, DDL `:32`; diagrama `cubo-03.plantuml:43-47`. |
| `sk_perfil.tipo_resposta` | `pesquisas."tipo de resposta"` → `tipo_resposta` | renomeado | `schema.py:78`, DDL `:33`; diagrama `cubo-03.plantuml:43-47`. |
| `qtd_a_finalizar` | Não deve ser armazenada; derivar consulta semântica usando flag do status | sem origem | Removida após revisão (`projeto.md:1103`; DMC `dmc.json:353`). A imagem C03 não a inclui. Se `flag_conta_como_a_finalizar` não estiver homologada, a consulta também fica indisponível. |

### C04 — Resultados e Questionários

**Fato e grão.** DMC JSON e Markdown definem uma associação entre `pesquisa_id` e pergunta, `FATO_PESQUISA_PERGUNTA`, factless; `qtd_pergunta` é `COUNT(*)` das associações distintas e `qtd_alternativas` pertence à dimensão, não ao fato (`dmc.json:402,405-423`; `docs/dmc.md:580-608`). A imagem/diagrama PlantUML diverge e precisa ser alinhada.

| Item de C04 | Origem executável e regra disponível | Estado | Evidência e divergência |
| :--- | :--- | :--- | :--- |
| Grão associação pergunta × pesquisa | `questoes` por `(pesquisa_id, pergunta_id)`; `KEYS` declara ambas (`schema.py:112-125,140-145`) | derivável com regra | DMC `:405-408`; a ingestão conserva versões de conteúdo (`001_ingestao_tratada.sql:123-150`), então usar estado atual/deduplicação explícita antes de contar associação. |
| Fato `FATO_PESQUISA_PERGUNTA` | Associação das chaves pesquisa e pergunta, sem medidas armazenadas | derivável com regra | Nome no Mermaid JSON `:402` e regra factless/contagem `:408,417-418`; projeto §5.2.4 `:1115-1127`. A associação deduplicada é derivável dos registros de `questoes`; a tabela fato não existe no DDL. |
| `FATO_INSTRUMENTO` e 4 medidas do diagrama | A imagem/PlantUML chama o fato `FATO_INSTRUMENTO` e lista `qtd_pergunta`, `qtd_alternativas`, `qtd_linhas_matriz`, `qtd_colunas_matriz` | dependente de homologação | Conflito de nome com `FATO_PESQUISA_PERGUNTA` (`cubo-04.plantuml:45-58` vs. `dmc.json:402`). Os quatro campos na imagem contradizem o fato sem medidas do texto; `qtd_alternativas` contradiz a decisão de atributo da dimensão. `qtd_linhas_matriz`/`qtd_colunas_matriz` não têm fórmula, tipo, nulabilidade ou aditividade no contrato. |
| `sk_pesquisa` / `pesquisa_id` original | `questoes.pesquisa_id`; quando correspondente, liga a `pesquisas.pesquisa_id` | direto | Coluna obrigatória na transformação (`schema.py:112-115`) e DDL (`:123-126`); dimensão/fato no DMC `:421-423`. Vínculos sem correspondência ficam em reconciliação. |
| `pesquisa_titulo` para eventual fallback | Coluna recebida em `questoes.csv` | dependente de homologação | Campo existe (`schema.py:115`, DDL `:126`), mas existência do título não valida identidade. §5.2.4 afirma fallback exato já aplicado para 4 IDs (`projeto.md:1159`); DMC atual exige estado em reconciliação e fallback exato auditável (`dmc.json:433-439`). Tratar título como candidato; não canonicalizar sem reconciliação registrada. |
| `sk_pergunta` / `id_pergunta` | `questoes.id_pergunta` → `pergunta_id`; chave da origem é o par pesquisa+pergunta | renomeado | `schema.py:112-114,140-145`, DDL `:123-125`; imagem C04 traz `id_pergunta`. Não presumir unicidade global sem `pesquisa_id`. |
| `DIM_PERGUNTA.enunciado` | `questoes.enunciado` | direto | `schema.py:116`, DDL `:127`; DMC `:422`. |
| `DIM_PERGUNTA.tipo_pergunta` | `questoes.tipo` | renomeado | `schema.py:117`, DDL `:128`; imagem usa `tipo_pergunta` (`cubo-04.plantuml:30-43`). |
| `DIM_PERGUNTA.qtd_alternativas` | `questoes.qtd_alternativas` | direto | `schema.py:118`, DDL `:129`; DMC `:418,422`. Atributo da dimensão, nunca somado repetidamente por associação. |
| `alternativas`, `linhas_matriz`, `colunas_matriz` | Mesmo nome em `questoes.csv`; listas serializadas em JSON/VARCHAR | direto | `schema.py:119-121`; DDL `:130-132`. Contagem de linhas/colunas exigiria regra sobre listas válidas; não há measure rule aprovada. |
| `nivel_confianca` | `questoes.confianca` | renomeado | DDL contém `confianca` (`:133`); imagem usa `nivel_confianca` (`cubo-04.plantuml:39`). |
| `formato_arquivo_origem` | `questoes.formato_arquivo` | renomeado | `schema.py:123`, DDL `:134`; imagem `cubo-04.plantuml:40`. |
| `col_origem` | `questoes.col_origem` | direto | `schema.py:124`, DDL `:135`; imagem `cubo-04.plantuml:41`. |
| `flag_pergunta_perfil` | Nenhuma coluna ou regra de classificação de pergunta | sem origem | Só está na imagem (`cubo-04.plantuml:42`); exige requisito e classificação antes de entrar no contrato. |
| `qtd_pergunta` | `COUNT(*)` após deduplicar associações distintas no grão | derivável com regra | `dmc.json:417,430-431`; não é coluna constante do fato. |
| `qtd_alternativas` como medida do fato | Sem coluna/regra que autorize tratá-la como medida do fato; o valor recebido é atributo da pergunta | sem origem | **Sem origem como medida.** O atributo está disponível, mas a *medida de fato* está explicitamente rejeitada por DMC (`dmc.json:418,431`) e contradiz PlantUML `:50-53`. |
| `respostas.csv` / futura `FATO_RESPOSTA` | `resposta_id`, `pesquisa_id`, `pergunta_id`, `respondent_id`, `empresa_id`, elemento de resposta | dependente de homologação | Campos são executáveis (`schema.py:127-136`; DDL `:152-161`), mas C04 atual usa `questoes.csv`; ponte de `respondent_id` para participação/cliente não foi comprovada (`projeto.md:821,1163`; DMC `:434,446`). Indicadores sobre resposta não transformam este fato em FATO_RESPOSTA. |
| Contagem/cobertura “231 linhas / 10 de 366 pesquisas / 2,7%” | Snapshot antigo da Sprint 2 | dependente de homologação | `projeto.md:1117,1161` ainda apresenta como atual. DMC JSON registra que v3 de `questoes.csv` tem 3.297 registros e manda recalcular cobertura e vínculos (`dmc.json:406-409`); `docs/inventario-fontes-etl.md:19` registra 3.297. Não divulgar 231/10 como situação atual. |
| IDs 424, 1116, 1139 e 1147 sem correspondência direta | `questoes.pesquisa_id`; `pesquisa_titulo` candidato | dependente de homologação | DMC mantém os quatro em reconciliação e fala em fallback auditável (`dmc.json:433-439`). §5.2.4 afirma correspondência exata já feita e ligação por título (`projeto.md:1159`): afirmação mais forte sem contrato/mapeamento executável citado. Fallback não é chave canônica aprovada. |
| `sk_data_pesquisa` | `pesquisas.data_divulgacao`, herdada via vínculo de pesquisa | derivável com regra | `projeto.md:1153-1155`; DMC `:423,427`. Sem vínculo de pesquisa reconciliado, a data não é comprovada. |

## Contradições entre artefatos a resolver em CB-02

1. **Nome de C01:** resumo do projeto “Ciclo de Vida das Pesquisas” vs. heading/DMC “Portfólio e Ciclo” (`projeto.md:814,833`; `dmc.json:101`).
2. **C01 data útil e calendário:** §5.2 rotula diferenças de datas como `dias_uteis_*` sem a ressalva do calendário (`projeto.md:849-870`); DMC manda rotular como dias corridos até calendário homologado (`dmc.json:149-152,177-179`). Existem quatro colunas de duração declaradas na ingestão (`schema.py:76-84`), mas nenhuma equivalência aprovada entre elas e aquelas diferenças.
3. **C01 papéis de tempo:** diagrama Mermaid diz sete; lista e imagem enumeram seis.
4. **C01 medida removida:** projeto e DMC dizem que `qtd_respondentes_na_pesquisa` saiu do cubo; imagem `cubo-01.png` ainda a mostra.
5. **C02 pessoa/cliente:** `cliente_id` é renomeação executável de `id_cliente`, mas a identidade “pessoa” é condicional à conciliação (`projeto.md:815,1014-1016`). Diagrama assume `DIM_PESSOA`/`sk_pessoa` e `id_pessoa_durable` (`cubo02.plantuml:48-81`). A ingestão só garante identidade de ocorrência para participação, e valores de cliente podem faltar (`ddl.py:38-40`; schema `:104-110`). Não unir com `respostas.respondent_id`.
6. **C02 `regiao`:** só no diagrama; `estado` existe, mas não autoriza uma região sem regra geográfica.
7. **C03 fluxos:** lista de medidas enumera entradas/saídas, mas a própria definição condiciona cálculo a histórico de transições; esse histórico não é uma das seis fontes. Manter indisponível até integração, e não calcular fluxo por delta líquido.
8. **C03 quantidade a finalizar:** removida do fato, usar `flag_conta_como_a_finalizar`; flag precisa de catálogo de status homologado.
9. **C04 nome/natureza e medidas:** DMC textual/JSON = `FATO_PESQUISA_PERGUNTA`, factless; diagrama fonte = `FATO_INSTRUMENTO`, com quatro campos de medida. `qtd_pergunta` é derivada; `qtd_alternativas` é atributo; duas contagens de matriz não têm regra.
10. **C04 vínculos e cobertura:** projeto §5.2 diz fallback exato já realizado e números 231/10 atuais; DMC mantém quatro IDs em reconciliação e marca a fotografia antiga, com v3 em 3.297 questões. Recalcular antes de publicar cobertura; só promover fallback depois de trilha e homologação.

## Estado do inventário anterior

`docs/inventario-contratos-dimensionais.md` contém observações úteis, mas não é autoridade para o estado atual nem substitui esta matriz: diz que `schema.py` está numa branch não incorporada (`:47-52`), embora o esquema e o DDL estejam no checkout atual; chama `cliente` e `pessoa` de “mesmo dado com rótulo diferente” sem ressalva semântica (`:118-121`); e registra C04 como `FATO_INSTRUMENTO`/fallback por título (`:157-167`). Esses trechos precisam ser revisados junto com CB-02 para não perpetuar status e nomes divergentes.

## Contagem desta matriz

A contagem é sobre as linhas das quatro tabelas, contando cada linha uma vez; a linha com status composto `direto / renomeado` é um mapeamento parcial. Totais: **direto 22; renomeado 12; derivável com regra 13; sem origem 7; dependente de homologação 20; parcial 1**. Total: **75 itens de matriz**. Estes totais contam linhas, não colunas físicas nem decisões já homologadas.
