# ADR 0007 — Consumo analítico controlado dos cubos

- **Status:** Proposto
- **Data:** 24/09/2026
- **Responsável pela decisão:** equipe de dados e analytics
- **Relaciona-se a:** [Data Model Canvas](../dmc.md)

## Contexto

O Data Model Canvas descreve quatro contratos de cubo (C01–C04), suas medidas,
dimensões, limitações e regras de acesso. Esses cubos ainda não estão
materializados pelo ETL: a entrega implementada termina na ingestão tratada do
DuckDB. Mesmo assim, é necessário fixar a forma de consumo para impedir que
reports futuros consultem arquivos brutos, refaçam regras de negócio ou
exponham respostas individuais.

O acesso precisa preservar o grão de cada cubo, a rastreabilidade até a fonte,
as restrições de denominador e cobertura e a separação entre detalhe interno e
agregado publicável.

## Alternativas consideradas

| Alternativa | Avaliação |
| :--- | :--- |
| Reports consultarem diretamente CSVs ou tabelas da ingestão tratada | Rejeitada: transfere reconciliação e regra de negócio para cada consumidor, favorece resultados divergentes e pode expor detalhe indevido. |
| Exportar planilhas independentes para cada report | Rejeitada como padrão: multiplica cópias, perde atualização e linhagem central e dificulta revogação de acesso. Exportação pontual continua possível quando autorizada e auditada. |
| Expor uma API de indicadores como única interface | Adiada: acrescenta serviço e operação antes de os contratos dimensionais serem materializados e homologados. |
| Consumir fatos, dimensões e agregados governados por meio de views de leitura | Selecionada: mantém grão, medida, filtro e política de publicação próximos ao modelo analítico. |

## Decisão

Os reports e painéis devem consumir **views de leitura governadas sobre os
cubos materializados**, nunca arquivos brutos ou tabelas internas do ETL. Cada
view deve:

- identificar o cubo, grão, medidas e dimensões de origem;
- aplicar apenas métricas homologadas no contrato dimensional;
- conservar chaves e metadados suficientes para auditoria e linhagem;
- representar indisponibilidade como `NULL`, estado explícito ou mensagem de
  dado indisponível, sem fabricar denominador, histórico ou vínculo;
- separar o perfil interno detalhado do perfil publicável agregado;
- registrar versão do contrato e instante de atualização.

O acesso será somente leitura e concedido por perfil. A camada interna atende a
Central de Pesquisas e responsáveis técnicos nos recortes autorizados. A
camada publicável aplica as regras de anonimização, agregação mínima e revisão
definidas na governança. O C04 não habilita análise por pessoa ou segmento
enquanto a ponte entre respostas e participantes não for comprovada.

Os quatro cubos continuam sendo contratos propostos. A materialização deve ser
homologada antes de qualquer report ser classificado como disponível.

## Justificativa

Views governadas criam uma fronteira clara entre processamento e apresentação,
evitam que cada report implemente sua própria versão das medidas e permitem
alterar a persistência física sem quebrar o contrato de consumo. A separação de
perfis mantém o princípio do menor privilégio e reduz o risco de publicação de
dado pessoal ou de agregado com baixa cardinalidade.

## Consequências

### Positivas

- métricas e limitações ficam consistentes entre reports;
- o acesso pode ser concedido e auditado por perfil;
- a linhagem de cada visual permanece ligada ao cubo e à medida homologada;
- indicadores sem evidência continuam indisponíveis de forma explícita.

### Negativas e riscos

- mudanças de grão ou medida exigem versionamento coordenado das views;
- a camada publicável demanda testes de privacidade e cardinalidade;
- consumidores exploratórios não acessam livremente o detalhe fora do perfil
  autorizado;
- views não substituem catálogo, monitoramento de atualização ou homologação.

## Limite de implantação

Esta ADR define o contrato de acesso futuro. Ela **não materializa cubos, não
cria usuários, não publica reports e não automatiza entrega em produção**. No
ambiente local/versionado, contratos e exemplos podem ser validados com dados
controlados. Uma implantação produtiva requer plataforma de consumo escolhida,
identidade corporativa, permissões, auditoria, retenção e aprovação dos donos
dos dados.
