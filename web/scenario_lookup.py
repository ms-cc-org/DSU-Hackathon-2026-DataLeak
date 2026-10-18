"""Prototype lookup, not a validated model.

The Planner's scenario numbers: an estimated crop-value loss for a drought level the user picks.
It uses the same per-level method as the 3D viewer's Scenario mode (lossForBucket in
web/assets/viewer/viewer.html), so a chosen level gives the same estimate in both. There is no
drought prediction: the user always chooses the level.

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
    county = _countiesByFips().get(fips)
    arrays = county["crops"].get(crop) if county else None
    if not arrays:
        return {"years": [], "trend": None, "acres": None}
    firstYear = LAST_YEAR - len(arrays["yield"]) + 1
    years = []
    for i, (lossBu, trend, asof) in enumerate(zip(arrays["lossBu"], arrays["trend"], arrays["asof"])):
        if lossBu is None or trend is None or asof is None:
            continue
        years.append({"year": firstYear + i, "bucket": bucketOf(asof), "loss": 100 * lossBu / trend})
    acres = [a for a in arrays["acres"] if a is not None]
    return {"years": years, "trend": tuple(arrays["trendCoef"]) if arrays["trendCoef"] else None,
            "acres": acres[-1] if acres else None, "name": county["name"], "state": county["state"]}


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
    """Estimated loss % and dollars for one county, crop, year and chosen drought level ("D0".."D4")."""
    records = countyRecords(fips, crop)
    history = records["years"]
    if len(history) < MIN_HISTORY_YEARS or records["trend"] is None:
        return {"error": "Too few reported yields for this county and crop to run a scenario."}

    slope, intercept = records["trend"]
    trendYield = intercept + slope * year
    acres = records["acres"]

    def dollars(lossPct):
        return None if acres is None else trendYield * lossPct / 100 * acres * price

    bucket = LEVELS.index(level)
    part = lossForBucket(history, bucket)
    return {"trendYield": trendYield, "acres": acres, "projected": year > LAST_YEAR, "dollars": dollars,
            **part, "bucket": bucket, "warnings": [part["warning"]] if part["warning"] else []}
