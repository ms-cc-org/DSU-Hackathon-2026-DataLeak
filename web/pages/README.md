# App pages

The root `app.py` registers these six Streamlit pages through `st.Page` and `st.navigation`.

| Page | Owner | What it shows |
|---|---|---|
| `1_overview.py` | Lane 4 | The user, the August 15 decision, how to use the site, a real Iowa corn yield chart |
| `2_county_risk.py` | Lane 4 | Ranked county cards, drought and cost charts by year, and the 3D viewer (Mode 1) |
| `3_scenarios.py` | Lane 3 | Scenario inputs and outputs; the 3D sandbox is available as `showViewer("sandbox", fips)` |
| `4_budget_allocation.py` | Lane 3 | Fund split by rule and trigger |
| `5_method_and_data.py` | Lane 4 | Filters, missing values, definitions, coverage, backtest results, limits |
| `6_credits.py` | Lane 4 | Data sources, software, generated media, AI use |

Pages show only results computed from the supplied records or the engine. Unfinished features say so with `web.ui.showPending`.
