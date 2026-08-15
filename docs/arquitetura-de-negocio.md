# **Arquitetura de Negócio**

*Central de Pesquisas do Sindusfarma*

# **Introdução e Contexto**

A Arquitetura de Negócio da Central de Pesquisas foi revisada a partir do **Data Model Canvas**, do escopo definido no TAPI e da análise direta das bases de dados disponibilizadas. Essa inclusão altera principalmente o pilar de **Informações**, permitindo refinar as capacidades de negócio e o fluxo de valor.

**Objetivos Estratégicos:**

* Aumentar adesão e engajamento;  
* Reduzir esforço manual e tempo de entrega;  
* Apoiar decisões estratégicas e estabelecer governança;  
* Garantir conformidade com a LGPD.

A V2 também considera uma ideia importante de Arquitetura Empresarial: a arquitetura deve servir às decisões e resultados do negócio, e não apenas documentar sistemas. A literatura fornecida sobre Enterprise Architecture reforça justamente a necessidade de conectar arquitetura a decisões estratégicas, reutilização e capacidade de evolução da organização.

# **1\. Fontes de Dados (V2)**

O TAPI registra originalmente quatro bases principais: `pesquisas.csv`, `clientes.csv`, `respondentes.csv` e `empresas.csv`. Com os arquivos adicionais recebidos, o panorama observado passa a ser de **sete conjuntos de dados de negócio**, além de um dicionário de variáveis.

| Fonte | Dimensão observada | Papel no negócio |
| ----- | ----- | ----- |
| **`pesquisas.csv`** | 366 registros × 33 colunas | Cadastro e acompanhamento do ciclo de vida das pesquisas |
| **`empresas.csv`** | 779 × 9 | Cadastro das empresas e características estratégicas |
| **`clientes.csv`** | 5.430 × 5 | Cadastro de pessoas ligadas às empresas |
| **`respondentes.csv`** | 18.735 × 6 | Registro da participação de clientes/empresas nas pesquisas |
| **`questoes.csv`** | 231 × 13 | Estrutura dos questionários e perguntas |
| **`respostas.csv`** | 20.607 × 9 | Respostas coletadas nas pesquisas |
| **Dicionário de variáveis** | 9 variáveis documentadas | Definição do significado e uso analítico das colunas |

Isso revela uma arquitetura informacional mais rica do que a apresentada inicialmente. Não existem apenas dados sobre **pesquisas, empresas, clientes e respondentes**: há também uma camada explícita de **questionário e respostas**, fundamental para representar a execução da pesquisa.

O dicionário atual descreve exatamente as nove variáveis presentes em `respostas.csv`, incluindo unidade de análise, tipo da variável, domínio esperado e análises adequadas. Portanto, ele já funciona como um primeiro artefato de governança, embora ainda precise ser ampliado para as outras seis bases.

# **2\. Pilar 1 — Capacidades de Negócio**

As capacidades representam aquilo que a Central de Pesquisas precisa conseguir realizar para entregar valor. Com as novas fontes, algumas capacidades da V1 podem ser refinadas.

| Capacidade | Descrição |
| ----- | ----- |
| **Gestão do ciclo de vida das pesquisas** | Registrar e acompanhar uma pesquisa desde a solicitação até sua entrega e publicação, incluindo status, área, tipo, datas, participantes e prazos. |
| **Planejamento e estruturação de questionários** | Estruturar perguntas, alternativas, matrizes e formatos de resposta antes da coleta. |
| **Validação técnica das pesquisas** | Revisar conteúdo e estrutura dos questionários junto às áreas técnicas antes da divulgação. |
| **Gestão da participação das empresas** | Identificar empresas convidadas ou participantes e acompanhar adesão ao longo das pesquisas. |
| **Gestão de respondentes** | Relacionar participantes às empresas, cargos e departamentos, permitindo compreender quem está efetivamente engajado. |
| **Gestão da coleta de respostas** | Receber e organizar respostas de múltipla escolha, caixas de seleção, matrizes, campos numéricos e respostas abertas. |
| **Gestão do desempenho operacional** | Monitorar tempo entre solicitação, divulgação, encerramento e entrega, além de prorrogações e pesquisas em aberto. |
| **Análise de adesão e engajamento** | Avaliar participação por pesquisa, empresa, departamento, cargo, área e período. |
| **Gestão da qualidade dos dados** | Validar chaves, campos obrigatórios, domínios, duplicidades e consistência entre fontes. |
| **Governança e rastreabilidade** | Controlar origem, significado, acesso e responsabilidade sobre as informações. |
| **Inteligência de negócio** | Transformar os dados consolidados em indicadores operacionais e estratégicos. |
| **Publicação e disponibilização de resultados** | Disponibilizar resultados permitidos para solicitantes e participantes, mantendo consistência com os dados internos. |

