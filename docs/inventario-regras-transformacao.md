# Inventário de regras de transformação

MG-01, relacionado ao card #170. Base inspecionada: `aa23f32` de `develop`.
Este inventário distingue o contrato acadêmico, o que foi observado nos dados
e as decisões técnicas propostas para MG-02 a MG-11.

## Fontes e autoridade

| Fonte | Uso | Limite |
| --- | --- | --- |
| Enunciado da Sprint 3 fornecido pelo aluno | Transformar antes da carga no ClickHouse; tratamento de inválidos, tipos, nulos, consistência e metadados | Não exige enriquecimento analítico nem implantação de cubos |
| [Inventário LN-01](inventario-fontes-etl.md) | Seis fontes e descrição da v3 | V3 ainda não disponível no diretório local inspecionado |
| [Contrato LN-02](contrato-lote-extraido.md) | `ExtractedBatch`, checkpoint candidato e metadados | Confirmar checkpoint somente após persistência de aceitos e rejeitados |
| [Manifesto de qualidade](../scripts/data_quality/manifest.json) | Campos recebidos, sentinelas específicas, relações e nulos condicionais | Perfilamento não equivale a transformação implementada |
| [Governança](Governança-de-Dados-do-Projeto.md), seções 2 e 3 | Rejeição, reconciliação, privacidade, catálogo e rastreabilidade | Metas e papéis propostos não são homologação do parceiro |
| TAPI, arquitetura, dicionário e seis CSVs externos em `/ultimo/context` | Semântica e verificação local da versão anterior | Dados brutos e registros individuais não entram no Git |

## Regras inventariadas

| ID | Regra | Estado e fundamento | Tratamento previsto |
| --- | --- | --- | --- |
| R01 | Seis fontes com campos declarados | Confirmada pelo contrato do ETL e pelos cabeçalhos locais | Schema explícito por fonte; rejeitar campos desconhecidos preenchidos |
| R02 | CSV UTF-8/BOM, separador `;`, nomes com espaços e acentos | Observada no snapshot local | Renomear por mapa; preservar origem em linhagem |
| R03 | Onze colunas sem nome em pesquisas | Observada no cabeçalho bruto | Descartar somente quando vazias; conteúdo inesperado deve falhar |
| R04 | IDs não são medidas | Confirmada pelo dicionário | Normalizar inteiros sem conversão por float; rejeitar fração e sentinela obrigatória |
| R05 | Percentuais em pontos percentuais | Observada: vírgula decimal e `%` | Decimal finito no intervalo 0 a 100; não inferir proporção nem trocar ausência por zero |
| R06 | Datas e horários sem fuso declarado | Pendente de confirmação pelo parceiro | Datas civis continuam datas; timestamp local exige fuso configurado, sem usar o fuso da máquina |
| R07 | Campos vazios e sentinelas têm semântica por campo | Confirmada no manifesto | Não tratar todo `NA` ou `-` textual como nulo global |
| R08 | Obrigatoriedade de resposta depende da questão | Confirmada pelo dicionário e manifesto | Matriz exige linha/coluna; aberta e numérica exigem valor; seleção exige alternativa |
| R09 | Uma resposta é um elemento atômico | Confirmada no dicionário | Preservar elementos diferentes da mesma pessoa/pergunta |
| R10 | `respondent_id` não tem ponte comprovada com `id_cliente` | Pendente nos documentos do parceiro | Não construir essa relação nem inferi-la por igualdade ou título |
| R11 | IDs de pesquisas têm lacunas entre fontes | Observada no snapshot anterior | Referência ausente resulta em quarentena; não inventar pesquisa |
| R12 | Duplicata técnica difere de atualização conflitante | Proposta técnica derivada do requisito de idempotência | Mesma identidade e conteúdo: duplicata; conteúdo divergente: conflito, sem vencedor arbitrário |
| R13 | Participação pode ter chave incompleta | Observada no inventário LN-01 | Preservar eventos identificáveis pela origem; não colapsar pessoas ausentes em uma participação fictícia |
| R14 | Rejeitados precisam de motivo e linhagem | Confirmada no enunciado e governança | Código estável, campo, fonte, lote, execução, checksum; nenhum valor bruto em logs |
| R15 | Data de ingestão não é data da fonte | Confirmada pela ausência de data de extração | Carimbo UTC separado das datas de negócio e fora da chave de deduplicação |
| R16 | Schema de destino precisa ser verificável | Confirmada no enunciado | Contrato tipado e teste de compatibilidade; integração da carga depende de MC-03 |

## Divergência de versões

O snapshot local tem 366 pesquisas, 779 empresas, 5.430 clientes, 18.735
participações, 231 questões e 20.607 respostas. `teste.csv` é o alias local
de respostas, comprovado pelo cabeçalho e dicionário. O inventário LN-01
descreve v3 com 3.297 questões e 281.835 respostas. Os volumes antigos não
serão usados como limite de domínio nem como prova de execução da v3.

## Dependências e decisões pendentes

LN-01, LN-02 e LN-03 estão em `develop`. As branches de MG-02 a MG-10
existem, mas não possuem commits exclusivos contra essa base na inspeção.
Estado fechado de card não comprova implementação ou revisão.

AN-03, MC-03, KP-07, OV-05 e VB-03 precisam de evidências de contrato ou
implementação para encerrar a integração. A transformação pode ser validada
com o contrato LN-02 e massa sintética própria; isso não comprova a carga,
orquestração ou revisão por outra pessoa. A matriz final deve manter essa
distinção.
