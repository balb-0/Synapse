# Validação de rastreabilidade

O manifesto registra a cadeia executável entre perguntas de negócio,
requisitos, indicadores, cubos e dashboards. O validador compara esse contrato
com a matriz da §5.4 de `docs/projeto.md` e com os IDs e nomes dos quatro cubos
em `docs/dmc.json`.

```bash
python3 scripts/traceability/validate_traceability.py
python3 -m unittest discover -s scripts/traceability -p 'test_*.py'
```

PB10, PB11 e PB13 mantêm I12–I15 como lacuna dimensional formal da Task 43.
Essa classificação evita tratar a existência de fonte ou dashboard proposto
como se um cubo de resultados/questionários já tivesse sido entregue.
