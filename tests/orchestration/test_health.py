"""Health check do orquestrador (Prefect) e do banco de ingestão (OB-09).

Cobre as duas checagens isoladas (Prefect via HTTP injetado, DuckDB via
``run_health_check`` já existente) e o evento estruturado publicado ao final,
no mesmo formato técnico das demais camadas (ADR 0001).
"""

from __future__ import annotations

import importlib.util
import logging
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.orchestration.health import (  # noqa: E402
    HEALTH_CHECK_EVENT,
    check_database_health,
    check_prefect_health,
    log_health_check,
    run_orchestration_health_check,
)

DUCKDB_INSTALLED = importlib.util.find_spec("duckdb") is not None
SEM_DUCKDB = "duckdb não instalado; use pip install -r requirements.txt"


class LogRecordCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class VerificaSaudeDoPrefect(unittest.TestCase):
    def test_relata_ok_quando_o_servidor_responde_200(self) -> None:
        chamadas = []

        def http_get_falso(url: str, timeout: float) -> int:
            chamadas.append((url, timeout))
            return 200

        resultado = check_prefect_health("http://prefect.local/api", http_get=http_get_falso)

        self.assertTrue(resultado.passed)
        self.assertEqual(chamadas, [("http://prefect.local/api/health", 5.0)])

    def test_relata_falha_quando_o_servidor_responde_status_diferente_de_200(self) -> None:
        resultado = check_prefect_health(
            "http://prefect.local/api", http_get=lambda url, timeout: 503
        )

        self.assertFalse(resultado.passed)
        self.assertIn("503", resultado.detail)

    def test_relata_falha_quando_a_conexao_e_recusada(self) -> None:
        def http_get_que_falha(url: str, timeout: float) -> int:
            raise OSError("connection refused")

        resultado = check_prefect_health("http://prefect.local/api", http_get=http_get_que_falha)

        self.assertFalse(resultado.passed)

    def test_relata_falha_quando_a_porta_responde_mas_nao_fala_http(self) -> None:
        import http.client

        def http_get_com_resposta_corrompida(url: str, timeout: float) -> int:
            raise http.client.BadStatusLine("lixo binário, não é HTTP")

        resultado = check_prefect_health(
            "http://prefect.local/api", http_get=http_get_com_resposta_corrompida
        )

        self.assertFalse(resultado.passed)
        self.assertIn("inacessível", resultado.detail)
        self.assertIn("inacessível", resultado.detail)

    def test_relata_falha_explicita_quando_api_url_nao_esta_configurada(self) -> None:
        resultado = check_prefect_health(None, http_get=lambda url, timeout: 200)

        self.assertFalse(resultado.passed)
        self.assertIn("PREFECT_API_URL", resultado.detail)

    def test_remove_barra_final_do_api_url_antes_de_montar_a_url_de_saude(self) -> None:
        chamadas = []

        def http_get_falso(url: str, timeout: float) -> int:
            chamadas.append(url)
            return 200

        check_prefect_health("http://prefect.local/api/", http_get=http_get_falso)

        self.assertEqual(chamadas, ["http://prefect.local/api/health"])


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class VerificaSaudeDoBanco(unittest.TestCase):
    def test_relata_ok_para_um_banco_valido(self) -> None:
        from etl.load.config import load_duckdb_settings

        with tempfile.TemporaryDirectory() as tmp:
            settings = load_duckdb_settings({"database_path": Path(tmp) / "warehouse.duckdb"})

            resultado = check_database_health(settings)

        self.assertTrue(resultado.passed)
        self.assertIn("DuckDB", resultado.detail)

    def test_relata_falha_em_vez_de_propagar_quando_o_health_check_da_carga_estoura(
        self,
    ) -> None:
        from etl.load.config import load_duckdb_settings
        from etl.load.environment import DatabaseEnvironmentError

        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch(
                "etl.orchestration.health.run_health_check",
                side_effect=DatabaseEnvironmentError("arquivo bloqueado por outro processo"),
            ),
        ):
            settings = load_duckdb_settings({"database_path": Path(tmp) / "warehouse.duckdb"})

            resultado = check_database_health(settings)

        self.assertFalse(resultado.passed)
        self.assertIn("bloqueado", resultado.detail)

    def test_relata_falha_quando_o_relatorio_da_carga_tem_uma_checagem_reprovada(self) -> None:
        from etl.load.config import load_duckdb_settings
        from etl.load.environment import HealthCheck, HealthCheckReport

        relatorio_com_falha = HealthCheckReport(
            database_path=Path("/tmp/warehouse.duckdb"),
            duckdb_version="1.5.5",
            database_created=False,
            checks=(HealthCheck(name="persistencia", passed=False, detail="linha não voltou"),),
        )
        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch(
                "etl.orchestration.health.run_health_check", return_value=relatorio_com_falha
            ),
        ):
            settings = load_duckdb_settings({"database_path": Path(tmp) / "warehouse.duckdb"})

            resultado = check_database_health(settings)

        self.assertFalse(resultado.passed)
        self.assertIn("linha não voltou", resultado.detail)


@unittest.skipUnless(DUCKDB_INSTALLED, SEM_DUCKDB)
class VerificacaoCombinadaEEvento(unittest.TestCase):
    def test_relatorio_combinado_falha_se_qualquer_checagem_falhar(self) -> None:
        from etl.load.config import load_duckdb_settings

        with tempfile.TemporaryDirectory() as tmp:
            settings = load_duckdb_settings({"database_path": Path(tmp) / "warehouse.duckdb"})

            relatorio = run_orchestration_health_check(
                api_url=None, settings=settings, http_get=lambda url, timeout: 200
            )

        self.assertFalse(relatorio.passed)
        self.assertTrue(relatorio.database.passed)
        self.assertFalse(relatorio.prefect.passed)

    def test_relatorio_combinado_passa_quando_as_duas_checagens_passam(self) -> None:
        from etl.load.config import load_duckdb_settings

        with tempfile.TemporaryDirectory() as tmp:
            settings = load_duckdb_settings({"database_path": Path(tmp) / "warehouse.duckdb"})

            relatorio = run_orchestration_health_check(
                api_url="http://prefect.local/api",
                settings=settings,
                http_get=lambda url, timeout: 200,
            )

        self.assertTrue(relatorio.passed)

    def test_publica_um_unico_evento_estruturado_com_o_resultado(self) -> None:
        from etl.load.config import load_duckdb_settings

        logger = logging.getLogger("etl.orchestration")
        coletor = LogRecordCollector()
        logger.addHandler(coletor)
        logger.setLevel(logging.INFO)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                settings = load_duckdb_settings({"database_path": Path(tmp) / "warehouse.duckdb"})
                relatorio = run_orchestration_health_check(
                    api_url=None, settings=settings, http_get=lambda url, timeout: 200
                )
                log_health_check(relatorio, logger=logger)
        finally:
            logger.removeHandler(coletor)

        eventos = [r for r in coletor.records if getattr(r, "event", None) == HEALTH_CHECK_EVENT]
        self.assertEqual(len(eventos), 1)
        evento = eventos[0]
        self.assertEqual(evento.stage, "orchestration")
        self.assertEqual(evento.status, "degraded")
        self.assertFalse(evento.prefect_available)
        self.assertTrue(evento.database_available)
        self.assertGreaterEqual(evento.duration_ms, 0)


if __name__ == "__main__":
    unittest.main()
