"""Contract tests for the prefit Lane 2 engine."""

from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from src.engine import _loadArtifact, _loadScenarioInputs, predict, replay, scenario


repoRoot = Path(__file__).resolve().parents[1]
referencePath = repoRoot / "app" / "model" / "results" / "test_state_years.csv"


class EngineTests(unittest.TestCase):
    def testOfficialStateYearTotals(self) -> None:
        """The test artifact must reproduce every saved official D statewide X."""
        reference = pd.read_csv(referencePath)
        actualRows = []
        for year in range(2016, 2026):
            result = replay(year)
            self.assertEqual(result["model"], "test")
            self.assertEqual(result["evaluation_label"], "out-of-sample")
            actualRows.append(result["statewide_totals"].assign(year=year))
        actual = pd.concat(actualRows, ignore_index=True)
        compared = actual.merge(reference, left_on=["state", "year"],
                                right_on=["state_alpha", "year"], validate="one_to_one")
        self.assertEqual(len(compared), len(reference))
        maximumDifference = (compared["X_payout_usd"] - compared["d_x_payout_usd"]).abs().max()
        self.assertLess(maximumDifference, 1.0)

    def testScenarioReturnsNonnegativeDollars(self) -> None:
        result = scenario(2023, 2012)
        table = result["county_table"]
        self.assertFalse(table.empty)
        for columnName in ("X_payout_usd", "Y_deductible_exposure_usd", "Z_relief_95pct_usd"):
            self.assertTrue(table[columnName].ge(0).all())
            self.assertGreaterEqual(result["statewide_totals"][columnName], 0)
        self.assertEqual(len(result["closest_historical_years"]), 3)
        self.assertLessEqual(result["historical_scenario_range_x_usd"]["low_usd"],
                             result["historical_scenario_range_x_usd"]["high_usd"])

    def testOutOfRangeInputIsFlagged(self) -> None:
        example = _loadScenarioInputs().loc[lambda frame: frame["liability"].gt(0)].head(1).copy()
        upperBound = _loadArtifact("full")["feature_bounds"].loc["max", "d2_pct_last_map"]
        example["d2_pct_last_map"] = upperBound + 100
        result = predict(example)
        self.assertTrue(bool(result["out_of_range"].iloc[0]))
        self.assertIn("d2_pct_last_map", result["out_of_range_features"].iloc[0])

    def testAcresScaleDoublesXExactly(self) -> None:
        baseResult = scenario(2023, 2012)
        scaledResult = scenario(2023, 2012, acres_scale=2)
        baseX = baseResult["county_table"]["X_payout_usd"]
        scaledX = scaledResult["county_table"]["X_payout_usd"]
        pd.testing.assert_series_equal(scaledX, baseX * 2, check_exact=True)
        self.assertEqual(scaledResult["statewide_totals"]["X_payout_usd"],
                         float(scaledX.sum()))


if __name__ == "__main__":
    unittest.main()
