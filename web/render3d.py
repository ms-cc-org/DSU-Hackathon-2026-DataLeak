"""County records for the 3D viewer, and the viewer itself embedded in Streamlit.

The viewer is web/assets/viewer/viewer.html: a self-contained three.js scene (state map,
county diorama, side panel). This module
  1. builds the county records the viewer and the County risk page need (real data only),
  2. inlines three.js from web/assets/viewer/vendor/ so the viewer works without a network,
  3. embeds the result with st.iframe.

Mode 1 ("history") reads the 2000-2025 records directly. Mode 2 ("sandbox") runs a simple
lookup in the browser over the same records; it is labeled as an illustration, not a validated
prediction. When Lane 2's scenario function lands in src/engine.py, the sandbox numbers should
come from it instead (see docs/readme_notes/lane-4.md).
"""

import base64
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from src.data_loader import load_counties, load_master, load_weekly_drought


STATE = "IA"
STATE_NAME = "Iowa"
DEFAULT_FIPS = "19123"  # Mahaska County: all 26 corn years reported, 12 of them at D2+ drought
CROPS = ["CORN", "SOYBEANS"]
DEFAULT_PRICE = {"CORN": 4.00, "SOYBEANS": 10.00}  # assumed $/bushel until a cited price is added
FIRST_YEAR, LAST_YEAR, LAST_PROJECTED_YEAR = 2000, 2025, 2030
YEARS = list(range(FIRST_YEAR, LAST_YEAR + 1))
DECISION_DATE = (8, 15)  # Aug 15: the budget officer's decision date
SEASON_START = (5, 1)    # corn and soybean seasons both start May 1
MIN_TREND_YEARS = 10     # same rule as the master's yield_anomaly_pct

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
    return round(float(value), digits)


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
def loadCountyHistory(state: str = STATE, crop: str = "CORN") -> pd.DataFrame:
    """One row per county and year (2000-2025) with yield vs trend and estimated loss.

    Only rows with yield_status == "reported" carry a yield; other years keep NaN, never zero.
    The trend is fitted per county on all reported 2000-2025 years (hindsight), like the
    master's yield_anomaly_pct. loss_bu = max(0, trend - yield); loss_pct = loss_bu / trend.
    """
    master = load_master()  # fips is text, count columns are float
    rows = master[(master["state_alpha"] == state) & (master["crop"] == crop)].copy()

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
        frames.append(pd.DataFrame({
            "fips": fips,
            "county_name": group["county_name"].dropna().iloc[0],
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
            "aws_mm": group["aws_100cm_mm"].dropna().iloc[0] if group["aws_100cm_mm"].notna().any() else np.nan,
            "nccpi": group["nccpi_crop"].dropna().iloc[0] if group["nccpi_crop"].notna().any() else np.nan,
        }))
    return pd.concat(frames, ignore_index=True)


@st.cache_data(show_spinner=False)
def loadAsOfSeverity(state: str = STATE) -> pd.DataFrame:
    """Peak drought level from May 1 to Aug 15 for each county and year.

    Same rule as the master: a level counts when it covers more than 1% of the county, and
    the scale is the master's shifted one (0 = none, 1 = D0, ..., 5 = D4). Only weekly maps
    dated on or before Aug 15 are used, so nothing after the decision date leaks in.
    """
    master = load_master()
    stateFips = set(master.loc[master["state_alpha"] == state, "fips"])
    weekly = load_weekly_drought()
    weekly = weekly[weekly["fips"].isin(stateFips)].copy()
    year = weekly["map_date"].dt.year
    month, day = weekly["map_date"].dt.month, weekly["map_date"].dt.day
    afterStart = (month > SEASON_START[0]) | ((month == SEASON_START[0]) & (day >= SEASON_START[1]))
    beforeCutoff = (month < DECISION_DATE[0]) | ((month == DECISION_DATE[0]) & (day <= DECISION_DATE[1]))
    weekly = weekly[afterStart & beforeCutoff].assign(year=year)

    weekly["severity"] = 0
    for level, column in enumerate(["D0", "D1", "D2", "D3", "D4"], start=1):
        weekly.loc[weekly[column] > 1, "severity"] = level
    return weekly.groupby(["fips", "year"], as_index=False)["severity"].max()


# ---------------------------------------------------------------------------
# Viewer payload
# ---------------------------------------------------------------------------

def _cropArrays(history: pd.DataFrame) -> dict:
    """Year-indexed lists for one county and crop (null where there is no data)."""
    slope, intercept = history["trend_slope"].iloc[0], history["trend_intercept"].iloc[0]
    return {
        "yield": [jsonNumber(v, 1) for v in history["yield"]],
        "trend": [jsonNumber(v, 1) for v in history["trend"]],
        "anomaly": [jsonNumber(v, 1) for v in history["anomaly_pct"]],
        "lossBu": [jsonNumber(v, 2) for v in history["loss_bu"]],
        "lossPct": [jsonNumber(v, 2) for v in history["loss_pct"]],
        "acres": [jsonNumber(v, 0) for v in history["acres_planted"]],
        "trendCoef": None if pd.isna(slope) else [round(slope, 4), round(intercept, 2)],
    }


