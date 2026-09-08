# KP-11 — Gates finais do Data Model Canvas

## Gates automatizados

Em 8 de setembro de 2026, o comando abaixo foi executado sobre a versão
canônica presente na branch:

```bash
python scripts/dmc/run_gates.py
```

Resultado: cinco gates aprovados — sintaxe JSON, contrato semântico do DMC,
rastreabilidade, testes do DMC e testes de rastreabilidade. O documento contém
exatamente quatro cubos.

## Gate de reexportação

O gate de reexportação permanece pendente porque requer uma ação na ferramenta
oficial: importar `docs/dmc.json` em sessão nova, conferir visualmente os quatro
cards e exportar um novo JSON. A URL ou uma instalação executável dessa
ferramenta não está versionada no projeto.

Quando o arquivo temporário estiver disponível, executar:

```bash
python scripts/dmc/run_gates.py --reexport /caminho/temporario/dmc-reexportado.json
```

Esse modo adiciona a validação sintática do arquivo reexportado e a comparação
semântica integral com `docs/dmc.json`. O artefato temporário não deve ser
versionado.

## Dependências

A execução final deve ocorrer depois da integração de KP-07, KP-08 e KP-10,
conforme a dependência declarada na issue. Até essa integração e a conferência
manual, esta evidência registra automação pronta e resultado parcial, não a
conclusão do gate de sessão nova.
