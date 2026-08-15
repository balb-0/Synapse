# Gestão do projeto

Este documento registra o acompanhamento sintético da Sprint 1 do projeto
Governança e Integração de Dados da Central de Pesquisas do Sindusfarma.

## Sprint 1

| Eixo | Resultado |
| :--- | :--- |
| Contexto e requisitos | Consolidado em [`projeto.md`](projeto.md) e na entrada formal [`contexto_organizacional_+_requisitos_da_solução_analítica.md`](contexto_organizacional_+_requisitos_da_solução_analítica.md) |
| Modelagem quantitativa | Relatório produzido em [`modelagem_quantitativa_de_dados_do_parceiro.md`](modelagem_quantitativa_de_dados_do_parceiro.md), com cálculos reproduzíveis a partir dos CSVs externos |
| Data Model Canvas | Exportação mantida em [`dmc.json`](dmc.json), com quatro cubos analíticos documentados |
| Rastreabilidade | Contrato PB-RF-indicador-cubo/dashboard validado em [`../scripts/traceability/`](../scripts/traceability/) |
| Protótipos | Dashboards D01-D04 e dados agregados em [`assets/prototipos-dashboards/`](assets/prototipos-dashboards/) |

## Riscos acompanhados

| Risco | Tratamento |
| :--- | :--- |
| Confundir proposta futura com capacidade implementada | Documentação separa observado, derivado, proposto e dependente de integração futura |
| Usar dados pessoais ou identificáveis na entrega | Repositório mantém apenas documentação, agregados e artefatos sem publicação de CSV bruto |
| Inferir vínculos inexistentes entre participação e resposta | O projeto declara a ausência de ponte explícita entre `respondentes` e `respostas` |
| Medir indicadores sem denominador válido | KPIs indicam indisponibilidade quando faltam universo elegível, regra aprovada ou metadado |

## Próximas decisões

- Homologar papéis de governança e política de acesso com o parceiro.
- Definir a plataforma do banco relacional em nuvem e o papel do n8n.
- Priorizar a primeira ingestão do pipeline e seus contratos de qualidade.
- Validar os dashboards com usuários da Central de Pesquisas antes da implementação produtiva.
