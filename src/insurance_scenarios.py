"""Auditable future insurance scenarios over the unchanged fitted model D."""

from collections.abc import Sequence

import numpy as np
import pandas as pd

from src.engine import _closestYears, _loadArtifact, _loadScenarioInputs, _modelModule, moneyColumns, predict, replay


insuranceStates = {"IA": "Iowa", "NE": "Nebraska"}
insuranceCrops = ("CORN", "SOYBEANS")


def insuranceInventory() -> dict:
    """Describe the saved inputs and fitted model without fitting anything."""
    inputs = _loadScenarioInputs()
    bundle = _loadArtifact("full")
    return {
        "firstYear": int(inputs["year"].min()), "lastYear": int(inputs["year"].max()),
        "trainingYears": bundle["training_years"], "featureOrder": bundle["feature_order"],
        "settings": bundle["settings"]["D"],
    }


def exposureRows(state: str, baseYear: int, crops: Sequence[str] | None = None) -> pd.DataFrame:
    """Select supported, positive insured exposure; absent coverage is never zero loss."""
    if state not in insuranceStates:
        raise ValueError("Model D supports Iowa and Nebraska only.")
    selectedCrops = tuple(insuranceCrops if crops is None else crops)
    if not selectedCrops or len(set(selectedCrops)) != len(selectedCrops) or not set(selectedCrops).issubset(insuranceCrops):
        raise ValueError("Model D supports corn and soybeans only; select each crop once.")
    inputs = _loadScenarioInputs()
    rows = inputs.loc[inputs["state_alpha"].eq(state) & inputs["year"].eq(baseYear)
                      & inputs["crop"].isin(selectedCrops) & inputs["liability"].gt(0)
                      & inputs["insured_acres"].gt(0) & inputs["avg_coverage"].gt(0)].copy()
    if rows.empty:
        raise ValueError(f"No positive insured exposure for {state} in {baseYear}.")
    return rows.sort_values(["fips", "crop"]).reset_index(drop=True)


def substituteClimate(baseRows: pd.DataFrame, footprintYear: int) -> pd.DataFrame:
    """Reuse one complete season's spatial pattern across counties and both crops."""
    bundle = _loadArtifact("full")
    climateColumns = bundle["drought_features"] + bundle["weather_features"]
    keys = ["fips", "crop"]
    baseIndexed = baseRows.set_index(keys)
    inputs = _loadScenarioInputs()
    footprint = inputs.loc[inputs["year"].eq(footprintYear)].set_index(keys)
    absentKeys = baseIndexed.index.difference(footprint.index)
    if len(absentKeys):
        raise ValueError(f"Footprint {footprintYear} lacks {len(absentKeys)} insured county/crop combinations.")
    baseIndexed.loc[:, climateColumns] = footprint.loc[baseIndexed.index, climateColumns].to_numpy()
    return baseIndexed.reset_index()


def scaledPrediction(inputs: pd.DataFrame, model: str, acresScale: float, priceScale: float) -> pd.DataFrame:
    """Predict the two shares, then convert them using explicitly scaled insured exposure."""
    if not np.isfinite([acresScale, priceScale]).all() or acresScale <= 0 or priceScale <= 0:
        raise ValueError("Insured-acre and insured-value multipliers must be positive and finite.")
    table = predict(inputs, model=model)
    dollarScale = float(acresScale * priceScale)
    if not np.isfinite(dollarScale):
        raise ValueError("The combined insured exposure multiplier must be finite.")
    table.loc[:, list(moneyColumns)] *= dollarScale
    table["scenarioLiabilityUsd"] = table["liability"] * dollarScale
    table["scenarioInsuredAcres"] = table["insured_acres"] * acresScale
    table["scenarioFullCropValueUsd"] = inputs["full_crop_value"].to_numpy() * dollarScale
    table["predDamagedAcres"] = table["pred_damaged_acre_share"] * table["scenarioInsuredAcres"]
    return table


