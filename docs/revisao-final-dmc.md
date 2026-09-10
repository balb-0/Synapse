# Revisão final do Data Model Canvas

## Parecer

O `docs/dmc.json`, versão 1.1 de 10 de setembro de 2026, está completo para o
recorte da Sprint 3 e aprovado nos gates reproduzíveis do repositório. O
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
| Conteúdo dos cubos | grão, fatos, métricas e dimensões em cada cubo | Completo |
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
5. O documento principal foi alinhado ao recorte vigente: Dados e Governança
   por cubo estão fora da Sprint 3; Governança Corporativa permanece completa.

## Validações executadas

Em 10 de setembro de 2026:

```text
python scripts/dmc/run_gates.py
[ok] 5 gates aprovados

python -m unittest discover -s scripts/dmc -p "test_*.py"
Ran 40 tests
OK
```

Os gates cobrem JSON canônico, contrato semântico, rastreabilidade, 40 testes
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
