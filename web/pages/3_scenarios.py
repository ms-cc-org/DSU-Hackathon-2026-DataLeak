
"""Superseded by the Planner tab (web/pages/3_planner.py); kept on disk, not registered in app.py."""
=======
"""Historical-footprint scenario UI backed by the fitted Lane 2 engine."""


from __future__ import annotations

import pandas as pd
import streamlit as st

from src.engine import scenario
from src.data_loader import load_counties
from web.ui import markdownSafe


@st.cache_data(show_spinner=False)
def iowaCountyChoices() -> dict[str, str]:
    """Return county labels keyed by five-character FIPS."""
    boundaries = load_counties()
    return {
        str(feature["id"]).zfill(5): str(feature["properties"]["county_name"])
        for feature in boundaries["features"]
        if feature["properties"]["state_alpha"] == "IA"
    }


def moneyValue(value: float) -> str:
    """Format one estimated dollar amount for display."""
    return f"${value:,.0f}"


def showCountyTable(table: pd.DataFrame) -> None:
    """Show the state universe and its model flags without changing estimates."""
    displayTable = table[
        ["county", "fips", "X_payout_usd", "Y_deductible_exposure_usd",
         "Z_relief_95pct_usd", "out_of_range"]
    ].sort_values("X_payout_usd", ascending=False)
    st.dataframe(
        displayTable,
        hide_index=True,
        width="stretch",
        column_config={
            "county": "County",
            "fips": "FIPS",
            "X_payout_usd": st.column_config.NumberColumn("X · estimated insurance payouts", format="dollar"),
            "Y_deductible_exposure_usd": st.column_config.NumberColumn("Y · deductible exposure", format="dollar"),
            "Z_relief_95pct_usd": st.column_config.NumberColumn("Z · illustrative 95% relief", format="dollar"),
            "out_of_range": "Beyond training range",
        },
    )


st.title("Historical drought scenarios")
st.caption(
    "Iowa corn · August 15 inputs · model D. Choose a base year for insured exposure "
    "and a historical year whose drought and weather conditions are applied as a footprint. "
    "This is a scenario, not a weather forecast."
)

countyChoices = iowaCountyChoices()
countyNames = {"all": "All Iowa counties"}
countyNames.update(countyChoices)

inputColumns = st.columns(3)
with inputColumns[0]:
    baseYear = st.selectbox("Base year · insured values", list(range(2000, 2026)),
                            index=23, help="Liability, insured acres, coverage, soil and history stay with this year.")
with inputColumns[1]:
    footprintYear = st.selectbox("Drought and weather footprint", list(range(2000, 2026)),
                                 index=12, help="All modeled drought and weather fields come from this historical year.")
with inputColumns[2]:
    selectedCounty = st.selectbox("Apply footprint to", list(countyNames),
                                  format_func=countyNames.get,
                                  help="Choose one county or apply the footprint statewide. Other counties keep base-year conditions.")

scaleColumns = st.columns(2)
with scaleColumns[0]:
    acresScale = st.number_input("Insured-acre multiplier", min_value=0.1, max_value=10.0,
                                 value=1.0, step=0.1,
                                 help="Scales displayed dollars after prediction; it does not change model inputs.")
with scaleColumns[1]:
    priceScale = st.number_input("Crop-value multiplier", min_value=0.1, max_value=10.0,
                                 value=1.0, step=0.1,
                                 help="Scales displayed dollars after prediction; it does not change model inputs.")

try:
    result = scenario(
        base_year=baseYear,
        footprint_year=footprintYear,
        state="IA",
        crop="CORN",
        counties=None if selectedCounty == "all" else [selectedCounty],
        acres_scale=acresScale,
        price_scale=priceScale,
    )
except (FileNotFoundError, ValueError) as error:
    st.error(f"Scenario could not be calculated: {error}")
    st.stop()

stateTotals = result["statewide_totals"]
metricColumns = st.columns(3)
metricColumns[0].metric("X · estimated insurance payouts", moneyValue(stateTotals["X_payout_usd"]))
metricColumns[1].metric("Y · estimated deductible exposure", moneyValue(stateTotals["Y_deductible_exposure_usd"]))
metricColumns[2].metric("Z · illustrative 95% relief", moneyValue(stateTotals["Z_relief_95pct_usd"]))
st.caption(
    "X is the headline estimate. Y is deductible exposure. Z illustrates a 95% coverage "
    "assumption; it is not an official USDA or state payment forecast."
)

historicalRange = result["historical_scenario_range_x_usd"]
st.markdown(markdownSafe(
    f"**Rough historical range for statewide X:** "
    f"{moneyValue(historicalRange['low_usd'])}–{moneyValue(historicalRange['high_usd'])}. "
    "Based on model C's historical neighbors; this is not a calibrated probability interval."
))

if selectedCounty != "all":
    focusedRow = result["county_table"].loc[result["county_table"]["fips"].eq(selectedCounty)].iloc[0]
    st.subheader(str(focusedRow["county"]))
    st.markdown(markdownSafe(
        f"Estimated payout X: **{moneyValue(focusedRow['X_payout_usd'])}** · "
        f"damaged-acre share: **{focusedRow['pred_damaged_acre_share']:.1%}** · "
        f"insured liability in the base year: **{moneyValue(focusedRow['liability'])}**."
    ))

rangeSummary = result["out_of_range_summary"]
if rangeSummary["county_crop_rows_flagged"]:
    st.warning(
        f"{rangeSummary['county_crop_rows_flagged']} of {rangeSummary['total_county_crop_rows']} "
        "county rows have features beyond the full model's training range. "
        "Inspect the county table before using these estimates."
    )

st.subheader("County estimates")
showCountyTable(result["county_table"])
st.subheader("Closest historical years")
st.caption("Ranked by model C's liability-weighted neighbor similarity; these are examples, not probabilities.")
st.dataframe(pd.DataFrame(result["closest_historical_years"])[["year", "neighbor_matches"]],
             hide_index=True, width="stretch",
             column_config={"year": "Year", "neighbor_matches": "Neighbor matches"})
