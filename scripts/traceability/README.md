# Validação de rastreabilidade

O manifesto registra a cadeia executável entre perguntas de negócio,
requisitos, indicadores, cubos e dashboards. O validador compara esse contrato
com a matriz da §5.4 de `docs/projeto.md` e com os IDs e nomes dos quatro cubos
em `docs/dmc.json`.

```bash
python3 scripts/traceability/validate_traceability.py
python3 -m unittest discover -s scripts/traceability -p 'test_*.py'
```

Para o gate completo da Task 52, informe o diretório externo que contém os
arquivos originais. O validador confere SHA-256 e os trechos que sustentam
escopo, MVP, problema, fluxo, públicos, conceitos e papéis:

```bash
python3 scripts/traceability/validate_traceability.py \
  --sources-dir /caminho/seguro/das-fontes
```

Os originais não são copiados nem publicados pelo script. Sem
`--sources-dir`, o comando valida apenas a consistência interna e declara essa
limitação na saída.

PB10, PB11 e PB13 mantêm I12–I15 como lacuna dimensional formal da Task 43.
Essa classificação evita tratar a existência de fonte ou dashboard proposto
como se um cubo de resultados/questionários já tivesse sido entregue.