A principal evolução em relação à V1 é a separação entre **gerenciar a pesquisa**, **gerenciar o questionário**, **gerenciar a participação** e **gerenciar as respostas**. Os dados mostram que esses são objetos diferentes do negócio e, portanto, não devem ser tratados como uma única capacidade genérica.

---

# **3\. Pilar 2 — Fluxo de Valor**

O fluxo de valor central pode ser definido como:

***"Transformar uma necessidade de informação do setor farmacêutico em conhecimento estruturado e confiável."***

O Data Model Canvas já descreve as principais etapas desse processo, da solicitação à publicação. A análise das bases permite agora associar cada etapa às informações realmente utilizadas ou produzidas.

| Etapa | Atividade | Principais informações | Fontes relacionadas |
| ----- | ----- | ----- | ----- |
| **1\. Solicitação** | Registrar a necessidade de uma nova pesquisa | título, tipo, área, objetivo, solicitante e data | `pesquisas.csv` |
| **2\. Triagem e aprovação** | Avaliar a demanda e decidir sua continuidade | status, aprovação, prioridade e responsáveis | `pesquisas.csv` |
| **3\. Planejamento** | Definir cronograma e questionário | datas, complexidade, perguntas, alternativas e formato | `pesquisas.csv, questoes.csv` |
| **4\. Validação técnica** | Validar o conteúdo com a área responsável | questionário, estrutura e alterações | `questoes.csv, informações operacionais` |
| **5\. Divulgação** | Disponibilizar a pesquisa aos participantes | pesquisa ativa, data de divulgação e prazo | `pesquisas.csv` |
| **6\. Coleta e monitoramento** | Acompanhar empresas e pessoas participantes | empresa, participante, horários, market share | `respondentes.csv, clientes.csv, empresas.csv` |
| **7\. Registro das respostas** | Capturar as respostas de cada questionário | pergunta, respondente, alternativa, matriz e valor | `respostas.csv, questoes.csv` |
| **8\. Encerramento e validação** | Verificar completude e consistência dos dados recebidos | respostas válidas, campos ausentes e inconsistências | `respostas.csv, dicionário` |
| **9\. Tabulação e análise** | Consolidar as respostas e produzir indicadores | resultados, participação, adesão e segmentações | conjunto integrado das bases |
| **10\. Entrega e publicação** | Entregar resultados e disponibilizar o conteúdo autorizado | data de entrega, resultado e publicação | `pesquisas.csv + repositório` |

A arquitetura proposta não modifica a lógica essencial desse processo. O ganho está em evitar que cada etapa seja uma ilha.

Hoje, conforme o problema descrito pelo parceiro, as ferramentas são consolidadas individualmente, mas não existe integração estruturada que acompanhe o dado ao longo do fluxo inteiro.

Na arquitetura-alvo, cada etapa **produz informações que permanecem conectadas à mesma pesquisa**, permitindo rastreabilidade da demanda até o resultado.

---

# **4\. Pilar 3 — Estrutura de Informações**

Este é o pilar que mais evolui na V2.

A análise das bases mostra que a arquitetura de informações pode ser organizada em sete objetos principais.

## **4.1 Pesquisa**

Abaixo estão detalhados os principais objetos de negócio identificados nas bases de dados:

`pesquisas.csv` contém informações como:

* título;  
* status;  
* tipo;  
* área;  
* número de participantes;  
* participação de mercado;  
* datas de solicitação, divulgação, limite, prorrogação e entrega;  
* complexidade;  
* tipo de resposta;  
* tempo de preenchimento;  
* objetivo;  
* tempos operacionais.

Assim, **Pesquisa** funciona como o elemento que organiza todo o ciclo.

O arquivo também possui colunas vazias provenientes da exportação (`Unnamed`), que não representam informação de negócio e não devem fazer parte do modelo canônico.

