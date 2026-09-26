# Limitações encontradas — análise crítica e propostas

Registro das limitações que afetam o uso da solução de dashboards, no formato
exigido: **impacto** (no usuário/decisão), **causa observada** (com a
evidência que a sustenta) e **proposta de solução**. Toda proposta está
marcada como **proposta** — nenhuma é decisão tomada. Cada limitação aponta a
decisão aberta (DR01–DR06, §5.1 do [`projeto.md`](../projeto.md)) ou a tarefa
de usabilidade que a evidencia; as limitações vindas das sessões de execução
(US-06/US-07) serão acrescentadas na seção 2 quando as rodadas ocorrerem.

## 1. Limitações estruturais observadas no planejamento

### L01 — Taxas sem denominador documentado

- **Impacto:** o usuário espera "taxa de adesão" e a solução só pode exibir
  contagens; taxa apresentada sem denominador induziria decisão errada sobre
  representatividade.
- **Causa observada:** não há universo de empresas/pessoas convidadas nas
  fontes (DR01); I08 e I11 marcados indisponíveis na §5.6.
- **Proposta (não decidida):** acordar com o parceiro o registro do universo
  convidado por pesquisa; até lá, telas mantêm o rótulo "participação
  observada" e o estado "denominador indisponível" — comportamento cuja
  compreensão é testada em T-DET-02.

### L02 — Participação e resposta sem ponte de identidade

- **Impacto:** não é possível responder "quantas pessoas únicas responderam"
  nem detalhar do agregado de respostas para o respondente; soma ingênua de
  linhas superestima pessoas.
- **Causa observada:** 542 `respondent_id` distintos em `respostas.csv` sem
  conciliação com `respondentes.csv` (DR03; §5.2).
- **Proposta (não decidida):** contrato de identidade entre os dois sistemas
  de origem; enquanto não existir, o elo aparece "em reconciliação" (RF07) e
  nenhuma tela soma respostas como pessoas.

### L03 — Pipeline mensal sem histórico retroativo

- **Impacto:** comparações de fluxo mês a mês (entradas/saídas de status) só
  passam a existir do go-live em diante; o gestor não consegue comparar com
  meses anteriores à implantação.
- **Causa observada:** C03 é snapshot periódico e o histórico de transições
  de status não foi recebido (§5.2).
- **Proposta (não decidida):** iniciar a captura mensal imediatamente na
  implantação e comunicar na tela a data de início da série.

### L04 — Cobertura do instrumento de questionários

- **Impacto:** a tela de resultados (D03) representa hoje apenas 10 pesquisas
  (2,7% do acervo); leituras generalizantes a partir dela são inválidas.
- **Causa observada:** cobertura declarada do C04 (§5.2).
- **Proposta (não decidida):** ingestão completa dos questionários junto ao
  parceiro; até lá, a tela expõe a cobertura ao lado da distribuição.

### L05 — Classificação de atraso sem regra aprovada

- **Impacto:** o usuário procura "pesquisas atrasadas" e a solução não pode
  classificar atraso; ausência de regra vira frustração de navegação.
- **Causa observada:** I06 depende de regra de data de referência e
  prioridade não aprovadas (§5.6; critérios do RF03).
- **Proposta (não decidida):** aprovar com o parceiro a regra de referência
  temporal e prioridade; até lá, telas exibem prazos e prorrogações sem
  rótulo de atraso.

### L06 — Papéis de governança sem titular

- **Impacto:** fluxos de qualidade, acesso e publicação (D04) não têm dono
  real para validar; nas sessões, o papel é exercido por participante
  interno, o que limita a validade externa do teste.
- **Causa observada:** papéis propostos sem designação formal (§5.1;
  levantamento de perfis).
- **Proposta (não decidida):** designação formal pelo parceiro; os registros
  de sessão anotam "papel exercido" para não inflar a evidência.

### L07 — Validação funcional sem métricas de uso

- **Impacto:** os testes já documentados (§6.1.2) provam que o dado certo
  aparece, mas não medem se o usuário **chega** a ele em tempo aceitável —
  risco de aprovar telas corretas e inutilizáveis.
- **Causa observada:** lacuna registrada no
  [levantamento](perfis-e-criterios.md) (testes validam requisito, não
  usabilidade).
- **Proposta (não decidida):** manter o plano desta pasta como etapa
  obrigatória de validação, com as métricas de conclusão/tempo/desvio/erro do
  [roteiro](roteiro-execucao.md).

### L08 — Janela de execução dependente das telas finais

- **Impacto:** as sessões de usabilidade dependem das telas dos reports
  (RP-08); indisponibilidade delas na janela da sprint empurra a execução
  para piloto sobre o protótipo, com menor fidelidade.
- **Causa observada:** dependência declarada nos cards US-06/US-07 e estado
  das entregas RP na sprint.
- **Proposta (não decidida):** executar o piloto no protótipo navegável para
  não perder a janela e **reexecutar** nas telas finais, mantendo os dois
  registros separados (regra já fixada no roteiro, §6).

## 2. Limitações encontradas nas sessões de execução

_Reservado. Preenchido a partir das fichas de US-06/US-07 quando as rodadas
ocorrerem, no mesmo formato (impacto, causa observada com a ficha/tarefa que
a evidencia, proposta marcada como proposta)._
