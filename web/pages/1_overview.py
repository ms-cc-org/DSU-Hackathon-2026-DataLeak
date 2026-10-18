"""Overview: who the tool is for, the decision, how to use the site, and the data behind it."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data import loadIowaCornHistory
from src.data_loader import load_counties, load_master
from web.render3d import STATES, loadSeasonPeak
from web.ui import DROUGHT_COLORS, DROUGHT_LABELS, DROUGHT_WORDS, animatedStats, heroBanner, showVideo


@st.cache_data(show_spinner=False)
def getIowaCornHistory() -> pd.DataFrame:
    """Cache the supplied Iowa corn history for the overview page."""
    return loadIowaCornHistory()


@st.cache_data(show_spinner=False)
def datasetCounts() -> dict:
    master = load_master()
    return {"years": master["year"].nunique(), "counties": master["fips"].nunique(),
            "states": master["state_alpha"].nunique(),
            "reported": int((master["yield_status"] == "reported").sum())}


@st.cache_data(show_spinner=False)
def growingSeasonDrought() -> pd.DataFrame:
    """Peak drought level from May 1 to Sep 30 for every county and year (weekly maps, all 253 counties)."""
    peak = loadSeasonPeak((5, 1), (9, 30))
    peak["level"] = peak["severity"].map(lambda s: DROUGHT_LABELS[int(s)])
    return peak.sort_values(["year", "fips"])


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

if not showVideo("intro_loop.mp4", caption="Illustrative animation (AI-generated, Higgsfield). Not data."):
    heroBanner("Drought Relief Allocation Planner",
               "Where should a state drought-relief fund go on August 15? 26 years of county records answer.")

try:
    counts = datasetCounts()
    animatedStats([("years of records", counts["years"], ""), ("counties", counts["counties"], ""),
                   ("states", counts["states"], ""), ("reported county-crop yields", counts["reported"], "")])
except Exception as error:
    st.warning(f"Dataset counts are unavailable: {error}")

st.markdown(
    """
**Who it is for:** a state drought-relief budget officer.

**The decision:** on **August 15**, how to split a fixed relief fund across counties, using what is
known about the season by that date.

**What the tool shows:** for each county, how often severe drought hits (exposure), how much yield it
loses when it does (vulnerability), and what that costs in dollars (an estimated crop loss, not a
program payout).
"""
)

st.subheader("Drought across the four states, 2000-2025")
st.caption("Press play: each frame is one growing season (May 1 to Sep 30), colored by the worst U.S. Drought "
           "Monitor level reached in each county. Real weekly maps for all 253 counties.")
scopeNames = {"ALL": "All four states", **STATES}
scope = st.segmented_control("Show", list(scopeNames), default="IA", format_func=scopeNames.get) or "IA"
try:
    drought = growingSeasonDrought()
    geo = load_counties()
    features = [f for f in geo["features"] if f["properties"]["state_alpha"] in STATES
                and (scope == "ALL" or f["properties"]["state_alpha"] == scope)]
    names = {f["id"]: f"{f['properties']['county_name']}, {f['properties']['state_alpha']}" for f in features}
    shown = drought[drought["fips"].isin(names)].copy()
    shown["county"] = shown["fips"].map(names)
    shown["meaning"] = shown["severity"].map(lambda s: DROUGHT_WORDS[int(s)])
    # One numeric trace per frame with a stepped color scale (one band per drought level), so every
    # level shows in every year. Categorical colors would drop levels absent from the first frame.
    steps = []
    for k, color in enumerate(DROUGHT_COLORS):
        steps += [(k / 6, color), ((k + 1) / 6, color)]
    droughtMap = px.choropleth(
        shown, geojson={"type": "FeatureCollection", "features": features}, locations="fips", featureidkey="id",
        color="severity", animation_frame="year", hover_name="county",
        hover_data={"level": True, "meaning": True, "fips": False, "severity": False},
        color_continuous_scale=steps, range_color=[-0.5, 5.5], labels={"level": "Worst level", "meaning": "Meaning"},
    )
    droughtMap.update_geos(fitbounds="locations", visible=False, projection_type="mercator", bgcolor="rgba(0,0,0,0)")
    droughtMap.update_traces(marker_line_width=0.3, marker_line_color="#10151b")
    droughtMap.update_layout(height=460, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)",
                             coloraxis_colorbar=dict(title="Worst level", tickvals=list(range(6)), ticktext=DROUGHT_LABELS))
    droughtMap.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 650
    droughtMap.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 250
    st.plotly_chart(droughtMap, width="stretch")
except Exception as error:
    st.warning(f"The drought map could not be drawn: {error}")

st.subheader("How to use this site")
st.markdown(
    """
1. **County risk** - ranked county cards for any of the four states and crops, each county's drought and
   loss history, and a 3D view with a 2000-2025 year slider and a map of all four states. Real records only.
2. **Scenarios** - enter a county, crop, year (up to 2030) and drought level to see the expected loss and
   the closest historical years. An illustration, not a weather forecast.
3. **Budget allocation** - split a fund across counties under a chosen rule and trigger.
4. **Method and data** - how the numbers are made, what is filtered out, and the limits.
5. **Credits** - data sources, tools, and how AI was used.
"""
)

try:
    cornHistory = getIowaCornHistory()
    reportedHistory = cornHistory.loc[cornHistory["yield_status"] == "reported"]
    meanYield = reportedHistory.groupby("year", as_index=False)["yield_per_acre"].mean()
    yieldChart = px.area(
        meanYield, x="year", y="yield_per_acre", markers=True,
        labels={"year": "Year", "yield_per_acre": "Mean reported yield (bu/acre)"},
        title="Iowa corn: mean reported county yield (the 2012 drought stands out)",
    )
    yieldChart.update_traces(line_color="#f0b429", fillcolor="rgba(240,180,41,0.15)")
    yieldChart.update_yaxes(rangemode="tozero")
    st.plotly_chart(yieldChart, width="stretch")
    st.caption("A descriptive mean of counties with a reported yield in each year. "
               "Years without a reported yield are left out, never counted as zero.")
except Exception as error:
    st.error(f"The supplied Iowa corn data could not be loaded: {error}")
