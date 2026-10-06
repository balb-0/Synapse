"""Qualidade de respondentes acompanha a ocorrência selecionada em C02."""

import copy
import hashlib
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

import duckdb

from etl.analytics.load import load_analytics, selected_respondentes
from etl.analytics.publish import publish_cubes
from etl.analytics.reconcile import reconcile_analytics
from etl.load.ddl import table_statements, view_statements
from etl.orchestration import analytics as analytics_module
from scripts.analytics.conferir_geracao_bi import conferir


class QualitySnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.database = root / "private.duckdb"
        self.output = root / "published"
        with duckdb.connect(str(self.database)) as con:
            for statement in (*table_statements(), *view_statements()):
                con.execute(statement)
        self.insert("pesquisas", "p1", "ref", pesquisa_id="p1")
        self.insert("empresas", "e1", "ref", empresa_id="e1")
        self.insert("clientes", "c1", "ref", cliente_id="c1", empresa_id="e1")

    def insert(self, source, identity, checksum, **business):
        values = {
            **business,
            "source": source,
            "run_id": checksum,
            "task_id": "t1",
            "batch_id": "b1",
            "source_checksum": checksum,
            "source_offset": int(identity[-1]),
            "content_checksum": identity,
            "record_identity": identity,
            "idempotency_key": identity,
            "ingested_at": datetime(2026, 9, 1),
            "schema_version": "1.0",
        }
        columns = ", ".join(f'"{name}"' for name in values)
        with duckdb.connect(str(self.database)) as con:
            con.execute(
                f'INSERT INTO "ingestao_{source}" ({columns}) '
                f"VALUES ({', '.join('?' for _ in values)})",
                list(values.values()),
            )

    def complete(self, checksum, day, *, incomplete=False):
        at = datetime(2026, 9, day)
        with duckdb.connect(str(self.database)) as con:
            count = con.execute(
                "SELECT count(*) FROM ingestao_respondentes WHERE source_checksum=?", [checksum]
            ).fetchone()[0]
            con.execute(
                """INSERT INTO _batch_metadata VALUES
                ('respondentes', ?, 't1', 'b1', 'carregado', ?, ?, 0, 0, 10, '1.0', ?, ?, ?)""",
                [checksum, count + int(incomplete), count, checksum, at, at],
            )
            con.execute(
                "INSERT INTO _control_object VALUES ('respondentes', ?, ?, ?)",
                [checksum, checksum, at],
            )

    def load(self, observed_at=None):
        with duckdb.connect(str(self.database)) as con:
            result = load_analytics(con, observed_at=observed_at)
            self.assertTrue(reconcile_analytics(con).reconciled)
        return result.load_id

    def current_snapshot(self):
        self.insert(
            "respondentes",
            "old1",
            "old-file",
            pesquisa_id="missing-p",
            empresa_id="missing-e",
            cliente_id="missing-c",
        )
        self.complete("old-file", 1)
        self.load()
        for index in (1, 2):
            self.insert(
                "respondentes",
                f"new{index}",
                "new'file",
                pesquisa_id="p1",
                empresa_id="e1",
                cliente_id="c1",
                hora_termino=datetime(2026, 9, 2),
            )
        self.complete("new'file", 2)
        return self.load()

    def publish(self, load_id):
        manifest = publish_cubes(self.database, self.output, load_reference=load_id)
        generation = self.output / manifest["generation"]
        self.assertEqual(len(list(generation.glob("*.parquet"))), 7)
        result = conferir(generation, self.database)
        self.assertEqual(result["preparation"]["status"], "ok")
        self.assertEqual(result["final_acceptance"], "pendente")
        return manifest, generation, result

    def rows(self, generation, table, query):
        with duckdb.connect() as con:
            return con.execute(query, [str(generation / f"{table}.parquet")]).fetchall()

    def test_two_loads_do_not_publish_old_orphans_or_old_nulls(self):
        load_id = self.current_snapshot()
        # Histórico físico de pesquisas permanece na medida de duplicidade.
        self.insert("pesquisas", "version2", "ref2", pesquisa_id="p1")
        load_id = self.load()
        manifest, generation, _ = self.publish(load_id)
        c02 = self.rows(
            generation, "PUB_C02_PARTICIPACAO", "SELECT sum(qtd_participacoes) FROM read_parquet(?)"
        )
        self.assertEqual(c02, [(2,)])
        filled = self.rows(
            generation,
            "PUB_QUALIDADE_CAMPO",
            "SELECT qtd_linhas,qtd_preenchidas FROM read_parquet(?) WHERE tabela='respondentes' AND campo='hora_termino'",
        )
        self.assertEqual(filled, [(2, 2)])
        relations = self.rows(
            generation,
            "PUB_QUALIDADE_RELACAO",
            "SELECT qtd_chaves_informadas,qtd_chaves_correspondentes FROM read_parquet(?) WHERE relacao LIKE 'respondentes.%'",
        )
        self.assertEqual(relations, [(2, 2)] * 3)
        duplicates = self.rows(
            generation,
            "PUB_QUALIDADE_DUPLICIDADE",
            "SELECT qtd_linhas,qtd_chaves_distintas FROM read_parquet(?) WHERE tabela='pesquisas'",
        )
        self.assertEqual(duplicates, [(2, 1)])
        with duckdb.connect(str(self.database)) as con:
            self.assertEqual(
                con.execute("SELECT count(*) FROM ingestao_respondentes").fetchone()[0], 3
            )
        for name in ("PUB_QUALIDADE_CAMPO", "PUB_QUALIDADE_RELACAO"):
            self.assertEqual(
                manifest["tables"][name]["population_scope"]["respondentes"],
                "selected_reconciled_c02_snapshot",
            )
            self.assertNotIn("source_checksum", manifest["tables"][name]["columns"])

    def test_newer_incomplete_snapshot_does_not_replace_last_reconciled_file(self):
        self.current_snapshot()
        self.insert(
            "respondentes",
            "partial1",
            "partial-file",
            pesquisa_id="missing-p",
            empresa_id="missing-e",
        )
        self.complete("partial-file", 3, incomplete=True)
        with duckdb.connect(str(self.database)) as con:
            self.assertEqual(selected_respondentes(con)[0], "new'file")
        load_id = self.load()
        _, generation, _ = self.publish(load_id)
        self.assertEqual(
            self.rows(
                generation,
                "PUB_QUALIDADE_CAMPO",
                "SELECT qtd_linhas,qtd_preenchidas FROM read_parquet(?) WHERE tabela='respondentes' AND campo='hora_termino'",
            ),
            [(2, 2)],
        )

    def test_selected_empty_snapshot_remains_zero_rows_despite_old_nonempty_file(self):
        self.current_snapshot()
        self.complete("empty-current", 3)
        _, generation, _ = self.publish(self.load())
        self.assertEqual(
            self.rows(
                generation,
                "PUB_QUALIDADE_CAMPO",
                "SELECT qtd_linhas,qtd_preenchidas FROM read_parquet(?) WHERE tabela='respondentes' AND campo='hora_termino'",
            ),
            [(0, 0)],
        )
        self.assertEqual(
            self.rows(
                generation,
                "PUB_QUALIDADE_RELACAO",
                "SELECT qtd_chaves_informadas,qtd_chaves_correspondentes FROM read_parquet(?) WHERE relacao LIKE 'respondentes.%'",
            ),
            [(0, 0)] * 3,
        )

    def test_retry_uses_same_snapshot_contract_and_validates_scope_metadata(self):
        load_id = self.current_snapshot()
        first, generation, _ = self.publish(load_id)
        with mock.patch.object(analytics_module, "_event"):
            with mock.patch.object(analytics_module, "publish_cubes") as publisher:
                reused = analytics_module.publish_warehouse.fn(
                    str(self.database), str(self.output), load_id
                )
            publisher.assert_not_called()
            self.assertEqual(reused, first)
            changed = copy.deepcopy(first)
            changed["tables"]["PUB_QUALIDADE_CAMPO"]["population_scope"]["respondentes"] = (
                "physical_ingestion_history"
            )
            (generation / "manifest.json").write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, "semântica do manifesto"):
                conferir(generation, self.database)
            repaired = analytics_module.publish_warehouse.fn(
                str(self.database), str(self.output), load_id
            )
        self.assertNotEqual(first["generation"], repaired["generation"])
        self.assertEqual(
            first["tables"]["PUB_QUALIDADE_CAMPO"], repaired["tables"]["PUB_QUALIDADE_CAMPO"]
        )

    def test_conferidor_distinguishes_observed_zero_from_no_observation(self):
        self.complete("empty-current", 1)
        _, _, missing = self.publish(self.load())
        self.assertEqual(missing["preparation"]["c03_stock_by_month"], [])
        self.assertEqual(
            missing["preparation"]["c03_observation"], "sem_fechamento_observado_na_publicacao"
        )
        with duckdb.connect(str(self.database)) as con:
            con.execute("DELETE FROM ingestao_pesquisas")
        _, _, zero = self.publish(self.load(datetime(2026, 9, 30, 23)))
        self.assertEqual(zero["preparation"]["tables"]["PUB_C03_PIPELINE_MENSAL"], 1)
        self.assertEqual(
            zero["preparation"]["c03_stock_by_month"], [{"month_end": "2026-09-30", "stock": 0}]
        )
        self.assertEqual(zero["preparation"]["c03_observation"], "observado")

    def test_missing_snapshot_is_unavailable_and_cannot_publish_a_verified_zero(self):
        with duckdb.connect(str(self.database)) as con:
            result = load_analytics(con)
            report = reconcile_analytics(con)
        self.assertIsNone(report.respondent_checksum)
        self.assertEqual(report.cubes[1].status, "source_unavailable")
        self.assertFalse(report.reconciled)
        with self.assertRaisesRegex(ValueError, "não reconciliou"):
            publish_cubes(self.database, self.output, load_reference=result.load_id)
        self.assertFalse((self.output / "current.json").exists())

    def test_rehashed_quality_values_are_checked_against_selected_snapshot(self):
        load_id = self.current_snapshot()
        manifest, generation, _ = self.publish(load_id)
        target = generation / "PUB_QUALIDADE_CAMPO.parquet"
        changed = Path(self.temp.name) / "changed.parquet"
        source_literal = "'" + str(target).replace("'", "''") + "'"
        target_literal = "'" + str(changed).replace("'", "''") + "'"
        with duckdb.connect() as con:
            con.execute(
                "COPY (SELECT * REPLACE(CASE WHEN tabela='respondentes' "
                "THEN qtd_linhas+1 ELSE qtd_linhas END AS qtd_linhas) "
                f"FROM read_parquet({source_literal})) TO {target_literal} (FORMAT PARQUET)"
            )
        target.write_bytes(changed.read_bytes())
        manifest["tables"]["PUB_QUALIDADE_CAMPO"]["sha256"] = hashlib.sha256(
            target.read_bytes()
        ).hexdigest()
        (generation / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "conteúdo Parquet/DuckDB"):
            conferir(generation, self.database)


if __name__ == "__main__":
    unittest.main()
