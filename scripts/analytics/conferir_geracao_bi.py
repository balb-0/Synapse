#!/usr/bin/env python3
"""Confere uma geração BI contra seu DuckDB de origem e um recibo do Desktop."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import duckdb

from etl.analytics.load import current_source_digests, selected_respondentes
from etl.analytics.publish import PUBLICATIONS

EXPECTED_COLUMNS = {
    "PUB_C01_CICLO": [
        "area",
        "status",
        "tipo",
        "qtd_pesquisas",
        "soma_dias_validacao",
        "qtd_validacao_disponivel",
        "soma_dias_coleta",
        "qtd_coleta_disponivel",
        "soma_dias_tabulacao",
        "qtd_tabulacao_disponivel",
        "soma_dias_ciclo_total",
        "qtd_ciclo_total_disponivel",
    ],
    "PUB_C02_PARTICIPACAO": [
        "area",
        "tipo",
        "mes_resposta",
        "qtd_participacoes",
        "soma_minutos_preenchimento",
        "qtd_preenchimento_disponivel",
    ],
    "PUB_C03_PIPELINE_MENSAL": [
        "data_fim_mes",
        "status",
        "area",
        "tipo",
        "complexidade",
        "tipo_resposta",
        "qtd_pesquisas_no_status",
        "qtd_entradas_no_mes",
        "qtd_saidas_no_mes",
    ],
    "PUB_C04_INSTRUMENTO": ["area", "tipo_pergunta", "qtd_perguntas"],
    "PUB_QUALIDADE_CAMPO": ["tabela", "campo", "qtd_linhas", "qtd_preenchidas"],
    "PUB_QUALIDADE_RELACAO": ["relacao", "qtd_chaves_informadas", "qtd_chaves_correspondentes"],
    "PUB_QUALIDADE_DUPLICIDADE": ["tabela", "qtd_linhas", "qtd_chaves_distintas"],
}
AGGREGATES = {
    "PUB_C01_CICLO": "qtd_pesquisas",
    "PUB_C02_PARTICIPACAO": "qtd_participacoes",
    "PUB_C03_PIPELINE_MENSAL": "qtd_pesquisas_no_status",
    "PUB_C04_INSTRUMENTO": "qtd_perguntas",
}
FACTS = {
    "PUB_C01_CICLO": "FATO_CICLO_PESQUISA",
    "PUB_C02_PARTICIPACAO": "FATO_PARTICIPACAO",
    "PUB_C04_INSTRUMENTO": "FATO_PESQUISA_PERGUNTA",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _parquet(con: duckdb.DuckDBPyConnection, path: Path, sql: str):
    return con.execute(sql, [str(path)]).fetchall()


def _check_load_reference(con: duckdb.DuckDBPyConnection, reference: str) -> dict:
    has_control = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = current_schema() AND table_name = 'analytics_load_run'"
    ).fetchone()[0]
    if not has_control:
        return {"status": "sem_controle_de_carga_disponivel"}
    run = con.execute(
        "SELECT load_id, pesquisas_digest, empresas_digest, clientes_digest, "
        'questoes_digest, respondentes_checksum FROM "analytics_load_run" '
        "ORDER BY loaded_at DESC, load_id DESC LIMIT 1"
    ).fetchone()
    _require(
        run is not None and run[0] == reference, "load_reference diverge da última carga analítica"
    )
    current = current_source_digests(con)
    for index, source in enumerate(("pesquisas", "empresas", "clientes", "questoes"), 1):
        _require(run[index] == current[source], f"fonte {source} diverge da carga analítica")
    selected = selected_respondentes(con)
    _require(
        run[5] == (selected[0] if selected else None),
        "fonte respondentes diverge da carga analítica",
    )
    return {"status": "confere", "load_id": run[0]}


def conferir(
    geracao: Path, database: Path, desktop: Path | None = None, *, sintetico: bool = False
) -> dict:
    geracao = geracao.resolve(strict=True)
    database = database.resolve(strict=True)
    _require(geracao.is_dir(), "geração deve ser um diretório")
    _require(database.is_file(), "database deve ser um arquivo DuckDB")
    manifest = json.loads((geracao / "manifest.json").read_text())
    _require(manifest.get("version") == 1, "versão do manifesto inválida")
    _require(manifest.get("generation") == geracao.name, "ID da geração diverge do diretório")
    reference = manifest.get("load_reference")
    _require(isinstance(reference, str) and bool(reference), "load_reference ausente")
    is_synthetic = reference.lower().startswith("synthetic")
    _require(not is_synthetic or sintetico, "geração sintética exige --sintetico")
    tables = manifest.get("tables")
    _require(
        isinstance(tables, dict) and set(tables) == set(EXPECTED_COLUMNS),
        "manifesto deve declarar exatamente as sete tabelas",
    )
    _require(
        set(PUBLICATIONS) == set(EXPECTED_COLUMNS),
        "contrato de publicação mudou; revisar o conferidor",
    )
    expected_files = {"manifest.json"} | {f"{name}.parquet" for name in EXPECTED_COLUMNS}
    _require(
        {path.name for path in geracao.iterdir()} == expected_files,
        "arquivos da geração divergem do manifesto",
    )

    report = {
        "generation": geracao.name,
        "load_reference": reference,
        "synthetic": is_synthetic,
        "preparation": {"status": "ok", "tables": {}},
        "desktop": {"status": "pendente"},
        "final_acceptance": "pendente",
    }
    con = duckdb.connect(str(database), read_only=True)
    try:
        report["preparation"]["source_control"] = _check_load_reference(con, reference)
        for name, columns in EXPECTED_COLUMNS.items():
            entry = tables[name]
            _require(isinstance(entry, dict), f"{name}: entrada inválida")
            _require(entry.get("file") == f"{name}.parquet", f"{name}: nome do arquivo inválido")
            _require(entry.get("columns") == columns, f"{name}: colunas do manifesto divergentes")
            _require(
                type(entry.get("rows")) is int and entry["rows"] >= 0, f"{name}: contagem inválida"
            )
            _require(
                isinstance(entry.get("sha256"), str)
                and re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) is not None,
                f"{name}: SHA256 inválido",
            )
            path = geracao / entry["file"]
            _require(path.is_file() and not path.is_symlink(), f"{name}: Parquet ausente ou link")
            _require(_sha256(path) == entry["sha256"], f"{name}: SHA256 divergente")
            observed_columns = [
                column[0]
                for column in con.execute(
                    "SELECT * FROM read_parquet(?) LIMIT 0", [str(path)]
                ).description
            ]
            _require(observed_columns == columns, f"{name}: colunas físicas divergentes")
            rows = _parquet(con, path, "SELECT COUNT(*) FROM read_parquet(?)")[0][0]
            _require(rows == entry["rows"], f"{name}: contagem Parquet/manifesto divergente")
            source_rows = con.execute(f"SELECT COUNT(*) FROM ({PUBLICATIONS[name]})").fetchone()[0]
            _require(rows == source_rows, f"{name}: contagem Parquet/DuckDB divergente")
            report["preparation"]["tables"][name] = rows

        report["preparation"]["aggregates"] = {}
        for name, fact in FACTS.items():
            column = AGGREGATES[name]
            actual = _parquet(
                con,
                geracao / f"{name}.parquet",
                f"SELECT COALESCE(SUM({column}), 0)::BIGINT FROM read_parquet(?)",
            )[0][0]
            expected = con.execute(f"SELECT COUNT(*) FROM {fact}").fetchone()[0]
            _require(actual == expected, f"{name}: agregado diverge do fato {fact}")
            report["preparation"]["aggregates"][name] = actual

        # Estoque de C03 é semiaditivo: comparar cada fechamento observado isoladamente.
        source_months = [
            (str(month), total)
            for month, total in con.execute(
                "SELECT data_fim_mes, SUM(qtd_pesquisas_no_status)::BIGINT FROM FATO_PIPELINE_MENSAL GROUP BY 1 ORDER BY 1"
            ).fetchall()
        ]
        file_months = [
            (str(month), total)
            for month, total in _parquet(
                con,
                geracao / "PUB_C03_PIPELINE_MENSAL.parquet",
                "SELECT data_fim_mes, SUM(qtd_pesquisas_no_status)::BIGINT FROM read_parquet(?) GROUP BY 1 ORDER BY 1",
            )
        ]
        _require(
            file_months == source_months, "PUB_C03_PIPELINE_MENSAL: estoque por fechamento diverge"
        )
        report["preparation"]["c03_stock_by_month"] = [
            {"month_end": month, "stock": total} for month, total in file_months
        ]
        report["preparation"]["c03_observation"] = (
            "observado" if file_months else "sem_fechamento_observado_na_publicacao"
        )

        if desktop is not None:
            receipt = json.loads(desktop.read_text())
            _require(receipt.get("generation") == geracao.name, "Desktop: geração diferente")
            _require(
                receipt.get("load_reference") == reference,
                "Desktop: load_reference divergente ou ausente",
            )
            receipt_tables = receipt.get("tables")
            _require(
                isinstance(receipt_tables, dict)
                and set(receipt_tables) == set(EXPECTED_COLUMNS)
                and all(type(value) is int and value >= 0 for value in receipt_tables.values())
                and receipt_tables == report["preparation"]["tables"],
                "Desktop: contagens divergentes",
            )
            aggregates = receipt.get("aggregates")
            _require(
                isinstance(aggregates, dict) and set(aggregates) == set(AGGREGATES),
                "Desktop: exige agregado por cubo C01, C02, C03 e C04",
            )
            for table, column in AGGREGATES.items():
                aggregate = aggregates[table]
                _require(
                    isinstance(aggregate, dict) and aggregate.get("column") == column,
                    f"Desktop: agregado {table} inválido",
                )
                if table == "PUB_C03_PIPELINE_MENSAL":
                    if file_months:
                        _require(
                            set(aggregate) == {"column", "month_end", "value"}
                            and type(aggregate.get("value")) is int,
                            "Desktop: C03 exige fechamento observado e estoque numérico",
                        )
                        matching = [
                            stock for date, stock in file_months if date == aggregate["month_end"]
                        ]
                        _require(len(matching) == 1, "Desktop: fechamento C03 não observado")
                        expected = matching[0]
                    else:
                        _require(
                            aggregate
                            == {
                                "column": column,
                                "state": "sem_fechamento_observado",
                                "value": None,
                            },
                            "Desktop: C03 sem fechamento exige estado indisponível e valor nulo",
                        )
                        continue
                else:
                    _require(
                        set(aggregate) == {"column", "value"}
                        and type(aggregate.get("value")) is int,
                        f"Desktop: valor agregado {table} inválido",
                    )
                    expected = report["preparation"]["aggregates"][table]
                _require(aggregate["value"] == expected, f"Desktop: agregado {table} divergente")
            report["desktop"] = {
                "status": "recibo_confere",
                "aggregates": aggregates,
                "note": "O recibo não comprova por si só execução ou atualização no Desktop.",
            }
    finally:
        con.close()
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geracao", required=True, type=Path)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--desktop", type=Path, help="recibo JSON de conferência no Desktop")
    parser.add_argument(
        "--sintetico",
        action="store_true",
        help="permite apenas ensaio com load_reference synthetic*",
    )
    args = parser.parse_args()
    try:
        result = conferir(args.geracao, args.database, args.desktop, sintetico=args.sintetico)
    except (OSError, ValueError, duckdb.Error, json.JSONDecodeError) as exc:
        result = {
            "preparation": {"status": "falha"},
            "desktop": {"status": "nao_conferido"},
            "final_acceptance": "pendente",
            "error": str(exc),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(1) from None
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
