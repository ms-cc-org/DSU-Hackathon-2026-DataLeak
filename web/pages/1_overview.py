"""Project overview and a real, descriptive Iowa corn yield chart."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data import loadIowaCornHistory


@st.cache_data
def getIowaCornHistory() -> pd.DataFrame:
    """Cache the supplied Iowa corn history for the overview page."""
    return loadIowaCornHistory()


st.title("Drought Relief Allocation Planner")
st.write(
    "A planning tool for an Iowa drought-relief budget officer deciding how much "
    "support counties may need and how a fund could be allocated on August 15."
)
st.warning(
    "Project scaffold: the chart below shows reported history. Loss predictions, "
    "funding recommendations, validation results, and the satellite map are not built yet."
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
countyColumn.metric("Counties in dataset", cornHistory["fips"].nunique())
yearColumn.metric("Years", cornHistory["year"].nunique())
recordColumn.metric("Reported county-years", len(reportedHistory))

meanYield = reportedHistory.groupby("year", as_index=False)["yield_per_acre"].mean()
yieldChart = px.line(
    meanYield,
    x="year",
    y="yield_per_acre",
    labels={"year": "Year", "yield_per_acre": "Mean reported yield (bu/acre)"},
    title="Iowa corn: mean reported county yield",
)
st.plotly_chart(yieldChart, width="stretch")
st.caption(
    "This is a descriptive mean of counties with reported yields in each year. "
    "It is not a prediction or an estimate of crop-value loss."
)
