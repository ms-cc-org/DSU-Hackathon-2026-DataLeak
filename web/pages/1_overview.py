"""Story: the user, the decision and the method in three chapters, beside a real drought map."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import load_counties, load_master
from web.render3d import STATES, loadSeasonPeak
from web.ui import DROUGHT_COLORS, DROUGHT_LABELS, DROUGHT_WORDS, GROUND, animatedStats, duskHero, showVideo


PAGE_CSS = """
<style>
/* CTAs sit over the lower part of the hero frame */
.st-key-heroCtas { margin-top: -300px; margin-left: clamp(20px, 5vw, 64px); margin-right: 16px; position: relative;
  z-index: 3; margin-bottom: 218px; flex-wrap: wrap; width: auto; max-width: calc(100% - 36px); }
@media (max-width: 640px) { .st-key-heroCtas { flex-direction: column; align-items: flex-start; } }
/* Chapters scroll on the left while the map stays pinned on the right (wide screens only) */
@media (min-width: 900px) {
  [data-testid="stHorizontalBlock"]:has(.st-key-stickymap) { align-items: flex-start; }
  [data-testid="stColumn"]:has(.st-key-stickymap) { position: sticky; top: 84px; }
}
.drChapter { min-height: 300px; padding: 8px 0 28px; border-top: 1px solid #26313B; }
.drChapterNum { font: 500 2.4rem "JetBrains Mono", ui-monospace, monospace; color: #F2A33A; }
.drChapter h3 { font-family: "Bricolage Grotesque", "DM Sans", sans-serif; font-size: 1.9rem; line-height: 1.15; margin: .3rem 0 .6rem; }
.drChapter p { color: #B9C0C7; font-size: 1.05rem; line-height: 1.6; max-width: 460px; }
</style>
"""


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


def chapter(number: str, headline: str, copy: str) -> None:
    st.html(f'<div class="drChapter"><div class="drChapterNum">{number}</div><h3>{headline}</h3><p>{copy}</p></div>')

def droughtMap() -> None:
    """The animated 2000-2025 drought map with its state switch (real weekly Drought Monitor data)."""
    scope = st.segmented_control("State", list(STATES), default="IA", format_func=STATES.get,
                                 key="storyScope") or "IA"
    drought = growingSeasonDrought()
    geo = load_counties()
    features = [f for f in geo["features"] if f["properties"]["state_alpha"] in STATES
                and f["properties"]["state_alpha"] == scope]
    names = {f["id"]: f"{f['properties']['county_name']}, {f['properties']['state_alpha']}" for f in features}
    shown = drought[drought["fips"].isin(names)].copy()
    shown["county"] = shown["fips"].map(names)
    shown["meaning"] = shown["severity"].map(lambda s: DROUGHT_WORDS[int(s)])
    # One numeric trace per frame with a stepped color scale (one band per drought level), so every
    # level shows in every year. Categorical colors would drop levels absent from the first frame.
    steps = []
    for k, color in enumerate(DROUGHT_COLORS):
        steps += [(k / 6, color), ((k + 1) / 6, color)]
    fig = px.choropleth(
        shown, geojson={"type": "FeatureCollection", "features": features}, locations="fips", featureidkey="id",
        color="severity", animation_frame="year", hover_name="county",
        hover_data={"level": True, "meaning": True, "fips": False, "severity": False},
        color_continuous_scale=steps, range_color=[-0.5, 5.5], labels={"level": "Worst level", "meaning": "Meaning"},
    )

    fig.update_geos(fitbounds="locations", visible=False, projection_type="mercator", bgcolor="rgba(0,0,0,0)")
    fig.update_traces(marker_line_width=0.4, marker_line_color=GROUND)
    fig.update_layout(height=470, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="DM Sans, sans-serif"),
                      coloraxis_colorbar=dict(title="Worst level", tickvals=list(range(6)), ticktext=DROUGHT_LABELS))
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 650
    fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 250
    st.plotly_chart(fig, width="stretch")
    st.caption("Each frame is one growing season (May 1 to Sep 30), colored by the worst U.S. Drought Monitor level "
               "reached in each county. Real weekly maps for all 253 counties.")



# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.html(PAGE_CSS)

if not showVideo("intro_loop.mp4", caption="Illustrative animation (AI-generated). Not data."):
    duskHero("DROUGHT ASSISTANCE TARGETING · FOUR STATES · FOUR CROPS", "Where does the relief go first?",
             "Explore county crop history across the dataset and test drought conditions before an August 15 "
             "funding decision.")
    with st.container(key="heroCtas", horizontal=True, gap="small"):
        with st.container(key="ctaprimary", width="content"):
            st.page_link("web/pages/2_county_risk.py", label="Explore in 3D", icon=":material/view_in_ar:")
        with st.container(key="ctasecondary", width="content"):
            st.page_link("web/pages/3_planner.py", label="Open the planner", icon=":material/tune:")
st.page_link("web/pages/3_scenarios.py", label="View insurance predictions", icon=":material/arrow_forward:")
st.caption("Model D predicts insurance payout share and damaged-acre share for Iowa/Nebraska corn and soybeans. "
           "The all-crop Planner uses a separate historical crop-loss lookup; fund allocations are policy arithmetic.")


try:
    counts = datasetCounts()
    animatedStats([("years of records", counts["years"], ""), ("counties", counts["counties"], ""),
                   ("states", counts["states"], ""), ("reported yields", counts["reported"], "")])
except Exception as error:
    st.warning(f"Dataset counts are unavailable: {error}")

chapters, mapColumn = st.columns([5, 7], gap="large")
with chapters:
    chapter("01", "Measure each year against its own county.",
            "Each county's yield is compared with its own 2000-2025 trend, so a bad year shows up as a "
            "shortfall below what that county normally grows, not as a naturally low-yield county. Years "
            "without a reported yield stay blank, never zero.")
    chapter("02", "Turn the shortfall into dollars.",
            "Estimated crop-value loss = trend yield x loss % x planted acres x price. The price is an "
            "editable assumption, and crop-value loss is not a relief payment.")
    chapter("03", "Split a fixed fund on August 15.",
            "Set one state fund and share it across all supported crops in proportion to estimated crop-value "
            "loss. Review county totals, crop shares and unavailable estimates in the Planner. These are "
            "illustrative allocations from the prototype lookup, not official relief payments.")
with mapColumn:
    with st.container(key="stickymap"):
        try:
            droughtMap()
        except Exception as error:
            st.warning(f"The drought map could not be drawn: {error}")

st.html('<div class="drFooter">Data: USDA NASS · U.S. Drought Monitor · NOAA ACIS · NRCS SSURGO · MODIS<br>'
        'AI use and full credits: see the README</div>')
