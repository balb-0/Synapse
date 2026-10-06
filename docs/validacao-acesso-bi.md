# Validação de conexão e atualização no Power BI

Este registro atende BI-02, BI-05 e BI-06 e mantém o procedimento de DX-04.
O projeto consumidor é `powerbi/CentralPesquisasBI.pbip`, com sete partições
Parquet e dimensões calculadas. O consumidor recebe somente a geração
publicada; o DuckDB de ingestão permanece na máquina autorizada de carga.

## Procedimento reproduzível

1. Na máquina de carga, publique somente depois da
   [reconciliação analítica](reconciliacao-analitica.md). Registre o `load_id`
   em `--load-reference`, conforme [publicação e acesso](acesso-cubos-bi.md).
   Guarde a conferência de BI-05 contra o banco dessa mesma carga.
2. Copie a subpasta imutável indicada por `current.json` para uma pasta
   restrita no Windows. Ela contém `manifest.json` e sete Parquet.
   Confira hashes e contagens antes da conexão. Mantenha o pacote fora do Git.
3. Abra `powerbi/CentralPesquisasBI.pbip`. Em **Transformar dados > Gerenciar
   parâmetros**, configure `PastaPublicacaoBI` para a subpasta copiada, sem
   barra final. Use **Fechar e aplicar** e **Atualizar**. Preserve o parâmetro
   de exemplo no arquivo versionado; o caminho da máquina fica na cópia local.
4. Registre versão do Desktop, Windows, data com fuso, ID da geração,
   `load_reference`, caminho sanitizado e os erros de cada consulta.
   Execute `COUNTROWS` para as sete tabelas no modo de consulta DAX e um
   agregado por cubo, conforme [BI-05](refresh-final-bi05.md).
5. Compare cada número com o manifesto, os Parquet e consultas ao DuckDB da
   mesma carga. Teste médias ponderadas e estados indisponíveis conforme
   [especificação de medidas](especificacao-medidas-bi.md). Os vínculos dos visuais
   e sua aceitação são rastreados em RP-13/RP-14 e na auditoria do pacote
   integrado; eles não substituem as consultas às partições carregadas.
6. Para trocar a geração, copie o pacote novo inteiro para outra subpasta,
   altere `PastaPublicacaoBI` e repita aplicar, atualizar e as conferências.
   Alterar `current.json` no publicador não atualiza o parâmetro do relatório.
   Registre os IDs antigo/novo e confirme que os resultados mudaram conforme
   os respectivos manifestos. Uma cópia parcial deve falhar; não aceitar um
   refresh que mantenha silenciosamente o cache anterior.

## Evidência necessária para o aceite

As capturas devem mostrar projeto/versão, parâmetro com caminho sanitizado,
conclusão ou erro do refresh e resultados DAX das sete tabelas. Registre também
a troca entre duas gerações. Evite nomes de usuário, registros individuais,
IDs de pessoa/empresa, e-mails ou credenciais. Uma captura do dashboard com
dados sintéticos demonstra o visual; não prova qual geração foi importada.

| Etapa | Geração e execução | Resultado |
| :--- | :--- | :--- |
| BI-01 | Migração de duas páginas e 48 visuais | Estrutura versionada; aceitação visual do pacote integrado pendente |
| BI-02 | Fixture `synthetic-bi02-fixture` | Sete tabelas consultadas no Desktop real, partições processadas sem erro |
| BI-03/BI-04 | Pacote integrado `f068a01` | Projeção TOM com 128 itens/zero diferenças; médias e estoque do fixture consultados |
| BI-05 | Geração CB-16 `6b1eaa686aac43b18b6d6545e1c2c5f1` | Publicação, origem e refresh v3 conferidos; revisão visual final pendente |
| BI-06 | Refresh e troca de geração | Fixture e v3 consultados; troca registrada, falha de arquivo ausente observada; recuperação pendente |

Até completar as evidências de cada etapa, o respectivo aceite permanece
pendente. Card fechado, branch criada, pipeline ou recibo preenchido não
comprovam execução no Power BI Desktop.

## Tabelas e agregados a registrar

| Tabela | Linhas do manifesto | Linhas no Desktop | Agregado ou estado |
| :--- | :--- | :--- | :--- |
| `PUB_C01_CICLO` | 57 | 57 | 366 pesquisas, conforme o recibo v3 |
| `PUB_C02_PARTICIPACAO` | 32 | 32 | 17740 participações, conforme o recibo v3 |
| `PUB_C03_PIPELINE_MENSAL` | 0 | 0 | Sem fechamento observado; estoque indisponível |
| `PUB_C04_INSTRUMENTO` | 45 | 45 | 3186 associações pesquisa-pergunta |
| `PUB_QUALIDADE_CAMPO` | 64 | 64 | Linhas conferidas; KPI DAX por campo ainda não registrado |
| `PUB_QUALIDADE_RELACAO` | 8 | 8 | Linhas conferidas; KPI DAX por relação ainda não registrado |
| `PUB_QUALIDADE_DUPLICIDADE` | 5 | 5 | Linhas conferidas; KPI DAX por tabela ainda não registrado |

## Limites do contrato publicado

- C01 publica durações em dias corridos e a base válida de cada fase. Falta
  `flag_prorrogada`; taxa de prorrogação permanece indisponível.
