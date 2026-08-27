# Validação do documento de governança

O validador confere as Seções 1, 3, 4 e 5 do artefato da Sprint 2 sem ler ou
imprimir as bases do parceiro. A checagem cobre:

- papéis de governança, mapa funcional, RACI e interfaces de custódia;
- campos comuns do catálogo e requisitos específicos de fatos, dimensões,
  medidas e fontes;
- exemplo `FATO_CICLO_PESQUISA`, seus contratos e os quatro cubos;
- consistência dos papéis entre documento, TAPI, DMC e Arquitetura de Negócio,
  mantendo aliases, fornecedores e ferramentas como evidências distintas;
- classificação, campos de risco, perfis e matriz de acesso por camada;
- identidade do TAPI e ausência de fontes brutas rastreadas pelo Git.

Os checks estruturais aceitam estados explícitos como `indisponivel` e
`pendente_confirmacao`. Eles bloqueiam ausência, duplicidade ou contradição do
contrato; não interpretam uma proposta documentada como implantação produtiva.
Por padrão, o gate lê `docs/dmc.json` e `docs/arquitetura-de-negocio.md` a
partir de `--repository-root`; caminhos alternativos podem ser informados por
`--dmc` e `--architecture`.

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
