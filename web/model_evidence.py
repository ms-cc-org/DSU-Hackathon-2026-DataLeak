"""Shared access to the existing insurance model test reports and actual outcomes."""

from pathlib import Path

import pandas as pd
import streamlit as st

from web.ui import markdownSafe


resultsDir = Path(__file__).resolve().parents[1] / "app" / "model" / "results"


@st.cache_data(show_spinner=False)
def loadModelMetrics() -> pd.DataFrame:
    """Read saved official test metrics without reevaluating or training models."""
    return pd.read_csv(resultsDir / "test_metrics.csv")


@st.cache_data(show_spinner=False)
def loadInsuranceActuals() -> pd.DataFrame:
    """Expose historical outcomes solely for replay comparisons, never future inputs."""
    columns = ["fips", "crop", "year", "drought_indemnity", "drought_loss_acres"]
    return pd.read_csv(resultsDir / "test_predictions.csv", dtype={"fips": str}, usecols=columns).rename(
        columns={"drought_indemnity": "actualPayoutUsd", "drought_loss_acres": "actualDamagedAcres"})


def renderModelEvidence() -> None:
    """Show real saved D performance, baselines and historical errors with their scope."""
    st.subheader("Model D: saved insurance test results")
    st.write("Tweedie GLM · alpha 0.001 · power 1.5 · uncalibrated. Trained on 2000–2015, tested on "
             "2016–2025 Iowa/Nebraska corn and soybeans. These results evaluate insurance outcomes, "
             "not the all-crop historical lookup or the hypothetical future ensemble.")
    try:
        metrics = loadModelMetrics()
        payoutMetrics = metrics.loc[metrics["target"].eq("t1") & metrics["group"].eq("all")]
        modelRow = payoutMetrics.loc[payoutMetrics["model"].eq("D")].iloc[0]
        errorColumn, captureColumn, rangeColumn = st.columns(3)
        errorColumn.metric("Mean statewide payout error", f"${modelRow['stat_abs_err']:,.0f}")
        captureColumn.metric("Top-20 county loss capture", f"{modelRow['capture_top20']:.1%}")
        rangeColumn.metric("Historical range coverage", f"{modelRow['range_cov']:.0%}")
        st.warning("The model has large historical misses. Its rough ranges are not calibrated probability "
                   "intervals. A working calculation does not establish reliable future accuracy.")
        comparison = payoutMetrics.loc[payoutMetrics["model"].isin(["D", "B2a", "B2b", "B4"]),
                                        ["model", "stat_abs_err", "worst_shortfall", "capture_top20"]]
        st.dataframe(comparison, hide_index=True, width="stretch", column_config={
            "model": "Model / baseline", "stat_abs_err": st.column_config.NumberColumn("Mean state error", format="dollar"),
            "worst_shortfall": st.column_config.NumberColumn("Worst state shortfall", format="dollar"),
            "capture_top20": st.column_config.NumberColumn("Top-20 capture", format="percent"),
        })
        with st.expander("Official state-year predicted versus actual payouts"):
            stateYears = pd.read_csv(resultsDir / "test_state_years.csv")
            stateYears["errorUsd"] = stateYears["d_x_payout_usd"] - stateYears["actual_x_payout_usd"]
            st.dataframe(stateYears, hide_index=True, width="stretch")
        with st.expander("Full official report and evaluation caveats"):
            st.markdown(markdownSafe((resultsDir / "test_report.md").read_text()))
        with st.expander("Iowa corn test slice"):
            st.markdown(markdownSafe((resultsDir / "iowa_corn_test_slice.md").read_text()))
    except (OSError, ValueError, KeyError, IndexError) as error:
        st.error(f"Saved insurance evidence could not be loaded: {error}")
