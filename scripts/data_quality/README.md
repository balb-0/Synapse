# Perfilamento local das bases

`profile_csv.py` valida o contrato de entrada e gera somente agregados
determinísticos. O diretório que contém os CSVs é somente leitura para o
script; o resultado deve ficar em diretório temporário ou em um diretório de
artefatos que não seja publicado com dados brutos.

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
`datas.csv`, `coerencia_temporal.csv`, `identidades.csv` e
`manifesto_aplicado.json`. CSVs de resposta, nomes de empresas, e-mails e
textos livres não são gravados nas saídas; domínios de resposta não são
materializados. As porcentagens usam uma casa decimal, vírgula decimal e
sufixo `%`. O processo falha com código 2 e mensagem explícita em caso de
arquivo ausente, cabeçalho incompatível, linha com número de campos inválido,
UTF-8 inválido ou dicionário informado inexistente.

Os limiares de aceitação são propostas de governança, não evidência de
segurança ou autorização para publicar qualquer dado.
