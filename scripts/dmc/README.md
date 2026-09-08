# Validação do Data Model Canvas

O validador confere o recorte da Sprint 3: sintaxe e seções corporativas
obrigatórias, quatro cubos com nomes e IDs canônicos, esquema dimensional,
tipo de fato e preenchimento de grão, fatos, métricas e dimensões.

Nos cubos, o contrato aceita somente os campos de Modelo Dimensional. Campos
das antigas subseções Dados e Governança — como `fontes`, `qualidade`,
`controleAcesso` e `retencao` — são rejeitados. A seção corporativa
`governancaCorporativa` continua obrigatória e não é afetada por esse recorte.
Na adequação foram retirados, de cada cubo, 21 campos e as quatro listas
`fontes`, `transformacoes`, `qualidade` e `scd`. Os testes negativos cobrem a
reintrodução indevida de `controleAcesso` e `fontes`.

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
