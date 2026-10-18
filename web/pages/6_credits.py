"""Superseded by the Evidence tab, which shows this content; kept on disk, not registered in app.py."""

import streamlit as st

from web.credits import renderCredits


st.title("Credits")
renderCredits()
