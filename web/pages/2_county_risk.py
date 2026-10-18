"""Explore 3D: the 3D viewer inline, then counties ranked by expected annual loss (all four states).

Reads the 2000-2025 records directly (no model): every number is what the data says.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from web.render3d import CROPS, DEFAULT_FIPS, STATES, loadCountyHistory, showViewer
from web.ui import (AMBER, CROP_NAMES, DROUGHT_COLORS, DROUGHT_LABELS, LOSS_LABEL, MUTED, NO_DATA_COLOR,
                    droughtLabel, eyebrow, markdownSafe, money, priceInput)


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


def openInViewer(fips: str) -> None:
    st.session_state["focusFips"] = fips


def countyCard(row) -> None:
    # The "cardhover" key gives the container a CSS class, which web/ui.py uses for the card style and hover lift.
    with st.container(key=f"cardhover_{row.fips}"):
        st.markdown(f"**#{row['rank']} {row.county}**")
        st.metric("Expected loss per year", money(row.expected_loss),
                  help="Exposure x average dollar loss in a D2+ year")
        st.markdown(f"Exposure **{row.exposure:.0%}** · Vulnerability **{row.vulnerability_pct:.1f}%** below trend",
                    help="Exposure: share of years at D2 or worse. Vulnerability: average loss in those years.")
        st.caption(reasonLine(row))
        st.button("Open in 3D", key=f"open_{row.fips}", on_click=openInViewer, args=(row.fips,),
                  icon=":material/view_in_ar:", width="stretch")


def historyCharts(county: pd.DataFrame, price: float, crop: str) -> None:
    """Drought level and estimated cost by year, side by side. Missing years are labeled gaps."""
    county = county.assign(cost=county["loss_bu"] * county["acres_planted"] * price)
    noData = county.loc[county["loss_pct"].isna(), "year"].tolist()
    left, right = st.columns(2)
    with left:
        levels = county["max_severity"]
        fig = go.Figure(go.Bar(
            x=county["year"], y=levels,
            marker_color=[DROUGHT_COLORS[int(v)] if pd.notna(v) else NO_DATA_COLOR for v in levels],
            hovertext=[droughtLabel(v) for v in levels], hoverinfo="x+text",
        ))
        fig.add_hline(y=D2_OR_WORSE - 0.5, line_dash="dash", line_color=MUTED, annotation_text="D2+")
        fig.update_layout(title=f"Worst drought level in the {CROP_NAMES[crop].lower()} season", height=320, margin=dict(t=40, b=30),
                          yaxis=dict(tickvals=list(range(6)), ticktext=DROUGHT_LABELS, range=[0, 5.5]))
        st.plotly_chart(fig, width="stretch")
    with right:
        fig = go.Figure(go.Bar(
            x=county["year"], y=county["cost"], marker_color=AMBER,
            hovertext=[f"{p:.1f}% below trend" if pd.notna(p) else "No data" for p in county["loss_pct"]],
            hoverinfo="x+y+text",
        ))
        for year in noData:  # gaps are labeled, never drawn as zero
            fig.add_annotation(x=year, y=0, text="No data", textangle=-90, yanchor="bottom",
                               showarrow=False, font=dict(size=10, color=MUTED, family="JetBrains Mono"))
        fig.update_layout(title=f"Estimated cost by year ({LOSS_LABEL})", height=320,
                          yaxis_tickprefix="$", margin=dict(t=40, b=30))
        st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

eyebrow("EXPLORE 3D")
st.title("Every county, every season since 2000.")
st.caption("Drag the year strip or press Play: the diorama, the drought level and the dollar figure follow. "
           "Real 2000-2025 records; the scene itself is an illustration.")

stateColumn, cropColumn, priceColumn = st.columns([2, 2, 2])
state = stateColumn.selectbox("State", list(STATES), index=list(STATES).index("IA"), format_func=STATES.get)
crop = cropColumn.selectbox("Crop", CROPS, format_func=CROP_NAMES.get)
price = priceInput(crop, where=priceColumn)
try:
    summary = countySummary(price, state, crop)
    history = loadCountyHistory(state, crop)
except Exception as error:
    st.error(f"The county records could not be loaded, so this page cannot show results: {error}")
    st.stop()
if summary.empty:
    st.info(f"There are no {CROP_NAMES[crop].lower()} records for {STATES[state]} in the dataset.")
    st.stop()

# The county shown in the viewer: a card's "Open in 3D" choice, else Mahaska County (Iowa), else the top-ranked county.
order = summary["fips"].tolist()
focus = st.session_state.get("focusFips")
if focus not in order:
    focus = DEFAULT_FIPS if DEFAULT_FIPS in order else order[0]
showViewer("history", focus, startYear=2012, crop=crop, price=price)

st.subheader("Counties ranked by expected annual loss")
ranked = summary[summary["expected_loss"].notna()]
st.caption(markdownSafe(
    f"{STATES[state]} {CROP_NAMES[crop].lower()}. Expected loss = exposure x average dollar loss in a D2+ year, at "
    f"${price:.2f}/bu (assumed). Loss is yield below each county's 2000-2025 linear trend (hindsight, uses all years); "
    f"{LOSS_LABEL}. Never ranked by average yield_anomaly_pct. {len(ranked)} of {len(summary)} counties have enough "
    f"reported yields in drought years to rank."))
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

names = summary.set_index("fips")["county"]
st.subheader(f"{names[focus]} by year")
row = summary[summary["fips"] == focus].iloc[0]
st.write(reasonLine(row))
historyCharts(history[history["fips"] == focus], price, crop)