- C02 conta ocorrências de participação, não empresas ou pessoas distintas.
  Não há chave pública para benchmark individual ou participação de mercado.
- C03 publica estoque observado por mês. Entradas e saídas são medidas
  operacionais fora do catálogo I01–I25, com motivo de indisponibilidade
  quando falta histórico de transições. Não recebem o identificador I05,
  que pertence à taxa de prorrogação.
- O pacote atual não distingue fechamento observado com estoque zero de
  ausência de fechamento quando ambos não produzem linhas C03. A publicação
  precisa preservar essa evidência antes do aceite desse caso; o consumidor
  não pode substituir a ausência por zero.
- C04 conta associações pesquisa-pergunta, não respostas ou respondentes.
- Parseabilidade e divergência de título não têm consulta publicada nesta
  geração. `DIM_INDICADORES_BLOQUEADOS` contém 18 entradas: 17 com status
  "Sem dado" e uma "Parcial". O catálogo registra os motivos; não implementa
  uma medida numérica vazia para cada entrada. As duas medidas individuais
  `Taxa de Prorrogacao` e `Representatividade` retornam texto com o motivo,
  conforme [sinalização](sinalizacao-indicadores-bloqueados.md).

## Tratamento de erro

Registre a mensagem, a tabela, a geração e a ação corretiva. Arquivo ausente,
hash divergente, tipo incompatível, expressão DAX inválida ou caminho ambíguo
interrompem o aceite. Corrija a origem ou o modelo, repita o refresh e as
consultas e preserve a evidência do erro e da correção.

## Ensaios executados e diagnóstico

O ensaio do pacote integrado `f068a01` executou em VM Windows com Power BI
Desktop `2.158.1177.0` em 06/10/2026 às 14:08:45 UTC, com relógio
sincronizado. As sete contagens do fixture foram 2/3/4/2/64/8/5 na ordem
C01, C02, C03, C04 e três tabelas de qualidade. As 13 partições do projeto
e duas automáticas de data estavam processadas sem erro. A comparação TOM
teve 128 itens e zero diferenças, dentro do escopo de projeção registrado.

Os recibos sintéticos de [BI-02](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/merge_requests/276),
[BI-03](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/merge_requests/278) e
[BI-04](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/merge_requests/290)
registram fonte do pacote, hashes, contagens, versão e consultas. A execução
foi automatizada no Desktop real; não há declaração de operação humana.
A igualdade semântica não identifica o commit exato dentro do engine.

As capturas históricas de diagnóstico mostram falhas anteriores de
[coluna no relacionamento](evidencias/bi-desktop/erro-coluna-calculada.png) e
[valor de direção de filtro](evidencias/bi-desktop/erro-direcao-filtro.png).
São recortes sem dados de origem ou credenciais; não identificam a revisão
exata do projeto e não são capturas do ensaio integrado aprovado. O recibo
posterior registra o modelo corrigido processado e consultado.

A publicação v3 está conferida em CB-16. O refresh e a troca de geração
têm os recibos adicionais abaixo. A falha de arquivo ausente foi observada; sua recuperação e a revisão
visual final continuam pendentes.

## Troca do fixture para a geração v3

O [recibo de troca](evidencias/bi06/troca-fixture-v3.json) liga as execuções
das 14:08:45 e 14:15:30 UTC de 06/10/2026. O parâmetro da cópia privada
do PBIP mudou de `C:\BI\<pacote>\data\g1` para
`C:\BI\<pacote>\data\v3`; o projeto foi reaberto e atualizado. Os
caminhos desta página estão sanitizados. Em ambos os estados, o arquivo
local do parâmetro e sua expressão no modelo ativo foram conferidos.

O [recibo v3](evidencias/bi06/desktop-v3-antes-ajustes-relatorio.json) registra
57/32/0/45/64/8/5 linhas nas sete publicações e totais C01/C02/C04 de
366/17740/3186. São diferentes de 2/3/4/2/64/8/5 e 4/4/3 do fixture,
conforme seus manifestos. A geração v3 é
`6b1eaa686aac43b18b6d6545e1c2c5f1`, carga
`afcde424-45e8-457b-8793-bf0866d142b2`. C03 ficou sem fechamento observado,
com estoque e fluxos indisponíveis.

Esta rodada usou o pacote `f068a01` e antecede os ajustes de títulos do
relatório. Confirma conexão, troca e atualização do modelo daquela revisão.
A falha de arquivo ausente está registrada abaixo. Sua recuperação e as
capturas finais serão registradas depois da execução.

## Falha de arquivo ausente observada

Ao remover `PUB_C01_CICLO.parquet` somente da cópia privada Windows da geração
v3 e clicar Atualizar, o Desktop exibiu sete consultas bloqueadas e o erro
"File or Folder: Could not find file" para C01. O
[recibo do diagnóstico](evidencias/bi06/arquivo-ausente-v3.json) registra a
observação em 06/10/2026 às 14:19:20 UTC; a
[captura do diálogo](evidencias/bi06/arquivo-ausente-v3.png) mostra a falha
sem dados de origem ou credenciais. O pacote imutável da publicação ficou
preservado.

Essa falha não foi aceita como refresh bem-sucedido. A restauração do arquivo
e uma nova atualização com consultas ao engine ainda aguardam o recibo de
recuperação neste registro. Uma consulta ao cache anterior, sozinha, não
comprova que a atualização com o arquivo ausente funcionou.
