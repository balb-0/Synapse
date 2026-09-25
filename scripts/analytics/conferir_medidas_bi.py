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


REFERENCIAS = [
    Referencia(
        medida="Qtd Pesquisas",
        valor=366,
        fonte='docs/resultados_analise.txt, T1 ("pesquisas: 366")',
        tolerancia="Snapshot da apuração é anterior à geração conferida: o valor atual pode ser maior, nunca menor.",
    ),
    Referencia(
        medida="Base Valida Validacao",
        valor=20,
        fonte="docs/resultados_analise.txt, T1 (cobertura de data_aprov: 20 de 366, 5,5%)",
        tolerancia="Limite superior: a base válida exige data_aprov E data_solicitacao preenchidas com par coerente; pode ser menor que a cobertura bruta de data_aprov, nunca maior.",
    ),
    Referencia(
        medida="Qtd Participacoes",
        valor=18735,
        fonte='docs/dmc.md, seção 3.2 ("aproximadamente 18.735 linhas no snapshot atual")',
        tolerancia="Valor aproximado já na fonte; e o snapshot da apuração pode ser anterior à geração conferida.",
    ),
]


def _read_parquet_scalar(con: duckdb.DuckDBPyConnection, path: Path, sql: str) -> float | None:
    if not path.exists():
        return None
    return con.execute(sql, [str(path)]).fetchone()[0]


def calcular_valores_publicados(geracao: Path) -> dict[str, float | None]:
    con = duckdb.connect(":memory:")
    try:
        valores = {
            "Qtd Pesquisas": _read_parquet_scalar(
                con,
                geracao / "PUB_C01_CICLO.parquet",
                "SELECT SUM(qtd_pesquisas) FROM read_parquet(?)",
            ),
            "Base Valida Validacao": _read_parquet_scalar(
                con,
                geracao / "PUB_C01_CICLO.parquet",
                "SELECT SUM(qtd_validacao_disponivel) FROM read_parquet(?)",
            ),
            "Qtd Participacoes": _read_parquet_scalar(
                con,
                geracao / "PUB_C02_PARTICIPACAO.parquet",
                "SELECT SUM(qtd_participacoes) FROM read_parquet(?)",
            ),
        }
    finally:
        con.close()
    return valores


def conferir(geracao: Path) -> list[dict]:
    publicados = calcular_valores_publicados(geracao)
    linhas = []
    for referencia in REFERENCIAS:
        valor_publicado = publicados.get(referencia.medida)
        if valor_publicado is None:
            status = "sem arquivo publicado nesta geracao"
        elif valor_publicado == referencia.valor:
            status = "bate exato"
        elif valor_publicado > referencia.valor:
            status = "diverge (maior que a referencia, esperado por snapshot mais novo)"
        else:
            status = "diverge (menor que a referencia, investigar)"
        linhas.append(
            {
                "medida": referencia.medida,
                "valor_publicado": valor_publicado,
                "valor_referencia": referencia.valor,
                "status": status,
                "fonte_referencia": referencia.fonte,
                "tolerancia": referencia.tolerancia,
            }
        )
    return linhas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geracao", type=Path, required=True)
    args = parser.parse_args()
    resultado = conferir(args.geracao)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    if any(
        linha["status"] == "diverge (menor que a referencia, investigar)" for linha in resultado
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
