"""Verificação estrutural das fixtures sintéticas versionadas (VB-03).

Garante que cada CSV do diretório é pequeno, determinístico, fiel ao contrato
do seu extrator e coerente nos relacionamentos entre arquivos — sem depender
do pipeline de transformação ou de qualquer infraestrutura.
"""

from __future__ import annotations

import csv
import sys
import unittest
from io import StringIO
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.orchestration.flow import EXTRACTORS  # noqa: E402
from tests import fixtures  # noqa: E402


def _linhas(source: str) -> list[dict[str, str]]:
    texto = fixtures.payload(source).decode("utf-8")
    return list(csv.DictReader(StringIO(texto), delimiter=";"))


class EstruturaDasFixturesTests(unittest.TestCase):
    def test_toda_fonte_tem_fixture_versionada(self) -> None:
        for source in fixtures.ORDEM_CARGA:
            with self.subTest(fonte=source):
                self.assertTrue(fixtures.caminho(source).is_file())

    def test_fixture_desconhecida_falha_cedo(self) -> None:
        with self.assertRaises(ValueError):
            fixtures.payload("fonte_inexistente")

    def test_payload_e_deterministico(self) -> None:
        for source in fixtures.ORDEM_CARGA:
            with self.subTest(fonte=source):
                self.assertEqual(fixtures.payload(source), fixtures.payload(source))

    def test_cabecalho_corresponde_ao_contrato_do_extrator(self) -> None:
        for source in fixtures.ORDEM_CARGA:
            with self.subTest(fonte=source):
                cabecalho = fixtures.payload(source).decode("utf-8").splitlines()[0]
                self.assertEqual(
                    tuple(cabecalho.split(";")),
                    EXTRACTORS[source].required_columns,
                )

    def test_quantidade_de_registros_confere_com_o_manifesto(self) -> None:
        for source in fixtures.ORDEM_CARGA:
            with self.subTest(fonte=source):
                linhas = _linhas(source)
                self.assertEqual(len(linhas), fixtures.ESPERADO[source]["registros"])
                self.assertTrue(all(None not in linha for linha in linhas))

    def test_fixtures_sao_pequenas_e_sem_dados_reais(self) -> None:
        for source in fixtures.ORDEM_CARGA:
            with self.subTest(fonte=source):
                self.assertLess(len(fixtures.payload(source)), 2048)
                emails = [linha.get("e-mail", "") for linha in _linhas(source)]
                for email in emails:
                    if email:
                        self.assertTrue(email.endswith("@example.invalid"))


class CenariosCobertosTests(unittest.TestCase):
    """Cada categoria exigida aparece ao menos uma vez no conjunto."""

    def test_duplicados_dentro_do_mesmo_arquivo(self) -> None:
        ids_empresas = [linha["ID"] for linha in _linhas("empresas")]
        self.assertEqual(ids_empresas.count("101"), 2)
        ids_respostas = [linha["id_resposta"] for linha in _linhas("respostas")]
        self.assertEqual(ids_respostas.count("3001"), 2)

    def test_nulos_e_sentinelas(self) -> None:
        empresa = _linhas("empresas")[1]
        self.assertEqual(empresa["ID"], "102")
        self.assertTrue(all(valor == "" for chave, valor in empresa.items() if chave != "ID"))
        respondente = _linhas("respondentes")[1]
        self.assertEqual(respondente["market_share"], "na")
        self.assertEqual(respondente["id_cliente"], "s/i")

    def test_casos_invalidos_presentes(self) -> None:
        gama = _linhas("pesquisas")[2]

        def inverte(d):
            return tuple(reversed(d.split("/")))

        self.assertGreater(inverte(gama["data_solicitacao"]), inverte(gama["data_entrega"]))
        respondente = _linhas("respondentes")[2]
        self.assertGreater(respondente["hora_inicio"], respondente["hora_termino"])
        self.assertEqual(_linhas("questoes")[2]["tipo"], "tipo_inexistente")
        self.assertEqual(_linhas("respostas")[2]["alternativa"], "Z")

    def test_casos_de_borda_zero_como_medida_valida(self) -> None:
        self.assertEqual(_linhas("pesquisas")[3]["participantes"], "0")
        self.assertEqual(_linhas("empresas")[3]["% de mercado"], "0")


class RelacionamentosEntreArquivosTests(unittest.TestCase):
    def setUp(self) -> None:
        self.empresas = {linha["ID"] for linha in _linhas("empresas")}
        self.pesquisas = {linha["id"] for linha in _linhas("pesquisas")}
        self.clientes = {linha["id_cliente"]: linha for linha in _linhas("clientes")}
        self.questoes = {linha["id_pergunta"] for linha in _linhas("questoes")}

    def test_clientes_referenciam_empresas(self) -> None:
        validos = {"1001", "1002"}
        for id_cliente in validos:
            with self.subTest(id_cliente=id_cliente):
                self.assertIn(self.clientes[id_cliente]["id_empresa"], self.empresas)

    def test_cliente_orfao_e_intencional(self) -> None:
        """A referência órfã existe de propósito para exercitar a rejeição."""
        self.assertNotIn(self.clientes["1003"]["id_empresa"], self.empresas)

    def test_respondentes_referenciam_pesquisas_empresas_e_clientes(self) -> None:
        for linha in _linhas("respondentes"):
            with self.subTest(linha=linha):
                self.assertIn(linha["id_pesq"], self.pesquisas)
                self.assertIn(linha["id_empresa"], self.empresas)
                if linha["id_cliente"] != "s/i":
                    cliente = self.clientes[linha["id_cliente"]]
                    self.assertEqual(cliente["id_empresa"], linha["id_empresa"])

    def test_questoes_referenciam_pesquisas(self) -> None:
        for linha in _linhas("questoes"):
            with self.subTest(pergunta=linha["id_pergunta"]):
                self.assertIn(linha["pesquisa_id"], self.pesquisas)

    def test_respostas_referenciam_pesquisas_questoes_e_empresas(self) -> None:
        for linha in _linhas("respostas"):
            with self.subTest(resposta=linha["id_resposta"]):
                self.assertIn(linha["pesquisa_id"], self.pesquisas)
                self.assertIn(linha["id_pergunta"], self.questoes)
                if linha["id_empresa"]:
                    self.assertIn(linha["id_empresa"], self.empresas)


if __name__ == "__main__":
    unittest.main()
