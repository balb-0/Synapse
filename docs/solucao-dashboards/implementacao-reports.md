# Documento da solução — implementação dos reports a partir dos cubos

Seção do documento da solução que descreve **como cada visualização dos
reports nasce dos cubos analíticos** C01–C04 (contratos da §5.2 do
[`projeto.md`](../projeto.md)): cubo de origem, medidas, dimensões, filtros,
relacionamentos, hierarquias e medidas personalizadas. Convenção de estado,
mantida em todo o documento: **[contrato]** = definido nos cubos/modelo e
válido para implementação; **[pendente: DX/RP]** = depende da entrega do
modelo semântico (DX) ou da construção das telas (RP) para virar
comportamento verificável. Nada marcado pendente é apresentado como entregue.

## 1. Visualizações por tela e cubo de origem

<div align="center">
<sub>Tabela 1 - Tela, visual, cubo de origem, medidas e dimensões</sub><br>

| Tela | Visual | Cubo | Medidas | Dimensões de corte |
| :--- | :--- | :--- | :--- | :--- |
| Operação (D01) | Cartões de portfólio (total, por status) | C01 | Contagem de pesquisas (I01) | Status, tipo, área, complexidade |
| Operação (D01) | Evolução temporal de solicitações | C01 | Contagem por período (I02) | Tempo (papel: `data_solicitacao`) |
| Operação (D01) | Marcos e prorrogações | C01 | Contagem de prorrogações (I05); tempos entre marcos (I03–I04) | Papéis de tempo por marco, status |
| Operação (D01) | Fluxo mensal do pipeline | C03 | Estoque por status (semiaditiva), entradas e saídas do mês | Tempo, status, área, tipo, perfil |
| Participação (D02) | Total de participações observadas | C02 | Contagem de participações (I07) | Pesquisa, tempo, empresa |
| Participação (D02) | Distribuição por empresa (agregada) | C02 | Contagem por empresa | Empresa (sem identificação nominal na tela) |
| Participação (D02) | Engajamento por cargo/departamento | C02 | Contagens agrupadas | Cargo, departamento — **[pendente: reconciliação DR03]** |
| Resultados (D03) | Distribuição por tipo de questão | C04 | Quantidade de perguntas, de alternativas | Pesquisa, pergunta, tipo de questão |
| Resultados (D03) | Exemplos fechados autorizados | C04 | — (amostra rotulada) | Sem IDs de pesquisa/questão (limite LGPD) |
| Qualidade (D04) | Matriz de regras de completude/validade | Perfilamento (§5.3) | Numerador/denominador por regra (I16–I20) | Fonte, campo, regra, natureza do nulo |
| Qualidade (D04) | Integridade e órfãos | Perfilamento (§5.3) | Contagens de órfãos e elos em reconciliação | Relação, fonte |

<sup>Material produzido pelos autores (2026), a partir dos contratos C01–C04 (§5.2) e do mapa D01–D04 (§5.7)</sup>

</div><br>

