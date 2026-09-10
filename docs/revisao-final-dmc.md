# Revisão final do Data Model Canvas

## Parecer

O `docs/dmc.json`, versão 1.1 de 10 de setembro de 2026, está completo para a
interface ampliada do Data Model Canvas e aprovado nos gates reproduzíveis do repositório. O
artefato preserva limitações e decisões externas como estados explícitos, sem
transformá-las em resultados inventados ou capacidades já implantadas.

A única verificação que não pode ser concluída apenas com o repositório é o
round-trip visual na
[ferramenta oficial](https://afonsolelis.github.io/aulas/pages/module-11-eng-software/data-model-canvas.html).
O esquema serializado da página foi conferido, mas ainda falta uma exportação
gerada por uma nova sessão para provar visualmente o ciclo importar–exportar. O
gate documentado em `scripts/dmc/README.md` compara essa reexportação
integralmente.

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
| Táticas arquiteturais | idempotência, quarentena fail-closed e resiliência orientada a eventos | Completo no JSON e no Markdown |
| Arquitetura do ETL | fontes, camadas, orquestração, carga, qualidade, telemetria, custo e fluxo | Completo no JSON e no Markdown |
| Rastreabilidade | 13 perguntas, 25 indicadores e 4 cubos no manifesto | Aprovada |

## Avaliação contra o barema

| Critério de avaliação | Verificação realizada | Parecer |
| :--- | :--- | :--- |
| Coerência com contextualização e requisitos | Os 7 objetivos, 5 processos, PB01–PB13, perfis, riscos e papéis foram reconciliados com `contexto_organizacional_+_requisitos_da_solução_analítica.md`; estados futuros não foram convertidos em capacidades existentes. | Atendido |
| Qualidade de Negócio, Consumo Analítico e Governança Corporativa | O JSON contém 13 perguntas, 25 indicadores com disponibilidade explícita, 4 públicos/canais com restrição, 6 decisões/riscos com impacto e estado e os 12 campos corporativos de governança. | Atendido |
| Consistência dimensional de cada cubo | C01 é fato acumulativo por pesquisa; C02 é fato transacional por participação; C03 é snapshot periódico mensal; C04 é fato sem medidas de associação pesquisa–pergunta. Cada escolha é compatível com o respectivo processo. | Atendido |
| Adequação de grão, fatos, métricas e dimensões | Todos os cubos declaram o menor nível, evitam dupla contagem, distinguem medidas aditivas, semi-aditivas e não aditivas e identificam dimensões conformadas. Limitações de denominador, calendário e reconciliação geram `NULL`, indisponibilidade ou bloqueio, não estimativas. | Atendido |
| Correspondência entre cubos e requisitos funcionais | A matriz PB–RF–indicador–cubo/artefato–dashboard cobre RF01–RF13. RF06–RF09 e RF12 são atendidos pelas seções transversais de qualidade, acesso, publicação e ETL; I12, I13 e I15 permanecem extensões explicitamente condicionadas à integração futura. | Atendido, com dependências declaradas |
| Organização e completude do `dmc.json` | O arquivo usa `schemaVersion: 1`, contém metadados, seções corporativas, 4 cubos, 3 táticas e ETL; todos os campos reconhecidos pela interface estão presentes e não vazios quando obrigatórios. | Atendido |

Não foram encontrados campos vazios, seções ausentes, IDs duplicados, métricas
sem grão identificável ou requisitos sem rota de atendimento. Os itens marcados
como pendentes são dependências de fonte, política ou homologação e estão
registrados como tais para evitar afirmações sem evidência.

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
6. Táticas Arquiteturais e Arquitetura do ETL foram incorporadas ao JSON e ao
   `dmc.md`, com oito diagramas Mermaid prontos para renderização.

## Validações executadas

Em 10 de setembro de 2026:

```text
python scripts/dmc/run_gates.py
[ok] 5 gates aprovados

python -m unittest discover -s scripts/dmc -p "test_*.py"
Ran 47 tests
OK
```

Os gates cobrem JSON canônico, contrato semântico, rastreabilidade, 47 testes
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
