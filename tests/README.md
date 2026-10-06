# Testes do G05

A suíte está separada do código em `src/etl/` e organizada por responsabilidade. Usa `unittest`, leitores/sinks em memória e DuckDB real em arquivos temporários. As fixtures versionadas são sintéticas; não copie bases do parceiro para esta pasta.

## Organização

| Diretório/arquivo | Cobertura |
| :--- | :--- |
| [`extraction/`](extraction/) | Contratos das seis fontes, leitura, lotes, checkpoints, erros e retry. |
| [`transformation/`](transformation/) | Tipos, normalização, regras, quarentena, integração com DuckDB e logs. |
| [`load/`](load/) | Configuração, DDL, persistência, lock, idempotência e retomada. |
| [`analytics/`](analytics/) | Dimensões/fatos, grão, recarga, reconciliação e publicação Parquet. |
| [`orchestration/`](orchestration/) | Flows, retry, retomada, telemetria e contratos de operação. |
| [`e2e/`](e2e/) | Cenários integrados do pipeline com fixtures. |
| [`fixtures/`](fixtures/) | Seis CSVs pequenos, manifesto e cenários controlados; emails `example.invalid`. |
| [`test_architecture_docs.py`](test_architecture_docs.py) | Contrato executável da documentação arquitetural. |

Scripts de validação têm testes próprios em `scripts/dmc`, `scripts/data_quality`, `scripts/governance`, `scripts/traceability` e `scripts/analytics`. `discover -s tests` não executa automaticamente todas essas suítes externas.

## Executar

Na raiz do repositório, use Python 3.12 e o ambiente virtual:

```bash
python -m pip install -r requirements.txt -r requirements-transformation-dev.txt
PYTHONPATH=src python -m unittest discover -s tests -t . -v
PYTHONPATH=src python -m unittest discover -s tests/analytics -t . -v
python -m unittest discover -s scripts/analytics -p 'test_*.py' -v
```

A suíte deve registrar erro real quando houver falha. Uma execução parcial ou com `skip` não comprova todos os cenários. Para outras validações documentais e seus insumos privados, siga o [portal](../docs/index.md#checks).

## Gates da CI

[`.gitlab-ci.yml`](../.gitlab-ci.yml) mantém jobs obrigatórios de lint e testes:

```bash
export PYTHONPATH=src
ruff check src scripts tests
ruff format --check src scripts tests
python scripts/architecture/validate_architecture_docs.py
python scripts/transformation/render_schema.py --check
PYTHONPATH=src coverage run --branch --source=etl -m xmlrunner discover -s tests -o test-reports -v
coverage report --fail-under=85
coverage xml -o coverage-etl.xml
```

A cobertura mínima é 85%; JUnit e Cobertura são artefatos da CI. Confira o SHA da MR e do pipeline antes de declarar aprovação. Cobertura do pacote ETL não mede layout de relatório, funcionamento real do DAX no Desktop ou usabilidade humana.

## Massas e evidências

[`fixtures/__init__.py`](fixtures/__init__.py) declara a ordem e o resultado esperado das seis fontes. [`fixtures/test_fixtures_sinteticas.py`](fixtures/test_fixtures_sinteticas.py) verifica cabeçalhos, contagens, relacionamentos e domínio de email sintético. Cenários deliberadamente inválidos testam rejeição e quarentena; não são dados reais.

Testes com dados autorizados externos devem registrar versão, origem, comando, resultado e limites sem publicar registros individuais. Capturas do Power BI e sessões S1–S4 pertencem à [documentação de validação](../docs/validacao-acesso-bi.md) e à [usabilidade](../docs/usabilidade/), com evidência da execução específica. Não preencher fichas humanas com resultados de testes unitários.
