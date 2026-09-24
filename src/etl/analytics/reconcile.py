"""Read-only reconciliation of the four analytical facts with treated ingestion."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

import duckdb
from etl.analytics.dimensions_ddl import unknown_key
from etl.analytics.load import current_source_digests, selected_respondentes


@dataclass(frozen=True)
class CubeCount:
    cube: str
    eligible: int | None
    loaded: int
    discarded: int
    difference: int | None
    missing_keys: int
    unexpected_keys: int
    status: str


@dataclass(frozen=True)
class ReconciliationReport:
    load_id: str | None
    loaded_at: str | None
    source_digests_match: bool
    respondent_checksum: str | None
    respondent_run_id: str | None
    cubes: tuple[CubeCount, ...]
    orphan_reasons: tuple[dict[str, str | int], ...]
    orphan_audit: tuple[dict[str, str | int], ...]
    monthly_closures: tuple[dict[str, str | int], ...]

    @property
    def reconciled(self) -> bool:
        cubes_ok = all(cube.status in {"ok", "not_observed"} for cube in self.cubes)
        return (
            self.load_id is not None
            and self.source_digests_match
            and cubes_ok
            and all(row["expected"] == row["logged"] for row in self.orphan_audit)
        )

    def as_dict(self) -> dict:
        return {**asdict(self), "reconciled": self.reconciled}


def _scalar(con: duckdb.DuckDBPyConnection, sql: str, params: tuple = ()) -> int:
    return int(con.execute(sql, params).fetchone()[0])


def _current_cube(
    con: duckdb.DuckDBPyConnection,
    cube: str,
    source_sql: str,
    fact_sql: str,
    params: tuple = (),
) -> CubeCount:
    """Compare identities both ways so equal counts cannot hide wrong members."""
    eligible = _scalar(con, f"SELECT count(*) FROM ({source_sql}) AS source", params)
    loaded = _scalar(con, f"SELECT count(*) FROM ({fact_sql}) AS fact", params)
    missing = _scalar(con, f"SELECT count(*) FROM (({source_sql}) EXCEPT ({fact_sql}))", params * 2)
    unexpected = _scalar(
        con, f"SELECT count(*) FROM (({fact_sql}) EXCEPT ({source_sql}))", params * 2
    )
    # Current cubes intentionally retain orphans under unknown dimension keys.
    # Neither source deduplication nor a rejected ingestion line is a discard here.
    discarded = 0
    difference = eligible - loaded - discarded
    status = "ok" if difference == missing == unexpected == 0 else "mismatch"
    return CubeCount(cube, eligible, loaded, discarded, difference, missing, unexpected, status)


def _monthly_cube(con: duckdb.DuckDBPyConnection) -> CubeCount:
    """Reconcile retained month-end members with the stored group measures."""
    members = _scalar(con, 'SELECT count(*) FROM "analytics_pipeline_membership"')
    stock = _scalar(
        con, 'SELECT coalesce(sum(qtd_pesquisas_no_status), 0) FROM "FATO_PIPELINE_MENSAL"'
    )
    expected = """SELECT data_fim_mes, sk_status, sk_area, sk_tipo, sk_perfil,
                         observed_at, count(*) AS quantity
                  FROM "analytics_pipeline_membership"
                  GROUP BY data_fim_mes, sk_status, sk_area, sk_tipo, sk_perfil, observed_at"""
    actual = '''SELECT data_fim_mes, sk_status, sk_area, sk_tipo, sk_perfil,
                       observed_at, qtd_pesquisas_no_status AS quantity
                FROM "FATO_PIPELINE_MENSAL"'''
    missing = _scalar(con, f"SELECT count(*) FROM (({expected}) EXCEPT ({actual}))")
    unexpected = _scalar(con, f"SELECT count(*) FROM (({actual}) EXCEPT ({expected}))")
    # Grouping by observed_at would otherwise allow two observations in one month.
    mixed = _scalar(
        con,
        """SELECT count(*) FROM (
        SELECT data_fim_mes FROM "analytics_pipeline_membership"
        GROUP BY data_fim_mes HAVING count(DISTINCT observed_at) <> 1
    )""",
    )
    discarded = 0
    difference = members - stock - discarded
    if members == stock == 0 and missing == unexpected == 0:
        return CubeCount("C03", None, 0, 0, None, 0, 0, "not_observed")
    status = "ok" if difference == missing == unexpected == mixed == 0 else "mismatch"
    return CubeCount("C03", members, stock, discarded, difference, missing, unexpected, status)


def reconcile_analytics(con: duckdb.DuckDBPyConnection) -> ReconciliationReport:
    """Check persisted fact membership and report the limits of monthly history.

    Run after ``load_analytics`` on the same database. This function never
    modifies data and reports a clear error if the analytical schema is absent.
    """
    required = {
        "analytics_load_run",
        "analytics_reconciliation",
        "analytics_pipeline_membership",
        "FATO_CICLO_PESQUISA",
        "FATO_PARTICIPACAO",
        "FATO_PIPELINE_MENSAL",
        "FATO_PESQUISA_PERGUNTA",
        "DIM_PESQUISA",
    }
    existing = {
        row[0]
        for row in con.execute("""SELECT table_name FROM information_schema.tables
            WHERE table_schema = current_schema()""").fetchall()
    }
    missing_tables = sorted(required - existing)
    if missing_tables:
        raise RuntimeError(
            "camada analítica ausente; execute load_analytics antes da reconciliação: "
            + ", ".join(missing_tables)
        )
    selected = selected_respondentes(con)
    manifest = con.execute("""SELECT load_id, loaded_at, pesquisas_digest,
        empresas_digest, clientes_digest, questoes_digest, respondentes_checksum
        FROM "analytics_load_run" ORDER BY loaded_at DESC, load_id DESC LIMIT 1""").fetchone()
    current_digests = current_source_digests(con)
    source_digests_match = (
        manifest is not None
        and all(
            manifest[index] == current_digests[source]
            for index, source in enumerate(("pesquisas", "empresas", "clientes", "questoes"), 2)
        )
        and manifest[6] == (selected[0] if selected else None)
    )
    cycle = _current_cube(
        con,
        "C01",
        'SELECT pesquisa_id FROM "ingestao_pesquisas_atual"',
        'SELECT d.pesquisa_id FROM "FATO_CICLO_PESQUISA" f '
        'JOIN "DIM_PESQUISA" d USING (sk_pesquisa)',
    )
    if selected is None:
        loaded = _scalar(con, 'SELECT count(*) FROM "FATO_PARTICIPACAO"')
        participation = CubeCount("C02", None, loaded, 0, None, 0, loaded, "source_unavailable")
    else:
        checksum = selected[0]
        participation = _current_cube(
            con,
            "C02",
            'SELECT source_checksum, source_offset FROM "ingestao_respondentes" '
            "WHERE source_checksum = ?",
            'SELECT source_checksum, source_offset FROM "FATO_PARTICIPACAO" '
            "WHERE source_checksum = ?",
            (checksum,),
        )
        # A fact from an earlier checksum is an unexpected loaded occurrence.
        extra = _scalar(
            con,
            'SELECT count(*) FROM "FATO_PARTICIPACAO" WHERE source_checksum <> ?',
            (checksum,),
        )
        if extra:
            participation = CubeCount(
                "C02",
                participation.eligible,
                participation.loaded + extra,
                0,
                participation.difference - extra if participation.difference is not None else None,
                participation.missing_keys,
                participation.unexpected_keys + extra,
                "mismatch",
            )
    instrument = _current_cube(
        con,
        "C04",
        'SELECT pesquisa_id, pergunta_id FROM "ingestao_questoes_atual"',
        "SELECT pesquisa_id_origem AS pesquisa_id, pergunta_id_origem AS pergunta_id "
        'FROM "FATO_PESQUISA_PERGUNTA"',
    )
    closure_rows = con.execute("""
        SELECT CAST(data_fim_mes AS VARCHAR), count(*), sum(qtd_pesquisas_no_status),
               count(DISTINCT (sk_status, sk_area, sk_tipo, sk_perfil)),
               count(DISTINCT observed_at)
        FROM "FATO_PIPELINE_MENSAL" GROUP BY data_fim_mes ORDER BY data_fim_mes
    """).fetchall()
    closures = tuple(
        {
            "month": month,
            "groups": groups,
            "stock": stock,
            "distinct_groups": distinct_groups,
            "observations": observations,
        }
        for month, groups, stock, distinct_groups, observations in closure_rows
    )
    monthly = _monthly_cube(con)
    orphan_rows = con.execute("""
        SELECT source, target, reason, method, count(*)
        FROM "analytics_reconciliation"
        GROUP BY source, target, reason, method
        ORDER BY source, target, reason, method
    """).fetchall()
    orphan_reasons = tuple(
        {
            "source": source,
            "target": target,
            "reason": reason,
            "method": method,
            "count": count,
        }
        for source, target, reason, method, count in orphan_rows
    )
    checks = (
        ("respondentes", "DIM_PESQUISA", "pesquisa_id_ausente", "FATO_PARTICIPACAO", "sk_pesquisa"),
        ("respondentes", "DIM_EMPRESA", "empresa_id_ausente", "FATO_PARTICIPACAO", "sk_empresa"),
        ("respondentes", "DIM_PESSOA", "cliente_id_ausente", "FATO_PARTICIPACAO", "sk_pessoa"),
    )
    orphan_audit = []
    for source, target, reason, table, column in checks:
        expected = _scalar(
            con, f'SELECT count(*) FROM "{table}" WHERE "{column}" = ?', (unknown_key(target),)
        )
        logged = _scalar(
            con,
            """SELECT count(*) FROM "analytics_reconciliation"
            WHERE source = ? AND target = ? AND reason = ?""",
            (source, target, reason),
        )
        orphan_audit.append(
            {
                "source": source,
                "target": target,
                "reason": reason,
                "expected": expected,
                "logged": logged,
            }
        )
    question_unknown = _scalar(
        con,
        'SELECT count(*) FROM "FATO_PESQUISA_PERGUNTA" WHERE sk_pesquisa = ?',
        (unknown_key("DIM_PESQUISA"),),
    )
    question_logged = _scalar(
        con,
        """SELECT count(*) FROM "analytics_reconciliation"
        WHERE source = 'questoes' AND target = 'DIM_PESQUISA'
        AND reason IN ('titulo_ambiguo', 'pesquisa_nao_encontrada')""",
    )
    orphan_audit.append(
        {
            "source": "questoes",
            "target": "DIM_PESQUISA",
            "reason": "sem_vinculo_unico",
            "expected": question_unknown,
            "logged": question_logged,
        }
    )
    return ReconciliationReport(
        manifest[0] if manifest else None,
        manifest[1].isoformat() if manifest else None,
        source_digests_match,
        selected[0] if selected else None,
        selected[1] if selected else None,
        (cycle, participation, monthly, instrument),
        orphan_reasons,
        tuple(orphan_audit),
        closures,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", help="arquivo DuckDB com ingestão e cubos carregados")
    args = parser.parse_args()
    con = duckdb.connect(args.database, read_only=True)
    try:
        report = reconcile_analytics(con)
    finally:
        con.close()
    print(json.dumps(report.as_dict(), ensure_ascii=False, sort_keys=True))
    if not report.reconciled:
        parser.exit(1)


if __name__ == "__main__":
    main()
