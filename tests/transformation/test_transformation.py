import copy
import json
import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from etl.extraction.contracts import BatchMetadata, ExtractedBatch, ExtractionCheckpoint
from etl.transformation import conversion as c
from etl.transformation.consistency import ReferenceData
from etl.transformation.identity import canonical_json, classify_duplicates, digest
from etl.transformation.normalization import normalize_record, string_list
from etl.transformation.pipeline import transform_batch, transform_object
from etl.transformation.quarantine import QuarantineStore
from etl.transformation.schema import SCHEMAS
from etl.transformation.validation import conditional_fields, missing

NOW = datetime(2026, 9, 9, 12, tzinfo=timezone.utc)
RAW = {
    "empresas": {"ID": "1", "Nome Fantasia": "Empresa fictícia", "Associado": "Sim"},
    "pesquisas": {"id": "1", "titulo": "Pesquisa fictícia"},
    "clientes": {"id_cliente": "1", "id_empresa": "1", "e-mail": "teste@example.invalid"},
    "respondentes": {"id_pesq": "1", "id_empresa": "1", "id_cliente": "1"},
    "questoes": {"id_pergunta": "1", "pesquisa_id": "1", "tipo": "aberta"},
    "respostas": {
        "id_resposta": "1",
        "pesquisa_id": "1",
        "id_pergunta": "1",
        "respondent_id": "9007199254740993",
        "valor": "Resposta fictícia",
    },
}


def refs():
    return ReferenceData(
        {
            source: [normalize_record(source, RAW[source])[0]]
            for source in ("empresas", "pesquisas", "clientes", "questoes")
        }
    )


def batch(source, rows, run="run-1", batch_id="batch-1"):
    return ExtractedBatch(
        rows,
        ExtractionCheckpoint(source, "opaque-cursor", 0),
        BatchMetadata(source, run, "task", batch_id, NOW, NOW, len(rows), 100, "1.0", "a" * 64),
    )


def run(source, rows, **kwargs):
    options = dict(references=refs(), previous={}, source_offset=0, ingested_at=NOW)
    options.update(kwargs)
    return transform_batch(batch(source, rows), **options)


class ConversionTests(unittest.TestCase):
    def test_ids_do_not_lose_precision(self):
        for original, expected in [
            ("001", "1"),
            ("12.00", "12"),
            ("9007199254740993", "9007199254740993"),
        ]:
            self.assertEqual(c.identifier(original), expected)
        for value in (True, 1.0, "-1", "1.2", "1e3", "s/i", "9" * 129):
            with self.subTest(value=value), self.assertRaises(c.ConversionError):
                c.identifier(value)

    def test_finite_precise_numbers(self):
        self.assertEqual(c.decimal("1.234,56789"), Decimal("1234.56789"))
        self.assertEqual(c.decimal("100%", True), Decimal(100))
        self.assertEqual(c.decimal("0%", True), Decimal(0))
        for value in (
            "NaN",
            "Infinity",
            "1%2",
            "101%",
            "-1%",
            "1.0000001",
            "1000000000000",
            1.2,
            True,
        ):
            with self.subTest(value=value), self.assertRaises(c.ConversionError):
                c.decimal(value, True)

    def test_integer_destination_limits(self):
        self.assertEqual(c.integer(str(2**63 - 1)), 2**63 - 1)
        for value in ("1.5", str(2**63), str(-(2**63) - 1)):
            with self.assertRaises(c.ConversionError):
                c.integer(value)

    def test_civil_dates(self):
        self.assertEqual(c.civil_date("29/02/2024"), date(2024, 2, 29))
        self.assertEqual(c.civil_date("2024-02-29"), date(2024, 2, 29))
        self.assertEqual(c.civil_date(date(2024, 2, 29)), date(2024, 2, 29))
        for value in ("29/02/2023", "0000-00-00", "2024-01-01T00:00:00Z", NOW, 1, "1899-01-01"):
            with self.subTest(value=value), self.assertRaises(c.ConversionError):
                c.civil_date(value)

    def test_timestamp_requires_explicit_timezone(self):
        self.assertEqual(c.instant("2026-09-09T09:00:00-03:00"), NOW)
        self.assertEqual(c.instant("09/09/2026 09:00", "America/Sao_Paulo"), NOW)
        self.assertEqual(c.instant(NOW), NOW)
        for value in ("2026-09-09", "2026-09-09 09:00:00", "invalid", 1):
            with self.assertRaises(c.ConversionError):
                c.instant(value)

    def test_dst_gap_and_ambiguity(self):
        for value in ("2024-03-10 02:30:00", "2024-11-03 01:30:00"):
            with self.assertRaisesRegex(c.ConversionError, "AMBIGUOUS"):
                c.instant(value, "America/New_York")

    def test_boolean_closed_domain(self):
        for value in ("Sim", "TRUE", True):
            self.assertTrue(c.boolean(value))
        for value in ("Não", "nao", "false", False):
            self.assertFalse(c.boolean(value))
        with self.assertRaises(c.ConversionError):
            c.boolean("talvez")


