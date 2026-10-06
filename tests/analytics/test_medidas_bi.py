"""Independent reference cases for the published BI measure contract.

These tests calculate expected values from small publication-shaped fixtures;
they do not execute DAX. Desktop acceptance queries live in
``tests/analytics/dax/bi04-acceptance-queries.dax``.
"""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
C01 = (
    ROOT / "powerbi/CentralPesquisasBI.SemanticModel/definition/tables/PUB_C01_CICLO.tmdl"
).read_text(encoding="utf-8")
C02 = (
    ROOT / "powerbi/CentralPesquisasBI.SemanticModel/definition/tables/PUB_C02_PARTICIPACAO.tmdl"
).read_text(encoding="utf-8")
C03 = (
    ROOT / "powerbi/CentralPesquisasBI.SemanticModel/definition/tables/PUB_C03_PIPELINE_MENSAL.tmdl"
).read_text(encoding="utf-8")
DAX_QUERIES = (ROOT / "tests/analytics/dax/bi04-acceptance-queries.dax").read_text(encoding="utf-8")
C03_REFERENCE_DATE = C03.split("measure 'Data de Referência do Estoque' =", 1)[1].split(
    "formatString:", 1
)[0]
C03_STOCK = C03.split("measure 'Estoque no Último Mês Observado' =", 1)[1].split(
    "formatString:", 1
)[0]


def reference_weighted_mean(groups: list[tuple[int | None, int]]) -> float | None:
    """Compute an aggregate mean from published sum and valid-count pairs."""
    numerator = sum(total for total, _count in groups if total is not None)
    denominator = sum(count for _total, count in groups)
    return numerator / denominator if denominator else None


def reference_stock(
    rows: list[tuple[str, str, int]],
    observed_months: set[str],
    selected_months: set[str],
) -> tuple[str, int] | None:
    """Return the latest observed month and its stock across disjoint groups."""
    candidates = observed_months & selected_months
    if not candidates:
        return None
    month = max(candidates)
    return month, sum(stock for row_month, _group, stock in rows if row_month == month)


