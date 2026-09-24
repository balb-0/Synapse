"""Publica recortes agregados dos quatro cubos em Parquet.

O arquivo DuckDB de origem nunca é distribuído. Cada execução grava uma geração
imutável; ``current.json`` aponta para a geração completa após a validação.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb

PUBLICATIONS = {
    "PUB_C01_CICLO": """
        SELECT a.area, s.status, t.tipo,
               COUNT(*)::BIGINT AS qtd_pesquisas,
               SUM(f.dias_corridos_validacao)::HUGEINT AS soma_dias_validacao,
               COUNT(f.dias_corridos_validacao)::BIGINT AS qtd_validacao_disponivel,
               SUM(f.dias_corridos_coleta)::HUGEINT AS soma_dias_coleta,
               COUNT(f.dias_corridos_coleta)::BIGINT AS qtd_coleta_disponivel,
               SUM(f.dias_corridos_tabulacao)::HUGEINT AS soma_dias_tabulacao,
               COUNT(f.dias_corridos_tabulacao)::BIGINT AS qtd_tabulacao_disponivel,
               SUM(f.dias_corridos_ciclo_total)::HUGEINT AS soma_dias_ciclo_total,
               COUNT(f.dias_corridos_ciclo_total)::BIGINT AS qtd_ciclo_total_disponivel
          FROM FATO_CICLO_PESQUISA f
          LEFT JOIN DIM_AREA a ON a.sk_area = f.sk_area
          LEFT JOIN DIM_STATUS_PESQUISA s ON s.sk_status = f.sk_status
          LEFT JOIN DIM_TIPO_PESQUISA t ON t.sk_tipo = f.sk_tipo
         GROUP BY a.area, s.status, t.tipo
    """,
    "PUB_C02_PARTICIPACAO": """
        SELECT a.area, t.tipo, date_trunc('month', tempo.data)::DATE AS mes_resposta,
               COUNT(*)::BIGINT AS qtd_participacoes,
               SUM(f.minutos_preenchimento)::HUGEINT AS soma_minutos_preenchimento,
               COUNT(f.minutos_preenchimento)::BIGINT AS qtd_preenchimento_disponivel
          FROM FATO_PARTICIPACAO f
          LEFT JOIN FATO_CICLO_PESQUISA ciclo ON ciclo.sk_pesquisa = f.sk_pesquisa
          LEFT JOIN DIM_AREA a ON a.sk_area = ciclo.sk_area
          LEFT JOIN DIM_TIPO_PESQUISA t ON t.sk_tipo = ciclo.sk_tipo
          LEFT JOIN DIM_TEMPO tempo ON tempo.sk_tempo = f.sk_data_resposta
         GROUP BY a.area, t.tipo, date_trunc('month', tempo.data)::DATE
    """,
    "PUB_C03_PIPELINE_MENSAL": """
        SELECT f.data_fim_mes, s.status, a.area, t.tipo,
               perfil.complexidade, perfil.tipo_resposta,
               f.qtd_pesquisas_no_status,
               f.qtd_entradas_no_mes, f.qtd_saidas_no_mes
          FROM FATO_PIPELINE_MENSAL f
          LEFT JOIN DIM_STATUS_PESQUISA s ON s.sk_status = f.sk_status
          LEFT JOIN DIM_AREA a ON a.sk_area = f.sk_area
          LEFT JOIN DIM_TIPO_PESQUISA t ON t.sk_tipo = f.sk_tipo
          LEFT JOIN DIM_PERFIL_PESQUISA perfil ON perfil.sk_perfil = f.sk_perfil
    """,
    "PUB_C04_INSTRUMENTO": """
        SELECT a.area, pergunta.tipo AS tipo_pergunta,
               COUNT(*)::BIGINT AS qtd_perguntas
          FROM FATO_PESQUISA_PERGUNTA f
          LEFT JOIN DIM_PERGUNTA pergunta ON pergunta.sk_pergunta = f.sk_pergunta
          LEFT JOIN FATO_CICLO_PESQUISA ciclo ON ciclo.sk_pesquisa = f.sk_pesquisa
          LEFT JOIN DIM_AREA a ON a.sk_area = ciclo.sk_area
         GROUP BY a.area, pergunta.tipo
    """,
}


def _sql_literal(value: Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def publish_cubes(database: Path, output: Path) -> dict:
    """Publica uma geração verificada e muda o ponteiro só no fim.

    ``output`` deve ficar fora do checkout. O diretório é privado por padrão;
    a distribuição a consumidores autorizados ocorre fora deste processo.
    """
    database = Path(database).resolve(strict=True)
    output = Path(output).resolve()
    repo = Path(__file__).resolve().parents[3]
    if output == repo or repo in output.parents:
        raise ValueError("a publicação deve ficar fora do repositório")
    if not database.is_file():
        raise ValueError("a origem deve ser um arquivo DuckDB existente")
    if output == database or database in output.parents:
        raise ValueError("a publicação não pode ficar dentro do arquivo de origem")

    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    if output.is_symlink():
        raise ValueError("diretório de publicação simbólico não é permitido")
    output.chmod(0o700)
    generation = uuid.uuid4().hex
    staging = output / f".pending-{generation}"
    final = output / generation
    staging.mkdir(mode=0o700)
    conn = None
    try:
        conn = duckdb.connect(str(database), read_only=True)
        conn.execute("BEGIN TRANSACTION")
        tables = {}
        for name, query in PUBLICATIONS.items():
            target = staging / f"{name}.parquet"
            conn.execute(
                f"COPY ({query}) TO {_sql_literal(target)} (FORMAT PARQUET, COMPRESSION ZSTD)"
            )
            target.chmod(0o600)
            parquet = _sql_literal(target)
            rows = conn.execute(f"SELECT COUNT(*) FROM read_parquet({parquet})").fetchone()[0]
            source_rows = conn.execute(f"SELECT COUNT(*) FROM ({query})").fetchone()[0]
            if rows != source_rows:
                raise RuntimeError(f"{name}: contagem Parquet diferente da consulta")
            source_columns = [column[0] for column in conn.execute(query + " LIMIT 0").description]
            file_columns = [
                column[0]
                for column in conn.execute(
                    f"SELECT * FROM read_parquet({parquet}) LIMIT 0"
                ).description
            ]
            if source_columns != file_columns:
                raise RuntimeError(f"{name}: colunas Parquet diferentes da consulta")
            tables[name] = {
                "file": f"{name}.parquet",
                "rows": rows,
                "columns": file_columns,
                "sha256": _digest(target),
            }
        conn.execute("COMMIT")
        manifest = {
            "version": 1,
            "generation": generation,
            "published_at_utc": datetime.now(timezone.utc).isoformat(),
            "tables": tables,
        }
        manifest_path = staging / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        manifest_path.chmod(0o600)
        staging.rename(final)
        pointer = output / f".current-{generation}.json"
        pointer.write_text(json.dumps({"generation": generation}) + "\n")
        pointer.chmod(0o600)
        os.replace(pointer, output / "current.json")
        return manifest
    except Exception:
        if conn is not None:
            conn.execute("ROLLBACK")
        shutil.rmtree(staging, ignore_errors=True)
        raise
    finally:
        if conn is not None:
            conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = publish_cubes(args.database, args.output)
    print(
        json.dumps(
            {
                "generation": result["generation"],
                "rows": {name: table["rows"] for name, table in result["tables"].items()},
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
