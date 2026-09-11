"""Fixtures sintéticas versionadas dos seis CSVs de ingestão (VB-03).

Os arquivos `.csv` deste diretório são pequenos, determinísticos e livres de
dados reais ou PII: identificadores são sequenciais artificiais e os e-mails
usam o domínio reservado `example.invalid`. Cada arquivo cobre, dentro do
conjunto, os cenários exigidos pela estratégia de testes:

- válido:        linhas integralmente aceitas pelo pipeline;
- nulo:          campos opcionais vazios ou com sentinelas (`na`, `s/i`);
- inválido:      violações de domínio/consistência que viram rejeição
                 (ordem temporal, tipo de questão desconhecido, alternativa
                 fora do domínio, referência órfã);
- duplicado:     mesma identidade repetida no arquivo (empresas, respostas);
- borda:         zero como medida válida (participantes, % de mercado);
- relacionamento: chaves que se referenciam entre arquivos
                 (clientes -> empresas, respondentes -> empresas/pesquisas/
                 clientes, questoes -> pesquisas, respostas -> pesquisas/
                 questoes/empresas).

`ESPERADO` declara, por fonte, quantas linhas o arquivo tem e quantas devem
ser aceitas, rejeitadas e deduplicadas pela transformação — o contrato que os
testes de ponta a ponta e de integração usam para conferir o pipeline.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent

# Ordem de carga que respeita os relacionamentos entre as fontes.
ORDEM_CARGA = (
    "pesquisas",
    "empresas",
    "clientes",
    "questoes",
    "respondentes",
    "respostas",
)

ESPERADO = {
    "pesquisas": {"registros": 4, "aceitos": 3, "rejeitados": 1, "duplicados": 0},
    "empresas": {"registros": 4, "aceitos": 3, "rejeitados": 0, "duplicados": 1},
    "clientes": {"registros": 3, "aceitos": 2, "rejeitados": 1, "duplicados": 0},
    "questoes": {"registros": 3, "aceitos": 2, "rejeitados": 1, "duplicados": 0},
    "respondentes": {"registros": 3, "aceitos": 2, "rejeitados": 1, "duplicados": 0},
    "respostas": {"registros": 4, "aceitos": 2, "rejeitados": 1, "duplicados": 1},
}


def caminho(source: str) -> Path:
    """Caminho do CSV fixture da fonte; falha cedo se a fonte for desconhecida."""
    if source not in ESPERADO:
        raise ValueError(f"fonte sem fixture: {source!r}")
    return FIXTURES_DIR / f"{source}.csv"


def payload(source: str) -> bytes:
    """Conteúdo em bytes do fixture, pronto para um ObjectReader em memória."""
    return caminho(source).read_bytes()
