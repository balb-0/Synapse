# Índice da documentação

## Produto e entregáveis

| Artefato | Papel |
| :--- | :--- |
| [`projeto.md`](projeto.md) | Documento canônico: contexto, arquitetura, modelagem dimensional, requisitos, governança e avaliação |
| [`Governança-de-Dados-do-Projeto.md`](Governança-de-Dados-do-Projeto.md) | Artefato da Sprint 2: estrutura organizacional, qualidade, metadados, classificação, segurança, ciclo de vida e maturidade |
| [`contexto_organizacional_+_requisitos_da_solução_analítica.md`](contexto_organizacional_+_requisitos_da_solução_analítica.md) | Entrada formal do Entregável A, apontando para as seções canônicas |
| [`arquitetura-de-negocio.md`](arquitetura-de-negocio.md) | Cópia local da Arquitetura de Negócio usada como fonte primária de contexto |
| [`dmc.json`](dmc.json) | Exportação do Data Model Canvas para importação na ferramenta oficial |
| [`fontes-e-dependencias.md`](fontes-e-dependencias.md) | Mapa de fontes, limitações e dependências entre os três entregáveis da Sprint 1 |
| [`contrato-lote-extraido.md`](contrato-lote-extraido.md) | Interface comum dos extratores, contrato de lote, checkpoint e metadados |
| [`configuracao-extracao.md`](configuracao-extracao.md) | Configuração segura de caminhos, endpoints e credenciais da extração |
| [`inventario-fontes-etl.md`](inventario-fontes-etl.md) | Inventário técnico das seis fontes do ETL: formato, grão, chaves, volumes, integridade, acesso e disponibilidade |
| [`matriz-evidencias-problem-canvas.md`](matriz-evidencias-problem-canvas.md) | Relação entre dores, causas, impactos, necessidades, objetivos, KPIs, públicos, governança e riscos |

O conteúdo essencial permanece em `projeto.md`. O documento de governança é o
artefato específico da Sprint 2 e detalha suas políticas sem transformar
propostas em controles já implantados. Os demais arquivos auxiliares existem
para tornar matrizes extensas auditáveis e reutilizáveis, não para substituir o
documento principal.

## Evidências e protótipos

| Diretório | Conteúdo |
| :--- | :--- |
| [`assets/prototipos-dashboards/`](assets/prototipos-dashboards/) | interface autocontida, agregado sem identificação, testes e capturas dos dashboards D01–D04 |
| [`../scripts/data_quality/`](../scripts/data_quality/) | manifesto, perfilador, testes e contrato das saídas agregadas |
| [`../scripts/governance/`](../scripts/governance/) | validação reproduzível da classificação, do TAPI e da matriz de acesso |
| [`../scripts/traceability/`](../scripts/traceability/) | contrato executável PB–RF–indicador–cubo/dashboard e validação das extensões futuras de resposta conciliada |

## Documentos de gestão

- [`gestao-configuração.md`](gestao-configuração.md): política de branches, commits, dados sensíveis e configuração.
- [`gestao-projeto.md`](gestao-projeto.md): acompanhamento e avaliação das sprints.
- [`dev-rules.md`](dev-rules.md): regras gerais de desenvolvimento.

Esses documentos registram práticas internas do projeto e não são fonte
primária de requisitos do parceiro.

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
python3 scripts/dmc/validate_dmc.py docs/dmc.json
python3 -m unittest discover -s scripts/dmc -p 'test_*.py'
python3 -m unittest discover -s scripts/data_quality -p 'test_*.py'
python3 -m unittest discover -s scripts/governance -p 'test_*.py'
python3 scripts/traceability/validate_traceability.py
python3 -m unittest discover -s scripts/traceability -p 'test_*.py'
git diff --check
```

A validação completa de governança também confere o TAPI externo sem exibir seu
conteúdo:

```bash
python3 scripts/governance/validate_governance.py \
  --document docs/Governança-de-Dados-do-Projeto.md \
  --tapi /caminho/seguro/Tapi-sinduspharma.txt \
  --repository-root .
```

Para conferir também a identidade e os trechos usados das duas fontes
primárias externas, execute:

```bash
python3 scripts/traceability/validate_traceability.py \
  --sources-dir /caminho/seguro/das-fontes
```

Os protótipos possuem instruções próprias em
[`assets/prototipos-dashboards/README.md`](assets/prototipos-dashboards/README.md).
A suíte de integração depende dos seis CSVs externos e deve receber o diretório
por `SINDUSFARMA_CSV_DIR`; ausência das fontes produz `skip`, não aprovação do
gate completo.
