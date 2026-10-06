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
        self.assertEqual(por_medida["Qtd Pesquisas"]["linhas_publicadas"], 1)
        self.assertEqual(conferir_medidas_bi.codigo_saida(resultado), 0)

    def test_valor_maior_que_referencia_exige_reconciliacao_da_mesma_geracao(self) -> None:
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
        self.assertIn("maior que a referencia historica", por_medida["Qtd Pesquisas"]["status"])
        self.assertIn(
            "maior que a referencia historica", por_medida["Base Valida Validacao"]["status"]
        )
        self.assertEqual(conferir_medidas_bi.codigo_saida(resultado), 1)

    def test_arquivo_ausente_nao_derruba_a_conferencia(self) -> None:
        resultado = conferir_medidas_bi.conferir(self.geracao)

        por_medida = {linha["medida"]: linha for linha in resultado}
        for linha in por_medida.values():
            self.assertEqual(linha["status"], "sem arquivo publicado nesta geracao")
            self.assertFalse(linha["arquivo_presente"])
            self.assertIsNone(linha["linhas_publicadas"])
            self.assertIsNone(linha["valor_publicado"])
        self.assertEqual(conferir_medidas_bi.codigo_saida(resultado), 1)

    def test_parquet_vazio_existente_nao_e_classificado_como_ausente(self) -> None:
        con = duckdb.connect(":memory:")
        try:
            con.execute(
                f"COPY (SELECT 1::BIGINT AS qtd_pesquisas, "
                f"1::BIGINT AS qtd_validacao_disponivel WHERE FALSE) "
                f"TO '{self.geracao / 'PUB_C01_CICLO.parquet'}' (FORMAT PARQUET)"
            )
            con.execute(
                f"COPY (SELECT 1::BIGINT AS qtd_participacoes WHERE FALSE) "
                f"TO '{self.geracao / 'PUB_C02_PARTICIPACAO.parquet'}' (FORMAT PARQUET)"
            )
        finally:
            con.close()

        resultado = conferir_medidas_bi.conferir(self.geracao)

        for linha in resultado:
            self.assertEqual(linha["status"], "arquivo publicado sem linhas nesta geracao")
            self.assertTrue(linha["arquivo_presente"])
            self.assertEqual(linha["linhas_publicadas"], 0)
            self.assertIsNone(linha["valor_publicado"])
        self.assertEqual(conferir_medidas_bi.codigo_saida(resultado), 1)

    def test_coluna_nula_em_parquet_com_linhas_nao_e_classificada_como_vazia(self) -> None:
        con = duckdb.connect(":memory:")
        try:
            con.execute(
                f"COPY (SELECT NULL::BIGINT AS qtd_pesquisas, "
                f"NULL::BIGINT AS qtd_validacao_disponivel) "
                f"TO '{self.geracao / 'PUB_C01_CICLO.parquet'}' (FORMAT PARQUET)"
            )
            con.execute(
                f"COPY (SELECT NULL::BIGINT AS qtd_participacoes) "
                f"TO '{self.geracao / 'PUB_C02_PARTICIPACAO.parquet'}' (FORMAT PARQUET)"
            )
        finally:
            con.close()

        resultado = conferir_medidas_bi.conferir(self.geracao)

        for linha in resultado:
            self.assertEqual(linha["status"], "arquivo publicado sem valor agregado nesta geracao")
            self.assertTrue(linha["arquivo_presente"])
            self.assertEqual(linha["linhas_publicadas"], 1)
            self.assertIsNone(linha["valor_publicado"])
        self.assertEqual(conferir_medidas_bi.codigo_saida(resultado), 1)

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
        self.assertEqual(conferir_medidas_bi.codigo_saida(resultado), 1)


if __name__ == "__main__":
    unittest.main()
