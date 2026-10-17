"""Hypothetical corn-loss scenario page scaffold."""

import streamlit as st

from src.ui import showPending


st.title("Scenarios")
st.write(
    "The planned controls are an Iowa county, hypothetical drought conditions, "
    "planted acres, and corn price. The eventual output will be estimated crop-value "
    "loss, not a weather forecast or a relief payment."
)
showPending("The trained scenario model and its uncertainty range")
