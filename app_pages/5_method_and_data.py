"""Method and data notes page scaffold."""

import streamlit as st


st.title("Method and data")
st.write(
    "The supplied data spans 2000–2025. A valid August 15 model will use only "
    "weather and drought observations available by that date, then evaluate on "
    "later years using a walk-forward backtest."
)
st.info("No model or backtest result has been produced in this scaffold.")
st.write(
    "Missing county yields are not zero. Historical crop-value-loss estimates, "
    "insurance payments, and state relief payments are different measures."
)
