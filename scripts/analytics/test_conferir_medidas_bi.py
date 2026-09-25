#!/usr/bin/env python3
"""Testes da conferência das medidas do BI contra a apuração de referência."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import conferir_medidas_bi
import duckdb


class ConferirMedidasBiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.geracao = Path(self.temp.name)

    def test_bate_exato_quando_geracao_reproduz_a_referencia(self) -> None:
        con = duckdb.connect(":memory:")
        try:
            con.execute(
                f"COPY (SELECT 366::BIGINT AS qtd_pesquisas, 20::BIGINT AS qtd_validacao_disponivel) "
                f"TO '{self.geracao / 'PUB_C01_CICLO.parquet'}' (FORMAT PARQUET)"
            )
            con.execute(
                f"COPY (SELECT 18735::BIGINT AS qtd_participacoes) "
                f"TO '{self.geracao / 'PUB_C02_PARTICIPACAO.parquet'}' (FORMAT PARQUET)"
            )
        finally:
            con.close()

        resultado = conferir_medidas_bi.conferir(self.geracao)

        por_medida = {linha["medida"]: linha for linha in resultado}
        self.assertEqual(por_medida["Qtd Pesquisas"]["status"], "bate exato")
        self.assertEqual(por_medida["Base Valida Validacao"]["status"], "bate exato")
        self.assertEqual(por_medida["Qtd Participacoes"]["status"], "bate exato")

    def test_geracao_mais_nova_diverge_para_cima_sem_ser_erro(self) -> None:
        con = duckdb.connect(":memory:")
        try:
            con.execute(
                f"COPY (SELECT 400::BIGINT AS qtd_pesquisas, 25::BIGINT AS qtd_validacao_disponivel) "
                f"TO '{self.geracao / 'PUB_C01_CICLO.parquet'}' (FORMAT PARQUET)"
            )
        finally:
            con.close()

        resultado = conferir_medidas_bi.conferir(self.geracao)

        por_medida = {linha["medida"]: linha for linha in resultado}
        self.assertIn("maior que a referencia", por_medida["Qtd Pesquisas"]["status"])
        self.assertIn("maior que a referencia", por_medida["Base Valida Validacao"]["status"])

    def test_arquivo_ausente_nao_derruba_a_conferencia(self) -> None:
        resultado = conferir_medidas_bi.conferir(self.geracao)

        por_medida = {linha["medida"]: linha for linha in resultado}
        for linha in por_medida.values():
            self.assertEqual(linha["status"], "sem arquivo publicado nesta geracao")
            self.assertIsNone(linha["valor_publicado"])

    def test_geracao_menor_que_a_referencia_sinaliza_investigar(self) -> None:
        con = duckdb.connect(":memory:")
        try:
            con.execute(
                f"COPY (SELECT 10::BIGINT AS qtd_pesquisas, 1::BIGINT AS qtd_validacao_disponivel) "
                f"TO '{self.geracao / 'PUB_C01_CICLO.parquet'}' (FORMAT PARQUET)"
            )
        finally:
            con.close()

        resultado = conferir_medidas_bi.conferir(self.geracao)

        por_medida = {linha["medida"]: linha for linha in resultado}
        self.assertIn("investigar", por_medida["Qtd Pesquisas"]["status"])


if __name__ == "__main__":
    unittest.main()
