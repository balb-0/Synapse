"""Carga transacional dos quatro cubos sobre a ingestão tratada em DuckDB."""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import date, datetime

import duckdb

from etl.analytics.dimensions_ddl import (
    canonical_key,
    dimension_statements,
    surrogate_key,
    unknown_key,
)
from etl.analytics.facts_cycle_participation import fact_statements as cycle_statements
from etl.analytics.facts_pipeline_instrument import fact_statements as other_statements


@dataclass(frozen=True)
class LoadResult:
    load_id: str
    pesquisas: int
    participacoes: int
    perguntas: int
    orfaos: int
    respondentes_checksum: str | None
    fechamento: date | None


def _rows(con: duckdb.DuckDBPyConnection, sql: str, params: tuple = ()) -> list[dict]:
    cursor = con.execute(sql, params)
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, values, strict=True)) for values in cursor.fetchall()]


def _normalized(value: str | None) -> str | None:
    if value is None:
        return None
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split()) or None


def _digest(rows: list[dict]) -> str:
    """Stable identity fingerprint for a current source view, including empty."""
    material = "".join(
        f"{len(key)}:{key}" for key in sorted(row["idempotency_key"] for row in rows)
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def current_source_digests(con: duckdb.DuckDBPyConnection) -> dict[str, str]:
    """Fingerprint the four current views used by C01/C02 dimensions and C04."""
    return {
        source: _digest(_rows(con, f'SELECT idempotency_key FROM "ingestao_{source}_atual"'))
        for source in ("pesquisas", "empresas", "clientes", "questoes")
    }


def _member(con: duckdb.DuckDBPyConnection, table: str, key: str, attributes: dict) -> str:
    if any(part is None for part in (key,)):
        return unknown_key(table)
    natural = canonical_key(key)
    sk = surrogate_key(table, key)
    columns = {"natural_key": natural, **attributes}
    names = [f'"{name}"' for name in columns]
    values = [sk, *columns.values()]
    con.execute(
        f'INSERT INTO "{table}" ("sk_{_suffix(table)}", {", ".join(names)}) '
        f"VALUES ({', '.join('?' for _ in values)}) "
        f'ON CONFLICT ("sk_{_suffix(table)}") DO NOTHING',
        values,
    )
    existing = con.execute(
        f'SELECT {", ".join(names[1:])} FROM "{table}" WHERE "sk_{_suffix(table)}" = ?', (sk,)
    ).fetchone()
    changed = [
        (name, value)
        for (name, value), old in zip(attributes.items(), existing, strict=True)
        if value != old
    ]
    if changed:
        con.execute(
            f'UPDATE "{table}" SET '
            + ", ".join(f'"{name}" = ?' for name, _ in changed)
            + f' WHERE "sk_{_suffix(table)}" = ?',
            [*(value for _, value in changed), sk],
        )
    return sk


def _suffix(table: str) -> str:
    return {
        "DIM_TEMPO": "tempo",
        "DIM_PESQUISA": "pesquisa",
        "DIM_STATUS_PESQUISA": "status",
        "DIM_AREA": "area",
        "DIM_TIPO_PESQUISA": "tipo",
        "DIM_PERFIL_PESQUISA": "perfil",
        "DIM_EMPRESA": "empresa",
        "DIM_PESSOA": "pessoa",
        "DIM_PERGUNTA": "pergunta",
        "DIM_FAMILIA_PESQUISA": "familia",
        "DIM_FONTE_DADO": "fonte",
        "DIM_EXECUCAO_CARGA": "carga",
    }[table]


def _composite_member(con, table: str, parts: tuple[str | None, ...], attributes: dict) -> str:
    natural = canonical_key(*parts)
    sk = surrogate_key(table, *parts)
    columns = {"natural_key": natural, **attributes}
    names = [f'"{name}"' for name in columns]
    values = [sk, *columns.values()]
    con.execute(
        f'INSERT INTO "{table}" ("sk_{_suffix(table)}", {", ".join(names)}) '
        f"VALUES ({', '.join('?' for _ in values)}) "
        f'ON CONFLICT ("sk_{_suffix(table)}") DO NOTHING',
        values,
    )
    existing = con.execute(
        f'SELECT {", ".join(names[1:])} FROM "{table}" WHERE "sk_{_suffix(table)}" = ?', (sk,)
    ).fetchone()
    changed = [
        (name, value)
        for (name, value), old in zip(attributes.items(), existing, strict=True)
        if value != old
    ]
    if changed:
        con.execute(
            f'UPDATE "{table}" SET '
            + ", ".join(f'"{name}" = ?' for name, _ in changed)
            + f' WHERE "sk_{_suffix(table)}" = ?',
            [*(value for _, value in changed), sk],
        )
    return sk


def _time(con, value: date | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        value = value.date()
    return _member(
        con,
        "DIM_TEMPO",
        value.isoformat(),
        {
            "data": value,
            "ano": value.year,
            "trimestre": (value.month - 1) // 3 + 1,
            "mes": value.month,
            "dia": value.day,
            "dia_semana": value.isoweekday(),
            "fim_mes": value.day == calendar.monthrange(value.year, value.month)[1],
        },
    )


def _duration(start, end) -> int | None:
    return (end - start).days if start and end and end >= start else None


def selected_respondentes(con: duckdb.DuckDBPyConnection) -> tuple[str, str, datetime] | None:
    """Latest complete reconciled respondent file, breaking timestamp ties by checksum."""
    selected = con.execute("""
        SELECT object.source_checksum, object.run_id, object.concluded_at
        FROM "_control_object" object
        JOIN "reconciliacao_execucao" rec ON rec.run_id = object.run_id
        WHERE object.source = 'respondentes' AND object.source_checksum IS NOT NULL
          AND object.source_checksum <> '' AND rec.conciliado
          AND rec.status <> 'falha'
          AND EXISTS (SELECT 1 FROM "_batch_metadata" batch
                      WHERE batch.run_id = object.run_id AND batch.source = 'respondentes'
                        AND batch.status <> 'falha')
          AND NOT EXISTS (SELECT 1 FROM "_batch_metadata" batch
                          WHERE batch.run_id = object.run_id AND batch.source = 'respondentes'
                            AND batch.status = 'falha')
        ORDER BY object.concluded_at DESC, object.source_checksum DESC
        LIMIT 1
    """).fetchone()
    return selected


def _orphan(
    con,
    source: str,
    source_id: str | None,
    target: str,
    reason: str,
    method: str = "unknown",
    matched_id: str | None = None,
) -> None:
    con.execute(
        """INSERT INTO "analytics_reconciliation"
        (source, source_id, target, reason, method, matched_id)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (source, source_id, target, reason, method, matched_id),
    )


def _ensure_analytics_schema(con: duckdb.DuckDBPyConnection) -> None:
    """Create dimensions, facts and technical control tables inside the caller transaction."""
    for statement in (*dimension_statements(), *cycle_statements(), *other_statements()):
        con.execute(statement)
    con.execute("""CREATE TABLE IF NOT EXISTS "analytics_reconciliation" (
        source VARCHAR NOT NULL, source_id VARCHAR, target VARCHAR NOT NULL,
        reason VARCHAR NOT NULL, method VARCHAR NOT NULL, matched_id VARCHAR
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS "analytics_pipeline_membership" (
        data_fim_mes DATE NOT NULL, sk_pesquisa VARCHAR NOT NULL,
        sk_status VARCHAR NOT NULL, sk_area VARCHAR NOT NULL,
        sk_tipo VARCHAR NOT NULL, sk_perfil VARCHAR NOT NULL,
        observed_at TIMESTAMP NOT NULL,
        PRIMARY KEY (data_fim_mes, sk_pesquisa)
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS "analytics_pipeline_closure" (
        data_fim_mes DATE PRIMARY KEY, observed_at TIMESTAMP NOT NULL,
        load_id VARCHAR NOT NULL
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS "analytics_load_run" (
        load_id VARCHAR PRIMARY KEY, loaded_at TIMESTAMP NOT NULL,
        pesquisas_digest VARCHAR NOT NULL, empresas_digest VARCHAR NOT NULL,
        clientes_digest VARCHAR NOT NULL, questoes_digest VARCHAR NOT NULL,
        respondentes_checksum VARCHAR, observed_at TIMESTAMP
    )""")


def _replace_current_facts(con: duckdb.DuckDBPyConnection, *, preserve_participation: bool) -> None:
    """Rebuild current facts before Type 1 updates; preserve C02 when its source is absent."""
    # DuckDB keeps FK references to deleted rows until commit. Rebuild the
    # three current facts transactionally before refreshing Type 1 members.
    if preserve_participation:
        con.execute('CREATE TEMP TABLE _previous_participacao AS SELECT * FROM "FATO_PARTICIPACAO"')
    for table in ("FATO_PESQUISA_PERGUNTA", "FATO_PARTICIPACAO", "FATO_CICLO_PESQUISA"):
        con.execute(f'DROP TABLE "{table}"')
    for statement in (*cycle_statements(), *other_statements()):
        con.execute(statement)
    if preserve_participation:
        con.execute('INSERT INTO "FATO_PARTICIPACAO" SELECT * FROM _previous_participacao')
        con.execute("DROP TABLE _previous_participacao")


def load_entity_dimensions(
    con: duckdb.DuckDBPyConnection, empresas: list[dict], clientes: list[dict]
) -> None:
    """Refresh conformed company and person members; the caller owns the transaction."""
    for row in empresas:
        _member(
            con,
            "DIM_EMPRESA",
            row["empresa_id"],
            {
                name: row[name]
                for name in (
                    "empresa_id",
                    "nome_fantasia",
                    "part_mercado",
                    "nacionalidade",
                    "associado",
                    "tipo_associado",
                    "cidade",
                    "estado",
                    "pais",
                )
            },
        )
    for row in clientes:
        _member(
            con,
            "DIM_PESSOA",
            row["cliente_id"],
            {
                "cliente_id": row["cliente_id"],
                "empresa_id": row["empresa_id"],
                "cargo": row["cargo"],
                "departamento": row["departamento"],
            },
        )


def load_cycle_fact(con: duckdb.DuckDBPyConnection, pesquisas: list[dict]) -> None:
    """Load C01 and its conformed research, category, date and execution members."""
    runs: dict[tuple[str, str], list] = {}
    for row in pesquisas:
        pair = (row["source"], row["run_id"])
        runs.setdefault(pair, []).append(row)
    for (source, run_id), run_rows in sorted(runs.items()):
        checksums = {row["source_checksum"] for row in run_rows}
        _composite_member(
            con,
            "DIM_EXECUCAO_CARGA",
            (source, run_id),
            {
                "source": source,
                "run_id": run_id,
                "concluded_at": max(row["ingested_at"] for row in run_rows),
                "source_checksum": next(iter(checksums)) if len(checksums) == 1 else None,
            },
        )
    for row in pesquisas:
        pid = row["pesquisa_id"]
        sk = _member(
            con,
            "DIM_PESQUISA",
            pid,
            {"pesquisa_id": pid, "titulo": row["titulo"], "objetivos": row["objetivos"]},
        )
        category = {}
        for table, field in (
            ("DIM_AREA", "area"),
            ("DIM_STATUS_PESQUISA", "status"),
            ("DIM_TIPO_PESQUISA", "tipo"),
        ):
            value = _normalized(row[field])
            category[table] = (
                _member(con, table, value, {field: value}) if value else unknown_key(table)
            )
        profile_parts = (_normalized(row["complexidade"]), _normalized(row["tipo_resposta"]))
        profile = (
            _composite_member(
                con,
                "DIM_PERFIL_PESQUISA",
                profile_parts,
                {"complexidade": profile_parts[0], "tipo_resposta": profile_parts[1]},
            )
            if any(profile_parts)
            else unknown_key("DIM_PERFIL_PESQUISA")
        )
        family = _normalized(row["titulo"])
        family_sk = (
            _member(
                con,
                "DIM_FAMILIA_PESQUISA",
                family,
                {"titulo_normalizado": family, "estado_homologacao": "pendente"},
            )
            if family
            else unknown_key("DIM_FAMILIA_PESQUISA")
        )
        source = row["source"]
        run_id = row["run_id"]
        source_sk = _member(con, "DIM_FONTE_DADO", source, {"source": source})
        load_sk = surrogate_key("DIM_EXECUCAO_CARGA", source, run_id)
        dates = [
            row[name]
            for name in (
                "data_solicitacao",
                "data_aprov",
                "data_divulgacao",
                "data_limite",
                "prorrogada_ate",
                "data_entrega",
            )
        ]
        limit = dates[4] or dates[3]
        con.execute(
            """INSERT INTO "FATO_CICLO_PESQUISA" VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                sk,
                *(_time(con, day) for day in dates),
                category["DIM_AREA"],
                category["DIM_STATUS_PESQUISA"],
                category["DIM_TIPO_PESQUISA"],
                profile,
                family_sk,
                source_sk,
                load_sk,
                _duration(dates[0], dates[1]),
                _duration(dates[2], limit),
                _duration(limit, dates[5]),
                _duration(dates[0], dates[5]),
                row["participantes"],
                dates[4] is not None,
            ),
        )


def load_participation_fact(
    con: duckdb.DuckDBPyConnection,
    selected: tuple[str, str, datetime] | None,
    pesquisas: list[dict],
    empresas: list[dict],
    clientes: list[dict],
) -> int:
    """Load C02 occurrences and orphan reasons from the selected reconciled export."""
    pesquisa_ids = {row["pesquisa_id"] for row in pesquisas}
    pesquisa_by_id = {row["pesquisa_id"]: row for row in pesquisas}
    empresa_ids = {row["empresa_id"] for row in empresas}
    cliente_ids = {row["cliente_id"] for row in clientes}
    participacoes = 0
    if selected:
        checksum = selected[0]
        respondents = _rows(
            con,
            """SELECT * FROM "ingestao_respondentes"
            WHERE source_checksum = ? ORDER BY source_offset""",
            (checksum,),
        )
        sequence: dict[tuple[str, str], int] = {}
        for row in respondents:
            pid, eid, cid = row["pesquisa_id"], row["empresa_id"], row["cliente_id"]
            if pid not in pesquisa_ids:
                _orphan(
                    con,
                    "respondentes",
                    f"{checksum}:{row['source_offset']}",
                    "DIM_PESQUISA",
                    "pesquisa_id_ausente",
                )
            if eid not in empresa_ids:
                _orphan(
                    con,
                    "respondentes",
                    f"{checksum}:{row['source_offset']}",
                    "DIM_EMPRESA",
                    "empresa_id_ausente",
                )
            if cid and cid not in cliente_ids:
                _orphan(
                    con,
                    "respondentes",
                    f"{checksum}:{row['source_offset']}",
                    "DIM_PESSOA",
                    "cliente_id_ausente",
                )
            person = (
                surrogate_key("DIM_PESSOA", cid)
                if cid in cliente_ids
                else unknown_key("DIM_PESSOA")
                if cid
                else None
            )
            seq = None
            if cid:
                pair = (pid, cid)
                sequence[pair] = sequence.get(pair, 0) + 1
                seq = sequence[pair]
            start, end = row["hora_inicio"], row["hora_termino"]
            minutes = (
                int((end - start).total_seconds() // 60) if start and end and end >= start else None
            )
            reason = (
                None
                if minutes is not None
                else (
                    "inicio_ausente"
                    if start is None
                    else "termino_ausente"
                    if end is None
                    else "termino_anterior_ao_inicio"
                )
            )
            con.execute(
                """INSERT INTO "FATO_PARTICIPACAO" VALUES
                (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)""",
                (
                    checksum,
                    row["source_offset"],
                    surrogate_key("DIM_PESQUISA", pid)
                    if pid in pesquisa_ids
                    else unknown_key("DIM_PESQUISA"),
                    surrogate_key("DIM_EMPRESA", eid)
                    if eid in empresa_ids
                    else unknown_key("DIM_EMPRESA"),
                    person,
                    _time(con, pesquisa_by_id[pid]["data_divulgacao"])
                    if pid in pesquisa_by_id
                    else None,
                    _time(con, start),
                    seq,
                    minutes,
                    reason,
                    row["market_share"],
                ),
            )
            participacoes += 1
    return participacoes


def load_instrument_fact(
    con: duckdb.DuckDBPyConnection, questoes: list[dict], pesquisas: list[dict]
) -> None:
    """Load C04, retaining unmatched questions and uniquely matched research titles."""
    pesquisa_ids = {row["pesquisa_id"] for row in pesquisas}
    pesquisa_by_id = {row["pesquisa_id"]: row for row in pesquisas}
    title_ids: dict[str, set[str]] = {}
    for row in pesquisas:
        title = _normalized(row["titulo"])
        if title:
            title_ids.setdefault(title, set()).add(row["pesquisa_id"])
    for row in questoes:
        qid, pid = row["pergunta_id"], row["pesquisa_id"]
        question_source_id = json.dumps([pid, qid], ensure_ascii=False)
        question_sk = _composite_member(
            con,
            "DIM_PERGUNTA",
            (pid, qid),
            {
                name: row[name]
                for name in (
                    "pesquisa_id",
                    "pergunta_id",
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
                )
            },
        )
        target = pid if pid in pesquisa_ids else None
        method = "id" if target else "desconhecido"
        if target is None:
            matches = title_ids.get(_normalized(row["pesquisa_titulo"]), set())
            if len(matches) == 1:
                target = next(iter(matches))
                method = "titulo_unico"
                _orphan(
                    con,
                    "questoes",
                    question_source_id,
                    "DIM_PESQUISA",
                    "id_divergente",
                    "titulo_exato_unico",
                    target,
                )
            else:
                _orphan(
                    con,
                    "questoes",
                    question_source_id,
                    "DIM_PESQUISA",
                    "titulo_ambiguo" if matches else "pesquisa_nao_encontrada",
                )
        con.execute(
            """INSERT INTO "FATO_PESQUISA_PERGUNTA"
            (sk_pesquisa, sk_pergunta, sk_data_pesquisa,
             pesquisa_id_origem, pergunta_id_origem, metodo_vinculo)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                surrogate_key("DIM_PESQUISA", target) if target else unknown_key("DIM_PESQUISA"),
                question_sk,
                _time(con, pesquisa_by_id[target]["data_divulgacao"]) if target else None,
                pid,
                qid,
                method,
            ),
        )


def load_monthly_fact(
    con: duckdb.DuckDBPyConnection,
    observed_at: datetime | None,
    load_id: str,
) -> date | None:
    """Record a prospective C03 closure only when a newer real month-end observation exists."""
    closure = None
    if observed_at is not None:
        closure = observed_at.date()
        prior_closure = con.execute(
            'SELECT observed_at FROM "analytics_pipeline_closure" WHERE data_fim_mes = ?',
            (closure,),
        ).fetchone()
        existing = prior_closure[0] if prior_closure else None
        if existing is None or observed_at > existing:
            con.execute('DELETE FROM "FATO_PIPELINE_MENSAL" WHERE data_fim_mes = ?', (closure,))
            con.execute(
                'DELETE FROM "analytics_pipeline_membership" WHERE data_fim_mes = ?', (closure,)
            )
            con.execute(
                'DELETE FROM "analytics_pipeline_closure" WHERE data_fim_mes = ?', (closure,)
            )
            con.execute(
                'INSERT INTO "analytics_pipeline_closure" VALUES (?, ?, ?)',
                (closure, observed_at, load_id),
            )
            month_sk = _time(con, closure)
            con.execute(
                '''INSERT INTO "analytics_pipeline_membership"
                SELECT ?, sk_pesquisa, sk_status, sk_area, sk_tipo, sk_perfil, ?
                FROM "FATO_CICLO_PESQUISA"''',
                (closure, observed_at),
            )
            for group in _rows(
                con,
                """SELECT sk_status, sk_area, sk_tipo, sk_perfil,
                    count(*) AS quantity FROM "FATO_CICLO_PESQUISA"
                    GROUP BY sk_status, sk_area, sk_tipo, sk_perfil""",
            ):
                con.execute(
                    """INSERT INTO "FATO_PIPELINE_MENSAL" VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)""",
                    (
                        month_sk,
                        closure,
                        observed_at,
                        group["sk_status"],
                        group["sk_area"],
                        group["sk_tipo"],
                        group["sk_perfil"],
                        group["quantity"],
                    ),
                )
    return closure


def record_load_manifest(
    con: duckdb.DuckDBPyConnection,
    load_id: str,
    pesquisas: list[dict],
    empresas: list[dict],
    clientes: list[dict],
    questoes: list[dict],
    selected: tuple[str, str, datetime] | None,
    observed_at: datetime | None,
) -> None:
    """Persist the exact source fingerprints only after all four cube stages succeed."""
    con.execute(
        """INSERT INTO "analytics_load_run" VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            load_id,
            datetime.now(),
            _digest(pesquisas),
            _digest(empresas),
            _digest(clientes),
            _digest(questoes),
            selected[0] if selected else None,
            observed_at,
        ),
    )


def load_analytics(
    con: duckdb.DuckDBPyConnection,
    *,
    observed_at: datetime | None = None,
    fail_after: str | None = None,
) -> LoadResult:
    """Replace current facts atomically; optional C03 observation is a real month end.

    Each cube stage can be called inside a caller-managed transaction. This
    entry point owns the single transaction spanning dimensions, facts and
    manifest. The caller owns the connection; publication is separate.
    ``fail_after`` is a deterministic transaction fault hook for integration tests.
    """
    if observed_at is not None:
        if observed_at.day != calendar.monthrange(observed_at.year, observed_at.month)[1]:
            raise ValueError("observed_at deve ocorrer no último dia do mês")
    con.execute("BEGIN TRANSACTION")
    try:
        _ensure_analytics_schema(con)
        con.execute("DELETE FROM \"analytics_reconciliation\" WHERE source = 'questoes'")
        pesquisas = _rows(con, 'SELECT * FROM "ingestao_pesquisas_atual" ORDER BY pesquisa_id')
        empresas = _rows(con, 'SELECT * FROM "ingestao_empresas_atual" ORDER BY empresa_id')
        clientes = _rows(con, 'SELECT * FROM "ingestao_clientes_atual" ORDER BY cliente_id')
        questoes = _rows(
            con, 'SELECT * FROM "ingestao_questoes_atual" ORDER BY pesquisa_id, pergunta_id'
        )
        selected = selected_respondentes(con)
        if selected:
            con.execute("DELETE FROM \"analytics_reconciliation\" WHERE source = 'respondentes'")
        _replace_current_facts(con, preserve_participation=not selected)
        load_entity_dimensions(con, empresas, clientes)
        if fail_after == "dimensions":
            raise RuntimeError("injected failure after dimensions")
        load_cycle_fact(con, pesquisas)
        if fail_after == "cycle":
            raise RuntimeError("injected failure after cycle")
        participacoes = load_participation_fact(con, selected, pesquisas, empresas, clientes)
        load_instrument_fact(con, questoes, pesquisas)
        load_id = str(uuid.uuid4())
        closure = load_monthly_fact(con, observed_at, load_id)
        if fail_after == "facts":
            raise RuntimeError("injected failure after facts")
        orphans = con.execute('SELECT count(*) FROM "analytics_reconciliation"').fetchone()[0]
        record_load_manifest(
            con, load_id, pesquisas, empresas, clientes, questoes, selected, observed_at
        )
        con.execute("COMMIT")
        return LoadResult(
            load_id,
            len(pesquisas),
            participacoes,
            len(questoes),
            orphans,
            selected[0] if selected else None,
            closure,
        )
    except Exception:
        con.execute("ROLLBACK")
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", help="Caminho para um DuckDB com ingestão tratada")
    parser.add_argument(
        "--observed-at", help="ISO timestamp de fechamento observado no último dia do mês"
    )
    args = parser.parse_args()
    observed = datetime.fromisoformat(args.observed_at) if args.observed_at else None
    with duckdb.connect(args.database) as con:
        print(load_analytics(con, observed_at=observed))


if __name__ == "__main__":
    main()
