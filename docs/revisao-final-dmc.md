# Revisão final do Data Model Canvas

## Parecer

O `docs/dmc.json`, versão 1.1 de 10 de setembro de 2026, está completo para a
interface ampliada do Data Model Canvas e aprovado nos gates reproduzíveis do repositório. O
artefato preserva limitações e decisões externas como estados explícitos, sem
transformá-las em resultados inventados ou capacidades já implantadas.

A única verificação que não pode ser concluída apenas com o repositório é o
round-trip visual na ferramenta oficial. Não há URL, executável nem exportação
gerada por uma nova sessão. Quando um desses meios estiver disponível, o gate
documentado em `scripts/dmc/README.md` compara a reexportação integralmente.

## Cobertura revisada

| Dimensão | Evidência | Resultado |
| :--- | :--- | :--- |
| Metadados | parceiro, grupo, data ISO e versão | Completo |
| Negócio | 7 objetivos e 5 processos atuais | Completo |
| Perguntas | PB01–PB13, em ordem canônica | Completo |
| Indicadores | I01–I25, com disponibilidade ou dependência declarada | Completo |
| Usuários e canais | UC01–UC04, todos com limite de acesso | Completo |
| Decisões e riscos | DR01–DR06, todos com impacto e estado | Completo |
| Governança corporativa | 12 campos obrigatórios preenchidos | Completo |
| Modelo dimensional | C01–C04, IDs e nomes canônicos | Completo |
| Conteúdo dimensional | grão, fatos, métricas, dimensões e dimensões especiais em cada cubo | Completo |
| Dados por cubo | fontes, transformações, qualidade e histórico/SCD | Completo |
| Governança por cubo | otimização, classificação, acesso, auditoria, ciclo de vida, catálogo e KPIs | Completo |
| Táticas arquiteturais | idempotência, quarentena fail-closed e resiliência orientada a eventos | Documentadas no Markdown |
| Arquitetura do ETL | fontes, camadas, orquestração, carga, qualidade, telemetria, custo e fluxo | Documentada no Markdown |
| Rastreabilidade | 13 perguntas, 25 indicadores e 4 cubos no manifesto | Aprovada |

## Correções desta revisão

1. As três métricas temporais derivadas do C01 deixaram de apresentar uma
   subtração simples de datas como dias úteis. Até existir calendário
   homologado, o contrato exige dias corridos, denominador e exclusão de pares
   incompletos.
2. A versão documental foi elevada de 1.0 para 1.1 e recebeu a data da revisão.
3. O validador passou a rejeitar data ou versão malformada, campo dimensional
   ausente ou vazio, seletor não booleano e item duplicado nas listas dos cubos.
4. O teste de consistência de governança passou a abrir o DMC explicitamente em
   UTF-8, eliminando falha dependente do locale no Windows.
5. A ampliação da ferramenta em 10 de setembro foi incorporada: Dados e
   Governança por cubo voltaram ao contrato e foram preenchidos sem perder a
   Governança Corporativa transversal.
6. O `dmc.md` passou a consolidar também os blocos novos de Táticas
   Arquiteturais e Arquitetura do ETL, com oito diagramas Mermaid prontos para
   renderização ou transferência à ferramenta.

## Validações executadas

Em 10 de setembro de 2026:

```text
python scripts/dmc/run_gates.py
[ok] 5 gates aprovados

python -m unittest discover -s scripts/dmc -p "test_*.py"
Ran 42 tests
OK
```

Os gates cobrem JSON canônico, contrato semântico, rastreabilidade, 42 testes
do DMC e 14 testes de rastreabilidade. Um teste de rastreabilidade de fontes
primárias é corretamente ignorado quando os arquivos externos protegidos não
estão presentes.

## Limites preservados corretamente

Os estados pendente, indisponível ou proposto do canvas representam dependências
reais do parceiro ou da operação: universo de convidados, fonte autoritativa de
market share, identidade conciliada, metadados de carga/publicação, política de
acesso e homologação dos papéis. Eles não são lacunas de preenchimento. Fechá-los
sem nova evidência violaria a rastreabilidade e poderia produzir indicadores
enganosos.

## Gate externo restante

Para validar a compatibilidade visual quando a ferramenta oficial estiver
disponível:

```bash
python scripts/dmc/run_gates.py --reexport /caminho/dmc-reexportado.json
```

O arquivo usado deve ser uma exportação real de uma sessão nova; uma cópia do
JSON versionado não constitui evidência de round-trip.