class PublishedMeasureReferenceTests(unittest.TestCase):
    def test_weighted_mean_uses_the_published_denominator_not_group_averages(self) -> None:
        # Group means are 1 and 9, with valid populations 1 and 9.
        # The correct combined result is (1*1 + 9*9) / (1+9) = 8.2.
        self.assertEqual(reference_weighted_mean([(1, 1), (81, 9)]), 8.2)
        self.assertEqual((1 + 9) / 2, 5)
        self.assertIn(
            "DIVIDE(SUM(PUB_C01_CICLO[soma_dias_validacao]), SUM(PUB_C01_CICLO[qtd_validacao_disponivel]))",
            C01,
        )
        self.assertIn(
            "DIVIDE(SUM(PUB_C02_PARTICIPACAO[soma_minutos_preenchimento]), SUM(PUB_C02_PARTICIPACAO[qtd_preenchimento_disponivel]))",
            C02,
        )

    def test_zero_numerator_is_a_real_zero_but_empty_denominator_is_unavailable(self) -> None:
        self.assertEqual(reference_weighted_mean([(0, 4)]), 0)
        self.assertIsNone(reference_weighted_mean([(None, 0)]))
        self.assertIn("DIVIDE(SUM(PUB_C01_CICLO[soma_dias_validacao])", C01)
        self.assertIn("DIVIDE(SUM(PUB_C02_PARTICIPACAO[soma_minutos_preenchimento])", C02)

    def test_stock_sums_groups_at_latest_observed_month_only(self) -> None:
        rows = [
            ("2026-09", "A", 10),
            ("2026-10", "A", 4),
            ("2026-10", "B", 3),
        ]
        observed = {"2026-09", "2026-10"}
        self.assertEqual(reference_stock(rows, observed, observed), ("2026-10", 7))
        self.assertEqual(reference_stock(rows, observed, {"2026-09"}), ("2026-09", 10))
        self.assertEqual(sum(stock for _month, _group, stock in rows), 17)
        self.assertIn("MAX(PUB_C03_PIPELINE_MENSAL[data_fim_mes])", C03_REFERENCE_DATE)
        self.assertNotIn("REMOVEFILTERS(DIM_TEMPO)", C03_REFERENCE_DATE)
        self.assertIn("SUM(PUB_C03_PIPELINE_MENSAL[qtd_pesquisas_no_status])", C03)

    def test_hierarchy_leaf_keeps_global_closure_date_under_area_slicer(self) -> None:
        # C03's report hierarchy groups raw fact columns. Area A has an earlier
        # row but no row in October; area B proves that October is an observed
        # closure within the selected period. The date remains global, while
        # the area A stock at that date is a valid zero.
        snapshots: list[tuple[str, str, str, str, str, int]] = [
            ("2026-09", "Área A", "Tipo 1", "Perfil 1", "Em andamento", 10),
            ("2026-10", "Área B", "Tipo 2", "Perfil 2", "Em andamento", 4),
        ]
        selected_months = {"2026-09", "2026-10"}
        observed_months = {row[0] for row in snapshots}
        latest_global_month = max(observed_months & selected_months)
        latest_month_for_area_a = max(
            row[0] for row in snapshots if row[0] in selected_months and row[1] == "Área A"
        )
        area_a_stock_at_global_month = sum(
            row[5] for row in snapshots if row[0] == latest_global_month and row[1] == "Área A"
        )

        self.assertEqual(latest_global_month, "2026-10")
        self.assertEqual(latest_month_for_area_a, "2026-09")
        self.assertEqual(area_a_stock_at_global_month, 0)
        self.assertEqual(max(observed_months & {"2026-09"}), "2026-09")

        self.assertIn("MAX(PUB_C03_PIPELINE_MENSAL[data_fim_mes])", C03_REFERENCE_DATE)
        self.assertNotIn("REMOVEFILTERS(DIM_TEMPO)", C03_REFERENCE_DATE)
        for column in ("area", "tipo", "status", "perfil", "complexidade", "tipo_resposta"):
            self.assertIn(f"REMOVEFILTERS(PUB_C03_PIPELINE_MENSAL[{column}])", C03)
        for table in ("DIM_AREA", "DIM_STATUS_PESQUISA", "DIM_TIPO_PESQUISA"):
            self.assertIn(f"REMOVEFILTERS({table})", C03)
        self.assertIn("SUMMARIZECOLUMNS(", DAX_QUERIES)
        for column in ("area", "tipo", "perfil"):
            self.assertIn(f"PUB_C03_PIPELINE_MENSAL[{column}]", DAX_QUERIES)
        self.assertIn('TREATAS({"<area>"}, DIM_AREA[area])', DAX_QUERIES)

    def test_period_without_an_observed_c03_month_is_unavailable(self) -> None:
        self.assertIsNone(reference_stock([], set(), {"2099-12"}))
        self.assertIn("'Estado do Estoque'", C03)
        self.assertIn("Indisponível: a geração publicada não contém linha C03", C03)
        self.assertIn("IF(ISBLANK(DataReferencia), BLANK()", C03)

    def test_stock_readback_filters_c03_directly_at_the_reference_date(self) -> None:
        raw_c03 = [("2026-02-28", 4)]
        reference_date = max(date for date, _stock in raw_c03)
        stock = sum(value for date, value in raw_c03 if date == reference_date)

        self.assertEqual(reference_date, "2026-02-28")
        self.assertEqual(stock, 4)
        self.assertIn("REMOVEFILTERS(DIM_TEMPO)", C03_STOCK)
        self.assertIn(
            "PUB_C03_PIPELINE_MENSAL[data_fim_mes] = DataReferencia",
            C03_STOCK,
        )
        self.assertNotIn("DIM_TEMPO[data]", C03_STOCK)
        self.assertIn("BI04 Fixture Estoque Direto na Data Ref", DAX_QUERIES)
        self.assertIn('TREATAS({"2026-02"}, DIM_TEMPO[ano_mes])', DAX_QUERIES)

    def test_dx10_desktop_queries_show_catalog_and_two_text_measures(self) -> None:
        for column in ("indicador", "medida", "status", "motivo"):
            self.assertIn(f"DIM_INDICADORES_BLOQUEADOS[{column}]", DAX_QUERIES)
        self.assertIn("COUNTROWS(DIM_INDICADORES_BLOQUEADOS)", DAX_QUERIES)
        self.assertIn("[Qtd Indicadores Sem Dado]", DAX_QUERIES)
        self.assertIn("[Taxa de Prorrogacao]", DAX_QUERIES)
        self.assertIn("[Representatividade]", DAX_QUERIES)

    def test_zero_stock_and_no_observation_are_distinct_reference_states(self) -> None:
        observed_zero = reference_stock([], {"2026-10"}, {"2026-10"})
        not_observed = reference_stock([], set(), {"2026-10"})
        self.assertEqual(observed_zero, ("2026-10", 0))
        self.assertIsNone(not_observed)
        # Existing PUB_C03 has no closure marker, so DAX must leave this state
        # unavailable instead of manufacturing a zero or a sentinel fact row.
        self.assertIn("COALESCE(EstoqueNoMes, 0)", C03)
        self.assertIn("ISBLANK(DataReferencia), BLANK()", C03)
        self.assertNotIn("analytics_pipeline_closure", C03)

    def test_flow_numbers_stay_blank_and_have_separate_reason_measures(self) -> None:
        self.assertIn("SUM(PUB_C03_PIPELINE_MENSAL[qtd_entradas_no_mes])", C03)
        self.assertIn("SUM(PUB_C03_PIPELINE_MENSAL[qtd_saidas_no_mes])", C03)
        self.assertIn("'Estado das Entradas no Mês'", C03)
        self.assertIn("'Estado das Saídas no Mês'", C03)
        self.assertIn("histórico de transições de status não publicado", C03)


if __name__ == "__main__":
    unittest.main()
