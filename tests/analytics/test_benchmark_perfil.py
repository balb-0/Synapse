"""SQL reference for the area-profile contract; this does not execute DAX."""

import sqlite3
import unittest


def reference_profile(rows, selected, areas):
    """Distinct research per company, then equal-weight mean over a fixed cohort."""
    if selected is None:
        return {area: None for area in areas}
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE TABLE participation(company, research, area)")
        connection.executemany("INSERT INTO participation VALUES (?, ?, ?)", rows)
        connection.execute("CREATE TABLE selected_area(area PRIMARY KEY)")
        connection.executemany("INSERT INTO selected_area VALUES (?)", [(a,) for a in areas])
        result = connection.execute(
            """
            WITH observed AS (
                SELECT DISTINCT company, research, area FROM participation
                WHERE company IS NOT NULL AND research IS NOT NULL
                  AND company <> ? AND area IN (SELECT area FROM selected_area)
            ), cohort AS (
                SELECT company, COUNT(DISTINCT research) AS total
                FROM observed GROUP BY company
            )
            SELECT a.area, AVG(1.0 * (
                SELECT COUNT(DISTINCT o.research) FROM observed o
                WHERE o.company = c.company AND o.area = a.area
            ) / c.total)
            FROM selected_area a LEFT JOIN cohort c ON TRUE GROUP BY a.area
            """,
            (selected,),
        ).fetchall()
        return dict(result)
    finally:
        connection.close()


class BenchmarkAreaContractTests(unittest.TestCase):
    def test_disjoint_companies_do_not_make_every_area_one_hundred_percent(self):
        rows = [(f"company-{i}", f"research-{i}", a) for i, a in enumerate("ABCD")]
        values = reference_profile(rows, "selected", list("ABCD"))
        self.assertEqual(values, dict.fromkeys("ABCD", 0.25))
        self.assertAlmostEqual(sum(values.values()), 1)

    def test_mean_of_company_shares_is_not_share_of_all_participations(self):
        rows = [("b", "1", "A"), ("b", "2", "A"), ("b", "3", "A")]
        rows += [("b", "4", "B"), ("c", "4", "B")]
        self.assertEqual(reference_profile(rows, "selected", ["A", "B"]), {"A": 0.375, "B": 0.625})

    def test_slicer_changes_cohort_and_preserves_zero_in_empty_axis_area(self):
        rows = [("b", "1", "A"), ("c", "2", "B")]
        self.assertEqual(reference_profile(rows, "selected", ["A"]), {"A": 1.0})
        self.assertEqual(reference_profile(rows, "selected", ["A", "C"]), {"A": 1.0, "C": 0.0})

    def test_duplicates_unknown_keys_and_selected_company_do_not_change_reference(self):
        rows = [("b", "1", "A"), ("b", "1", "A"), (None, "2", "B")]
        rows += [("b", None, "B"), ("selected", "3", "B")]
        self.assertEqual(reference_profile(rows, "selected", ["A", "B"]), {"A": 1.0, "B": 0.0})

    def test_no_comparable_company_or_no_unique_selection_is_unavailable(self):
        self.assertEqual(reference_profile([], "selected", ["A"]), {"A": None})
        self.assertEqual(
            reference_profile([("selected", "1", "A")], "selected", ["A"]), {"A": None}
        )
        self.assertEqual(reference_profile([("b", "1", "A")], None, ["A"]), {"A": None})