## **4.2 Empresa**

`empresas.csv` representa as organizações relacionadas às pesquisas.

Entre as informações disponíveis estão:

* identificador;  
* nome;  
* participação de mercado;  
* nacionalidade;  
* condição de associado;  
* tipo de associado;  
* cidade;  
* estado;  
* país.

Esse objeto é necessário para análises previstas no próprio Data Model Canvas, como participação por empresa, diferença entre empresas nacionais e multinacionais, empresas sem participação e representatividade de mercado.

## **4.3 Cliente / Pessoa**

`clientes.csv` funciona como o cadastro de pessoas vinculadas às empresas.

Ele contém:

* `id_cliente`;  
* `id_empresa`;  
* cargo;  
* departamento;  
* e-mail.

A V1 tratava “cliente” e “respondente” de forma bastante próxima. Os dados mostram que é útil separá-los.

**Cliente** representa a pessoa conhecida pela Central, enquanto a participação dela em uma pesquisa é outro evento.

Essa distinção também é relevante para LGPD, pois essa base possui informações pessoais e de contato.

## **4.4 Participação na pesquisa**

Apesar do nome `respondentes.csv`, o conteúdo do arquivo se comporta principalmente como um **registro de participação**.

Cada registro relaciona:

**Pesquisa \+ Empresa \+ Cliente**

e inclui, quando disponível:

* horário de início;  
* horário de término;  
* market share.

Por isso, conceitualmente, essa informação pode ser tratada na arquitetura como:

**Participação em Pesquisa**

em vez de ser considerada somente um cadastro de respondentes.

Essa mudança é importante porque permite distinguir:

**Pessoa** → quem é o participante  
**Participação** → em qual pesquisa ele participou

## **4.5 Questão**

`questoes.csv` adiciona um objeto que não aparecia de forma explícita na V1.

Cada questão possui:

* pesquisa;  
* título da pesquisa;  
* enunciado;  
* tipo;  
* número e lista de alternativas;  
* linhas e colunas de matrizes;  
* nível de confiança;  
* formato de origem.

Foram identificados cinco tipos de questão:

* múltipla escolha;  
* caixas de seleção;  
* matriz de avaliação;  
* numérica;  
* aberta.

Isso significa que a arquitetura não deve considerar o questionário apenas como um arquivo associado à pesquisa. **Perguntas são objetos estruturados do negócio**, utilizados posteriormente para interpretar as respostas.

## **4.6 Resposta**

`respostas.csv` contém 20.607 registros associados às 231 questões existentes em `questoes.csv`.

O dicionário fornecido esclarece a função das nove variáveis:

`id_resposta`, `pesquisa_id`, `id_pergunta`, `respondent_id`, `id_empresa`, `alternativa`, `linha_matriz`, `coluna_matriz` e `valor`.

Um ponto importante é que **uma linha de `respostas.csv` não representa necessariamente um questionário completo respondido por uma pessoa**.

Questões com checkbox ou matriz podem gerar diversos registros para a mesma combinação de respondente e pergunta. Portanto, a granularidade correta é mais próxima de:

> **um elemento de resposta de um respondente para uma pergunta de uma pesquisa.**

Isso precisa ser respeitado ao construir KPIs. Contar linhas de `respostas.csv`, por exemplo, **não equivale a contar respondentes**.

## **4.7 Metadados e Dicionário**

O dicionário deixa de ser apenas documentação auxiliar e passa a ser um objeto importante da arquitetura.

Ele define para cada variável:

* significado;  
* unidade de análise;  
* tipo;  
* domínio esperado;  
* análise adequada.

Na arquitetura-alvo, esse conceito deve ser expandido para todas as bases.

O catálogo de dados previsto no Data Model Canvas já aponta nessa direção, propondo registrar entidades, campos, tipos, origens, regras e responsáveis.

# **5\. Relações e Integração**

A partir dos arquivos recebidos, a estrutura conceitual pode ser resumida assim:

**EMPRESA**

↓

**CLIENTE / PESSOA** ◄─── possui ─── **EMPRESA** ─── participa ───► **PARTICIPAÇÃO**

↑

**PESQUISA**

│

├── possui ──► **QUESTÃO** ──► recebe ──► **RESPOSTA**

│

