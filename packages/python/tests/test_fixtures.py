from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "python" / "src"))

from cumbin import cumbin  # noqa: E402


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
