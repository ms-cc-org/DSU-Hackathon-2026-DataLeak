"""Prototype lookup, not a validated model.

The Planner's scenario numbers. This is the same method as the 3D viewer's Scenario mode
(lossForBucket and runEngine in web/assets/viewer/viewer.html), ported to Python so both show the
same numbers. Lane 3 reuses this lookup for every county and crop in a state;
the separate src/engine.py contract estimates RMA insurance payouts.

Method, for one county and crop:
  1. History: every 2000-2025 year with a reported yield, its loss % below the county's 2000-2025
     linear trend, and its drought level as known on Aug 15 (peak level in the weekly maps from the
     crop's season start to Aug 15; see AS_OF_WINDOWS in web/render3d.py). A year with no drought
     counts as D0.
  2. A chosen level D0-D4: the estimate is the median loss of past years at that level. With fewer
     than 2 matching years, or a level outside the county's history, it is the average of the nearest
     3 years (by level, then most recent), and a warning says so.
  3. Dollars = trend yield for the selected year x loss % x planted acres x price. 2026-2030 trend
     yield is a linear extension of the 2000-2025 trend; planted acres are the latest reported.

It reads the same county records the viewer receives (web/render3d.py: buildViewerData), so the
Planner and the viewer show identical numbers.
"""

import statistics

import streamlit as st

from web.render3d import LAST_YEAR, buildViewerData


LEVELS = ["D0", "D1", "D2", "D3", "D4"]
MIN_HISTORY_YEARS = 5


def bucketOf(severity) -> int:
    """Master scale 0-5 (0 = none, 1 = D0, ..., 5 = D4) to a bucket 0-4 (D0-D4); none counts as D0."""
    return max(1, int(severity)) - 1


@st.cache_data(show_spinner=False)
def _countiesByFips() -> dict:
    """The same county records the 3D viewer receives, so both show identical numbers."""
    return {c["fips"]: c for c in buildViewerData()["counties"] if c.get("inMaster")}


def countyRecords(fips: str, crop: str) -> dict:
    """Year-by-year history for one county and crop, plus its trend line and latest planted acres."""
    return recordsForCrop(_countiesByFips().get(fips), crop)


def recordsForCrop(countyData: dict | None, crop: str) -> dict:
    """Extract records from an already-loaded county, avoiding repeated bulk reads."""
    cropArrays = countyData["crops"].get(crop) if countyData else None
    if not cropArrays:
        return {"years": [], "trend": None, "acres": None}
    firstYear = LAST_YEAR - len(cropArrays["yield"]) + 1
    years = []
    for yearIndex, (lossBu, trendYield, asOf) in enumerate(zip(cropArrays["lossBu"], cropArrays["trend"], cropArrays["asof"])):
        if lossBu is None or trendYield is None or trendYield <= 0 or asOf is None:
            continue
        years.append({"year": firstYear + yearIndex, "bucket": bucketOf(asOf), "loss": 100 * lossBu / trendYield})
    acreageRecords = [(firstYear + yearIndex, value) for yearIndex, value in enumerate(cropArrays["acres"])
                      if value is not None]
    return {"years": years, "trend": tuple(cropArrays["trendCoef"]) if cropArrays["trendCoef"] else None,
            "acres": acreageRecords[-1][1] if acreageRecords else None,
            "acreageYear": acreageRecords[-1][0] if acreageRecords else None,
            "name": countyData["name"], "state": countyData["state"]}


def lossForBucket(history: list[dict], bucket: int) -> dict:
    """Loss for one drought level: matching years, or the nearest years with a warning."""
    buckets = [h["bucket"] for h in history]
    low, high = min(buckets), max(buckets)
    matches = [h for h in history if h["bucket"] == bucket]
    nearest = sorted(history, key=lambda h: (abs(h["bucket"] - bucket), -h["year"]))[:3]
    warning, basis = None, matches
    if bucket < low or bucket > high:
        warning = (f"{LEVELS[bucket]} is outside this county's history by Aug 15 ({LEVELS[low]}-{LEVELS[high]}). "
                   "The estimate is the average of the nearest 3 historical years, so treat it with caution.")
        basis = nearest
    elif len(matches) < 2:
        warning = (f"Only {len(matches)} past year(s) reached exactly {LEVELS[bucket]} by Aug 15. "
                   "The estimate is the average of the nearest 3 historical years, so treat it with caution.")
        basis = nearest
    losses = [h["loss"] for h in basis]
    confident = warning is None
    return {"mid": statistics.median(losses) if confident else sum(losses) / len(losses),
            "low": min(losses), "high": max(losses), "n": len(basis), "nearest": nearest,
            "warning": warning, "confident": confident}


def scenario(fips: str, crop: str, year: int, level: str, price: float) -> dict:
    """Expected loss % and dollars for one county, crop, year and drought level ("D0".."D4" or "Predict")."""
    return scenarioFromRecords(countyRecords(fips, crop), year, level, price)


def scenarioFromRecords(records: dict, year: int, level: str, price: float) -> dict:
    """Run the same single-county lookup from records already loaded by either workflow."""
    history = records["years"]
    if len(history) < MIN_HISTORY_YEARS or records["trend"] is None:
        return {"error": "Too few reported yields for this county and crop to run a scenario."}

    slope, intercept = records["trend"]
    trendYield = intercept + slope * year
    if trendYield <= 0:
        return {"error": "The projected trend yield is not positive for this county and crop."}
    acres = records["acres"]

    def dollars(lossPct: float) -> float | None:
        return None if acres is None else trendYield * lossPct / 100 * acres * price

    bucket = LEVELS.index(level)
    part = lossForBucket(history, bucket)
    return {"trendYield": trendYield, "acres": acres, "projected": year > LAST_YEAR, "dollars": dollars,
            **part, "bucket": bucket, "warnings": [part["warning"]] if part["warning"] else []}
