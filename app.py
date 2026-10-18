"""Streamlit entry point: four tabs in a top bar, and the shared style.

Run from the repository root:
    python -m streamlit run app.py
"""

from pathlib import Path

import streamlit as st

from web.ui import applyStyle


st.set_page_config(
    page_title="Drought Relief Planner",
    page_icon=":material/agriculture:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

currentPage = st.navigation(
    [
        st.Page("web/pages/1_overview.py", title="Story", default=True),
        st.Page("web/pages/2_county_risk.py", title="Explore 3D", url_path="explore"),
        st.Page("web/pages/3_planner.py", title="Planner", url_path="planner"),
        st.Page("web/pages/5_method_and_data.py", title="Evidence", url_path="evidence"),
    ],
    position="top",
)

brand = Path(__file__).resolve().parent / "web" / "assets" / "brand.svg"
if brand.exists():
    st.logo(str(brand), size="large")
applyStyle()  # shared tokens and motion for every page (style only; takes no space)
st.sidebar.caption(
    "Drought Relief Planner · four states, four crops, 2000-2025 records · August 15 decision. "
    "Dollar values are estimated crop-value loss, not relief payments."
)
currentPage.run()
