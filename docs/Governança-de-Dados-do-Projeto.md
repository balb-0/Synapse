<Table>
  <tr>
    <td><a href= "link"><img src="img/logo.png" alt="Nome" border="0"></td>
    <td>
      <a href= "https://www.inteli.edu.br/"><img src="img/logo-Inteli.png" alt="Inteli - Instituto de Tecnologia e Liderança" border="0"></a>
    </td>
  </tr>
</table>

# Governança de Dados do Projeto — Central de Pesquisas do Sindusfarma

## Nome do Grupo: Synapse

## Integrantes:

- <a href="https://www.linkedin.com/in/anna-riciopo/">Anna Riciopo</a>
- <a href="https://www.linkedin.com/in/karine-paixao/">Karine Paixão</a>
- <a href="https://www.linkedin.com/in/lucas-nunes-matheus/">Lucas Nunes Matheus</a>
- <a href="https://www.linkedin.com/in/marlos-do-carmo-guedes-366987250/">Marlos Guedes</a>
- <a href="https://www.linkedin.com/in/milena-castro-vieira/">Milena Castro Vieira</a>
- <a href="https://www.linkedin.com/in/otavio-vasc/">Otávio Vasconcelos</a>
- <a href="https://www.linkedin.com/in/vitor-balbo/">Vitor Balbo</a>

# Sumário

