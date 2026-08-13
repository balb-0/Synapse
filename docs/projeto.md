<Table>
  <tr>
    <td><a href= "link"><img src="img/logo.png" alt="Nome" border="0"></td>
    <td>
      <a href= "https://www.inteli.edu.br/"><img src="img/logo-Inteli.png" alt="Inteli - Instituto de Tecnologia e Liderança" border="0"></a>
    </td>
  </tr>
</table>

# Nome do Projeto: <nome do projeto>

## Nome do Grupo: <nome do grupo>

## Integrantes:

- <a href="https://www.linkedin.com/in/username/">Nome</a>
- <a href="https://www.linkedin.com/in/username/">Nome</a>
- <a href="https://www.linkedin.com/in/username/">Nome</a>
- <a href="https://www.linkedin.com/in/username/">Nome</a>
- <a href="https://www.linkedin.com/in/username/">Nome</a>
- <a href="https://www.linkedin.com/in/username/">Nome</a>
- <a href="https://www.linkedin.com/in/username/">Nome</a>

# Sumário

- [1. Introdução](#1-introdução)
- [2. Descrição do Problema](#2-descrição-do-problema)
- [3. Objetivos](#3-objetivos)
- [4. Arquitetura de Dados (ISO/IEC 10746)](#4-arquitetura-de-dados-isoiec-10746)
  - [4.0 Estado Atual (AS-IS)](#40-estado-atual-as-is)
  - [4.1 Visão de Informação](#41-visão-de-informação-information-viewpoint)
  - [4.2 Visão de Tecnologia](#42-visão-de-tecnologia-technology-viewpoint)
  - [4.3 Visão de Engenharia](#43-visão-de-engenharia-engineering-viewpoint)
  - [4.4 Aspectos Não Funcionais](#44-aspectos-não-funcionais)
- [5. Modelagem Dimensional e Cubos OLAP](#5-modelagem-dimensional-e-cubos-olap)
  - [5.1 Visão Geral do Modelo Dimensional (Data Model Canvas)](#51-visão-geral-do-modelo-dimensional-data-model-canvas)
  - [5.2 Cubos Analíticos](#52-cubos-analíticos)
  - [5.3 Qualidade e Validação de Dados](#53-qualidade-e-validação-de-dados)
  - [5.4 Rastreabilidade Analítica](#54-rastreabilidade-analítica)
  - [5.5 Infraestrutura de Dados](#55-infraestrutura-de-dados)
  - [5.6 Mapa de Cobertura de Indicadores](#56-mapa-de-cobertura-de-indicadores)
  - [5.7 Mapa de Cobertura de Dashboards](#57-mapa-de-cobertura-de-dashboards)
- [6. Requisitos e Governança de Dados](#6-requisitos-e-governança-de-dados)
  - [6.1 Requisitos Funcionais](#61-requisitos-funcionais)
  - [6.2 Requisitos Não Funcionais (ISO/IEC 25010)](#62-requisitos-não-funcionais-isoiec-25010)
  - [6.3 Perguntas de Negócio](#63-perguntas-de-negócio)
  - [6.4 Indicadores e Métricas de Negócio](#64-indicadores-e-métricas-de-negócio)
  - [6.5 Dashboards Analíticos](#65-dashboards-analíticos)
  - [6.6 Governança, Segurança da Informação e LGPD](#66-governança-segurança-da-informação-e-lgpd)
- [7. Referências](#7-referências)
- [8. Avaliação dos Resultados](#8-avaliação-dos-resultados)
  - [8.1 Resultados Quantitativos](#81-resultados-quantitativos)
  - [8.2 Diagnóstico Qualitativo](#82-diagnóstico-qualitativo)
  - [8.3 Tabela de Fontes e Auditabilidade](#83-tabela-de-fontes-e-auditabilidade)

# 1. Introdução

_conteúdo_

**Nota:** Contextualizar o projeto em uma frase de propósito e apresentar, em alto nível, o que este documento cobre (arquitetura de dados, modelagem dimensional, requisitos, governança e avaliação).

# 2. Descrição do Problema

_conteúdo_

**Nota:** Descrever a dor de negócio que o projeto ataca — fragmentação das fontes, esforço manual, baixa rastreabilidade/qualidade, ausência de fonte única da verdade.

# 3. Objetivos

**Objetivo geral:** Construir a espinha dorsal de dados da Central de Pesquisas do Sindusfarma — integrando as fontes hoje dispersas (planilhas, formulários de coleta, gestão de tarefas e o repositório publicado), centralizando-as em um banco de dados na nuvem e sustentando governança, qualidade e visualização do dado ao longo de todo o ciclo de vida das pesquisas.[<sup>\[1\]</sup>](#7-referências)

**Objetivos específicos:** cada objetivo traz o valor gerado ao parceiro e o indicador que permite acompanhá-lo (ver seção 6.4 — Indicadores e Métricas de Negócio). A definição parte dos documentos do projeto disponibilizados pela faculdade e pelo parceiro.[<sup>\[1\]</sup>](#7-referências)[<sup>\[2\]</sup>](#7-referências)[<sup>\[3\]</sup>](#7-referências)

| Objetivo (verbo de ação) | Valor para o parceiro | Como é medido |
| :--- | :--- | :--- |
| Integrar as fontes de dados hoje dispersas em um repositório central único | Elimina os cruzamentos manuais entre ferramentas e estabelece uma fonte única da verdade | Percentual de fontes integradas e completude dos registros consolidados |
| Garantir rastreabilidade ponta a ponta do ciclo de vida da pesquisa, da solicitação à publicação | Auditabilidade e confiabilidade em cada etapa, sem conferência manual | Percentual de pesquisas com todas as etapas do ciclo registradas |
| Reduzir o esforço manual e o tempo de entrega das pesquisas | Libera a capacidade da equipe da Central para análise em vez de tabulação | Tempo médio, em dias úteis, de validação, coleta, tabulação e do ciclo total |
| Ampliar a adesão e o engajamento das indústrias participantes | Pesquisas mais representativas e maior relevância setorial | Taxa de adesão por pesquisa e por empresa; número de respondentes únicos no período |
| Sustentar decisões estratégicas com dashboards operacionais e estratégicos atualizados automaticamente | Visão consolidada e data-driven em tempo real, sem atualização manual do painel | Volume de pesquisas por período e indicadores de status a partir do banco central |
| Assegurar governança, segurança da informação e conformidade com a LGPD no tratamento de dados de empresas e de respostas individuais | Proteção dos dados dos participantes e conformidade regulatória | Percentual de completude e validade dos campos; cobertura do controle de acesso por perfil |

# 4. Arquitetura de Dados (ISO/IEC 10746)

_conteúdo_

**Nota:** Descrever a arquitetura da solução de dados pelos pontos de vista (Viewpoints) da ISO/IEC 10746 (RM-ODP). A §4.0 registra o ponto de partida (AS-IS); as §4.1 a §4.4 descrevem a proposta (TO-BE) e servem de linha de base para a avaliação da §8.

## 4.0 Estado Atual (AS-IS)

_conteúdo_

**Nota:** Diagnóstico do cenário atual, com fonte (workshop/entrevista com o parceiro, TAPI, análise das bases). É o ponto de comparação para o TO-BE.

### 4.0.1 Fontes de dados e ferramentas atuais

As bases disponibilizadas pelo parceiro são seis arquivos CSV estruturados (separador `;`), somando cerca de 46 mil registros que cobrem o ciclo de vida das pesquisas — da pesquisa e das empresas participantes até o questionário e as respostas coletadas. O quadro abaixo resume as dimensões de cada base; as "colunas úteis" desconsideram colunas vazias remanescentes da exportação.[<sup>\[1\]</sup>](#7-referências)[<sup>\[2\]</sup>](#7-referências)

<div align="center">
<sub>Tabela X - Inventário das bases disponibilizadas</sub><br>

| Base | Registros | Colunas úteis | Colunas brutas |
| :--- | ---: | ---: | ---: |
| `pesquisas.csv` | 366 | 22 | 33 |
| `empresas.csv` | 779 | 9 | 9 |
| `clientes.csv` | 5.430 | 5 | 5 |
| `respondentes.csv` | 18.735 | 6 | 6 |
| `questoes.csv` | 231 | 13 | 13 |
| `respostas.csv` | 20.607 | 9 | 9 |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

Em `pesquisas.csv`, 11 das 33 colunas são resíduos vazios da exportação e foram desconsideradas (22 úteis). As tabelas a seguir detalham, por base, os campos e seus tipos — **técnico** (como o dado está armazenado) e **semântico** (o papel do campo na análise).

#### pesquisas.csv

<div align="center">
<sub>Tabela X - Estrutura de pesquisas.csv</sub><br>

| Campo | Tipo técnico | Tipo semântico |
| :--- | :--- | :--- |
| id | inteiro | identificador |
| titulo | texto | texto |
| status | texto | categórico |
| tipo | texto | categórico |
| area | texto | categórico |
| participantes | inteiro | numérico |
| part_mercado | texto | numérico |
| data_solicitacao | data | temporal |
| data_aprov | data | temporal |
| data_divulgacao | data | temporal |
| data_limite | data | temporal |
| prorrogada_ate | data | temporal |
| data_entrega | data | temporal |
| dias_uteis_para_entrega | inteiro | numérico |
| complexidade | texto | categórico |
| tipo de resposta | texto | categórico |
| tempo_preenchimento | inteiro | numérico |
| objetivos | texto | texto |
| dia da semana de lançamento | inteiro | numérico |
| dias úteis aberta | inteiro | numérico |
| dias entre a solicitação e a divulgação | inteiro | numérico |
| dias para tabulação | inteiro | numérico |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

#### empresas.csv

<div align="center">
<sub>Tabela X - Estrutura de empresas.csv</sub><br>

| Campo | Tipo técnico | Tipo semântico |
| :--- | :--- | :--- |
| ID | inteiro | identificador |
| Nome Fantasia | texto | texto |
| % de mercado | texto | numérico |
| Nacionalidade | texto | categórico |
| Associado | texto | categórico |
| Tipo de Associado | texto | categórico |
| Cidade | texto | categórico |
| Estado | texto | categórico |
| País | texto | categórico |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

#### clientes.csv

<div align="center">
<sub>Tabela X - Estrutura de clientes.csv</sub><br>

| Campo | Tipo técnico | Tipo semântico |
| :--- | :--- | :--- |
| id_cliente | texto | identificador |
| id_empresa | inteiro | identificador |
| cargo | texto | categórico |
| departamento | texto | categórico |
| e-mail | texto | texto |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

#### respondentes.csv

<div align="center">
<sub>Tabela X - Estrutura de respondentes.csv</sub><br>

| Campo | Tipo técnico | Tipo semântico |
| :--- | :--- | :--- |
| id_pesq | inteiro | identificador |
| hora_inicio | data/hora | temporal |
| hora_termino | data/hora | temporal |
| id_empresa | inteiro | identificador |
| market_share | texto | numérico |
| id_cliente | inteiro | identificador |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

#### questoes.csv

<div align="center">
<sub>Tabela X - Estrutura de questoes.csv</sub><br>

| Campo | Tipo técnico | Tipo semântico |
| :--- | :--- | :--- |
| id_pergunta | inteiro | identificador |
| pesquisa_id | inteiro | identificador |
| pesquisa_titulo | texto | categórico |
| enunciado | texto | texto |
| tipo | texto | categórico |
| qtd_alternativas | inteiro | numérico |
| alternativas | texto | texto |
| linhas_matriz | texto | categórico |
| colunas_matriz | texto | categórico |
| confianca | texto | categórico |
| formato_arquivo | texto | categórico |
| col_origem | texto | texto |
| observacoes | vazio | — (sem preenchimento) |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

#### respostas.csv

<div align="center">
<sub>Tabela X - Estrutura de respostas.csv</sub><br>

| Campo | Tipo técnico | Tipo semântico |
| :--- | :--- | :--- |
| id_resposta | inteiro | identificador |
| pesquisa_id | inteiro | identificador |
| id_pergunta | inteiro | identificador |
| respondent_id | inteiro | identificador |
| id_empresa | inteiro | identificador |
| alternativa | texto | categórico |
| linha_matriz | texto | categórico |
| coluna_matriz | texto | categórico |
| valor | texto | categórico |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

Dois pontos observados na estrutura, a serem quantificados no diagnóstico de qualidade: as medidas de participação de mercado (`part_mercado`, `% de mercado`, `market_share`) são numéricas mas estão armazenadas como texto; e `id_cliente` aparece como texto em `clientes.csv` e como inteiro em `respondentes.csv`, o que exige conciliação de identidade entre as bases.

### 4.0.2 Fluxo de trabalho atual

O fluxo de trabalho atual da Central de Pesquisas percorre ferramentas consolidadas em cada etapa (planilhas, formulários de coleta, gestão de tarefas e o repositório publicado), mas sem integração estruturada entre elas: o único ponto de conexão apenas replica novas solicitações, sem consolidar o dado ao longo do ciclo de vida da pesquisa. A seguir estão os principais processos organizacionais impactados pela solução, com a situação atual, as limitações existentes e as melhorias esperadas após a implantação.[<sup>\[1\]</sup>](#7-referências)[<sup>\[2\]</sup>](#7-referências)

- **Solicitação e triagem** — registro e aprovação da demanda de uma nova pesquisa.
- **Planejamento e validação do questionário** — estruturação das perguntas e revisão técnica com as áreas responsáveis.
- **Divulgação, coleta e participação** — disponibilização da pesquisa e acompanhamento da adesão de empresas e respondentes.
- **Encerramento, tabulação e análise** — consolidação das respostas e produção de indicadores.
- **Publicação e acervo** — entrega dos resultados e disponibilização no repositório.

<div align="center">
<sub>Tabela X - Processos organizacionais impactados</sub><br>

| Processo | Situação atual | Limitações existentes | Melhorias esperadas |
| :--- | :--- | :--- | :--- |
| Solicitação e triagem | Demanda registrada manualmente e distribuída entre ferramentas isoladas | Sem rastreabilidade da solicitação até o resultado; status disperso | Registro único e rastreável da demanda, com status consolidado |
| Planejamento e validação do questionário | Questionário estruturado e revisado fora de um repositório central | Versões e validações não ficam ligadas à pesquisa de forma auditável | Perguntas e validações vinculadas à pesquisa, com histórico auditável |
| Divulgação, coleta e participação | Adesão de empresas e respondentes acompanhada manualmente | Visão fragmentada da participação; difícil medir adesão em tempo real | Participação consolidada e adesão acompanhada em tempo real |
| Encerramento, tabulação e análise | Respostas consolidadas e cruzadas manualmente em planilhas | Processo lento, sujeito a erro e sem indicadores padronizados | Indicadores calculados automaticamente a partir do banco central |
| Publicação e acervo | Repositório público atualizado manualmente, isolado do sistema interno | Risco de inconsistência entre o interno e o publicado | Acervo alimentado automaticamente e consistente com o banco central |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

### 4.0.3 Gargalos quantificados

_conteúdo_

**Nota:** Listar dores com números sempre que possível (tempos, custos, retrabalho). Citar a fonte de cada número.

### 4.0.4 Contexto e implicações

_conteúdo_

**Nota:** Registrar restrições, tamanho de time, capacidade e demais fatores que impactam prioridade e ROI da solução.

### 4.0.5 Síntese para a proposta TO-BE

_conteúdo_

| Pergunta de partida (AS-IS) | Responde em |
| :--- | :--- |
| _ | _ |

## 4.1 Visão de Informação (Information Viewpoint)

_conteúdo_

**Nota:** Objetos de negócio, entidades principais, relacionamentos e o modelo conceitual/canônico do dado (base para o Data Model Canvas da §5).

## 4.2 Visão de Tecnologia (Technology Viewpoint)

_conteúdo_

**Nota:** Ferramentas e padrões técnicos escolhidos (banco/DW, ferramenta de BI/dashboards, orquestração/ETL, ambiente de nuvem).

## 4.3 Visão de Engenharia (Engineering Viewpoint)

_conteúdo_

**Nota:** Mecanismos de execução — pipeline de ingestão/integração, transformações, deduplicação, padronização e isolamento de ambientes.

## 4.4 Aspectos Não Funcionais

_conteúdo_

**Nota:** Requisitos operacionais da solução (desempenho de consulta, atualização/latência dos dados, disponibilidade, segurança e conformidade). Marcar metas provisórias como aspiracionais até haver medição.

# 5. Modelagem Dimensional e Cubos OLAP

_conteúdo_

**Nota:** Consolidar a modelagem dimensional. Onde as tabelas trouxerem estado, usar a coluna **Estado** para separar o que já está **modelado/validado** do que é **proposto**.

## 5.1 Visão Geral do Modelo Dimensional (Data Model Canvas)

_conteúdo_

**Nota:** Resumir o Data Model Canvas (Negócio, Consumo Analítico, Governança Corporativa) e referenciar o `dmc.json` exportado.

## 5.2 Cubos Analíticos

_conteúdo_

**Nota:** Para cada cubo, definir grão, estrutura (star/snowflake), tipo de fato, fatos/eventos, métricas, dimensões e dimensões especiais.

| Cubo | Grão | Tipo de fato | Métricas principais | Dimensões |
| :--- | :--- | :--- | :--- | :--- |
| _ | _ | _ | _ | _ |

## 5.3 Qualidade e Validação de Dados

Esta seção diagnostica dados ausentes e registros duplicados nas seis bases disponibilizadas, para apoiar as regras de qualidade da solução. A medição foi executada pelo artefato versionado `scripts/data_quality/profile_csv.py`, conforme `scripts/data_quality/manifest.json`, usando UTF-8 (BOM aceito), separador `;`, decimal brasileiro e percentual com sufixo `%`. O manifesto registra `teste.csv` como alias local conceitual de `respostas.csv`; o arquivo bruto não foi copiado para o repositório nem para as saídas. O dicionário é validado de fato: cabeçalho, nove variáveis, conteúdo mínimo e alegações de nulos. **Nenhuma base apresenta registros duplicados** — nem linhas totalmente idênticas, nem identificadores repetidos. As ausências, por outro lado, exigem leitura cuidadosa: parte é **condicional** — estrutural e esperada, seguindo o tipo da pergunta ou o estágio do ciclo de vida da pesquisa (ex.: `linha_matriz` só existe em perguntas de matriz; `prorrogada_ate` só quando há prorrogação) — e parte é **a investigar**, indicando possível lacuna de preenchimento a tratar antes de automatizar indicadores.[<sup>\[2\]</sup>](#7-referências)[<sup>\[4\]</sup>](#7-referências)

O grão de `respostas` é **um elemento atômico de resposta de um respondente para uma pergunta de uma pesquisa**. Uma linha não representa necessariamente um questionário completo: caixas de seleção e matrizes podem produzir várias linhas para o mesmo respondente e pergunta. Portanto, `COUNT(*)` nessa fonte mede elementos de resposta, e não respondentes; qualquer KPI de adesão deve usar a chave e a unidade de análise explicitamente.

<div align="center">
<sub>Tabela X - Resumo de qualidade por base</sub><br>

| Base | Registros | Duplicados | Variáveis com ausência |
| :--- | ---: | ---: | ---: |
| `pesquisas.csv` | 366 | 0 | 16 |
| `empresas.csv` | 779 | 0 | 6 |
| `clientes.csv` | 5.430 | 0 | 4 |
| `respondentes.csv` | 18.735 | 0 | 4 |
| `questoes.csv` | 231 | 0 | 5 |
| `respostas.csv` (alias local `teste.csv`) | 20.607 | 0 | 5 |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

As tabelas a seguir detalham, por base, apenas as variáveis com ausência — quantidade, percentual e natureza (condicional ou a investigar). Percentuais de ausência são calculados sobre as linhas da própria base; um valor ausente não é convertido em zero.

O resumo de chaves separa unicidade de completude: todas as seis chaves são `UNICA`, mas `clientes.id_cliente` tem 1 linha semanticamente incompleta (`s/i`) e `respondentes.(id_pesq,id_empresa,id_cliente)` tem 857 linhas incompletas (856 vazios e 1 `s/i`). A taxa de completude da chave de respondentes é 95,4%; a ausência não é tratada como duplicata nem como correspondência válida.

#### pesquisas.csv

<div align="center">
<sub>Tabela X - Ausências em pesquisas.csv</sub><br>

| Variável | Ausentes | % | Natureza |
| :--- | ---: | ---: | :--- |
| data_aprov | 346 | 94,5% | condicional |
| prorrogada_ate | 298 | 81,4% | condicional |
| complexidade | 276 | 75,4% | a investigar |
| tempo_preenchimento | 135 | 36,9% | a investigar |
| objetivos | 123 | 33,6% | a investigar |
| part_mercado | 44 | 12,0% | a investigar |
| dias para tabulação | 36 | 9,8% | condicional |
| dias_uteis_para_entrega | 35 | 9,6% | condicional |
| dias entre a solicitação e a divulgação | 34 | 9,3% | condicional |
| data_entrega | 32 | 8,7% | condicional |
| participantes | 31 | 8,5% | a investigar |
| data_divulgacao | 8 | 2,2% | condicional |
| data_limite | 8 | 2,2% | condicional |
| data_solicitacao | 4 | 1,1% | a investigar |
| dia da semana de lançamento | 3 | 0,8% | condicional |
| dias úteis aberta | 3 | 0,8% | condicional |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

#### empresas.csv

<div align="center">
<sub>Tabela X - Ausências em empresas.csv</sub><br>

| Variável | Ausentes | % | Natureza |
| :--- | ---: | ---: | :--- |
| Nacionalidade | 69 | 8,9% | a investigar |
| País | 58 | 7,4% | a investigar |
| Tipo de Associado | 49 | 6,3% | condicional |
| Estado | 43 | 5,5% | a investigar |
| Cidade | 42 | 5,4% | a investigar |
| Associado | 1 | 0,1% | a investigar |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

#### clientes.csv

<div align="center">
<sub>Tabela X - Ausências em clientes.csv</sub><br>

| Variável | Ausentes | % | Natureza |
| :--- | ---: | ---: | :--- |
| cargo | 35 | 0,6% | a investigar |
| departamento | 31 | 0,6% | a investigar |
| id_empresa | 1 | 0,0% | a investigar |
| e-mail | 1 | 0,0% | a investigar |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

#### respondentes.csv

<div align="center">
<sub>Tabela X - Ausências em respondentes.csv</sub><br>

| Variável | Ausentes | % | Natureza |
| :--- | ---: | ---: | :--- |
| hora_inicio | 17.928 | 95,7% | condicional |
| hora_termino | 17.928 | 95,7% | condicional |
| id_cliente | 856 | 4,6% | a investigar |
| market_share | 5 | 0,0% | a investigar |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

#### questoes.csv

<div align="center">
<sub>Tabela X - Ausências em questoes.csv</sub><br>

| Variável | Ausentes | % | Natureza |
| :--- | ---: | ---: | :--- |
| observacoes | 231 | 100,0% | condicional |
| linhas_matriz | 228 | 98,7% | condicional |
| colunas_matriz | 228 | 98,7% | condicional |
| alternativas | 29 | 12,6% | condicional |
| qtd_alternativas | 25 | 10,8% | condicional |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

#### respostas.csv

<div align="center">
<sub>Tabela X - Ausências em respostas.csv</sub><br>

| Variável | Ausentes | % | Natureza |
| :--- | ---: | ---: | :--- |
| linha_matriz | 16.603 | 80,6% | condicional |
| coluna_matriz | 16.603 | 80,6% | condicional |
| alternativa | 10.266 | 49,8% | condicional |
| valor | 8.307 | 40,3% | condicional |
| id_empresa | 10 | 0,0% | a investigar |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

As ausências **a investigar** mais relevantes concentram-se em `pesquisas.csv` (`complexidade`, `objetivos`, `tempo_preenchimento`, `participantes` e `part_mercado`) e nas lacunas cadastrais de `empresas.csv` (localização e nacionalidade). Já `id_cliente` ausente em `respondentes.csv` (4,6%) e `id_empresa` ausente em `respostas.csv` e `clientes.csv` reforçam a necessidade de conciliação de identidade entre as bases antes de consolidar os indicadores.

### 5.3.1 Evidências adicionais do perfilamento

O manifesto e os arquivos gerados em diretório temporário tornam o diagnóstico repetível sem armazenar CSV bruto. A execução produziu seis fontes com 366, 779, 5.430, 18.735, 231 e 20.607 registros, respectivamente. `pesquisas.csv` possui 33 colunas, das quais 11 têm cabeçalho vazio e nenhum valor; `questoes.observacoes` é a única coluna nomeada integralmente vazia (231/231). Os demais números de ausência estão nas tabelas acima.

Todos os valores de data não nulos foram parseáveis. Foram comparáveis 20 pares `data_solicitacao`–`data_aprov`, 20 pares `data_aprov`–`data_divulgacao`, 331 pares `data_solicitacao`–`data_entrega` e 68 pares `data_limite`–`prorrogada_ate`; não houve violação na ordem temporal. Em `respondentes`, 807 pares `hora_inicio`–`hora_termino` foram comparáveis e também não houve violação. O timezone não é informado na exportação: a origem e o horário local precisam ser confirmados antes de converter fusos. A coerência temporal cobre somente pares com ambas as datas preenchidas e parseáveis, sem imputação; o resultado não mede completude do processo.

O perfilamento de domínios seguros encontrou inconsistências que precisam de normalização: `empresas.Associado` possui `Sim` (612), `sim` (1), `<SENTINELA:->` (165) e 1 vazio; `empresas.País` possui `Brasil` (669), `BRASIL` (46) e `brasil` (4), além de 58 vazios. Em `questoes`, os tipos são `multipla_escolha` (123), `caixas_de_selecao` (80), `matriz_avaliacao` (3), `numerica` (21) e `aberta` (4), o que sustenta regras de completude condicionais. O domínio de respostas não é exportado pelo perfilador, pois pode conter texto fornecido por participantes; a saída `nulos_condicionais.csv` apresenta apenas contagens por tipo.

As três medidas de participação de mercado continuam armazenadas como texto (`part_mercado`, `% de mercado` e `market_share`); a interpretação deve converter a vírgula decimal e remover `%` somente em uma camada tipada, preservando o texto original para auditoria. O arquivo `percentuais.csv` mediu 322/322, 779/779 e 18.730/18.730 valores não nulos parseáveis, respectivamente; foram 0 inválidos e 0 fora do intervalo proposto `[0,100]` em cada campo. Sem essa conversão, médias e comparações podem ser lexicográficas ou falhar silenciosamente.

As sentinelas são configuradas por campo, não por substituição textual global: `s/i` não participa de chaves de cliente; `NA` em `respostas.valor` é nulo semântico; `-` é sentinela em `empresas.Associado`, mas continua texto livre válido em `respostas.valor`. Assim, `valor` possui 8.307 vazios físicos, 2 `NA` e 8.309 nulos semânticos. Esse é o motivo da divergência documentada pelo dicionário: a alegação de 8.309 nulos não coincide com a contagem física de vazios, mas coincide após a regra semântica.

### 5.3.2 Chaves, órfãos e identidades entre sistemas

As verificações de relacionamento usam apenas chaves não nulas e reportam o denominador comparável. Os resultados medidos foram:

| Relação | Comparáveis | Encontradas | Órfãs | % órfãs | Interpretação |
| :--- | ---: | ---: | ---: | ---: | :--- |
| `clientes.id_empresa → empresas.ID` | 5.429 | 5.429 | 0 | 0,0% | 1 cliente sem `id_empresa` não entra no teste de chave |
| `respondentes.id_empresa → empresas.ID` | 18.735 | 18.735 | 0 | 0,0% | Relação empresa–participação presente |
| `respondentes.id_pesq → pesquisas.id` | 18.735 | 18.680 | 55 | 0,3% | 55 linhas apontam para o ID 304 ausente; afeta adesão e série temporal |
| `respostas.id_empresa → empresas.ID` | 20.597 | 20.597 | 0 | 0,0% | 10 respostas sem empresa exigem decisão de tratamento |
| `respondentes.id_cliente → clientes.id_cliente` | 17.878 | 17.878 | 0 | 0,0% | 856 vazios e 1 `s/i` não são comparáveis; igualdade normalizada não prova identidade histórica |
| `respostas.(pesquisa_id,id_pergunta) → questoes` | 20.607 | 20.607 | 0 | 0,0% | Grão atômico de resposta preservado |
| `questoes.pesquisa_id → pesquisas.id` | 231 | 188 | 43 | 18,6% | IDs históricos precisam de identidade canônica |
| `respostas.pesquisa_id → pesquisas.id` | 20.607 | 17.015 | 3.592 | 17,4% | Não atribuir silenciosamente a pesquisa atual |

Os domínios de identificador reforçam a hipótese de múltiplos sistemas: há 366 `pesquisas.id` distintos, 327 `respondentes.id_pesq` e 10 `pesquisa_id` distintos em cada uma de `questoes` e `respostas`. A relação `respondentes.id_pesq → pesquisas.id` tem 55 linhas órfãs concentradas no ID 304; isso pode retirar participações de uma pesquisa dos KPIs de adesão e de suas séries temporais se for descartado sem mapeamento. As interseções entre `pesquisas.id` e `questoes.pesquisa_id` e entre `pesquisas.id` e `respostas.pesquisa_id` são de 6; entre `questoes` e `respostas`, 10. Isso é evidência de reconciliação necessária, não autorização para descartar os IDs órfãos.

`id_cliente` aparece como texto no cadastro e como identificador numérico/textual na participação. O perfilamento encontrou 5.429 valores distintos em cada lado e interseção de 5.429 após normalização, mas a diferença de tipo e o registro `s/i` do cadastro exigem regra explícita. `respostas.respondent_id` possui 542 valores distintos e não tem uma chave homônima em `respondentes.csv`; por isso o perfilador não o classifica como órfão, apenas como identidade ainda não ligada.

A verificação da cópia denormalizada `questoes.pesquisa_titulo` contra `pesquisas.titulo` encontrou 188 pares comparáveis, 147 coincidentes e 41 divergências (21,8%), todas concentradas nos IDs 414 (13 linhas) e 415 (28 linhas). O título canônico deve vir de `pesquisas`; a divergência não deve criar uma segunda identidade nem ser corrigida sobrescrevendo a origem sem auditoria.

`nulos_condicionais.csv` classifica cada campo de resposta por `questoes.tipo`, separando linhas aplicáveis, não aplicáveis, preenchidas, ausências condicionais e ausências inesperadas. Para `linha_matriz` e `coluna_matriz`, foram 4 ausências inesperadas em 4.008 linhas de `matriz_avaliacao` (0,1%); `alternativa` é obrigatória em `caixas_de_selecao` e não teve ausência inesperada. As regras são explícitas no manifesto e devem ser revisadas pelo Data Steward antes de virarem bloqueio de ingestão.

### 5.3.3 Indicadores, fórmulas, unidades e grãos

As métricas abaixo são as definições usadas nos artefatos de perfilamento. Quando o resultado é medido, a fonte é o CSV local indicado; quando a regra ainda depende do processo futuro, ela está marcada como proposta.

| Indicador | Fórmula | Unidade | Grão | Fonte | Resultado/interpretação |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Completude de campo | `(linhas − nulos) / linhas × 100` | % | campo por base | `campos.csv` | Mede preenchimento; não transforma vazio condicional em erro |
| Taxa de duplicação de linhas | `linhas_duplicadas_extras / linhas × 100` | % | linha da base | `resumo.csv` | 0,0% nas seis bases medidas |
| Taxa de órfãos | `órfãos / comparáveis × 100` | % | chave de relação | `relacionamentos.csv` | 18,6% em questões→pesquisas e 17,4% em respostas→pesquisas |
| Elementos de resposta | `COUNT(respostas.id_resposta)` | registros | elemento atômico de resposta | `respostas.csv`/alias `teste.csv` | 20.607; não equivale a respondentes |
| Respondentes distintos | `COUNT(DISTINCT respondent_id)` | respondentes | pesquisa e respondente | `respostas.csv`/alias `teste.csv` | 542 distintos; vínculo com `respondentes` ainda não está comprovado |
| Violação temporal | `pares fora de ordem / pares comparáveis × 100` | % | par temporal por pesquisa/participação | `coerencia_temporal.csv` | 0,0% nos pares preenchidos medidos; completude continua separada |
| Consistência de domínio | `contagem por valor normalizado / linhas × 100` | % | campo categórico | `dominios.csv` | Identifica `Sim/sim`, `Brasil/BRASIL/brasil` e vazios |
| Percentual parseável | `valores parseáveis / valores não nulos × 100` | % | campo percentual | `percentuais.csv` | 100,0% nos três campos; inválidos e fora de `[0,100]` = 0 |
| Ausência condicional inesperada | `ausências obrigatórias / linhas aplicáveis × 100` | % | tipo de questão e campo de resposta | `nulos_condicionais.csv` | 0,1% em cada dimensão de matriz; regra proposta por tipo |
| Divergência denormalizada | `títulos divergentes / pares comparáveis × 100` | % | questão–pesquisa | `denormalizados.csv` | 41/188 (21,8%), IDs 414 e 415 |
| Divergência do dicionário | `alegação − contagem física/semântica` | registros | campo `respostas.valor` | `dicionario_validacao.csv` | 8.309 alegados − 8.307 vazios = 2 sentinelas; semântica fecha em 0 |

Os indicadores de negócio devem registrar ainda a dimensão usada (pesquisa, empresa, pergunta, respondente e período), a fórmula, a unidade e a origem. Por exemplo, adesão por pesquisa deve usar empresas/participações deduplicadas no grão definido, e não o número de linhas de `respostas`; tempo de entrega deve usar somente pares de datas válidos e declarar o denominador.

### 5.3.4 Impacto nos KPIs e controles de qualidade

| Desafio observado | Impacto no KPI/dashboard | Controle preventivo | Controle detectivo | Controle corretivo |
| :--- | :--- | :--- | :--- | :--- |
| Exportação com 11 colunas sem nome e `questoes.observacoes` 100% vazia | Metadados podem ser confundidos com atributos analíticos | Contrato de schema no manifesto e catálogo de campos | Falha explícita de cabeçalho/contagem e alerta de coluna vazia | Remover apenas após aprovação e preservar o mapeamento da origem |
| Percentuais armazenados como texto com vírgula e `%` | Média, soma e filtros podem ser lexicográficos ou inválidos | Tipo semântico e conversor único com regra brasileira | Contagem de parseáveis, valores fora do domínio e amostra independente | Corrigir na camada tipada, mantendo o valor original e a evidência |
| Ausências condicionais em perguntas/matrizes | Denominador errado e falso alerta de incompletude | Regra por `questoes.tipo` e dicionário | Completude condicional por tipo e relatório de nulos | Solicitar correção na fonte ou registrar “não aplicável”; não preencher com zero |
| Sentinelas misturadas a vazios (`s/i`, `NA`, `-`) | Chaves e completude podem contar “sem informação” como categoria válida | Sentinelas configuradas por campo e preservação do valor original | `campos.csv`, `dominios.csv` e `dicionario_validacao.csv` separam físico, sentinela e semântico | Confirmar significado com o Data Steward; corrigir camada tipada sem tratar `-` de texto livre como nulo |
| `complexidade`, `objetivos`, `participantes` e prazos incompletos | Comparação de prazo, volume e cobertura pode ter viés | Campos críticos definidos pelo Data Steward | `campos.csv`, `datas.csv` e revisão de amostra | Backfill na fonte, quarentena do registro ou exclusão documentada do denominador |
| `questoes.pesquisa_id` e `respostas.pesquisa_id` órfãos | Pesquisa, período e área podem ser atribuídos incorretamente | Tabela de identidade canônica e chave de origem por sistema | `relacionamentos.csv` e reconciliação de interseções | Mapear ID legado, reprocessar e manter órfão pendente até decisão |
| `respondentes.id_pesq` órfão (55 linhas, ID 304) | Participações podem desaparecer de adesão e série temporal | Relação obrigatória no contrato de ingestão | `relacionamentos.csv` com linhas e chaves órfãs distintas | Mapear ID 304 ou manter pendente; não descartar participação |
| `questoes.pesquisa_titulo` divergente (41 linhas) | Filtros e agrupamentos podem usar título inconsistente | Título canônico em `pesquisas` e chave de origem preservada | `denormalizados.csv` e reconciliação dos IDs 414/415 | Corrigir fonte/mapeamento após auditoria; não sobrescrever silenciosamente |
| Ausência de chave explícita entre `respondent_id` e `respondentes` | Adesão de pessoas e respostas pode ser duplicada ou não ligada | Definir contrato de identidade antes do KPI | Checagem de cardinalidade e relatório de identidade sem descarte | Criar mapeamento aprovado; não inferir pessoa apenas por coincidência |
| Datas ausentes ou fora de ordem | Tempos médios e SLA podem ser artificialmente baixos | Regras de ordem e fuso documentadas na entrada | `coerencia_temporal.csv` e checagem de pares comparáveis | Corrigir origem ou marcar a métrica como não calculável |

Como proposta inicial, a equipe pode submeter à aprovação do Data Steward os limiares de 0% para duplicação, falha de schema, falha de parsing e órfãos em chaves obrigatórias, e 0% de violações temporais nos pares comparáveis. Campos condicionais não recebem um limiar universal; cada tipo de pergunta deve ter regra e denominador próprios. Esses limiares são propostas de controle, não resultados obtidos nem garantia de publicação segura.

### 5.3.5 Fluxo detectar → auditar → corrigir

0. **Detectar:** executar o manifesto em diretório somente leitura e guardar `resumo.csv`, `campos.csv`, `datas.csv`, `dominios.csv`, `relacionamentos.csv`, `coerencia_temporal.csv`, `identidades.csv`, `nulos_condicionais.csv`, `percentuais.csv`, `denormalizados.csv`, `dicionario_validacao.csv` e o manifesto aplicado. Falha de arquivo, UTF-8, separador, cabeçalho ou quantidade de campos interrompe o processo com código explícito.
0. **Classificar:** separar ausência estrutural/condicional, ausência a investigar, falha de domínio, órfão, duplicata, falha temporal, percentual inválido, sentinela e divergência de identidade. O denominador comparável deve acompanhar cada alerta.
0. **Auditar:** o Data Steward revisa a regra e uma amostra independente de primeira, mediana e última linha de cada base, confrontando contagem, chaves, nulos e datas com a exportação recebida. Para respostas, a revisão confirma que múltiplas linhas por respondente/pergunta são compatíveis com o tipo da questão.
0. **Corrigir:** solicitar backfill na fonte, normalizar em camada tipada, criar mapeamento canônico ou colocar o registro em quarentena. Não apagar silenciosamente respostas ou IDs órfãos.
0. **Reprocessar e aprovar:** executar novamente, comparar hashes dos agregados e registrar decisão, responsável, data, versão do manifesto e evidências. Só então liberar o conjunto aprovado para o próximo estágio do pipeline, sem inferir que o perfilamento autoriza publicar os dados.

O arquivo `scripts/data_quality/README.md` documenta o comando, a validação do dicionário e as salvaguardas. Os testes unitários cobrem BOM, separador, percentual brasileiro, falha de schema, dicionário arbitrário e ausência de valores brutos nas saídas; a validação operacional deste diagnóstico também incluiu `py_compile`, duas execuções independentes e `git diff --check`.

## 5.4 Rastreabilidade Analítica

_conteúdo_

**Nota:** Cadeia pergunta de negócio → requisito → indicador → cubo → dashboard. Garantir que todo requisito chegue a um dashboard e todo dashboard atenda a pelo menos um requisito.

| Pergunta de negócio | Requisito | Indicador | Cubo | Dashboard |
| :--- | :--- | :--- | :--- | :--- |
| _ | _ | _ | _ | _ |

## 5.5 Infraestrutura de Dados

_conteúdo_

**Nota:** Onde os dados vivem e como são processados (DW na nuvem, orquestração, armazenamento de artefatos, retenção).

## 5.6 Mapa de Cobertura de Indicadores

_conteúdo_

**Nota:** Matriz de rastreabilidade dos indicadores. A coluna **Estado** separa o que já é **calculado/validado** do que é **proposto**.

| Indicador | Estado | Cubo / fonte | Fórmula / granularidade | Evidência |
| :--- | :--- | :--- | :--- | :--- |
| _ | _ | _ | _ | _ |

## 5.7 Mapa de Cobertura de Dashboards

_conteúdo_

**Nota:** Para cada dashboard, registrar objetivo, perguntas respondidas, indicadores, filtros/segmentações e estado.

| Dashboard | Estado | Objetivo | Indicadores apresentados | Evidência |
| :--- | :--- | :--- | :--- | :--- |
| _ | _ | _ | _ | _ |

# 6. Requisitos e Governança de Dados

_conteúdo_

## 6.1 Requisitos Funcionais

_conteúdo_

**Nota:** Lista de requisitos funcionais com identificadores (`RF01`, `RF02`, ...), cada um em formato de User Story, com critério de aceitação e teste de usuário.

| ID | User Story | Critério de aceitação | Teste de usuário |
| :--- | :--- | :--- | :--- |
| RF01 | _ | _ | _ |

## 6.2 Requisitos Não Funcionais (ISO/IEC 25010)

Os requisitos não funcionais abaixo seguem as características da ISO/IEC 25010 e priorizam desempenho, segurança, confiabilidade, usabilidade e manutenibilidade, derivados das necessidades do parceiro. As metas numéricas são **provisórias e aspiracionais**, a serem confirmadas por medição (ver §4.4 — Aspectos Não Funcionais).[<sup>\[1\]</sup>](#7-referências)

<div align="center">
<sub>Tabela X - Requisitos não funcionais (ISO/IEC 25010)</sub><br>

| ID | Categoria (ISO 25010) | User Story | Critério de aceitação | Teste |
| :--- | :--- | :--- | :--- | :--- |
| RNF01 | Eficiência de desempenho | Como analista da Central de Pesquisas, quero que as consultas dos dashboards respondam rapidamente para acompanhar os indicadores sem espera. | Consultas dos painéis retornam em menos de 5 s no volume atual (~46 mil registros). | Abrir o dashboard de volume de pesquisas e cronometrar a resposta ao aplicar filtros de período e área. |
| RNF02 | Segurança | Como gestor da Central, quero que cada usuário acesse apenas os dados permitidos ao seu perfil, para proteger dados sensíveis e cumprir a LGPD. | Acesso controlado por perfil (equipe interna, áreas técnicas e solicitantes externos); tentativa de acesso não autorizado é bloqueada e registrada. | Autenticar com um perfil externo e confirmar que dados internos ou identificáveis não são exibidos nem baixáveis. |
| RNF03 | Confiabilidade | Como equipe da Central, quero que a plataforma esteja disponível no horário de trabalho para operar o fluxo sem interrupção. | Disponibilidade ≥ 99,9% no horário comercial. | Monitorar o uptime por um período e verificar se as indisponibilidades ficam dentro do limite. |
| RNF04 | Usabilidade | Como usuário das áreas técnicas, quero navegar pelos dashboards de forma intuitiva para encontrar indicadores sem treinamento extenso. | Um usuário novo localiza um indicador-chave (ex.: taxa de adesão) em até 3 cliques e 2 minutos, sem consultar manual. | Pedir a um usuário sem treino que encontre a taxa de adesão de uma pesquisa e medir cliques e tempo. |
| RNF05 | Manutenibilidade | Como responsável técnico, quero que incluir uma nova fonte no pipeline seja simples, para manter a solução evoluindo com baixo esforço. | Adicionar uma nova fonte não exige reescrever o modelo central; a configuração é documentada e as alterações são versionadas. | Simular a adição de uma fonte de teste e verificar que o pipeline a ingere pela configuração documentada, sem alterar o schema central. |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

## 6.3 Perguntas de Negócio

_conteúdo_

**Nota:** Perguntas rastreáveis que o DW precisa responder, cada uma associada a pelo menos um requisito funcional.

| ID | Pergunta de negócio | Requisito(s) associado(s) |
| :--- | :--- | :--- |
| _ | _ | _ |

## 6.4 Indicadores e Métricas de Negócio

_conteúdo_

**Nota:** Para cada indicador: nome, objetivo, significado para o negócio, fórmula, variáveis, granularidade e dimensões de segmentação.

| Indicador | Objetivo | Fórmula | Granularidade | Dimensões |
| :--- | :--- | :--- | :--- | :--- |
| _ | _ | _ | _ | _ |

## 6.5 Dashboards Analíticos

_conteúdo_

**Nota:** Nome, objetivo, perguntas respondidas, indicadores apresentados, visualizações, filtros e segmentações. Incluir protótipos/wireframes.

<!-- Inserir wireframe/protótipo do dashboard -->

## 6.6 Governança, Segurança da Informação e LGPD

_conteúdo_

**Nota:** Papéis e responsáveis (Data Owner, Data Steward, Data Custodian), políticas de acesso por perfil, auditoria, classificação de dados, tratamento de dados pessoais/sensíveis, anonimização, retenção e direitos dos titulares.

| Papel | Responsável | Responsabilidade |
| :--- | :--- | :--- |
| Data Owner | _ | _ |
| Data Steward | _ | _ |
| Data Custodian | _ | _ |

# 7. Referências

[1] INTELI; SINDUSFARMA. **Termo de Abertura de Projeto Inteli (TAPI) — ESMD11: arquitetura e governança de dados alinhada à estratégia corporativa**. São Paulo, 2026. Documento de projeto (arquivo `TAPI.pdf`) disponibilizado pela faculdade e pelo parceiro de projeto.

[2] INTELI; SINDUSFARMA. **Arquitetura de Negócio: Central de Pesquisas do Sindusfarma**. São Paulo, 2026. Documento de projeto (arquivo `Arquitetura de Negócio.pdf`) disponibilizado pela faculdade e pelo parceiro de projeto.

[3] INTELI; SINDUSFARMA. **Data Model Canvas: Data Warehouse — Sindusfarma**. São Paulo, 2026. Artefato de documentação (arquivo `Data Model Canvas.pdf`) disponibilizado pela faculdade e pelo parceiro de projeto.

[4] GRUPO G05. **Dicionário de Variáveis — Respostas**. São Paulo, 2026. Arquivo local `Dicionario_Variaveis_Respostas_Grupo6.xlsx - Dicionário.csv`, disponibilizado junto às bases do parceiro.

# 8. Avaliação dos Resultados

_conteúdo_

**Nota:** Confrontar o cenário AS-IS (§4.0) com os resultados da solução proposta (TO-BE). Separar explicitamente o que foi **medido** do que é **meta projetada**.

## 8.1 Resultados Quantitativos

_conteúdo_

### 8.1.1 Resultado medido nesta sprint

_conteúdo_

**Nota:** Somente fatos medidos, com a origem de cada número (query, artefato, coleta). Nada de estimativa aqui.

| Indicador | Resultado medido | Como foi medido |
| :--- | :--- | :--- |
| _ | _ | _ |

### 8.1.2 Meta / projetado para sprints futuras

_conteúdo_

**Nota:** Indicadores ainda não medidos, com a meta e a razão de não ter sido medido nesta sprint. Nenhum valor aqui deve ser lido como resultado obtido.

| Indicador (projetado) | Meta | Por que não foi medido nesta sprint |
| :--- | :--- | :--- |
| _ | _ | _ |

## 8.2 Diagnóstico Qualitativo

_conteúdo_

**Nota:** Análise textual aderente às tabelas da §8.1 — descrever como "medido" só o que roda de fato e marcar como "projetado" o que ainda é meta.

## 8.3 Tabela de Fontes e Auditabilidade

_conteúdo_

**Nota:** Cada afirmação quantitativa da §8.1 deve ter fonte auditável (commit, MR, artefato, coleta ou documento do parceiro).

| Documento/Evento | Referência (auditável) | Data |
| :--- | :--- | :--- |
| _ | _ | _ |
