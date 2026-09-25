"""Publica recortes agregados dos quatro cubos e da qualidade do dado em Parquet.

O arquivo DuckDB de origem nunca é distribuído. Cada execução grava uma geração
imutável; ``current.json`` aponta para a geração completa após a validação.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb

PUBLICATIONS = {
    "PUB_C01_CICLO": """
        SELECT a.area, s.status, t.tipo,
               COUNT(*)::BIGINT AS qtd_pesquisas,
               SUM(f.dias_corridos_validacao)::BIGINT AS soma_dias_validacao,
               COUNT(f.dias_corridos_validacao)::BIGINT AS qtd_validacao_disponivel,
               SUM(f.dias_corridos_coleta)::BIGINT AS soma_dias_coleta,
               COUNT(f.dias_corridos_coleta)::BIGINT AS qtd_coleta_disponivel,
               SUM(f.dias_corridos_tabulacao)::BIGINT AS soma_dias_tabulacao,
               COUNT(f.dias_corridos_tabulacao)::BIGINT AS qtd_tabulacao_disponivel,
               SUM(f.dias_corridos_ciclo_total)::BIGINT AS soma_dias_ciclo_total,
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
               SUM(f.minutos_preenchimento)::BIGINT AS soma_minutos_preenchimento,
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

COLUNAS_QUALIDADE = {
    "pesquisas": [
        "pesquisa_id",
        "titulo",
        "status",
        "tipo",
        "area",
        "participantes",
        "part_mercado",
        "data_solicitacao",
        "data_aprov",
        "data_divulgacao",
        "data_limite",
        "prorrogada_ate",
        "data_entrega",
        "dias_uteis_para_entrega",
        "complexidade",
        "tipo_resposta",
        "tempo_preenchimento",
        "objetivos",
        "dia_semana_lancamento",
        "dias_uteis_aberta",
        "dias_solicitacao_divulgacao",
        "dias_tabulacao",
    ],
    "empresas": [
        "empresa_id",
        "nome_fantasia",
        "part_mercado",
        "nacionalidade",
        "associado",
        "tipo_associado",
        "cidade",
        "estado",
        "pais",
    ],
    "clientes": ["cliente_id", "empresa_id", "cargo", "departamento", "email"],
    "respondentes": [
        "pesquisa_id",
        "hora_inicio",
        "hora_termino",
        "empresa_id",
        "market_share",
        "cliente_id",
    ],
    "questoes": [
        "pergunta_id",
        "pesquisa_id",
        "pesquisa_titulo",
        "enunciado",
        "tipo",
        "qtd_alternativas",
        "alternativas",
        "linhas_matriz",
        "colunas_matriz",
        "confianca",
        "formato_arquivo",
        "col_origem",
        "observacoes",
    ],
    "respostas": [
        "resposta_id",
        "pesquisa_id",
        "pergunta_id",
        "respondent_id",
        "empresa_id",
        "alternativa",
        "linha_matriz",
        "coluna_matriz",
        "valor",
    ],
}

RELACOES_QUALIDADE = [
    ("questoes", "pesquisa_id", "pesquisas", "pesquisa_id"),
    ("respostas", "pesquisa_id", "pesquisas", "pesquisa_id"),
    ("respostas", "pergunta_id", "questoes", "pergunta_id"),
    ("respostas", "empresa_id", "empresas", "empresa_id"),
    ("respondentes", "pesquisa_id", "pesquisas", "pesquisa_id"),
    ("respondentes", "empresa_id", "empresas", "empresa_id"),
    ("respondentes", "cliente_id", "clientes", "cliente_id"),
    ("clientes", "empresa_id", "empresas", "empresa_id"),
]

CHAVES_QUALIDADE = {
    "pesquisas": ("pesquisa_id",),
    "empresas": ("empresa_id",),
    "clientes": ("cliente_id",),
    "questoes": ("pesquisa_id", "pergunta_id"),
    "respostas": ("pesquisa_id", "resposta_id"),
}


def _view_atual(fonte: str) -> str:
    if fonte == "respondentes":
        return "ingestao_respondentes"
    return f"ingestao_{fonte}_atual"


