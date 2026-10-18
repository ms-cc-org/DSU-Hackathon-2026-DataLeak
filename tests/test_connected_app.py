"""Connected navigation, actual model predictions, fund joins and evidence rendering."""

from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest


repoRoot = Path(__file__).resolve().parents[1]


class ConnectedAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.appTest = AppTest.from_file(str(repoRoot / "app.py")).run(timeout=30)

    def openInsurance(self) -> None:
        self.appTest.switch_page("web/pages/3_scenarios.py").run(timeout=30)
        self.assertFalse(self.appTest.exception)

    def testFutureModelIsVisibleAndDirectPredictionsHaveExplicitLabels(self) -> None:
        self.openInsurance()
        definitions = self.appTest.dataframe[0].value
        self.assertEqual(definitions.loc[definitions["Source"].eq("Predicted by model D"), "Quantity"].tolist(),
                         ["Payout share (T1)", "Damaged-acre share (T2)"])
        self.appTest.button[0].click().run(timeout=30)
        self.assertFalse(self.appTest.exception)
        self.assertFalse(self.appTest.error)
        result = self.appTest.session_state["insuranceResult"]
        self.assertEqual(result["metadata"]["targetYear"], 2026)
        self.assertEqual(len(result["scenarioTotals"]), 26)
        labels = [metric.label for metric in self.appTest.metric]
        self.assertIn("D predicts · payout share", labels)
        self.assertIn("D predicts · damaged-acre share", labels)
        self.assertIn("X · estimated insurance payouts", labels)
        self.assertEqual(len(self.appTest.get("download_button")), 3)

    def testNebraskaSingleCropFutureScenarioUsesTheSelectedFootprint(self) -> None:
        self.openInsurance()
        next(widget for widget in self.appTest.selectbox if widget.label == "Insurance state").select("NE")
        next(widget for widget in self.appTest.selectbox if widget.label == "Insurance crops").select("SOYBEANS")
        next(widget for widget in self.appTest.selectbox if widget.label == "Insurance target year").select(2027)
        next(widget for widget in self.appTest.selectbox if widget.label == "Drought and weather assumption").select(2012)
        self.appTest.button[0].click().run(timeout=30)
        self.assertFalse(self.appTest.exception)
        self.assertFalse(self.appTest.error)
        result = self.appTest.session_state["insuranceResult"]
        self.assertEqual(set(result["countyTable"]["state"]), {"NE"})
        self.assertEqual(set(result["countyTable"]["crop"]), {"SOYBEANS"})
        self.assertEqual(result["metadata"]["footprintYears"], [2012])

    def testReplayShowsHeldOutModelAndObservedHistoricalOutcomes(self) -> None:
        self.openInsurance()
        self.appTest.radio[0].set_value("Historical replay").run(timeout=30)
        self.appTest.button[0].click().run(timeout=30)
        self.assertFalse(self.appTest.exception)
        self.assertFalse(self.appTest.error)
        result = self.appTest.session_state["insuranceResult"]
        self.assertEqual(result["metadata"]["modelArtifact"], "d_test.joblib")
        predictionTables = [frame.value for frame in self.appTest.dataframe if "actualPayoutUsd" in frame.value]
        self.assertEqual(len(predictionTables), 1)
        self.assertTrue(predictionTables[0]["actualPayoutUsd"].notna().all())

    def testHistoricalWhatIfIsClearlyDifferentFromHeldOutReplay(self) -> None:
        self.openInsurance()
        self.appTest.radio[0].set_value("Historical footprint scenario").run(timeout=30)
        next(widget for widget in self.appTest.selectbox if widget.label == "Drought and weather assumption").select(2012)
        self.appTest.button[0].click().run(timeout=30)
        self.assertFalse(self.appTest.exception)
        self.assertFalse(self.appTest.error)
        result = self.appTest.session_state["insuranceResult"]
        self.assertEqual(result["metadata"]["modelArtifact"], "d_full.joblib")
        self.assertIn("In-sample", result["metadata"]["evaluationLabel"])

    def testFundCalculationConnectsInsuranceWithoutChangingItsAllocationBasis(self) -> None:
        self.appTest.switch_page("web/pages/3_planner.py").run(timeout=30)
        self.appTest.button[0].click().run(timeout=30)
        self.assertFalse(self.appTest.exception)
        result = self.appTest.session_state["stateFundPlan"]
        self.assertIsNotNone(result["insuranceContext"])
        self.assertEqual(result["summary"]["allocatedUsd"], 10_000_000)
        self.assertEqual(set(result["countyCropTable"]["allocationRule"]), {"proportionalCropValueLoss"})
        self.assertIn("insurancePayoutShare", result["countyCropTable"])
        cornSoy = result["countyCropTable"]["crop"].isin(["CORN", "SOYBEANS"])
        self.assertTrue(result["countyCropTable"].loc[cornSoy, "insurancePayoutShare"].notna().all())
        self.assertTrue(result["countyCropTable"].loc[~cornSoy, "insurancePayoutShare"].isna().all())
        with self.assertNoLogs("streamlit.elements.lib.policies", level="WARNING"):
            self.appTest.switch_page("web/pages/3_scenarios.py").run(timeout=30)
        self.assertFalse(self.appTest.exception)
        self.assertEqual(self.appTest.session_state["insuranceResult"]["metadata"]["targetYear"], result["inputs"]["year"])
        self.assertEqual(self.appTest.selectbox(key="insuranceTargetYear").value, result["inputs"]["year"])
        self.assertEqual(self.appTest.selectbox(key="insuranceState").value, result["inputs"]["state"])

    def testAllFivePagesRenderAndEvidenceShowsSavedModelResults(self) -> None:
        for pagePath in ("web/pages/1_overview.py", "web/pages/2_county_risk.py", "web/pages/3_planner.py",
                         "web/pages/3_scenarios.py", "web/pages/5_method_and_data.py"):
            self.appTest.switch_page(pagePath).run(timeout=30)
            with self.subTest(pagePath=pagePath):
                self.assertFalse(self.appTest.exception)
                self.assertFalse(self.appTest.error)
        self.assertIn("Mean statewide payout error", [metric.label for metric in self.appTest.metric])


if __name__ == "__main__":
    unittest.main()
