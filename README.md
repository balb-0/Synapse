# Central de Pesquisas do Sindusfarma

Repositório do Grupo 05 para os artefatos de arquitetura e governança de dados
da Central de Pesquisas. O documento canônico do produto é
[`docs/projeto.md`](docs/projeto.md); o índice de documentação explica onde
encontrar cada artefato e como reproduzir as validações.

## Artefatos da Sprint 1

- [Documento principal](docs/projeto.md): contexto, modelagem quantitativa, requisitos, governança e avaliação.
- [Data Model Canvas](docs/dmc.json): exportação JSON no schema da ferramenta oficial.
- [Fontes e dependências](docs/fontes-e-dependencias.md): origem e limitações dos três entregáveis.
- [Matriz de evidências](docs/matriz-evidencias-problem-canvas.md): distinção entre observação, inferência, proposta e pendência.
- [Índice de documentação](docs/index.md): estrutura completa e comandos de validação.

## Dados e privacidade

As bases brutas não fazem parte do repositório. CSV, XLS e XLSX são ignorados
por padrão porque podem conter e-mail, identificadores estáveis ou texto livre.
Não use `git add -f` para publicar uma base sem comprovar sua natureza e aplicar
os controles de anonimização, minimização e autorização necessários.

## Validação estrutural rápida

```bash
jq empty docs/dmc.json
python3 scripts/dmc/validate_dmc.py docs/dmc.json
python3 -m unittest discover -s scripts/dmc -p 'test_*.py'
python3 -m unittest discover -s scripts/data_quality -p 'test_*.py'
python3 scripts/traceability/validate_traceability.py
python3 -m unittest discover -s scripts/traceability -p 'test_*.py'
git diff --check
```

A conferência completa da rastreabilidade também compara os hashes e os
trechos auditáveis do TAPI e da Arquitetura de Negócio, mantidos fora do Git:

```bash
python3 scripts/traceability/validate_traceability.py \
  --sources-dir /caminho/seguro/das-fontes
SINDUSFARMA_SOURCE_DIR=/caminho/seguro/das/fontes \
  python3 -m unittest discover -s scripts/traceability -p 'test_*.py'
```

Os testes de integração dos protótipos exigem os seis CSVs externos. Consulte
[`docs/assets/prototipos-dashboards/README.md`](docs/assets/prototipos-dashboards/README.md)
para executar essa suíte sem publicar as fontes.
