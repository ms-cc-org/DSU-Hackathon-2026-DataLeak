"""Cached model inference shared by Insurance and the all-crop state fund workflow."""

import streamlit as st

from src.insurance_scenarios import historicalInsuranceScenario, insuranceInventory, insuranceStates, projectInsurance, replayInsurance


@st.cache_data(show_spinner=False)
def runInsurance(inputs: dict) -> dict:
    """Cache inference results only; fitting is never part of a page request."""
    crops = None if inputs["crop"] == "ALL" else [inputs["crop"]]
    if inputs["mode"] == "Historical replay":
        result = replayInsurance(inputs["year"], inputs["state"], crops)
    elif inputs["mode"] == "Historical footprint scenario":
        result = historicalInsuranceScenario(inputs["baseYear"], inputs["footprint"], inputs["state"], crops,
                                             inputs["acresScale"], inputs["priceScale"])
    elif inputs["mode"] == "Future insurance scenario":
        result = projectInsurance(inputs["year"], inputs["state"], inputs["baseYear"],
                             None if inputs["footprint"] == "ALL" else [inputs["footprint"]], crops,
                             inputs["acresScale"], inputs["priceScale"])
    else:
        raise ValueError(f"Unknown insurance calculation: {inputs['mode']}")
    result["metadata"]["crops"] = sorted(result["countyTable"]["crop"].unique())
    result["metadata"]["selection"] = dict(inputs)
    return result


def insuranceContextForFund(state: str, year: int) -> dict | None:
    """Use the saved model for supported states; never extrapolate to untrained crops."""
    if state not in insuranceStates:
        return None
    return runInsurance({"mode": "Future insurance scenario", "state": state, "year": year,
                         "crop": "ALL", "baseYear": insuranceInventory()["lastYear"], "footprint": "ALL",
                         "acresScale": 1.0, "priceScale": 1.0})
