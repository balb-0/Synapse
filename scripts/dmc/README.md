# Validação do Data Model Canvas

O validador confere o recorte da Sprint 1: sintaxe e seções obrigatórias,
quatro cubos com nomes e IDs únicos, esquema dimensional, tipo de fato e
preenchimento das seções de Modelo Dimensional, Dados e Governança dos cubos.

Na raiz do repositório:

```bash
python3 scripts/dmc/validate_dmc.py docs/dmc.json
python3 -m unittest discover -s scripts/dmc -p 'test_*.py'
```

Depois de exportar o canvas novamente, use `--baseline` para comparar
semanticamente o documento completo com o arquivo que foi importado:

```bash
python3 scripts/dmc/validate_dmc.py /tmp/dmc-reexportado.json \
  --baseline docs/dmc.json
```

A abertura e a renderização dos cards ainda devem ser conferidas em uma sessão
nova da ferramenta oficial; o parser isolado não substitui esse gate.
