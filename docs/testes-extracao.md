# Testes dos extratores

A suíte de extração verifica o comportamento dos seis extratores sem acessar
os arquivos do parceiro, o MinIO ou qualquer banco de dados. As entradas usadas
nos testes são sintéticas e os leitores de objetos são substituídos por
implementações em memória.

## Cobertura funcional

| Cenário | Testes |
| :--- | :--- |
| Extração com sucesso | testes específicos das seis fontes e `test_extractor_contract_suite.py` |
| Fonte vazia | `test_csv_extractors.py` e `test_extractor_contract_suite.py` |
| Paginação e retomada por checkpoint | `test_batching_checkpoints.py` |
| Timeout, retry e limite de tentativas | `test_resilience.py` |
| Entrada ou checkpoint malformado | `test_csv_extractors.py`, `test_questoes_respostas_extractors.py` e `test_batching_checkpoints.py` |
| Contrato comum de lote e metadados | `test_contracts.py` e `test_extractor_contract_suite.py` |
| Logs técnicos sem conteúdo dos registros | `test_extraction_logs.py` |
| Fluxo conjunto das seis fontes | `test_smoke_extraction.py` |

A suíte comum de contrato instancia cada extrator pelo mesmo protocolo,
confere os tipos de lote e checkpoint e valida os atributos técnicos entregues
ao estágio seguinte. Isso evita que uma fonte implemente um formato diferente
das demais.

## Execução

Para executar todos os testes do repositório:

```bash
python -m unittest discover -s tests -v
```

Para executar somente os testes acrescentados para a validação conjunta dos
extratores:

```bash
python -m unittest tests.extraction.test_extractor_contract_suite -v
python -m unittest tests.extraction.test_smoke_extraction -v
```

Para medir a cobertura da camada de extração:

```bash
python -m coverage erase
python -m coverage run --source=src/etl/extraction -m unittest discover -s tests
python -m coverage report -m
```

O smoke test e seu resultado estão descritos em
[`smoke-test-extracao.md`](smoke-test-extracao.md).