@st.cache_data(show_spinner=False)
def buildViewerData() -> dict:
    """Real county records for the viewer. Raises if the data cannot be loaded."""
    histories = {crop: loadCountyHistory(STATE, crop) for crop in CROPS}
    asof = loadAsOfSeverity(STATE).set_index(["fips", "year"])["severity"]
    corn = histories["CORN"]

    counties = []
    for feature in load_counties()["features"]:
        if feature["properties"]["state_alpha"] != STATE:
            continue
        fips = feature["id"]
        geometry = feature["geometry"]
        polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        county = {
            "fips": fips,
            "name": feature["properties"]["county_name"],
            "rings": [[[round(x, 4), round(y, 4)] for x, y in polygon[0]] for polygon in polygons],
            "inMaster": bool((corn["fips"] == fips).any()),
        }
        if county["inMaster"]:
            cornRows = corn[corn["fips"] == fips]
            county.update({
                "aws": jsonNumber(cornRows["aws_mm"].iloc[0], 0),
                "nccpi": jsonNumber(cornRows["nccpi"].iloc[0], 2),
                "sev": [jsonNumber(v, 0) for v in cornRows["max_severity"]],     # full corn season
                "weeks": [jsonNumber(v, 0) for v in cornRows["weeks_d2_plus"]],  # full corn season
                "asofSev": [jsonNumber(asof.get((fips, y)), 0) for y in YEARS],  # May 1 - Aug 15
                "crops": {},
            })
            for crop in CROPS:
                cropRows = histories[crop][histories[crop]["fips"] == fips]
                if not cropRows.empty:
                    county["crops"][crop] = _cropArrays(cropRows)
                else:  # county does not grow this crop: every value is null
                    county["crops"][crop] = {key: [None] * len(YEARS) for key in
                                             ["yield", "trend", "anomaly", "lossBu", "lossPct", "acres"]}
                    county["crops"][crop]["trendCoef"] = None
        counties.append(county)
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
            "lossBu": [jsonNumber(v, 2) for v in lossBu], "lossPct": [jsonNumber(v, 2) for v in 100 * lossBu / trend],
            "acres": [120000.0] * len(YEARS), "trendCoef": [2.0, 150 - 2.0 * FIRST_YEAR],
        }
        counties.append({
            "fips": f"99{n:03d}", "name": f"Placeholder County {n + 1}", "inMaster": True,
            "rings": [[[x0, y0], [x0 + 0.45, y0], [x0 + 0.45, y0 + 0.45], [x0, y0 + 0.45], [x0, y0]]],
            "aws": 180.0, "nccpi": 0.7, "sev": [int(s) for s in sev], "weeks": [int(max(s - 2, 0) * 3) for s in sev],
            "asofSev": [int(s) for s in sev], "crops": {crop: arrays for crop in CROPS},
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


def viewerHtml(mode: str = "history", focusFips: str = DEFAULT_FIPS, startYear: int = 2012,
               cornPrice: float | None = None) -> str:
    """The full viewer page. mode is "history" (Mode 1) or "sandbox" (Mode 2)."""
    try:
        data = dict(buildViewerData())
    except Exception:
        data = buildPlaceholderData()
    fipsList = [c["fips"] for c in data["counties"] if c.get("inMaster")]
    data.update({
        "mode": mode,
        "focusFips": focusFips if focusFips in fipsList else fipsList[0],
        "stateName": "Placeholder state" if data["placeholder"] else STATE_NAME,
        "firstYear": FIRST_YEAR,
        "lastYear": LAST_YEAR,
        "lastProjectedYear": LAST_PROJECTED_YEAR,
        "startYear": int(min(max(startYear, FIRST_YEAR), LAST_YEAR)),
        "defaultPrice": {**DEFAULT_PRICE, **({"CORN": float(cornPrice)} if cornPrice is not None else {})},
    })
    template = (VIEWER_DIR / "viewer.html").read_text()
    dataJson = json.dumps(data).replace("</", "<\\/")  # never close the <script> tag early
    return template.replace("__IMPORT_MAP__", _importMap()).replace("__DATA_JSON__", dataJson)


def showViewer(mode: str = "history", focusFips: str = DEFAULT_FIPS, startYear: int = 2012,
               cornPrice: float | None = None, height: int = 800) -> None:
    """Embed the 3D viewer at full width. Mode 1: showViewer("history", fips, year, price).
    Mode 2: showViewer("sandbox", fips). cornPrice starts the viewer's price input (assumed price)."""
    if not (VIEWER_DIR / "viewer.html").exists():
        st.warning("The 3D viewer file is missing (web/assets/viewer/viewer.html); the rest of the page still works.")
        return
    # st.iframe embeds our own HTML string (built here, trusted) in an isolated frame.
    st.iframe(viewerHtml(mode, focusFips, startYear, cornPrice), height=height)
