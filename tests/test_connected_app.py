"""Connected navigation, actual model predictions and fund joins."""

import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


repoRoot = Path(__file__).resolve().parents[1]


class ConnectedAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.appTest = AppTest.from_file(str(repoRoot / "app.py")).run(timeout=30)

    def openInsurance(self) -> None:
        self.appTest.switch_page("web/pages/3_scenarios.py").run(timeout=30)
        self.assertFalse(self.appTest.exception)

    def mapPayload(self) -> dict:
        frames = self.appTest.get("iframe")
        self.assertEqual(len(frames), 1)
        payload = re.search(r'<script id="predictionData" type="application/json">(.*?)</script>', frames[0].proto.srcdoc)
        self.assertIsNotNone(payload)
        return json.loads(payload.group(1))

    def assertSelectedInsuranceScope(self, crops: set[str], state: str = "IA") -> None:
        result = self.appTest.session_state["insuranceResult"]
        self.assertFalse(self.appTest.exception)
        self.assertFalse(self.appTest.error)
        for tableName in ("countyTable", "drawTable", "modelInputs"):
            table = result[tableName]
            self.assertEqual(set(table["crop"]), crops)
            stateColumn = "state_alpha" if tableName == "modelInputs" else "state"
            self.assertEqual(set(table[stateColumn]), {state})
        payload = self.mapPayload()
        self.assertEqual(payload["stateCode"], state)
        self.assertAlmostEqual(payload["totalPayoutUsd"], result["totals"]["X_payout_usd"], places=5)
        countyRows = result["countyTable"]
        countyTotals = countyRows.groupby("fips")["X_payout_usd"].sum()
        cropNames = {"CORN": "Corn", "SOYBEANS": "Soybeans"}
        for county in payload["counties"]:
            if county["payoutUsd"] is not None:
                self.assertAlmostEqual(county["payoutUsd"], countyTotals.loc[county["fips"]], places=5)
                self.assertTrue({crop["name"] for crop in county["crops"]}.issubset({cropNames[crop] for crop in crops}))
        for label, key in (("Predicted insurance payouts", "X_payout_usd"),
                           ("Y · estimated deductible exposure", "Y_deductible_exposure_usd"),
                           ("Z · illustrative 95% relief", "Z_relief_95pct_usd")):
            metric = next(metric for metric in self.appTest.metric if metric.label == label)
            self.assertEqual(metric.value, f"${countyRows[key].sum():,.0f}")
        predictionTable = next(frame.value for frame in self.appTest.dataframe if "pred_payout_share" in frame.value)
        self.assertEqual(set(predictionTable["crop"]), crops)

    def testChangingCropRefreshesEveryResultWithoutAnotherRunClick(self) -> None:
        self.openInsurance()
        self.appTest.button[0].click().run(timeout=30)
        self.assertSelectedInsuranceScope({"CORN", "SOYBEANS"})
        for crop, selected in (("CORN", {"CORN"}), ("SOYBEANS", {"SOYBEANS"}), ("ALL", {"CORN", "SOYBEANS"})):
            with self.subTest(crop=crop):
                self.appTest.selectbox(key="insuranceCrop").select(crop).run(timeout=30)
                self.assertSelectedInsuranceScope(selected)

    def testScenarioControlsRefreshInputsTotalsAndMapTogether(self) -> None:
        self.openInsurance()
        self.appTest.button[0].click().run(timeout=30)
        self.appTest.selectbox(key="insuranceCrop").select("CORN").run(timeout=30)
        self.appTest.selectbox(key="insuranceState").select("NE").run(timeout=30)
        self.assertSelectedInsuranceScope({"CORN"}, "NE")
        self.appTest.selectbox(key="insuranceTargetYear").select(2027).run(timeout=30)
        self.appTest.selectbox(key="insuranceBaseYear").select(2023).run(timeout=30)
        self.appTest.selectbox(key="insuranceFutureFootprint").select(2012).run(timeout=30)
        baseResult = self.appTest.session_state["insuranceResult"]
        self.assertEqual(baseResult["metadata"]["exposureBaseYear"], 2023)
        self.assertEqual(baseResult["metadata"]["footprintYears"], [2012])
        self.assertEqual(self.mapPayload()["year"], 2027)
        self.appTest.number_input(key="insuranceAcresScale").set_value(2.0).run(timeout=30)
        self.appTest.number_input(key="insurancePriceScale").set_value(1.5).run(timeout=30)
        result = self.appTest.session_state["insuranceResult"]
        self.assertAlmostEqual(result["totals"]["X_payout_usd"], baseResult["totals"]["X_payout_usd"] * 3)
        self.assertAlmostEqual(result["totals"]["payoutShare"], baseResult["totals"]["payoutShare"], places=12)
        self.assertSelectedInsuranceScope({"CORN"}, "NE")

    def testCropChangesRefreshHistoricalWhatIfAndReplay(self) -> None:
        self.openInsurance()
        self.appTest.button[0].click().run(timeout=30)
        for mode in ("Historical footprint scenario", "Historical replay"):
            self.appTest.radio(key="insuranceMode").set_value(mode).run(timeout=30)
            for crop, selected in (("SOYBEANS", {"SOYBEANS"}), ("CORN", {"CORN"}), ("ALL", {"CORN", "SOYBEANS"})):
                with self.subTest(mode=mode, crop=crop):
                    self.appTest.selectbox(key="insuranceCrop").select(crop).run(timeout=30)
                    self.assertSelectedInsuranceScope(selected)
                    self.assertEqual(self.appTest.session_state["insuranceResult"]["metadata"]["selection"]["mode"], mode)
        self.appTest.selectbox(key="insuranceReplayYear").select(2022).run(timeout=30)
        self.assertEqual(self.mapPayload()["year"], 2022)

    def testFailedRefreshRemovesStalePredictionsAndCanRecover(self) -> None:
        self.openInsurance()
        self.appTest.button[0].click().run(timeout=30)
        with patch("web.insurance_ui.runInsurance", side_effect=ValueError("Unavailable selected inputs")):
            self.appTest.selectbox(key="insuranceCrop").select("CORN").run(timeout=30)
        self.assertTrue(self.appTest.error)
        self.assertNotIn("insuranceResult", self.appTest.session_state)
        self.assertEqual(len(self.appTest.metric), 0)
        self.assertEqual(len(self.appTest.get("iframe")), 0)
        self.assertEqual(len(self.appTest.get("download_button")), 0)
        self.appTest.run(timeout=30)
        self.assertSelectedInsuranceScope({"CORN"})

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
        self.assertIn("Predicted payout share", labels)
        self.assertIn("Predicted damaged-acre share", labels)
        self.assertIn("Predicted insurance payouts", labels)
        payload = self.mapPayload()
        self.assertEqual(len(payload["counties"]), 99)
        self.assertAlmostEqual(payload["totalPayoutUsd"], result["totals"]["X_payout_usd"], places=5)
        self.assertIn("Predicted results · Iowa · 2026", [heading.value for heading in self.appTest.subheader])
        self.assertNotIn("Insurance payout map", [expander.label for expander in self.appTest.expander])
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
        payload = self.mapPayload()
        self.assertEqual(payload["stateCode"], "NE")
        self.assertEqual(payload["year"], 2027)
        self.assertEqual(len(payload["counties"]), 93)
        self.assertEqual(payload["cropLabel"], "Soybeans")
        self.assertAlmostEqual(payload["totalPayoutUsd"], result["totals"]["X_payout_usd"], places=5)

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

    def testPlannerLinksToInsuranceWithoutStateFundControls(self) -> None:
        self.appTest.switch_page("web/pages/3_planner.py").run(timeout=30)
        self.assertFalse(self.appTest.exception)
        self.assertFalse(self.appTest.error)
        self.assertEqual(next(widget for widget in self.appTest.selectbox if widget.label == "Year").value, 2026)
        self.assertFalse(any(widget.label == "State fund ($)" for widget in self.appTest.number_input))
        self.assertFalse(any(button.label == "Calculate state allocation" for button in self.appTest.button))
        self.openInsurance()
        self.appTest.button[0].click().run(timeout=30)
        self.assertSelectedInsuranceScope({"CORN", "SOYBEANS"})

    def testAllFourPagesRenderWithoutRemovedEvidenceLinks(self) -> None:
        for pagePath in ("web/pages/1_overview.py", "web/pages/2_county_risk.py", "web/pages/3_planner.py",
                         "web/pages/3_scenarios.py"):
            self.appTest.switch_page(pagePath).run(timeout=30)
            with self.subTest(pagePath=pagePath):
                self.assertFalse(self.appTest.exception)
                self.assertFalse(self.appTest.error)
                self.assertFalse(any("Evidence" in link.proto.label for link in self.appTest.get("page_link")))
        self.assertFalse((repoRoot / "web/pages/5_method_and_data.py").exists())


if __name__ == "__main__":
    unittest.main()
