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
   [especificação de medidas](especificacao-medidas-bi.md). Tabelas visuais
   ainda vinculadas ao protótipo dependem de RP-13/RP-14; elas não substituem
   a consulta das partições efetivamente carregadas.
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
| BI-01 | Migração de duas páginas e 48 visuais | Estrutura e recursos conferidos; campos de RP-13/RP-14 pendentes |
| BI-02 | Fixture `synthetic-bi02-fixture` | Sete arquivos conferidos em Python; registro de importação no Desktop em preparação |
| BI-03/BI-04 | Modelo corrigido | Verificações estruturais e referências independentes; execução DAX no Desktop a registrar |
| BI-05 | Geração final CB-16 | ID final e aceite da origem ainda não identificados |
| BI-06 | Refresh e troca de geração | Capturas e números do Desktop ainda a registrar |

Até completar as evidências de cada etapa, o respectivo aceite permanece
pendente. Card fechado, branch criada, pipeline ou recibo preenchido não
comprovam execução no Power BI Desktop.

## Tabelas e agregados a registrar

| Tabela | Linhas do manifesto | Linhas no Desktop | Agregado ou estado |
| :--- | :--- | :--- | :--- |
| `PUB_C01_CICLO` | A registrar | A registrar | Soma de `qtd_pesquisas` versus contagem de `FATO_CICLO_PESQUISA` |
| `PUB_C02_PARTICIPACAO` | A registrar | A registrar | Soma de `qtd_participacoes` versus contagem de `FATO_PARTICIPACAO` |
| `PUB_C03_PIPELINE_MENSAL` | A registrar | A registrar | Estoque de um fechamento observado, sem somar meses; ausência de fechamento fica indisponível |
| `PUB_C04_INSTRUMENTO` | A registrar | A registrar | Soma de `qtd_perguntas` versus contagem de `FATO_PESQUISA_PERGUNTA` |
| `PUB_QUALIDADE_CAMPO` | A registrar | A registrar | Numerador e denominador por campo |
| `PUB_QUALIDADE_RELACAO` | A registrar | A registrar | Correspondências e chaves informadas por relação |
| `PUB_QUALIDADE_DUPLICIDADE` | A registrar | A registrar | Linhas e chaves distintas por tabela |

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
  geração. Indicadores bloqueados mantêm valor numérico em branco e motivo
  textual, conforme [sinalização](sinalizacao-indicadores-bloqueados.md).

## Tratamento de erro

Registre a mensagem, a tabela, a geração e a ação corretiva. Arquivo ausente,
hash divergente, tipo incompatível, expressão DAX inválida ou caminho ambíguo
interrompem o aceite. Corrija a origem ou o modelo, repita o refresh e as
consultas e preserve a evidência do erro e da correção.
