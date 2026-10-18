"""The 3D view must show the completed insurance numbers, including absent and zero estimates."""

import unittest

import pandas as pd

from web.insurance_map import insuranceMapData


class InsuranceMapTests(unittest.TestCase):
    def testCountyTotalsAndExposureWeightedSharesPreserveAllBoundaries(self) -> None:
        table = pd.DataFrame([
            {"fips": "19001", "crop": "CORN", "X_payout_usd": 100.25, "scenarioLiabilityUsd": 1000,
             "scenarioInsuredAcres": 100, "predDamagedAcres": 20, "out_of_range": False},
            {"fips": "19001", "crop": "SOYBEANS", "X_payout_usd": 200.50, "scenarioLiabilityUsd": 4000,
             "scenarioInsuredAcres": 400, "predDamagedAcres": 40, "out_of_range": True},
            {"fips": "19003", "crop": "CORN", "X_payout_usd": 0, "scenarioLiabilityUsd": 1000,
             "scenarioInsuredAcres": 100, "predDamagedAcres": 0, "out_of_range": False},
        ])
        payload = insuranceMapData(table, "IA", 2027)
        self.assertEqual(len(payload["counties"]), 99)
        self.assertEqual(payload["year"], 2027)
        self.assertEqual(payload["totalPayoutUsd"], 300.75)
        counties = {county["fips"]: county for county in payload["counties"]}
        self.assertEqual(counties["19001"]["payoutUsd"], 300.75)
        self.assertAlmostEqual(counties["19001"]["payoutShare"], 300.75 / 5000)
        self.assertAlmostEqual(counties["19001"]["damagedAcreShare"], 60 / 500)
        self.assertTrue(counties["19001"]["outOfRange"])
        self.assertEqual([crop["name"] for crop in counties["19001"]["crops"]], ["Corn", "Soybeans"])
        self.assertEqual(counties["19003"]["payoutUsd"], 0)
        self.assertIsNone(counties["19005"]["payoutUsd"])
        self.assertTrue(all(county["rings"] for county in counties.values()))

    def testNebraskaOnlyIncludesSelectedCropPredictions(self) -> None:
        table = pd.DataFrame([{"fips": "31001", "crop": "SOYBEANS", "X_payout_usd": 40,
                               "scenarioLiabilityUsd": 1000, "scenarioInsuredAcres": 100,
                               "predDamagedAcres": 5, "out_of_range": False}])
        payload = insuranceMapData(table, "NE", 2026)
        self.assertEqual(len(payload["counties"]), 93)
        available = [county for county in payload["counties"] if county["payoutUsd"] is not None]
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0]["crops"], [{"name": "Soybeans", "payoutUsd": 40}])
        self.assertEqual(payload["totalPayoutUsd"], 40)


if __name__ == "__main__":
    unittest.main()
