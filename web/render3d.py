"""County records for the 3D viewer, and the viewer itself embedded in Streamlit.

The viewer is web/assets/viewer/viewer.html: a self-contained three.js scene (state map of all four
states, county diorama, side panel). This module
  1. builds the county records the viewer and the pages need (real data only),
  2. inlines three.js from web/assets/viewer/vendor/ so the viewer works without a network,
  3. embeds the result with st.iframe.

Mode 1 ("history") reads the 2000-2025 records directly. Mode 2 ("sandbox") runs a simple lookup in
the browser over the same records; it is labeled as an illustration, not a validated prediction.
When Lane 2's scenario function lands in src/engine.py, the sandbox numbers should come from it
instead (see docs/readme_notes/lane-4.md).
"""

import base64
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from src.data_loader import load_counties, load_master, load_weekly_drought
from web.ui import CROP_NAMES, DEFAULT_PRICE


STATES = {"CA": "California", "DE": "Delaware", "IA": "Iowa", "NE": "Nebraska"}
CROPS = ["CORN", "SOYBEANS", "WHEAT", "SORGHUM"]
DEFAULT_FIPS = "19123"  # Mahaska County, Iowa: all 26 corn years reported, 12 of them at D2+ drought
FIRST_YEAR, LAST_YEAR, LAST_PROJECTED_YEAR = 2000, 2025, 2030
YEARS = list(range(FIRST_YEAR, LAST_YEAR + 1))
MIN_TREND_YEARS = 10  # same rule as the master's yield_anomaly_pct

# Drought window used by the Scenarios engine for each crop: weekly maps from the season start up to
# the Aug 15 decision date. Winter wheat is harvested before Aug 15, so it uses its whole season
# (Sep 1 of the previous year to Jun 30), the same window as the master.
AS_OF_WINDOWS = {
    "CORN": ((5, 1), (8, 15), False),
    "SOYBEANS": ((5, 1), (8, 15), False),
    "SORGHUM": ((6, 1), (8, 15), False),
    "WHEAT": ((9, 1), (6, 30), True),
}

VIEWER_DIR = Path(__file__).resolve().parent / "assets" / "viewer"
VENDOR_FILES = {  # import name -> bundled file (three.js r169, MIT license in vendor/LICENSE)
    "three": "three.module.min.js",
    "three/addons/controls/OrbitControls.js": "OrbitControls.js",
    "three/addons/utils/BufferGeometryUtils.js": "BufferGeometryUtils.js",
}
CDN_IMPORT_MAP = {  # only used if the bundled files are missing
    "three": "https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.min.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/",
}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def jsonNumber(value, digits: int = 2):
    """JSON-safe number: NaN becomes null (never zero)."""
    if value is None or pd.isna(value):
        return None
    value = round(float(value), digits)
    return int(value) if digits == 0 else value


def fitTrend(years: np.ndarray, yields: np.ndarray):
    """Linear yield trend (slope, intercept) from reported years, or None if too few years."""
    if len(yields) < MIN_TREND_YEARS:
        return None
    slope, intercept = np.polyfit(years, yields, 1)
    return float(slope), float(intercept)


# ---------------------------------------------------------------------------
# County records (real data)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def loadCountyHistory(state: str | None = "IA", crop: str = "CORN") -> pd.DataFrame:
    """One row per county and year (2000-2025) with yield vs trend and estimated loss.

    state=None returns all four states. Only rows with yield_status == "reported" carry a yield;
    other years keep NaN, never zero. The trend is fitted per county on all reported 2000-2025
    years (hindsight), like the master's yield_anomaly_pct. loss_bu = max(0, trend - yield);
    loss_pct = loss_bu / trend.
    """
    master = load_master()  # fips is text, count columns are float
    rows = master[master["crop"] == crop]
    if state is not None:
        rows = rows[rows["state_alpha"] == state]

    frames = []
    for fips, group in rows.groupby("fips"):
        group = group.set_index("year").reindex(YEARS)
        reported = group["yield_status"] == "reported"
        yields = group["yield_per_acre"].where(reported)
        ok = yields.notna()
        trend = fitTrend(np.array(YEARS)[ok.values], yields[ok].values)
        trendValues = (pd.Series(np.nan, index=YEARS) if trend is None
                       else trend[1] + trend[0] * pd.Series(YEARS, index=YEARS, dtype=float))
        lossBu = (trendValues - yields).clip(lower=0)
        first = lambda column: group[column].dropna().iloc[0] if group[column].notna().any() else np.nan
        frames.append(pd.DataFrame({
            "fips": fips,
            "county_name": first("county_name"),
            "state_alpha": first("state_alpha"),
            "year": YEARS,
            "yield_status": group["yield_status"].fillna("no_row").values,
            "yield": yields.values,
            "trend": trendValues.values,
            "trend_slope": np.nan if trend is None else trend[0],
            "trend_intercept": np.nan if trend is None else trend[1],
            "anomaly_pct": group["yield_anomaly_pct"].where(reported).values,
            "loss_bu": lossBu.values,
            "loss_pct": (100 * lossBu / trendValues).values,
            "acres_planted": group["acres_planted"].values,
            "max_severity": group["max_drought_severity"].values,
            "weeks_d2_plus": group["weeks_in_d2_plus"].values,
            "aws_mm": first("aws_100cm_mm"),
            "nccpi": first("nccpi_crop"),
        }))
    columns = ["fips", "county_name", "state_alpha", "year", "yield", "trend", "loss_bu", "loss_pct"]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=columns)


