#!/usr/bin/env python3
"""Confere as medidas do modelo Power BI contra a apuração já registrada.

Uso:
    PYTHONPATH=src python -m scripts.analytics.conferir_medidas_bi \
        --geracao /caminho/privado/publicacao-bi/GERACAO
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import duckdb


@dataclass(frozen=True)
class Referencia:
    medida: str
    valor: float
    fonte: str
    tolerancia: str


@dataclass(frozen=True)
class ValorPublicado:
    arquivo_presente: bool
    linhas: int | None
    valor: int | float | None


REFERENCIAS = [
    Referencia(
        medida="Qtd Pesquisas",
        valor=366,
        fonte='docs/resultados_analise.txt, T1 ("pesquisas: 366")',
        tolerancia="Referência histórica; valor maior também exige reconciliação da identidade na mesma geração.",
    ),
    Referencia(
        medida="Base Valida Validacao",
        valor=20,
        fonte="docs/resultados_analise.txt, T1 (cobertura de data_aprov: 20 de 366, 5,5%)",
        tolerancia="Comparação histórica; valide pares de datas e denominador contra a fonte da mesma geração.",
    ),
    Referencia(
        medida="Qtd Participacoes",
        valor=18735,
        fonte='docs/dmc.md, seção 3.2 ("aproximadamente 18.735 linhas no snapshot atual")',
        tolerancia="Referência histórica aproximada; diferenças exigem reconciliação de ocorrências na mesma geração.",
    ),
]


def _read_parquet_agregado(con: duckdb.DuckDBPyConnection, path: Path, sql: str) -> ValorPublicado:
    if not path.exists():
        return ValorPublicado(arquivo_presente=False, linhas=None, valor=None)
    linhas, valor = con.execute(sql, [str(path)]).fetchone()
    return ValorPublicado(arquivo_presente=True, linhas=linhas, valor=valor)


def calcular_valores_publicados(geracao: Path) -> dict[str, ValorPublicado]:
    con = duckdb.connect(":memory:")
    try:
        valores = {
            "Qtd Pesquisas": _read_parquet_agregado(
                con,
                geracao / "PUB_C01_CICLO.parquet",
                "SELECT COUNT(*), SUM(qtd_pesquisas) FROM read_parquet(?)",
            ),
            "Base Valida Validacao": _read_parquet_agregado(
                con,
                geracao / "PUB_C01_CICLO.parquet",
                "SELECT COUNT(*), SUM(qtd_validacao_disponivel) FROM read_parquet(?)",
            ),
            "Qtd Participacoes": _read_parquet_agregado(
                con,
                geracao / "PUB_C02_PARTICIPACAO.parquet",
                "SELECT COUNT(*), SUM(qtd_participacoes) FROM read_parquet(?)",
            ),
        }
    finally:
        con.close()
    return valores


def conferir(geracao: Path) -> list[dict]:
    publicados = calcular_valores_publicados(geracao)
    linhas = []
    for referencia in REFERENCIAS:
        publicado = publicados[referencia.medida]
        valor_publicado = publicado.valor
        if not publicado.arquivo_presente:
            status = "sem arquivo publicado nesta geracao"
        elif publicado.linhas == 0:
            status = "arquivo publicado sem linhas nesta geracao"
        elif valor_publicado is None:
            status = "arquivo publicado sem valor agregado nesta geracao"
        elif valor_publicado == referencia.valor:
            status = "bate exato"
        elif valor_publicado > referencia.valor:
            status = "diverge (maior que a referencia historica; reconciliar a mesma geracao)"
        else:
            status = "diverge (menor que a referencia, investigar)"
        linhas.append(
            {
                "medida": referencia.medida,
                "arquivo_presente": publicado.arquivo_presente,
                "linhas_publicadas": publicado.linhas,
                "valor_publicado": valor_publicado,
                "valor_referencia": referencia.valor,
                "status": status,
                "fonte_referencia": referencia.fonte,
                "tolerancia": referencia.tolerancia,
            }
        )
    return linhas


def codigo_saida(resultado: list[dict]) -> int:
    """Treat every missing or divergent historical value as unverified."""
    return 0 if all(linha["status"] == "bate exato" for linha in resultado) else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geracao", type=Path, required=True)
    args = parser.parse_args()
    resultado = conferir(args.geracao)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    raise SystemExit(codigo_saida(resultado))


if __name__ == "__main__":
    main()
