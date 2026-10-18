"""Fit Lane 2 deployment artifacts once, outside the Streamlit request path.

Run from the repository root with ``python app/model/build_artifacts.py``. The
official testing input directory is ignored by Git in this checkout. When it is
absent, rebuild its August 15 feature rows from the checked-in source panels
and join only the saved official test predictions for exposure and labels.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

modelDir = Path(__file__).resolve().parent
repoRoot = modelDir.parents[1]
sys.path.insert(0, str(modelDir))
sys.path.insert(0, str(repoRoot))

from analog import Analog  # noqa: E402
from data import CATEGORY, DROUGHT, FEATURES, KEY, NUMERIC, RESULTS, T1, T2, WEATHER, load_usable, usable  # noqa: E402
from tweedie import Tweedie  # noqa: E402

artifactDir = modelDir / "artifacts"
sourcePath = artifactDir / "scenario_inputs.parquet"
referencePath = RESULTS / "test_state_years.csv"
testPredictionPath = RESULTS / "test_predictions.csv"


def loadOfficialTestPredictions() -> pd.DataFrame:
    """Load the frozen official test output as a reference and label source."""
    if not testPredictionPath.exists():
        raise FileNotFoundError(f"Official test predictions are required: {testPredictionPath}")
    testPredictions = pd.read_csv(testPredictionPath, dtype={"fips": str})
    requiredColumns = set(KEY + ["state_alpha", "county_name", "liability", "insured_acres",
                                 "avg_coverage", "full_crop_value", "t1_actual", "t2_actual", "t1_D", "t2_D"])
    missingColumns = requiredColumns.difference(testPredictions.columns)
    if missingColumns:
        raise ValueError(f"Official test predictions are missing {sorted(missingColumns)}")
    if testPredictions.duplicated(KEY).any():
        raise ValueError("Official test predictions contain duplicate county-crop-years")
    return testPredictions


def rebuildDecisionInputs() -> pd.DataFrame:
    """Recreate August 15 rows with the same organizer function used originally."""
    from organize_usda_data import build_inputs

    return build_inputs(repoRoot)


def joinTestInputs(testPredictions: pd.DataFrame, decisionInputs: pd.DataFrame) -> pd.DataFrame:
    """Pair recreated inputs with the official test's observed RMA exposures."""
    testInputs = decisionInputs.loc[decisionInputs["year"].between(2016, 2025)].copy()
    carryColumns = KEY + ["liability", "insured_acres", "avg_coverage", "full_crop_value",
                          "t1_actual", "t2_actual"]
    testRows = testPredictions[carryColumns].merge(testInputs, on=KEY, how="left", validate="one_to_one",
                                                    indicator=True)
    if not testRows["_merge"].eq("both").all():
        raise ValueError("Could not recreate all official test feature rows")
    testRows = testRows.drop(columns="_merge")
    if testRows[FEATURES[:-len(CATEGORY)]].isna().all(axis=1).any():
        raise ValueError("A recreated test row has no model features")
    testRows["is_soybeans"] = testRows["crop"].eq("SOYBEANS").astype(int)
    testRows["is_ne"] = testRows["state_alpha"].eq("NE").astype(int)
    testRows[T1] = testRows["t1_actual"]
    testRows[T2] = testRows["t2_actual"]
    testRows["insured"] = True
    testRows["rma_year_available"] = True
    return testRows


def fitBundle(trainRows: pd.DataFrame, trainingYears: str) -> dict:
    """Fit D and C on exactly the rows supplied, without changing settings."""
    dModels = {target: Tweedie(alpha=0.001).fit(trainRows, target) for target in (T1, T2)}
    cModels = {target: Analog(k=25, drought_weight=1.0).fit(trainRows, target)
               for target in (T1, T2)}
    bounds = trainRows[FEATURES].agg(["min", "max"])
    return {"model": "D", "training_years": trainingYears, "d_models": dModels,
            "c_models": cModels, "feature_order": list(FEATURES),
            "drought_features": list(DROUGHT), "weather_features": list(WEATHER),
            "numeric_features": list(NUMERIC), "feature_bounds": bounds,
            "settings": {"D": {"alpha": 0.001, "power": 1.5},
                         "C": {"k": 25, "drought_weight": 1.0}}}


