"""Historical insurance outcomes used for replay comparisons."""

from pathlib import Path

import pandas as pd
import streamlit as st


resultsDir = Path(__file__).resolve().parents[1] / "app" / "model" / "results"


@st.cache_data(show_spinner=False)
def loadInsuranceActuals() -> pd.DataFrame:
    """Expose historical outcomes solely for replay comparisons, never future inputs."""
    columns = ["fips", "crop", "year", "drought_indemnity", "drought_loss_acres"]
    return pd.read_csv(resultsDir / "test_predictions.csv", dtype={"fips": str}, usecols=columns).rename(
        columns={"drought_indemnity": "actualPayoutUsd", "drought_loss_acres": "actualDamagedAcres"})
