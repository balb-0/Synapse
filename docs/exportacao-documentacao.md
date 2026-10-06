# PDF da documentação principal

O arquivo [documentacao-principal.pdf](assets/documentacao/documentacao-principal.pdf)
exporta **todo o conteúdo de [projeto.md](projeto.md)**, incluindo tabelas,
imagens locais, referências, limitações e anexos presentes nesse documento.
Os documentos ligados por links continuam separados; a exportação não os incorpora.
Os PDFs de diagramas existentes em `docs/assets/diagramas/` não substituem esta publicação.

## Gerar e conferir

Execute na raiz do repositório, com Python 3.12 e as bibliotecas de sistema
Pango e Fontconfig disponíveis. Em Debian/Ubuntu, instale `libpango-1.0-0`,
`libpangoft2-1.0-0` e `fontconfig`; `poppler-utils` permite a inspeção visual.
As dependências de exportação ficam separadas das dependências do ETL:

```sh
python -m venv /tmp/g05-docs-venv
/tmp/g05-docs-venv/bin/pip install -r requirements-docs.txt
/tmp/g05-docs-venv/bin/python scripts/docs/export_documentation.py
/tmp/g05-docs-venv/bin/python scripts/docs/export_documentation.py --check
python -m unittest discover -s tests/docs -v
```

Versione o PDF e seu manifesto juntos após mudar a fonte, uma imagem, uma fonte
tipográfica, o exportador ou as dependências de exportação. O comando `--check`
não escreve arquivos e falha se o documento estiver desatualizado, faltar uma
imagem/arquivo ligado, existir âncora interna inválida ou o hash do PDF divergir.
O comando de exportação recusa imagens externas e não executa JavaScript.

## Proveniência e limites

O [manifesto](assets/documentacao/documentacao-principal.manifest.json) registra
SHA-256 de cada entrada renderizada, versão dos componentes principais, revisão
Git da fonte, número de páginas e SHA-256 do PDF. A revisão é a última que alterou
`docs/projeto.md`, evitando a dependência circular de incluir no PDF o SHA do próprio
commit que publica o PDF. O `--check` compara os hashes da fonte e entradas atuais,
inclusive mudanças ainda não commitadas.

As fontes Noto Sans, Noto Sans Mono, Noto Sans Math, Noto Sans Symbols 2 e um
subconjunto de Noto Color Emoji (U+26A0 e U+26D4) estão versionadas junto ao artefato, sob
[SIL Open Font License](assets/documentacao/fonts/OFL.txt), para manter acentos e
símbolos sem depender das fontes instaladas na máquina. O formato A4 horizontal
acomoda tabelas extensas; cabeçalhos de tabelas e paginação permanecem na exportação.
As definições Mermaid são preservadas integralmente como código, identificadas
no PDF. Imagens dos diagramas já presentes na fonte são incorporadas. A exportação
não acrescenta diagramas renderizados a partir de fontes Mermaid.

Os links entre seções do documento são internos ao PDF. Links para outros
arquivos apontam para a revisão da fonte no GitLab e podem exigir permissão de acesso.
Os links externos permanecem com seus destinos originais; o exportador não testa
a disponibilidade de serviços externos. Gerar o PDF não valida as afirmações do
documento nem comprova execução de testes, acesso ao Desktop ou aceite humano.

Todas as versões Python instaladas precisam coincidir com `requirements-docs.txt`;
o exportador confere essa igualdade antes de gerar ou validar o PDF. Bibliotecas de sistema
podem alterar paginação ou bytes entre plataformas. O critério de atualidade é
a integridade das entradas e do artefato publicado, e não igualdade universal
de bytes entre sistemas operacionais.

## Inspeção antes de publicar

```sh
mkdir -p /tmp/g05-docs-pages
pdftoppm -r 90 -png docs/assets/documentacao/documentacao-principal.pdf /tmp/g05-docs-pages/page
pdftotext docs/assets/documentacao/documentacao-principal.pdf /tmp/g05-docs-pages/documento.txt
```

Confira todas as páginas renderizadas, com atenção a tabelas largas, imagens,
blocos Mermaid, acentos e transições de seção. Compare também os títulos e o fim
do texto extraído com a fonte. O `--check` verifica integridade e vínculos; a revisão
visual continua necessária para encontrar cortes, sobreposições ou texto ilegível.
