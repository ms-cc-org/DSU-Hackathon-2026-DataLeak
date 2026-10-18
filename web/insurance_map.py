"""Join completed insurance predictions to every county and embed their 3D state map."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.insurance_scenarios import insuranceStates
from web.maps import boundaryRings, countyMapData
from web.render3d import _importMap, jsonNumber
from web.ui import CROP_NAMES


def insuranceMapData(table: pd.DataFrame, state: str, year: int) -> dict:
    """Sum selected crops per county; use exposure weights for shares and null for absent rows."""
    geometry, countyTotals = countyMapData(table, state, "X_payout_usd")
    if not geometry["features"]:
        raise ValueError(f"No supplied county boundaries for {state}.")
    groups = dict(tuple(table.groupby("fips")))
    counties = []
    for feature in geometry["features"]:
        fips = feature["id"]
        countyRows = groups.get(fips)
        county = {"fips": fips, "name": feature["properties"]["county_name"],
                  "rings": boundaryRings(feature), "payoutUsd": None, "payoutShare": None,
                  "damagedAcreShare": None, "damagedAcres": None, "crops": [], "outOfRange": False}
        if countyRows is not None:
            payoutUsd = countyRows["X_payout_usd"].sum(min_count=1)
            liabilityUsd = countyRows["scenarioLiabilityUsd"].sum(min_count=1)
            insuredAcres = countyRows["scenarioInsuredAcres"].sum(min_count=1)
            damagedAcres = countyRows["predDamagedAcres"].sum(min_count=1)
            county.update(payoutUsd=jsonNumber(payoutUsd, 6),
                          payoutShare=jsonNumber(payoutUsd / liabilityUsd, 8) if liabilityUsd > 0 else None,
                          damagedAcreShare=jsonNumber(damagedAcres / insuredAcres, 8) if insuredAcres > 0 else None,
                          damagedAcres=jsonNumber(damagedAcres, 2),
                          outOfRange=bool(countyRows["out_of_range"].any()),
                          crops=[{"name": CROP_NAMES.get(row.crop, row.crop),
                                  "payoutUsd": jsonNumber(row.X_payout_usd, 6)}
                                 for row in countyRows.itertuples(index=False)])
        counties.append(county)
    cropLabel = " + ".join(CROP_NAMES.get(crop, crop) for crop in sorted(table["crop"].unique()))
    return {"state": insuranceStates.get(state, state), "stateCode": state, "year": int(year), "cropLabel": cropLabel,
            "totalPayoutUsd": jsonNumber(countyTotals["value"].sum(min_count=1), 6), "counties": counties}


def insuranceMapHtml(table: pd.DataFrame, state: str, year: int) -> str:
    """Use the Planner's bundled three.js runtime with completed predictions, never a crop-loss lookup."""
    payload = json.dumps(insuranceMapData(table, state, year), allow_nan=False).replace("</", "<\\/")
    template = Path(__file__).with_name("assets") / "viewer" / "insurance_map.html"
    return template.read_text().replace("__IMPORT_MAP__", _importMap()).replace("__DATA_JSON__", payload)


def renderInsuranceMap(table: pd.DataFrame, state: str, year: int) -> None:
    """Display an always-visible interactive 3D view of the completed run."""
    st.iframe(insuranceMapHtml(table, state, year), height=650)
    st.caption("County height and color show predicted insurance payouts, summed across the selected crops. "
               "Drag to orbit, scroll to zoom, and select a county for its breakdown. Grey counties have no estimate. "
               "Heights represent dollars, not terrain; this 3D view uses local county boundaries without imagery tiles.")
