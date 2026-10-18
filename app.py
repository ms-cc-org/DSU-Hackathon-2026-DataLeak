"""Streamlit entry point: navigation and the shared sidebar.

Run from the repository root:
    python -m streamlit run app.py
"""

import streamlit as st

from web.ui import applyStyle


st.set_page_config(
    page_title="Drought Relief Allocation Planner",
    page_icon=":material/agriculture:",
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

applyStyle()  # shared theme motion for every page (style only; takes no space)
st.sidebar.caption(
    "California · Delaware · Iowa · Nebraska · August 15 decision. Dollar values are an estimated crop loss, not program payout."
)
currentPage.run()
