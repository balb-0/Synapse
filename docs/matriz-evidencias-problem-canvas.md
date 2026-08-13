# Matriz de evidências do Problem Canvas

Esta matriz conecta os elementos atribuídos ao Problem Canvas aos artefatos da
Sprint 1 sem tratar uma referência indireta como confirmação do parceiro. O
arquivo primário do canvas não está neste checkout; por isso, elementos que
dependem exclusivamente dele permanecem **pendentes de validação**, com a
auditoria da fonte primária registrada na evidência.

| Elemento | Evidência disponível | Fonte | Status | Artefato de destino |
| :--- | :--- | :--- | :--- | :--- |
| Dor: fontes e etapas fragmentadas | o documento consolidado descreve ferramentas independentes e cruzamentos manuais; falta auditar os originais | Problem Canvas [14] e Arquitetura [2], citados; síntese na §4.0.2 | Pendente de validação | contexto, escopo e fluxo de valor |
| Evidência de rastreabilidade limitada | há relações órfãs e não existe ponte comprovada entre o registro de participação de `respondentes.csv` e o elemento atômico de `respostas.csv` | snapshot externo identificado pelos hashes da §5.3.6; §§5.3.2 e 5.4 | Observado nos dados | requisitos RF07/RF12, I18/I22 e C04 |
| Dor: baixa rastreabilidade ponta a ponta | as relações órfãs e a ausência de ponte permitem inferir dificuldade para seguir a cadeia completa | síntese das §§5.3.2 e 5.4 | Inferência | contexto e fluxo de valor |
| Evidência: identificadores incompatíveis | domínios de pesquisa não coincidem integralmente e `respondent_id` não possui ponte comprovada com o registro de participação | snapshot externo identificado pelos hashes da §5.3.6; §§5.3.2 e 5.4 | Observado nos dados | reconciliação, C02–C04 e D04 |
| Causa possível: sistemas de origem distintos | a incompatibilidade é compatível com múltiplos sistemas, mas a origem não é comprovada pelos CSVs | §5.3.2 | Inferência | contexto e arquitetura de integração |
| Evidência de qualidade e metadados incompletos | há campos ausentes, percentuais textuais e timezone não informado | snapshot externo e perfilador; §§5.3.1–5.3.4 | Observado nos dados | RF06, I16–I20 e C04 |
| Impacto: esforço manual e demora | aparece na síntese do processo atual, sem medição de tempo ou custo nesta sprint; falta auditar os originais | TAPI [1], Arquitetura [2] e §4.0.2 | Pendente de validação | objetivos, escopo e fluxo de valor |
| Impacto: indicador indisponível, ambíguo ou sujeito a interpretação incorreta | a ausência de universo impede adesão; fontes de mercado divergem; elemento atômico de resposta não equivale a pessoa | §§5.3, 5.6 e 6.4 | Inferência | I08–I11 e regras dos dashboards |
| Necessidade: centralizar informações | resultado pretendido registrado nos objetivos, não capacidade implantada | referências [1], [2], [13], [14]; §3 | Proposta da equipe | escopo TO-BE, RF12 e DMC |
| Necessidade: integrar o ciclo da pesquisa | contratos conectam solicitação, questionário, participação, resultado e publicação | §§4.0.2, 5.2 e 6.1 | Proposta da equipe | fluxo TO-BE e C01–C04 |
| Necessidade: governar acesso e publicação | política final e logs não estão comprovados nas fontes analisadas | §§6.4–6.6 | Pendente de validação | RF08/RF09, I23/I25 e Governança Corporativa |
| Objetivo: rastreabilidade da solicitação à publicação | síntese derivada: objetivo e perguntas PB02/PB07/PB09/PB11/PB12 formalizam a cadeia; falta auditar as fontes primárias | §§3, 5.4 e 6.3 | Inferência | RF02/RF07/RF09/RF12, C01/C03/C04 |
| Objetivo: reduzir esforço manual | não existe baseline medido de horas, custo ou retrabalho | §3 e referências primárias citadas | Pendente de validação | avaliação futura; não apresentar ganho nesta sprint |
| Perguntas de negócio | síntese derivada: PB01–PB13 cobrem portfólio, ciclo, participação, qualidade, acesso, publicação e resultados; falta auditar as fontes primárias | §6.3 | Inferência | indicadores, dashboards e cubos |
| KPIs de portfólio e ciclo disponíveis | I01–I05 têm campos observáveis | CSVs; §§5.6 e 6.4 | Observado nos dados | C01 e D01 |
| KPI de atraso e prioridade | I06 depende de regra e data de referência aprovadas | §§5.6 e 6.4 | Pendente de validação | C01 e D01 |
| KPI de participação observada | I07 conta participações sem afirmar adesão | `respondentes.csv`; §§5.6 e 6.4 | Observado nos dados | C02 e D02 |
| KPIs de adesão, mercado e engajamento | I08 e I11 não têm denominador; I09/I10 exigem reconciliação | CSVs; §§5.6 e 6.4 | Pendente de validação | C02 e D02 |
| KPIs de resultados disponíveis | I12–I14 usam resposta atômica | CSVs; §§5.6 e 6.4 | Observado nos dados | C03 e D03 |
| KPI de questionário validado | I15 depende de metadados de versão e validação | §§5.6 e 6.4 | Pendente de validação | C03 e D03 |
| KPIs de qualidade disponíveis | I16–I20 são derivados do perfilamento | perfilador; §§5.3–5.6 e 6.4 | Observado nos dados | C04 e D04 |
| KPIs de atualização, publicação e acesso | I21 e I23–I25 exigem logs e decisões futuras | §§5.6 e 6.4 | Pendente de validação | C04 e D04 |
| Público: Central de Pesquisas | uso operacional recorrente de portfólio, prazos, participação e qualidade | D01, D02 e D04; §6.5 | Proposta da equipe | Consumo Analítico |
| Públicos: áreas técnicas e gestores | validação, acompanhamento e decisão consolidada são descritos, mas perfis finais não foram aprovados | §§6.5 e 6.6 | Proposta da equipe | Consumo Analítico e controle de acesso |
| Público externo | somente conteúdo autorizado e agregado pode chegar ao acervo | RF09 e §§6.5–6.6 | Proposta da equipe | D03, publicação e acervo |
| Governança: Owner, Steward e Custodian | nomes aparecem no baseline do DMC, mas não comprovam designação formal | DMC [3], `dmc.json` e §6.6.2 | Pendente de validação | Governança Corporativa |
| Risco: exposição ou reidentificação | o snapshot externo possui e-mail, chaves estáveis e textos livres | estrutura observada e §6.6 | Observado nos dados | minimização, agregação e controle de acesso |
| Risco: “tempo real” sem fonte operacional | timestamp de carga e integração contínua não estão presentes nas fontes analisadas | §§5.3.6, 5.6 e 6.5 | Observado nos dados | tratar atualização automática como proposta |

## Regras de uso

0. Uma linha com dois estados deve ser desdobrada no indicador específico antes de implementação.
0. Valores demonstrativos dos protótipos não substituem métricas homologadas.
0. Empresa, cliente/pessoa, participação e elemento de resposta são conceitos distintos.
0. Uma proposta só passa a “confirmada pelo parceiro” quando a fonte primária ou decisão registrada puder ser auditada.
