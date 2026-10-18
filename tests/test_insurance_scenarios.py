"""Verify actual model inference, input provenance and future insurance arithmetic."""

from io import StringIO
import unittest

import numpy as np
import pandas as pd

from src.engine import _loadArtifact, _loadScenarioInputs, scenario
from src.insurance_scenarios import (exposureRows, historicalInsuranceScenario, insuranceAnalogContext,
                                      projectInsurance, replayInsurance, substituteClimate)
from web.insurance_ui import exportTable
from web.insurance_data import runInsurance


class InsuranceScenarioTests(unittest.TestCase):
    def testSelectedCropOutputsMatchFrozenModelsAndDollarFormulasInEveryMode(self) -> None:
        moneyColumns = ["X_payout_usd", "Y_deductible_exposure_usd", "Z_relief_95pct_usd"]
        predictionColumns = ["pred_payout_share", "pred_damaged_acre_share", *moneyColumns, "predDamagedAcres"]
        for mode in ("Future insurance scenario", "Historical footprint scenario", "Historical replay"):
            for state in ("IA", "NE"):
                for crop in ("ALL", "CORN", "SOYBEANS"):
                    with self.subTest(mode=mode, state=state, crop=crop):
                        inputs = {"mode": mode, "state": state, "crop": crop,
                                  "year": 2026 if mode == "Future insurance scenario" else 2023,
                                  "baseYear": 2025 if mode == "Future insurance scenario" else 2023,
                                  "footprint": "ALL" if mode == "Future insurance scenario" else 2012,
                                  "acresScale": 1.7, "priceScale": 1.3}
                        result = runInsurance(inputs)
                        selectedCrops = {"CORN", "SOYBEANS"} if crop == "ALL" else {crop}
                        self.assertEqual(set(result["countyTable"]["crop"]), selectedCrops)
                        self.assertEqual(set(result["modelInputs"]["crop"]), selectedCrops)
                        self.assertEqual(set(result["metadata"]["crops"]), selectedCrops)
                        self.assertEqual(result["metadata"]["selection"], inputs)
                        modelName = "test" if mode == "Historical replay" else "full"
                        models = _loadArtifact(modelName)["d_models"]
                        acresScale = 1.0 if mode == "Historical replay" else inputs["acresScale"]
                        priceScale = 1.0 if mode == "Historical replay" else inputs["priceScale"]
                        dollarScale = acresScale * priceScale
                        expectedDraws = []
                        for footprintYear, rows in result["modelInputs"].groupby("footprintYear"):
                            expected = rows[["fips", "crop"]].copy()
                            payoutShares = models["drought_payout_share"].predict(rows)
                            damagedShares = models["drought_loss_acre_share"].predict(rows)
                            expected["pred_payout_share"] = payoutShares
                            expected["pred_damaged_acre_share"] = damagedShares
                            expected["X_payout_usd"] = payoutShares * rows["liability"].to_numpy() * dollarScale
                            expected["Y_deductible_exposure_usd"] = damagedShares * rows["full_crop_value"].to_numpy() * (1 - rows["avg_coverage"].to_numpy()) * dollarScale
                            expected["Z_relief_95pct_usd"] = damagedShares * rows["full_crop_value"].to_numpy() * np.maximum(0, 0.95 - rows["avg_coverage"].to_numpy()) * dollarScale
                            expected["predDamagedAcres"] = damagedShares * rows["insured_acres"].to_numpy() * acresScale
                            expectedDraws.append(expected)
                        expectedTable = pd.concat(expectedDraws).groupby(["fips", "crop"])[predictionColumns].mean()
                        actualTable = result["countyTable"].set_index(["fips", "crop"])[predictionColumns].sort_index()
                        np.testing.assert_allclose(actualTable, expectedTable, rtol=1e-11, atol=1e-7)
                        for columnName in moneyColumns:
                            self.assertAlmostEqual(result["totals"][columnName], expectedTable[columnName].sum(), places=5)
                        self.assertAlmostEqual(result["totals"]["payoutShare"], expectedTable["X_payout_usd"].sum() / result["countyTable"]["scenarioLiabilityUsd"].sum())
                        self.assertAlmostEqual(result["totals"]["damagedAcreShare"], expectedTable["predDamagedAcres"].sum() / result["countyTable"]["scenarioInsuredAcres"].sum())
                        exported = pd.read_csv(StringIO(exportTable(result["countyTable"]).decode()), dtype={"fips": str})
                        self.assertEqual(set(exported["crop"]), selectedCrops)
                        np.testing.assert_allclose(exported.set_index(["fips", "crop"])[predictionColumns].sort_index(), expectedTable, rtol=1e-11, atol=1e-7)

    def testFutureScenarioReproducesExistingModelDWithTheSameInputs(self) -> None:
        future = projectInsurance(2026, "IA", 2023, [2012], ["CORN"])
        original = scenario(2023, 2012)
        for columnName in ("X_payout_usd", "Y_deductible_exposure_usd", "Z_relief_95pct_usd"):
            self.assertAlmostEqual(future["totals"][columnName], original["statewide_totals"][columnName], places=5)
        self.assertEqual(future["metadata"]["modelArtifact"], "d_full.joblib")
        self.assertEqual(future["metadata"]["settings"], {"alpha": 0.001, "power": 1.5})
        self.assertEqual(set(future["countyTable"]["year"]), {2026})

    def testEveryClimateFeatureComesFromTheFootprintAndOthersStayAtBase(self) -> None:
        base = exposureRows("NE", 2025).set_index(["fips", "crop"])
        replaced = substituteClimate(base.reset_index(), 2012).set_index(["fips", "crop"])
        raw = _loadScenarioInputs()
        footprint = raw.loc[raw["year"].eq(2012)].set_index(["fips", "crop"])
        bundle = _loadArtifact("full")
        climateColumns = bundle["drought_features"] + bundle["weather_features"]
        pd.testing.assert_frame_equal(replaced[climateColumns], footprint.loc[base.index, climateColumns])
        otherColumns = [columnName for columnName in base if columnName not in climateColumns]
        pd.testing.assert_frame_equal(replaced[otherColumns], base[otherColumns])

    def testWholeSeasonEnsembleUsesStatewideDrawTotalsForItsRange(self) -> None:
        result = projectInsurance(2026, "IA", footprintYears=[2005, 2012, 2020])
        self.assertEqual(result["scenarioTotals"]["footprintYear"].tolist(), [2005, 2012, 2020])
        self.assertAlmostEqual(result["totals"]["X_payout_usd"], result["scenarioTotals"]["X_payout_usd"].mean(), places=5)
        self.assertEqual(result["range"]["lowUsd"], result["scenarioTotals"]["X_payout_usd"].quantile(0.1))
        countyKeys = ["fips", "crop"]
        expectedKeys = set(map(tuple, exposureRows("IA", 2025)[countyKeys].to_numpy()))
        for footprintYear, rows in result["drawTable"].groupby("footprintYear"):
            with self.subTest(footprintYear=footprintYear):
                self.assertEqual(set(map(tuple, rows[countyKeys].to_numpy())), expectedKeys)

    def testScalingChangesDollarsAndExposuresButNotLearnedShares(self) -> None:
        base = projectInsurance(2026, footprintYears=[2012])
        acres = projectInsurance(2026, footprintYears=[2012], acresScale=2)
        price = projectInsurance(2026, footprintYears=[2012], priceScale=2)
        for scaled in (acres, price):
            pd.testing.assert_series_equal(base["countyTable"]["pred_payout_share"], scaled["countyTable"]["pred_payout_share"])
            pd.testing.assert_series_equal(base["countyTable"]["pred_damaged_acre_share"], scaled["countyTable"]["pred_damaged_acre_share"])
            self.assertEqual(scaled["totals"]["X_payout_usd"], base["totals"]["X_payout_usd"] * 2)
        self.assertEqual(acres["totals"]["scenarioInsuredAcres"], base["totals"]["scenarioInsuredAcres"] * 2)
        self.assertEqual(price["totals"]["predDamagedAcres"], base["totals"]["predDamagedAcres"])

    def testChangingYearAloneDoesNotInventNewModelFeatures(self) -> None:
        first = projectInsurance(2026, footprintYears=[2012])
        second = projectInsurance(2027, footprintYears=[2012])
        self.assertEqual(first["totals"], second["totals"])
        self.assertEqual(set(second["modelInputs"]["year"]), {2027})

    def testHistoricalReplayReproducesSavedStateTotalsAndUsesTestArtifact(self) -> None:
        reference = pd.read_csv("app/model/results/test_state_years.csv")
        for state, year in (("IA", 2023), ("NE", 2022)):
            result = replayInsurance(year, state)
            expected = reference.loc[reference["state_alpha"].eq(state) & reference["year"].eq(year), "d_x_payout_usd"].iloc[0]
            with self.subTest(state=state):
                self.assertLess(abs(result["totals"]["X_payout_usd"] - expected), 1)
                self.assertEqual(result["metadata"]["modelArtifact"], "d_test.joblib")
                self.assertEqual(result["metadata"]["evaluationLabel"], "out-of-sample")
        self.assertEqual(replayInsurance(2012)["metadata"]["evaluationLabel"], "in-sample")

    def testHistoricalFootprintModeUsesFullModelAndLabelsTheWhatIf(self) -> None:
        result = historicalInsuranceScenario(2023, 2012, crops=["CORN"])
        original = scenario(2023, 2012)
        self.assertAlmostEqual(result["totals"]["X_payout_usd"], original["statewide_totals"]["X_payout_usd"], places=5)
        self.assertEqual(set(result["countyTable"]["year"]), {2023})
        self.assertIn("In-sample", result["metadata"]["evaluationLabel"])
        context = insuranceAnalogContext(result["modelInputs"], "full")
        self.assertEqual(len(context["closestYears"]), 3)
        self.assertLessEqual(context["lowUsd"], result["totals"]["X_payout_usd"])
        self.assertGreaterEqual(context["highUsd"], result["totals"]["X_payout_usd"])

    def testUnsupportedScopeAndInvalidScenarioInputsAreRejected(self) -> None:
        for arguments in ({"state": "CA"}, {"crops": ["WHEAT"]}, {"footprintYears": [2031]},
                          {"footprintYears": []}, {"footprintYears": [2012, 2012]}, {"acresScale": 0},
                          {"priceScale": float("nan")}):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                projectInsurance(2026, **arguments)
        with self.assertRaises(ValueError):
            projectInsurance(2031)

    def testPredictionExportsIdentifyModelTargetsAndAssumedInputs(self) -> None:
        result = projectInsurance(2026, footprintYears=[2012])
        predictions = pd.read_csv(StringIO(exportTable(result["countyTable"]).decode()), dtype={"fips": str})
        self.assertTrue(predictions["predictionSource"].str.contains("Model D").all())
        self.assertEqual(set(predictions["modelArtifact"]), {"d_full.joblib"})
        self.assertEqual(set(predictions["exposureBaseYear"]), {2025})
        self.assertTrue(predictions["pred_payout_share"].between(0, 1).all())
        self.assertTrue(np.isfinite(predictions["X_payout_usd"]).all())
        self.assertEqual(result["metadata"]["predictedQuantities"], ["payout share", "damaged-acre share"])
        self.assertNotIn("drought_indemnity", result["modelInputs"])


if __name__ == "__main__":
    unittest.main()
