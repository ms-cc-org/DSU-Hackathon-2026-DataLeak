"""Policy, money conservation and missing-data tests for the state fund."""

import unittest

import pandas as pd

from src.allocation import allocateFund


def exampleEstimates(losses: list[float | None]) -> pd.DataFrame:
    """Distinct county/crop records in a single state and year."""
    return pd.DataFrame([
        {"fips": f"06{rowIndex // 2 + 1:03d}", "county": f"County {rowIndex // 2 + 1}",
         "state": "CA", "crop": ["CORN", "WHEAT"][rowIndex % 2], "year": 2026,
         "estimatedLossUsd": loss}
        for rowIndex, loss in enumerate(losses)
    ], columns=["fips", "county", "state", "crop", "year", "estimatedLossUsd"])


class AllocationTests(unittest.TestCase):
    def testOneFundSharesAcrossCropsAndRollsUpCounties(self) -> None:
        result = allocateFund(exampleEstimates([100, 300, 600, None]), 100)
        detail = result["countyCropTable"]
        self.assertEqual(detail["allocationCents"].iloc[:3].tolist(), [1000, 3000, 6000])
        self.assertTrue(pd.isna(detail["allocationUsd"].iloc[3]))
        self.assertEqual(result["countyTable"]["allocationCents"].tolist(), [4000, 6000])
        self.assertEqual(int(result["cropTable"]["allocationCents"].sum()), 10000)
        self.assertEqual(result["summary"]["fundingGapUsd"], 900)
        self.assertEqual(result["summary"]["unavailableCropRows"], 1)

    def testLargestRemainderBalancesEveryCentDeterministically(self) -> None:
        estimates = exampleEstimates([1, 1, 1])
        result = allocateFund(estimates, 0.02)
        reversedResult = allocateFund(estimates.iloc[::-1], 0.02)
        self.assertEqual(result["countyCropTable"]["allocationCents"].tolist(), [1, 1, 0])
        pd.testing.assert_frame_equal(result["countyCropTable"], reversedResult["countyCropTable"])
        self.assertEqual(result["summary"]["allocatedUsd"], 0.02)

    def testMissingStaysMissingAndKnownZeroReceivesZero(self) -> None:
        result = allocateFund(exampleEstimates([None, None, 0]), 10)
        self.assertTrue(result["countyTable"]["estimatedLossUsd"].isna().iloc[0])
        self.assertTrue(pd.isna(result["countyTable"]["allocationUsd"].iloc[0]))
        self.assertEqual(result["countyTable"]["coverage"].tolist(), ["unavailable", "complete"])
        self.assertEqual(result["countyCropTable"]["allocationUsd"].iloc[2], 0)
        self.assertEqual(result["summary"]["unallocatedUsd"], 10)

    def testNoDataDoesNotClaimZeroLoss(self) -> None:
        result = allocateFund(exampleEstimates([None, None]), 10)
        self.assertIsNone(result["summary"]["estimatedLossUsd"])
        self.assertIsNone(result["summary"]["fundingGapUsd"])
        self.assertEqual(result["summary"]["unallocatedUsd"], 10)
        emptyResult = allocateFund(exampleEstimates([]), 10)
        self.assertTrue(emptyResult["countyTable"].empty)
        self.assertEqual(emptyResult["summary"]["unallocatedUsd"], 10)

    def testZeroFundAndFundAboveLossFollowTheDocumentedRule(self) -> None:
        estimates = exampleEstimates([100, 300])
        zeroResult = allocateFund(estimates, 0)
        self.assertEqual(zeroResult["summary"]["allocatedUsd"], 0)
        largeResult = allocateFund(estimates, 800)
        self.assertEqual(largeResult["countyCropTable"]["allocationUsd"].tolist(), [200, 600])
        self.assertEqual(largeResult["summary"]["fundToLossRatio"], 2)

    def testInvalidAmountsAreRejected(self) -> None:
        for fundUsd in (-1, float("nan"), float("inf")):
            with self.subTest(fundUsd=fundUsd), self.assertRaises(ValueError):
                allocateFund(exampleEstimates([100]), fundUsd)
        for lossUsd in (-1, float("inf"), "bad"):
            with self.subTest(lossUsd=lossUsd), self.assertRaises(ValueError):
                allocateFund(exampleEstimates([lossUsd]), 100)

    def testCrossStateAndCrossYearFundsAndDuplicateRowsAreRejected(self) -> None:
        for columnName, invalidValue in (("state", "IA"), ("year", 2027)):
            estimates = exampleEstimates([100, 100])
            estimates.loc[1, columnName] = invalidValue
            with self.subTest(columnName=columnName), self.assertRaises(ValueError):
                allocateFund(estimates, 100)
        estimates = exampleEstimates([100])
        with self.assertRaises(ValueError):
            allocateFund(pd.concat([estimates, estimates]), 100)

    def testFipsTextIsPreserved(self) -> None:
        self.assertEqual(allocateFund(exampleEstimates([100]), 1)["countyTable"]["fips"].iloc[0], "06001")
        estimates = exampleEstimates([100])
        estimates["fips"] = 6001
        with self.assertRaises(ValueError):
            allocateFund(estimates, 1)


if __name__ == "__main__":
    unittest.main()
