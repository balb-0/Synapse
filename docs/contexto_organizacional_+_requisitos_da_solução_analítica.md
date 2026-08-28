# Contexto organizacional e requisitos da solução analítica

## Nome do Projeto

Governança e Integração de Dados da Central de Pesquisas

## Nome do Grupo

Synapse

## Integrantes

- [Anna Riciopo](https://www.linkedin.com/in/anna-riciopo/)
- [Karine Paixão](https://www.linkedin.com/in/karine-paixao/)
- [Lucas Nunes Matheus](https://www.linkedin.com/in/lucas-nunes-matheus/)
- [Marlos Guedes](https://www.linkedin.com/in/marlos-do-carmo-guedes-366987250/)
- [Milena Castro Vieira](https://www.linkedin.com/in/milena-castro-vieira/)
- [Otávio Vasconcelos](https://www.linkedin.com/in/otavio-vasc/)
- [Vitor Balbo](https://www.linkedin.com/in/vitor-balbo/)

Este documento apresenta o contexto organizacional, o alinhamento estratégico,
os requisitos e a especificação analítica da solução proposta para a Central de
Pesquisas do Sindusfarma. Ele é uma síntese autocontida do entregável formal; o
documento [`projeto.md`](projeto.md) mantém a versão detalhada, as evidências,
as limitações e os contratos técnicos complementares.

# 1. Cenário Organizacional e Contexto do Projeto

## 1.1 Visão Geral do Parceiro

<div align="center">
<sub>Tabela 1 - Visão geral do parceiro Sindusfarma</sub><br>

| Item | Síntese |
| :--- | :--- |
| Organização | Sindusfarma — Sindicato da Indústria de Produtos Farmacêuticos no Estado de São Paulo. |
| Setor de atuação | Representação institucional, apoio técnico, regulatório, estratégico e inteligência de mercado para a indústria farmacêutica. |
| Localização geográfica | Atuação vinculada ao Estado de São Paulo, com relevância para empresas do setor farmacêutico no Brasil. |
| Porte / escala operacional considerada no projeto | Entidade setorial relevante; a Central de Pesquisas opera aproximadamente 120 pesquisas por ano, com cerca de 60 empresas envolvidas por pesquisa, conforme TAPI. |
| Principais serviços relacionados ao projeto | Pesquisas setoriais, levantamentos de mercado, coleta de respostas, tabulação, análise, publicação de resultados e apoio à tomada de decisão das empresas participantes. |
| Histórico resumido no escopo do projeto | O Sindusfarma já possui ferramentas consolidadas para partes do processo, como Excel, SurveyMonkey, Trello, sistema interno, automações pontuais e repositório do site. A maturidade atual é operacionalmente funcional, mas fragmentada do ponto de vista de dados. |
| Propósito institucional considerado | Apoiar a indústria farmacêutica com informação técnica, regulatória e estratégica. No projeto, esse propósito é traduzido em uma Central de Pesquisas capaz de produzir conhecimento setorial confiável, rastreável e governado. |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

A área diretamente atendida é a **Central de Pesquisas**, responsável por
transformar necessidades de informação do setor farmacêutico em pesquisas,
questionários, respostas, análises e resultados autorizados.

## 1.2 Contexto do Negócio

A indústria farmacêutica depende de informação confiável para acompanhar
tendências, práticas, adesão, comportamento de mercado e demandas das empresas
associadas. Nesse contexto, a Central de Pesquisas atua como uma frente de
inteligência setorial, coletando e organizando dados que apoiam decisões
operacionais, regulatórias e estratégicas.

O processo atual é rico em dados, mas distribuído entre diferentes ferramentas.
As solicitações, questionários, status, respostas, empresas, participantes,
resultados e publicações não estão ligados por uma camada única de dados. O
TAPI descreve que o único ponto de conexão existente é um fluxo em n8n voltado a
replicar novas solicitações, sem consolidar nem governar todo o ciclo de vida da
pesquisa.

Os principais desafios do negócio são:

- fragmentação das fontes entre planilhas, SurveyMonkey, Trello, sistema
  interno, automações e repositório público;
- atualização manual de dashboards e indicadores;
- baixa rastreabilidade entre solicitação, execução, resultado e publicação;
- risco de inconsistência entre o dado interno e o acervo publicado;
- esforço operacional elevado para cruzar dados e validar indicadores;
- necessidade de tratar dados pessoais, dados de empresas e respostas
  individuais conforme LGPD e regras de confidencialidade.

As oportunidades identificadas são:

- criar uma fonte única da verdade para o ciclo de vida das pesquisas;
- reduzir cruzamentos manuais e retrabalho;
- melhorar qualidade, completude e confiabilidade dos indicadores;
- fortalecer governança, catálogo, metadados e rastreabilidade;
- disponibilizar dashboards internos e resultados externos autorizados com
  regras claras de acesso e publicação;
- evoluir de uma operação baseada em planilhas para uma arquitetura de dados
  centralizada, reutilizável e escalável.

## 1.3 Objetivos do Projeto

<div align="center">
<sub>Tabela 2 - Objetivos do projeto e valor gerado para o parceiro</sub><br>

| Objetivo | Valor gerado para o parceiro |
| :--- | :--- |
| Centralizar os dados do ciclo de vida das pesquisas em um banco relacional em nuvem. | Reduz dispersão de informações e cria base única para acompanhamento, análise e auditoria. |
| Integrar fontes existentes sem substituir as ferramentas operacionais atuais. | Preserva o modo de trabalho já consolidado e reduz ruptura operacional, conectando Excel, SurveyMonkey, Trello, sistema interno e acervo. |
| Automatizar ao menos uma ingestão de dados com tratamento básico de inconsistências e deduplicação. | Diminui atualização manual e cria base para evolução gradual dos pipelines. |
| Disponibilizar dashboards operacionais e estratégicos alimentados pelo banco central. | Permite acompanhar volume, status, prazos, adesão, participação, qualidade e resultados com mais agilidade. |
| Implantar regras de governança, qualidade, segurança e LGPD. | Protege dados pessoais e informações sensíveis de empresas, formalizando responsabilidades e critérios de uso. |
| Garantir rastreabilidade da solicitação à publicação. | Aumenta confiança na origem dos indicadores e reduz divergências entre o ambiente interno e o acervo externo. |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

## 1.4 Escopo do Projeto

### Escopo Incluído

- modelagem de um banco relacional em nuvem para representar solicitação,
  planejamento, execução, resultado e publicação de pesquisas;
- ingestão de pelo menos uma fonte atual, com tratamento básico de
  inconsistências, padronização e deduplicação;
- dashboards com KPIs operacionais e estratégicos;
- regras de qualidade, catálogo, metadados e rastreabilidade;
- controle de acesso por perfil;
- tratamento de dados sensíveis, pessoais e corporativos conforme LGPD;
- proposta de integração com o repositório público do site para resultados
  autorizados.

### Escopo Não Incluído

<div align="center">
<sub>Tabela 3 - Itens fora do escopo do projeto e justificativas</sub><br>

| Item fora do escopo | Justificativa |
| :--- | :--- |
| Substituir SurveyMonkey, Trello, Excel, sistema interno ou repositório público | O projeto integra e governa ferramentas existentes, sem trocar os sistemas operacionais já utilizados. |
| Publicar CSVs brutos, respostas individuais ou dados identificáveis no repositório acadêmico | As bases podem conter e-mails, identificadores e respostas; a entrega pública deve usar apenas agregados, dados sintéticos ou anonimizados. |
| Prometer atualização em tempo real antes de pipeline, logs e SLA homologados | O TAPI registra atualização em tempo real como benefício esperado, mas o snapshot atual não comprova integração contínua. |
| Calcular adesão sem universo elegível de convidados | Sem denominador confiável, o indicador deve aparecer como indisponível, e não como zero ou estimativa. |
| Garantir conformidade produtiva apenas por documentação | Políticas, contratos, perfis e bases legais precisam ser validados e implantados pelo parceiro. |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

# 2. Alinhamento Estratégico

## 2.1 Fluxo de Valor

O fluxo de valor central é **transformar uma necessidade de informação do setor
farmacêutico em conhecimento estruturado e confiável**.

<div align="center">
<sub>Tabela 4 - Fluxo de valor da Central de Pesquisas por etapa</sub><br>

| Etapa | Entrada | Saída de valor | Atores principais | Como a solução contribui |
| :--- | :--- | :--- | :--- | :--- |
| 1. Solicitação | Necessidade, objetivo e contexto | Demanda registrada | Solicitante e Central | Integra a origem da demanda à pesquisa. |
| 2. Triagem e aprovação | Demanda registrada | Pesquisa priorizada ou rejeitada | Central, gestor e área técnica | Preserva decisão, status, prioridade e responsáveis. |
| 3. Planejamento | Pesquisa aprovada | Cronograma e questionário proposto | Central | Liga prazos e perguntas à mesma pesquisa. |
| 4. Validação técnica | Questionário proposto | Instrumento validado | Áreas técnicas e Central | Registra versão, revisão e decisão de validação quando disponível. |
| 5. Divulgação | Pesquisa validada | Convite e prazo comunicados | Central e participantes | Vincula divulgação, prazo e público ao ciclo rastreável. |
| 6. Coleta e monitoramento | Pesquisa divulgada | Participações observadas | Central, empresas e respondentes | Consolida participação sem inventar universo elegível. |
| 7. Registro das respostas | Questionário respondido | Elementos de resposta | Participantes e Central | Preserva relação entre pesquisa, pergunta, resposta e origem. |
| 8. Encerramento e validação | Coleta encerrada | Dados classificados por qualidade | Central e Data Stewards | Aplica regras por tipo de campo e registra anomalias. |
| 9. Tabulação e análise | Dados validados | Indicadores e resultados agregados | Central, áreas técnicas e gestores | Gera métricas com denominador, grão e limitações explícitos. |
| 10. Entrega e publicação | Resultado agregado | Entrega autorizada e acervo consistente | Central, Data Owner, solicitantes e público autorizado | Registra autorização, versão, linhagem e regra de publicação. |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

## 2.2 Análise de Stakeholders

<div align="center">
<sub>Tabela 5 - Análise de stakeholders do projeto</sub><br>

| Stakeholder | Papel na organização | Interesse no projeto | Benefícios esperados | Possíveis preocupações ou resistências |
| :--- | :--- | :--- | :--- | :--- |
| Equipe interna da Central de Pesquisas | Opera o ciclo das pesquisas, acompanha status, prazos, coleta, tabulação, análise e preparação de resultados. | Reduzir cruzamentos manuais, acompanhar pesquisas em um ambiente integrado e aumentar a confiabilidade operacional. | Menos retrabalho, visão única do ciclo, identificação mais rápida de atrasos, pendências e inconsistências. | Receio de aumento de etapas de registro, dependência de novas rotinas e exposição de falhas antes tratadas manualmente. |
| Coordenação / Data Owner | Define prioridades, aprova finalidades, indicadores, perfis de acesso e publicação de resultados. | Ter controle gerencial sobre fluxo, riscos, qualidade, acesso e publicação das pesquisas. | Decisões mais rastreáveis, priorização baseada em evidências e governança mais clara sobre dados e indicadores. | Preocupação com responsabilidade formal sobre decisões de acesso, publicação, exceções e risco residual. |
| Áreas técnicas do Sindusfarma | Validam questionários, acompanham pesquisas relacionadas aos seus temas e interpretam resultados setoriais. | Consultar indicadores confiáveis por pesquisa, área, empresa ou período, com rastreabilidade das fontes. | Melhor acompanhamento de adesão, qualidade e desempenho das pesquisas, além de maior segurança para orientar decisões técnicas. | Resistência a indicadores que revelem baixa adesão, atraso ou limitação de dados; expectativa de respostas mais detalhadas do que o modelo atual comporta. |
| Empresas associadas e participantes | Fornecem respostas por meio de representantes e consomem resultados autorizados. | Ter pesquisas mais úteis, resultados confiáveis e proteção adequada de dados enviados. | Maior transparência sobre resultados agregados, preservação de confidencialidade e redução de solicitações duplicadas. | Preocupação com exposição de participação, respostas individuais, dados de mercado ou comparações que permitam reidentificação. |
| TI / Data Custodian e fornecedores externos | Sustentam infraestrutura, segurança, disponibilidade, integrações, logs, backups e componentes hospedados. | Garantir que a solução seja segura, operável, auditável e compatível com a infraestrutura definida pelo parceiro. | Menor dispersão de dados, melhor controle técnico, trilhas de auditoria e políticas de acesso mais claras. | Risco de aumento de carga operacional, integração com sistemas legados, definição incompleta de responsabilidades e custos de sustentação. |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

## 2.3 Processos Impactados

<div align="center">
<sub>Tabela 6 - Processos impactados pelo projeto e melhorias esperadas</sub><br>

| Processo impactado | Situação atual | Limitações existentes | Melhorias esperadas |
| :--- | :--- | :--- | :--- |
| Solicitação e triagem de pesquisas | Demandas entram por ferramentas e registros distribuídos, com automação pontual em n8n. | A solicitação não se conecta automaticamente a todo o ciclo posterior. | Criar identidade rastreável da pesquisa desde a origem da demanda. |
| Planejamento e validação de questionários | Questionários e revisões são conduzidos fora de um repositório central de versões. | Decisão, versão, área revisora e histórico de alteração não ficam plenamente auditáveis. | Associar questionário, versão, área, estado de validação e marcos da pesquisa. |
| Coleta e monitoramento de participação | SurveyMonkey e planilhas registram respostas e participantes. | Denominadores de convite, participação e resposta podem não estar integrados. | Diferenciar empresa, pessoa, participação e elemento de resposta, preservando limitações de cálculo. |
| Encerramento, tabulação e análise | Indicadores dependem de cruzamentos manuais e validações em planilhas. | Há risco de erro, duplicidade, uso de denominadores inadequados e atraso na atualização. | Automatizar regras de qualidade, métricas e alertas de indisponibilidade. |
| Publicação e acervo externo | Resultados publicados ficam em repositório separado do ambiente interno. | Pode haver divergência entre resultado interno, versão publicada e autorização. | Registrar decisão de publicação, versão, origem, data e perfil autorizado. |
| Governança, segurança e LGPD | Responsabilidades existem em artefatos, mas precisam ser operacionalizadas em política e logs. | Acesso, retenção, descarte e auditoria dependem de decisões formais. | Definir papéis, catálogo, controles de acesso, trilhas de auditoria e retenção. |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

## 2.4 Objetivos Estratégicos Atendidos

<div align="center">
<sub>Tabela 7 - Objetivos estratégicos atendidos pelo projeto</sub><br>

| Objetivo estratégico | Contribuição do projeto |
| :--- | :--- |
| Tornar a Central referência em dados do setor farmacêutico | Organiza histórico, indicadores e resultados autorizados em uma estrutura confiável e governada. |
| Aumentar adesão e engajamento | Permite monitorar participação por pesquisa, empresa, área, cargo ou departamento, quando os denominadores estiverem disponíveis. |
| Reduzir esforço manual e tempo de entrega | Substitui cruzamentos manuais por pipelines, regras de qualidade e dashboards alimentados pelo banco central. |
| Melhorar qualidade e relevância das pesquisas | Usa indicadores de completude, consistência, validade e rastreabilidade para orientar melhorias. |
| Sustentar decisões data-driven | Disponibiliza perguntas, métricas e dashboards com grão, fonte e limitação explícitos. |
| Garantir governança e conformidade | Define papéis, controles, classificação, acesso, retenção e publicação conforme LGPD. |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

# 3. Governança de Dados

## 3.1 Estrutura de Governança

<div align="center">
<sub>Tabela 8 - Estrutura de governança de dados e responsabilidades</sub><br>

| Papel | Responsável / função indicada | Responsabilidades no projeto |
| :--- | :--- | :--- |
| Data Owner | Fabio Moreira, Gestor da Central de Pesquisas, conforme baseline do DMC | Aprovar finalidades, indicadores, acesso, publicação, exceções e risco residual. |
| Data Stewards | Felipe Rojas, Reinaldo Nobrega e Lucas Andrade | Definir significado dos dados, regras de qualidade, catálogo, linhagem, completude e tratamento de inconsistências. |
| Data Custodian | Rodrigo Giorgetto / TI, com apoio de fornecedores como RentalHost quando aplicável | Sustentar infraestrutura, segurança, armazenamento, backups, logs e execução técnica das decisões aprovadas. |
| Controlador / encarregado LGPD | A confirmar pelo Sindusfarma para cada fluxo | Validar bases legais, orientar operadores, coordenar direitos dos titulares e incidentes. |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

As decisões devem seguir a lógica: negócio decide finalidade e exposição,
stewards definem semântica e qualidade, custódia implementa controles técnicos.

## 3.2 Segurança da Informação

Os controles de segurança propostos seguem menor privilégio, necessidade de
conhecer, segregação por ambiente e rastreabilidade. A solução deve prever:

- autenticação de usuários e controle de sessão;
- perfis separados para equipe interna, áreas técnicas, Data Owner, Data
  Steward, Data Custodian, solicitantes e público externo;
- bloqueio de dados identificáveis em dashboards públicos ou acadêmicos;
- logs de consulta, exportação, erro, publicação e tentativa de acesso negado;
- criptografia em trânsito e em repouso no banco e armazenamento;
- backups com retenção definida e teste de recuperação;
- revisão humana antes de qualquer publicação externa.

## 3.3 LGPD e Aspectos Regulatórios

As bases podem conter dados pessoais, contatos, cargos, departamentos,
identificadores de respondentes, dados de empresas e respostas textuais. Por
isso, o projeto deve adotar minimização, finalidade explícita, controle de
acesso e anonimização/agregação antes de publicação externa.

Impactos no projeto:

- respostas individuais não devem ser exibidas em dashboards abertos;
- exportações devem respeitar perfil, finalidade e autorização;
- publicações externas devem usar resultados agregados e aprovados;
- campos de e-mail, identificadores estáveis e textos livres devem ser
  protegidos ou removidos de ambientes públicos;
- solicitações de titulares e incidentes precisam de registro operacional;
- dados reais não devem ser versionados em repositório público.

## 3.4 Qualidade dos Dados

Os principais desafios de qualidade são:

- campos ausentes em variáveis críticas, como datas, objetivos, complexidade,
  participantes e participação de mercado;
- domínios inconsistentes, como variações de maiúsculas/minúsculas;
- identificadores de pesquisa sem correspondência entre fontes;
- ausência de ponte comprovada entre participação e resposta individual;
- baixa cobertura de alguns horários e metadados operacionais;
- campos condicionais em respostas, nos quais vazio pode ser esperado ou
  inconsistente conforme o tipo de pergunta.

Os indicadores de qualidade devem monitorar completude, validade, consistência,
unicidade, integridade referencial e atualidade. Ausências ou limitações devem
ser exibidas como indisponibilidade ou pendência, nunca como zero implícito.

# 4. Especificação dos Requisitos

## 4.1 Requisitos Funcionais

<div align="center">
<sub>Tabela 9 - Requisitos funcionais da solução analítica</sub><br>

| ID | User Story | Critérios de aceitação | Teste de usuário |
| :--- | :--- | :--- | :--- |
| RF01 | Como analista da Central, quero consultar o portfólio de pesquisas para entender volume por período, tipo, área, complexidade e status. | Exibir filtros e totais coerentes; impedir acesso por perfil não autorizado. | Filtrar por ano, área e status e conferir se os totais mudam corretamente. |
| RF02 | Como analista da Central, quero abrir o detalhe de uma pesquisa para acompanhar seus marcos e informações disponíveis. | Mostrar status, datas, fonte e campos pendentes sem preencher ausências artificialmente. | Abrir uma pesquisa com datas completas e outra incompleta e comparar alertas. |
| RF03 | Como gestor da Central, quero identificar atrasos, prorrogações e prioridades para orientar a operação. | Exibir regra, denominador e data de referência usados no cálculo. | Filtrar pesquisas prorrogadas e verificar motivo de atraso ou indisponibilidade. |
| RF04 | Como analista, quero analisar participação e representatividade para avaliar adesão por empresa e pesquisa. | Separar participação observada de taxa de adesão dependente de universo elegível. | Consultar uma pesquisa e verificar numerador, denominador e aviso quando o denominador faltar. |
| RF05 | Como área técnica, quero ver engajamento por cargo, departamento e área para direcionar ações. | Exibir apenas agregados autorizados e proteger dados pessoais. | Filtrar por área e confirmar que e-mail e resposta individual não aparecem. |
| RF06 | Como Data Steward, quero monitorar qualidade e atualização das fontes para decidir se o dado pode alimentar KPIs. | Mostrar completude, duplicidade, validade, órfãos e estado de atualização por fonte. | Abrir painel de qualidade e conferir regra aplicada a um campo crítico. |
| RF07 | Como auditor de dados, quero rastrear origem e linhagem de agregados para não criar vínculos sem evidência. | Exibir fonte, chave, estado observado ou pendente e anomalias conhecidas. | Selecionar um indicador e consultar sua fonte e relação com cubos/dashboards. |
| RF08 | Como Data Owner, quero definir acesso por perfil para proteger dados de empresas e respondentes. | Aplicar matriz de permissões por perfil, dado e operação. | Entrar como perfil externo e confirmar bloqueio de dados internos ou identificáveis. |
| RF09 | Como gestor da Central, quero publicar apenas resultados autorizados para manter consistência com o acervo. | Exigir decisão, versão, data, responsável e regra de agregação antes da publicação. | Tentar publicar resultado sem autorização e verificar bloqueio. |
| RF10 | Como analista, quero consultar resultados agregados de questionários para interpretar respostas por pesquisa. | Preservar grão de elemento de resposta e denominadores por pergunta. | Abrir resultado de questão e verificar `n`, `N` e filtros disponíveis. |
| RF11 | Como usuário autorizado, quero contextualizar respostas por recortes permitidos para analisar padrões sem expor indivíduos. | Bloquear detalhamento individual e sinalizar falta de ponte participação-resposta. | Aplicar recorte por empresa/área e verificar proteção de identidade. |
| RF12 | Como responsável técnico, quero integrar fontes atuais com tratamento de inconsistências para reduzir atualização manual. | Registrar execução, fonte, erro, duplicidade e regra de padronização. | Executar carga de teste e validar logs e resultados agregados. |
| RF13 | Como área técnica, quero versionar questionários validados para preservar histórico antes da divulgação. | Registrar pesquisa, versão, área revisora, estado de validação e alterações quando os metadados existirem. | Criar nova versão de questionário e confirmar que a anterior não foi sobrescrita. |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

## 4.2 Requisitos Não Funcionais

<div align="center">
<sub>Tabela 10 - Requisitos não funcionais por categoria ISO 25010</sub><br>

| ID | Categoria ISO 25010 | User Story | Critérios de aceitação | Teste de usuário |
| :--- | :--- | :--- | :--- | :--- |
| RNF01 | Adequação funcional | Como analista da Central, quero que os dashboards respondam às perguntas de negócio definidas para confiar na utilidade da solução. | Todo dashboard deve estar ligado a pelo menos uma pergunta de negócio e requisito funcional. | Verificar matriz RF-PB-dashboard e confirmar cobertura. |
| RNF02 | Eficiência de desempenho | Como analista, quero consultas rápidas para acompanhar indicadores sem espera excessiva. | Painéis respondem em até 5 s no volume atual de aproximadamente 46 mil registros. | Aplicar filtros de período e área e cronometrar resposta. |
| RNF03 | Compatibilidade | Como responsável técnico, quero que a solução conviva com fontes atuais para preservar ferramentas existentes. | Pipeline aceita dados de CSV/planilhas e prepara integração com SurveyMonkey, Trello e acervo sem substituí-los. | Executar ingestão de fonte de teste e verificar preservação da origem. |
| RNF04 | Usabilidade | Como usuário de área técnica, quero navegar sem treinamento extenso para encontrar indicadores relevantes. | Usuário localiza indicador-chave em até 3 cliques e 2 minutos. | Pedir que usuário encontre taxa de participação ou volume por área. |
| RNF05 | Confiabilidade | Como equipe da Central, quero disponibilidade no horário de trabalho para operar o fluxo. | Indisponibilidades são registradas e comunicadas; meta operacional deve ser validada com o parceiro antes de produção. | Simular falha de consulta e verificar mensagem, log e recuperação. |
| RNF06 | Segurança | Como Data Owner, quero que cada perfil acesse apenas dados permitidos para cumprir LGPD e confidencialidade. | Tentativas não autorizadas são bloqueadas e registradas. | Autenticar com perfil externo e testar acesso a dados internos. |
| RNF07 | Manutenibilidade | Como responsável técnico, quero incluir novas fontes com baixo esforço para evoluir o projeto. | Nova fonte deve ser configurável e versionada sem reescrever o modelo central. | Adicionar fonte de teste e validar carga documentada. |
| RNF08 | Portabilidade | Como TI, quero que a solução possa ser implantada em nuvem equivalente para reduzir dependência de fornecedor. | Banco relacional, scripts e documentação devem evitar recursos proprietários sem justificativa. | Revisar dependências e simular configuração em ambiente equivalente. |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

# 5. Especificação da Solução Analítica

## 5.1 Perguntas de Negócio

<div align="center">
<sub>Tabela 11 - Perguntas de negócio e requisitos relacionados</sub><br>

| ID | Pergunta de negócio | Requisito |
| :--- | :--- | :--- |
| PB01 | Quais pesquisas compõem o portfólio e como se distribuem por período, tipo, área, complexidade e status? | RF01 |
| PB02 | Em que etapa está cada pesquisa e quais marcos estão disponíveis? | RF02 |
| PB03 | Quais pesquisas estão atrasadas, prorrogadas ou demandam prioridade? | RF03 |
| PB04 | A participação alcançada é suficiente e representa empresas ou parcelas de mercado relevantes? | RF04 |
| PB05 | Quais áreas, departamentos e cargos participam mais ou menos? | RF05 |
| PB06 | Quais dados estão completos, válidos, incompletos ou pendentes? | RF06 |
| PB07 | Qual fonte sustenta cada agregado e quais elos estão observados ou pendentes? | RF07 |
| PB08 | Que dados cada perfil pode consultar, detalhar ou publicar? | RF08 |
| PB09 | O resultado foi autorizado e publicado de forma consistente com a pesquisa interna? | RF09 |
| PB10 | Como se distribuem as respostas agregadas por pergunta e pesquisa? | RF10 |
| PB11 | Que recortes de resposta são permitidos sem expor identidade individual? | RF11 |
| PB12 | Quais integrações e cargas estão atualizadas, com erro ou pendentes? | RF12 |
| PB13 | Qual versão do questionário foi validada, por quem e em que estado? | RF13 |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

## 5.2 Indicadores e Métricas de Negócio

<div align="center">
<sub>Tabela 12 - Indicadores e métricas de negócio</sub><br>

| Indicador | Objetivo | Granularidade | Segmentações possíveis |
| :--- | :--- | :--- | :--- |
| Volume de pesquisas | Medir produção e demanda da Central. | Pesquisa por período. | Ano, mês, área, tipo, status e complexidade. |
| Pesquisas em andamento | Acompanhar carteira ativa. | Pesquisa. | Status, prazo, área e responsável. |
| Tempo de ciclo | Medir duração entre solicitação e entrega. | Pesquisa. | Área, tipo, complexidade, período e status. |
| Taxa de prorrogação | Identificar extensão de prazo. | Pesquisa. | Área, tipo, período e complexidade. |
| Participação observada | Medir eventos de participação registrados. | Participação. | Pesquisa, empresa, pessoa, área e período. |
| Representatividade de mercado | Avaliar peso das empresas participantes. | Empresa ou pesquisa. | Nacionalidade, tipo de associado, pesquisa e período. |
| Respondentes únicos | Diferenciar pessoas de linhas de resposta. | Pessoa/participação. | Cargo, departamento, empresa, pesquisa e área. |
| Completude de campos críticos | Monitorar qualidade do dado. | Campo por fonte. | Base, coluna, regra, criticidade e período. |
| Integridade referencial | Identificar chaves órfãs ou não reconciliadas. | Relação entre fontes. | Fonte, entidade, chave e estado. |
| Estado de publicação | Controlar resultado autorizado e publicado. | Resultado/pesquisa. | Perfil, versão, data, responsável e acervo. |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

## 5.3 Dashboards Propostos

Os dashboards são formas de consumo dos mesmos fatos e dimensões da modelagem.
Os relatórios selecionados pelo grupo para produção visual não restringem o
modelo: eles funcionam como recortes de validação. A modelagem deve sustentar os
demais relatórios a partir de fatos reutilizáveis, dimensões conformadas e
regras de acesso.

<div align="center">
<sub>Tabela 13 - Dashboards propostos e cobertura analítica</sub><br>

| Dashboard | Objetivo | Perguntas respondidas | Indicadores | Visualizações e filtros |
| :--- | :--- | :--- | :--- | :--- |
| D01 — Operação: portfólio e prazos | Acompanhar produção, status, ritmo e gargalos da Central. | PB01, PB02, PB03 | Volume, andamento, ciclo, prorrogação e atraso. | Cartões de KPI, barras por mês, distribuição por tipo/área, filtros de período, status, área e tipo. |
| D02 — Adesão e representatividade | Analisar participação por empresa, mercado e público. | PB04, PB05 | Participação observada, respondentes únicos, representatividade e engajamento. | Barras, rankings, tabelas e filtros por pesquisa, empresa, área, cargo e período. |
| D03 — Resultados e questionários | Consultar resultados agregados e estrutura dos questionários. | PB10, PB11, PB13 | Distribuição de respostas, quantidade de perguntas, alternativas e versões. | Barras, matrizes, tabelas de questões e filtros por pesquisa, pergunta, tipo e versão. |
| D04 — Qualidade e governança | Monitorar qualidade, linhagem, atualização, acesso e publicação. | PB06, PB07, PB08, PB09, PB12 | Completude, duplicidade, órfãos, estado de carga, publicação e acesso. | Semáforos, tabelas de anomalias, matriz de regras, filtros por fonte, campo, severidade e estado. |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

# 6. Matriz de Rastreabilidade

<div align="center">
<sub>Tabela 14 - Matriz de rastreabilidade entre requisitos, perguntas e dashboards</sub><br>

| Requisito Funcional | Pergunta de Negócio | Dashboard |
| :--- | :--- | :--- |
| RF01 | PB01 | D01 |
| RF02 | PB02 | D01 |
| RF03 | PB03 | D01 |
| RF04 | PB04 | D02 |
| RF05 | PB05 | D02 |
| RF06 | PB06 | D04 |
| RF07 | PB07 | D04 |
| RF08 | PB08 | D04 |
| RF09 | PB09 | D04 |
| RF10 | PB10 | D03 |
| RF11 | PB11 | D03, D04 |
| RF12 | PB12 | D04 |
| RF13 | PB13 | D03 |

<sup>Material produzido pelos autores (2026)</sup>

</div><br>

# 7. Fontes e Continuidade

As principais fontes internas usadas nesta síntese são:

- TAPI do projeto;
- Arquitetura de Negócio em [`arquitetura-de-negocio.md`](arquitetura-de-negocio.md);
- documentação detalhada em [`projeto.md`](projeto.md);
- Data Model Canvas em [`dmc.json`](dmc.json);
- matriz de evidências em [`matriz-evidencias-problem-canvas.md`](matriz-evidencias-problem-canvas.md);
- modelagem quantitativa em [`modelagem_quantitativa_de_dados_do_parceiro.md`](modelagem_quantitativa_de_dados_do_parceiro.md).

As decisões de implantação, política final de acesso, plataforma de nuvem,
metadados de publicação, logs de atualização e integrações produtivas continuam
dependentes de validação com o Sindusfarma antes de serem tratadas como
capacidade operacional concluída.
