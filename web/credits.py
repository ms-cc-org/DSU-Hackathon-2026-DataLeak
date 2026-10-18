"""Credits content (data sources, software, animation and media, AI use), shown on the Evidence tab."""

import streamlit as st

from web.ui import assetPath


def renderCredits() -> None:
    hasMedia = bool(assetPath("intro_loop.mp4") or assetPath("hero_field.jpg"))

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
- **MODIS:** Didan, K. (2021). MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN Grid V061.
  NASA EOSDIS Land Processes DAAC.
- **County boundaries:** U.S. Census Bureau county boundaries, from the plotly/datasets county GeoJSON.
- **Crop prices:** the app uses editable assumed prices (corn \\$4.00/bu, soybeans \\$10.00/bu, winter wheat
  \\$5.50/bu, sorghum \\$4.00/bu) until a cited price source is added.
"""
    )

    st.subheader("Software and fonts")
    st.markdown(
        """
- [Streamlit](https://streamlit.io), [pandas](https://pandas.pydata.org), [NumPy](https://numpy.org),
  [Plotly](https://plotly.com/python/), [scikit-learn](https://scikit-learn.org).
- [three.js](https://threejs.org) r169 (MIT license) for the 3D viewer, bundled in
  `web/assets/viewer/vendor/` so the app runs without a network.
- Fonts: Bricolage Grotesque, DM Sans and JetBrains Mono (SIL Open Font License), bundled in `static/fonts/`.
"""
    )

    st.subheader("Animation and media")
    st.write("The Story hero landscape and the banner motion are drawn in code (SVG and CSS). They are decorative and never data.")
    if hasMedia:
        st.write("Some images or video were generated with Higgsfield. They are decorative illustrations, never data. "
                 "Prompts and settings are in `web/assets/PROMPTS.md`.")
    else:
        st.write("No AI-generated media is included in this version.")

    st.subheader("AI use")
    st.markdown(
        f"""
- **Claude Code (Anthropic):** helped write the 3D viewer, the Story, Explore 3D, Planner and Evidence tabs, the
  prototype scenario lookup (`web/scenario_lookup.py`), the theme, and the README. Verified by running every page,
  checking numbers against the master table (for example Mahaska County corn 2012: 133.0 bu/acre, 25.0% below
  trend, D3), and a clean-clone test.
- **OpenAI Codex:** helped organize the repository scaffold, page navigation and the Iowa corn history filter.
{"- **Higgsfield:** generated the decorative media noted above." if hasMedia else ""}

Every number, chart and map in the app is computed from the supplied records or the documented lookup; the team
can explain and change any part of the code.
"""
    )
