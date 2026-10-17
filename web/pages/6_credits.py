"""Data-source and contribution credits page scaffold."""

import streamlit as st


st.title("Credits")
st.write(
    "The starter data combines USDA NASS yield and acreage, NOAA ACIS weather, "
    "U.S. Drought Monitor conditions, USDA NRCS soil data, and Census county boundaries."
)
st.info(
    "Add the selected satellite-imagery provider, corn-price source, USDA RMA extension, "
    "team members, and complete AI-use disclosure as those pieces are incorporated."
)
