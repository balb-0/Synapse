# FN-02 — Investimento inicial de referência

**Data-base:** 06/10/2026. **Moeda:** BRL. **Natureza:** cenário incremental de implantação a partir do repositório existente, não valor já gasto nem proposta comercial. O esforço anterior da equipe é custo histórico fora desta decisão.

## Método e tarifas

O [Anexo II vigente da Portaria SGD/MGI nº 750/2023](https://www.gov.br/governodigital/pt-br/contratacoes-de-tic/legislacao/modelo-de-contratacao-de-servicos-de-desenvolvimento-manutencao-e-sustentacao-de-software/portaria-sgd-mgi-no-750-de-20-de-marco-de-2023) fornece salário de referência e fator-k para contratação de serviços de software. Como aproximação de planejamento, usamos `custo/h = salário mensal × fator-k ÷ 160 h`. A referência federal não é cotação do parceiro. O fator-k já compõe o custo do perfil; não somamos encargos outra vez. Calculamos com precisão integral e arredondamos apenas as linhas exibidas e o total.

| Perfil de referência | Código | Salário (R$/mês) | Fator-k | Custo calculado (R$/h) |
| :--- | :--- | ---: | ---: | ---: |
| Desenvolvedor pleno | DESENV-02 | 11.023,35 | 2,03 | 139,86 |
| Analista de BI pleno | ABI-02 | 11.071,12 | 2,02 | 139,77 |
| Analista de negócios pleno | ANR-02 | 9.561,11 | 2,04 | 121,90 |
| Analista de testes pleno | ATQ-02 | 8.616,67 | 2,06 | 110,94 |

As horas abaixo são hipóteses explícitas a validar com um plano de implantação. Cada hora pertence a uma atividade e perfil; horas de operação mensal não entram neste investimento.

## Quantidades e cenários

**Piloto:** integrar os fluxos já versionados, preparar um ambiente assistido, conferir cubos e reports e treinar usuários-chave. **Produção de referência:** acrescentar endurecimento, implantação mais ampla e validação adicional. O segundo cenário não é a soma do primeiro com uma implantação nova: representa o investimento total alternativo a partir da mesma base existente.

| Atividade única | Perfil | Piloto (h) | Produção (h) | Premissa a validar |
| :--- | :--- | ---: | ---: | :--- |
| Integração, ajustes e implantação | Desenvolvedor | 160 | 224 | Escopo final de fontes, autenticação e infraestrutura. |
| Configuração inicial e passagem operacional | Desenvolvedor | 16 | 16 | Uma implantação por cenário, sem duplicar sustentação. |
| Modelo BI, reports e homologação visual | Analista de BI | 80 | 144 | Quantidade de visuais e regras aprovadas. |
| Treinamento ministrado | Analista de BI | 16 | 16 | Uma turma de usuários-chave; mais turmas exigem revisão. |
| Levantamento e aceite de requisitos | Analista de negócios | 40 | 64 | Disponibilidade dos responsáveis e mudanças de escopo. |
| Participação dos usuários no treinamento | Analista de negócios, como proxy de custo de oportunidade | 16 | 16 | Substituir pelo custo real dos participantes. |
| Testes, reconciliação e aceite técnico | Analista de testes | 40 | 80 | Cobertura de fontes e volume de dados de homologação. |
| **Horas totais de implantação** | | **368** | **560** | Somente trabalho inicial. |

Treinamento inclui quem ministra e quem participa: são horas de pessoas distintas. O custo de oportunidade dos participantes é uma aproximação conservadora, não desembolso contratual confirmado.
