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
| `teste.csv` (nome canônico: `respostas.csv`) | 20.607 | 9 | 9 |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

O arquivo recebido como `teste.csv` é tratado neste documento pelo nome
canônico de negócio `respostas.csv`, adotado nas tabelas de estrutura, no
dicionário e nos requisitos. Essa equivalência é de nomenclatura; a integração
entre a fonte recebida e as demais bases ainda precisa ser verificada.

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

A matriz completa de cubos, grãos, métricas, dimensões e estados é dependência
da issue **#23**. A tabela abaixo permanece como estrutura de trabalho e não
afirma que cubos ou métricas estejam implementados ou validados.

| Cubo | Grão | Tipo de fato | Métricas principais | Dimensões |
| :--- | :--- | :--- | :--- | :--- |
| _ | _ | _ | _ | _ |

## 5.3 Qualidade e Validação de Dados

Esta seção diagnostica dados ausentes e registros duplicados nas seis bases disponibilizadas, para apoiar as regras de qualidade da solução. **Não foram encontrados registros duplicados por linha ou por identificador primário**. Identificadores usados como chaves estrangeiras, como `pesquisa_id`, `id_pesq`, `id_pergunta` e `id_empresa`, podem repetir-se legitimamente para representar relações; portanto, a coluna **Duplicados** não trata FKs repetidas como duplicatas. As ausências, por outro lado, exigem leitura cuidadosa: parte é **condicional** — estrutural e esperada, seguindo o tipo da pergunta ou o estágio do ciclo de vida da pesquisa (ex.: `linha_matriz` só existe em perguntas de matriz; `prorrogada_ate` só quando há prorrogação) — e parte é **a investigar**, indicando possível lacuna de preenchimento a tratar antes de automatizar indicadores.[<sup>\[2\]</sup>](#7-referências)

<div align="center">
<sub>Tabela X - Resumo de qualidade por base</sub><br>

| Base | Registros | Duplicados | Variáveis com ausência |
| :--- | ---: | ---: | ---: |
| `pesquisas.csv` | 366 | 0 | 16 |
| `empresas.csv` | 779 | 0 | 6 |
| `clientes.csv` | 5.430 | 0 | 4 |
| `respondentes.csv` | 18.735 | 0 | 4 |
| `questoes.csv` | 231 | 0 | 5 |
| `teste.csv` (nome canônico: `respostas.csv`) | 20.607 | 0 | 5 |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

As tabelas a seguir detalham, por base, apenas as variáveis com ausência — quantidade, percentual e natureza (condicional ou a investigar).

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

## 5.4 Rastreabilidade Analítica

_conteúdo_

**Nota:** Cadeia pergunta de negócio → requisito → indicador → cubo → dashboard. Garantir que todo requisito chegue a um dashboard e todo dashboard atenda a pelo menos um requisito.

A matriz completa de rastreabilidade é dependência da issue **#23**. Nesta
etapa, a tabela registra apenas o vínculo a detalhar; não representa
implementação, cálculo validado ou dashboard existente.

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

Os requisitos funcionais abaixo traduzem necessidades da Central em comportamentos
observáveis de consulta, acompanhamento, análise, controle e publicação. Os
identificadores são estáveis e a cobertura considera os objetivos (§3), os
processos atuais (§4.0.2), o dicionário de dados (§4.0.1), o diagnóstico de
qualidade (§5.3), o TAPI e a Arquitetura de Negócio ([1] e [2]), o Data Model
Canvas ([3]) e os artefatos locais de JTBD/HMW e Problem Canvas ([4] e [5]).
A menção a uma fonte sem campo correspondente no dicionário registra uma
necessidade a confirmar, não um dado já disponível.

Esta tabela delimita escopo e comportamento funcional; não prescreve tecnologia,
SLA, periodicidade ou atualização em tempo real. Os critérios de aceitação e os
testes de usuário que tornam cada requisito verificável estão descritos nas
subseções 6.1.1 e 6.1.2. Eles devem ser avaliados com os dados e as permissões
disponíveis no momento da validação, sem transformar informação ausente em zero
ou em erro e sem inferir vínculos que as fontes não sustentam.

As personas usadas nas User Stories correspondem aos públicos do projeto:
analista ou operador da Central (acompanha e analisa o ciclo), gestor da Central
(prioriza e autoriza), responsável de área técnica (valida e versiona o
questionário), auditor de dados (confere qualidade e linhagem) e solicitante ou
participante autorizado (consulta resultados permitidos). “Leitor autorizado”
é a forma curta para o solicitante ou participante com permissão de consulta;
“auditor de dados” é um papel funcional de governança, não uma afirmação de
cargo adicional na organização. Esses papéis são derivados dos usuários
primário, secundário e terciário do TAPI [1] e dos públicos do Problem Canvas
[5].

Na governança, o Data Owner é o responsável de negócio por aprovar prioridades,
acessos e publicação; o Data Steward cuida de definições, qualidade e linhagem;
e o Data Custodian/TI responde pela custódia, atualização e sustentação das
fontes. A atribuição nominal desses papéis ainda é um ponto a validar com o
parceiro e não cria requisitos adicionais.

| ID | Nome curto | User Story | Funcionalidade analítica | Pergunta(s) de negócio | Fonte/motivação |
| :--- | :--- | :--- | :--- | :--- | :--- |
| RF01 | Portfólio de pesquisas | Como gestor ou analista da Central, quero consultar o portfólio de pesquisas por período, tipo, área, complexidade e status, para decidir quais demandas acompanhar. | Listar e segmentar as pesquisas e apresentar a distribuição do portfólio pelos atributos disponíveis, preservando o identificador e o título de cada pesquisa. | Quais pesquisas compõem o portfólio e como elas se distribuem por período, tipo, área, complexidade e status? | Objetivos (§3); processos de solicitação e triagem (§4.0.2); campos de `pesquisas.csv` (§4.0.1); TAPI [1], JTBD/HMW [4] e Problem Canvas [5]. |
| RF02 | Ciclo e detalhe da pesquisa | Como analista da Central, quero acompanhar a etapa e abrir o detalhe de uma pesquisa, para entender sua situação e o que precisa ser acompanhado. | Exibir status, datas e detalhes do ciclo — solicitação, aprovação, divulgação, coleta, entrega, tabulação e publicação — classificando cada marco como observado (registrado na fonte), derivado (inferido de dados disponíveis) ou futuro/proposto (ainda não representado); ausência de registro não deve ser apresentada como conclusão do marco. | Em que etapa está cada pesquisa, quais marcos foram observados ou derivados e quais informações do seu detalhe estão disponíveis? | Fluxo de trabalho e processos (§4.0.2); datas, status, objetivos e participantes de `pesquisas.csv`, além de `questoes.csv` (§4.0.1); Arquitetura de Negócio [2]. |
| RF03 | Prazos e prioridades | Como gestor ou analista da Central, quero analisar prazos, tempos, atrasos, prorrogações e as prioridades informadas, para ordenar o acompanhamento das pesquisas. | Comparar datas de solicitação, divulgação, limite, prorrogação e entrega e consultar medidas de tempo disponíveis, como dias em aberto e para tabulação; informar marcos ausentes e não classificar atraso, duração ou prorrogação quando faltar data de referência, denominador ou outro dado necessário. A prioridade é uma regra proposta e só deve ser usada quando houver prioridade declarada. | Quais pesquisas estão atrasadas, foram prorrogadas ou demandam prioridade, qual denominador sustenta cada comparação e como os tempos do ciclo se comparam entre elas? | Objetivos (§3); `data_limite`, `prorrogada_ate`, `data_entrega`, `dias úteis aberta`, `dias para tabulação`, `complexidade` e demais campos temporais (§4.0.1); Arquitetura de Negócio [2], JTBD/HMW [4] e Problem Canvas [5]. O dicionário atual não lista campo próprio de prioridade; a regra é proposta. |
| RF04 | Adesão e representatividade | Como analista da Central, quero comparar adesão e participação de empresas com a participação de mercado disponível, para avaliar a representatividade da pesquisa. | Calcular e segmentar adesão por pesquisa e empresa somente quando houver universo convidado, esperado ou outro denominador documentado; exibir numerador e denominador, declarando denominador indisponível quando não existir. Relacionar respondentes, empresas e medidas de mercado somente após conciliação de identidade e distinguir ausência de dado de baixa participação. | A participação alcançada é suficiente e representa as empresas ou parcelas de mercado relevantes, e qual denominador sustenta essa leitura? | Objetivo de ampliar adesão (§3); processo de divulgação, coleta e participação (§4.0.2); `participantes`, `part_mercado`, `market_share`, `empresas.csv` e `respondentes.csv` (§4.0.1); TAPI [1], JTBD/HMW [4] e Problem Canvas [5]. |
| RF05 | Engajamento dos públicos | Como gestor ou analista da Central, quero analisar o engajamento por área, departamento e cargo, para identificar públicos mais ou menos participantes. | Agrupar pesquisas, participações e respostas por área da pesquisa, departamento e cargo do cliente, após conciliação dos identificadores; apresentar contagens e calcular taxas apenas quando houver denominador documentado, declarando-o indisponível quando não houver. | Quais áreas, departamentos e cargos participam mais ou menos, qual é o denominador disponível e onde há oportunidade de ampliar o engajamento? | Objetivo de ampliar adesão (§3); `area` de `pesquisas.csv`, `departamento` e `cargo` de `clientes.csv`, e vínculos de `respondentes.csv` (§4.0.1); JTBD/HMW [4] e Problem Canvas [5]. |
| RF06 | Qualidade e atualização | Como Data Steward ou analista da Central, quero verificar a completude, a validade e a atualização das fontes, para interpretar os indicadores com confiança. | Consultar, por fonte e campo, registros de ausência, inconsistências de identidade, tipos armazenados e data ou estado de atualização disponível, distinguindo ausência condicional de lacuna a investigar e indicando quando a fonte não oferece a informação; o Data Steward acompanha as definições e a qualidade, e o Custodian/TI informa a custódia ou atualização disponível. | Quais dados estão completos e válidos para análise, quais lacunas permanecem e qual é o estado de atualização de cada fonte? | Diagnóstico de qualidade (§5.3), dicionário (§4.0.1), rastreabilidade (§5.4), objetivo de governança e qualidade (§3), DMC [3], JTBD/HMW [4] e Problem Canvas [5]. |
| RF07 | Linhagem agregada ponta a ponta | Como Data Steward ou auditor de dados, quero rastrear a origem de um resultado agregado, para verificar como o dado foi produzido sem presumir uma consulta individual. | Exibir, para cada elo da linhagem agregada fonte → pesquisa → participação → questão → resposta, o sistema ou arquivo de origem, a chave disponível e o estado **observado** (registro/chave encontrado), **em reconciliação** (incompatibilidade ou ausência de correspondência) ou **proposto** (metadado ou vínculo ainda não representado). Quando o sistema de origem não estiver identificado, declarar essa ausência e usar apenas o arquivo recebido. A análise verificou `pesquisa_id` 424, 1116, 1139 e 1147 em `questoes.csv`/`respostas.csv` sem correspondência em `pesquisas.csv`, além de 55 participações em `respondentes.csv` com `id_pesq=304` ausente em `pesquisas.csv`; esses casos permanecem em reconciliação. Não prometer vínculo individual: não há ponte explícita entre `respostas.respondent_id` e `respondentes.id_cliente` nos arquivos recebidos. | Qual fonte e sistema sustentam cada elo do agregado, qual é o estado de cada relação e quais anomalias ou vínculos ainda precisam de conciliação? | Objetivo de rastreabilidade (§3); processos de planejamento, coleta, tabulação e publicação (§4.0.2); chaves de `pesquisas.csv`, `respondentes.csv`, `questoes.csv` e `respostas.csv` (§4.0.1); Arquitetura de Negócio [2], DMC [3], Problem Canvas [5] e dicionário [6]. |
| RF08 | Acesso por perfil | Como Data Owner ou gestor da Central, quero que cada perfil veja apenas os dados permitidos, para proteger informações de empresas e respondentes. | Aplicar a visibilidade definida para perfis internos, áreas técnicas e solicitantes externos, diferenciando dados operacionais, respostas identificáveis e resultados agregados; o Data Owner aprova a regra de acesso e a decisão é registrada quando aplicável. | Que dados cada perfil pode consultar, detalhar ou publicar sem expor informações não autorizadas? | Objetivo de governança, segurança e LGPD (§3); processo de publicação e acervo (§4.0.2); requisito não funcional de segurança (RNF02); TAPI [1], Arquitetura de Negócio [2] e Problem Canvas [5]. |
| RF09 | Publicação autorizada | Como Data Owner ou gestor da Central, quero publicar somente resultados autorizados e acompanhar seu estado de publicação, para manter o acervo público coerente com o processo interno. | Tratar autorização, estado e data de publicação como metadados propostos, dependentes da integração futura com o acervo; o Data Owner aprova a publicação e o Custodian/TI sustenta a disponibilização conforme essa decisão. Disponibilizar no acervo apenas conteúdo explicitamente autorizado e manter o vínculo com a pesquisa de origem. `data_divulgacao` é uma data da pesquisa e não prova autorização ou publicação. | O resultado foi autorizado e publicado, quais metadados sustentam essa decisão e ele está consistente com a pesquisa interna correspondente? | Processo de publicação e acervo (§4.0.2); `data_divulgacao` e status de `pesquisas.csv` (§4.0.1), que não comprovam publicação; objetivo de rastreabilidade (§3); Arquitetura de Negócio [2], DMC [3] e Problem Canvas [5]. |
| RF10 | Resultados agregados | Como analista da Central ou leitor autorizado, quero consultar resultados agregados por pesquisa e questão, para interpretar as respostas sem expor registros individuais. | Apresentar contagens ou distribuições por alternativa, valor e, quando aplicável, linha e coluna de matriz, com recortes por pesquisa e questão; informar o número de respostas válidas e declarar denominador populacional indisponível quando não houver universo de referência, sem inferir uma taxa. | Qual foi a distribuição das respostas para cada questão, qual denominador está disponível e como ela varia entre pesquisas ou segmentos permitidos? | Processo de encerramento, tabulação e análise (§4.0.2); `questoes.csv` e `respostas.csv` (§4.0.1); cubos propostos no DMC [3]; objetivo de apoiar decisões (§3); JTBD/HMW [4] e Problem Canvas [5]. |
| RF11 | Contexto de resposta autorizado | Como auditor de dados ou analista da Central autorizado, quero consultar o contexto disponível de uma resposta agregada, para conferir a interpretação sem expor dados individuais. | Relacionar o agregado à questão, pesquisa e participação somente pelos elos disponíveis; declarar denominador de respostas ou da população indisponível quando não houver base para calculá-lo. Qualquer consulta individual fica limitada a ambiente e perfil autorizados e depende de uma ponte de identidade existente. Nos arquivos recebidos, não há ponte explícita entre `respostas.respondent_id` e `respondentes.id_cliente`; ausência dessa ponte deve ser exibida, não compensada por inferência. | Qual evidência agregada sustenta este resultado, que contexto está disponível e a consulta individual é autorizada e suportada pelos dados? | Rastreabilidade analítica (§5.4); chaves e atributos de `respostas.csv`, `questoes.csv` e `respondentes.csv` (§4.0.1); requisitos de acesso e publicação (RF08 e RF09); DMC [3], Problem Canvas [5] e dicionário [6]. |
| RF12 | Integração e atualização das fontes | Como Data Custodian/TI ou analista da Central, quero acompanhar a integração e a atualização das fontes, para usar dados padronizados, não duplicados e com origem preservada. | Consolidar registros recebidos com padronização de nomes, tipos e domínios; detectar duplicidades e tratar reprocessamentos com idempotência, sem duplicar registros; preservar a origem de cada dado e informar o estado ou a data de atualização disponível. O Custodian/TI acompanha a custódia e a atualização; integrações automáticas entre ferramentas são dependência futura e não são pressupostas neste requisito. | Quais fontes foram recebidas, atualizadas e padronizadas, quais registros foram deduplicados e qual origem sustenta cada dado? | Objetivo de integrar fontes (§3); limitações e melhoria esperada do fluxo (§4.0.2); dicionário (§4.0.1); TAPI [1], Arquitetura de Negócio [2], DMC [3], JTBD/HMW [4] e Problem Canvas [5]. |
| RF13 | Questionário validado e versionado | Como responsável de uma área técnica, quero revisar e versionar o questionário associado à pesquisa, para assegurar que perguntas e validações estejam identificadas antes da divulgação. | Associar a cada versão a pesquisa, área revisora, estado da validação e histórico de alterações quando esses metadados estiverem registrados; classificar a validação como observada ou proposta e não afirmar que uma versão foi validada quando não houver registro. | Qual versão do questionário foi revisada por qual área técnica, em que estado de validação e antes de qual marco do ciclo? | Processo de planejamento e validação (§4.0.2); `questoes.csv` (§4.0.1); capacidade de validação técnica da Arquitetura de Negócio [2]; TAPI [1], JTBD/HMW [4] e Problem Canvas [5]. |

### 6.1.1 Critérios de aceitação dos requisitos funcionais

Os critérios abaixo descrevem resultados observáveis, independentemente da
tecnologia de implementação. “Sem dados” significa que a consulta foi executada
com sucesso e não encontrou registros; “indisponível” significa que a fonte não
fornece o dado necessário; e “erro” significa que a consulta não pôde ser
concluída. Essas situações devem permanecer distintas.

#### RF01 — Portfólio de pesquisas

- **Consulta principal:** Dado um gestor ou analista autorizado e pesquisas disponíveis, quando consultar o portfólio, então cada item apresenta ao menos o identificador e o título preservados da fonte.
- **Filtros e segmentações:** Dado o portfólio carregado, quando aplicar combinações dos filtros de período, tipo, área, complexidade e status, então a lista e a distribuição exibem somente pesquisas compatíveis e permitem retirar os filtros.
- **Estado vazio:** Dado um conjunto de filtros sem correspondência, quando executar a consulta, então o resultado informa que não há pesquisas para o recorte, sem apresentar falha de carregamento ou contagens de outro recorte.
- **Erro:** Dado que a fonte não pôde ser consultada, quando abrir ou filtrar o portfólio, então a indisponibilidade é informada e nenhum resultado parcial é apresentado como completo.
- **Acesso:** Dado um perfil sem permissão para o portfólio interno, quando tentar consultá-lo, então os dados são bloqueados sem revelar títulos, identificadores ou atributos restritos.

#### RF02 — Ciclo e detalhe da pesquisa

- **Consulta principal:** Dada uma pesquisa existente, quando abrir seu detalhe, então são exibidos o identificador, o status e os marcos disponíveis de solicitação, aprovação, divulgação, coleta, entrega, tabulação e publicação.
- **Classificação dos marcos:** Dado um marco registrado, inferível ou ainda não representado, quando o detalhe for exibido, então ele é identificado respectivamente como **observado**, **derivado** ou **proposto**, com a informação que sustenta a classificação.
- **Dado ausente:** Dado um marco sem registro suficiente, quando abrir o detalhe, então o marco é informado como indisponível ou proposto, conforme o caso, e não como concluído.
- **Pesquisa inexistente:** Dado um identificador sem correspondência, quando solicitar o detalhe, então a interface informa que a pesquisa não foi encontrada e não reutiliza dados da consulta anterior.
- **Erro ou acesso:** Dada uma falha de consulta ou um perfil sem permissão para o detalhe interno, quando tentar abri-lo, então a situação correspondente é informada sem expor conteúdo restrito.

#### RF03 — Prazos e prioridades

- **Comparação temporal:** Dadas pesquisas com datas de referência disponíveis, quando consultar prazos e tempos, então cada classificação de atraso, duração ou prorrogação permite identificar as datas usadas na comparação.
- **Prorrogação:** Dada uma pesquisa com `prorrogada_ate` registrada, quando compará-la ao prazo original, então o novo marco é apresentado sem substituir ou ocultar a data limite original.
- **Filtros:** Dado o conjunto de pesquisas, quando filtrar por período, estado de prazo, prorrogação ou prioridade declarada, então somente os registros compatíveis compõem a lista e as comparações.
- **Informação indisponível:** Dada uma pesquisa sem uma data necessária ou sem prioridade declarada, quando analisá-la, então a classificação dependente aparece como indisponível e não como atraso, ausência de prioridade ou duração igual a zero.
- **Erro ou acesso:** Dada uma falha da fonte ou um perfil sem acesso aos dados operacionais, quando consultar prazos, então a consulta é interrompida com mensagem própria e sem expor detalhes restritos.

#### RF04 — Adesão e representatividade

- **Cálculo sustentado:** Dada uma pesquisa com universo documentado, quando consultar adesão, então o resultado exibe o numerador, o denominador e o recorte usados no cálculo.
- **Segmentação:** Dados vínculos conciliados, quando segmentar por pesquisa ou empresa, então as contagens e medidas de mercado refletem somente o recorte selecionado e preservam a origem dos valores.
- **Denominador ausente:** Dada uma pesquisa sem universo convidado, esperado ou equivalente documentado, quando consultar adesão, então são exibidas as contagens disponíveis e a indicação “denominador indisponível”, sem taxa inferida.
- **Identidade em reconciliação:** Dada uma participação ou empresa sem correspondência conciliada, quando compor a análise, então o registro é sinalizado como em reconciliação e não é associado por semelhança de nome ou identificador incompatível.
- **Vazio, erro ou acesso:** Dado um recorte sem participação, uma falha de consulta ou um perfil não autorizado, quando executar a análise, então cada estado é distinguido e dados de empresas ou pessoas não são expostos indevidamente.

#### RF05 — Engajamento dos públicos

- **Agrupamentos:** Dados identificadores conciliados, quando agrupar a participação por área da pesquisa, departamento ou cargo, então cada grupo apresenta sua contagem e o recorte aplicado.
- **Filtros:** Dado o resultado agrupado, quando filtrar por pesquisa, período, empresa ou uma dimensão disponível, então os agrupamentos são recalculados apenas para o recorte selecionado.
- **Taxa sustentada:** Dado um denominador documentado para um grupo, quando exibir uma taxa de engajamento, então numerador e denominador ficam identificáveis; sem esse universo, apenas as contagens são exibidas e o denominador é marcado como indisponível.
- **Ausência distinta de zero:** Dado um cargo ou departamento ausente na fonte, quando formar os grupos, então ele aparece como informação não disponível e não como categoria com participação zero.
- **Vazio, erro ou acesso:** Dado um recorte sem registros, uma falha da fonte ou um perfil sem permissão, quando consultar o engajamento, então a situação é informada sem reutilizar resultados anteriores nem revelar dados pessoais.

#### RF06 — Qualidade e atualização

- **Consulta principal:** Dado um Data Steward ou analista autorizado, quando consultar a qualidade, então é possível identificar a fonte, o campo, a regra avaliada e a quantidade ou os registros afetados.
- **Nulos condicionais:** Dada uma regra dependente do tipo de questão ou do contexto do campo, quando avaliar completude, então uma ausência permitida é classificada separadamente de uma lacuna a investigar.
- **Validade e identidade:** Dadas variações de domínio, tipo ou chave entre fontes, quando avaliadas, então as ocorrências incompatíveis são sinalizadas sem correção silenciosa ou associação presumida.
- **Atualização:** Dada uma fonte com data ou estado de atualização disponível, quando consultá-la, então essa informação e sua origem são exibidas; sem metadado correspondente, o estado é “indisponível”, não “desatualizado”.
- **Vazio, erro ou acesso:** Dada uma consulta sem ocorrências, uma falha de leitura ou um perfil não autorizado, quando acessar a análise, então “nenhuma ocorrência”, “erro de consulta” e “acesso negado” são apresentados como estados distintos.

#### RF07 — Linhagem agregada ponta a ponta

- **Caminho observado:** Dado um resultado agregado com chaves correspondentes, quando consultar sua linhagem, então cada elo fonte → pesquisa → participação → questão → resposta exibe o arquivo ou sistema conhecido, a chave disponível e o estado **observado**.
- **Origem não identificada:** Dado um elo cujo sistema de origem não está registrado, quando exibir a linhagem, então o arquivo recebido é mostrado como origem disponível e o sistema é marcado como indisponível.
- **Pesquisas órfãs:** Dados os `pesquisa_id` 424, 1116, 1139 e 1147 presentes em questões ou respostas sem pesquisa correspondente, quando consultar a linhagem, então esses elos aparecem **em reconciliação** e não são associados a outra pesquisa.
- **Participações órfãs:** Dadas as 55 participações com `id_pesq=304` sem correspondência em `pesquisas.csv`, quando consultar a linhagem, então o vínculo com a pesquisa aparece **em reconciliação**, mantendo os registros e seus identificadores de origem.
- **Vazio, erro ou acesso:** Dado um agregado sem elo disponível, uma falha de consulta ou um perfil sem permissão de auditoria, quando solicitar a linhagem, então a situação correspondente é informada sem fabricar elos nem expor respostas individuais.

#### RF08 — Acesso por perfil

- **Visibilidade por perfil:** Dada a mesma consulta realizada por equipe interna, área técnica e solicitante externo, quando cada perfil acessar o resultado, então recebe apenas dados operacionais, identificáveis ou agregados permitidos pela regra aprovada para esse perfil.
- **Detalhamento:** Dado um perfil que pode consultar o agregado, mas não registros identificáveis, quando tentar detalhá-lo, então o detalhamento restrito é bloqueado sem revelar o conteúdo protegido.
- **Exportação:** Dado um perfil autorizado apenas a resultados agregados, quando exportar uma consulta, então o arquivo contém o mesmo recorte permitido na tela e nenhum campo identificável adicional.
- **Regra sem aprovação:** Dado um acesso para o qual não exista regra aprovada, quando o usuário tentar consultar, detalhar ou publicar, então a operação não é liberada como se houvesse autorização.
- **Registro da decisão:** Dada uma tentativa permitida ou bloqueada para a qual o processo exija registro, quando ela ocorrer, então perfil, operação e resultado da decisão podem ser verificados por pessoa autorizada.

#### RF09 — Publicação autorizada

- **Autorização explícita:** Dado um resultado com autorização registrada pelo Data Owner, quando o Custodian/TI o disponibilizar, então o estado de publicação, a decisão e o vínculo com a pesquisa de origem ficam consultáveis.
- **Ausência de autorização:** Dado um resultado sem autorização explícita, quando houver tentativa de publicação, então ele não é disponibilizado e o estado informa que a autorização está ausente.
- **Data insuficiente:** Dada uma pesquisa com `data_divulgacao`, mas sem metadado de autorização ou publicação, quando consultar seu estado, então a data não é usada como prova de que o resultado foi autorizado ou publicado.
- **Consistência:** Dado um conteúdo publicado, quando compará-lo à referência interna permitida, então o identificador da pesquisa e os metadados de publicação correspondem; divergências são sinalizadas sem substituição silenciosa.
- **Vazio, erro ou acesso:** Dada uma consulta sem publicações, uma falha do acervo ou um perfil sem permissão de publicar, quando executar a operação, então o estado correspondente é informado e conteúdo não autorizado permanece indisponível.

#### RF10 — Resultados agregados

- **Distribuição:** Dada uma pesquisa e questão com respostas, quando consultar seus resultados, então são exibidas as contagens por alternativa ou valor e o número de elementos de resposta válidos no recorte.
- **Granularidade atômica:** Dadas questões que geram múltiplas linhas por respondente, como checkbox ou matriz, quando contar os dados, então cada linha é tratada como elemento de resposta e não é apresentada automaticamente como um questionário ou respondente único.
- **Matriz:** Dada uma questão matricial, quando consultar a distribuição, então linha, coluna e valor disponíveis permanecem associados à questão e ao recorte da pesquisa.
- **Filtros e denominador:** Dado um filtro permitido por pesquisa, questão ou segmento, quando aplicá-lo, então a distribuição é recalculada para o recorte; na ausência de universo populacional, o denominador é indicado como indisponível e nenhuma taxa populacional é inferida.
- **Vazio, erro ou acesso:** Dada uma questão sem respostas, uma falha de consulta ou um perfil limitado ao agregado, quando abrir o resultado, então o estado é informado e nenhum registro individual é exibido.

#### RF11 — Contexto de resposta autorizado

- **Contexto agregado:** Dado um resultado agregado, quando um analista ou auditor autorizado consultar seu contexto, então são exibidos somente os elos disponíveis com pesquisa, questão e participação e os denominadores efetivamente sustentados.
- **Ponte individual ausente:** Dado que os arquivos recebidos não oferecem ponte explícita entre `respostas.respondent_id` e `respondentes.id_cliente`, quando solicitar contexto individual, então a ausência do vínculo é informada e nenhuma associação por nome, posição ou semelhança é produzida.
- **Permissão individual:** Dado um perfil sem autorização para dados individuais, quando tentar detalhar o agregado, então a consulta é bloqueada mesmo que algum identificador esteja presente na fonte.
- **Denominador ausente:** Dado um agregado sem universo de respostas ou população documentado, quando exibir seu contexto, então o denominador é marcado como indisponível e não é substituído pela quantidade de linhas.
- **Vazio ou erro:** Dado um resultado sem contexto relacionável ou uma falha de consulta, quando abrir o contexto, então a ausência de elos e o erro são distinguidos e não se exibe contexto de outra consulta.

#### RF12 — Integração e atualização das fontes

- **Recebimento e origem:** Dada uma fonte recebida, quando consultar sua integração, então são identificáveis a fonte, o estado ou data de atualização disponível e a origem preservada dos registros.
- **Padronização:** Dados nomes, tipos ou domínios divergentes, quando a fonte for consolidada, então as transformações aplicadas são verificáveis e os valores originais permanecem rastreáveis.
- **Duplicidades:** Dados registros que atendam à regra documentada de duplicidade, quando processados, então são sinalizados ou consolidados conforme essa regra sem eliminar silenciosamente registros distintos.
- **Reprocessamento idempotente:** Dado o mesmo conteúdo de origem já processado, quando ele for reprocessado sem alteração, então não surgem registros adicionais e o estado da execução pode ser verificado.
- **Metadado ausente, erro ou acesso:** Dada uma fonte sem data de atualização, uma execução com falha ou um perfil não autorizado, quando consultar a integração, então os estados “indisponível”, “erro” e “acesso negado” permanecem distintos e não se presume integração automática.

#### RF13 — Questionário validado e versionado

- **Versão observada:** Dado um questionário com metadados de versão e validação registrados, quando abrir seu histórico, então pesquisa, versão, área revisora, estado da validação e alterações disponíveis podem ser conferidos.
- **Relação temporal:** Dados marcos de validação e divulgação registrados, quando consultar o questionário, então é possível verificar sua ordem sem afirmar que a validação ocorreu antes da divulgação quando faltar uma das datas.
- **Metadados ausentes:** Dadas questões associadas a uma pesquisa, mas sem versão, área revisora ou aprovação registradas, quando consultar o questionário, então esses metadados aparecem como propostos ou indisponíveis e o questionário não é rotulado como validado.
- **Filtros e histórico:** Dados questionários de diferentes pesquisas ou estados, quando filtrar por pesquisa, área ou estado disponível, então somente versões compatíveis são exibidas e versões anteriores não são sobrescritas no histórico.
- **Vazio, erro ou acesso:** Dada uma pesquisa sem questões, uma falha de consulta ou um perfil sem permissão de revisão, quando abrir ou alterar a validação, então a situação correspondente é informada e nenhuma aprovação é registrada.

### 6.1.2 Testes de usuário dos requisitos funcionais

Os testes devem usar um ambiente controlado, perfis de validação sem dados
pessoais reais e uma versão identificada das fontes. Sempre que uma
pré-condição depender de metadado ainda proposto — como autorização de
publicação, versionamento ou regra nominal de acesso — o dado deve ser preparado
como massa de teste e identificado como tal. A equipe da Central de Pesquisas é
a responsável pela aprovação funcional, com participação do papel de governança
indicado em cada roteiro.

#### RF01 — Teste do portfólio de pesquisas

- **Persona e objetivo:** gestor ou analista da Central; localizar pesquisas e conferir a distribuição do portfólio em um recorte relevante.
- **Pré-condições e dados:** perfil autorizado; fonte `pesquisas.csv` identificada; ao menos uma combinação de filtros com resultado e outra sem resultado; mecanismo controlado para simular falha da consulta; perfil sem acesso interno.
- **Passos:**
  0. Abrir o portfólio e conferir identificador e título de pesquisas da fonte.
  0. Aplicar e retirar filtros de período, tipo, área, complexidade e status, isoladamente e em combinação.
  0. Aplicar o recorte previamente identificado sem correspondências.
  0. Repetir a consulta durante a falha controlada e com o perfil sem acesso.
- **Resultado esperado:** lista e distribuição acompanham os filtros; retirar filtros restaura o conjunto permitido; recorte vazio, erro e bloqueio de acesso têm mensagens distintas; nenhum dado restrito aparece ao perfil sem acesso.
- **Evidência:** capturas do estado inicial, dos filtros, do vazio, do erro e do bloqueio, acompanhadas do recorte da fonte usado na conferência.
- **Aprovação:** gestor ou analista da Central registra aprovação se todos os resultados corresponderem à fonte e nenhum estado for confundido com outro.

#### RF02 — Teste do ciclo e detalhe da pesquisa

- **Persona e objetivo:** analista da Central; entender a etapa e os marcos sustentados no detalhe de uma pesquisa.
- **Pré-condições e dados:** perfil autorizado; uma pesquisa existente com marcos registrados e ausentes; regra documentada para eventual marco derivado; identificador comprovadamente inexistente; falha controlada; perfil sem acesso ao detalhe interno.
- **Passos:**
  0. Abrir a pesquisa existente e comparar status, datas e marcos com a fonte.
  0. Conferir as classificações observado, derivado e proposto e a evidência disponível para cada uma.
  0. Consultar o identificador inexistente.
  0. Repetir a abertura durante a falha controlada e com o perfil sem acesso.
- **Resultado esperado:** o detalhe preserva a pesquisa consultada; marcos sem registro não aparecem como concluídos; o identificador inexistente não retorna outro registro; erro e bloqueio são distintos e não expõem conteúdo.
- **Evidência:** captura do detalhe e de suas classificações, comparação com as linhas da fonte e registros dos estados inexistente, erro e bloqueado.
- **Aprovação:** analista da Central aprova quando consegue explicar cada classificação a partir da evidência exibida.

#### RF03 — Teste de prazos e prioridades

- **Persona e objetivo:** gestor ou analista da Central; comparar prazos e ordenar o acompanhamento sem conclusões temporais indevidas.
- **Pré-condições e dados:** pesquisas com datas de referência completas, com `prorrogada_ate` e com datas necessárias ausentes; se houver teste de prioridade, metadado de prioridade declarado como massa proposta; perfil restrito e falha controlada.
- **Passos:**
  0. Consultar as pesquisas com datas completas e conferir as comparações com as datas de origem.
  0. Abrir a pesquisa prorrogada e verificar prazo original e novo prazo.
  0. Aplicar filtros de período, prazo, prorrogação e, quando disponível, prioridade declarada.
  0. Consultar a pesquisa com data ausente e repetir a consulta sob falha e acesso restrito.
- **Resultado esperado:** classificações temporais mostram as referências usadas; a prorrogação não apaga o prazo original; dados ausentes ficam indisponíveis, sem zero ou conclusão; erro e acesso negado não exibem resultados operacionais.
- **Evidência:** planilha de conferência das datas e classificações, capturas dos filtros e registros dos estados indisponível, erro e bloqueado.
- **Aprovação:** gestor ou analista da Central aprova se reproduzir as comparações a partir das datas disponíveis e não encontrar prioridade inferida.

#### RF04 — Teste de adesão e representatividade

- **Persona e objetivo:** analista da Central; validar uma leitura de adesão e representatividade sem inventar universo ou identidade.
- **Pré-condições e dados:** pesquisa com denominador documentado em massa controlada; pesquisa sem denominador; participações e empresas conciliadas; caso em reconciliação; recorte vazio; perfil não autorizado e falha controlada.
- **Passos:**
  0. Consultar a pesquisa com universo documentado e recalcular a medida usando numerador e denominador exibidos.
  0. Segmentar por pesquisa e empresa e conferir contagens e medidas de mercado com as fontes.
  0. Consultar a pesquisa sem universo e o caso de identidade em reconciliação.
  0. Executar o recorte vazio e repetir a consulta sob falha e acesso restrito.
- **Resultado esperado:** somente o caso sustentado apresenta taxa; o caso sem universo apresenta contagem e denominador indisponível; identidade não conciliada não é unida automaticamente; vazio, erro e bloqueio permanecem distintos.
- **Evidência:** memória de cálculo, extratos anonimizados das fontes, capturas das segmentações e registros dos estados excepcionais.
- **Aprovação:** analista da Central e Data Steward aprovam se o cálculo for reproduzível e todos os vínculos usados estiverem conciliados ou explicitamente sinalizados.

#### RF05 — Teste de engajamento dos públicos

- **Persona e objetivo:** gestor ou analista da Central; comparar participação por área, departamento e cargo sem interpretar ausência como zero.
- **Pré-condições e dados:** identificadores conciliados entre pesquisas, participações e clientes; grupos preenchidos e ausentes; denominador documentado apenas para um recorte controlado; recorte vazio; falha controlada e perfil sem acesso a dados pessoais.
- **Passos:**
  0. Agrupar por área, departamento e cargo e comparar as contagens com as fontes.
  0. Aplicar filtros por pesquisa, período, empresa e dimensão disponível.
  0. Conferir o recorte com denominador e outro sem universo documentado.
  0. Consultar um atributo ausente, o recorte vazio, a falha controlada e o perfil restrito.
- **Resultado esperado:** grupos e filtros preservam o recorte; taxa aparece somente com numerador e denominador; atributo ausente não vira grupo de participação zero; dados pessoais não são revelados no bloqueio.
- **Evidência:** tabela de reconciliação das contagens, memória de cálculo e capturas dos agrupamentos e estados excepcionais.
- **Aprovação:** gestor ou analista da Central aprova se as contagens forem reproduzíveis e Data Steward confirma o tratamento das ausências.

#### RF06 — Teste de qualidade e atualização

- **Persona e objetivo:** Data Steward ou analista da Central; distinguir lacunas reais, ausências condicionais e metadados indisponíveis.
- **Pré-condições e dados:** versão identificada das fontes e do dicionário; questão aberta sem campos de matriz; questão matricial com os campos aplicáveis; variações de domínio ou tipo conhecidas; fonte com e sem metadado de atualização; perfil restrito e falha controlada.
- **Passos:**
  0. Executar as regras de completude sobre os dois tipos de questão e conferir a classificação dos nulos.
  0. Consultar ocorrências de validade, domínio e identidade por fonte e campo.
  0. Comparar o estado de atualização das fontes com os metadados disponíveis.
  0. Consultar uma regra sem ocorrências e repetir sob falha e acesso restrito.
- **Resultado esperado:** nulo permitido não é lacuna; inconsistências permanecem visíveis; fonte sem metadado aparece como indisponível, não desatualizada; zero ocorrências, erro e bloqueio são distintos.
- **Evidência:** relatório das regras executadas com versão das fontes, amostras anonimizadas das ocorrências e capturas dos estados avaliados.
- **Aprovação:** Data Steward aprova após confirmar regra, fonte, campo e interpretação de cada resultado.

#### RF07 — Teste de linhagem agregada ponta a ponta

- **Persona e objetivo:** Data Steward ou auditor de dados; rastrear um agregado e confirmar que anomalias não recebem vínculos inventados.
- **Pré-condições e dados:** agregado com chaves correspondentes; arquivos de origem identificados; casos `pesquisa_id` 424, 1116, 1139 e 1147; 55 participações com `id_pesq=304`; caso sem sistema de origem registrado; perfil sem auditoria e falha controlada.
- **Passos:**
  0. Abrir a linhagem do agregado conciliado e seguir cada elo até os arquivos e chaves disponíveis.
  0. Consultar um elo cujo sistema de origem não esteja identificado.
  0. Consultar separadamente os quatro `pesquisa_id` órfãos e as participações vinculadas a `id_pesq=304`.
  0. Repetir a consulta sob falha e com o perfil sem auditoria.
- **Resultado esperado:** caminho conciliado aparece como observado; sistema ausente é declarado; os casos órfãos permanecem em reconciliação com seus IDs originais; falha e bloqueio não fabricam linhagem nem expõem resposta individual.
- **Evidência:** exportação ou captura de cada caminho, conferência das chaves nas fontes e registro da quantidade de participações órfãs.
- **Aprovação:** Data Steward ou auditor aprova se conseguir percorrer os elos observados e confirmar a preservação de todas as anomalias.

#### RF08 — Teste de acesso por perfil

- **Persona e objetivo:** Data Owner ou gestor da Central; confirmar que consulta, detalhe e exportação obedecem à regra aprovada.
- **Pré-condições e dados:** regra de acesso aprovada para perfis de equipe interna, área técnica e solicitante externo; contas de teste para cada perfil; consulta comum com dados operacionais, identificáveis e agregados; exportação habilitada onde permitida.
- **Passos:**
  0. Executar a mesma consulta com cada perfil e registrar os campos e níveis de detalhe visíveis.
  0. Tentar abrir dado identificável com um perfil limitado ao agregado.
  0. Exportar a consulta com cada perfil autorizado e comparar arquivo e tela.
  0. Tentar uma operação cuja regra ainda não tenha aprovação e consultar o registro da decisão, quando aplicável.
- **Resultado esperado:** cada perfil vê apenas o permitido; detalhe restrito é bloqueado; exportação não amplia o acesso; regra ausente não concede permissão; a decisão é verificável por perfil autorizado.
- **Evidência:** matriz perfil × operação × resultado, capturas anonimizadas e arquivos exportados inspecionados campo a campo.
- **Aprovação:** Data Owner aprova a matriz e confirma que nenhum caminho de tela ou exportação ultrapassa a regra vigente.

#### RF09 — Teste de publicação autorizada

- **Persona e objetivo:** Data Owner ou gestor da Central; comprovar que somente resultado explicitamente autorizado chega ao acervo.
- **Pré-condições e dados:** resultados de teste autorizado e não autorizado; decisão identificada do Data Owner; pesquisa com `data_divulgacao` e sem metadado de publicação; referência interna permitida; perfil sem permissão de publicar e falha controlada do acervo.
- **Passos:**
  0. Publicar o resultado autorizado e conferir estado, decisão e vínculo com a pesquisa.
  0. Tentar publicar o resultado sem autorização explícita.
  0. Consultar a pesquisa que possui apenas `data_divulgacao` e comparar o conteúdo publicado à referência interna.
  0. Consultar o acervo vazio ou indisponível e tentar publicar com o perfil restrito.
- **Resultado esperado:** somente o autorizado é disponibilizado; `data_divulgacao` não prova publicação; divergências ficam sinalizadas; vazio, falha e falta de permissão são distintos e não liberam conteúdo.
- **Evidência:** registro da autorização, capturas antes e depois da tentativa, referência do item no acervo e comparação dos metadados.
- **Aprovação:** Data Owner aprova a disponibilização e a equipe da Central confirma o vínculo; qualquer publicação sem decisão explícita reprova o teste.

#### RF10 — Teste de resultados agregados

- **Persona e objetivo:** analista da Central ou leitor autorizado; conferir distribuições sem confundir elemento de resposta, respondente e questionário.
- **Pré-condições e dados:** pesquisa com questão de alternativa ou valor; questão do tipo checkbox; questão matricial; questão sem respostas; recortes permitidos; perfil limitado ao agregado e falha controlada.
- **Passos:**
  0. Consultar e recalcular as distribuições da questão de alternativa ou valor.
  0. Comparar quantidade de linhas, respondentes distintos e questões no caso de checkbox, sem tratá-las como a mesma medida.
  0. Conferir linha, coluna e valor da questão matricial e aplicar filtros permitidos.
  0. Abrir a questão sem respostas e repetir sob falha e com o perfil limitado ao agregado.
- **Resultado esperado:** distribuições correspondem aos elementos válidos; checkbox e matriz preservam a granularidade atômica; denominador populacional ausente não gera taxa; vazio e erro são distintos; nenhum registro individual é exposto.
- **Evidência:** memória de contagem por tipo de questão, extratos anonimizados das fontes e capturas das distribuições, filtros e estados excepcionais.
- **Aprovação:** analista da Central aprova se reproduzir as distribuições; leitor autorizado confirma que a apresentação é compreensível e não identificável.

#### RF11 — Teste de contexto de resposta autorizado

- **Persona e objetivo:** auditor de dados ou analista autorizado; verificar o contexto sustentado de um agregado sem presumir identidade individual.
- **Pré-condições e dados:** agregado relacionado a pesquisa e questão; arquivos desta versão sem ponte explícita entre `respostas.respondent_id` e `respondentes.id_cliente`; perfil autorizado ao agregado e perfil sem acesso individual; caso sem contexto relacionável; falha controlada.
- **Passos:**
  0. Abrir o contexto do agregado e conferir cada elo e denominador com as fontes.
  0. Solicitar o contexto individual baseado nos dois campos sem ponte explícita.
  0. Tentar o detalhamento com o perfil sem acesso individual.
  0. Abrir o caso sem contexto e repetir durante a falha controlada.
- **Resultado esperado:** somente elos sustentados são exibidos; a ponte ausente é declarada e não inferida; o perfil restrito é bloqueado; contexto ausente e erro não reutilizam dados de outra consulta.
- **Evidência:** captura do contexto agregado, consulta das chaves nas fontes e registros das tentativas individual, bloqueada, vazia e com erro.
- **Aprovação:** auditor ou analista e Data Steward aprovam se nenhum vínculo individual ou denominador for criado sem evidência.

#### RF12 — Teste de integração e atualização das fontes

- **Persona e objetivo:** Data Custodian/TI ou analista da Central; verificar origem, padronização, deduplicação e reprocessamento sem duplicação.
- **Pré-condições e dados:** cópia controlada de uma fonte com origem identificada; valores de domínio ou tipo que exijam padronização; duplicatas segundo regra documentada e registros semelhantes que não atendam à regra; fonte sem data de atualização; perfil restrito; execução com falha controlada.
- **Passos:**
  0. Processar a fonte e conferir origem, transformações, estado ou data disponível e tratamento das duplicatas.
  0. Confirmar que registros apenas semelhantes não foram eliminados.
  0. Reprocessar sem alteração exatamente o mesmo conteúdo e comparar as quantidades e identificadores antes e depois.
  0. Consultar a fonte sem metadado, a execução com falha e o perfil restrito.
- **Resultado esperado:** transformações são rastreáveis; a regra de duplicidade é respeitada; o reprocessamento não cria registros adicionais; metadado indisponível, falha e acesso negado são estados distintos.
- **Evidência:** identificação do conteúdo de entrada, relatório de transformações, contagens e identificadores antes/depois e registros das execuções.
- **Aprovação:** Data Custodian/TI aprova a execução e Data Steward confirma que padronização e deduplicação seguem regras documentadas.

#### RF13 — Teste de questionário validado e versionado

- **Persona e objetivo:** responsável de área técnica; conferir versão, revisão e validação de um questionário sem afirmar metadados inexistentes.
- **Pré-condições e dados:** questionário de teste com versão e validação registradas; outro com questões, mas sem metadados de versão, área revisora ou aprovação; marcos temporais disponíveis e ausentes; pesquisa sem questões; perfil sem permissão de revisão e falha controlada.
- **Passos:**
  0. Abrir o histórico do questionário versionado e conferir pesquisa, versão, área, estado, alterações e datas com os registros.
  0. Filtrar por pesquisa, área e estado e retornar a uma versão anterior.
  0. Abrir o questionário sem metadados e verificar a relação possível com o marco de divulgação.
  0. Consultar a pesquisa sem questões e tentar validar sob falha e com o perfil restrito.
- **Resultado esperado:** histórico não é sobrescrito; ordem temporal só é afirmada com marcos disponíveis; metadados ausentes aparecem como propostos ou indisponíveis; vazio, erro e bloqueio não registram validação.
- **Evidência:** capturas do histórico e filtros, comparação com os metadados de teste e registros das tentativas sem dados, com erro e sem permissão.
- **Aprovação:** responsável da área técnica aprova o histórico observado e Data Steward confirma que nenhuma validação ou versão foi inferida.

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

As perguntas abaixo explicitam o vínculo mínimo entre os requisitos e o uso
analítico. Elas não definem dashboards, visualizações ou critérios de teste;
essas especificações ficam para as seções e issues próprias.

| ID | Pergunta de negócio | Requisito(s) associado(s) |
| :--- | :--- | :--- |
| PB01 | Quais pesquisas compõem o portfólio e como se distribuem por período, tipo, área, complexidade e status? | RF01 |
| PB02 | Em que etapa está cada pesquisa, quais marcos foram observados ou derivados e quais informações do seu detalhe estão disponíveis? | RF02 |
| PB03 | Quais pesquisas estão atrasadas, foram prorrogadas ou demandam prioridade, qual denominador sustenta cada comparação e como os tempos do ciclo se comparam? | RF03 |
| PB04 | A participação alcançada é suficiente e representa as empresas ou parcelas de mercado relevantes, e qual denominador sustenta essa leitura? | RF04 |
| PB05 | Quais áreas, departamentos e cargos participam mais ou menos, e qual é o denominador disponível para o engajamento? | RF05 |
| PB06 | Quais dados estão completos e válidos, quais lacunas permanecem e qual é o estado de atualização de cada fonte? | RF06 |
| PB07 | Qual sistema ou arquivo sustenta cada elo do agregado, qual é o estado observado, em reconciliação ou proposto, e como tratar os quatro `pesquisa_id` (424, 1116, 1139 e 1147) sem correspondência e as 55 participações com `id_pesq=304` ausente? | RF07 |
| PB08 | Que dados cada perfil pode consultar, detalhar ou publicar sem expor informações não autorizadas? | RF08 |
| PB09 | O resultado foi autorizado e publicado, quais metadados sustentam essa decisão e ele está consistente com a pesquisa interna correspondente? | RF09 |
| PB10 | Qual foi a distribuição das respostas para cada questão, qual denominador está disponível e como ela varia entre pesquisas ou segmentos permitidos? | RF10 |
| PB11 | Qual evidência agregada sustenta este resultado, que contexto está disponível e a consulta individual é autorizada e suportada pelos dados? | RF11 |
| PB12 | Quais fontes foram recebidas, atualizadas e padronizadas, quais registros foram deduplicados e qual origem sustenta cada dado? | RF12 |
| PB13 | Qual versão do questionário foi revisada por qual área técnica, em que estado de validação e antes de qual marco do ciclo? | RF13 |

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
| Data Owner | A designar pelo parceiro (a validar) | Aprovar prioridades, regras de acesso e publicação dos resultados. |
| Data Steward | A designar pelo parceiro (a validar) | Definir significados, acompanhar qualidade, reconciliação e linhagem dos dados. |
| Data Custodian/TI | Equipe de TI; atribuição nominal a validar | Custodiar fontes, acompanhar atualização e sustentar a disponibilização autorizada. |

# 7. Referências

[1] INTELI; SINDUSFARMA. **Termo de Abertura de Projeto Inteli (TAPI) — ESMD11: arquitetura e governança de dados alinhada à estratégia corporativa**. São Paulo, 2026. Documento de projeto (arquivo local `context/Tapi-sinduspharma.txt`) disponibilizado pela faculdade e pelo parceiro de projeto.

[2] INTELI; SINDUSFARMA. **Arquitetura de Negócio: Central de Pesquisas do Sindusfarma**. São Paulo, 2026. Documento de projeto (arquivo local `context/Arquitetura-de-Negócio-Central-de-Pesquisas-do-Sindusfarma.txt`) disponibilizado pela faculdade e pelo parceiro de projeto.

[3] INTELI; SINDUSFARMA. **Data Model Canvas: Data Warehouse — Sindusfarma**. São Paulo, 2026. Artefato de documentação (arquivo `Data Model Canvas.pdf`) disponibilizado pela faculdade e pelo parceiro de projeto.

[4] GRUPO 5. **JTBD a partir do Data Model Canvas — Central de Pesquisas do Sindusfarma**. São Paulo, 2026. Artefato local de levantamento (arquivo `context/JTBD-a-partir-do-Data-Model-Canvas.txt`).

[5] GRUPO 5. **Problem Canvas — Gestão integrada de pesquisas setoriais**. São Paulo, 2026. Artefato local de levantamento (arquivo `context/problem_canvas_sindusfarma_completo (1).html`).

[6] GRUPO 5. **Dicionário de variáveis de respostas**. São Paulo, 2026. Artefato local de dados (arquivo `context/Dicionario_Variaveis_Respostas_Grupo6.xlsx - Dicionário.csv`).

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
