"""Evidence: method and data notes (filters, missing values, definitions, coverage, validation, limits), then credits."""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.data_loader import load_master
from web.credits import renderCredits
from web.ui import eyebrow


REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "analysis" / "validation" / "results"
COVERAGE_FILE = REPO_ROOT / "docs" / "coverage.csv"


@st.cache_data(show_spinner=False)
def coverageTable() -> pd.DataFrame:
    """Counties with a reported yield, by state, crop and year. Uses docs/coverage.csv if Lane 1 saved one."""
    if COVERAGE_FILE.exists():
        return pd.read_csv(COVERAGE_FILE)
    master = load_master()
    reported = master[master["yield_status"] == "reported"]
    table = pd.crosstab([reported["state_alpha"], reported["crop"]], reported["year"])
    keep = [y for y in table.columns if y % 5 == 0 or y == 2025]
    table = table[keep].reset_index().rename(columns={"state_alpha": "State", "crop": "Crop"})
    table.columns = [str(c) for c in table.columns]  # years as text headers
    return table


eyebrow("EVIDENCE")
st.title("How the numbers are made.")
st.write("Filters, definitions, coverage, validation results and limits, then the credits. Every number in the app "
         "comes from the supplied records or the documented prototype lookup.")

st.subheader("The decision and the cutoff")
st.write(
    "The budget officer decides on **August 15**. Anything used to estimate a season must be known "
    "by that date: drought levels in the Planner and the viewer's Scenario mode come only from weekly Drought Monitor maps "
    "dated from the crop's season start to August 15 (May 1 for corn and soybeans, June 1 for sorghum). "
    "Winter wheat is harvested before August 15, so its level covers its whole season (September to June). "
    "The master table's season totals are used only to describe past years on the Explore 3D tab."
)

st.subheader("Filters and missing values")
st.markdown(
    """
- **Geography and crops:** all four states in the dataset (California, Delaware, Iowa, Nebraska) and all four
  crops (corn, soybeans, winter wheat, sorghum). Iowa corn is the default view because it has the best coverage
  and Iowa is rainfed. 23 counties in the boundary file have no records and show as "No data".
- **County codes:** FIPS is kept as 5-character text, so codes never lose a leading zero.
- **Yields:** only rows with `yield_status == "reported"` count. A missing yield is never filled with
  zero: it shows as "No data" (a gap in charts, bare grey soil in the 3D scene).
- **Trends:** a county's linear yield trend needs at least 10 reported years.
- **Drought scale:** the master's `max_drought_severity` runs 0-5 and is shifted by one
  (0 = none, 1 = D0, 4 = D3, 5 = D4). One helper converts it to labels everywhere.
"""
)

st.subheader("Definitions")
st.markdown(
    """
- **Loss %:** how far a year's yield fell below the county's 2000-2025 linear trend, floored at zero.
  The trend uses all years, so history views are hindsight; the walk-forward backtest refits trends on
  earlier years only.
- **Estimated crop loss ($):** bushels below trend x planted acres x price. The price is an editable
  assumption. This is an estimated crop loss, not an insurance claim or a program payout.
- **Exposure:** share of years whose worst drought level reached D2 or worse.
- **Vulnerability:** average loss % in those D2+ years.
- **Expected annual loss:** exposure x average dollar loss in a D2+ year.
- **Scenario years 2026-2030:** the trend yield is a linear extension of the county's 2000-2025 trend.
  Nothing beyond 2030 is offered.
"""
)

st.subheader("Coverage: counties with a reported yield")
try:
    st.dataframe(coverageTable(), hide_index=True, width="stretch")
    st.caption("Reported yields thin out in recent years (for example 2025) and are sparse for California, Delaware, "
               "sorghum and wheat outside Nebraska, so results there rest on few counties.")
except Exception as error:
    st.warning(f"Coverage could not be computed: {error}")

st.subheader("Validation: walk-forward backtest")
results = sorted(RESULTS_DIR.glob("*.csv")) if RESULTS_DIR.exists() else []
charts = sorted(RESULTS_DIR.glob("*.png")) if RESULTS_DIR.exists() else []
if results or charts:
    st.write("For each test year the method trains on earlier years only, refits trends in each window, "
             "and uses features clipped to August 15.")
    for chart in charts:
        st.image(str(chart), caption=chart.stem.replace("_", " "), width="stretch")
    for result in results:
        with st.expander(result.stem.replace("_", " ")):
            st.dataframe(pd.read_csv(result), hide_index=True, width="stretch")
else:
    st.info("The walk-forward backtest results are not saved yet. They will appear here from "
            "analysis/validation/results/ once the backtest has run.")

st.subheader("Limits")
st.markdown(
    """
- County averages only: nothing at field level. The 3D scene is illustrative, not a map of fields.
- Irrigation is not in the master table. Iowa is rainfed; Nebraska is about half irrigated and California almost
  fully, so drought losses there can look smaller for reasons the data cannot show.
- Drought explains only part of yield loss: some large losses (for example Mahaska County corn in 2010)
  came in years without D2+ drought.
- The scenario numbers come from a prototype lookup of similar past years (`web/scenario_lookup.py`), not a
  validated model. The user picks the drought level; nothing predicts drought or weather.
- Data ends in 2025.
"""
)

st.divider()
eyebrow("CREDITS")
st.title("Sources, tools and AI use.")
renderCredits()