class SchemaTests(unittest.TestCase):
    def test_every_source_and_field_has_destination(self):
        self.assertEqual(len(SCHEMAS), 6)
        for fields in SCHEMAS.values():
            self.assertEqual(len({f.name for f in fields}), len(fields))
            for f in fields:
                self.assertTrue(f.origin and f.duckdb_type)

    def test_all_six_valid_sources(self):
        for source, row in RAW.items():
            with self.subTest(source=source):
                result = run(source, [row])
                self.assertEqual(len(result.accepted), 1, result.rejected)
                self.assertEqual(set(result.accepted[0].data), {f.name for f in SCHEMAS[source]})
                json.dumps(result.accepted[0].as_duckdb_row(), allow_nan=False)

    def test_unknown_names_collision_and_export_columns(self):
        cases = [
            ("empresas", {"ID": "1", "empresa_id": "1"}, "FIELD_COLLISION"),
            ("empresas", {"ID": "1", "token-do-cliente": "secret"}, "UNKNOWN_FIELD"),
            ("pesquisas", {"id": "1", "": "unexpected"}, "NONEMPTY_EXPORT_COLUMN"),
        ]
        for source, row, code in cases:
            _, errors = normalize_record(source, row)
            self.assertIn(code, [e.code for e in errors])
            self.assertNotIn("secret", repr(errors))
        self.assertFalse(normalize_record("pesquisas", {"id": "1", "": ""})[1])

    def test_sentinels_are_field_specific(self):
        self.assertFalse(missing("NA"))
        self.assertTrue(missing("NA", ("na",)))
        row, errors = normalize_record("clientes", {"id_cliente": "s/i", "id_empresa": "1"})
        self.assertIsNone(row["cliente_id"])
        self.assertIn("REQUIRED", [e.code for e in errors])
        row, errors = normalize_record("empresas", {"ID": "1", "Associado": "-"})
        self.assertIsNone(row["associado"])
        self.assertFalse(errors)

    def test_lists_and_unicode(self):
        self.assertEqual(string_list('["A", "B"]'), ["A", "B"])
        self.assertEqual(string_list("A | B"), ["A", "B"])
        self.assertEqual(c.text(" cafe\u0301 "), "café")
        for value in ("[bad", "[1]", {"x": "y"}, "A||B"):
            with self.assertRaises(c.ConversionError):
                string_list(value)

    def test_input_is_not_mutated(self):
        original = copy.deepcopy(RAW)
        for source, row in RAW.items():
            run(source, [row])
        self.assertEqual(RAW, original)


