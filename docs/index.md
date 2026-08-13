# Índice da documentação

## Produto e entregáveis

| Artefato | Papel |
| :--- | :--- |
| [`projeto.md`](projeto.md) | Documento canônico: contexto, arquitetura, modelagem dimensional, requisitos, governança e avaliação |
| [`dmc.json`](dmc.json) | Exportação do Data Model Canvas para importação na ferramenta oficial |
| [`fontes-e-dependencias.md`](fontes-e-dependencias.md) | Mapa de fontes, limitações e dependências entre os três entregáveis da Sprint 1 |
| [`matriz-evidencias-problem-canvas.md`](matriz-evidencias-problem-canvas.md) | Relação entre dores, causas, impactos, necessidades, objetivos, KPIs, públicos, governança e riscos |

O conteúdo essencial permanece em `projeto.md`. Os arquivos auxiliares existem
para tornar matrizes extensas auditáveis e reutilizáveis, não para substituir o
documento principal.

## Evidências e protótipos

| Diretório | Conteúdo |
| :--- | :--- |
| [`assets/prototipos-dashboards/`](assets/prototipos-dashboards/) | interface autocontida, agregado sem identificação, testes e capturas dos dashboards D01–D04 |
| [`../scripts/data_quality/`](../scripts/data_quality/) | manifesto, perfilador, testes e contrato das saídas agregadas |

## Documentos de gestão

- [`gestao-configuração.md`](gestao-configuração.md): política de branches, commits, dados sensíveis e configuração.
- [`gestao-projeto.md`](gestao-projeto.md): acompanhamento e avaliação das sprints.
- [`dev-rules.md`](dev-rules.md): regras gerais de desenvolvimento.

Esses documentos ainda seguem o template acadêmico onde não houve task
específica de preenchimento. Eles não são fonte primária de requisitos do
parceiro.

## Bases e insumos locais

Os seis CSVs usados na análise ficam fora do Git. A raiz pode conter cópias
locais ignoradas, mas elas não devem ser movidas para `docs/` nem forçadas para
versionamento. O perfilador recebe o diretório por argumento, gera somente
agregados e não modifica a origem.

```bash
python3 scripts/data_quality/profile_csv.py \
  --input-dir /caminho/seguro/das-fontes \
  --output-dir /tmp/perfil-g05 \
  --dictionary "/caminho/seguro/dicionario.csv"
```

O dicionário e as fontes são obrigatórios para uma reprodução integral. Na
ausência deles, uma referência documental não deve ser apresentada como teste
executado.

## Checks

```bash
jq empty docs/dmc.json
python3 -m unittest discover -s scripts/data_quality -p 'test_*.py'
git diff --check
```

Os protótipos possuem instruções próprias em
[`assets/prototipos-dashboards/README.md`](assets/prototipos-dashboards/README.md).
A suíte de integração depende dos seis CSVs externos e deve receber o diretório
por `SINDUSFARMA_CSV_DIR`; ausência das fontes produz `skip`, não aprovação do
gate completo.
