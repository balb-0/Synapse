# Fontes e dependências dos artefatos da Sprint 1

Este mapa registra a origem de cada bloco dos três artefatos da Sprint 1:
contexto e requisitos, modelagem quantitativa e Data Model Canvas. Ele separa
fonte primária, evidência observada e conteúdo proposto para evitar que uma
síntese do grupo seja citada como confirmação do parceiro.

## Como ler o mapa

- **Confirmada pelo parceiro:** afirmação atribuída a um artefato primário do parceiro. Nesta cópia do repositório, a classificação só pode ser auditada quando o arquivo primário estiver disponível.
- **Observada nos dados ou no código:** resultado reproduzível nos CSVs, JSON ou scripts.
- **Inferência:** conclusão compatível com as evidências, mas não confirmada diretamente.
- **Proposta da equipe:** decisão de desenho ou resultado futuro ainda sujeito a validação ou implementação.
- **Pendente:** informação cuja fonte não está disponível ou cuja decisão ainda não foi registrada.

## Mapa de fontes

| Fonte | Conteúdo suportado | Artefato / seção | Tipo de evidência nesta cópia | Limitações |
| :--- | :--- | :--- | :--- | :--- |
| TAPI [[1]](projeto.md#7-referências) | contexto, objetivos, escopo macro e resultados pretendidos | contexto e requisitos; §§3, 4 e 6 | Pendente de auditoria primária | `context/Tapi-sinduspharma.txt` é citado, mas não está no checkout |
| Arquitetura de Negócio [[2]](projeto.md#7-referências) | atores, processo atual, sistemas e necessidades de integração | contexto e requisitos; §§4.0 e 6 | Pendente de auditoria primária | arquivo citado não está no checkout |
| Data Model Canvas em PDF [[3]](projeto.md#7-referências) | baseline de Negócio, Consumo Analítico e Governança Corporativa | DMC; §5.1 e `docs/dmc.json` | Pendente de auditoria primária | PDF citado não está no checkout; somente o JSON e a distinção registrada na §5.1 podem ser observados |
| JTBD [[13]](projeto.md#7-referências) | necessidades, públicos e decisões esperadas | contexto, perguntas de negócio e consumo analítico | Pendente de auditoria primária | arquivo citado não está no checkout |
| Problem Canvas [[14]](projeto.md#7-referências) | dores, causas, impactos, necessidades, públicos, governança e riscos | contexto, requisitos e matriz de evidências | Pendente de auditoria primária | HTML citado não está no checkout |
| seis CSVs locais | entidades, grãos, cardinalidades, nulos, chaves e relações | modelagem quantitativa; §§4.0.1, 5.2–5.6 | Observada nos dados | contêm campos identificáveis e permanecem fora do Git |
| dicionário de respostas [[12]](projeto.md#7-referências) | semântica e regras dos nove campos de `respostas.csv` | modelagem quantitativa; §5.3 | Pendente de auditoria primária | arquivo citado não está no checkout; o perfilador exige sua presença |
| `scripts/data_quality/` | método de perfilamento, regras, manifesto e testes | modelagem quantitativa; §§5.3–5.6 | Observada no código | não autoriza publicação nem substitui a decisão do parceiro |
| `docs/projeto.md` | síntese consolidada, PB01–PB13, RF01–RF13, I01–I25 e C01–C04 | todos os artefatos | Evidência documental derivada | deve apontar até a origem; não é fonte primária de si próprio |
| `docs/dmc.json` | schema 1, conteúdo corporativo e estado dos cards | Data Model Canvas | Observada no arquivo | baseline atual possui dois cards de cubo vazios |
| GitLab | escopo das issues, decisões de implementação, commits e revisões | gestão e auditabilidade; issues #1–#3, #8, #9, #21–#25 e #40–#52 | Confirmada no processo do projeto | não confirma fatos do parceiro; a evidência concreta deve citar issue, branch, commit ou MR |

## Dependências entre artefatos

```text
TAPI + Arquitetura de Negócio + JTBD + Problem Canvas
  → contexto, dores, necessidades, atores e processo
  → matriz de evidências do Problem Canvas
  → escopo, fluxo de valor e consumo analítico
  → requisitos e perguntas de negócio
  → indicadores e formas de consumo
  → cubos e dimensões
  → Data Model Canvas

CSVs + dicionário + perfilamento reproduzível
  → entidades, grãos e relações observáveis
  → métricas viáveis e limitações
  → modelagem dimensional
  → cubos e Data Model Canvas
```

| Dependência | O que ela impede quando ausente | Tratamento adotado |
| :--- | :--- | :--- |
| Fonte primária do parceiro | confirmar escopo, processo, papéis e dores | manter a referência e marcar a auditoria como pendente; não promover síntese a fato |
| Universo de convidados ou elegíveis | calcular adesão e engajamento | indicadores ficam indisponíveis, nunca iguais a zero |
| Identidade canônica entre sistemas | unir participação, cliente e resposta individual | preservar chaves de origem e não inferir vínculos por semelhança |
| Fonte autoritativa de participação de mercado | homologar representatividade | manter valores em reconciliação e bloquear o indicador conflitante |
| Logs, versões e decisões de publicação | calcular auditoria, atualização e publicação | tratar I21 e I23–I25 como dependências futuras |
| Definição dimensional das Tasks 43–47 | preencher os cubos do canvas | revisar branches oficiais e reconciliar com C01–C04 antes da exportação |

## Fronteiras de responsabilidade

O mapa não confirma a natureza sintética ou real dos CSVs, não define política
de acesso e não preenche lacunas das fontes primárias por inferência. Os dados
brutos continuam ignorados; somente agregados sem identificação podem ser
versionados depois dos controles aplicáveis.
