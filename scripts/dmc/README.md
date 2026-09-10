# Validação do Data Model Canvas

O validador confere a versão ampliada do canvas: sintaxe e seções corporativas
obrigatórias, metadados com data e versão válidas, quatro cubos com nomes e IDs
canônicos, presença e tipo de todos os campos de Modelo Dimensional, Dados e
Governança, seleção de esquema e fato e listas não vazias nem duplicadas de
grão, fatos, métricas, dimensões, fontes, transformações, qualidade e SCD.

Os campos de Dados e Governança por cubo voltaram a ser obrigatórios após a
ampliação da ferramenta oficial em 10 de setembro de 2026. O contrato agora
inclui otimização, classificação, acesso, auditoria, ciclo de vida, catálogo e
KPIs, além da Governança Corporativa transversal. Campos desconhecidos continuam
rejeitados para evitar exportações silenciosamente incompatíveis.

Na raiz do repositório:

```bash
python3 scripts/dmc/validate_dmc.py docs/dmc.json
python3 -m unittest discover -s scripts/dmc -p 'test_*.py'
```

Depois de exportar o canvas novamente, use `--baseline` para comparar
semanticamente o documento completo com o arquivo que foi importado:

```bash
python3 scripts/dmc/validate_dmc.py /tmp/dmc-reexportado.json \
  --baseline docs/dmc.json
```

A abertura e a renderização dos cards ainda devem ser conferidas em uma sessão
nova da ferramenta oficial; o parser isolado não substitui esse gate.

## Baseline da Sprint 3

O inventário inicial de `docs/dmc.json` registrou `schemaVersion` 1, versão 1.0,
data 2026-07-31 e quatro cubos (`cubo-1` a `cubo-4`), todos com grão, fatos,
métricas e dimensões preenchidos. As seções de topo estavam presentes e não
havia campo vazio em Governança Corporativa.

O inventário também delimitou o trabalho posterior: revisão de Negócio e
Consumo Analítico em KP-02–KP-05, revisão de Governança Corporativa em KP-07 e
KP-08 e reconciliação dimensional em KP-09. KP-10 refletiu o recorte disponível
naquele momento; a ampliação posterior da interface tornou novamente
obrigatórios os campos de Dados e Governança por cubo. A abertura visual
continua sendo um gate manual porque o repositório não informa URL ou executável
da ferramenta oficial.

Para reproduzir o baseline:

```bash
python scripts/dmc/inventory_dmc.py docs/dmc.json
python scripts/dmc/validate_dmc.py docs/dmc.json
```

## Gates finais

O orquestrador executa, em sequência, a leitura estrutural do JSON, a validação
semântica do DMC, a rastreabilidade e as duas suítes de testes:

```bash
python scripts/dmc/run_gates.py
```

Após importar o canvas em uma sessão nova da ferramenta oficial, conferir os
quatro cards e exportar novamente para um caminho temporário fora do
repositório. O argumento `--reexport` acrescenta os gates estrutural e de
round-trip semântico desse arquivo:

```bash
python scripts/dmc/run_gates.py --reexport /caminho/temporario/dmc-reexportado.json
```

O gate só comprova o round-trip quando recebe um arquivo realmente produzido
pela ferramenta. Não use uma cópia de `docs/dmc.json` como substituta.

Na revisão 1.1, de 10 de setembro de 2026, os cinco gates locais foram
aprovados e o documento apresentou exatamente quatro cubos. KP-08 e KP-10 já
estão integradas. A reabertura em sessão nova permanece um gate manual externo:
ela depende da URL ou do executável da ferramenta oficial e de um JSON realmente
reexportado, nenhum dos quais está disponível no repositório. Essa dependência
não reduz a completude do artefato versionado, mas impede afirmar compatibilidade
visual sem executar o teste. O arquivo temporário de reexportação não deve ser
versionado.
