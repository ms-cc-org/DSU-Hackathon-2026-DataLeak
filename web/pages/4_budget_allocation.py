"""State funding and allocation page scaffold."""

import streamlit as st

from web.ui import showPending


st.title("Budget allocation")
st.write(
    "The officer will be able to compare a statewide funding estimate with a "
    "chosen fund and inspect county allocations under explicit policy rules."
)
showPending("Funding-need and allocation calculations")
