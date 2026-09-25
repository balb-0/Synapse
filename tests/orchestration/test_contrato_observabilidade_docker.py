"""Contratos do caminho Docker -> Logstash -> Elasticsearch -> Kibana.

Estes testes mantêm verificáveis as decisões operacionais do smoke OB-11:
o daemon Docker precisa alcançar o coletor pela porta publicada no host, cada
comando do smoke precisa ser um container cujo stdout seja coletado, e apenas
falhas de telemetria devem carregar a marca usada pelo alerta.
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class ContratoDoCompose(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compose = (REPOSITORY_ROOT / "docker-compose.yml").read_text()
        cls.prefect_logging = (REPOSITORY_ROOT / "observability/prefect-logging.yml").read_text()

    def test_driver_gelf_usa_a_porta_do_coletor_publicada_no_host(self) -> None:
        self.assertIn('gelf-address: "udp://127.0.0.1:12201"', self.compose)

    def test_runner_recebe_api_do_prefect_e_resolve_o_host(self) -> None:
        self.assertIn("PREFECT_API_URL: ${PREFECT_API_URL:-}", self.compose)
        self.assertIn(
            "PREFECT_LOGGING_SETTINGS_PATH: /app/observability/prefect-logging.yml", self.compose
        )
        self.assertIn('"host.docker.internal:host-gateway"', self.compose)

    def test_perfil_do_prefect_remove_o_console_humano_do_root(self) -> None:
        self.assertNotIn("PrefectConsoleHandler", self.prefect_logging)
        self.assertIn('root:\n  level: WARNING\n  handlers: ["null"]', self.prefect_logging)


class ContratoDoLogstash(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pipeline = (REPOSITORY_ROOT / "observability/logstash/pipeline/etl.conf").read_text()

    def test_remove_level_nativo_antes_de_parsear_o_json_da_aplicacao(self) -> None:
        remove_level = self.pipeline.index('remove_field => ["level"]')
        parse_json = self.pipeline.index("if [message] =~")

        self.assertLess(remove_level, parse_json)

    def test_parser_so_tenta_json_quando_a_mensagem_parece_json(self) -> None:
        self.assertIn("if [message] =~ /^\\s*\\{/", self.pipeline)
        self.assertIn('tag_on_failure => ["_jsonparsefailure", "etl_error"]', self.pipeline)

    def test_falha_relevante_sem_json_recebe_a_marca_do_alerta(self) -> None:
        self.assertIn('add_tag => ["etl_error"]', self.pipeline)


class ContratoDoSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.smoke = (REPOSITORY_ROOT / "scripts/orchestration/smoke_observabilidade.sh").read_text()
        cls.runbook = (REPOSITORY_ROOT / "docs/runbook-execucao.md").read_text()

    def test_cada_comando_do_smoke_roda_em_container_one_shot(self) -> None:
        self.assertIn('docker compose run --rm --no-deps -T runner "$@"', self.smoke)
        self.assertGreaterEqual(self.smoke.count("run_runner python"), 3)
        self.assertNotIn("docker compose exec -T runner", self.smoke)

    def test_alerta_documentado_usa_a_marca_de_erro_explicita(self) -> None:
        self.assertIn('tags: "etl_error"', self.runbook)


if __name__ == "__main__":
    unittest.main()