- [1. Estrutura Organizacional da Governança](#1-estrutura-organizacional-da-governança)
- [2. Política de Qualidade de Dados](#2-política-de-qualidade-de-dados)
  - [2.1 Atributos de qualidade](#21-atributos-de-qualidade)
  - [2.2 Métricas e procedimentos de mensuração](#22-métricas-e-procedimentos-de-mensuração)
  - [2.3 Metas mínimas e limiares de tolerância](#23-metas-mínimas-e-limiares-de-tolerância)
  - [2.4 Indicadores (KPIs) de qualidade](#24-indicadores-kpis-de-qualidade)
  - [2.5 Fluxo de ações corretivas](#25-fluxo-de-ações-corretivas)
  - [2.6 Regras de validação na ingestão](#26-regras-de-validação-na-ingestão)
  - [2.7 Auditoria e monitoramento contínuo](#27-auditoria-e-monitoramento-contínuo)
  - [2.8 Tratamento de inconformidades e registros duplicados](#28-tratamento-de-inconformidades-e-registros-duplicados)
- [3. Gestão de Metadados e Catálogo](#3-gestão-de-metadados-e-catálogo)
- [4. Classificação e Proteção de Dados](#4-classificação-e-proteção-de-dados)
- [5. Segurança e Acesso](#5-segurança-e-acesso)
- [6. Ciclo de Vida dos Dados](#6-ciclo-de-vida-dos-dados)
- [7. Avaliação de Maturidade](#7-avaliação-de-maturidade)

# 1. Estrutura Organizacional da Governança

_conteúdo_

**Nota:** Papéis da governança de dados (Data Owner, Data Steward, Data Custodian), responsabilidades por metadados, qualidade, segurança e compliance, e o organograma funcional — incluindo o Sindusfarma e custódias externas.

# 2. Política de Qualidade de Dados

A Política de Qualidade de Dados define quais atributos de qualidade são monitorados no acervo de pesquisas e no banco de dados relacional, como cada um é medido, quais metas e indicadores (KPIs) acompanham a saúde do dado, e como a equipe reage quando a qualidade sai do aceitável. As definições partem do diagnóstico realizado na Sprint 1 sobre as bases disponibilizadas (completude e duplicidade medidas por base e variável) e seguem as dimensões de qualidade consagradas no DAMA-DMBOK 2.0.

A seção está organizada da definição à operação: primeiro **o que** se monitora (2.1 atributos), depois **como** se mede (2.2 métricas), **até onde** se aceita (2.3 metas e limiares), **o que se acompanha** no dashboard (2.4 KPIs), e por fim **como se reage e se previne** o desvio (2.5 ações corretivas, 2.6 validação na ingestão, 2.7 auditoria contínua e 2.8 tratamento de inconformidades).

## 2.1 Atributos de qualidade

Atributo de qualidade é a dimensão sob a qual a confiabilidade de um dado é avaliada. O projeto adota cinco atributos, selecionados a partir das dimensões do DAMA-DMBOK 2.0 e priorizados pelo que o diagnóstico da Sprint 1 mostrou ser crítico para o acervo de pesquisas: cada um responde por um tipo distinto de risco sobre os indicadores que a solução vai calcular (adesão, tempos de ciclo, representatividade). Um mesmo registro pode estar completo mas impreciso, ou único mas desatualizado — por isso os atributos são monitorados de forma independente.

<div align="center">
<sub>Tabela X - Atributos de qualidade monitorados no projeto</sub><br>

| Atributo | Definição | Relevância para o acervo de pesquisas | Bases/variáveis mais sensíveis |
| :--- | :--- | :--- | :--- |
| **Acurácia** | O valor registrado corresponde ao fato real que ele representa. | Garante que os indicadores (adesão, tempos, participação) reflitam a realidade das pesquisas, e não erros de digitação ou de conversão de tipo. | Medidas de mercado (`part_mercado`) armazenadas como texto; datas do ciclo em `pesquisas.csv`. |
| **Completude** | Proporção de campos preenchidos onde o preenchimento é exigido. | Campos obrigatórios vazios inviabilizam KPIs; distingue-se ausência **condicional** (estrutural e esperada) de ausência **problemática**. | `data_aprov` (94,5% nula) em `pesquisas.csv`; campos de contato em `clientes.csv`. |
| **Atualidade** | O dado reflete o estado mais recente do processo (defasagem temporal baixa). | Status e datas do ciclo precisam estar atualizados para o acompanhamento operacional em tempo quase real. | Campo de status e marcos de data das pesquisas em andamento. |
| **Consistência** | O mesmo dado é coerente entre as diferentes bases e ao longo do tempo. | Identificadores e domínios precisam bater entre as fontes, senão o cruzamento (drill-across) produz dupla contagem ou órfãos. | `id_cliente` (texto em `clientes.csv`, inteiro em `respondentes.csv`); domínio de país. |
| **Unicidade** | Ausência de duplicidades indevidas de um mesmo registro. | Contagens de empresas, respondentes e respostas só são confiáveis sem duplicatas — base para adesão e representatividade. | Chaves naturais de `empresas.csv`, `clientes.csv` e `respondentes.csv`. |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

**Ausência condicional × problemática.** No atributo de completude, nem todo campo vazio é defeito: há ausências **estruturais** — por exemplo, atributos de matriz que só existem para questões do tipo matriz — que são esperadas e não contam como erro. A política só trata como problemática a ausência em campo obrigatório para o tipo de registro em questão. Essa distinção, levantada no diagnóstico da Sprint 1, evita metas de completude artificialmente pessimistas e é a base para as métricas da seção 2.2.

## 2.2 Métricas e procedimentos de mensuração

Cada atributo definido em 2.1 é traduzido em uma métrica calculável sobre as bases de pesquisas, clientes, empresas, respondentes, questões e respostas. Uma métrica só é útil se tiver **fórmula, unidade e granularidade** explícitas — por isso cada uma é especificada com o denominador de referência (o universo esperado) e o nível em que é apurada (por campo, por base ou por relacionamento entre bases).

<div align="center">
<sub>Tabela X - Métricas de mensuração da qualidade por atributo</sub><br>

| Atributo | Métrica | Fórmula | Unidade | Granularidade |
| :--- | :--- | :--- | :--- | :--- |
| **Completude** | Percentual de completude | `(registros preenchidos ÷ registros esperados) × 100` | % | Por campo obrigatório de cada base |
| **Unicidade** | Taxa de duplicidade | `(registros duplicados ÷ total de registros) × 100` | % | Por base, sobre a chave natural/composta |
| **Consistência** | Taxa de conformidade referencial | `(chaves com correspondência na base de origem ÷ total de chaves) × 100` | % | Por relacionamento (ex.: `respostas`→`empresas`) |
| **Acurácia** | Percentual de valores válidos por regra | `(valores que passam nas regras de negócio ÷ total avaliado) × 100` | % | Por campo com regra definida |
| **Atualidade** | Defasagem temporal | `data de referência − data do último evento registrado` | dias úteis | Por registro em aberto (mediana no dashboard) |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

**Convenção do denominador (registros esperados).** Para a completude, o denominador não é o total de linhas da base, e sim o total de linhas em que o campo é **obrigatório para aquele tipo de registro** — coerente com a distinção condicional × problemática da seção 2.1. Assim, um atributo que só se aplica a questões do tipo matriz não penaliza a métrica das demais.

**Rotina de extração.** As métricas são apuradas sobre a **camada tratada** do pipeline (dados já tipados e padronizados), nunca sobre a camada bruta — que contém chaves órfãs, nulos e tipos inconsistentes que distorceriam a medição. A rotina roda a cada carga (ingestão incremental) e, adicionalmente, em varredura completa programada (ver periodicidade em 2.7), gravando o resultado num histórico de qualidade que alimenta os KPIs da seção 2.4 e serve de trilha de auditoria.

**Exemplo aplicado (linha de base da Sprint 1).** A completude de `data_aprov` em `pesquisas.csv` mediu ~5,5% (94,5% nula); a taxa de duplicidade das seis bases mediu 0%. Esses dois números são a linha de base concreta que calibra as metas da seção 2.3.

## 2.3 Metas mínimas e limiares de tolerância

Uma métrica sem meta não governa nada: é preciso dizer **a partir de qual valor o dado é aceitável** e **em que ponto a equipe é acionada ou a ingestão é barrada**. Esta seção fixa, para cada métrica da 2.2, três referências — a meta mínima (nível desejado), o limiar de alerta (dispara a ação corretiva da seção 2.5) e o limiar de bloqueio (barra a gravação na ingestão, seção 2.6). As metas são **provisórias**: foram calibradas pela linha de base medida na Sprint 1 e serão renegociadas com o parceiro à medida que o histórico de qualidade amadurecer.

<div align="center">
<sub>Tabela X - Metas mínimas e limiares de tolerância por métrica</sub><br>

| Métrica | Meta mínima | Limiar de alerta | Limiar de bloqueio | Justificativa da calibragem |
| :--- | :--- | :--- | :--- | :--- |
| Completude de campo obrigatório | ≥ 95% | < 95% | < 80% em campo crítico | Linha de base heterogênea; campos como `data_aprov` exigem exceção documentada (ver nota). |
| Taxa de duplicidade | 0% | > 0% | > 0% em chave natural | Diagnóstico da Sprint 1 mediu 0% nas seis bases; qualquer duplicata é regressão. |
| Conformidade referencial | ≥ 98% | < 98% | chave órfã em campo obrigatório | Existem chaves órfãs conhecidas (pesquisa_id 424, 1116, 1139, 1147) a reconciliar. |
| Conformidade de domínio | ≥ 98% | < 98% | valor fora de domínio fechado | Categóricos (país, status) devem cair em domínio canônico. |
| Defasagem (atualidade) | dentro do ciclo da pesquisa | acima do ciclo previsto | — | Atualidade gera alerta, não bloqueio: é sinal de processo, não de dado inválido. |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

**Alerta × bloqueio.** O limiar de **alerta** sinaliza degradação e aciona o fluxo de ações corretivas (2.5) sem interromper o pipeline; o limiar de **bloqueio** impede que o registro seja gravado no banco central até correção (2.6). Nem toda métrica tem bloqueio: a atualidade, por exemplo, só gera alerta, porque um dado atrasado ainda é um dado válido — o problema está no processo, não na integridade.

**Exceção documentada (`data_aprov`).** Como a base histórica traz `data_aprov` ~94,5% nula, aplicar a meta de 95% de completude reprovaria praticamente todo o acervo legado. A política adota, para esse campo, uma **meta segmentada**: 95% para pesquisas novas (a partir da adoção do pipeline) e cobertura reportada (não meta) para o legado — todo indicador de tempo de validação derivado dele é publicado **com o número de casos**, para não sugerir precisão inexistente. Toda exceção de meta é registrada no catálogo de metadados (Seção 3).

## 2.4 Indicadores (KPIs) de qualidade

Os KPIs consolidam as métricas (2.2) e suas metas (2.3) em indicadores acompanhados nos dashboards analíticos. Separam-se em **operacionais** — acompanhados a cada carga pela equipe de dados, orientados à ação imediata — e **estratégicos** — agregados por período, voltados à leitura de tendência pela gestão. Cada KPI declara fórmula, meta de referência, forma de apresentação e o público que o consome.

<div align="center">
<sub>Tabela X - KPIs de qualidade de dados</sub><br>

| KPI | Tipo | Fórmula | Meta (ref. 2.3) | Apresentação no dashboard |
| :--- | :--- | :--- | :--- | :--- |
| Taxa de dados ausentes | Operacional | ausentes em campos obrigatórios ÷ total esperado | ≤ 5% | Cartão + série temporal por base |
| Taxa de duplicidade | Operacional | registros duplicados ÷ total | 0% | Cartão com semáforo (verde/vermelho) |
| Índice de consistência entre fontes | Operacional | chaves com correspondência ÷ total de chaves | ≥ 98% | Barra por relacionamento (ex.: `respostas`→`empresas`) |
| Índice de conformidade de domínio | Operacional | valores em domínio válido ÷ total | ≥ 98% | Barra por variável categórica |
| Tempo de defasagem (atualidade) | Operacional | mediana da defasagem dos registros abertos | dentro do ciclo | Cartão + distribuição |
| Índice geral de qualidade (IGQ) | Estratégico | média ponderada dos KPIs operacionais por base | ≥ 95% | Gauge + evolução mensal |
| Cobertura de campos críticos | Estratégico | campos críticos acima da meta ÷ total de campos críticos | ≥ 90% | Heatmap base × atributo |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

**Índice geral de qualidade (IGQ).** É o indicador estratégico de topo: uma média ponderada dos KPIs operacionais, com peso maior para os atributos que travam decisão (consistência e unicidade, que sustentam contagens de adesão e representatividade). Serve para a gestão ler a saúde do acervo num único número, sem precisar interpretar cada métrica isolada — e para comparar a evolução entre sprints e cargas.

**Semântica das cores.** A apresentação segue o código de limiares da 2.3: **verde** acima da meta mínima, **amarelo** entre a meta e o limiar de alerta, **vermelho** abaixo do limiar de alerta (ou em qualquer bloqueio ativo). Assim o dashboard comunica não só o valor, mas se ele já exige ação corretiva (2.5).

**Nota de rastreabilidade.** Cada KPI aqui referenciado é rastreável até uma pergunta de negócio e uma métrica da 2.2; a validação da aplicabilidade desses KPIs contra amostras reais das bases é objeto de verificação específica no plano de testes do projeto.

## 2.5 Fluxo de ações corretivas

Quando um KPI (2.4) cruza um limiar da seção 2.3, dispara-se um **procedimento operacional padrão (POP)** de correção. O fluxo é o mesmo independentemente do atributo violado; o que muda é a **severidade**, que determina prazo e nível de intervenção. O procedimento tem sete passos encadeados, do disparo à reavaliação:

1. **Detecção** — a rotina de mensuração (2.2) identifica a métrica fora do limiar e registra o evento no histórico de qualidade.
2. **Classificação** — o desvio recebe uma severidade (crítica / alta / média / baixa) conforme a tabela abaixo.
3. **Contenção** — nos casos de limiar de bloqueio, o lote é retido e isolado antes de qualquer gravação no banco central.
4. **Correção** — o dado é saneado na origem ou por regra de padronização documentada; nunca por edição manual não rastreada.
5. **Re-ingestão** — o registro corrigido retorna ao início do pipeline e passa novamente pelas regras de validação (2.6).
6. **Reavaliação** — o KPI é recalculado; se voltou à meta, o caso é encerrado no histórico.
7. **Escalonamento** — se o desvio persistir após a correção, o caso sobe ao Data Owner para decisão (aceitar exceção documentada ou acionar a fonte).

<div align="center">
<sub>Tabela X - Fluxo de ações corretivas por severidade</sub><br>

| Severidade | Gatilho (limiar da 2.3) | Ação | Prazo | Responsável (ver Seção 1) |
| :--- | :--- | :--- | :--- | :--- |
| **Crítica** | Duplicidade > 0% ou chave órfã em campo obrigatório | Bloquear ingestão do lote, isolar registros e corrigir na origem | 1 dia útil | Data Steward + Data Custodian |
| **Alta** | Completude de campo obrigatório abaixo do limiar de alerta | Sinalizar, completar na origem e reprocessar | 3 dias úteis | Data Steward |
| **Média** | Conformidade de domínio/referencial abaixo do limiar | Padronizar valores e registrar regra de saneamento | 5 dias úteis | Data Steward |
| **Baixa** | Defasagem de atualidade fora do esperado | Revisar rotina de atualização da fonte | Próximo ciclo | Data Owner |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

**Encerramento e trilha.** Toda ação corretiva — gatilho, severidade, responsável, data e resultado da reavaliação — é gravada no histórico de qualidade, compondo a trilha de auditoria consolidada na seção 2.7. A atribuição nominal/funcional dos responsáveis pelo disparo e pela execução de cada ação é detalhada em documento específico do projeto, e a aderência dos prazos à cadência operacional da Central de Pesquisas é revisada periodicamente para garantir que o fluxo seja executável, e não apenas formal.

## 2.6 Regras de validação na ingestão

_conteúdo_

## 2.7 Auditoria e monitoramento contínuo

_conteúdo_

## 2.8 Tratamento de inconformidades e registros duplicados

_conteúdo_

# 3. Gestão de Metadados e Catálogo

_conteúdo_

**Nota:** Estratégia e ferramentas de catalogação, metadados obrigatórios para tabelas de fato, dimensões e medidas (nome, definição, fonte, periodicidade, sensibilidade, grão), versionamento do catálogo e tabela de exemplo de metadados do DW.

# 4. Classificação e Proteção de Dados

_conteúdo_

**Nota:** Categorias de classificação (público, interno, confidencial, restrito; dado pessoal/sensível/crítico) e a aplicação da LGPD ao tratamento dos dados de empresas e respostas individuais.

# 5. Segurança e Acesso

_conteúdo_

**Nota:** Perfis de acesso (equipe interna, áreas técnicas, solicitantes externos), camadas de proteção, autenticação e práticas técnicas de segurança e auditoria de acesso.

# 6. Ciclo de Vida dos Dados

_conteúdo_

**Nota:** Retenção, arquivamento, descarte e linhagem dos dados ao longo do ciclo de vida das pesquisas.

# 7. Avaliação de Maturidade

_conteúdo_

**Nota:** Diagnóstico do estágio atual de governança, lacunas identificadas e plano de evolução da maturidade.
