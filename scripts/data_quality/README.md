# Perfilamento local das bases

`profile_csv.py` valida o contrato de entrada e gera somente agregados
determinísticos. O diretório que contém os CSVs é somente leitura para o
script; o resultado deve ficar em diretório temporário ou em um diretório de
artefatos que não seja publicado com dados brutos. O dicionário é obrigatório
na interface de linha de comando e seu cabeçalho, nove variáveis, conteúdo
mínimo e alegações de nulos são validados; um dicionário arbitrário falha antes
da gravação das saídas.

O manifesto usa `teste.csv` como alias conceitual local de `respostas.csv`.
Esse alias documenta a origem recebida sem renomear, copiar ou publicar o CSV.
A unidade de análise de `respostas` é um elemento atômico de resposta de um
respondente para uma pergunta de uma pesquisa; uma linha não equivale a um
questionário completo.

Exemplo, a partir da raiz do repositório:

```bash
python3 scripts/data_quality/profile_csv.py \
  --input-dir /caminho/local/context/csv \
  --output-dir /tmp/perfil-g05 \
  --dictionary "/caminho/local/context/Dicionario_Variaveis_Respostas_Grupo6.xlsx - Dicionário.csv"
```

Saídas: `resumo.csv`, `campos.csv`, `dominios.csv`, `relacionamentos.csv`,
`datas.csv`, `coerencia_temporal.csv`, `identidades.csv`,
`nulos_condicionais.csv`, `percentuais.csv`, `denormalizados.csv`,
`dicionario_validacao.csv` e `manifesto_aplicado.json`. O perfilador reporta
chaves incompletas separadamente da unicidade, reconcilia
`questoes.pesquisa_titulo` com `pesquisas.titulo`, e classifica nulos por tipo
de questão como aplicáveis, não aplicáveis, condicionais ou inesperados.
Percentuais informam parseáveis, inválidos e fora de `[0,100]`.

Sentinelas são configuradas por campo no manifesto: `s/i`, `NA`, `N/A` e
`n/a` podem ser nulos semânticos; `-` só é sentinela em campos configurados
(por exemplo, `empresas.Associado`) e permanece texto em `respostas.valor`.
As contagens física, de sentinelas e semântica ficam separadas. Assim, o
dicionário informa 8.309 nulos em `valor`, enquanto o CSV tem 8.307 vazios e
2 `NA`; a soma semântica é 8.309. CSVs de resposta, nomes de empresas,
e-mails e textos livres não são gravados nas saídas; domínios de resposta não
são materializados.

As porcentagens usam uma casa decimal, vírgula decimal e sufixo `%`. Datas e
horas são tratadas sem conversão de fuso: a origem não informa timezone, que
fica registrada no manifesto, e a coerência temporal cobre somente pares com
ambos os valores preenchidos e parseáveis. O processo falha com código 2 e
mensagem explícita em caso de arquivo ausente, cabeçalho incompatível, linha
com número de campos inválido, UTF-8 inválido, dicionário arbitrário ou
dicionário informado inexistente.

Os limiares de aceitação são propostas de governança, não evidência de
segurança ou autorização para publicar qualquer dado.
