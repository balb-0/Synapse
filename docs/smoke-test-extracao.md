# Smoke test da extração

O smoke test executa os seis extratores em uma única verificação e compara as
quantidades produzidas com valores previamente definidos. As fixtures são
geradas em memória e contêm somente valores sintéticos; nenhum arquivo real,
serviço externo ou credencial é necessário.

## Resultado da execução

- Data: 10 de setembro de 2026
- Ambiente: Python 3.13.1
- Comando: `python -m unittest tests.extraction.test_smoke_extraction -v`
- Resultado: 1 teste executado com sucesso

| Fonte | Registros esperados | Registros obtidos | Lotes esperados | Lotes obtidos | Situação |
| :--- | ---: | ---: | ---: | ---: | :---: |
| Pesquisas | 2 | 2 | 1 | 1 | Aprovado |
| Empresas | 3 | 3 | 2 | 2 | Aprovado |
| Clientes | 4 | 4 | 2 | 2 | Aprovado |
| Respondentes | 2 | 2 | 1 | 1 | Aprovado |
| Questões | 3 | 3 | 2 | 2 | Aprovado |
| Respostas | 5 | 5 | 3 | 3 | Aprovado |
| **Total** | **19** | **19** | **11** | **11** | **Aprovado** |

O tamanho do lote foi fixado em dois registros para que a mesma execução
também percorresse fontes com mais de uma página. Além das contagens, o teste
confere que cada lote gera um evento de log, que todos os eventos preservam o
identificador da execução e que o checkpoint final corresponde ao último
registro da fonte.

Por não depender de arquivos locais nem de infraestrutura externa, o comando
pode ser executado no pipeline de integração contínua nas mesmas condições da
execução local.