└── gera ──► **RESULTADO / PUBLICAÇÃO**

Essa estrutura é mais próxima do que os dados efetivamente representam do que uma arquitetura baseada somente em quatro cadastros independentes.

# **6\. Pontos de integração identificados**

A análise dos arquivos também evidencia quais relações já estão relativamente bem estabelecidas e quais precisam ser governadas.

### **Relações observadas**

`empresas.ID` funciona como referência para empresas encontradas em `clientes`, `respondentes` e `respostas`.

Os `id_cliente` preenchidos em `respondentes.csv` encontram correspondência no cadastro de `clientes.csv`.

As 231 combinações de pesquisa/pergunta presentes em `questoes.csv` possuem registros correspondentes em `respostas.csv`.

Isso mostra que existe uma base concreta para integração.

### **Identidades que precisam ser conciliadas**

Há, entretanto, um ponto importante na identificação das pesquisas.

`respondentes.csv` utiliza principalmente IDs compatíveis com o histórico de `pesquisas.csv`, enquanto `questoes.csv` e `respostas.csv` incluem identificadores como `424`, `1116`, `1139` e `1147`, que não aparecem como `id` no arquivo atual de pesquisas.

Isso sugere que existem **identificadores provenientes de contextos ou sistemas diferentes**, algo coerente com o cenário de múltiplas ferramentas descrito pelo parceiro.

Portanto, a arquitetura não deve assumir que todo campo chamado `pesquisa_id` possui automaticamente o mesmo domínio.

Uma solução conceitual importante é estabelecer uma **identidade canônica da pesquisa**, mantendo também o identificador utilizado por cada sistema de origem.

Também não existe, nos arquivos desta versão, uma chave explícita ligando:

`respostas.respondent_id`

a

`respondentes.id_cliente`.

Essa ligação precisa ser compreendida antes que análises individuais de resposta e histórico de participação sejam tratadas como completamente integradas.

# **6\. Qualidade e Governança**

Os dados reforçam que qualidade não deve ser tratada apenas como uma etapa técnica do pipeline.

Alguns exemplos observados:

* `empresas.csv` possui variações como `Sim` e `sim`;  
* o campo país contém formas como `Brasil`, `BRASIL` e `brasil`;  
* existem campos históricos com baixa completude;  
* `data_aprov` está preenchida apenas em uma parcela das pesquisas;  
* os horários de início e término aparecem em uma pequena parte de `respondentes.csv`;  
* várias colunas de `pesquisas.csv` são apenas resíduos vazios da exportação.

Ao mesmo tempo, nem todo campo vazio representa um erro.

O próprio dicionário ajuda a demonstrar isso em `respostas.csv`: `alternativa`, `valor`, `linha_matriz` e `coluna_matriz` dependem do **tipo da pergunta**.

Uma pergunta aberta naturalmente não precisa possuir `linha_matriz`. Uma pergunta em matriz, por outro lado, depende desse campo.

Por isso, a regra correta não deve ser:

> “todo campo nulo é um problema”.

Ela deve ser:

> **“cada tipo de informação possui uma regra própria de completude e validade”.**

Essa distinção será essencial para que os futuros indicadores de qualidade sejam confiáveis.

# **8\. Pilar 4 — Estrutura Organizacional**

A estrutura organizacional continua baseada nos papéis definidos pelo parceiro, mas a existência de informações mais granulares deixa mais clara a responsabilidade de cada ator.

O Data Model Canvas identifica Fabio Moreira como Data Owner; Felipe Rojas, Reinaldo Nobrega e Lucas Andrade como Data Stewards e responsáveis técnicos; e Rodrigo Giorgetto/TI como Data Custodian, além da participação da RentalHost na custódia externa.

| Ator | Responsabilidade na Arquitetura de Negócio |
| ----- | ----- |
| **Gestor da Central / Data Owner** | Define prioridades, regras de negócio e uso esperado das informações. |
| **Data Stewards** | Definem significado, regras de qualidade, relacionamento e uso correto dos dados. |
| **Equipe da Central de Pesquisas** | Opera o ciclo das pesquisas e mantém informações necessárias ao acompanhamento. |
| **Áreas técnicas** | Validam questionários e conteúdo técnico e acompanham pesquisas relacionadas às suas áreas. |
| **TI / Data Custodian** | Garante armazenamento, disponibilidade, segurança e sustentação da infraestrutura. |
| **RentalHost e sistemas externos** | Mantêm componentes e informações presentes em ambientes externos sob sua responsabilidade. |
| **Gestores do Sindusfarma** | Consomem indicadores consolidados para decisões operacionais e estratégicas. |
| **Empresas participantes** | Fornecem dados por meio de seus participantes e consomem resultados permitidos. |
| **Respondentes** | Fornecem as respostas que constituem o principal insumo analítico das pesquisas. |

