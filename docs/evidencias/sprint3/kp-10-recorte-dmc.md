# KP-10 — Recorte do Data Model Canvas

## Resultado

O arquivo `docs/dmc.json` mantém exatamente quatro cubos e, dentro de cada
cubo, somente o escopo de Modelo Dimensional solicitado para a Sprint 3.

Foram retirados de cada cubo 21 campos das antigas subseções de Dados e
Governança e quatro listas (`fontes`, `transformacoes`, `qualidade` e `scd`).
As seções corporativas de Negócio e Consumo Analítico e de Governança
Corporativa foram preservadas.

## Contrato estrutural

Cada cubo conserva:

- identificação e seleção do esquema e do tipo de fato;
- informações de bridge tables, junk dimensions e dimensões conformadas;
- listas não vazias de grão, fatos, métricas e dimensões.

O validador não exige as subseções excluídas e rejeita qualquer campo ou lista
fora desse contrato. Os testes cobrem tanto um campo (`controleAcesso`) quanto
uma lista (`fontes`) indevidamente reintroduzidos.

## Verificação reproduzível

Na raiz do repositório:

```bash
python scripts/dmc/validate_dmc.py docs/dmc.json
python -m unittest discover -s scripts/dmc -p "test_*.py"
```

Resultado esperado: documento válido com quatro cubos e todos os testes do
validador aprovados.
