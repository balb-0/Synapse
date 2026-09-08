# KP-07 — revisão de segurança, conformidade e LGPD

## Critério revisado

As regras corporativas do `docs/dmc.json` foram confrontadas com a seção 6.6 de
`docs/projeto.md`. O canvas registra diretrizes de projeto, não comprovação de
controles implantados pelo parceiro.

| Tema exigido | Registro no DMC | Fonte no projeto | Estado |
|---|---|---|---|
| Minimização | Finalidade documentada, mínimo necessário e separação da identidade | §6.6.4 e §6.6.5 | Proposta sujeita ao controlador |
| Segregação | Separação entre ambientes acadêmico, desenvolvimento, homologação e produção | §6.6.6 | Desenho ainda não homologado |
| Retenção | Prazo definido por finalidade e obrigação, com eliminação, anonimização ou bloqueio | §6.6.9 | Política a aprovar |
| Acesso | Menor privilégio, necessidade de conhecer, recurso, ação e finalidade | §6.6.6 | Matriz de perfis a aprovar |
| Rejeitados | Classificação, quarentena, auditoria, reconciliação e reprocessamento | §5.3.5 e §6.6.11 | Fluxo proposto |
| Publicação | Somente dados sintéticos, agregados ou com anonimização testada | §6.6.5 e §6.6.11 | Condicionada à aprovação |

## Decisões preservadas como pendentes

- Controlador, operador, encarregado, base legal e prazo de retenção devem ser
  confirmados por fluxo; o canvas não atribui esses papéis por inferência.
- O limiar de supressão `k = 5` é uma proposta inicial e precisa ser testado com
  os dados autorizados antes da produção.
- A matriz final de perfis, exceções e logs de acesso depende de homologação do
  Data Owner e da TI.
- A dependência `MG-01` (`#170`) permanece aberta. Por isso, regras específicas
  de schema ou domínio que ainda não estejam inventariadas não foram declaradas
  como confirmadas.

## Verificações

```bash
python -m json.tool docs/dmc.json
python scripts/dmc/validate_dmc.py docs/dmc.json
python scripts/traceability/validate_traceability.py \
  --manifest scripts/traceability/manifest.json \
  --dmc docs/dmc.json \
  --project docs/projeto.md
```

O diff não inclui dados pessoais, bases reais, credenciais ou decisões não
sustentadas pelo documento do projeto.
