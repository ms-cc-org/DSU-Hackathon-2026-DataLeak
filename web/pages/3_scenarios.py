"""Superseded by the Planner tab (web/pages/3_planner.py); kept on disk, not registered in app.py."""

import streamlit as st

from web.ui import showPending


st.title("Scenarios")
st.write(
    "The planned controls are an Iowa county, hypothetical drought conditions, "
    "planted acres, and corn price. The eventual output will be estimated crop-value "
    "loss, not a weather forecast or a relief payment."
)
showPending("The trained scenario model and its uncertainty range")
