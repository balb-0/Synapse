#!/usr/bin/env python3
"""Confere métricas dos fatos contra consultas independentes à ingestão tratada.

Uso: python -m scripts.analytics.verificar_metricas_cubos caminho/banco.duckdb

O banco é aberto somente para leitura. O JSON contém apenas contagens agregadas;
qualquer divergência ou fonte indispensável ausente produz código de saída 1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path

import duckdb


def _rows(con: duckdb.DuckDBPyConnection, sql: str, params: tuple = ()) -> list[dict]:
    cursor = con.execute(sql, params)
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def _index(rows: list[dict], grain: tuple[str, ...]) -> dict[tuple, dict]:
    indexed = {tuple(row[name] for name in grain): row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError("grão duplicado na origem ou no fato")
    return indexed


def _compare(
    source: list[dict], fact: list[dict], grain: tuple[str, ...], fields: tuple[str, ...]
) -> dict:
    expected = _index(source, grain)
    actual = _index(fact, grain)
    common = expected.keys() & actual.keys()
    mismatches = {
        field: sum(expected[key][field] != actual[key][field] for key in common) for field in fields
    }
    missing = len(expected.keys() - actual.keys())
    unexpected = len(actual.keys() - expected.keys())
    return {
        "source_rows": len(source),
        "fact_rows": len(fact),
        "missing_grains": missing,
        "unexpected_grains": unexpected,
        "field_mismatches": mismatches,
        "status": "ok" if missing == unexpected == sum(mismatches.values()) == 0 else "mismatch",
    }


def _measure(rows: list[dict], field: str) -> dict:
    values = [row[field] for row in rows if row[field] is not None]
    return {"sum": sum(values) if values else None, "denominator": len(values)}


def _cycle(con: duckdb.DuckDBPyConnection) -> dict:
    source = _rows(
        con,
        """
        SELECT pesquisa_id,
          CASE WHEN data_aprov >= data_solicitacao
            THEN date_diff('day', data_solicitacao, data_aprov) END AS dias_corridos_validacao,
          CASE WHEN coalesce(prorrogada_ate, data_limite) >= data_divulgacao
            THEN date_diff('day', data_divulgacao, coalesce(prorrogada_ate, data_limite))
            END AS dias_corridos_coleta,
          CASE WHEN data_entrega >= coalesce(prorrogada_ate, data_limite)
            THEN date_diff('day', coalesce(prorrogada_ate, data_limite), data_entrega)
            END AS dias_corridos_tabulacao,
          CASE WHEN data_entrega >= data_solicitacao
            THEN date_diff('day', data_solicitacao, data_entrega)
            END AS dias_corridos_ciclo_total,
          participantes AS qtd_empresas_na_pesquisa,
          prorrogada_ate IS NOT NULL AS flag_prorrogada
        FROM ingestao_pesquisas_atual
    """,
    )
    fact = _rows(
        con,
        """
        SELECT p.pesquisa_id, f.dias_corridos_validacao, f.dias_corridos_coleta,
          f.dias_corridos_tabulacao, f.dias_corridos_ciclo_total,
          f.qtd_empresas_na_pesquisa, f.flag_prorrogada
        FROM FATO_CICLO_PESQUISA f
        LEFT JOIN DIM_PESQUISA p USING (sk_pesquisa)
    """,
    )
    durations = (
        "dias_corridos_validacao",
        "dias_corridos_coleta",
        "dias_corridos_tabulacao",
        "dias_corridos_ciclo_total",
    )
    result = _compare(
        source,
        fact,
        ("pesquisa_id",),
        (*durations, "qtd_empresas_na_pesquisa", "flag_prorrogada"),
    )
    result["metrics"] = {
        name: {"source": _measure(source, name), "fact": _measure(fact, name)} for name in durations
    }
    result["metrics"]["qtd_pesquisas"] = {"source": len(source), "fact": len(fact)}
    result["metrics"]["qtd_empresas_na_pesquisa_disponivel"] = {
        "source": sum(row["qtd_empresas_na_pesquisa"] is not None for row in source),
        "fact": sum(row["qtd_empresas_na_pesquisa"] is not None for row in fact),
    }
    return result


def _respondent_snapshot(con: duckdb.DuckDBPyConnection) -> str | None:
    row = con.execute("""
        SELECT o.source_checksum
        FROM _control_object o
        JOIN reconciliacao_execucao r ON r.run_id = o.run_id
        WHERE o.source = 'respondentes' AND o.source_checksum IS NOT NULL
          AND o.source_checksum <> '' AND r.conciliado AND r.status <> 'falha'
          AND EXISTS (SELECT 1 FROM _batch_metadata b
                      WHERE b.run_id = o.run_id AND b.source = 'respondentes'
                        AND b.status <> 'falha')
          AND NOT EXISTS (SELECT 1 FROM _batch_metadata b
                          WHERE b.run_id = o.run_id AND b.source = 'respondentes'
                            AND b.status = 'falha')
        ORDER BY o.concluded_at DESC, o.source_checksum DESC
        LIMIT 1
    """).fetchone()
    return row[0] if row else None


def _participation(con: duckdb.DuckDBPyConnection, recorded_checksum: str | None) -> dict:
    selected = _respondent_snapshot(con)
    if selected is None:
        count = con.execute("SELECT count(*) FROM FATO_PARTICIPACAO").fetchone()[0]
        return {"status": "source_unavailable", "fact_rows": count}
    source = _rows(
        con,
        """
        WITH occurrences AS (
          SELECT source_checksum, source_offset, pesquisa_id, cliente_id,
            hora_inicio, hora_termino, market_share,
            CASE WHEN cliente_id IS NOT NULL AND cliente_id <> ''
              THEN row_number() OVER (
                PARTITION BY pesquisa_id, cliente_id ORDER BY source_offset
              ) END AS seq_ocorrencia
          FROM ingestao_respondentes WHERE source_checksum = ?
        )
        SELECT source_checksum, source_offset, 1 AS qtd_participacao,
          seq_ocorrencia,
          CASE WHEN hora_inicio IS NOT NULL AND hora_termino >= hora_inicio
            THEN floor(date_diff('microseconds', hora_inicio, hora_termino) / 60000000.0)::BIGINT
            END AS minutos_preenchimento,
          CASE WHEN hora_inicio IS NULL THEN 'inicio_ausente'
            WHEN hora_termino IS NULL THEN 'termino_ausente'
            WHEN hora_termino < hora_inicio THEN 'termino_anterior_ao_inicio'
            END AS motivo_minutos_indisponivel,
          market_share AS pct_mercado_na_participacao
        FROM occurrences
    """,
        (selected,),
    )
    fact = _rows(
        con,
        """
        SELECT source_checksum, source_offset, qtd_participacao, seq_ocorrencia,
          minutos_preenchimento, motivo_minutos_indisponivel,
          pct_mercado_na_participacao
        FROM FATO_PARTICIPACAO
    """,
    )
    result = _compare(
        source,
        fact,
        ("source_checksum", "source_offset"),
        (
            "qtd_participacao",
            "seq_ocorrencia",
            "minutos_preenchimento",
            "motivo_minutos_indisponivel",
            "pct_mercado_na_participacao",
        ),
    )
    result["snapshot_matches_load"] = selected == recorded_checksum
    if not result["snapshot_matches_load"]:
        result["status"] = "mismatch"
    result["metrics"] = {
        "qtd_participacoes": {
            "source": sum(row["qtd_participacao"] for row in source),
            "fact": sum(row["qtd_participacao"] for row in fact),
        },
        "minutos_preenchimento": {
            "source": _measure(source, "minutos_preenchimento"),
            "fact": _measure(fact, "minutos_preenchimento"),
        },
        "pct_mercado_disponivel": {
            "source": sum(row["pct_mercado_na_participacao"] is not None for row in source),
            "fact": sum(row["pct_mercado_na_participacao"] is not None for row in fact),
        },
    }
    return result


def _instrument(con: duckdb.DuckDBPyConnection) -> dict:
    source = _rows(
        con,
        """
        SELECT pesquisa_id AS pesquisa_id_origem, pergunta_id AS pergunta_id_origem,
          tipo, qtd_alternativas
        FROM ingestao_questoes_atual
    """,
    )
    fact = _rows(
        con,
        """
        SELECT f.pesquisa_id_origem, f.pergunta_id_origem, p.tipo, p.qtd_alternativas
        FROM FATO_PESQUISA_PERGUNTA f
        LEFT JOIN DIM_PERGUNTA p USING (sk_pergunta)
    """,
    )
    result = _compare(
        source,
        fact,
        ("pesquisa_id_origem", "pergunta_id_origem"),
        ("tipo", "qtd_alternativas"),
    )
    result["metrics"] = {
        "qtd_perguntas": {"source": len(source), "fact": len(fact)},
        "qtd_alternativas_disponivel": {
            "source": sum(row["qtd_alternativas"] is not None for row in source),
            "fact": sum(row["qtd_alternativas"] is not None for row in fact),
        },
    }
    return result


def _normalized(value: str | None) -> str | None:
    if value is None:
        return None
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split()) or None


def _research_digest(con: duckdb.DuckDBPyConnection) -> str:
    keys = [
        row[0]
        for row in con.execute("SELECT idempotency_key FROM ingestao_pesquisas_atual").fetchall()
    ]
    material = "".join(f"{len(key)}:{key}" for key in sorted(keys))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _research_groups(con: duckdb.DuckDBPyConnection) -> list[dict]:
    rows = _rows(
        con,
        """
        SELECT pesquisa_id, status, area, tipo, complexidade, tipo_resposta
        FROM ingestao_pesquisas_atual
    """,
    )
    return [
        {
            "pesquisa_id": row["pesquisa_id"],
            **{
                name: _normalized(row[name])
                for name in ("status", "area", "tipo", "complexidade", "tipo_resposta")
            },
        }
        for row in rows
    ]


GROUP_FIELDS = ("status", "area", "tipo", "complexidade", "tipo_resposta")


def _monthly(con: duckdb.DuckDBPyConnection) -> dict:
    closures = _rows(
        con,
        """
        SELECT data_fim_mes, observed_at, load_id
        FROM analytics_pipeline_closure ORDER BY data_fim_mes
    """,
    )
    fact_count = con.execute("SELECT count(*) FROM FATO_PIPELINE_MENSAL").fetchone()[0]
    member_count = con.execute("SELECT count(*) FROM analytics_pipeline_membership").fetchone()[0]
    missing_markers = con.execute("""
        SELECT count(*) FROM (
          (SELECT DISTINCT CAST(observed_at AS DATE) AS data_fim_mes
           FROM analytics_load_run WHERE observed_at IS NOT NULL)
          EXCEPT (SELECT data_fim_mes FROM analytics_pipeline_closure)
        )
    """).fetchone()[0]
    if not closures:
        status = (
            "not_observed" if fact_count == member_count == missing_markers == 0 else "mismatch"
        )
        return {
            "status": status,
            "closures": 0,
            "fact_rows": fact_count,
            "membership_rows": member_count,
            "missing_closure_markers": missing_markers,
            "stock": None,
            "entries": None,
            "exits": None,
            "months": [],
        }

    source_digest = _research_digest(con)
    source = _research_groups(con)
    expected_groups = Counter(tuple(row[name] for name in GROUP_FIELDS) for row in source)
    months = []
    for closure in closures:
        month = closure["data_fim_mes"]
        run = con.execute(
            """
            SELECT pesquisas_digest, observed_at FROM analytics_load_run WHERE load_id = ?
        """,
            (closure["load_id"],),
        ).fetchone()
        if (
            run is None
            or run[0] != source_digest
            or run[1] != closure["observed_at"]
            or closure["observed_at"].date() != month
        ):
            months.append({"month": month.isoformat(), "status": "source_snapshot_unavailable"})
            continue
        members = _rows(
            con,
            """
            SELECT p.pesquisa_id, m.observed_at, s.status, a.area, t.tipo,
              perfil.complexidade, perfil.tipo_resposta
            FROM analytics_pipeline_membership m
            LEFT JOIN DIM_PESQUISA p USING (sk_pesquisa)
            LEFT JOIN DIM_STATUS_PESQUISA s USING (sk_status)
            LEFT JOIN DIM_AREA a USING (sk_area)
            LEFT JOIN DIM_TIPO_PESQUISA t USING (sk_tipo)
            LEFT JOIN DIM_PERFIL_PESQUISA perfil USING (sk_perfil)
            WHERE m.data_fim_mes = ?
        """,
            (month,),
        )
        expected_members = [{**row, "observed_at": closure["observed_at"]} for row in source]
        membership = _compare(
            expected_members, members, ("pesquisa_id",), (*GROUP_FIELDS, "observed_at")
        )
        facts = _rows(
            con,
            """
            SELECT f.observed_at, s.status, a.area, t.tipo,
              perfil.complexidade, perfil.tipo_resposta,
              f.qtd_pesquisas_no_status, f.qtd_entradas_no_mes, f.qtd_saidas_no_mes
            FROM FATO_PIPELINE_MENSAL f
            LEFT JOIN DIM_STATUS_PESQUISA s USING (sk_status)
            LEFT JOIN DIM_AREA a USING (sk_area)
            LEFT JOIN DIM_TIPO_PESQUISA t USING (sk_tipo)
            LEFT JOIN DIM_PERFIL_PESQUISA perfil USING (sk_perfil)
            WHERE f.data_fim_mes = ?
        """,
            (month,),
        )
        actual_groups = _index(facts, GROUP_FIELDS)
        missing = len(expected_groups.keys() - actual_groups.keys())
        unexpected = len(actual_groups.keys() - expected_groups.keys())
        common = expected_groups.keys() & actual_groups.keys()
        wrong_stock = sum(
            expected_groups[key] != actual_groups[key]["qtd_pesquisas_no_status"] for key in common
        )
        wrong_instant = sum(row["observed_at"] != closure["observed_at"] for row in facts)
        flows_present = sum(
            row["qtd_entradas_no_mes"] is not None or row["qtd_saidas_no_mes"] is not None
            for row in facts
        )
        valid_date = month == con.execute("SELECT last_day(?)", (month,)).fetchone()[0]
        ok = (
            membership["status"] == "ok"
            and missing == unexpected == wrong_stock == wrong_instant == flows_present == 0
            and valid_date
        )
        months.append(
            {
                "month": month.isoformat(),
                "status": "ok" if ok else "mismatch",
                "source_rows": len(source),
                "membership_rows": len(members),
                "fact_rows": len(facts),
                "stock": {
                    "source": len(source),
                    "fact": sum(row["qtd_pesquisas_no_status"] for row in facts),
                },
                "entries": None,
                "exits": None,
                "membership_missing": membership["missing_grains"],
                "membership_unexpected": membership["unexpected_grains"],
                "membership_mismatches": sum(membership["field_mismatches"].values()),
                "missing_groups": missing,
                "unexpected_groups": unexpected,
                "stock_mismatches": wrong_stock,
                "observed_at_mismatches": wrong_instant,
                "flows_without_source": flows_present,
            }
        )
    orphan_fact_months = con.execute("""
        SELECT count(*) FROM FATO_PIPELINE_MENSAL f
        LEFT JOIN analytics_pipeline_closure c USING (data_fim_mes)
        WHERE c.data_fim_mes IS NULL
    """).fetchone()[0]
    orphan_member_months = con.execute("""
        SELECT count(*) FROM analytics_pipeline_membership m
        LEFT JOIN analytics_pipeline_closure c USING (data_fim_mes)
        WHERE c.data_fim_mes IS NULL
    """).fetchone()[0]
    status = (
        "ok"
        if all(row["status"] == "ok" for row in months)
        and orphan_fact_months == orphan_member_months == missing_markers == 0
        else "mismatch"
    )
    return {
        "status": status,
        "closures": len(closures),
        "fact_rows": fact_count,
        "membership_rows": member_count,
        "missing_closure_markers": missing_markers,
        "orphan_fact_months": orphan_fact_months,
        "orphan_membership_months": orphan_member_months,
        "months": months,
    }


def verificar(con: duckdb.DuckDBPyConnection) -> dict:
    latest = con.execute("""
        SELECT load_id, respondentes_checksum
        FROM analytics_load_run ORDER BY loaded_at DESC, load_id DESC LIMIT 1
    """).fetchone()
    if latest is None:
        raise ValueError("carga analítica ausente")
    cubes = {
        "C01": _cycle(con),
        "C02": _participation(con, latest[1]),
        "C03": _monthly(con),
        "C04": _instrument(con),
    }
    return {
        "load_id": latest[0],
        "ok": all(cube["status"] in {"ok", "not_observed"} for cube in cubes.values()),
        "cubes": cubes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path, help="DuckDB com ingestão e fatos carregados")
    args = parser.parse_args(argv)
    try:
        with duckdb.connect(str(args.database), read_only=True) as con:
            report = verificar(con)
    except (duckdb.Error, OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error).splitlines()[0]}))
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
