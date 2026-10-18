"""Tests for the statewide-X planning band (exploratory, DECISIONS.md Entry 9).

Run: python -m unittest tests.test_ratio_band   (pytest also works)
"""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import reserve_band as engine  # noqa: E402

_spec = importlib.util.spec_from_file_location("ratio_band", ROOT / "app" / "model" / "ratio_band.py")
ratio_band = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ratio_band)


class RatioBandTests(unittest.TestCase):
    def test_source_years_not_after_2015(self):
        self.assertLessEqual(max(engine.load_ratio_band()["source_years"]), 2015)

    def test_band_brackets_one(self):
        b = engine.load_ratio_band()
        self.assertLess(b["q05"], 1)
        self.assertGreater(b["q95"], 1)

    def test_high_is_x_times_q95_and_low_is_x_times_q05(self):
        b, x = engine.load_ratio_band(), 123_456_789.0
        r = engine.reserve_band_x_usd(x)
        self.assertEqual(r["high_usd"], x * b["q95"])
        self.assertEqual(r["low_usd"], x * b["q05"])
        self.assertEqual(r["plan_usd"], x)
        self.assertEqual(r["label"], b["label"])
        self.assertEqual(r["source_years"], "2006-2015")

    def test_band_scales_with_acres_and_price(self):
        x, acres_scale, price_scale = 80_000_000.0, 1.25, 0.9
        k = acres_scale * price_scale
        base, scaled = engine.reserve_band_x_usd(x), engine.reserve_band_x_usd(x * acres_scale * price_scale)
        self.assertAlmostEqual(scaled["high_usd"], base["high_usd"] * k, places=3)
        self.assertAlmostEqual(scaled["low_usd"], base["low_usd"] * k, places=3)

    def test_missing_json_message(self):
        engine.load_ratio_band.cache_clear()
        saved = engine._BAND_PATH
        try:
            engine._BAND_PATH = Path(tempfile.mkdtemp()) / "ratio_band.json"
            with self.assertRaisesRegex(FileNotFoundError, "run python app/model/ratio_band.py"):
                engine.load_ratio_band()
        finally:
            engine._BAND_PATH = saved
            engine.load_ratio_band.cache_clear()

    def test_ratio_band_refuses_a_2016_plus_year(self):
        df = pd.read_csv(ROOT / "app" / "model" / "results" / "oos_predictions.csv", dtype={"fips": str})
        ratio_band.compute_band(df)  # the real input is accepted
        bad = df.copy()
        bad.loc[bad.index[0], "year"] = 2016
        with self.assertRaisesRegex(AssertionError, "outside 2006..2015"):
            ratio_band.compute_band(bad)


if __name__ == "__main__":
    unittest.main()
