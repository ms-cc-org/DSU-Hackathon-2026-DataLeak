"""Cached Lane 2 prediction contract over fitted insurance-loss models.

X is estimated insurance payouts; Y is estimated deductible exposure; Z is an
illustrative relief allocation under a 95% coverage assumption.
"""

from __future__ import annotations

import importlib
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Sequence

import joblib
import numpy as np
import pandas as pd

repoRoot = Path(__file__).resolve().parents[1]
modelDir = repoRoot / "app" / "model"
artifactDir = modelDir / "artifacts"
moneyColumns = ("X_payout_usd", "Y_deductible_exposure_usd", "Z_relief_95pct_usd")
modelName = Literal["full", "test"]


def _modelModule(moduleName: str) -> Any:
    """Register existing script-style model modules before unpickling."""
    if str(modelDir) not in sys.path:
        sys.path.insert(0, str(modelDir))
    return importlib.import_module(moduleName)


@lru_cache(maxsize=2)
def _loadArtifact(model: modelName) -> dict[str, Any]:
    if model not in ("full", "test"):
        raise ValueError("model must be 'full' or 'test'")
    artifactPath = artifactDir / f"d_{model}.joblib"
    if not artifactPath.exists():
        raise FileNotFoundError(f"Missing {artifactPath}; run python app/model/build_artifacts.py")
    _modelModule("tweedie")
    _modelModule("analog")
    bundle = joblib.load(artifactPath)
    if bundle.get("model") != "D" or not bundle.get("feature_order"):
        raise ValueError(f"Invalid D artifact: {artifactPath}")
    return bundle


@lru_cache(maxsize=1)
def _loadScenarioInputs() -> pd.DataFrame:
    inputPath = artifactDir / "scenario_inputs.parquet"
    if not inputPath.exists():
        raise FileNotFoundError(f"Missing {inputPath}; run python app/model/build_artifacts.py")
    return pd.read_parquet(inputPath)


def _prepareFeatures(features_df: pd.DataFrame, bundle: dict[str, Any]) -> pd.DataFrame:
    if not isinstance(features_df, pd.DataFrame) or features_df.empty:
        raise ValueError("features_df must be a non-empty pandas DataFrame")
    frame = features_df.copy()
    if "county_name" not in frame and "county" in frame:
        frame["county_name"] = frame["county"]
    if "state_alpha" not in frame and "state" in frame:
        frame["state_alpha"] = frame["state"]
    requiredColumns = {"fips", "county_name", "state_alpha", "crop", "year", "liability",
                       "insured_acres", "avg_coverage"}.union(bundle["feature_order"])
    missingColumns = requiredColumns.difference(frame.columns)
    if missingColumns:
        raise ValueError(f"Missing prediction columns: {sorted(missingColumns)}")
    frame["fips"] = frame["fips"].astype("string").str.zfill(5)
    if frame["fips"].isna().any() or not frame["fips"].str.fullmatch(r"\d{5}").all():
        raise ValueError("fips must be a five-character county code")
    if frame.duplicated(["fips", "crop", "year"]).any():
        raise ValueError("Duplicate county-crop-year rows are not allowed")
    for columnName in ("liability", "insured_acres", "avg_coverage"):
        frame[columnName] = pd.to_numeric(frame[columnName], errors="coerce")
    exposures = frame[["liability", "insured_acres", "avg_coverage"]].to_numpy(float)
    if not np.isfinite(exposures).all() or (frame["liability"] <= 0).any() or (frame["insured_acres"] <= 0).any():
        raise ValueError("Each row needs positive, finite insured liability and acres")
    if (frame["avg_coverage"] <= 0).any() or (frame["avg_coverage"] > 1).any():
        raise ValueError("avg_coverage must be in (0, 1]")
    if "full_crop_value" not in frame:
        frame["full_crop_value"] = frame["liability"] / frame["avg_coverage"]
    frame["full_crop_value"] = pd.to_numeric(frame["full_crop_value"], errors="coerce")
    if not np.isfinite(frame["full_crop_value"].to_numpy(float)).all() or (frame["full_crop_value"] <= 0).any():
        raise ValueError("full_crop_value must be positive and finite")
    return frame.reset_index(drop=True)


