"""Verify the county Planner's year selection and displayed crop-loss amounts."""

from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

from web.scenario_lookup import scenario


repoRoot = Path(__file__).resolve().parents[1]


class PlannerUiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.appTest = AppTest.from_file(str(repoRoot / "app.py")).run(timeout=30)
        self.appTest.switch_page("web/pages/3_planner.py").run(timeout=30)
        self.assertFalse(self.appTest.exception)

    def testDefaultYearAndLabelsAreConsistentWithoutFundControls(self) -> None:
        yearControl = next(widget for widget in self.appTest.selectbox if widget.label == "Year")
        self.assertEqual(yearControl.value, 2026)
        self.assertEqual(yearControl.options, [f"{year} (projected)" for year in range(2026, 2031)])
        self.assertEqual(len(self.appTest.number_input), 1)
        self.assertFalse(any(heading.value == "Allocate a state fund" for heading in self.appTest.subheader))
        self.assertFalse(any("fund" in button.label.lower() for button in self.appTest.button))

    def testChangingYearRecalculatesDisplayedLoss(self) -> None:
        yearControl = next(widget for widget in self.appTest.selectbox if widget.label == "Year")
        for year in (2026, 2027, 2030):
            with self.subTest(year=year):
                yearControl.select(year).run(timeout=30)
                self.assertFalse(self.appTest.exception)
                county = next(widget.value for widget in self.appTest.selectbox if widget.label == "County")
                crop = next(widget.value for widget in self.appTest.selectbox if widget.label == "Crop")
                price = self.appTest.number_input[0].value
                result = scenario(county, crop, year, "D2", price)
                self.assertTrue(result["confident"])
                metric = next(metric for metric in self.appTest.metric if metric.label == "Central loss estimate")
                self.assertEqual(metric.value, f"${result['dollars'](result['mid']):,.0f}")
                yearControl = next(widget for widget in self.appTest.selectbox if widget.label == "Year")


if __name__ == "__main__":
    unittest.main()
