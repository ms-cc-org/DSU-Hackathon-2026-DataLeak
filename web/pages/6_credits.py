"""Legacy credits page; kept on disk, not registered in app.py. Current credits are in README.md."""

import streamlit as st

from web.credits import renderCredits


st.title("Credits")
renderCredits()
