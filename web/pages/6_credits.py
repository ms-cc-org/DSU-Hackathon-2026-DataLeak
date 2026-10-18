"""Credits: data sources, software, generated media, and AI use."""

import streamlit as st

from web.ui import applyStyle, assetPath


applyStyle()
st.title("Credits")

st.subheader("Data sources")
st.markdown(
    """
All data is public federal data, supplied in the starter repository.

- **U.S. Drought Monitor:** The U.S. Drought Monitor is jointly produced by the National Drought Mitigation
  Center at the University of Nebraska-Lincoln, the United States Department of Agriculture, and the
  National Oceanic and Atmospheric Administration.
- **USDA NASS:** This product uses the NASS API but is not endorsed or certified by NASS.
- **NOAA ACIS:** Weather data from the Applied Climate Information System (ACIS), NOAA Regional Climate Centers.
- **Soil:** Soil Survey Staff, Natural Resources Conservation Service, United States Department of
  Agriculture. Soil Survey Geographic (SSURGO) Database, via Soil Data Access.
- **County boundaries:** U.S. Census Bureau county boundaries, from the plotly/datasets county GeoJSON.
- **Crop prices:** the app uses an editable assumed price (corn \\$4.00/bu, soybeans \\$10.00/bu) until a
  cited price source is added.
"""
)

st.subheader("Software")
st.markdown(
    """
- [Streamlit](https://streamlit.io), [pandas](https://pandas.pydata.org), [NumPy](https://numpy.org),
  [Plotly](https://plotly.com/python/), [scikit-learn](https://scikit-learn.org).
- [three.js](https://threejs.org) r169 (MIT license) for the 3D viewer, bundled in
  `web/assets/viewer/vendor/` so the app runs without a network.
"""
)

st.subheader("Generated media")
if assetPath("intro_loop.mp4") or assetPath("hero_field.jpg"):
    st.write(
        "The intro animation and header images were generated with Higgsfield. They are decorative "
        "illustrations, never data. Prompts and settings are in `web/assets/PROMPTS.md`."
    )
else:
    st.write("No generated media is included in this version.")

st.subheader("AI use")
st.markdown(
    """
- **Claude Code (Anthropic):** helped write the 3D viewer, the County risk, Overview, Method and Credits
  pages, and the README. Verified by running every page, checking numbers against the master table
  (for example Mahaska County corn 2012: 133.0 bu/acre, 25.0% below trend, D3), and a clean-clone test.
- **OpenAI Codex:** helped organize the repository scaffold, page navigation and the Iowa corn history filter.
- **Higgsfield:** generated the decorative video and images listed above.

Every number, chart and map in the app is computed from the supplied records; the team can explain
and change any part of the code.
"""
)
