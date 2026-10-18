"""Planner: estimates crop-value loss for one county under a chosen drought scenario.

Uses web/scenario_lookup.py (a prototype lookup, not a validated model), the same method and numbers as
the 3D viewer's Scenario mode.
"""

import pandas as pd
import streamlit as st

from web.render3d import CROPS, DEFAULT_FIPS, LAST_YEAR, LAST_PROJECTED_YEAR, STATES, loadCountyHistory
from web.scenario_lookup import LEVELS, countyRecords, scenario
from web.ui import CROP_NAMES, DEFAULT_PRICE, DROUGHT_COLORS, eyebrow, markdownSafe, money


PAGE_CSS = """
<style>
.drRange { font: 500 clamp(28px, 4vw, 44px)/1.1 "JetBrains Mono", ui-monospace, monospace; color: #F2A33A; }
.drRangeNote { color: #B9C0C7; margin: 4px 0 14px; }
.drProb { display: flex; align-items: center; gap: 8px; margin: 5px 0; font: 12.5px "JetBrains Mono", monospace; }
.drProb .track { flex: 1; height: 10px; background: #0E1318; border-radius: 999px; overflow: hidden; border: 1px solid #26313B; }
.drProb .fill { height: 100%; border-radius: 999px; }
.drWarn { background: rgba(242,163,58,.12); border: 1px solid rgba(242,163,58,.5); border-radius: 14px; padding: 10px 12px; margin: 6px 0 12px; }
@media (min-width: 900px) { .st-key-cardInputs { max-width: 460px; } }
</style>
"""

@st.cache_data(show_spinner=False)
def countyOptions() -> pd.DataFrame:
    """Counties with records for at least one crop, sorted by state then name."""
    frames = [loadCountyHistory(None, crop)[["fips", "county_name", "state_alpha"]].drop_duplicates() for crop in CROPS]
    counties = pd.concat(frames).drop_duplicates("fips")
    return counties.sort_values(["state_alpha", "county_name"]).reset_index(drop=True)


def probabilityBars(probs: list[float]) -> None:
    rows = "".join(
        f'<div class="drProb"><span style="width:26px">{level}</span><div class="track">'
        f'<div class="fill" style="width:{100 * p:.0f}%; background:{DROUGHT_COLORS[b + 1]}"></div></div>'
        f'<span style="width:38px;text-align:right">{100 * p:.0f}%</span></div>'
        for b, (level, p) in enumerate(zip(LEVELS, probs))
    )
    st.html(rows)


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.html(PAGE_CSS)
eyebrow("PLANNER")
st.title("Test a drought on a county.")
st.write("Estimate the crop-value loss for one county under a drought level you choose, or the most likely level "
         "from 2000-2025 history. It is not a weather forecast or an official payment.")

st.subheader("Scenario")
inputsColumn, outputsColumn = st.columns([5, 7], gap="medium")
with inputsColumn:
    with st.container(key="cardInputs"):
        counties = countyOptions()
        labels = {r.fips: f"{r.county_name}, {r.state_alpha}" for r in counties.itertuples()}
        order = counties["fips"].tolist()
        fips = st.selectbox("County", order, index=order.index(DEFAULT_FIPS) if DEFAULT_FIPS in order else 0,
                            format_func=labels.get)
        usableCrops = [c for c in CROPS if countyRecords(fips, c)["trend"] is not None]
        crop = st.selectbox("Crop", usableCrops or CROPS, format_func=CROP_NAMES.get)
        years = list(range(LAST_YEAR + 1, LAST_PROJECTED_YEAR + 1))
        year = st.selectbox("Year", years, format_func=lambda y: f"{y} (projected)")
        st.caption("Projections stop at 2030. 2026-2030 trend yield is a linear extension of the county's "
                   "2000-2025 trend.")
        level = st.segmented_control("Drought level", LEVELS + ["Predict"], default="Predict") or "Predict"
        price = st.number_input(f"Price assumption ({CROP_NAMES[crop].lower()}, $ per bushel)", min_value=0.0,
                                value=DEFAULT_PRICE[crop], step=0.25, key=f"planPrice_{crop}",
                                help="An editable assumption, not a cited market price.")

with outputsColumn:
    with st.container(key="cardOutputs"):
        result = scenario(fips, crop, year, level, price)
        if "error" in result:
            st.html(f'<div class="drWarn">{result["error"]} Pick another crop or county.</div>')
        else:
            dollars = result["dollars"]
            st.html('<div class="drMono">Estimated crop-value loss</div>')
            for warning in result["warnings"]:
                st.html(f'<div class="drWarn">{warning}</div>')
            if result["acres"] is None:
                st.html('<div class="drWarn">No planted acres on record, so dollars cannot be estimated.</div>')
            else:
                st.html(f'<div class="drRange">{money(dollars(result["low"]))} - {money(dollars(result["high"]))}</div>')
            if result["confident"]:
                st.html(f'<div class="drRangeNote">Expected loss {result["mid"]:.1f}% below the county trend '
                        f'(range {result["low"]:.1f}% to {result["high"]:.1f}%).</div>')
            else:
                st.html(f'<div class="drRangeNote">Range of the nearest years only: {result["low"]:.1f}% to '
                        f'{result["high"]:.1f}% below the county trend. No confident estimate.</div>')
            if result["predict"]:
                st.html(f'<div class="drMono">Probability of each drought level by Aug 15 · most likely '
                        f'{LEVELS[result["bucket"]]}</div>')
                probabilityBars(result["probs"])
            st.html('<div class="drMono" style="margin-top:12px">Closest 3 historical years</div>')
            nearest = pd.DataFrame([{"Year": h["year"], "Drought level by Aug 15": LEVELS[h["bucket"]],
                                     "Actual loss (% below trend)": round(h["loss"], 1)} for h in result["nearest"]])
            st.dataframe(nearest, hide_index=True, width="stretch")
            st.caption(markdownSafe(
                f"Dollars = {result['trendYield']:.1f} bu/acre trend yield x loss % x "
                f"{result['acres'] or 0:,.0f} planted acres (latest reported) x ${price:.2f}/bu (assumed)."))
        st.caption("Model estimate from 2000-2025 history, not a weather forecast. If an input falls outside the "
                   "county's history, a warning replaces the confident number. Prototype lookup, not a validated model.")
