"""Structural checks for the published-cube Power BI semantic model.

These checks cover the TMDL contract only; they do not claim Desktop execution.
"""

import re
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFINITION = ROOT / "powerbi/CentralPesquisasBI.SemanticModel/definition"
TABLES = DEFINITION / "tables"


def _columns(table_name: str) -> set[str]:
    source = (TABLES / f"{table_name}.tmdl").read_text(encoding="utf-8")
    return set(re.findall(r"(?m)^\s*column\s+([^\s=]+)", source))


def _relationships() -> list[dict[str, str]]:
    source = (DEFINITION / "relationships.tmdl").read_text(encoding="utf-8")
    result = []
    for block in re.split(r"(?m)^relationship\s+", source)[1:]:
        name, *lines = block.splitlines()
        properties = dict(re.findall(r"(?m)^\s*([A-Za-z]+):\s*(.+?)\s*$", "\n".join(lines)))
        properties["name"] = name.strip()
        result.append(properties)
    return result


class PublishedModelContractTests(unittest.TestCase):
    def test_relationships_are_exact_dimension_to_fact_dag(self):
        expected = {
            ("PUB_C01_CICLO.area", "DIM_AREA.area"),
            ("PUB_C02_PARTICIPACAO.area", "DIM_AREA.area"),
            ("PUB_C03_PIPELINE_MENSAL.area", "DIM_AREA.area"),
            ("PUB_C04_INSTRUMENTO.area", "DIM_AREA.area"),
            ("PUB_C01_CICLO.tipo", "DIM_TIPO_PESQUISA.tipo"),
            ("PUB_C02_PARTICIPACAO.tipo", "DIM_TIPO_PESQUISA.tipo"),
            ("PUB_C03_PIPELINE_MENSAL.tipo", "DIM_TIPO_PESQUISA.tipo"),
            (
                "PUB_C04_INSTRUMENTO.tipo_pergunta",
                "DIM_TIPO_PERGUNTA.tipo_pergunta",
            ),
            ("PUB_C01_CICLO.status", "DIM_STATUS_PESQUISA.status"),
            ("PUB_C03_PIPELINE_MENSAL.status", "DIM_STATUS_PESQUISA.status"),
            ("PUB_C02_PARTICIPACAO.mes_resposta", "DIM_TEMPO.data"),
            ("PUB_C03_PIPELINE_MENSAL.data_fim_mes", "DIM_TEMPO.data"),
        }
        relationships = _relationships()
        self.assertEqual(len(relationships), len(expected))
        actual = {
            (relationship["fromColumn"], relationship["toColumn"]) for relationship in relationships
        }
        self.assertEqual(actual, expected)

        nodes = set()
        outgoing: dict[str, set[str]] = {}
        indegree: dict[str, int] = {}
        for relationship in relationships:
            self.assertEqual(
                set(relationship),
                {
                    "name",
                    "fromCardinality",
                    "toCardinality",
                    "crossFilteringBehavior",
                    "fromColumn",
                    "toColumn",
                },
            )
            source_table, source_column = relationship["fromColumn"].split(".")
            target_table, target_column = relationship["toColumn"].split(".")
            self.assertTrue(source_table.startswith("PUB_C0"))
            self.assertTrue(target_table.startswith("DIM_"))
            self.assertIn(source_column, _columns(source_table))
            self.assertIn(target_column, _columns(target_table))
            self.assertEqual(relationship["fromCardinality"], "many")
            self.assertEqual(relationship["toCardinality"], "one")
            self.assertEqual(relationship["crossFilteringBehavior"], "oneDirection")

            # Model filter flow from the one-side dimension to the many-side fact.
            nodes.update((target_table, source_table))
            outgoing.setdefault(target_table, set()).add(source_table)
            outgoing.setdefault(source_table, set())
            indegree.setdefault(target_table, 0)
            indegree[source_table] = indegree.get(source_table, 0) + 1

        ready = [node for node in nodes if indegree.get(node, 0) == 0]
        visited = 0
        while ready:
            node = ready.pop()
            visited += 1
            for neighbor in outgoing[node]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    ready.append(neighbor)
        self.assertEqual(visited, len(nodes), "filter propagation graph has a cycle")
        self.assertTrue(all(not outgoing[table] for table in nodes if table.startswith("PUB_C0")))

    def test_calculated_table_columns_map_to_dax_output_columns(self):
        calculated_tables = []
        for path in sorted(TABLES.glob("*.tmdl")):
            source = path.read_text(encoding="utf-8")
            if not re.search(r"(?m)^\s*partition\s+[^\n]+\s*=\s*calculated\s*$", source):
                continue

            columns = []
            lines = source.splitlines()
            for index, line in enumerate(lines):
                match = re.match(r"\tcolumn\s+([^\s=]+)(?:\s*=.*)?$", line)
                if not match:
                    continue

                # A column expression defines a calculated column in the
                # model; only unassigned columns are outputs of the table DAX.
                if "=" in line:
                    continue

                properties = []
                for property_line in lines[index + 1 :]:
                    if re.match(r"\t(?:column|measure|partition|hierarchy)\b", property_line):
                        break
                    properties.append(property_line.strip())
                columns.append((match.group(1), properties))

            self.assertTrue(columns, f"calculated table {path.stem} has no output columns")
            calculated_tables.append(path.stem)
            for name, properties in columns:
                with self.subTest(table=path.stem, column=name):
                    self.assertIn("isNameInferred", properties)
                    self.assertIn("isDataTypeInferred", properties)
                    self.assertIn(f"sourceColumn: [{name}]", properties)

        self.assertEqual(
            set(calculated_tables),
            {
                "DIM_AREA",
                "DIM_INDICADORES_BLOQUEADOS",
                "DIM_STATUS_PESQUISA",
                "DIM_TEMPO",
                "DIM_TIPO_PERGUNTA",
                "DIM_TIPO_PESQUISA",
            },
        )

    def test_month_sort_key_is_functional_for_c02_and_c03_dates(self):
        source = (TABLES / "DIM_TEMPO.tmdl").read_text(encoding="utf-8")
        self.assertRegex(source, r"(?m)^\s*sortByColumn:\s*ano_mes_ordenacao$")
        self.assertIn("YEAR([data]) * 100 + MONTH([data])", source)
        self.assertIn('"ano_mes", IF(ISBLANK([data]), BLANK(), FORMAT([data], "YYYY-MM"))', source)
        for attribute in (
            "ano",
            "numero_trimestre",
            "trimestre",
            "numero_mes",
            "mes",
            "ano_mes",
        ):
            self.assertRegex(
                source,
                rf'"{attribute}", IF\(ISBLANK\(\[data\]\), BLANK\(\),',
            )

        # C02 publishes month start, while C03 publishes month end. Both must
        # map to the same YYYYMM sort value for the label YYYY-MM.
        dates = (date(2026, 9, 1), date(2026, 9, 30))
        sort_values_by_label: dict[str, set[int]] = {}
        for value in dates:
            label = value.strftime("%Y-%m")
            sort_values_by_label.setdefault(label, set()).add(value.year * 100 + value.month)
        self.assertEqual(sort_values_by_label, {"2026-09": {202609}})

    def test_calendar_filters_blank_fact_dates_out_of_dimension(self):
        source = (TABLES / "DIM_TEMPO.tmdl").read_text(encoding="utf-8")
        calendar_expression = source.split("partition DIM_TEMPO = calculated", 1)[1]
        self.assertRegex(
            calendar_expression,
            r"FILTER\(\s*DISTINCT\(UNION\(_DatasParticipacao, _DatasPipeline\)\),"
            r"\s*NOT ISBLANK\(\[data\]\)\s*\)",
        )

    def test_unknown_and_partial_profile_values_are_explicit(self):
        source = (TABLES / "PUB_C03_PIPELINE_MENSAL.tmdl").read_text(encoding="utf-8")
        profile = source.split("\tcolumn perfil =", 1)[1].split("\n\thierarchy", 1)[0]
        self.assertIn("ISBLANK([complexidade]) && ISBLANK([tipo_resposta])", profile)
        self.assertIn("BLANK()", profile)
        self.assertIn('COALESCE([complexidade], "Indisponível")', profile)
        self.assertIn('COALESCE([tipo_resposta], "Indisponível")', profile)

        self.assertIn("column: perfil", source)


if __name__ == "__main__":
    unittest.main()