def _sql_qualidade_campo() -> str:
    partes = [
        f"""SELECT '{fonte}' AS tabela, '{coluna}' AS campo,
               COUNT(*)::BIGINT AS qtd_linhas,
               COUNT({coluna})::BIGINT AS qtd_preenchidas
          FROM {_view_atual(fonte)}"""
        for fonte, colunas in COLUNAS_QUALIDADE.items()
        for coluna in colunas
    ]
    return "\n         UNION ALL\n".join(partes)


def _sql_qualidade_relacao() -> str:
    partes = [
        f"""SELECT '{filha}.{col_filha}' AS relacao,
               COUNT(*)::BIGINT AS qtd_chaves_informadas,
               COUNT(p.{col_pai})::BIGINT AS qtd_chaves_correspondentes
          FROM {_view_atual(filha)} f
          LEFT JOIN {_view_atual(pai)} p ON p.{col_pai} = f.{col_filha}
         WHERE f.{col_filha} IS NOT NULL"""
        for filha, col_filha, pai, col_pai in RELACOES_QUALIDADE
    ]
    return "\n         UNION ALL\n".join(partes)


def _sql_qualidade_duplicidade() -> str:
    partes = [
        f"""SELECT '{fonte}' AS tabela,
               COUNT(*)::BIGINT AS qtd_linhas,
               (SELECT COUNT(*) FROM (
                    SELECT DISTINCT {", ".join(chaves)} FROM ingestao_{fonte}
                ))::BIGINT AS qtd_chaves_distintas
          FROM ingestao_{fonte}"""
        for fonte, chaves in CHAVES_QUALIDADE.items()
    ]
    return "\n         UNION ALL\n".join(partes)


PUBLICATIONS.update(
    {
        "PUB_QUALIDADE_CAMPO": _sql_qualidade_campo(),
        "PUB_QUALIDADE_RELACAO": _sql_qualidade_relacao(),
        "PUB_QUALIDADE_DUPLICIDADE": _sql_qualidade_duplicidade(),
    }
)


def _sql_literal(value: Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def publish_cubes(database: Path, output: Path, *, load_reference: str) -> dict:
    """Publica uma geração verificada e muda o ponteiro só no fim.

    ``output`` deve ficar fora do checkout. O diretório é privado por padrão;
    a distribuição a consumidores autorizados ocorre fora deste processo.
    """
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", load_reference):
        raise ValueError("load_reference deve ser um identificador simples, sem segredo")
    database = Path(database).resolve(strict=True)
    if Path(output).is_symlink():
        raise ValueError("diretório de publicação simbólico não é permitido")
    output = Path(output).resolve()
    if any((directory / ".git").exists() for directory in (output, *output.parents)):
        raise ValueError("a publicação deve ficar fora do repositório")
    if not database.is_file():
        raise ValueError("a origem deve ser um arquivo DuckDB existente")
    if output == database or database in output.parents:
        raise ValueError("a publicação não pode ficar dentro do arquivo de origem")

    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    output.chmod(0o700)
    generation = uuid.uuid4().hex
    staging = output / f".pending-{generation}"
    final = output / generation
    pointer = output / f".current-{generation}.json"
    staging.mkdir(mode=0o700)
    conn = None
    in_transaction = False
    published = False
    try:
        conn = duckdb.connect(str(database), read_only=True)
        conn.execute("BEGIN TRANSACTION")
        in_transaction = True
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
        in_transaction = False
        manifest = {
            "version": 1,
            "generation": generation,
            "published_at_utc": datetime.now(timezone.utc).isoformat(),
            "load_reference": load_reference,
            "tables": tables,
        }
        manifest_path = staging / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        manifest_path.chmod(0o600)
        staging.rename(final)
        pointer.write_text(json.dumps({"generation": generation}) + "\n")
        pointer.chmod(0o600)
        os.replace(pointer, output / "current.json")
        published = True
        return manifest
    except Exception:
        if conn is not None and in_transaction:
            conn.execute("ROLLBACK")
        shutil.rmtree(staging, ignore_errors=True)
        pointer.unlink(missing_ok=True)
        if not published:
            shutil.rmtree(final, ignore_errors=True)
        raise
    finally:
        if conn is not None:
            conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--load-reference", required=True)
    args = parser.parse_args()
    result = publish_cubes(args.database, args.output, load_reference=args.load_reference)
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
