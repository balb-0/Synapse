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
| Operação (D01) | Fluxo mensal do pipeline | C03 | Estoque por status (semiaditiva); entradas e saídas indisponíveis sem histórico de transições | Tempo, status, área, tipo, perfil |
| Participação (D02) | Total de participações observadas | C02 | Contagem de participações (I07) | Pesquisa, tempo, empresa |
| Participação (D02) | Distribuição por empresa (agregada) | C02 | Contagem por empresa | Empresa (sem identificação nominal na tela) |
| Participação (D02) | Engajamento por cargo/departamento | C02 | Contagens agrupadas | Cargo, departamento — **[pendente: reconciliação DR03]** |
| Resultados (D03) | Distribuição por tipo de questão | C04 | Contagem de associações; número de alternativas é atributo da pergunta | Pesquisa, pergunta, tipo de questão |
| Resultados (D03) | Exemplos fechados do protótipo, para uso interno | Protótipo D03; publicação pendente de autorização | — (amostra rotulada) | Sem IDs de pesquisa/questão (limite LGPD) |
| Qualidade (D04) | Matriz de regras de completude/validade | Perfilamento (§5.3) | Numerador/denominador por regra (I16–I20) | Fonte, campo, regra, natureza do nulo |
| Qualidade (D04) | Integridade e órfãos | Perfilamento (§5.3) | Contagens de órfãos e elos em reconciliação | Relação, fonte |

<sup>Material produzido pelos autores (2026), a partir dos contratos C01–C04 (§5.2) e do mapa D01–D04 (§5.7)</sup>

</div><br>

## 2. Relacionamentos do modelo

Estrutura em estrela conforme os contratos: **[contrato]**

- `DIM_TEMPO` é **conformada nos quatro cubos**; em C01 atua por **papéis**
  (uma relação por marco: solicitação, aprovação, divulgação, prazo,
  prorrogação, entrega), com `data_solicitacao` como papel padrão das telas.
- `DIM_PESQUISA` é conformada em C01, C02 e C04; Status, Área, Tipo e Perfil
  são compartilhadas entre C01 e C03.
- Cardinalidade: dimensão (1) → fato (N) em todas as relações; filtro
  propaga da dimensão para o fato, em direção única. Caminhos ambíguos entre
  fatos não permanecem ativos — cruzamento entre fatos só por dimensão
  conformada. **[pendente: DX-05** materializar cardinalidade e direção no
  modelo da ferramenta de BI**]**
- Não existe relação participação ↔ resposta (C02 ↔ C04): a ponte de
  identidade não foi conciliada (DR03) e o modelo não a presume.

## 3. Filtros e hierarquias

- Filtros compartilhados entre telas: período (papel `data_solicitacao` por
  padrão, outros marcos só rotulados), tipo, área, complexidade, status.
  **[contrato; comportamento entre telas pendente: RP-07]**
- Hierarquia de tempo: ano → trimestre → mês (→ dia onde o grão sustentar),
  sem quebrar o total entre níveis. **[pendente: DX-06]**
- Hierarquias de classificação: área → tipo → perfil da pesquisa; e a
  hierarquia de qualidade fonte → campo → regra na D04. **[pendente: DX-06]**

## 4. Medidas personalizadas

Medidas que não são coluna direta dos cubos e precisam ser criadas no modelo
semântico, com a regra estatística correspondente (§ regras DX-03):

<div align="center">
<sub>Tabela 2 - Medidas personalizadas, fórmula e tratamento de nulo</sub><br>

| Medida | Fórmula (contrato) | Nulo/indisponível | Estado |
| :--- | :--- | :--- | :--- |
| Participações observadas | contagem de linhas de C02 (sem afirmar pessoa única) | — | [contrato] |
| % participação por empresa | contagem da empresa ÷ total de participações do recorte | denominador zero → indisponível (nunca 0%) | [pendente: DX-08] |
| Tempo de ciclo entre marcos | diferença entre pares de datas nomeados (RF03) | par incompleto → indisponível (nunca zero dias) | [pendente: DX-07] |
| Estoque mensal do pipeline | último valor do período (semiaditiva — **não** soma entre meses) | mês sem snapshot → indisponível | [pendente: DX-07] |
| Completude por campo | válidos ÷ avaliados, por regra, com ausência permitida separada | regra sem avaliação → indisponível | [pendente: DX-09] |
| Indicador bloqueado | rótulo "indisponível" + motivo textual | nunca exibido como zero | [pendente: DX-10] |

<sup>Material produzido pelos autores (2026), conforme contratos dos cubos e regras estatísticas</sup>

</div><br>

## 5. Rastreabilidade e pendências

- Cada visual analítico da Tabela 1 rastreia a um cubo (C01–C04) ou ao
  perfilamento (§5.3). Os exemplos fechados pertencem somente ao protótipo
  interno; sua publicação depende de autorização específica.
- Pendências abertas nesta seção: DX-05/06 (relacionamentos e hierarquias no
  modelo), DX-07/08/09/10 (medidas), RP-07 (filtros entre telas). Quando
  essas entregas ocorrerem, os marcadores **[pendente]** são resolvidos e
  esta seção passa a afirmar comportamento verificado — a conferência final
  é objeto do [checklist de avaliação](checklist-avaliacao.md).