@st.cache_data(show_spinner=False)
def loadSeasonPeak(start: tuple[int, int], end: tuple[int, int], startsPreviousYear: bool = False) -> pd.DataFrame:
    """Peak drought level per county and season year from the weekly maps between two dates.

    Same rule as the master: a level counts when it covers more than 1% of the county, and the
    scale is the master's shifted one (0 = none, 1 = D0, ..., 5 = D4). Only maps inside the window
    are used, so nothing after the end date leaks in. With startsPreviousYear, the window runs from
    `start` in year-1 to `end` in year (winter wheat).
    """
    weekly = load_weekly_drought()
    month, day = weekly["map_date"].dt.month, weekly["map_date"].dt.day
    monthDay = month * 100 + day
    startKey, endKey = start[0] * 100 + start[1], end[0] * 100 + end[1]
    year = weekly["map_date"].dt.year
    if startsPreviousYear:
        inWindow = (monthDay >= startKey) | (monthDay <= endKey)
        year = year.where(monthDay <= endKey, year + 1)
    else:
        inWindow = (monthDay >= startKey) & (monthDay <= endKey)
    weekly = weekly[inWindow].assign(year=year[inWindow])

    weekly["severity"] = 0
    for level, column in enumerate(["D0", "D1", "D2", "D3", "D4"], start=1):
        weekly.loc[weekly[column] > 1, "severity"] = level
    peak = weekly.groupby(["fips", "year"], as_index=False)["severity"].max()
    # The Drought Monitor archive starts Jan 4, 2000: a window that begins in 1999 is incomplete,
    # so that season is left empty (the master does the same for winter wheat 2000).
    firstComplete = FIRST_YEAR + 1 if startsPreviousYear else FIRST_YEAR
    return peak[peak["year"].between(firstComplete, LAST_YEAR)]


# ---------------------------------------------------------------------------
# Viewer payload
# ---------------------------------------------------------------------------

def _cropArrays(history: pd.DataFrame, asof: pd.Series) -> dict:
    """Year-indexed lists for one county and crop (null where there is no data)."""
    slope, intercept = history["trend_slope"].iloc[0], history["trend_intercept"].iloc[0]
    fips = history["fips"].iloc[0]
    return {
        "yield": [jsonNumber(v, 1) for v in history["yield"]],
        "trend": [jsonNumber(v, 1) for v in history["trend"]],
        "anomaly": [jsonNumber(v, 1) for v in history["anomaly_pct"]],
        "lossBu": [jsonNumber(v, 2) for v in history["loss_bu"]],
        "acres": [jsonNumber(v, 0) for v in history["acres_planted"]],
        "sev": [jsonNumber(v, 0) for v in history["max_severity"]],      # full crop season (master)
        "weeks": [jsonNumber(v, 0) for v in history["weeks_d2_plus"]],   # full crop season (master)
        "asof": [jsonNumber(asof.get((fips, y)), 0) for y in YEARS],     # season start to Aug 15
        "nccpi": jsonNumber(history["nccpi"].iloc[0], 2),
        "trendCoef": None if pd.isna(slope) else [round(slope, 4), round(intercept, 2)],
    }


@st.cache_data(show_spinner=False)
def buildViewerData() -> dict:
    """Real county records for all four states. Raises if the data cannot be loaded."""
    histories = {crop: loadCountyHistory(None, crop) for crop in CROPS}
    asofByCrop = {crop: loadSeasonPeak(*AS_OF_WINDOWS[crop]).set_index(["fips", "year"])["severity"]
                  for crop in CROPS}
    groups = {crop: dict(tuple(histories[crop].groupby("fips"))) for crop in CROPS}

    counties = []
    for feature in load_counties()["features"]:
        props = feature["properties"]
        if props["state_alpha"] not in STATES:
            continue
        fips = feature["id"]
        geometry = feature["geometry"]
        polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        crops = {crop: _cropArrays(groups[crop][fips], asofByCrop[crop])
                 for crop in CROPS if fips in groups[crop]}
        aws = next((groups[c][fips]["aws_mm"].iloc[0] for c in CROPS if fips in groups[c]), None)
        counties.append({
            "fips": fips,
            "name": props["county_name"],
            "state": props["state_alpha"],
            "rings": [[[round(x, 3), round(y, 3)] for x, y in polygon[0]] for polygon in polygons],
            "inMaster": bool(crops),
            "aws": jsonNumber(aws, 0),
            "crops": crops,
        })
    return {"placeholder": False, "counties": counties}


