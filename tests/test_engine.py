"""Contract tests for the prefit Lane 2 engine."""

from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from src.engine import _loadArtifact, _loadScenarioInputs, predict, replay, scenario
from src.reserve_band import load_ratio_band


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


class PlanningBandEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = scenario(2023, 2012, state="IA", crop="CORN")
        cls.scaled = scenario(2023, 2012, state="IA", crop="CORN",
                              acres_scale=1.25, price_scale=0.9)
        cls.replayed = replay(2023)

    def assertBand(self, band, plan) -> None:
        constants = load_ratio_band()
        self.assertEqual(band["plan_usd"], plan)
        self.assertEqual(band["low_usd"], plan * constants["q05"])
        self.assertEqual(band["high_usd"], plan * constants["q95"])
        self.assertEqual(band["label"], constants["label"])
        self.assertEqual(band["source_years"], "2006-2015")

    def testScenarioBandUsesScaledStatewideX(self) -> None:
        for result in (self.base, self.scaled):
            self.assertBand(result["reserve_band_x_usd"],
                            result["statewide_totals"]["X_payout_usd"])
        for key in ("plan_usd", "low_usd", "high_usd"):
            self.assertAlmostEqual(self.scaled["reserve_band_x_usd"][key],
                                   self.base["reserve_band_x_usd"][key] * 1.25 * 0.9,
                                   delta=0.000001)

    def testReplayBandIsKeyedByState(self) -> None:
        bands = self.replayed["reserve_band_x_usd"]
        self.assertEqual(set(bands), {"IA", "NE"})
        for row in self.replayed["statewide_totals"].itertuples(index=False):
            self.assertBand(bands[row.state], row.X_payout_usd)

    def testExistingOutputsRemainUnchanged(self) -> None:
        # Regression values captured from main before adding the planning band.
        expectedTotals = {"X_payout_usd": 1323766930.2340508,
                          "Y_deductible_exposure_usd": 1037199907.5161399,
                          "Z_relief_95pct_usd": 769363693.1175536}
        for key, expected in expectedTotals.items():
            self.assertAlmostEqual(self.base["statewide_totals"][key], expected, delta=1.0)
        historicalRange = self.base["historical_scenario_range_x_usd"]
        self.assertAlmostEqual(historicalRange["low_usd"], 480195904.61809796, delta=1.0)
        self.assertAlmostEqual(historicalRange["high_usd"], 3551499750.777338, delta=1.0)
        self.assertFalse(historicalRange["widened"])
        inputs = _loadScenarioInputs()
        rows = inputs.loc[inputs["year"].eq(2023) & inputs["liability"].gt(0) &
                          inputs["insured_acres"].gt(0)]
        pd.testing.assert_frame_equal(self.replayed["county_table"], predict(rows, model="test"),
                                      check_exact=True)
        self.assertNotIn("reserve_band_x_usd", self.base["county_table"].columns)
        for row in self.replayed["statewide_totals"].itertuples(index=False):
            expected = {"IA": 479176885.48, "NE": 131481143.79}[row.state]
            self.assertAlmostEqual(row.X_payout_usd, expected, delta=1.0)

    def testRatioBandUsesOnlyOutOfSample2006Through2015(self) -> None:
        years = load_ratio_band()["source_years"]
        self.assertEqual(years, list(range(2006, 2016)))
        self.assertTrue(all(year <= 2015 for year in years))


if __name__ == "__main__":
    unittest.main()
