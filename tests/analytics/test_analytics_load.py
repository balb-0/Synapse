"""Integration checks for analytical snapshot replacement and transaction safety."""

import unittest
from datetime import datetime

import duckdb

from etl.analytics.load import load_analytics
from etl.load.ddl import table_statements, view_statements


class AnalyticsLoadTests(unittest.TestCase):
    def setUp(self):
        self.con = duckdb.connect()
        for statement in (*table_statements(), *view_statements()):
            self.con.execute(statement)

    def tearDown(self):
        self.con.close()

    def insert(self, source, identity, offset, **business):
        technical = {
            "source": source, "run_id": "r1", "task_id": "t1", "batch_id": "b1",
            "source_checksum": "file1", "source_offset": offset,
            "content_checksum": f"c{identity}", "record_identity": identity,
            "idempotency_key": identity, "ingested_at": datetime(2026, 9, 1),
            "schema_version": "1.0",
        }
        values = {**business, **technical}
        columns = ", ".join(f'"{name}"' for name in values)
        self.con.execute(
            f'INSERT INTO "ingestao_{source}" ({columns}) '
            f'VALUES ({", ".join("?" for _ in values)})', list(values.values()))

    def reconcile(self, checksum="file1", run="r1", finished=None):
        finished = finished or datetime(2026, 9, 1)
        self.con.execute('''INSERT INTO "_batch_metadata" VALUES
            ('respondentes', ?, 'task', ?, 'carregado', 1, 1, 0, 0, 10,
             '1.0', ?, ?, ?)''', (run, f"{run}-batch", checksum, finished, finished))
        self.con.execute('INSERT INTO "_control_object" VALUES (?, ?, ?, ?)',
                         ("respondentes", checksum, run, finished))

    def test_repeated_load_and_corrected_source(self):
        self.insert("pesquisas", "p1-a", 1, pesquisa_id="p1", titulo="Pesquisa A",
                    status="Aberta", data_solicitacao="2026-09-01", data_aprov="2026-09-03")
        self.insert("empresas", "e1-a", 1, empresa_id="e1")
        self.insert("clientes", "c1-a", 1, cliente_id="c1", empresa_id="e1")
        self.insert("respondentes", "respondent-a", 1, pesquisa_id="p1", empresa_id="e1",
                    cliente_id="c1", hora_inicio="2026-09-01 10:00:00",
                    hora_termino="2026-09-01 10:05:00")
        self.insert("questoes", "q1-a", 1, pesquisa_id="foreign", pergunta_id="q1",
                    pesquisa_titulo="  PESQUISA   A ", tipo="aberta")
        self.reconcile()
        first = load_analytics(self.con)
        self.assertEqual((first.pesquisas, first.participacoes, first.perguntas), (1, 1, 1))
        before = self.con.execute('SELECT * FROM "FATO_CICLO_PESQUISA"').fetchall()
        second_load = load_analytics(self.con)
        self.assertNotEqual(first.load_id, second_load.load_id)
        self.assertEqual((first.pesquisas, first.participacoes, first.perguntas),
                         (second_load.pesquisas, second_load.participacoes, second_load.perguntas))
        self.assertEqual(before, self.con.execute('SELECT * FROM "FATO_CICLO_PESQUISA"').fetchall())
        self.assertEqual(self.con.execute('''SELECT method, matched_id FROM "analytics_reconciliation"
            WHERE source = 'questoes' ''').fetchone(), ("titulo_exato_unico", "p1"))
        self.assertEqual(self.con.execute('''SELECT pesquisa_id_origem, pergunta_id_origem,
            metodo_vinculo FROM "FATO_PESQUISA_PERGUNTA"''').fetchone(),
                         ("foreign", "q1", "titulo_unico"))

        self.insert("pesquisas", "p1-b", 2, pesquisa_id="p1", titulo="Pesquisa A",
                    status="Fechada", data_solicitacao="2026-09-01", data_aprov="2026-09-04")
        second = load_analytics(self.con)
        self.assertEqual(second.participacoes, 1)
        self.assertEqual(self.con.execute('''SELECT dias_corridos_validacao
            FROM "FATO_CICLO_PESQUISA"''').fetchone()[0], 3)
        self.assertEqual(self.con.execute('SELECT count(*) FROM "FATO_PARTICIPACAO"').fetchone()[0], 1)

    def test_rollback_after_failure(self):
        self.insert("pesquisas", "p1-a", 1, pesquisa_id="p1", titulo="Original")
        load_analytics(self.con)
        self.insert("pesquisas", "p1-b", 2, pesquisa_id="p1", titulo="Corrigido")
        with self.assertRaisesRegex(RuntimeError, "injected"):
            load_analytics(self.con, fail_after="facts")
        self.assertEqual(self.con.execute('SELECT count(*) FROM "analytics_load_run"').fetchone()[0], 1)
        self.assertEqual(self.con.execute('SELECT titulo FROM "DIM_PESQUISA" WHERE pesquisa_id = ?',
                                          ("p1",)).fetchone()[0], "Original")
        self.assertEqual(self.con.execute('SELECT count(*) FROM "FATO_CICLO_PESQUISA"').fetchone()[0], 1)

    def test_month_end_is_prospective(self):
        self.insert("pesquisas", "p1-a", 1, pesquisa_id="p1", status="Aberta")
        load_analytics(self.con)
        self.assertEqual(self.con.execute('SELECT count(*) FROM "FATO_PIPELINE_MENSAL"').fetchone()[0], 0)
        with self.assertRaises(ValueError):
            load_analytics(self.con, observed_at=datetime(2026, 9, 29))
        load_analytics(self.con, observed_at=datetime(2026, 9, 30, 23, 0))
        self.assertEqual(self.con.execute('''SELECT qtd_pesquisas_no_status,
            qtd_entradas_no_mes, qtd_saidas_no_mes FROM "FATO_PIPELINE_MENSAL"''').fetchone(),
                         (1, None, None))
        self.assertEqual(self.con.execute('SELECT count(*) FROM "analytics_pipeline_membership"').fetchone()[0], 1)
        self.insert("pesquisas", "p1-b", 2, pesquisa_id="p1", status="Fechada")
        load_analytics(self.con)
        self.assertEqual(self.con.execute('''SELECT count(*) FROM "analytics_pipeline_membership"
            WHERE data_fim_mes = '2026-09-30' ''').fetchone()[0], 1)

    def test_unreconciled_export_does_not_replace_participation(self):
        self.insert("pesquisas", "p1-a", 1, pesquisa_id="p1")
        self.insert("empresas", "e1-a", 1, empresa_id="e1")
        self.insert("respondentes", "r1", 1, pesquisa_id="p1", empresa_id="e1")
        self.reconcile()
        load_analytics(self.con)
        self.insert("respondentes", "r2", 2, pesquisa_id="p1", empresa_id="e1")
        self.con.execute('''UPDATE "ingestao_respondentes" SET source_checksum = 'file2',
            run_id = 'r2' WHERE idempotency_key = 'r2' ''')
        load_analytics(self.con)
        self.assertEqual(self.con.execute('SELECT source_checksum FROM "FATO_PARTICIPACAO"').fetchall(),
                         [("file1",)])

    def test_new_reconciled_export_replaces_previous_occurrences(self):
        self.insert("pesquisas", "p1-a", 1, pesquisa_id="p1")
        self.insert("empresas", "e1-a", 1, empresa_id="e1")
        self.insert("respondentes", "r1", 1, pesquisa_id="p1", empresa_id="e1")
        self.reconcile()
        load_analytics(self.con)
        self.insert("respondentes", "r2", 2, pesquisa_id="p1", empresa_id="e1")
        self.con.execute('''UPDATE "ingestao_respondentes" SET source_checksum = 'file2',
            run_id = 'r2' WHERE idempotency_key = 'r2' ''')
        self.reconcile("file2", "r2", datetime(2026, 9, 2))
        result = load_analytics(self.con)
        self.assertEqual((result.respondentes_checksum, result.participacoes), ("file2", 1))
        self.assertEqual(self.con.execute('SELECT source_checksum FROM "FATO_PARTICIPACAO"').fetchall(),
                         [("file2",)])

    def test_ambiguous_title_keeps_unknown_research(self):
        self.insert("pesquisas", "p1-a", 1, pesquisa_id="p1", titulo="Título Comum")
        self.insert("pesquisas", "p2-a", 2, pesquisa_id="p2", titulo=" título  comum ")
        self.insert("questoes", "q1-a", 1, pesquisa_id="foreign", pergunta_id="q1",
                    pesquisa_titulo="TÍTULO COMUM", tipo="aberta")
        load_analytics(self.con)
        method = self.con.execute('''SELECT metodo_vinculo FROM "FATO_PESQUISA_PERGUNTA"''').fetchone()[0]
        self.assertEqual(method, "desconhecido")
        self.assertEqual(self.con.execute('''SELECT reason FROM "analytics_reconciliation"
            WHERE source = 'questoes' ''').fetchone()[0], "titulo_ambiguo")


if __name__ == "__main__":
    unittest.main()
