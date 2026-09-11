#!/usr/bin/env python3
"""Testes unitários sem depender dos CSVs protegidos do contexto."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

import profile_csv


class ProfileCsvTest(unittest.TestCase):
    def test_brazilian_number_and_percentage(self) -> None:
        self.assertEqual(profile_csv.parse_number("8,25%"), profile_csv.Decimal("8.25"))
        self.assertEqual(profile_csv.pct(1, 5430), "0,0%")
        self.assertEqual(profile_csv.pct(49, 366), "13,4%")

    def test_schema_failure_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_dir = root / "input"
            input_dir.mkdir()
            (root / "manifest.json").write_text(
                json.dumps(
                    {"sources": [{"id": "a", "file": "a.csv", "columns": ["id"], "key": ["id"]}]}
                ),
                encoding="utf-8",
            )
            (input_dir / "a.csv").write_text("\ufeffwrong\n1\n", encoding="utf-8")
            with self.assertRaisesRegex(profile_csv.ProfileError, r"\[schema\].*colunas ausentes"):
                profile_csv.run(input_dir, root / "out", root / "manifest.json")

    def test_output_is_bom_delimited_and_does_not_contain_raw_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_dir = root / "input"
            input_dir.mkdir()
            (root / "manifest.json").write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "id": "a",
                                "file": "a.csv",
                                "columns": ["id", "status"],
                                "key": ["id"],
                                "domain_columns": {"status": "hash"},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with (input_dir / "a.csv").open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.writer(stream, delimiter=";")
                writer.writerow(["id", "status"])
                writer.writerow(["1", "RESPPOSTA-SEGRETA"])
            output = root / "out"
            profile_csv.run(input_dir, output, root / "manifest.json")
            content = (output / "resumo.csv").read_bytes()
            self.assertTrue(content.startswith(b"\xef\xbb\xbf"))
            self.assertIn(b";", content)
            all_output = b"".join(path.read_bytes() for path in output.iterdir())
            self.assertNotIn(b"RESPPOSTA-SEGRETA", all_output)

    def test_arbitrary_dictionary_fails_before_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_dir = root / "input"
            input_dir.mkdir()
            (root / "manifest.json").write_text(
                json.dumps(
                    {"sources": [{"id": "a", "file": "a.csv", "columns": ["id"], "key": ["id"]}]}
                ),
                encoding="utf-8",
            )
            (input_dir / "a.csv").write_text("\ufeffid\n1\n", encoding="utf-8")
            dictionary = root / "arbitrario.csv"
            dictionary.write_text("wrong\nvalue\n", encoding="utf-8")
            with self.assertRaisesRegex(
                profile_csv.ProfileError, r"\[dicionário\] cabeçalho incompatível"
            ):
                profile_csv.run(input_dir, root / "out", root / "manifest.json", dictionary)
            self.assertFalse((root / "out").exists())

    def test_dictionary_cardinality_claim_fails_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_dir = root / "input"
            input_dir.mkdir()
            columns = [
                "id_resposta",
                "pesquisa_id",
                "id_pergunta",
                "respondent_id",
                "id_empresa",
                "alternativa",
                "linha_matriz",
                "coluna_matriz",
                "valor",
            ]
            (root / "manifest.json").write_text(
                json.dumps(
                    {
                        "dictionary": {
                            "required_columns": [
                                "Variável",
                                "Unidade de Análise",
                                "Tipo de Variável",
                                "Valores ou Domínio Esperado",
                                "Análises Adequadas",
                            ],
                            "required_variables": columns,
                            "required_nonempty_columns": [
                                "Unidade de Análise",
                                "Tipo de Variável",
                                "Valores ou Domínio Esperado",
                                "Análises Adequadas",
                            ],
                        },
                        "sources": [
                            {
                                "id": "respostas",
                                "file": "respostas.csv",
                                "columns": columns,
                                "key": ["id_resposta"],
                                "sentinels": {},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with (input_dir / "respostas.csv").open(
                "w", encoding="utf-8-sig", newline=""
            ) as stream:
                writer = csv.writer(stream, delimiter=";")
                writer.writerow(columns)
                writer.writerow(["1", "1", "1", "101", "5", "A", "", "", "ok"])
                writer.writerow(["2", "1", "1", "102", "6", "A", "", "", "ok"])
            dictionary = root / "dicionario.csv"
            dictionary_columns = [
                "Variável",
                "Unidade de Análise",
                "Tipo de Variável",
                "Valores ou Domínio Esperado",
                "Análises Adequadas",
            ]
            with dictionary.open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(dictionary_columns)
                for variable in columns:
                    claim = "1 valores únicos" if variable == "id_resposta" else "2 valores únicos"
                    writer.writerow([variable, "unidade", "nominal", claim, "frequência"])
            with self.assertRaisesRegex(profile_csv.ProfileError, r"\[dicionário\].*id_resposta"):
                profile_csv.run(input_dir, root / "out", root / "manifest.json", dictionary)
            self.assertFalse((root / "out").exists())


if __name__ == "__main__":
    unittest.main()
