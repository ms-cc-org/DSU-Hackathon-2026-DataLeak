"""Streamlit entry point and navigation for the drought relief planner."""

import streamlit as st


st.set_page_config(
    page_title="Drought Relief Allocation Planner",
    page_icon="🌽",
    layout="wide",
)

currentPage = st.navigation(
    [
        st.Page("web/pages/1_overview.py", title="Overview", default=True),
        st.Page("web/pages/2_county_risk.py", title="County risk"),
        st.Page("web/pages/3_scenarios.py", title="Scenarios"),
        st.Page("web/pages/4_budget_allocation.py", title="Budget allocation"),
        st.Page("web/pages/5_method_and_data.py", title="Method and data"),
        st.Page("web/pages/6_credits.py", title="Credits"),
    ]
)

st.sidebar.caption("Iowa corn · August 15 decision · scaffold")
currentPage.run()
