from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "python" / "src"))

from cumbin import cumbin, summarize_bins  # noqa: E402


class FixtureTests(unittest.TestCase):
    def test_shared_fixtures(self) -> None:
        fixtures = sorted((ROOT / "fixtures").glob("*.json"))
        self.assertGreater(len(fixtures), 0)

        for path in fixtures:
            with self.subTest(path=path.name):
                fixture = json.loads(path.read_text())
                actual = cumbin(fixture["input"], fixture["spec"])
                self.assert_rows_almost_equal(actual, fixture["expected"])

    def test_single_bin_when_cumulative_total_equals_bin_size(self) -> None:
        rows = cumbin(
            [
                {"label": "A", "value": 12},
                {"label": "B", "value": 3},
                {"label": "C", "value": 17},
            ],
            {"value": "value", "binSize": 32},
        )

        self.assertEqual(len(rows), 3)
        self.assertEqual(sorted({row["bin"] for row in rows}), [0])
        self.assertEqual([row["amount"] for row in rows], [12.0, 3.0, 17.0])
        self.assertEqual(
            [(row["bin_start"], row["bin_end"]) for row in rows],
            [(0.0, 32.0), (0.0, 32.0), (0.0, 32.0)],
        )

    def test_cumulative_mode_accepts_an_empty_string_field_name(self) -> None:
        rows = cumbin(
            [
                {"": 4},
                {"": 11},
            ],
            {"cumulative": "", "binSize": 10},
        )

        self.assertEqual([row["amount"] for row in rows], [4.0, 6.0, 1.0])
        self.assertEqual([row["source_start"] for row in rows], [0.0, 4.0, 4.0])
        self.assertEqual([row["source_end"] for row in rows], [4.0, 11.0, 11.0])

    def test_rejects_thresholds_with_fewer_than_two_boundaries(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "thresholds must include at least two boundaries",
        ):
            cumbin([{"value": 1}], {"value": "value", "thresholds": [0]})

    def test_rejects_non_finite_thresholds(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "expected a finite number for thresholds",
        ):
            cumbin(
                [{"value": 1}],
                {"value": "value", "thresholds": [0, float("nan")]},
            )

    def test_include_source_false_only_emits_transform_fields(self) -> None:
        rows = cumbin(
            [{"label": "A", "value": 12}],
            {"value": "value", "binSize": 10, "includeSource": False},
        )

        self.assertEqual(
            rows,
            [
                {
                    "bin": 0,
                    "bin_start": 0.0,
                    "bin_end": 10.0,
                    "amount": 10.0,
                    "source_index": 0,
                    "source_start": 0.0,
                    "source_end": 12.0,
                    "source_amount": 12.0,
                    "source_fraction": 10 / 12,
                },
                {
                    "bin": 1,
                    "bin_start": 10.0,
                    "bin_end": 20.0,
                    "amount": 2.0,
                    "source_index": 0,
                    "source_start": 0.0,
                    "source_end": 12.0,
                    "source_amount": 12.0,
                    "source_fraction": 2 / 12,
                },
            ],
        )

    def test_summarize_bins_aggregates_amounts_by_bin_and_group_fields(self) -> None:
        rows = cumbin(
            [
                {"group": "north", "value": 6},
                {"group": "south", "value": 4},
                {"group": "north", "value": 7},
            ],
            {"value": "value", "binSize": 10, "groupBy": "group"},
        )

        self.assertEqual(
            summarize_bins(rows, group_by="group"),
            [
                {
                    "bin": 0,
                    "bin_start": 0.0,
                    "bin_end": 10.0,
                    "amount": 10.0,
                    "count": 2,
                    "group": "north",
                },
                {
                    "bin": 0,
                    "bin_start": 0.0,
                    "bin_end": 10.0,
                    "amount": 4.0,
                    "count": 1,
                    "group": "south",
                },
                {
                    "bin": 1,
                    "bin_start": 10.0,
                    "bin_end": 20.0,
                    "amount": 3.0,
                    "count": 1,
                    "group": "north",
                },
            ],
        )

    def assert_rows_almost_equal(
        self,
        actual: list[dict[str, object]],
        expected: list[dict[str, object]],
    ) -> None:
        self.assertEqual(len(actual), len(expected))

        for row_index, (actual_row, expected_row) in enumerate(zip(actual, expected)):
            keys = set(actual_row) | set(expected_row)
            for key in keys:
                actual_value = actual_row.get(key)
                expected_value = expected_row.get(key)

                if isinstance(expected_value, (int, float)):
                    self.assertAlmostEqual(
                        actual_value,
                        expected_value,
                        places=12,
                        msg=f"row {row_index}.{key}",
                    )
                else:
                    self.assertEqual(
                        actual_value,
                        expected_value,
                        msg=f"row {row_index}.{key}",
                    )


if __name__ == "__main__":
    unittest.main()