class ConsistencyTests(unittest.TestCase):
    def test_matrix_count_is_cells_not_alternatives(self):
        raw = {
            **RAW["questoes"],
            "tipo": "matriz_avaliacao",
            "qtd_alternativas": "4",
            "linhas_matriz": "L1|L2",
            "colunas_matriz": "C1|C2",
        }
        self.assertEqual(len(run("questoes", [raw]).accepted), 1)

    def test_missing_reference_is_not_empty_reference(self):
        with self.assertRaisesRegex(ValueError, "REFERENCE_DATA_REQUIRED"):
            run("clientes", [RAW["clientes"]], references=ReferenceData({}))
        result = run("clientes", [RAW["clientes"]], references=ReferenceData({"empresas": []}))
        self.assertEqual(result.rejected[0].violations[0].code, "ORPHAN_REFERENCE")

    def test_duplicate_reference_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_REFERENCE"):
            ReferenceData({"empresas": [{"empresa_id": "1"}, {"empresa_id": "1"}]})

    def test_reference_snapshot_is_not_mutable(self):
        source = {"empresas": [{"empresa_id": "1"}]}
        reference = ReferenceData(source)
        source["empresas"][0]["empresa_id"] = "2"
        self.assertEqual(reference.get("empresas", ("1",))["empresa_id"], "1")

    def test_all_question_types_and_structural_nulls(self):
        valid = {
            "aberta": {"valor": "texto"},
            "numerica": {"valor": "12,5"},
            "multipla_escolha": {"valor": "A"},
            "caixas_de_selecao": {"alternativa": "A"},
            "matriz_avaliacao": {"linha_matriz": "L", "coluna_matriz": "C"},
        }
        for kind, row in valid.items():
            self.assertEqual(conditional_fields(row, {"tipo": kind}), [])
            self.assertTrue(conditional_fields({}, {"tipo": kind}))
        self.assertTrue(conditional_fields({"valor": "NaN"}, {"tipo": "numerica"}))
        self.assertTrue(
            conditional_fields({"valor": "ok", "linha_matriz": "L"}, {"tipo": "aberta"})
        )

    def test_orphan_question_and_person_identity(self):
        result = run("respostas", [{**RAW["respostas"], "id_pergunta": "2"}])
        self.assertEqual(result.rejected[0].violations[0].code, "ORPHAN_REFERENCE")
        # respondent_id intentionally does not match cliente_id.
        self.assertEqual(len(run("respostas", [RAW["respostas"]]).accepted), 1)

    def test_temporal_consistency(self):
        result = run(
            "pesquisas",
            [{"id": "1", "data_solicitacao": "02/01/2026", "data_entrega": "01/01/2026"}],
        )
        self.assertIn("TEMPORAL_ORDER", [v.code for v in result.rejected[0].violations])

    def test_negative_counts(self):
        result = run("pesquisas", [{"id": "1", "participantes": "-1"}])
        self.assertIn("NEGATIVE_MEASURE", [v.code for v in result.rejected[0].violations])


