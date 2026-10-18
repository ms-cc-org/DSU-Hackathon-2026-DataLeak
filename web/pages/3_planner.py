"""Planner: step 1 estimates crop-value loss for a county scenario; step 2 splits a fund across counties.

Step 1 uses web/scenario_lookup.py (a prototype lookup, not a validated model) because src/engine.py
has no scenario function yet. Step 2 uses src/allocation.py's allocation function when it exists;
until then it shows its controls and a "Not available yet" state, and no amounts are invented.
"""

import pandas as pd
import streamlit as st

import src.allocation as allocation
from web.render3d import CROPS, DEFAULT_FIPS, LAST_YEAR, LAST_PROJECTED_YEAR, STATES, loadCountyHistory
from web.scenario_lookup import LEVELS, countyRecords, scenario
from web.ui import AMBER, CROP_NAMES, DEFAULT_PRICE, DROUGHT_COLORS, eyebrow, markdownSafe, money, showPending


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

ALLOCATION_RULES = ["Proportional to expected loss", "Equal split", "Trigger only", "Tiered"]
TRIGGERS = ["Weeks in D2+", "Expected loss above a threshold"]


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
st.title("Test a drought, then split the fund.")
st.write("Step one estimates crop-value loss for a county. Step two turns expected losses into a county-by-county "
         "allocation. Neither is a weather forecast or an official payment.")

# --- Step 1: scenario ------------------------------------------------------------------------
st.subheader("Step 1 · Scenario")
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

# --- Step 2: budget allocation ------------------------------------------------------------------
st.subheader("Step 2 · Budget allocation")
with st.container(key="cardAllocation"):
    fundColumn, ruleColumn, triggerColumn, shareColumn = st.columns(4)
    fund = fundColumn.number_input("Fund size ($)", min_value=0, value=10_000_000, step=500_000)
    rule = ruleColumn.selectbox("Rule", ALLOCATION_RULES)
    trigger = triggerColumn.selectbox("Trigger", TRIGGERS)
    minimumShare = shareColumn.slider("Minimum share per county", 0.0, 0.05, 0.0, step=0.005, format="%.3f",
                                      help="Smallest share of the fund any eligible county receives.")

    allocate = getattr(allocation, "allocate", None)
    if not callable(allocate):
        showPending("County allocation (src/allocation.py has no allocation function yet)")
    else:
        # Interface agreed in the team to-do list: a table of expected losses in, a table of amounts and reasons out.
        state = countyRecords(fips, crop).get("state")
        stateCounties = counties[counties["state_alpha"] == state]
        losses = []
        for row in stateCounties.itertuples():
            r = scenario(row.fips, crop, year, level, price)
            if "error" not in r and r["acres"] is not None:
                losses.append({"fips": row.fips, "county": row.county_name, "expected_loss": r["dollars"](r["mid"])})
        try:
            table = pd.DataFrame(allocate(pd.DataFrame(losses), fund, rule, trigger, minimumShare))
            amount = table["amount"].fillna(0)
            loss = table["expected_loss"].fillna(0)
            hardest = loss >= loss.quantile(0.75)
            chips = st.columns(4)
            chips[0].metric("Loss covered", f"{100 * amount.clip(upper=loss).sum() / max(loss.sum(), 1):.0f}%")
            chips[1].metric("Fund to hardest-hit counties", f"{100 * amount[hardest].sum() / max(amount.sum(), 1):.0f}%")
            chips[2].metric("Counties left with nothing", int((amount <= 0).sum()))
            chips[3].metric("Remaining gap", money(max(loss.sum() - amount.sum(), 0)))
            shown = table.rename(columns={"county": "County", "expected_loss": "Expected loss", "amount": "Amount", "reason": "Reason"})
            st.dataframe(shown[["County", "Expected loss", "Amount", "Reason"]], hide_index=True, width="stretch")
            st.download_button("Download CSV", shown.to_csv(index=False), file_name="allocation.csv", mime="text/csv")
        except Exception as error:
            st.error(f"The allocation function could not be used: {error}")
    st.caption("Dollar figures are estimated crop-value loss, not insurance claims or official relief payments.")
