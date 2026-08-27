# Validação do documento de governança

O validador confere as seções 4 e 5 do artefato da Sprint 2 sem ler ou imprimir
as bases do parceiro. A checagem cobre classificação, campos de risco, perfis,
matriz de acesso por camada, hash do TAPI e fontes brutas rastreadas pelo Git.

```bash
python3 scripts/governance/validate_governance.py \
  --document docs/Governança-de-Dados-do-Projeto.md \
  --tapi /caminho/seguro/Tapi-sinduspharma.txt \
  --repository-root .
```

Testes unitários:

```bash
python3 -m unittest discover -s scripts/governance -p 'test_*.py'
```

O caminho do TAPI é externo ao repositório. O comando calcula o SHA-256 dos
bytes recebidos e compara com a identidade registrada no documento; nenhum
trecho da fonte é exibido.

Para arquivos rastreados, o gate bloqueia os nomes conhecidos das seis bases e
seu alias `teste.csv`, qualquer caminho sob `data/raw` ou `data/private` e CSVs
renomeados cujo cabeçalho contenha identificadores de risco do projeto. A saída
informa somente o caminho, nunca linhas de dados.
