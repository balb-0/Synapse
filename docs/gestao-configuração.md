# Gestão de configuração

Este documento define regras mínimas para manter o repositório da Sprint 1
auditável e sem dados indevidos.

## Branches e revisão

- Desenvolver mudanças em branches de trabalho e integrar por merge request.
- Evitar commits diretos na branch principal.
- Revisar alterações que afetem `docs/projeto.md`, `docs/dmc.json`,
  validadores, scripts de dados ou artefatos de entrega.
- Separar correções de conteúdo, reorganização de arquivos e mudanças de código
  quando possível, para facilitar revisão.

## Commits

Usar mensagens objetivas no padrão Conventional Commits:

```text
docs: ajusta rastreabilidade dos dashboards
fix: corrige métrica de respondentes no dmc
test: atualiza contrato de rastreabilidade
```

Evitar mensagens vagas como `ajustes`, `final` ou `melhorias`.

## Arquivos sensíveis

- Não versionar bases brutas do parceiro, arquivos pessoais, credenciais,
  tokens, dumps de banco ou `.env`.
- Manter apenas documentação, agregados, imagens, logs e dados sintéticos ou
  anonimizados.
- Qualquer saída de script deve ser revisada antes de entrar em `docs/assets/`.

## Validação antes da entrega

```bash
python -m json.tool docs/dmc.json
python scripts/dmc/validate_dmc.py docs/dmc.json
python scripts/traceability/validate_traceability.py --manifest scripts/traceability/manifest.json --dmc docs/dmc.json --project docs/projeto.md
```

Quando os CSVs externos estiverem disponíveis em diretório seguro, executar
também os testes e geradores que dependem dessas fontes.

## Rollback

Se uma alteração quebrar documentação, JSON ou testes, preferir uma correção
incremental ou um `git revert` do commit problemático. Não apagar histórico nem
remover alterações de outra pessoa sem alinhamento com o grupo.
