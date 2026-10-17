"""Historical county risk page scaffold."""

import streamlit as st

from src.ui import showPending


st.title("County risk")
st.write(
    "This page will show reported county history, drought exposure, soil context, "
    "and a clearly labeled county-level loss estimate."
)
showPending("Historical county cards and the satellite county map")
