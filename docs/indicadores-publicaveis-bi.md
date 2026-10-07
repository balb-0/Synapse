# Indicadores publicáveis, bloqueados e motivo — camada BI

Este documento cumpre a DX-01: separa, para os indicadores já levantados em
[`dmc.md`](dmc.md) (seção 1.4, catálogo I01–I25), o que é **calculável a
partir do que chega ao Power BI**, o que **exige normalização** e o que
**está sem dado disponível**, com o motivo de cada bloqueio. `dmc.md`
classifica os indicadores contra a camada de dados completa (o grão fino dos
quatro cubos, `docs/contrato-fisico-cubos.md`); este documento reclassifica
os mesmos indicadores contra o que efetivamente sai publicado para o Power BI
— os quatro Parquet de
[`docs/acesso-cubos-bi.md`](acesso-cubos-bi.md) (`PUB_C01_CICLO`,
`PUB_C02_PARTICIPACAO`, `PUB_C03_PIPELINE_MENSAL`, `PUB_C04_INSTRUMENTO`) mais
os três artefatos de qualidade publicados por
[`src/etl/analytics/publish.py`](../src/etl/analytics/publish.py)
(`PUB_QUALIDADE_CAMPO`, `PUB_QUALIDADE_RELACAO`, `PUB_QUALIDADE_DUPLICIDADE`,
ver DX-09).

As duas classificações divergem porque o publicador agrega os cubos por
área/status/tipo/mês antes de exportar: qualquer indicador que exija grão de
pesquisa, empresa ou pessoa individual, ou uma coluna que a consulta de
publicação não seleciona, fica indisponível na camada BI mesmo quando
`dmc.md` já o registra como calculável na camada de dados.

## Como ler a tabela

- **Camada de dados**: classificação de `dmc.md` (contra o cubo de grão
  fino).
- **Camada BI**: classificação real contra os sete arquivos publicados.
- **Fonte publicada**: arquivo e coluna(s) que sustentam o indicador quando
  calculável.
- **Motivo do bloqueio (BI)**: preenchido só quando a camada BI é mais
  restritiva que a camada de dados, ou quando ambas já bloqueiam pelo mesmo
  motivo documentado em `dmc.md`.

## Portfólio e ciclo (C01)

| ID | Indicador | Camada de dados | Camada BI | Fonte publicada | Motivo do bloqueio (BI) |
| :-- | :-- | :-- | :-- | :-- | :-- |
| I01 | Pesquisas no portfólio | Calculável | **Calculável** | `PUB_C01_CICLO.qtd_pesquisas` | — |
| I02 | Distribuição do portfólio | Calculável | **Calculável** | `PUB_C01_CICLO.qtd_pesquisas` por área/status/tipo | — |
| I03 | Cobertura dos marcos | Calculável | **Parcial** | `PUB_C01_CICLO.qtd_*_disponivel` | Só cobre os quatro pares de datas usados nas durações (validação, coleta, tabulação, ciclo total); cobertura de um marco isolado (ex.: só `data_aprov`) não é publicada. |
| I04 | Tempo entre marcos | Calculável | **Calculável, só média** | `PUB_C01_CICLO.soma_dias_*` / `qtd_*_disponivel` | O arquivo só traz soma e contagem; mediana exigiria o valor por pesquisa, que não é publicado (ver DX-03, regra de mediana). |
| I05 | Taxa observada de prorrogação | Calculável | **Sem dado** | — | `flag_prorrogada` existe no fato físico (`docs/contrato-fisico-cubos.md`) mas não foi incluída na consulta de `PUB_C01_CICLO` em `publish.py`; precisa de uma nova coluna publicada. |
| I06 | Pesquisas atrasadas ou prioritárias | Sem dado | **Sem dado** | — | Mesmo motivo da camada de dados: falta data de referência e regra aprovadas. |

## Adesão e participação (C02)

| ID | Indicador | Camada de dados | Camada BI | Fonte publicada | Motivo do bloqueio (BI) |
| :-- | :-- | :-- | :-- | :-- | :-- |
| I07 | Empresas participantes distintas por pesquisa | Calculável | **Sem dado** | — | `PUB_C02_PARTICIPACAO` agrega por área/tipo/mês e só expõe `qtd_participacoes` (contagem de ocorrências); a contagem distinta de empresa por pesquisa não sobrevive à agregação nem foi publicada à parte. |
| I08 | Taxa de adesão | Sem dado | **Sem dado** | — | Mesmo motivo da camada de dados: falta universo de convites. |
| I09 | Participação de mercado observada | Bloqueado (normalização) | **Sem dado** | — | `pct_mercado_na_participacao` existe no fato físico mas não é publicada; mesmo se fosse, a fonte segue não homologada (`dmc.md`, DR02). |
| I10 | Engajamento por público | Bloqueado (normalização) | **Sem dado** | — | Mesmo motivo da camada de dados: participação e cliente conciliado exigem reconciliação, e a reconciliação não é publicada. |
| I11 | Taxa de engajamento | Sem dado | **Sem dado** | — | Mesmo motivo da camada de dados: falta denominador de convidados por público. |

