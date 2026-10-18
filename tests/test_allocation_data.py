"""Real supplied-data coverage and consistency checks for statewide scenarios."""

import unittest

import pandas as pd

from src.allocation import allocateFund
from web.allocation_data import buildStateEstimates, estimateCountyCrop
from web.render3d import CROPS, STATES, buildViewerData
from web.scenario_lookup import scenario
from web.ui import DEFAULT_PRICE


class StateEstimateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.viewerData = buildViewerData()
        cls.stateTables = {state: buildStateEstimates(state, 2026, "Predict", DEFAULT_PRICE) for state in STATES}

    def testAllBoundaryCountiesAndAllFourCropsStayVisible(self) -> None:
        for state, table in self.stateTables.items():
            countyIds = {countyData["fips"] for countyData in self.viewerData["counties"] if countyData["state"] == state}
            with self.subTest(state=state):
                self.assertEqual(set(table["fips"]), countyIds)
                self.assertEqual(len(table), len(countyIds) * len(CROPS))
                self.assertEqual(set(table["crop"]), set(CROPS))
                missingRows = table["estimatedLossUsd"].isna()
                self.assertTrue(table.loc[missingRows, "unavailableReason"].str.len().gt(0).all())
                result = allocateFund(table, 10_000_000.01)
                self.assertEqual(result["summary"]["allocatedUsd"], 10_000_000.01)
                detail = result["countyCropTable"]
                self.assertTrue(detail.loc[detail["estimatedLossUsd"].isna(), "allocationUsd"].isna().all())

    def testBulkLossAgreesWithExistingCountyPlannerForEverySupportedStateCrop(self) -> None:
        for state, table in self.stateTables.items():
            for crop, rows in table.dropna(subset=["estimatedLossUsd"]).groupby("crop"):
                row = rows.iloc[0]
                with self.subTest(state=state, crop=crop):
                    singleResult = scenario(row["fips"], crop, 2026, "Predict", DEFAULT_PRICE[crop])
                    self.assertAlmostEqual(row["estimatedLossUsd"], singleResult["dollars"](singleResult["mid"]), places=6)

    def testPriceChangeOnlyRescalesThatCropsLossAndChangesItsFundShare(self) -> None:
        baseTable = self.stateTables["IA"]
        newPrices = {**DEFAULT_PRICE, "SOYBEANS": DEFAULT_PRICE["SOYBEANS"] * 2}
        scaledTable = buildStateEstimates("IA", 2026, "Predict", newPrices)
        soyRows = baseTable["crop"].eq("SOYBEANS")
        pd.testing.assert_series_equal(scaledTable.loc[soyRows, "estimatedLossUsd"], baseTable.loc[soyRows, "estimatedLossUsd"] * 2)
        pd.testing.assert_series_equal(scaledTable.loc[~soyRows, "estimatedLossUsd"], baseTable.loc[~soyRows, "estimatedLossUsd"])
        baseResult = allocateFund(baseTable, 1000)["cropTable"].set_index("crop")
        scaledResult = allocateFund(scaledTable, 1000)["cropTable"].set_index("crop")
        self.assertGreater(scaledResult.loc["SOYBEANS", "allocationUsd"], baseResult.loc["SOYBEANS", "allocationUsd"])

    def testSevereDroughtFlagsNearestYearFallbackAndRetainsTheWarnings(self) -> None:
        table = buildStateEstimates("IA", 2030, "D4", DEFAULT_PRICE)
        fallbackRows = table["estimatedLossUsd"].notna() & ~table["confident"]
        self.assertTrue(fallbackRows.any())
        self.assertTrue(table.loc[fallbackRows, "warnings"].str.len().gt(0).all())
        self.assertTrue(table["estimatedLossUsd"].dropna().ge(0).all())

    def testMissingAcreageIsExcludedRatherThanZeroed(self) -> None:
        countyData = next(countyData for countyData in self.viewerData["counties"]
                          if countyData["fips"] == "19123")
        cropArrays = {**countyData["crops"]["CORN"], "acres": [None] * 26}
        missingAcres = {**countyData, "crops": {"CORN": cropArrays}}
        row = estimateCountyCrop(missingAcres, "CORN", 2026, "Predict", 4)
        self.assertIsNone(row["estimatedLossUsd"])
        self.assertIn("acreage", row["unavailableReason"])

    def testInvalidScenarioInputsAreRejected(self) -> None:
        for state, year, level, prices in (
            ("NY", 2026, "Predict", DEFAULT_PRICE), ("IA", 2031, "Predict", DEFAULT_PRICE),
            ("IA", 2026, "D5", DEFAULT_PRICE), ("IA", 2026, "Predict", {"CORN": 4}),
            ("IA", 2026, "Predict", {**DEFAULT_PRICE, "CORN": -1}),
        ):
            with self.subTest(state=state, year=year, level=level), self.assertRaises(ValueError):
                buildStateEstimates(state, year, level, prices)


if __name__ == "__main__":
    unittest.main()