A expansão do dicionário também precisa ter responsabilidade definida. Não basta possuir documentação dos campos: alguém deve responder por sua definição, atualização e validação. Esse papel se encaixa diretamente nas atribuições de Data Steward.

---

# **7\. Conclusão e Próximos Passos**

# 

| Fluxo de Valor | Capacidades necessárias | Informações principais | Estrutura envolvida |
| ----- | ----- | ----- | ----- |
| Solicitar e aprovar | Gestão do ciclo | Pesquisa, área, solicitante, status | Central, gestor |
| Planejar | Planejamento | Pesquisa, cronograma | Central |
| Construir questionário | Gestão de questionários | Questões, alternativas, tipos | Central, áreas técnicas |
| Validar | Validação técnica | Questionário validado | Áreas técnicas |
| Divulgar | Gestão operacional | Pesquisa, prazo, público | Central |
| Coletar | Gestão da participação | Empresa, cliente, participação | Central, empresas |
| Responder | Gestão das respostas | Questão, resposta, respondente | Participantes |
| Validar dados | Qualidade e governança | Respostas, regras, dicionário | Central, Data Stewards |
| Analisar | Inteligência de negócio | KPIs, adesão, tempos e respostas | Central, gestores |
| Publicar | Gestão do acervo | Resultado e publicação | Central, participantes |

# **10\. Arquitetura de Negócio alvo**

A arquitetura-alvo pode ser sintetizada em três movimentos.

**No cenário atual:**

**Pesquisa**

▼

*Múltiplas Ferramentas*

▼

Dados e Identificadores Distribuídos

▼

Cruzamentos e Validações Manuais

▼

**Indicadores e Publicação**

**Na arquitetura desejada:**

**Necessidade de Informação**

▼

**PESQUISA**

┌───────────────┴───────────────┐

**Questionário** ─── **Participantes** ─── **Empresas**

└───────────────┬───────────────┘

▼

**RESPOSTAS INTEGRADAS**

▼

Indicadores e Análises ──► Resultado e Publicação

▼

**Decisão e Conhecimento Setorial**

O ponto central dessa arquitetura é que a **Pesquisa passa a funcionar como o eixo de rastreabilidade**, enquanto Empresa, Cliente, Participação, Questão e Resposta formam objetos relacionados a ela.

Com isso, a iniciativa deixa de representar apenas a criação de um banco central e passa a sustentar uma mudança no próprio modelo operacional da Central: **cada informação passa a ter significado, origem, relacionamento e responsabilidade definidos ao longo de todo o ciclo da pesquisa**.

Essa visão está alinhada ao objetivo estabelecido no projeto de evoluir de dados fragmentados para uma fonte única, rastreável e governada, sem substituir as ferramentas operacionais existentes.

### **Evolução principal da V1 para a V2**

A V1 partia principalmente do que o negócio dizia precisar. A V2 mantém essa visão, mas a confronta com **como os dados realmente estão estruturados**.

Isso revelou quatro pontos que devem orientar as próximas decisões do projeto:

1. **Pesquisa, questionário, participação e resposta são objetos de negócio diferentes**, embora façam parte do mesmo ciclo.  
2. **`respondentes.csv` representa principalmente participação**, enquanto `clientes.csv` funciona como cadastro de pessoas.  
3. **os identificadores entre fontes precisam ser governados**, especialmente os IDs de pesquisa e a relação entre `respondent_id` e `id_cliente`;  
4. **o dicionário de dados deve evoluir de um dicionário de `respostas.csv` para um catálogo integrado de todas as sete fontes**, tornando-se parte formal da governança da solução.

Esses pontos tornam a Arquitetura de Negócio mais aderente tanto ao Data Model Canvas quanto às evidências presentes nas bases disponibilizadas.