class DeliveryTests(unittest.TestCase):
    def test_configuration_errors_fail_before_processing(self):
        from dataclasses import replace

        valid = batch("empresas", [RAW["empresas"]])
        for changed in (
            replace(valid.metadata, source_checksum=None),
            replace(valid.metadata, contract_version="2.0"),
            replace(valid.metadata, run_id="email@example.invalid"),
        ):
            with self.assertRaises(ValueError):
                transform_batch(
                    replace(valid, metadata=changed),
                    references=refs(),
                    previous={},
                    source_offset=0,
                    ingested_at=NOW,
                )
        for offset in (-1, True, "0"):
            with self.assertRaises(ValueError):
                run("empresas", [RAW["empresas"]], source_offset=offset)
        with self.assertRaises(ValueError):
            run("empresas", [], ingested_at=NOW.replace(tzinfo=None))

    def test_decimal_canonicalization(self):
        self.assertEqual(digest({"v": Decimal("1.000")}), digest({"v": Decimal("1")}))
        self.assertEqual(digest({"v": Decimal("-0.0")}), digest({"v": Decimal("0")}))

    def test_domain_and_company_mismatch(self):
        from etl.transformation.consistency import validate_consistency

        reference = ReferenceData(
            {
                "empresas": [{"empresa_id": "1"}],
                "pesquisas": [{"pesquisa_id": "1"}],
                "clientes": [{"cliente_id": "1", "empresa_id": "2"}],
            }
        )
        result = run("respondentes", [RAW["respondentes"]], references=reference)
        self.assertIn("CLIENT_COMPANY_MISMATCH", [v.code for v in result.rejected[0].violations])
        for kind in ("matriz_avaliacao", "multipla_escolha"):
            question = {
                "pesquisa_id": "1",
                "pergunta_id": "1",
                "tipo": kind,
                "linhas_matriz": ["L"],
                "colunas_matriz": ["C"],
                "alternativas": ["A"],
            }
            reference = ReferenceData(
                {"empresas": [], "pesquisas": [{"pesquisa_id": "1"}], "questoes": [question]}
            )
            row = normalize_record("respostas", RAW["respostas"])[0]
            row.update(linha_matriz="bad", coluna_matriz="bad", alternativa="bad")
            self.assertIn(
                "ANSWER_DOMAIN", [v.code for v in validate_consistency("respostas", row, reference)]
            )

    def test_question_schema_errors(self):
        for changes, expected in (
            ({"tipo": "unknown"}, "UNKNOWN_QUESTION_TYPE"),
            ({"qtd_alternativas": "2", "alternativas": "A"}, "ALTERNATIVE_COUNT_MISMATCH"),
        ):
            result = run("questoes", [{**RAW["questoes"], **changes}])
            self.assertIn(expected, [v.code for v in result.rejected[0].violations])

    def test_quarantine_rejects_unsafe_paths(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "q.db"
            path.touch(mode=0o644)
            with self.assertRaises(ValueError):
                QuarantineStore(path)
            link = Path(d) / "link.db"
            link.symlink_to(path)
            with self.assertRaises(ValueError):
                QuarantineStore(link)

    def test_unknown_source_and_malformed_records(self):
        with self.assertRaises(ValueError):
            normalize_record("unknown", {})
        self.assertTrue(normalize_record("empresas", [1])[1])
        self.assertTrue(normalize_record("empresas", {1: "bad"})[1])
        with self.assertRaises(ValueError):
            ReferenceData({"unknown": []})
        with self.assertRaises(ValueError):
            ReferenceData({"empresas": [{"empresa_id": 1}]})

    def test_same_batch_twice_and_after_confirmed_load(self):
        first = run("empresas", [RAW["empresas"]])
        retry = run("empresas", [RAW["empresas"]])
        self.assertEqual(first.accepted, retry.accepted)
        m = first.accepted[0].metadata
        confirmed = {m["record_identity"]: m["content_checksum"]}
        replay = run("empresas", [RAW["empresas"]], previous=confirmed)
        self.assertEqual(len(replay.accepted), 0)
        self.assertEqual(len(replay.duplicates), 1)

    def test_conflicts_have_no_order_winner(self):
        rows = [RAW["empresas"], {**RAW["empresas"], "Nome Fantasia": "Outro"}]
        for order in (rows, list(reversed(rows))):
            result = run("empresas", order)
            self.assertEqual(len(result.accepted), 0)
            self.assertEqual(len(result.rejected), 2)

    def test_distinct_answer_elements_are_preserved(self):
        rows = [RAW["respostas"], {**RAW["respostas"], "id_resposta": "2"}]
        self.assertEqual(len(run("respostas", rows).accepted), 2)

    def test_participation_occurrences_are_not_collapsed(self):
        row = {**RAW["respondentes"], "id_cliente": ""}
        self.assertEqual(len(run("respondentes", [row, row]).accepted), 2)
        first = run("respondentes", [row], source_offset=4).accepted[0]
        second = transform_batch(
            batch("respondentes", [row], run="run-2"),
            references=refs(),
            previous={},
            source_offset=4,
            ingested_at=NOW,
        ).accepted[0]
        self.assertEqual(first.metadata["idempotency_key"], second.metadata["idempotency_key"])

    def test_empty_batch_and_count_equation(self):
        result = run("empresas", [])
        self.assertEqual(result.metrics["accepted_count"], 0)
        rows = [RAW["empresas"], RAW["empresas"], {"ID": "invalid"}]
        result = run("empresas", rows)
        self.assertEqual(
            [len(result.accepted), len(result.rejected), len(result.duplicates)], [1, 1, 1]
        )

    def test_logs_and_quarantine_do_not_contain_raw_values(self):
        result = run("clientes", [{**RAW["clientes"], "id_cliente": "not-an-id"}])
        rendered = repr(result) + canonical_json(result.safe_summary()) + repr(result.rejected)
        self.assertNotIn("teste@example.invalid", rendered)
        self.assertNotIn("not-an-id", rendered)
        with tempfile.TemporaryDirectory() as d:
            store = QuarantineStore(Path(d) / "q.db")
            store.persist(result.rejected)
            store.persist(result.rejected)
            self.assertEqual(store.count(), 1)
            self.assertEqual(store.path.stat().st_mode & 0o777, 0o600)
            self.assertNotIn(b"teste@example.invalid", store.path.read_bytes())

    def test_quarantine_failure_does_not_consume_batch(self):
        original = batch("clientes", [{"id_cliente": "bad"}])
        with tempfile.TemporaryDirectory() as d:
            store = QuarantineStore(Path(d) / "q.db")
            result = transform_batch(
                original, references=refs(), previous={}, source_offset=0, ingested_at=NOW
            )
            with patch(
                "etl.transformation.quarantine.sqlite3.connect",
                side_effect=sqlite3.OperationalError("test"),
            ):
                with self.assertRaises(sqlite3.OperationalError):
                    store.persist(result.rejected)
            store.persist(result.rejected)
            self.assertEqual(store.count(), 1)
            self.assertEqual(original.checkpoint.position, "opaque-cursor")

    def test_canonical_object_key_order(self):
        self.assertEqual(digest({"x": 1, "y": 2}), digest({"y": 2, "x": 1}))
        self.assertEqual(classify_duplicates([("a", "x")], {"a": "y"}), ["conflict"])


if __name__ == "__main__":
    unittest.main()


def object_batch(rows, *, sequence, source_offset):
    return ExtractedBatch(
        rows,
        ExtractionCheckpoint("pesquisas", f"row:{sequence}", sequence),
        BatchMetadata(
            "pesquisas",
            "run-1",
            "task",
            f"pesquisas-{sequence:06d}",
            NOW,
            NOW,
            len(rows),
            100,
            "1.0",
            "a" * 64,
            source_offset=source_offset,
        ),
    )


class TransformObjectTests(unittest.TestCase):
    """Decisão de identidade global entre os lotes de um objeto (feedback Sprint 3, item 3)."""

    def run_object(self, *lotes, previous=None):
        batches = [
            object_batch(rows, sequence=i + 1, source_offset=sum(len(r) for r in lotes[:i]))
            for i, rows in enumerate(lotes)
        ]
        return transform_object(
            batches, references=refs(), previous=previous or {}, ingested_at=NOW
        )

    def test_same_identity_and_content_in_a_later_batch_is_duplicate(self):
        first, second = self.run_object([RAW["pesquisas"]], [RAW["pesquisas"]])

        self.assertEqual(len(first.accepted), 1)
        self.assertEqual((len(second.accepted), len(second.duplicates)), (0, 1))

    def test_divergent_versions_across_batches_are_conflict_in_every_occurrence(self):
        changed = {**RAW["pesquisas"], "titulo": "Outro"}
        first, second = self.run_object([RAW["pesquisas"]], [changed])

        for result in (first, second):
            with self.subTest(batch=result.metrics["batch_id"]):
                self.assertEqual(len(result.accepted), 0)
                self.assertEqual(
                    [v.code for r in result.rejected for v in r.violations], ["IDENTITY_CONFLICT"]
                )

    def test_cross_batch_decision_matches_the_single_batch_decision(self):
        changed = {**RAW["pesquisas"], "titulo": "Outro"}
        (split_a, split_b) = self.run_object([RAW["pesquisas"]], [changed])
        (single,) = self.run_object([RAW["pesquisas"], changed])

        self.assertEqual(len(split_a.rejected) + len(split_b.rejected), len(single.rejected))

    def test_offsets_come_from_the_extractor_metadata(self):
        (result,) = transform_object(
            [object_batch([RAW["pesquisas"]], sequence=4, source_offset=3)],
            references=refs(),
            previous={},
            ingested_at=NOW,
        )

        self.assertEqual(result.accepted[0].metadata["source_offset"], 3)

    def test_missing_offset_is_a_contract_error(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_OFFSET_REQUIRED"):
            transform_object(
                [object_batch([RAW["pesquisas"]], sequence=1, source_offset=None)],
                references=refs(),
                previous={},
                ingested_at=NOW,
            )

    def test_every_batch_still_reconciles_on_its_own(self):
        results = self.run_object([RAW["pesquisas"], {"titulo": "sem id"}], [RAW["pesquisas"]])

        for result in results:
            m = result.metrics
            self.assertEqual(
                m["extracted_count"],
                m["accepted_count"] + m["rejected_count"] + m["duplicate_count"],
            )
