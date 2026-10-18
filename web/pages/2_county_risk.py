"""Mode 1 - County risk: ranked county cards, history charts, and the 3D year viewer (all four states).

Reads the 2000-2025 records directly (no model): every number is what the data says.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from web.render3d import CROPS, DEFAULT_FIPS, STATES, loadCountyHistory, showViewer
from web.ui import (CROP_NAMES, DROUGHT_COLORS, DROUGHT_LABELS, LOSS_LABEL, droughtLabel, markdownSafe,
                    money, priceInput, showImage)


D2_OR_WORSE = 3  # shifted scale: 3 = D2


@st.cache_data(show_spinner=False)
def countySummary(price: float, state: str, crop: str) -> pd.DataFrame:
    """Exposure, vulnerability and expected annual loss per county, ranked by expected loss.

    exposure      = share of years whose worst drought level reached D2 or worse
    vulnerability = average yield shortfall below trend in those D2+ years (reported yields only)
    expected loss = exposure x average dollar loss in a D2+ year
    Counties are never ranked by average yield_anomaly_pct.
    """
    history = loadCountyHistory(state, crop).copy()
    if history.empty:  # this state does not grow this crop (for example California soybeans)
        return pd.DataFrame()
    history["cost"] = history["loss_bu"] * history["acres_planted"] * price
    rows = []
    for fips, group in history.groupby("fips"):
        withDrought = group[group["max_severity"].notna()]
        droughtYears = withDrought[withDrought["max_severity"] >= D2_OR_WORSE]
        withYield = droughtYears[droughtYears["loss_pct"].notna()]
        exposure = len(droughtYears) / len(withDrought) if len(withDrought) else float("nan")
        rows.append({
            "fips": fips,
            "county": group["county_name"].iloc[0],
            "exposure": exposure,
            "vulnerability_pct": withYield["loss_pct"].mean(),
            "expected_loss": exposure * withYield["cost"].mean() if len(withYield) else float("nan"),
            "drought_years": len(droughtYears),
            "years": len(withDrought),
            "reported_years": int(group["yield"].notna().sum()),
            "aws_mm": group["aws_mm"].iloc[0],
        })
    summary = pd.DataFrame(rows).sort_values("expected_loss", ascending=False, na_position="last")
    summary["rank"] = range(1, len(summary) + 1)
    return summary.reset_index(drop=True)


def reasonLine(row) -> str:
    if pd.isna(row.vulnerability_pct):
        return f"D2+ drought in {row.drought_years} of {row.years} seasons; no reported yield in those seasons."
    return (f"D2+ drought in {row.drought_years} of {row.years} seasons; in those seasons yield averaged "
            f"{row.vulnerability_pct:.1f}% below trend.")


def countyCard(row) -> None:
    # The "card" key gives the container a CSS class, which web/ui.py uses for the hover lift.
    with st.container(border=True, key=f"card_{row.fips}"):
        st.markdown(f"**#{row['rank']} {row.county}**")
        st.metric("Expected loss per year", money(row.expected_loss),
                  help="Exposure x average dollar loss in a D2+ year")
        st.markdown(f"Exposure **{row.exposure:.0%}** · Vulnerability **{row.vulnerability_pct:.1f}%** below trend",
                    help="Exposure: share of years at D2 or worse. Vulnerability: average loss in those years.")
        st.caption(reasonLine(row))


def historyCharts(county: pd.DataFrame, price: float, crop: str) -> None:
    """Drought level and estimated cost by year, side by side. Missing years are labeled gaps."""
    county = county.assign(cost=county["loss_bu"] * county["acres_planted"] * price)
    noData = county.loc[county["loss_pct"].isna(), "year"].tolist()
    left, right = st.columns(2)
    with left:
        levels = county["max_severity"]
        fig = go.Figure(go.Bar(
            x=county["year"], y=levels,
            marker_color=[DROUGHT_COLORS[int(v)] if pd.notna(v) else "#a0a0a0" for v in levels],
            hovertext=[droughtLabel(v) for v in levels], hoverinfo="x+text",
        ))
        fig.add_hline(y=D2_OR_WORSE - 0.5, line_dash="dash", annotation_text="D2+")
        fig.update_layout(title=f"Worst drought level in the {CROP_NAMES[crop].lower()} season", height=320, margin=dict(t=40, b=30),
                          yaxis=dict(tickvals=list(range(6)), ticktext=DROUGHT_LABELS, range=[0, 5.5]))
        st.plotly_chart(fig, width="stretch")
    with right:
        fig = go.Figure(go.Bar(
            x=county["year"], y=county["cost"], marker_color="#b5452f",
            hovertext=[f"{p:.1f}% below trend" if pd.notna(p) else "No data" for p in county["loss_pct"]],
            hoverinfo="x+y+text",
        ))
        for year in noData:  # gaps are labeled, never drawn as zero
            fig.add_annotation(x=year, y=0, text="No data", textangle=-90, yanchor="bottom",
                               showarrow=False, font=dict(size=10, color="gray"))
        fig.update_layout(title=f"Estimated cost by year ({LOSS_LABEL})", height=320,
                          yaxis_tickprefix="$", margin=dict(t=40, b=30))
        st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.title("County risk")
st.write("Which counties lose the most crop value when drought hits? Ranked from the 2000-2025 records.")
showImage("hero_field.jpg")

stateColumn, cropColumn = st.columns(2)
state = stateColumn.selectbox("State", list(STATES), index=list(STATES).index("IA"), format_func=STATES.get)
crop = cropColumn.selectbox("Crop", CROPS, format_func=CROP_NAMES.get)
price = priceInput(crop)
try:
    summary = countySummary(price, state, crop)
    history = loadCountyHistory(state, crop)
except Exception as error:
    st.error(f"The county records could not be loaded, so this page cannot show results: {error}")
    st.stop()
if summary.empty:
    st.info(f"There are no {CROP_NAMES[crop].lower()} records for {STATES[state]} in the dataset.")
    st.stop()

ranked = summary[summary["expected_loss"].notna()]
st.subheader(f"Highest expected drought loss - {STATES[state]} {CROP_NAMES[crop].lower()}")
st.caption(markdownSafe(
    f"Expected loss = exposure x average dollar loss in a D2+ year, at ${price:.2f}/bu (assumed). "
    f"Loss is yield below each county's 2000-2025 linear trend (hindsight, uses all years); {LOSS_LABEL}. "
    f"{len(ranked)} of {len(summary)} counties have enough reported yields in drought years to rank."))
top = ranked.head(6)
for start in range(0, len(top), 3):
    for column, (_, row) in zip(st.columns(3), top.iloc[start:start + 3].iterrows()):
        with column:
            countyCard(row)

with st.expander(f"All {len(summary)} counties, ranked"):
    table = summary[["rank", "county", "exposure", "vulnerability_pct", "expected_loss", "drought_years", "reported_years"]]
    st.dataframe(
        table, hide_index=True, width="stretch",
        column_config={
            "exposure": st.column_config.NumberColumn("Exposure", format="percent"),
            "vulnerability_pct": st.column_config.NumberColumn("Vulnerability (% below trend)", format="%.1f"),
            "expected_loss": st.column_config.NumberColumn("Expected loss ($/yr)", format="dollar"),
            "drought_years": "D2+ years", "reported_years": "Years with reported yield",
        },
    )

st.subheader("County history")
names = summary.set_index("fips")["county"]
order = summary["fips"].tolist()
fips = st.selectbox("County", order, index=order.index(DEFAULT_FIPS) if DEFAULT_FIPS in order else 0,
                    format_func=lambda f: f"{names[f]} (#{order.index(f) + 1})")
row = summary[summary["fips"] == fips].iloc[0]
st.write(reasonLine(row))
historyCharts(history[history["fips"] == fips], price, crop)

st.subheader("3D view")
st.caption("Opens the county diorama with a 2000-2025 year slider and a map of all four states (253 counties). "
           "Illustrative scene - not a map of fields; the data has no field-level detail.")
if st.button("Visualize", type="primary"):
    st.session_state["showViewer"] = True
if st.session_state.get("showViewer"):
    showViewer("history", fips, startYear=2012, crop=crop, price=price)
