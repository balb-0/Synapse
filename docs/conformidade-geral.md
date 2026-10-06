# Resposta ao feedback de conformidade geral

Esta matriz relaciona os 37 critérios recebidos em 06/10/2026 às fontes do G05. Ela registra evidências e limites de verificação, sem recalcular a nota ou substituir a avaliação institucional. Base documental da conferência: `develop` em `c2ebb02`, integrada às entregas anteriores de BI/pipeline e às correções CF-01 a CF-05. CF-06 resolve conflitos de integração e regenera o PDF e sua proveniência neste snapshot. O estado de `develop` depende dos merges; a presença nesta branch não comprova publicação no destino.

## Como reproduzir a conferência

Leia o [portal](index.md), execute os comandos do [README](../README.md) e confira o [runbook](runbook-execucao.md). A estrutura é organizada por responsabilidade; `tests/` e `docs/` já existem separadamente. Não foi fornecido um template obrigatório de pastas para esta revisão. A camada de apresentação é Power BI, não uma aplicação web que exija React ou Vue.

| # | Critério recebido | Evidência e tratamento | Limite ou verificação necessária |
| :--- | :--- | :--- | :--- |
| 1 | Nome do projeto | [README](../README.md), título principal. | Conferir também o título do documento principal. |
| 2 | Nome do grupo | README, seção Nome do Grupo: Synapse. | G05 é o identificador acadêmico do grupo. |
| 3 | Integrantes descritos | README e [projeto](projeto.md), sete nomes. | Não inferir responsabilidades por autor de commit. |
| 4 | Links dos integrantes | README, seção Integrantes, perfis LinkedIn. | LinkedIn pode exigir login; URL presente não garante disponibilidade pública permanente. |
| 5 | Descrição curta | README distingue ETL local, camada analítica, BI e objetivo futuro de nuvem. | Provisionamento produtivo não é declarado entregue. |
| 6 | Estrutura de pastas | README, árvore real com `src/`, `tests/`, `docs/`, `sql/`, `powerbi/` e `scripts/`. | Sem template obrigatório fornecido, não afirmar adesão a um modelo desconhecido. |
| 7 | Instalação com versão | README, [Dockerfile](../Dockerfile), [requirements](../requirements.txt) e [dependências de desenvolvimento](../requirements-transformation-dev.txt). | Referência Python 3.12; versões posteriores precisam de gates. Imagens MinIO `latest` não têm reprodução por digest. |
| 8 | Histórico de lançamentos | README, releases 0.1.0 a 0.4.0 e 0.5.0 explicitamente em andamento. | Histórico de sprint não equivale a tag Git ou release publicada. |
| 9 | Histórico adequado | Datas e escopo por sprint no README. | A Sprint 5 não é apresentada como release concluída. |
| 10 | Licença | README, CC BY 4.0 com link oficial. | Licença do repositório não autoriza divulgar bases restritas. |
| 11 | Inteli na licença | README, instituição e link institucional explícitos. | Inteli é a instituição; Synapse é o grupo. |
| 12 | Grupo/integrantes na licença | README, atribuição Synapse (G05), Inteli e sete integrantes com nomes e links no bloco da licença. | Os nomes completos também constam na seção Integrantes. |
| 13 | Links na licença | Links do Inteli, da licença e dos sete integrantes no bloco de atribuição. | Restrições externas de acesso continuam possíveis. |
| 14 | Referências externas | [Referências](referencias.md) e [projeto, seção 7](projeto.md#7-referências). | Documentação `stable` pode mudar; execução usa dependências fixadas. |
| 15 | Remoção de template não utilizado | README descreve este projeto e seus comandos. | Fichas de sessões ainda não executadas são instrumentos de coleta, não resultado preenchido. |
| 16 | README coerente com repositório | Árvore, comandos e links conferidos contra arquivos versionados. | Componentes presentes não comprovam integração ou operação produtiva. |
| 17 | Requisitos declarados | README diferencia execução, desenvolvimento, análise e Desktop Windows. | Dependências exploratórias têm escopo separado do ETL. |
| 18 | Execução/instalação | README e runbook: ambiente virtual, dependências, Compose e suíte. | Executar serviços depende de Docker e configuração; esta revisão documental mantém os serviços desligados. |
| 19 | Ausência de dados sensíveis nas fontes | [Gestão de configuração](gestao-configuração.md), `.gitignore` e dados sintéticos em `tests/fixtures/` e `scripts/orchestration/fixtures/`. | Ignorar dados reais é política preventiva, não prova absoluta sobre histórico Git. |
| 20 | Ausência de dados sensíveis nos artefatos | README exige revisão de capturas, PDF, caches e gerações; [decisão de consumo](decisao-consumo-cubos.md) restringe publicação. | Agregado não significa anonimizado; ausência de CSV real não certifica todos os binários ou commits históricos. |
| 21 | Código-fonte | [`src/`](../src/) contém ETL e relatório legado. | Dados reais ficam fora do Git. |
| 22 | Organização mínima | [`src/etl/`](../src/etl/) separa extração, transformação, carga, análise e orquestração. | Organização por pacote não prova ausência de acoplamento interno. |
| 23 | Frontend quando aplicável | [`powerbi/`](../powerbi/) e [`src/pbir dash/`](../src/pbir%20dash/) são a apresentação PBIP/PBIR/TMDL. CF-02 documenta esse papel no [guia Power BI](../powerbi/README.md). | Não há requisito demonstrado de frontend web separado. |
| 24 | Lógica da aplicação | [`src/etl/`](../src/etl/) e entrypoints em [`scripts/`](../scripts/). | Scripts exploratórios têm instruções próprias. |
| 25 | Banco com README | CF-02 acrescenta [README em `sql/duckdb/`](../sql/duckdb/README.md) com as quatro DDLs e procedimento. | DuckDB é arquivo embutido; não há servidor de banco a provisionar. |
| 26 | Configuração produtiva | [`.env.example`](../.env.example), Compose e runbook explicam configuração local. | O exemplo não comprova ambiente produtivo; credenciais locais, TLS, distribuição e provisionamento exigem decisão própria. |
| 27 | Docs na raiz | [`docs/`](./) contém documento principal, contratos, governança, ADRs e evidências. | Insumos restritos permanecem externos. |
| 28 | Documentação acessível | README usa links relativos para o [portal](index.md); entrada por atividade, ADRs e comandos. | GitLab pode exigir autenticação institucional. |
| 29 | Markdown existente | Documento principal, portal, contratos e ADRs são `.md`. | PDF é uma exportação, Markdown continua a fonte. |
| 30 | Links funcionais e sem restrição | Validação dos destinos locais e referências externas listadas em CF-01. | Não prometer disponibilidade pública dos perfis, do GitLab ou de fontes privadas. |
| 31 | Formatação mínima | Títulos, tabelas, blocos de código e links nos documentos; CF-03 inclui exportação integral, conferência de páginas renderizadas e proveniência verificável. | Texto extraído do PDF sozinho não prova layout correto. |
| 32 | Seções principais preenchidas | [Projeto](projeto.md), seções 1 a 8: contexto, objetivos, arquitetura, modelagem, requisitos/governança, referências e resultados. | Metas futuras e tarefas humanas pendentes não podem ser convertidas em evidência executada. |
| 33 | Arquivos temporários removidos | `.gitignore` separa bancos, bases reais, caches e ambientes locais. | Não remover artefato histórico útil apenas por não ser código executável; não certificar todo histórico com essa regra. |
| 34 | PDF da documentação principal | CF-03 exporta `docs/projeto.md` integralmente em [PDF](assets/documentacao/documentacao-principal.pdf), com [gerador/verificação](exportacao-documentacao.md) e manifesto. | PDFs de fluxogramas já existentes não atendiam esse critério. Exportação precisa ser regenerada quando a fonte mudar. |
| 35 | Repositórios auxiliares | README e [referências](referencias.md) declaram não haver auxiliar obrigatório na configuração entregue. | Não inventar repositório para preencher critério; ferramentas externas não são projetos complementares do grupo. |
| 36 | Arquitetura detalhada | [ADRs](adrs/index.md), cinco visões ISO/IEC 10746 e [UML](assets/uml/) no portal. | Estado “proposto” de uma ADR é preservado; diagramas devem acompanhar o fluxo da versão avaliada. |
| 37 | Testes e massas formais | [`tests/`](../tests/) por domínio, fixtures sintéticas e testes de integração/e2e; CF-02 acrescenta [guia específico](../tests/README.md). | Teste com fixture não substitui conferência Desktop ou sessão humana; `skip` não é aprovação. |

## Entregas e rastreabilidade

- [CF-01, card #341](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/issues/341): README, portal, referências e esta matriz.
- [CF-02, card #342](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/issues/342): guias específicos de banco, apresentação e testes.
- [CF-03, card #343](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/issues/343): PDF integral, geração e validação.

- [CF-04, card #344](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/issues/344): fechamento C03 observado vazio e reuso de publicação.
- [CF-05, card #345](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/issues/345): completude física de preenchimento e bloqueio explícito de I16.
- [CF-06, card #346](https://git.inteli.edu.br/graduacao/2026-2a/t13/g05/-/issues/346): integração, resolução dos conflitos e PDF final.

Cada card recebe o link da MR correspondente e cada MR aponta para o card. A conclusão desta correção documental não registra aceite de sessões S1–S4, teste humano novo ou publicação produtiva. Essas provas têm tarefas e evidências próprias.
