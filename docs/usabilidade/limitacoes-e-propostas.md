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

