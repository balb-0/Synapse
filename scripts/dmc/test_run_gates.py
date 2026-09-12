#!/usr/bin/env python3
"""Testes do orquestrador de gates do Data Model Canvas."""

from __future__ import annotations

import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

import run_gates


class RunGatesTest(unittest.TestCase):
    def test_default_run_contains_five_repository_gates(self) -> None:
        gates = run_gates.build_gates(
            "python",
            Path("docs/dmc.json"),
            Path("scripts/traceability/manifest.json"),
            Path("docs/projeto.md"),
            None,
        )
        self.assertEqual(
            [gate.name for gate in gates],
            [
                "JSON canônico",
                "Contrato semântico do DMC",
                "Rastreabilidade",
                "Testes do DMC",
                "Testes de rastreabilidade",
            ],
        )

    def test_reexport_adds_json_and_round_trip_gates(self) -> None:
        gates = run_gates.build_gates(
            "python",
            Path("docs/dmc.json"),
            Path("scripts/traceability/manifest.json"),
            Path("docs/projeto.md"),
            Path("tmp/dmc-reexportado.json"),
        )
        self.assertEqual(gates[-2].name, "JSON reexportado")
        self.assertEqual(gates[-1].name, "Round-trip semântico")
        self.assertIn("--baseline", gates[-1].command)
        self.assertEqual(Path(gates[-1].command[-1]), Path("docs/dmc.json"))

    @mock.patch("run_gates.subprocess.run")
    def test_execution_stops_at_first_failed_gate(self, run: mock.Mock) -> None:
        run.side_effect = [
            subprocess.CompletedProcess(("first",), 0),
            subprocess.CompletedProcess(("second",), 3),
        ]
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            result = run_gates.execute_gates(
                [
                    run_gates.Gate("primeiro", ("first",)),
                    run_gates.Gate("segundo", ("second",)),
                    run_gates.Gate("terceiro", ("third",)),
                ]
            )
        self.assertEqual(result, 3)
        self.assertEqual(run.call_count, 2)

    @mock.patch("run_gates.subprocess.run")
    def test_success_runs_every_gate_from_repository_root(self, run: mock.Mock) -> None:
        run.return_value = subprocess.CompletedProcess(("ok",), 0)
        gates = [
            run_gates.Gate("primeiro", ("first",)),
            run_gates.Gate("segundo", ("second",)),
        ]
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            result = run_gates.execute_gates(gates)
        self.assertEqual(result, 0)
        self.assertEqual(run.call_count, 2)
        for call in run.call_args_list:
            self.assertEqual(call.kwargs["cwd"], run_gates.REPOSITORY_ROOT)
            self.assertFalse(call.kwargs["check"])


if __name__ == "__main__":
    unittest.main()