def officialStateYears(testPredictions: pd.DataFrame) -> pd.DataFrame:
    """Produce the missing state-year reference from saved official predictions."""
    reference = testPredictions.assign(
        d_x_payout_usd=testPredictions["t1_D"] * testPredictions["liability"],
        actual_x_payout_usd=testPredictions["t1_actual"] * testPredictions["liability"],
    ).groupby(["state_alpha", "year"], as_index=False)[["d_x_payout_usd", "actual_x_payout_usd"]].sum()
    return reference.sort_values(["state_alpha", "year"]).reset_index(drop=True)


def verifyOfficialTest(bundle: dict, testRows: pd.DataFrame, testPredictions: pd.DataFrame) -> dict:
    """Check the recreated D fit against saved 2023 IA and 2022 NE dollars."""
    reference = officialStateYears(testPredictions)
    reference.to_csv(referencePath, index=False)
    predictedShares = bundle["d_models"][T1].predict(testRows)
    predicted = testRows.assign(d_x_payout_usd=predictedShares * testRows["liability"])
    actualTotals = predicted.groupby(["state_alpha", "year"], as_index=False)["d_x_payout_usd"].sum()
    checks = actualTotals.merge(reference, on=["state_alpha", "year"], suffixes=("_artifact", "_official"),
                                validate="one_to_one")
    checked = {}
    for state, year in (("IA", 2023), ("NE", 2022)):
        row = checks.loc[checks["state_alpha"].eq(state) & checks["year"].eq(year)]
        if len(row) != 1:
            raise ValueError(f"Missing official reference for {state} {year}")
        difference = abs(float(row["d_x_payout_usd_artifact"].iloc[0] - row["d_x_payout_usd_official"].iloc[0]))
        if not np.isfinite(difference) or difference >= 1.0:
            raise AssertionError(f"D artifact differs from official {state} {year} by ${difference:,.2f}")
        checked[f"{state} {year}"] = difference
    return checked


def saveScenarioInputs(decisionInputs: pd.DataFrame, trainRows: pd.DataFrame,
                       testRows: pd.DataFrame) -> None:
    """Save a small, read-only inference table with exposures and no labels."""
    inputColumns = list(dict.fromkeys(KEY + ["county_name", "state_alpha", "decision_date", "liability",
                                               "insured_acres", "avg_coverage", "full_crop_value"] +
                                       list(FEATURES) + ["precip_mm", "precip_normal_prior", "irr_share_year"]))
    historical = pd.concat([trainRows, testRows], ignore_index=True)
    if historical.duplicated(KEY).any():
        raise ValueError("Historical exposure rows contain duplicate keys")
    inferenceRows = decisionInputs.merge(historical[KEY + ["liability", "insured_acres", "avg_coverage",
                                                           "full_crop_value"]], on=KEY, how="left", validate="one_to_one")
    inferenceRows["is_soybeans"] = inferenceRows["crop"].eq("SOYBEANS").astype(int)
    inferenceRows["is_ne"] = inferenceRows["state_alpha"].eq("NE").astype(int)
    inferenceRows[inputColumns].to_parquet(sourcePath, index=False)


def main() -> None:
    artifactDir.mkdir(parents=True, exist_ok=True)
    testPredictions = loadOfficialTestPredictions()
    decisionInputs = rebuildDecisionInputs()
    testRows = joinTestInputs(testPredictions, decisionInputs)
    trainRows = load_usable("training", "validation")
    if not trainRows["year"].between(2000, 2015).all():
        raise ValueError("The official test fit must use only 2000–2015")
    testBundle = fitBundle(trainRows, "2000-2015")
    checked = verifyOfficialTest(testBundle, testRows, testPredictions)
    joblib.dump(testBundle, artifactDir / "d_test.joblib", compress=3)

    fullRows = pd.concat([trainRows, usable(testRows)], ignore_index=True)
    if len(fullRows) != len(trainRows) + len(testPredictions):
        raise ValueError("Full-fit row count does not match the official test rows")
    fullBundle = fitBundle(fullRows, "2000-2025")
    joblib.dump(fullBundle, artifactDir / "d_full.joblib", compress=3)
    saveScenarioInputs(decisionInputs, trainRows, testRows)

    metadata = {"official_reference": str(referencePath.relative_to(repoRoot)),
                "reference_provenance": "Aggregated from saved results/test_predictions.csv",
                "state_year_differences_usd": checked, "test_fit_rows": len(trainRows),
                "full_fit_rows": len(fullRows), "inference_rows": len(pd.read_parquet(sourcePath))}
    (artifactDir / "build_report.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