def _rangeFlags(frame: pd.DataFrame, bundle: dict[str, Any]) -> list[list[str]]:
    bounds = bundle["feature_bounds"]
    features = bundle["feature_order"]
    values = frame[features].apply(pd.to_numeric, errors="coerce")
    beyond = values.lt(bounds.loc["min", features], axis=1) | values.gt(bounds.loc["max", features], axis=1)
    return [list(beyond.columns[row.to_numpy()]) for _, row in beyond.iterrows()]


def predict(features_df: pd.DataFrame, model: modelName = "full") -> pd.DataFrame:
    """Return county-crop D shares, X/Y/Z dollars, and training-range flags."""
    bundle = _loadArtifact(model)
    frame = _prepareFeatures(features_df, bundle)
    budgetModule = _modelModule("budget")
    payoutShares = bundle["d_models"]["drought_payout_share"].predict(frame)
    damageShares = bundle["d_models"]["drought_loss_acre_share"].predict(frame)
    components = budgetModule.budget_components(frame, payoutShares, damageShares)
    flags = _rangeFlags(frame, bundle)
    result = frame[["fips", "county_name", "state_alpha", "crop", "year", "liability",
                    "insured_acres", "avg_coverage"]].rename(
                        columns={"county_name": "county", "state_alpha": "state"}).copy()
    result["pred_payout_share"] = payoutShares
    result["pred_damaged_acre_share"] = damageShares
    result["X_payout_usd"] = components["insurance_pays"].to_numpy()
    result["Y_deductible_exposure_usd"] = components["out_of_pocket"].to_numpy()
    result["Z_relief_95pct_usd"] = components["relief_need"].to_numpy()
    result["out_of_range"] = [bool(names) for names in flags]
    result["out_of_range_features"] = flags
    return result


def _applyFootprint(baseRows: pd.DataFrame, footprintRows: pd.DataFrame,
                    selectedCounties: set[str], climateColumns: list[str]) -> pd.DataFrame:
    if not selectedCounties:
        return baseRows.copy()
    if footprintRows.duplicated("fips").any():
        raise ValueError("Footprint has duplicate county rows")
    missingCounties = selectedCounties.difference(set(footprintRows["fips"]))
    if missingCounties:
        raise ValueError(f"Footprint lacks counties {sorted(missingCounties)}")
    result = baseRows.copy().set_index("fips")
    replacement = footprintRows.set_index("fips")
    orderedCounties = sorted(selectedCounties)
    result.loc[orderedCounties, climateColumns] = replacement.loc[orderedCounties, climateColumns].to_numpy()
    return result.reset_index()


def _closestYears(frame: pd.DataFrame, analogModel: Any) -> list[dict[str, Any]]:
    """Aggregate C neighbor distance over the current county footprint."""
    scores: Counter[int] = Counter()
    matches: Counter[int] = Counter()
    for cropName, (neighbors, _, _, metadata) in analogModel.pool_.items():
        cropRows = frame.loc[frame["crop"].eq(cropName)]
        if cropRows.empty:
            continue
        distances, positions = neighbors.kneighbors(analogModel._z(cropRows), return_distance=True)
        for rowNumber, sourceRow in enumerate(cropRows.itertuples()):
            for distance, position in zip(distances[rowNumber], positions[rowNumber]):
                historicalYear = int(metadata.iloc[position]["year"])
                scores[historicalYear] += float(sourceRow.liability) / (1.0 + float(distance))
                matches[historicalYear] += 1
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:3]
    return [{"year": year, "proximity_score": score, "neighbor_matches": matches[year]}
            for year, score in ranked]


def _outOfRangeSummary(table: pd.DataFrame) -> dict[str, Any]:
    counts = Counter(featureName for names in table["out_of_range_features"] for featureName in names)
    return {"county_crop_rows_flagged": int(table["out_of_range"].sum()),
            "total_county_crop_rows": len(table), "feature_counts": dict(counts)}