def summarizeInsurance(drawTable: pd.DataFrame, modelInputs: pd.DataFrame, metadata: dict) -> dict:
    """Average complete model runs; calculate spread from statewide totals per season."""
    keys = ["fips", "county", "state", "crop", "year"]
    numericColumns = ["pred_payout_share", "pred_damaged_acre_share", "liability", "insured_acres", "avg_coverage",
                      *moneyColumns, "scenarioLiabilityUsd", "scenarioInsuredAcres", "scenarioFullCropValueUsd",
                      "predDamagedAcres"]
    grouped = drawTable.groupby(keys, sort=True)
    countyTable = grouped[numericColumns].mean()
    countyTable["out_of_range"] = grouped["out_of_range"].any()
    countyTable["out_of_range_features"] = grouped["out_of_range_features"].agg(
        lambda featureLists: sorted({feature for names in featureLists for feature in names}))
    countyTable["flaggedScenarioShare"] = grouped["out_of_range"].mean()
    countyTable = countyTable.reset_index()
    countyTable["predictionSource"] = "Model D: Tweedie GLM, alpha 0.001, power 1.5, uncalibrated"
    for columnName in ("modelArtifact", "trainingYears", "runMode", "exposureBaseYear", "acresScale", "priceScale"):
        countyTable[columnName] = metadata[columnName]
    countyTable["footprintYears"] = ",".join(map(str, metadata["footprintYears"]))
    scenarioTotals = drawTable.groupby("footprintYear", as_index=False)[list(moneyColumns)].sum()
    totals = {columnName: float(countyTable[columnName].sum()) for columnName in moneyColumns}
    liabilityUsd = float(countyTable["scenarioLiabilityUsd"].sum())
    insuredAcres = float(countyTable["scenarioInsuredAcres"].sum())
    totals.update(
        payoutShare=totals["X_payout_usd"] / liabilityUsd,
        damagedAcreShare=float(countyTable["predDamagedAcres"].sum()) / insuredAcres,
        predDamagedAcres=float(countyTable["predDamagedAcres"].sum()),
        scenarioLiabilityUsd=liabilityUsd, scenarioInsuredAcres=insuredAcres,
    )
    return {
        "countyTable": countyTable, "drawTable": drawTable, "modelInputs": modelInputs,
        "scenarioTotals": scenarioTotals, "totals": totals, "metadata": metadata,
        "range": {"lowUsd": float(scenarioTotals["X_payout_usd"].quantile(0.1)),
                  "highUsd": float(scenarioTotals["X_payout_usd"].quantile(0.9))},
        "flaggedRows": int(countyTable["out_of_range"].sum()),
        "imputedInputRows": int(modelInputs["imputedFeatures"].map(bool).sum()),
    }


def projectInsurance(targetYear: int, state: str = "IA", baseYear: int | None = None,
                     footprintYears: Sequence[int] | None = None, crops: Sequence[str] | None = None,
                     acresScale: float = 1.0, priceScale: float = 1.0) -> dict:
    """Predict hypothetical future insurance outcomes from complete historical footprints.

    Every footprint is evaluated once with equal weight. This is a historical
    sensitivity ensemble, not a calibrated drought probability or weather forecast.
    The base year's insured values, soil, irrigation and history remain assumptions.
    """
    inventory = insuranceInventory()
    if targetYear not in range(inventory["lastYear"] + 1, 2031):
        raise ValueError(f"Future insurance scenarios support {inventory['lastYear'] + 1}-2030.")
    return evaluateFootprints(targetYear, state, baseYear, footprintYears, crops, acresScale, priceScale)


def evaluateFootprints(targetYear: int, state: str, baseYear: int | None,
                       footprintYears: Sequence[int] | None, crops: Sequence[str] | None,
                       acresScale: float, priceScale: float) -> dict:
    """Run the same fitted model for explicit future or historical scenario assumptions."""
    inventory = insuranceInventory()
    baseYear = inventory["lastYear"] if baseYear is None else baseYear
    baseRows = exposureRows(state, baseYear, crops)
    selectedYears = list(range(inventory["firstYear"], inventory["lastYear"] + 1)
                         if footprintYears is None else footprintYears)
    if not selectedYears or len(set(selectedYears)) != len(selectedYears):
        raise ValueError("Select at least one distinct historical footprint year.")
    if not set(selectedYears).issubset(range(inventory["firstYear"], inventory["lastYear"] + 1)):
        raise ValueError("Historical footprints must fall inside the saved input years.")
    featureOrder = inventory["featureOrder"]
    predictions, auditedInputs = [], []
    for footprintYear in sorted(selectedYears):
        inputs = substituteClimate(baseRows, footprintYear)
        inputs["year"] = targetYear
        inputs["decision_date"] = f"{targetYear}-08-15"
        table = scaledPrediction(inputs, "full", acresScale, priceScale)
        table["footprintYear"] = footprintYear
        predictions.append(table)
        inputs["footprintYear"] = footprintYear
        inputs["exposureBaseYear"] = baseYear
        inputs["imputedFeatures"] = inputs[featureOrder].isna().apply(
            lambda row: list(row.index[row]), axis=1)
        auditedInputs.append(inputs)
    metadata = {
        "runMode": "future historical-footprint scenario", "state": state, "targetYear": targetYear,
        "exposureBaseYear": baseYear, "footprintYears": sorted(selectedYears),
        "modelArtifact": "d_full.joblib", "trainingYears": inventory["trainingYears"],
        "evaluationLabel": "Hypothetical future scenario; no held-out accuracy claim",
        "acresScale": acresScale, "priceScale": priceScale, "featureOrder": featureOrder,
        "climateSource": "Historical August 15 drought and weather features",
        "settings": inventory["settings"], "predictedQuantities": ["payout share", "damaged-acre share"],
    }
    return summarizeInsurance(pd.concat(predictions, ignore_index=True),
                              pd.concat(auditedInputs, ignore_index=True), metadata)