def buildPlaceholderData() -> dict:
    """A 4 x 4 grid of fake square counties. Only used if the real data cannot load,
    and the viewer then shows a permanent "PLACEHOLDER DATA - NOT REAL RESULTS" banner."""
    rng = np.random.default_rng(0)
    counties = []
    for n in range(16):
        x0, y0 = -94 + (n % 4) * 0.5, 41 + (n // 4) * 0.5
        sev = rng.choice([0, 1, 2, 3, 4], size=len(YEARS), p=[0.3, 0.2, 0.2, 0.2, 0.1])
        trend = 150 + 2 * (np.array(YEARS) - FIRST_YEAR)
        yields = trend * (1 - 0.04 * np.maximum(sev - 2, 0) + rng.normal(0, 0.03, len(YEARS)))
        yields[[7, 20]] = np.nan  # two years without a reported yield
        lossBu = np.clip(trend - yields, 0, None)
        arrays = {
            "yield": [jsonNumber(v, 1) for v in yields], "trend": [jsonNumber(v, 1) for v in trend],
            "anomaly": [jsonNumber(v, 1) for v in 100 * (yields - trend) / trend],
            "lossBu": [jsonNumber(v, 2) for v in lossBu], "acres": [120000] * len(YEARS),
            "sev": [int(s) for s in sev], "weeks": [int(max(s - 2, 0) * 3) for s in sev],
            "asof": [int(s) for s in sev], "nccpi": 0.7, "trendCoef": [2.0, 150 - 2.0 * FIRST_YEAR],
        }
        counties.append({
            "fips": f"99{n:03d}", "name": f"Placeholder County {n + 1}", "state": "IA", "inMaster": True,
            "rings": [[[x0, y0], [x0 + 0.45, y0], [x0 + 0.45, y0 + 0.45], [x0, y0 + 0.45], [x0, y0]]],
            "aws": 180, "crops": {"CORN": arrays},
        })
    return {"placeholder": True, "counties": counties}


# ---------------------------------------------------------------------------
# Viewer HTML and embedding
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _importMap() -> str:
    """Import map that inlines the bundled three.js files as data: URLs (no network needed).
    Falls back to the pinned CDN copy only if a bundled file is missing."""
    vendor = VIEWER_DIR / "vendor"
    if all((vendor / name).exists() for name in VENDOR_FILES.values()):
        imports = {key: "data:text/javascript;base64," + base64.b64encode((vendor / name).read_bytes()).decode()
                   for key, name in VENDOR_FILES.items()}
    else:
        imports = CDN_IMPORT_MAP
    return json.dumps({"imports": imports})


@st.cache_data(show_spinner=False)
def _dataJson() -> tuple[str, bool]:
    """The county records as JSON (built once), and whether they are placeholder data."""
    try:
        data = buildViewerData()
    except Exception:
        data = buildPlaceholderData()
    return json.dumps(data, separators=(",", ":")).replace("</", "<\\/"), data["placeholder"]


def viewerHtml(mode: str = "history", focusFips: str = DEFAULT_FIPS, startYear: int = 2012,
               crop: str = "CORN", price: float | None = None) -> str:
    """The full viewer page. mode is "history" (Mode 1) or "sandbox" (Mode 2)."""
    dataJson, placeholder = _dataJson()
    settings = {
        "mode": mode,
        "focusFips": focusFips,
        "states": STATES,
        "cropNames": CROP_NAMES,
        "firstYear": FIRST_YEAR,
        "lastYear": LAST_YEAR,
        "lastProjectedYear": LAST_PROJECTED_YEAR,
        "startYear": int(min(max(startYear, FIRST_YEAR), LAST_YEAR)),
        "startCrop": crop if crop in CROPS else "CORN",
        "defaultPrice": {**DEFAULT_PRICE, **({crop: float(price)} if price is not None else {})},
        "placeholder": placeholder,
    }
    template = (VIEWER_DIR / "viewer.html").read_text()
    return (template.replace("__IMPORT_MAP__", _importMap())
            .replace("__DATA_JSON__", dataJson)
            .replace("__SETTINGS_JSON__", json.dumps(settings)))


def showViewer(mode: str = "history", focusFips: str = DEFAULT_FIPS, startYear: int = 2012,
               crop: str = "CORN", price: float | None = None, height: int = 800) -> None:
    """Embed the 3D viewer at full width.
    Mode 1: showViewer("history", fips, year, crop, price). Mode 2: showViewer("sandbox", fips).
    price starts the viewer's price input for that crop (an assumed price)."""
    if not (VIEWER_DIR / "viewer.html").exists():
        st.warning("The 3D viewer file is missing (web/assets/viewer/viewer.html); the rest of the page still works.")
        return
    # st.iframe embeds our own HTML string (built here, trusted) in an isolated frame.
    st.iframe(viewerHtml(mode, focusFips, startYear, crop, price), height=height)
