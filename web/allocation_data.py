"""Bulk state scenario adapter using the active Planner's crop-value-loss lookup."""

import math

import pandas as pd
import streamlit as st

from web.render3d import CROPS, LAST_PROJECTED_YEAR, LAST_YEAR, STATES, buildViewerData
from web.scenario_lookup import LEVELS, recordsForCrop, scenarioFromRecords


def estimateCountyCrop(countyData: dict, crop: str, year: int, level: str, price: float) -> dict:
    """Keep unavailable combinations explicit alongside the scenario inputs and warnings."""
    records = recordsForCrop(countyData, crop)
    row = {
        "fips": countyData["fips"], "county": countyData["name"], "state": countyData["state"],
        "crop": crop, "year": year, "scenarioLevel": level, "pricePerBushel": price,
        "acres": records["acres"], "acreageYear": records.get("acreageYear"),
        "historyYears": len(records["years"]), "trendYield": None,
        "estimatedLossUsd": None, "lossLowUsd": None, "lossHighUsd": None,
        "confident": False, "warnings": "", "unavailableReason": "",
        "predictionSource": "Historical crop-loss lookup; not model D",
    }
    if crop not in countyData["crops"]:
        row["unavailableReason"] = "No supplied records for this county and crop."
        return row
    result = scenarioFromRecords(records, year, level, price)
    if "error" in result:
        row["unavailableReason"] = result["error"]
        return row
    row.update(trendYield=result["trendYield"], confident=result["confident"], warnings=" ".join(result["warnings"]))
    if records["acres"] is None:
        row["unavailableReason"] = "No planted acreage on record; dollar loss cannot be estimated."
        return row
    for resultKey, tableColumn in (("mid", "estimatedLossUsd"), ("low", "lossLowUsd"), ("high", "lossHighUsd")):
        amount = result["dollars"](result[resultKey])
        if not math.isfinite(amount) or amount < 0:
            raise ValueError(f"Invalid dollar estimate for {countyData['fips']} / {crop}.")
        row[tableColumn] = amount
    return row


@st.cache_data(show_spinner=False)
def buildStateEstimates(state: str, year: int, level: str, prices: dict[str, float]) -> pd.DataFrame:
    """One row per boundary county × all four crops, including unavailable combinations.

    A chosen D0-D4 level is applied across the state. Predict instead uses each
    county/crop's own historical drought frequencies. Prices are dollars/bushel.
    """
    if state not in STATES:
        raise ValueError(f"Unsupported state: {state}")
    if year not in range(LAST_YEAR + 1, LAST_PROJECTED_YEAR + 1):
        raise ValueError(f"Scenario year must be {LAST_YEAR + 1}-{LAST_PROJECTED_YEAR}.")
    if level not in LEVELS + ["Predict"]:
        raise ValueError(f"Unsupported drought level: {level}")
    if set(prices) != set(CROPS):
        raise ValueError("Provide a price assumption for every supported crop.")
    if any(not math.isfinite(price) or price < 0 for price in prices.values()):
        raise ValueError("Prices must be finite, non-negative dollars per bushel.")
    viewerData = buildViewerData()
    if viewerData.get("placeholder"):
        raise ValueError("Allocation requires supplied records, not placeholder county data.")
    countyRows = [countyData for countyData in viewerData["counties"] if countyData["state"] == state]
    if not countyRows:
        raise ValueError(f"No supplied county boundaries for {state}.")
    return pd.DataFrame([
        estimateCountyCrop(countyData, crop, year, level, prices[crop])
        for countyData in countyRows for crop in CROPS
    ])
