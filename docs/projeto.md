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

Esta seção diagnostica dados ausentes e registros duplicados nas seis bases disponibilizadas, para apoiar as regras de qualidade da solução. A medição foi executada pelo artefato versionado `scripts/data_quality/profile_csv.py`, conforme `scripts/data_quality/manifest.json`, usando UTF-8 (BOM aceito), separador `;`, decimal brasileiro e percentual com sufixo `%`. O manifesto registra `teste.csv` como alias local conceitual de `respostas.csv`; o arquivo bruto não foi copiado para o repositório nem para as saídas. O dicionário é validado de fato: cabeçalho, nove variáveis, conteúdo mínimo e alegações verificáveis de cardinalidade e nulos são confrontados com a base. **Não houve duplicidade de linha nem das chaves declaradas** nas seis fontes. Chaves estrangeiras (FKs) podem repetir legitimamente por representarem muitos registros filhos para uma mesma entidade e não foram tratadas como duplicatas. As ausências, por outro lado, exigem leitura cuidadosa: parte é **condicional** — estrutural e esperada, seguindo o tipo da pergunta ou o estágio do ciclo de vida da pesquisa (ex.: `linha_matriz` só existe em perguntas de matriz; `prorrogada_ate` só quando há prorrogação) — e parte é **a investigar**, indicando possível lacuna de preenchimento a tratar antes de automatizar indicadores.[<sup>\[2\]</sup>](#7-referências)[<sup>\[12\]</sup>](#7-referências)

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
| Taxa de duplicação de linhas/chaves declaradas | `duplicadas_extras / linhas × 100` | % | linha ou chave declarada da base | `resumo.csv` | 0,0% nas seis bases medidas; repetição de FK é legítima |
| Taxa de órfãos | `órfãos / comparáveis × 100` | % | chave de relação | `relacionamentos.csv` | 18,6% em questões→pesquisas e 17,4% em respostas→pesquisas |
| Elementos de resposta | `COUNT(respostas.id_resposta)` | registros | elemento atômico de resposta | `respostas.csv`/alias `teste.csv` | 20.607; não equivale a respondentes |
| Respondentes distintos | `COUNT(DISTINCT respondent_id)` | respondentes | pesquisa e respondente | `respostas.csv`/alias `teste.csv` | 542 distintos; vínculo com `respondentes` ainda não está comprovado |
| Violação temporal | `pares fora de ordem / pares comparáveis × 100` | % | par temporal por pesquisa/participação | `coerencia_temporal.csv` | 0,0% nos pares preenchidos medidos; completude continua separada |
| Consistência de domínio | `contagem por valor normalizado / linhas × 100` | % | campo categórico | `dominios.csv` | Identifica `Sim/sim`, `Brasil/BRASIL/brasil` e vazios |
| Percentual parseável | `valores parseáveis / valores não nulos × 100` | % | campo percentual | `percentuais.csv` | 100,0% nos três campos; inválidos e fora de `[0,100]` = 0 |
| Ausência condicional inesperada | `ausências obrigatórias / linhas aplicáveis × 100` | % | tipo de questão e campo de resposta | `nulos_condicionais.csv` | 0,1% em cada dimensão de matriz; regra proposta por tipo |
| Divergência denormalizada | `títulos divergentes / pares comparáveis × 100` | % | questão–pesquisa | `denormalizados.csv` | 41/188 (21,8%), IDs 414 e 415 |
| Divergência do dicionário | `alegação − medição física/semântica` | registros | cada um dos nove campos de `respostas` | `dicionario_validacao.csv` | Cardinalidades e nulos verificáveis conferem; em `valor`, 8.309 alegados − 8.307 vazios = 2 sentinelas |

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
Canvas ([3]) e os artefatos locais de JTBD/HMW e Problem Canvas ([13] e [14]).
A menção a uma fonte sem campo correspondente no dicionário registra uma
necessidade a confirmar, não um dado já disponível.

Esta tabela delimita escopo e comportamento funcional; não prescreve tecnologia,
SLA, periodicidade ou atualização em tempo real. Critérios de aceitação
completos e testes de usuário serão definidos e validados na issue **#19**;
portanto, não são repetidos aqui nem devem ser inferidos a partir da coluna de
funcionalidade analítica.

As personas usadas nas User Stories correspondem aos públicos do projeto:
analista ou operador da Central (acompanha e analisa o ciclo), gestor da Central
(prioriza e autoriza), responsável de área técnica (valida e versiona o
questionário), auditor de dados (confere qualidade e linhagem) e solicitante ou
participante autorizado (consulta resultados permitidos). “Leitor autorizado”
é a forma curta para o solicitante ou participante com permissão de consulta;
“auditor de dados” é um papel funcional de governança, não uma afirmação de
cargo adicional na organização. Esses papéis são derivados dos usuários
primário, secundário e terciário do TAPI [1] e dos públicos do Problem Canvas
[14].

Na governança, o Data Owner é o responsável de negócio por aprovar prioridades,
acessos e publicação; o Data Steward cuida de definições, qualidade e linhagem;
e o Data Custodian/TI responde pela custódia, atualização e sustentação das
fontes. A atribuição nominal desses papéis ainda é um ponto a validar com o
parceiro e não cria requisitos adicionais.

| ID | Nome curto | User Story | Funcionalidade analítica | Pergunta(s) de negócio | Fonte/motivação |
| :--- | :--- | :--- | :--- | :--- | :--- |
| RF01 | Portfólio de pesquisas | Como gestor ou analista da Central, quero consultar o portfólio de pesquisas por período, tipo, área, complexidade e status, para decidir quais demandas acompanhar. | Listar e segmentar as pesquisas e apresentar a distribuição do portfólio pelos atributos disponíveis, preservando o identificador e o título de cada pesquisa. | Quais pesquisas compõem o portfólio e como elas se distribuem por período, tipo, área, complexidade e status? | Objetivos (§3); processos de solicitação e triagem (§4.0.2); campos de `pesquisas.csv` (§4.0.1); TAPI [1], JTBD/HMW [13] e Problem Canvas [14]. |
| RF02 | Ciclo e detalhe da pesquisa | Como analista da Central, quero acompanhar a etapa e abrir o detalhe de uma pesquisa, para entender sua situação e o que precisa ser acompanhado. | Exibir status, datas e detalhes do ciclo — solicitação, aprovação, divulgação, coleta, entrega, tabulação e publicação — classificando cada marco como observado (registrado na fonte), derivado (inferido de dados disponíveis) ou futuro/proposto (ainda não representado); ausência de registro não deve ser apresentada como conclusão do marco. | Em que etapa está cada pesquisa, quais marcos foram observados ou derivados e quais informações do seu detalhe estão disponíveis? | Fluxo de trabalho e processos (§4.0.2); datas, status, objetivos e participantes de `pesquisas.csv`, além de `questoes.csv` (§4.0.1); Arquitetura de Negócio [2]. |
| RF03 | Prazos e prioridades | Como gestor ou analista da Central, quero analisar prazos, tempos, atrasos, prorrogações e as prioridades informadas, para ordenar o acompanhamento das pesquisas. | Comparar datas de solicitação, divulgação, limite, prorrogação e entrega e consultar medidas de tempo disponíveis, como dias em aberto e para tabulação; informar marcos ausentes e não classificar atraso, duração ou prorrogação quando faltar data de referência, denominador ou outro dado necessário. A prioridade é uma regra proposta e só deve ser usada quando houver prioridade declarada. | Quais pesquisas estão atrasadas, foram prorrogadas ou demandam prioridade, qual denominador sustenta cada comparação e como os tempos do ciclo se comparam entre elas? | Objetivos (§3); `data_limite`, `prorrogada_ate`, `data_entrega`, `dias úteis aberta`, `dias para tabulação`, `complexidade` e demais campos temporais (§4.0.1); Arquitetura de Negócio [2], JTBD/HMW [13] e Problem Canvas [14]. O dicionário atual não lista campo próprio de prioridade; a regra é proposta. |
| RF04 | Adesão e representatividade | Como analista da Central, quero comparar adesão e participação de empresas com a participação de mercado disponível, para avaliar a representatividade da pesquisa. | Calcular e segmentar adesão por pesquisa e empresa somente quando houver universo convidado, esperado ou outro denominador documentado; exibir numerador e denominador, declarando denominador indisponível quando não existir. Relacionar respondentes, empresas e medidas de mercado somente após conciliação de identidade e distinguir ausência de dado de baixa participação. | A participação alcançada é suficiente e representa as empresas ou parcelas de mercado relevantes, e qual denominador sustenta essa leitura? | Objetivo de ampliar adesão (§3); processo de divulgação, coleta e participação (§4.0.2); `participantes`, `part_mercado`, `market_share`, `empresas.csv` e `respondentes.csv` (§4.0.1); TAPI [1], JTBD/HMW [13] e Problem Canvas [14]. |
| RF05 | Engajamento dos públicos | Como gestor ou analista da Central, quero analisar o engajamento por área, departamento e cargo, para identificar públicos mais ou menos participantes. | Agrupar pesquisas, participações e respostas por área da pesquisa, departamento e cargo do cliente, após conciliação dos identificadores; apresentar contagens e calcular taxas apenas quando houver denominador documentado, declarando-o indisponível quando não houver. | Quais áreas, departamentos e cargos participam mais ou menos, qual é o denominador disponível e onde há oportunidade de ampliar o engajamento? | Objetivo de ampliar adesão (§3); `area` de `pesquisas.csv`, `departamento` e `cargo` de `clientes.csv`, e vínculos de `respondentes.csv` (§4.0.1); JTBD/HMW [13] e Problem Canvas [14]. |
| RF06 | Qualidade e atualização | Como Data Steward ou analista da Central, quero verificar a completude, a validade e a atualização das fontes, para interpretar os indicadores com confiança. | Consultar, por fonte e campo, registros de ausência, inconsistências de identidade, tipos armazenados e data ou estado de atualização disponível, distinguindo ausência condicional de lacuna a investigar e indicando quando a fonte não oferece a informação; o Data Steward acompanha as definições e a qualidade, e o Custodian/TI informa a custódia ou atualização disponível. | Quais dados estão completos e válidos para análise, quais lacunas permanecem e qual é o estado de atualização de cada fonte? | Diagnóstico de qualidade (§5.3), dicionário (§4.0.1), rastreabilidade (§5.4), objetivo de governança e qualidade (§3), DMC [3], JTBD/HMW [13] e Problem Canvas [14]. |
| RF07 | Linhagem agregada ponta a ponta | Como Data Steward ou auditor de dados, quero rastrear a origem de um resultado agregado, para verificar como o dado foi produzido sem presumir uma consulta individual. | Exibir, para cada elo da linhagem agregada fonte → pesquisa → participação → questão → resposta, o sistema ou arquivo de origem, a chave disponível e o estado **observado** (registro/chave encontrado), **em reconciliação** (incompatibilidade ou ausência de correspondência) ou **proposto** (metadado ou vínculo ainda não representado). Quando o sistema de origem não estiver identificado, declarar essa ausência e usar apenas o arquivo recebido. A análise verificou `pesquisa_id` 424, 1116, 1139 e 1147 em `questoes.csv`/`respostas.csv` sem correspondência em `pesquisas.csv`, além de 55 participações em `respondentes.csv` com `id_pesq=304` ausente em `pesquisas.csv`; esses casos permanecem em reconciliação. Não prometer vínculo individual: não há ponte explícita entre `respostas.respondent_id` e `respondentes.id_cliente` nos arquivos recebidos. | Qual fonte e sistema sustentam cada elo do agregado, qual é o estado de cada relação e quais anomalias ou vínculos ainda precisam de conciliação? | Objetivo de rastreabilidade (§3); processos de planejamento, coleta, tabulação e publicação (§4.0.2); chaves de `pesquisas.csv`, `respondentes.csv`, `questoes.csv` e `respostas.csv` (§4.0.1); Arquitetura de Negócio [2], DMC [3], Problem Canvas [14] e dicionário [12]. |
| RF08 | Acesso por perfil | Como Data Owner ou gestor da Central, quero que cada perfil veja apenas os dados permitidos, para proteger informações de empresas e respondentes. | Aplicar a visibilidade definida para perfis internos, áreas técnicas e solicitantes externos, diferenciando dados operacionais, respostas identificáveis e resultados agregados; o Data Owner aprova a regra de acesso e a decisão é registrada quando aplicável. | Que dados cada perfil pode consultar, detalhar ou publicar sem expor informações não autorizadas? | Objetivo de governança, segurança e LGPD (§3); processo de publicação e acervo (§4.0.2); requisito não funcional de segurança (RNF02); TAPI [1], Arquitetura de Negócio [2] e Problem Canvas [14]. |
| RF09 | Publicação autorizada | Como Data Owner ou gestor da Central, quero publicar somente resultados autorizados e acompanhar seu estado de publicação, para manter o acervo público coerente com o processo interno. | Tratar autorização, estado e data de publicação como metadados propostos, dependentes da integração futura com o acervo; o Data Owner aprova a publicação e o Custodian/TI sustenta a disponibilização conforme essa decisão. Disponibilizar no acervo apenas conteúdo explicitamente autorizado e manter o vínculo com a pesquisa de origem. `data_divulgacao` é uma data da pesquisa e não prova autorização ou publicação. | O resultado foi autorizado e publicado, quais metadados sustentam essa decisão e ele está consistente com a pesquisa interna correspondente? | Processo de publicação e acervo (§4.0.2); `data_divulgacao` e status de `pesquisas.csv` (§4.0.1), que não comprovam publicação; objetivo de rastreabilidade (§3); Arquitetura de Negócio [2], DMC [3] e Problem Canvas [14]. |
| RF10 | Resultados agregados | Como analista da Central ou leitor autorizado, quero consultar resultados agregados por pesquisa e questão, para interpretar as respostas sem expor registros individuais. | Apresentar contagens ou distribuições por alternativa, valor e, quando aplicável, linha e coluna de matriz, com recortes por pesquisa e questão; informar o número de respostas válidas e declarar denominador populacional indisponível quando não houver universo de referência, sem inferir uma taxa. | Qual foi a distribuição das respostas para cada questão, qual denominador está disponível e como ela varia entre pesquisas ou segmentos permitidos? | Processo de encerramento, tabulação e análise (§4.0.2); `questoes.csv` e `respostas.csv` (§4.0.1); cubos propostos no DMC [3]; objetivo de apoiar decisões (§3); JTBD/HMW [13] e Problem Canvas [14]. |
| RF11 | Contexto de resposta autorizado | Como auditor de dados ou analista da Central autorizado, quero consultar o contexto disponível de uma resposta agregada, para conferir a interpretação sem expor dados individuais. | Relacionar o agregado à questão, pesquisa e participação somente pelos elos disponíveis; declarar denominador de respostas ou da população indisponível quando não houver base para calculá-lo. Qualquer consulta individual fica limitada a ambiente e perfil autorizados e depende de uma ponte de identidade existente. Nos arquivos recebidos, não há ponte explícita entre `respostas.respondent_id` e `respondentes.id_cliente`; ausência dessa ponte deve ser exibida, não compensada por inferência. | Qual evidência agregada sustenta este resultado, que contexto está disponível e a consulta individual é autorizada e suportada pelos dados? | Rastreabilidade analítica (§5.4); chaves e atributos de `respostas.csv`, `questoes.csv` e `respondentes.csv` (§4.0.1); requisitos de acesso e publicação (RF08 e RF09); DMC [3], Problem Canvas [14] e dicionário [12]. |
| RF12 | Integração e atualização das fontes | Como Data Custodian/TI ou analista da Central, quero acompanhar a integração e a atualização das fontes, para usar dados padronizados, não duplicados e com origem preservada. | Consolidar registros recebidos com padronização de nomes, tipos e domínios; detectar duplicidades e tratar reprocessamentos com idempotência, sem duplicar registros; preservar a origem de cada dado e informar o estado ou a data de atualização disponível. O Custodian/TI acompanha a custódia e a atualização; integrações automáticas entre ferramentas são dependência futura e não são pressupostas neste requisito. | Quais fontes foram recebidas, atualizadas e padronizadas, quais registros foram deduplicados e qual origem sustenta cada dado? | Objetivo de integrar fontes (§3); limitações e melhoria esperada do fluxo (§4.0.2); dicionário (§4.0.1); TAPI [1], Arquitetura de Negócio [2], DMC [3], JTBD/HMW [13] e Problem Canvas [14]. |
| RF13 | Questionário validado e versionado | Como responsável de uma área técnica, quero revisar e versionar o questionário associado à pesquisa, para assegurar que perguntas e validações estejam identificadas antes da divulgação. | Associar a cada versão a pesquisa, área revisora, estado da validação e histórico de alterações quando esses metadados estiverem registrados; classificar a validação como observada ou proposta e não afirmar que uma versão foi validada quando não houver registro. | Qual versão do questionário foi revisada por qual área técnica, em que estado de validação e antes de qual marco do ciclo? | Processo de planejamento e validação (§4.0.2); `questoes.csv` (§4.0.1); capacidade de validação técnica da Arquitetura de Negócio [2]; TAPI [1], JTBD/HMW [13] e Problem Canvas [14]. |

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

Esta seção consolida uma proposta de governança para a arquitetura da Central de Pesquisas. Ela distingue o que foi observado nos artefatos de contexto do que ainda precisa ser decidido e validado pelo Sindusfarma. A presença de um campo em um CSV não prova, por si só, a finalidade, a hipótese legal, a titularidade ou a existência de um controle. A classificação e os controles abaixo devem ser confirmados pelo controlador e pelo encarregado antes de qualquer tratamento em produção.[<sup>\[4\]</sup>](#7-referências)

### 6.6.1 Mapa preliminar de dados e classificação

Os seis arquivos de negócio analisados representam pesquisa, empresa, pessoa/cliente, participação, questionário e elemento de resposta. A identificação das fontes parte do TAPI e da Arquitetura de Negócio, e a organização dos objetos segue o Data Model Canvas.[<sup>\[1\]</sup>](#7-referências)[<sup>\[2\]</sup>](#7-referências)[<sup>\[3\]</sup>](#7-referências) O mapa a seguir registra somente campos e categorias observados nos arquivos locais; não reproduz valores reais nem infere que uma categoria sensível esteja presente hoje.

Para evitar ambiguidade de nomenclatura, `respostas.csv` é o nome canônico usado nesta documentação para o conjunto de respostas; `teste.csv` é o arquivo original recebido fora do repositório de código. A equivalência é considerada apenas no nível de campos e categorias, não como prova de identidade, completude ou autorização para uso em produção.

| Fonte | Campos/categorias observados | Classificação preliminar | Cuidados para o projeto |
| :--- | :--- | :--- | :--- |
| `clientes.csv` | `id_cliente`, `id_empresa`, `cargo`, `departamento`, `e-mail` | Dados pessoais de identificação relacional, contexto profissional e contato | Manter a chave de identidade separada da camada analítica; não publicar e-mail, cargo, departamento ou combinações reidentificáveis. |
| `respondentes.csv` | `id_pesq`, `id_empresa`, `id_cliente`, `hora_inicio`, `hora_termino`, `market_share` | Participação vinculada a pessoa/empresa; horários podem ser pessoais quando associados a um identificador | Restringir o vínculo pessoa–pesquisa; exibir apenas adesão agregada; validar se horários e participação são necessários para cada finalidade. |
| `respostas.csv` | `id_resposta`, `pesquisa_id`, `id_pergunta`, `respondent_id`, `id_empresa`, `alternativa`, `linha_matriz`, `coluna_matriz`, `valor` | Identificadores e respostas de pessoa/empresa; `valor` é categoria aberta a conteúdo pessoal ou sensível conforme o enunciado | Classificar a pergunta e a resposta antes da ingestão; bloquear respostas individuais no repositório público e nos dashboards de gestão. |
| `questoes.csv` | Enunciado, tipo, alternativas, matriz, confiança, formato e observações | Metadados de questionário; podem revelar a finalidade da coleta e elevar o risco quando combinados com respostas | Catalogar finalidade e nível de risco por pergunta; evitar expor enunciados ou observações internas quando permitirem inferência sobre participantes. |
| `empresas.csv` | Identificador, nome, percentual de mercado, nacionalidade, associação, tipo, cidade, estado e país | Dados de organização e indicadores de negócio; podem identificar pessoa natural quando a organização for unipessoal ou quando combinados com outras fontes | Tratar indicadores comerciais como informação restrita; confirmar se a granularidade empresa é necessária em cada painel e se a divulgação foi autorizada. |
| `pesquisas.csv` | Identificador, título, status, tipo, área, participantes, datas, prazos, complexidade, tipo de resposta, objetivos e campos relacionais | Metadados operacionais; `objetivos` e outros campos textuais podem conter ou apontar para dados pessoais | Remover contatos e chaves de ambientes públicos; manter histórico e prazo somente pelo período necessário à finalidade documentada. |

Não foi identificado, apenas pelos nomes dos campos, um campo explicitamente de origem racial ou étnica, convicção religiosa, opinião política, filiação a sindicato ou a organização de caráter religioso, filosófico ou político, saúde, vida sexual, dado genético ou biométrico. Isso não autoriza concluir que dados pessoais sensíveis não existam: o conteúdo de `valor`, `enunciado`, `objetivos` e observações precisa ser amostrado e classificado antes da carga. Se uma resposta revelar qualquer dessas categorias, aplicam-se as hipóteses e salvaguardas próprias do art. 11 da LGPD; não se deve tratá-la como dado comum por estar em uma coluna textual.[<sup>\[4\]</sup>](#7-referências)

### 6.6.2 Papéis, agentes e responsabilidades a validar

Os papéis de governança não equivalem automaticamente aos agentes jurídicos da LGPD. A indicação de Data Owner, Data Steward ou Data Custodian é organizacional; controlador, operador, suboperador e encarregado devem ser definidos pela realidade de cada operação, pelas instruções e pelos contratos. A tabela registra os nomes apontados no material do projeto como referência de validação, não como designação já formalizada; os nomes e atribuições foram confrontados com o TAPI, a Arquitetura de Negócio e o Data Model Canvas.[<sup>\[1\]</sup>](#7-referências)[<sup>\[2\]</sup>](#7-referências)[<sup>\[3\]</sup>](#7-referências)

| Papel de governança | Referência do projeto | Responsabilidade proposta, sujeita a validação |
| :--- | :--- | :--- |
| Data Owner | Fabio Moreira, gestor da Central de Pesquisas | Aprovar finalidades, classificações, acesso por perfil, indicadores e publicação; decidir sobre exceções e risco residual. |
| Data Steward | Felipe Fernandes Rojas, Reinaldo Nobrega e Lucas Andrade | Manter o catálogo e o dicionário, definir significado e regras de qualidade, acompanhar origem, linhagem, minimização e atendimento operacional das solicitações. |
| Data Custodian | Rodrigo Giorgetto/TI e, na custódia externa, RentalHost | Administrar infraestrutura, credenciais, cópias, logs e segregação técnica segundo instruções aprovadas; não decidir finalidade por conta própria. |
| Controlador | A definir pelo Sindusfarma para cada fluxo | Decidir finalidades e meios, validar bases legais, instruir operadores, aprovar compartilhamentos e coordenar respostas e comunicações quando aplicável. |
| Encarregado | A indicar pelo controlador | Atuar como canal entre titulares, controlador e ANPD, receber reclamações e comunicações, orientar as equipes e apoiar o atendimento dos direitos e incidentes. |

Antes da produção, o parceiro deve registrar no inventário, por fluxo: controlador, operador, eventual suboperador, encarregado, finalidade, categorias de titulares e dados, origem, destinos, localização, prazo e mecanismo de descarte. SurveyMonkey, Trello, Excel, Outlook, n8n, hospedagem do site, banco em nuvem e ferramentas de dashboard entram nesse inventário somente se realmente tratarem dados pessoais; os respectivos contratos e instruções devem esclarecer acesso, subcontratação, devolução/eliminação e auditoria.[<sup>\[5\]</sup>](#7-referências)

### 6.6.3 Finalidades e hipóteses legais a confirmar

Consentimento não é uma autorização universal para o projeto. Cada finalidade deve ser específica, informada, necessária e associada a uma hipótese legal adequada; a hipótese escolhida, a forma de informação ao titular e a eventual necessidade de consentimento devem ser confirmadas pelo controlador e pelo encarregado. Quando essa hipótese for escolhida, consentimento significa manifestação livre, informada e inequívoca para finalidade determinada; o controlador deve conservar prova da obtenção, evitar autorizações genéricas e facilitar a revogação por procedimento gratuito. Consentimentos escritos devem estar destacados das demais cláusulas; para dados pessoais sensíveis, a manifestação deve ser específica e destacada para finalidades específicas. A revogação impede a continuidade de novos tratamentos baseados nesse consentimento, resguardados os tratamentos anteriores válidos e as hipóteses de conservação aplicáveis, e exige reavaliar a eliminação quando cabível.[<sup>\[4\]</sup>](#7-referências)

| Finalidade proposta | Dados minimizados | Hipótese a avaliar com o controlador | Evidência/decisão necessária |
| :--- | :--- | :--- | :--- |
| Operar o ciclo da pesquisa, convite, participação e acompanhamento de prazos | IDs de pesquisa/empresa/participação e, somente quando necessário, contato profissional | Execução de contrato ou procedimentos preliminares, obrigação legal/regulatória ou legítimo interesse com teste de necessidade e balanceamento; não presumir uma delas | Identificar a relação jurídica com o participante e documentar a informação fornecida. |
| Receber respostas e produzir indicadores internos | Respostas e chaves pseudonimizadas; retirar contato da camada de métricas | Legítimo interesse documentado, consentimento ou outra hipótese do art. 7º; para dado sensível, hipótese do art. 11 | Registrar finalidade por questionário, risco de reidentificação e regra de acesso. |
| Compartilhar resultado com solicitante, participante ou público | Resultado agregado, com supressão de células pequenas e sem chaves | Hipótese aplicável à divulgação e compatibilidade com a informação prestada; dado efetivamente anonimizado pode não ser dado pessoal, mas a eficácia deve ser avaliada | Aprovação do Data Owner e revisão de reidentificação antes da publicação. |
| Segurança, auditoria, prevenção a fraude e prestação de contas | Identidade de usuário, evento, recurso acessado e carimbo de tempo | Obrigação legal, exercício regular de direitos ou outra hipótese aplicável | Política de acesso, trilha de auditoria, retenção e responsáveis. |
| Atendimento de direitos dos titulares e gestão de incidentes | Dados necessários para localizar o titular, responder e registrar a decisão | Cumprimento de obrigação legal e exercício regular de direitos | Canal, procedimento, autenticação, prazo legal aplicável e registro de encerramento. |
| Uso acadêmico e demonstração do projeto | Dados sintéticos, anonimizados ou agregados; nunca a exportação bruta real | Finalidade acadêmica e hipótese legal a validar; consentimento não substitui a minimização nem autorização de publicação | Separar ambiente acadêmico da operação do parceiro e aprovar o material antes da entrega. |

As hipóteses acima são um roteiro de análise, não um parecer jurídico. A documentação final deve registrar, para cada operação, a finalidade, a base escolhida, a necessidade, a proporcionalidade, a transparência e as salvaguardas. A pesquisa que envolver pessoas identificáveis ou riscos além da vida cotidiana deve ainda ser confrontada com as normas éticas do Conselho Nacional de Saúde, especialmente as Resoluções CNS nº 466/2012 e nº 510/2016, sem presumir que todo levantamento setorial seja automaticamente pesquisa submetida ao CEP/Conep.[<sup>\[10\]</sup>](#7-referências)[<sup>\[11\]</sup>](#7-referências)

O uso acadêmico exige separar três situações: (i) protótipo da sprint, que deve usar dados sintéticos, anonimizados ou agregados; (ii) pesquisa acadêmica ou TCC, cuja finalidade deve ser registrada, com avaliação do orientador e verificação de aplicabilidade da Resolução CNS nº 510/2016 e do fluxo CEP/Conep antes de usar dados identificáveis; e (iii) operação administrativa ou comercial do parceiro, à qual a LGPD se aplica integralmente. O art. 4º, II, “b”, afasta parcialmente a LGPD para tratamento exclusivamente acadêmico, pois preserva a aplicação dos arts. 7º e 11; não afasta esses requisitos nem cobre o uso operacional, administrativo, comercial ou de publicação do parceiro. A decisão sobre o enquadramento, o consentimento e as salvaguardas deve ser registrada com o orientador e o parceiro.[<sup>\[4\]</sup>](#7-referências)[<sup>\[10\]</sup>](#7-referências)

### 6.6.4 Minimização, pseudonimização e divulgação

O princípio operacional é coletar e disponibilizar somente o que for adequado, necessário e proporcional à finalidade registrada. A camada de identificação deve ficar separada da camada analítica, com acesso restrito e vínculo controlado. Recomenda-se que o data warehouse de indicadores não carregue e-mail, cargo, departamento ou qualquer contato quando a métrica puder ser calculada sem esses campos; a chave de ligação deve ser substituída por um identificador pseudonimizado e rotacionável por finalidade.

Pseudonimização e anonimização não são sinônimos. Na pseudonimização, a associação é removida do dado de trabalho, mas pode ser refeita com informação adicional mantida separadamente; o resultado continua sendo dado pessoal e sujeito à LGPD. Na anonimização, a identificação deixa de ser possível considerando meios técnicos razoáveis e disponíveis no contexto, mas a organização deve avaliar risco de reidentificação, sobretudo por combinação de empresa, período, cargo, pergunta e resposta. Um hash sem gestão da chave, uma remoção superficial do nome ou um agrupamento com poucas pessoas não deve ser apresentado como anonimização comprovada.[<sup>\[4\]</sup>](#7-referências)

Para os dashboards e o acervo público, propõem-se as seguintes salvaguardas, ainda sujeitas a teste com dados reais:

- agregar resultados por pesquisa, período ou grupo de empresas, evitando a exposição de respondente, `id_cliente`, `respondent_id`, e-mail e resposta bruta;
- suprimir células com menos de cinco pessoas ou empresas (`k < 5`) e combinações que permitam dedução por diferença; o limiar `k = 5` é uma proposta inicial, não um controle já implantado;
- aplicar o mesmo teste a filtros, exportações, drill-downs e tabelas de baixa frequência, incluindo cargo, departamento, cidade e empresa;
- manter `market_share` e outros indicadores comerciais na menor granularidade compatível com a finalidade, validando se uma publicação por empresa é autorizada;
- bloquear a publicação quando a pergunta, o texto livre ou a combinação de dimensões puder revelar dado pessoal ou sensível, mesmo que os identificadores diretos tenham sido removidos.

### 6.6.5 Acesso, segurança e auditoria

O controle de acesso deve seguir menor privilégio, necessidade de conhecer, segregação entre ambientes e revisão periódica. A matriz abaixo é um desenho de referência; nenhum perfil deve ser considerado existente sem comprovação no ambiente correspondente.

| Perfil proposto | Acesso permitido | Restrições e revisão |
| :--- | :--- | :--- |
| Equipe da Central | Operar pesquisas e indicadores internos conforme a finalidade | Sem acesso automático a contatos ou respostas sensíveis; revisão pelo Data Owner. |
| Áreas técnicas | Questionários, metadados e indicadores necessários à validação | Sem exportação de identidade e sem acesso a outra área sem justificativa registrada. |
| Solicitantes/participantes | Resultado aprovado para sua pesquisa ou grupo | Apenas visão agregada; nenhuma navegação para registros de terceiros. |
| Público do site | Acervo expressamente aprovado e anonimizado/agregado | Sem dados de contato, chaves, respostas individuais ou filtros que desfaçam a agregação. |
| Custódia técnica | Administração necessária para operar a plataforma | Acesso emergencial justificado, temporário e auditado; não usar os dados para finalidade própria. |
| Acadêmico | Artefatos sintéticos, anonimizados ou agregados aprovados | Sem credenciais de produção, cópia dos CSVs reais ou acesso ao mapeamento de identidade. |

Como requisitos de projeto a validar, cada acesso deve ser autenticado individualmente, autorizado por recurso e perfil, protegido por credencial adequada e registrado com usuário, data/hora, operação, recurso e resultado. Logs devem ser protegidos contra alteração, ter retenção própria e permitir investigar leitura, exportação, alteração, exclusão e falha de autorização. Revisões de perfis, revogação de desligados, gestão de segredos, criptografia em trânsito e em repouso, testes de restauração de backup e varredura de repositório devem ser evidenciados antes da entrada em produção. O contexto recebido não comprova que esses controles já estejam implementados.

### 6.6.6 Direitos dos titulares e fluxo de atendimento

O titular deve ter canal de fácil acesso e gratuito para solicitar, conforme aplicável, confirmação de tratamento, acesso, correção, anonimização, bloqueio ou eliminação de dados desnecessários ou tratados em desconformidade, portabilidade, informação sobre compartilhamentos, informação sobre a possibilidade e as consequências de não fornecer consentimento, revogação do consentimento, oposição ao tratamento nas hipóteses e condições do art. 18, § 2º, e petição contra o controlador perante a ANPD. Também pode solicitar revisão de decisão automatizada, quando aplicável. A confirmação e o acesso devem ser fornecidos em formato simplificado imediatamente ou por declaração completa e clara em até 15 dias; os demais pedidos seguem os prazos e procedimentos específicos da LGPD e da regulamentação aplicável, sem que esta seção fixe prazo não confirmado para o caso concreto.[<sup>\[4\]</sup>](#7-referências)[<sup>\[9\]</sup>](#7-referências)

Fluxo mínimo proposto:

0. receber a solicitação no canal do controlador/encarregado e registrar protocolo, data, finalidade e pedido;
0. autenticar o solicitante de forma proporcional, sem exigir novos dados desnecessários;
0. localizar o titular na camada de identidade e mapear cópias, relacionamentos, respostas, exports, dashboards, backups e operadores;
0. classificar o pedido, verificar base legal, direitos de terceiros, segredo comercial e outras restrições documentadas;
0. executar ou justificar a medida (acesso, correção, anonimização, bloqueio, eliminação, informação ou negativa), propagando-a aos operadores quando aplicável;
0. responder em linguagem clara dentro do prazo legal aplicável e manter evidência da decisão, da revisão e do encerramento.

O registro de direitos deve ser uma trilha do atendimento, não um novo repositório de respostas. A equipe não deve apagar evidências necessárias à segurança, à auditoria ou ao exercício regular de direitos sem registrar a justificativa e o prazo de retenção correspondente.

### 6.6.7 Incidentes e RIPD sem duplicação

O procedimento de incidente deve ter um registro operacional único para o fluxo: detecção, contenção, preservação de evidências, avaliação de dados e titulares afetados, decisão do controlador, comunicações, medidas corretivas e encerramento. Um incidente pode envolver CSV local, GitLab, banco, dashboard, site, credencial ou operador; a origem não muda a necessidade de triagem. A comunicação é devida quando os critérios do art. 5º da Resolução CD/ANPD nº 15/2024 estiverem presentes cumulativamente: o incidente puder afetar significativamente interesses e direitos fundamentais e envolver pelo menos uma categoria de dados sensíveis, de crianças/adolescentes/idosos, financeiros, de autenticação, protegidos por sigilo legal/judicial/profissional ou em larga escala. Atendidos esses critérios, o controlador deve comunicar a ANPD e os titulares em três dias úteis contados do conhecimento de que o incidente afetou dados pessoais, salvo prazo específico diferente; se os critérios não se confirmarem, o incidente continua registrado e avaliado. O operador deve informar o controlador sem demora injustificada e fornecer as informações necessárias; contratos devem estabelecer esse fluxo.[<sup>\[6\]</sup>](#7-referências)

O RIPD deve ser tratado como política interna preventiva proposta para avaliar o processo de tratamento: mapa de dados, operações, finalidades, hipóteses legais, necessidade, riscos, salvaguardas, risco residual, responsáveis e decisões. A abertura ou atualização deve ser um gatilho de governança quando houver resposta sensível, novo operador, mudança de finalidade, publicação, exportação, transferência internacional, combinação de bases ou incidente que altere o risco, mas sempre condicionada à avaliação de alto risco e às exigências aplicáveis; não constitui obrigação legal automática para qualquer operação. O registro de incidente referencia a versão do RIPD e as medidas adotadas; não duplica toda a análise de risco nem substitui a comunicação exigida. A ANPD orienta o RIPD quando o tratamento puder gerar alto risco e indica seu conteúdo mínimo, cabendo ao controlador avaliar a necessidade, eventual exigência específica e publicidade no caso concreto.[<sup>\[7\]</sup>](#7-referências)

### 6.6.8 Retenção, descarte e cópias de segurança

Não se propõe um prazo único para todas as tabelas. O critério é manter o mínimo necessário enquanto durar a finalidade, obrigação legal, exercício regular de direitos ou necessidade de prestação de contas; terminada a justificativa, eliminar, anonimizar ou bloquear o dado, observando os requisitos que impeçam a eliminação imediata. Devem ser verificadas as hipóteses de conservação do art. 16 da LGPD, como cumprimento de obrigação legal ou regulatória, estudo por órgão de pesquisa com anonimização sempre que possível, transferência a terceiro respeitados os requisitos legais ou uso exclusivo do controlador com acesso de terceiro vedado.[<sup>\[4\]</sup>](#7-referências)

| Classe | Critério de retenção proposto | Descarte e backup |
| :--- | :--- | :--- |
| Contatos e mapa de identidade | Até cessar a finalidade de convite, atendimento ou vínculo, salvo obrigação documentada | Eliminar da produção e das filas/exports; expirar cópias de segurança conforme a política e registrar a conclusão. |
| Respostas brutas e participação identificável | Pelo período necessário à validação, entrega, contestação e obrigação aplicável | Bloquear acesso após encerramento; eliminar ou anonimizar após revisão do Data Owner e propagação aos operadores. |
| Dados pseudonimizados para indicadores | Enquanto a finalidade analítica existir e o risco for aceitável | Remover a chave de reidentificação quando não for mais necessária; não confundir pseudonimização com descarte. |
| Resultado agregado publicado | Enquanto houver finalidade de transparência/acervo e não houver reidentificação razoável | Manter somente a versão aprovada; corrigir ou retirar publicação incompatível e registrar a decisão. |
| Logs de acesso e auditoria | Pelo período necessário à responsabilização, investigação e obrigações aplicáveis | Proteger contra alteração; definir expiração formal e acesso restrito. |
| Registro de incidente com dados pessoais | No mínimo cinco anos contados da data do registro, inclusive para incidente não comunicado, salvo obrigação adicional que exija prazo maior | Guardar em repositório restrito, com evidências e referência ao processo, sem reter cópias desnecessárias dos dados afetados; essa regra não elimina as hipóteses de conservação do art. 16 da LGPD. |
| Artefatos acadêmicos | Apenas durante a finalidade acadêmica e a guarda exigida pela instituição, se aplicável | Entregar somente versão sintética/anonimizada aprovada e eliminar rascunhos, exports e caches reais. |

Backups devem ter inventário, criptografia, controle de acesso, periodicidade e teste de restauração definidos; a eliminação lógica na base primária não basta se a cópia continuar acessível. O procedimento deve prever expiração automática, destruição segura ou sobrescrita conforme a tecnologia e bloqueio de restauração indevida. Esses são critérios propostos, não evidência de que os backups atuais os atendam.

### 6.6.9 Compartilhamento, operadores e transferência internacional

O compartilhamento deve ser limitado ao mínimo necessário, com finalidade, campos, destinatários, período, instruções e responsabilidade registrados. Para cada fornecedor ou integração, a Central deve decidir se há operador, suboperador ou controlador independente, exigir confidencialidade e segurança, controlar subcontratação, prever apoio a direitos e incidentes, devolução/eliminação ao término e possibilidade de auditoria. O fluxo não deve enviar a um fornecedor o conjunto inteiro de CSVs quando a operação exige apenas um subconjunto.

| Destino | Compartilhamento previsto | Condição de validação |
| :--- | :--- | :--- |
| Equipe Central e áreas técnicas | Metadados e indicadores necessários à operação | Perfil, finalidade, necessidade e trilha de acesso aprovados. |
| Solicitantes, participantes e site | Resultado aprovado, agregado e revisado | Supressão `k < 5`, teste de reidentificação e aprovação para publicação. |
| SurveyMonkey, Trello, Outlook, n8n e outros sistemas | Somente os campos necessários ao fluxo específico | Contrato/instrução, operador e suboperadores identificados, retenção e eliminação verificadas. |
| Banco, dashboard e hospedagem em nuvem | Dados tratados sob custódia técnica | Região de armazenamento, acesso administrativo, cópias, suporte e resposta a incidentes documentados. |
| GitLab e site acadêmico | Código, documentação e dados sintéticos/anonimizados | Bloqueio de bases reais, contatos, chaves e respostas individuais; varredura antes de cada publicação. |

Se um fornecedor, suporte ou infraestrutura permitir acesso a dados pessoais a partir de país estrangeiro ou hospedagem fora do Brasil, há transferência internacional a ser analisada; não se presume sua existência nem sua inexistência. O inventário deve identificar país ou organismo de destino, exportador, importador, finalidade, categorias, duração, operação de acesso/armazenamento, eventuais transferências posteriores e subcontratados. O controlador deve confirmar a hipótese legal e o mecanismo de transferência, registrar as instruções ao importador e exigir salvaguardas, inclusive cláusulas-padrão contratuais da ANPD quando essa for a base escolhida, condições para transferências posteriores, apoio aos direitos, incidentes, término e eliminação. A validação deve observar a LGPD e a Resolução CD/ANPD nº 19/2024.[<sup>\[8\]</sup>](#7-referências)

### 6.6.10 Impacto por ambiente e critérios de liberação

| Ambiente/artefato | Risco principal | Regra de liberação proposta |
| :--- | :--- | :--- |
| CSVs de trabalho e ingestão | Cópias locais, e-mail, exportação ou repositório com contatos e respostas identificáveis | Armazenamento restrito, inventário de cópias, criptografia e eliminação após a carga; nenhum commit de dado real. |
| GitLab e site acadêmico | Compartilhamento público permanente e forks/cache fora do controle da equipe | Somente código, documentação e dados sintéticos/anonimizados; revisão humana e busca por e-mail, IDs e respostas antes do push/publicação. |
| Dashboards internos | Inferência por filtros, células pequenas ou exportações | Perfil, agregação, supressão `k < 5`, bloqueio de drill-down e auditoria de download. |
| Acervo público do site | Divulgação incompatível com a finalidade ou reidentificação por combinação | Publicar apenas resultado aprovado e compatível com a informação aos titulares; manter mecanismo de retirada/correção. |
| Produção do parceiro | Mistura de identidade, respostas e indicadores; acesso administrativo excessivo | Separar ambientes, usar dados reais somente sob decisão documentada do controlador e validar segurança, RIPD, contratos e recuperação antes da operação. |
| Entrega acadêmica | Confusão entre protótipo da sprint e sistema produtivo | Tratar a entrega como ambiente acadêmico independente; não prometer conformidade operacional nem reproduzir controles não verificados. |

Assim, a governança proposta atende ao ciclo completo — coleta, integração, análise, publicação, atendimento e descarte — sem afirmar que os controles já existem. A passagem para produção deve ser condicionada ao fechamento do inventário, à validação das bases legais e papéis, à revisão do RIPD, ao teste de acesso e de reidentificação, à confirmação de retenção/backups e à aprovação da publicação pelo parceiro.

# 7. Referências

[1] INTELI; SINDUSFARMA. **Termo de Abertura de Projeto Inteli (TAPI) — ESMD11: arquitetura e governança de dados alinhada à estratégia corporativa**. São Paulo, 2026. Documento de projeto (arquivo local `context/Tapi-sinduspharma.txt`) disponibilizado pela faculdade e pelo parceiro de projeto.

[2] INTELI; SINDUSFARMA. **Arquitetura de Negócio: Central de Pesquisas do Sindusfarma**. São Paulo, 2026. Documento de projeto (arquivo local `context/Arquitetura-de-Negócio-Central-de-Pesquisas-do-Sindusfarma.txt`) disponibilizado pela faculdade e pelo parceiro de projeto.

[3] INTELI; SINDUSFARMA. **Data Model Canvas: Data Warehouse — Sindusfarma**. São Paulo, 2026. Artefato de documentação (arquivo `Data Model Canvas.pdf`) disponibilizado pela faculdade e pelo parceiro de projeto.

[4] BRASIL. [**Lei nº 13.709, de 14 de agosto de 2018 (Lei Geral de Proteção de Dados Pessoais)**](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm). Brasília, 2018. Acesso em: 12 ago. 2026.

[5] AUTORIDADE NACIONAL DE PROTEÇÃO DE DADOS (ANPD). [**Guia orientativo para definições dos agentes de tratamento de dados pessoais e do encarregado**](https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/2021.05.27GuiaAgentesdeTratamento_Final.pdf). Versão 2.0. Brasília, 2022. Acesso em: 12 ago. 2026.

[6] AUTORIDADE NACIONAL DE PROTEÇÃO DE DADOS (ANPD). [**Comunicação de Incidente de Segurança**](https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/comunicado-de-incidente-de-seguranca-cis). Orientações com base na Resolução CD/ANPD nº 15, de 24 de abril de 2024. Brasília, 2024. Acesso em: 12 ago. 2026.

[7] AUTORIDADE NACIONAL DE PROTEÇÃO DE DADOS (ANPD). [**Relatório de Impacto à Proteção de Dados Pessoais (RIPD)**](https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/relatorio-de-impacto-a-protecao-de-dados-pessoais-ripd). Brasília, 2023. Acesso em: 12 ago. 2026.

[8] AUTORIDADE NACIONAL DE PROTEÇÃO DE DADOS (ANPD). [**Resolução CD/ANPD nº 19, de 23 de agosto de 2024: Regulamento de Transferência Internacional de Dados e cláusulas-padrão contratuais**](https://www.gov.br/anpd/pt-br/acesso-a-informacao/institucional/atos-normativos/regulamentacoes_anpd/resolucao-cd-anpd-no-19-de-23-de-agosto-de-2024). Brasília, 2024. Acesso em: 12 ago. 2026.

[9] AUTORIDADE NACIONAL DE PROTEÇÃO DE DADOS (ANPD). [**Direito dos Titulares**](https://www.gov.br/anpd/pt-br/assuntos/titular-de-dados-1/direito-dos-titulares). Brasília, 2024. Acesso em: 12 ago. 2026.

[10] CONSELHO NACIONAL DE SAÚDE (CNS). [**Resolução nº 510, de 7 de abril de 2016: normas aplicáveis a pesquisas em Ciências Humanas e Sociais**](https://www.gov.br/conselho-nacional-de-saude/pt-br/atos-normativos/resolucoes/2016/resolucao-no-510.pdf/view). Brasília, 2016. Acesso em: 12 ago. 2026.

[11] CONSELHO NACIONAL DE SAÚDE (CNS). [**Resolução nº 466, de 12 de dezembro de 2012: diretrizes e normas regulamentadoras de pesquisas envolvendo seres humanos**](https://www.gov.br/conselho-nacional-de-saude/pt-br/atos-normativos/resolucoes/2012/resolucao-no-466.pdf/view). Brasília, 2012. Acesso em: 12 ago. 2026.

[12] GRUPO G05. **Dicionário de Variáveis — Respostas**. São Paulo, 2026. Arquivo local `Dicionario_Variaveis_Respostas_Grupo6.xlsx - Dicionário.csv`, disponibilizado junto às bases do parceiro.

[13] GRUPO 5. **JTBD a partir do Data Model Canvas — Central de Pesquisas do Sindusfarma**. São Paulo, 2026. Artefato local de levantamento (arquivo `context/JTBD-a-partir-do-Data-Model-Canvas.txt`).

[14] GRUPO 5. **Problem Canvas — Gestão integrada de pesquisas setoriais**. São Paulo, 2026. Artefato local de levantamento (arquivo `context/problem_canvas_sindusfarma_completo (1).html`).

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
