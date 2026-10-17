"""Small shared Streamlit presentation helpers."""

import streamlit as st


def showPending(featureName: str) -> None:
    """Label an unimplemented feature without showing fabricated results."""
    st.info(f"{featureName}: planned; no calculated results yet.")