def historicalInsuranceScenario(baseYear: int, footprintYear: int, state: str = "IA",
                                 crops: Sequence[str] | None = None, acresScale: float = 1.0,
                                 priceScale: float = 1.0) -> dict:
    """Expose the original historical-footprint what-if using the unchanged full fit."""
    result = evaluateFootprints(baseYear, state, baseYear, [footprintYear], crops, acresScale, priceScale)
    result["metadata"].update(runMode="historical footprint scenario",
                              evaluationLabel="In-sample what-if; full model fitted on 2000–2025")
    result["countyTable"]["runMode"] = result["metadata"]["runMode"]
    return result


def insuranceAnalogContext(inputs: pd.DataFrame, model: str, acresScale: float = 1.0,
                            priceScale: float = 1.0) -> dict:
    """Return C's neighbors and existing rough range for one inspected footprint."""
    bundle = _loadArtifact(model)
    analog = bundle["c_models"]["drought_payout_share"]
    rawPredictions = bundle["d_models"]["drought_payout_share"].predict(inputs)
    budgetModule = _modelModule("budget")
    rangeResult = budgetModule.statewide_range(inputs, analog=analog, preds={"D": rawPredictions}, point_model="D")
    state = inputs["state_alpha"].iloc[0]
    lowUsd, highUsd = rangeResult["range"][state]
    scale = acresScale * priceScale
    return {"closestYears": _closestYears(inputs, analog), "lowUsd": lowUsd * scale, "highUsd": highUsd * scale}


def replayInsurance(year: int, state: str = "IA", crops: Sequence[str] | None = None) -> dict:
    """Expose existing historical replay with identical audit fields and held-out actuals."""
    inputs = exposureRows(state, year, crops)
    replayResult = replay(year)
    selectedCrops = set(inputs["crop"])
    table = replayResult["county_table"].loc[lambda rows: rows["state"].eq(state)
                                             & rows["crop"].isin(selectedCrops)].reset_index(drop=True)
    table["scenarioLiabilityUsd"] = table["liability"]
    table["scenarioInsuredAcres"] = table["insured_acres"]
    table["scenarioFullCropValueUsd"] = table["liability"] / table["avg_coverage"]
    table["predDamagedAcres"] = table["pred_damaged_acre_share"] * table["insured_acres"]
    table["footprintYear"] = year
    model = replayResult["model"]
    inputs["footprintYear"] = year
    inputs["exposureBaseYear"] = year
    featureOrder = _loadArtifact(model)["feature_order"]
    inputs["imputedFeatures"] = inputs[featureOrder].isna().apply(lambda row: list(row.index[row]), axis=1)
    metadata = {
        "runMode": "historical replay", "state": state, "targetYear": year, "exposureBaseYear": year,
        "footprintYears": [year], "modelArtifact": f"d_{model}.joblib",
        "trainingYears": _loadArtifact(model)["training_years"],
        "evaluationLabel": replayResult["evaluation_label"], "acresScale": 1.0, "priceScale": 1.0,
        "featureOrder": featureOrder, "climateSource": "Observed historical August 15 features",
        "settings": _loadArtifact(model)["settings"]["D"], "predictedQuantities": ["payout share", "damaged-acre share"],
    }
    return summarizeInsurance(table, inputs, metadata)
