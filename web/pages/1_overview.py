"""Overview: who the tool is for, the decision, how to use the site, and the data behind it."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data import loadIowaCornHistory
from web.ui import applyStyle, showVideo


@st.cache_data(show_spinner=False)
def getIowaCornHistory() -> pd.DataFrame:
    """Cache the supplied Iowa corn history for the overview page."""
    return loadIowaCornHistory()


applyStyle()
st.title("Drought Relief Allocation Planner")
showVideo("intro_loop.mp4", caption="Illustrative animation (AI-generated, Higgsfield). Not data.")

st.markdown(
    """
**Who it is for:** a state drought-relief budget officer in Iowa.

**The decision:** on **August 15**, how to split a fixed relief fund across counties, using what is
known about the season by that date.

**What the tool shows:** for each county, how often severe drought hits (exposure), how much corn
yield it loses when it does (vulnerability), and what that costs in dollars (an estimated crop
loss, not a program payout).
"""
)

st.subheader("How to use this site")
st.markdown(
    """
1. **County risk** - ranked county cards, each county's drought and loss history, and a 3D view
   with a 2000-2025 year slider and a state map. Real records only.
2. **Scenarios** - enter a county, crop, year (up to 2030) and drought level to see the expected
   loss and the closest historical years. An illustration, not a weather forecast.
3. **Budget allocation** - split a fund across counties under a chosen rule and trigger.
4. **Method and data** - how the numbers are made, what is filtered out, and the limits.
5. **Credits** - data sources, tools, and how AI was used.
"""
)

st.subheader("The data")
st.write(
    "26 years (2000-2025) of real county records: USDA NASS corn and soybean yields and acres, "
    "U.S. Drought Monitor weekly drought maps, NOAA ACIS daily weather, and USDA NRCS soil data. "
    "Full credits are on the Credits page."
)

try:
    cornHistory = getIowaCornHistory()
except Exception as error:
    st.error(f"The supplied Iowa corn data could not be loaded: {error}")
    st.stop()

reportedHistory = cornHistory.loc[cornHistory["yield_status"] == "reported"]
if reportedHistory.empty:
    st.info("No reported Iowa corn yields are available in the supplied data.")
    st.stop()

countyColumn, yearColumn, recordColumn = st.columns(3)
countyColumn.metric("Iowa counties", cornHistory["fips"].nunique())
yearColumn.metric("Years", cornHistory["year"].nunique())
recordColumn.metric("Reported county-years (corn)", f"{len(reportedHistory):,}")

meanYield = reportedHistory.groupby("year", as_index=False)["yield_per_acre"].mean()
yieldChart = px.line(
    meanYield, x="year", y="yield_per_acre", markers=True,
    labels={"year": "Year", "yield_per_acre": "Mean reported yield (bu/acre)"},
    title="Iowa corn: mean reported county yield (the 2012 drought stands out)",
)
st.plotly_chart(yieldChart, width="stretch")
st.caption(
    "A descriptive mean of counties with a reported yield in each year. "
    "Years without a reported yield are left out, never counted as zero."
)
