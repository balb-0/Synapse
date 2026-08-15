# Regras de desenvolvimento

Este documento registra as práticas técnicas adotadas para os artefatos da
Sprint 1.

## Organização

- Documentação principal e entregáveis ficam em `docs/`.
- Imagens, diagramas e protótipos ficam em `docs/assets/`.
- Scripts, validadores e notebooks exploratórios ficam em `scripts/`.
- Bases brutas recebidas do parceiro não devem ser versionadas no Git.

## Padrões de código

- Python deve priorizar funções pequenas, nomes descritivos e entrada por
argumentos de linha de comando quando o script for reproduzível.
- Scripts que processam dados devem receber diretórios por parâmetro e não
alterar os arquivos de origem.
- Saídas versionadas devem conter apenas agregados, logs ou evidências sem dado
pessoal identificável.
- Comentários devem explicar regra de negócio, limitação de dado ou decisão de
modelagem; não devem repetir o óbvio do código.

## Validação

Antes da entrega, executar quando aplicável:

```bash
python scripts/dmc/validate_dmc.py docs/dmc.json
python scripts/traceability/validate_traceability.py --manifest scripts/traceability/manifest.json --dmc docs/dmc.json --project docs/projeto.md
python -m unittest discover -s scripts/dmc -p "test_*.py"
python -m unittest discover -s scripts/traceability -p "test_*.py"
```

Testes que dependem dos CSVs externos devem receber o diretório seguro por
variável de ambiente ou argumento explícito.

## Dados sensíveis

- Não publicar CSV bruto, e-mail, resposta individual ou identificador pessoal.
- Não registrar senhas, tokens, chaves de API ou credenciais.
- Quando houver dúvida sobre reidentificação, entregar apenas agregado e
registrar a limitação no documento.
