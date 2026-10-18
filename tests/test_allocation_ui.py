"""Exercise the active Planner's statewide fund form through Streamlit AppTest."""

from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

from src.projections import preferredProjectionYear

repoRoot = Path(__file__).resolve().parents[1]


class AllocationUiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.appTest = AppTest.from_file(str(repoRoot / "app.py")).run(timeout=30)
        self.appTest.switch_page("web/pages/3_planner.py").run(timeout=30)
        self.assertEqual(len(self.appTest.exception), 0)

    def testNextYearIsDefaultAnd2027LossReachesTheFund(self) -> None:
        expectedYear = preferredProjectionYear(2026, 2030)
        countyYear = next(widget for widget in self.appTest.selectbox if widget.label == "Year")
        fundYear = next(widget for widget in self.appTest.selectbox if widget.label == "Fund scenario year")
        self.assertEqual(countyYear.value, expectedYear)
        self.assertEqual(fundYear.value, expectedYear)
        countyYear.select(2027).run(timeout=30)
        self.assertEqual(len(self.appTest.exception), 0)
        centralLoss = next(metric for metric in self.appTest.metric if metric.label == "Central loss estimate")
        self.assertNotEqual(centralLoss.value, "No data")
        next(widget for widget in self.appTest.selectbox if widget.label == "Fund scenario year").select(2027)
        self.appTest.button[0].click().run(timeout=30)
        self.assertEqual(len(self.appTest.exception), 0)
        result = self.appTest.session_state["stateFundPlan"]
        self.assertEqual(result["inputs"]["year"], 2027)
        self.assertEqual(set(result["countyCropTable"]["year"]), {2027})
        self.assertEqual(result["summary"]["allocatedUsd"], 10_000_000)

    def testSubmitAllStatesThroughActiveNavigation(self) -> None:
        for state in ("IA", "NE", "CA", "DE"):
            with self.subTest(state=state):
                next(widget for widget in self.appTest.selectbox if widget.label == "Fund state").select(state)
                next(widget for widget in self.appTest.number_input if widget.label == "State fund ($)").set_value(100.01)
                self.appTest.button[0].click().run(timeout=30)
                self.assertEqual(len(self.appTest.exception), 0)
                self.assertEqual(len(self.appTest.error), 0)
                result = self.appTest.session_state["stateFundPlan"]
                self.assertEqual(set(result["countyCropTable"]["state"]), {state})
                self.assertEqual(set(result["countyCropTable"]["crop"]), {"CORN", "SOYBEANS", "WHEAT", "SORGHUM"})
                self.assertEqual(result["summary"]["allocatedUsd"], 100.01)
                self.assertGreater(len(self.appTest.dataframe), 2)

    def testCropDetailFilterPreservesAllCropWeights(self) -> None:
        self.appTest.button[0].click().run(timeout=30)
        originalResult = self.appTest.session_state["stateFundPlan"]
        originalCents = originalResult["countyCropTable"]["allocationCents"].tolist()
        next(widget for widget in self.appTest.selectbox if widget.label == "Show crop detail").select("WHEAT").run(timeout=30)
        self.assertEqual(len(self.appTest.exception), 0)
        self.assertEqual(self.appTest.session_state["stateFundPlan"]["countyCropTable"]["allocationCents"].tolist(), originalCents)
        self.assertEqual(self.appTest.dataframe[-1].value["crop"].unique().tolist(), ["Winter wheat"])

    def testZeroPriceScenarioLeavesFundUnallocatedAndCanBeRecomputed(self) -> None:
        for widget in self.appTest.number_input:
            if widget.label in ("Corn", "Soybeans", "Winter wheat", "Sorghum"):
                widget.set_value(0.0)
        self.appTest.button[0].click().run(timeout=30)
        self.assertEqual(len(self.appTest.exception), 0)
        result = self.appTest.session_state["stateFundPlan"]
        self.assertEqual(result["summary"]["allocatedUsd"], 0)
        self.assertEqual(result["summary"]["unallocatedUsd"], 10_000_000)
        next(widget for widget in self.appTest.number_input if widget.label == "Corn").set_value(4.0)
        self.appTest.button[0].click().run(timeout=30)
        self.assertEqual(len(self.appTest.exception), 0)
        self.assertEqual(self.appTest.session_state["stateFundPlan"]["summary"]["allocatedUsd"], 10_000_000)


if __name__ == "__main__":
    unittest.main()