def scenario(base_year: int, footprint_year: int, state: str = "IA", crop: str = "CORN",
             counties: Sequence[str] | None = None, acres_scale: float = 1.0,
             price_scale: float = 1.0) -> dict[str, Any]:
    """Replace modeled drought/weather features and scale only dollar outputs."""
    if not np.isfinite([acres_scale, price_scale]).all() or acres_scale <= 0 or price_scale <= 0:
        raise ValueError("acres_scale and price_scale must be positive finite numbers")
    bundle = _loadArtifact("full")
    inputs = _loadScenarioInputs()
    baseRows = inputs.loc[inputs["year"].eq(base_year) & inputs["state_alpha"].eq(state) &
                          inputs["crop"].eq(crop) & inputs["liability"].gt(0) &
                          inputs["insured_acres"].gt(0)].copy()
    if baseRows.empty:
        raise ValueError(f"No insured base-year rows for {state} {crop} {base_year}")
    availableCounties = set(baseRows["fips"])
    selectedCounties = availableCounties if counties is None else {str(fips).zfill(5) for fips in counties}
    unknownCounties = selectedCounties.difference(availableCounties)
    if unknownCounties:
        raise ValueError(f"Counties outside insured base-year rows: {sorted(unknownCounties)}")
    footprintRows = inputs.loc[inputs["year"].eq(footprint_year) & inputs["state_alpha"].eq(state) &
                               inputs["crop"].eq(crop) & inputs["fips"].isin(selectedCounties)]
    climateColumns = bundle["drought_features"] + bundle["weather_features"]
    scenarioRows = _applyFootprint(baseRows, footprintRows, selectedCounties, climateColumns)
    countyTable = predict(scenarioRows, model="full")
    scale = float(acres_scale * price_scale)
    countyTable.loc[:, list(moneyColumns)] *= scale
    totals = {columnName: float(countyTable[columnName].sum()) for columnName in moneyColumns}
    budgetModule = _modelModule("budget")
    analogModel = bundle["c_models"]["drought_payout_share"]
    rawPredictions = bundle["d_models"]["drought_payout_share"].predict(scenarioRows)
    rangeResult = budgetModule.statewide_range(scenarioRows, analog=analogModel,
                                               preds={"D": rawPredictions}, point_model="D")
    lowValue, highValue = rangeResult["range"][state]
    historicalRange = {"low_usd": float(lowValue * scale), "high_usd": float(highValue * scale),
                       "method": "C historical neighbors, widened to include D point",
                       "label": rangeResult["label"], "widened": bool(rangeResult["widened"][state])}
    return {"county_table": countyTable, "statewide_totals": totals,
            "historical_scenario_range_x_usd": historicalRange,
            "closest_historical_years": _closestYears(scenarioRows, analogModel),
            "out_of_range_summary": _outOfRangeSummary(countyTable), "model": "full",
            "base_year": base_year, "footprint_year": footprint_year, "state": state, "crop": crop,
            "footprint_counties": sorted(selectedCounties),
            "acres_scale": acres_scale, "price_scale": price_scale}


def replay(year: int) -> dict[str, Any]:
    """Replay 2016–2025 out of sample; label earlier full-fit years in sample."""
    if year < 2000 or year > 2025:
        raise ValueError("replay year must be between 2000 and 2025")
    inputs = _loadScenarioInputs()
    rows = inputs.loc[inputs["year"].eq(year) & inputs["liability"].gt(0) &
                      inputs["insured_acres"].gt(0)].copy()
    selectedModel: modelName = "test" if year >= 2016 else "full"
    countyTable = predict(rows, model=selectedModel)
    stateTotals = countyTable.groupby("state", as_index=False)[list(moneyColumns)].sum()
    return {"county_table": countyTable, "statewide_totals": stateTotals,
            "model": selectedModel, "evaluation_label": "out-of-sample" if year >= 2016 else "in-sample",
            "year": year, "out_of_range_summary": _outOfRangeSummary(countyTable)}
