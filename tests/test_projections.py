"""Next-year projection defaults, dollar conversion and all-state fund handoff."""

from io import StringIO
import math
import unittest

import pandas as pd

from src.allocation import allocateFund
from src.projections import nextCalendarYear, preferredProjectionYear, projectionYearLabel
from web.allocation_data import buildStateEstimates
from web.scenario_lookup import countyRecords, scenario
from web.ui import DEFAULT_PRICE


class ProjectionTests(unittest.TestCase):
    def testNextYearUsesTheCalendarRatherThanTheDatasetEnd(self) -> None:
        self.assertEqual(nextCalendarYear(2026), 2027)
        self.assertEqual(preferredProjectionYear(2026, 2030, currentYear=2026), 2027)
        self.assertEqual(projectionYearLabel(2027, currentYear=2026), "2027 (next year)")
        self.assertEqual(projectionYearLabel(2026, currentYear=2026), "2026 (projected)")

    def testDefaultsStayWithinTheSupportedHorizon(self) -> None:
        self.assertEqual(preferredProjectionYear(2026, 2030, currentYear=2024), 2026)
        self.assertEqual(preferredProjectionYear(2026, 2030, currentYear=2030), 2030)
        self.assertEqual(projectionYearLabel(2030, currentYear=2030), "2030 (projected)")
        with self.assertRaises(ValueError):
            preferredProjectionYear(2031, 2030)

    def test2027CountyLossUsesThe2027YieldProjection(self) -> None:
        records = countyRecords("19123", "CORN")
        previousResult = scenario("19123", "CORN", 2026, "Predict", 4)
        nextResult = scenario("19123", "CORN", 2027, "Predict", 4)
        slope, intercept = records["trend"]
        expectedTrendYield = intercept + slope * 2027
        self.assertTrue(nextResult["projected"])
        self.assertAlmostEqual(nextResult["trendYield"], expectedTrendYield)
        self.assertAlmostEqual(nextResult["trendYield"] - previousResult["trendYield"], slope)
        expectedLossUsd = expectedTrendYield * nextResult["mid"] / 100 * records["acres"] * 4
        self.assertAlmostEqual(nextResult["dollars"](nextResult["mid"]), expectedLossUsd)
        self.assertGreater(expectedLossUsd, 0)
        self.assertNotEqual(nextResult["dollars"](nextResult["mid"]), previousResult["dollars"](previousResult["mid"]))

    def test2027AllStatePredictionsAllocateAndExportWithTheirYear(self) -> None:
        for state in ("IA", "NE", "CA", "DE"):
            with self.subTest(state=state):
                estimates = buildStateEstimates(state, 2027, "Predict", DEFAULT_PRICE)
                knownLosses = estimates["estimatedLossUsd"].dropna()
                self.assertFalse(knownLosses.empty)
                self.assertTrue(knownLosses.map(math.isfinite).all())
                self.assertTrue(knownLosses.ge(0).all())
                result = allocateFund(estimates, 1_000_000.01)
                exported = pd.read_csv(StringIO(result["countyCropTable"].to_csv(index=False)), dtype={"fips": str})
                self.assertEqual(set(exported["year"]), {2027})
                self.assertEqual(set(exported["crop"]), set(DEFAULT_PRICE))
                self.assertEqual(int(exported["allocationCents"].sum()), 100_000_001)
                self.assertEqual(result["summary"]["allocatedUsd"], 1_000_000.01)


if __name__ == "__main__":
    unittest.main()
