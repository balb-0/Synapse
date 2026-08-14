# Matriz de evidências do Problem Canvas

Esta matriz conecta os elementos atribuídos ao Problem Canvas aos artefatos da
Sprint 1 sem tratar uma referência indireta como confirmação do parceiro. O
arquivo primário do canvas não está neste checkout; por isso, elementos que
dependem exclusivamente dele permanecem **pendentes de validação**, com a
auditoria da fonte primária registrada na evidência.

| Elemento | Evidência disponível | Fonte | Status | Artefato de destino |
| :--- | :--- | :--- | :--- | :--- |
| Dor: fontes e etapas fragmentadas | o TAPI confirma ferramentas consolidadas por etapa, ausência de integração estruturada, dashboard manual e cruzamentos em planilhas | TAPI [1], Arquitetura [2] e §4.0.2 | Confirmado pelo parceiro | contexto, escopo e fluxo de valor |
| Evidência de rastreabilidade limitada | há relações órfãs e não existe ponte comprovada entre o registro de participação de `respondentes.csv` e o elemento atômico de `respostas.csv` | snapshot externo identificado pelos hashes da §5.3.6; §§5.3.2 e 5.4 | Observado nos dados | requisitos RF07/RF12, I18/I22 e C04 |
| Dor: baixa rastreabilidade ponta a ponta | as relações órfãs e a ausência de ponte permitem inferir dificuldade para seguir a cadeia completa | síntese das §§5.3.2 e 5.4 | Inferência | contexto e fluxo de valor |
| Evidência: identificadores incompatíveis | domínios de pesquisa não coincidem integralmente e `respondent_id` não possui ponte comprovada com o registro de participação | snapshot externo identificado pelos hashes da §5.3.6; §§5.3.2 e 5.4 | Observado nos dados | reconciliação, C02–C04 e D04 |
| Causa possível: sistemas de origem distintos | a incompatibilidade é compatível com múltiplos sistemas, mas a origem não é comprovada pelos CSVs | §5.3.2 | Inferência | contexto e arquitetura de integração |
| Evidência de qualidade e metadados incompletos | há campos ausentes, percentuais textuais e timezone não informado | snapshot externo e perfilador; §§5.3.1–5.3.4 | Observado nos dados | RF06, I16–I20 e C04 |
| Impacto: esforço manual e demora | o esforço manual e a dependência de atualização/tabulação manual são confirmados, mas tempo, custo e retrabalho não foram medidos nesta Sprint | TAPI [1], Arquitetura [2] e §4.0.2 | Confirmado pelo parceiro; magnitude pendente | objetivos, escopo e fluxo de valor |
| Impacto: indicador indisponível, ambíguo ou sujeito a interpretação incorreta | a ausência de universo impede adesão; fontes de mercado divergem; elemento atômico de resposta não equivale a pessoa | §§5.3, 5.6 e 6.4 | Inferência | I08–I11 e regras dos dashboards |
| Necessidade: centralizar informações | o TAPI exige banco central em nuvem e fonte única; isso confirma o objetivo, não sua implantação | TAPI [1], Arquitetura [2] e §3 | Confirmado pelo parceiro; implementação pendente | escopo TO-BE, RF12 e DMC |
| Necessidade: integrar o ciclo da pesquisa | TAPI e Arquitetura conectam solicitação, questionário, participação, resposta, análise e publicação | TAPI [1], Arquitetura [2], §§4.0.2, 5.2 e 6.1 | Confirmado pelo parceiro; implementação pendente | fluxo TO-BE e C01–C04 |
| Necessidade: governar acesso e publicação | política final e logs não estão comprovados nas fontes analisadas | §§6.4–6.6 | Pendente de validação | RF08/RF09, I23/I25 e Governança Corporativa |
| Objetivo: rastreabilidade da solicitação à publicação | o TAPI confirma rastreabilidade e auditabilidade ponta a ponta como benefício esperado; PB02/PB07/PB09/PB11/PB12 operacionalizam a necessidade | TAPI [1], Arquitetura [2], §§3, 5.4 e 6.3 | Confirmado pelo parceiro; implementação pendente | RF02/RF07/RF09/RF12, C01/C04 |
| Objetivo: reduzir esforço manual | TAPI e Arquitetura confirmam o objetivo, mas não fornecem baseline de horas, custo ou retrabalho | TAPI [1], Arquitetura [2] e §3 | Confirmado pelo parceiro; medição pendente | avaliação futura; não apresentar ganho nesta Sprint |
| Perguntas de negócio | PB01–PB13 são contratos derivados que cobrem necessidades confirmadas de portfólio, ciclo, participação, qualidade, acesso, publicação e resultados | TAPI [1], Arquitetura [2] e §6.3 | Proposta da equipe sustentada por fonte primária | indicadores, dashboards e cubos |
| KPIs de portfólio e ciclo disponíveis | I01–I05 têm campos observáveis | CSVs; §§5.6 e 6.4 | Observado nos dados | C01 e D01 |
| KPI de atraso e prioridade | I06 depende de regra e data de referência aprovadas | §§5.6 e 6.4 | Pendente de validação | C01 e D01 |
| KPI de participação observada | I07 conta participações sem afirmar adesão | `respondentes.csv`; §§5.6 e 6.4 | Observado nos dados | C02 e D02 |
| KPIs de adesão, mercado e engajamento | I08 e I11 não têm denominador; I09/I10 exigem reconciliação | CSVs; §§5.6 e 6.4 | Pendente de validação | C02 e D02 |
| KPIs de resultados disponíveis | I12–I14 usam resposta atômica; C04 cobre o instrumento de questionário, enquanto a resposta conciliada permanece extensão futura | CSVs; §§5.4, 5.6 e 6.4 | Observado nos dados; modelagem dimensional parcial | C04; D03 |
| KPI de questionário validado | I15 depende de metadados de versão e validação e do cubo próprio ainda não definido | Arquitetura [2]; §§5.4, 5.6 e 6.4 | Pendente de integração e modelagem | cubo de resultados pendente; D03 |
| KPIs de qualidade disponíveis | I16–I20 são derivados do perfilamento | perfilador; §§5.3–5.6 e 6.4 | Observado nos dados | C04 e D04 |
| KPIs de atualização, publicação e acesso | I21 e I23–I25 exigem logs e decisões futuras | §§5.6 e 6.4 | Pendente de validação | C04 e D04 |
| Público: Central de Pesquisas | o TAPI define a equipe interna como usuária principal para operar o fluxo e acompanhar indicadores | TAPI [1], Arquitetura [2], D01, D02 e D04; §6.5 | Confirmado pelo parceiro | Consumo Analítico |
| Públicos: áreas técnicas e gestores | o TAPI confirma áreas técnicas; a Arquitetura confirma gestores como consumidores consolidados; permissões finais ainda precisam de aprovação | TAPI [1], Arquitetura [2], §§6.5 e 6.6 | Confirmado pelo parceiro; acesso pendente | Consumo Analítico e controle de acesso |
| Público externo | o TAPI confirma solicitantes e participantes como público terciário do acervo; conteúdo continua condicionado a autorização | TAPI [1], Arquitetura [2], RF09 e §§6.5–6.6 | Confirmado pelo parceiro; controle pendente | D03, publicação e acervo |
| Governança: Owner, Steward e Custodian | a Arquitetura registra nomes e responsabilidades; a política final e a designação operacional ainda precisam de validação | Arquitetura [2], DMC [3], `dmc.json` e §6.6.2 | Confirmado documentalmente; formalização pendente | Governança Corporativa |
| Risco: exposição ou reidentificação | o snapshot externo possui e-mail, chaves estáveis e textos livres | estrutura observada e §6.6 | Observado nos dados | minimização, agregação e controle de acesso |
| Risco: “tempo real” sem fonte operacional | o TAPI registra “tempo real” como benefício esperado, mas o snapshot não contém timestamp de carga nem comprova integração contínua | TAPI [1], §§5.3.6, 5.6 e 6.5 | Objetivo confirmado; capacidade pendente | não apresentar atualização automática como resultado atual |

## Regras de uso

0. Uma linha com dois estados deve ser desdobrada no indicador específico antes de implementação.
0. Valores demonstrativos dos protótipos não substituem métricas homologadas.
0. Empresa, cliente/pessoa, participação e elemento de resposta são conceitos distintos.
0. Uma proposta só passa a “confirmada pelo parceiro” quando a fonte primária ou decisão registrada puder ser auditada.