## Resultados e questionários (C04)

| ID | Indicador | Camada de dados | Camada BI | Fonte publicada | Motivo do bloqueio (BI) |
| :-- | :-- | :-- | :-- | :-- | :-- |
| I12 | Distribuição agregada de respostas | Calculável (na fonte de respostas) | **Sem dado** | — | Nenhum dos quatro cubos publica distribuição de respostas; `respostas` não compõe `PUB_C04_INSTRUMENTO` (que só conta perguntas). |
| I13 | Respondentes distintos na fonte de respostas | Calculável | **Sem dado** | — | Não publicado; `PUB_C02_PARTICIPACAO.qtd_participacoes` conta ocorrência, não pessoa, e não pode substituir I13 (ver aviso em `acesso-cubos-bi.md`). |
| I14 | Questões por tipo | Calculável | **Calculável** | `PUB_C04_INSTRUMENTO.qtd_perguntas` por `tipo_pergunta` | — |
| I15 | Estado de validação e versão | Sem dado | **Sem dado** | — | Mesmo motivo da camada de dados: falta versão, área revisora, decisão e timestamp. |

## Qualidade, rastreabilidade e publicação

| ID | Indicador | Camada de dados | Camada BI | Fonte publicada | Motivo do bloqueio (BI) |
| :-- | :-- | :-- | :-- | :-- | :-- |
| I16 | Completude aplicável | Perfilamento exploratório; requisito indisponível sem regras homologadas | **Sem dado** | — | Regras homologadas de obrigatoriedade por campo e tipo/status não publicadas. `PUB_QUALIDADE_CAMPO` mede preenchimento sobre todas as linhas, incluindo nulos condicionais, e não substitui I16. |
| I17 | Taxa de duplicidade | Calculável | **Calculável** | (`PUB_QUALIDADE_DUPLICIDADE.qtd_linhas` - `qtd_chaves_distintas`) / `qtd_linhas` por tabela | — (idem) |
| I18 | Integridade referencial | Calculável | **Calculável** | `PUB_QUALIDADE_RELACAO.qtd_chaves_correspondentes` / `qtd_chaves_informadas` por relação | — (idem) |
| I19 | Parseabilidade | Calculável | **Sem dado** | — | Não publicado nesta rodada; exigiria testar conversão de tipo por campo e publicar a taxa (candidato a uma próxima extensão de `publish.py`, mesmo padrão das publicações de qualidade existentes). |
| I20 | Divergência de título | Calculável | **Sem dado** | — | Não publicado nesta rodada; a comparação de título entre fontes não tem consulta equivalente em `publish.py`. |
| I21 | Frescor da fonte | Sem dado | **Sem dado** | — | Mesmo motivo da camada de dados: falta timestamp de carga e regra aprovada. |
| I22 | Cobertura da linhagem | Bloqueado (mapeamento) | **Sem dado** | — | Mesmo motivo da camada de dados: exige mapeamento não publicado. |
| I23 | Estado de publicação autorizada | Sem dado | **Sem dado** | — | Mesmo motivo da camada de dados: falta decisão, estado e data de publicação. |
| I24 | Cobertura do processamento | Sem dado | **Sem dado** | — | Mesmo motivo da camada de dados: falta catálogo e execuções. |
| I25 | Conformidade de acesso | Sem dado | **Sem dado** | — | Mesmo motivo da camada de dados: falta política e logs. |

A medida adicional `Completude` permanece calculável como completude de
preenchimento. Ela usa `COUNT(coluna)` sobre `COUNT(*)` por campo, sem
excluir linhas onde o campo seja opcional ou inaplicável. É um diagnóstico
físico da ingestão tratada, sem classificar a ausência como defeito. O
requisito I16 de completude aplicável continua distinto e indisponível no
modelo publicado até que suas regras sejam homologadas e publicadas.

## Síntese

De 25 indicadores do catálogo, **6 são calculáveis na camada BI** (I01, I02,
I04 só em média, I14, I17 e I18); **I03 é parcial** e **18 estão sem
dado disponível** nessa camada — seis deles (I07, I09, I12, I13, I19, I20) porque a
consulta de publicação não seleciona a coluna, não porque o dado não exista
na camada física. Essa diferença é o motivo pelo qual este documento existe
separado de `dmc.md`: quem só olhar o catálogo da camada de dados vai esperar
mais indicadores prontos no Power BI do que os que realmente chegam a ele.

Qualquer indicador aqui marcado "Sem dado" deve aparecer no relatório com o
mecanismo de sinalização da DX-10 — motivo textual, nunca zero — usando a
coluna "Motivo do bloqueio (BI)" desta tabela como texto-base.
