# App pages


The root `app.py` registers four tabs through `st.Page` and `st.navigation` (top bar; there is no sidebar).

| Tab | File | Owner | What it shows |
|---|---|---|---|
| Story | `1_overview.py` | Lane 4 | Dusk hero, dataset stats, three method chapters beside the pinned drought map, evidence band, footer |
| Explore 3D | `2_county_risk.py` | Lane 4 | The 3D viewer inline (opens at State view, one state at a time; History and Scenario modes; year card), counties ranked by expected annual loss, yearly charts |
| Planner | `3_planner.py` | Lane 4 | County scenario for 2026-2030 (prototype lookup); no budget allocation |
| Evidence | `5_method_and_data.py` | Lane 4 | Method and data notes, saved validation results, then the credits (`web/credits.py`) |

Superseded, kept on disk and not registered: `3_scenarios.py` and `4_budget_allocation.py` (Lane 3; replaced by the
Planner tab) and `6_credits.py` (its content is on the Evidence tab).

Pages show only results computed from the supplied records or the documented prototype lookup. Anything not built yet
shows the "Not available yet" state from `web.ui.showPending`.
=======
The root `app.py` registers these six Streamlit pages through `st.Page` and `st.navigation`.

| Page | Owner | What it shows |
|---|---|---|
| `1_overview.py` | Lane 4 | The user, the August 15 decision, how to use the site, a real Iowa corn yield chart |
| `2_county_risk.py` | Lane 4 | Ranked county cards, drought and cost charts by year, and the 3D viewer (Mode 1) |
| `3_scenarios.py` | Lane 2/UI handoff | Iowa-corn historical-footprint controls and cached D-model X/Y/Z outputs, with county table and C analog years |
| `4_budget_allocation.py` | Lane 3 | Fund split by rule and trigger |
| `5_method_and_data.py` | Lane 4 | Filters, missing values, definitions, coverage, backtest results, limits |
| `6_credits.py` | Lane 4 | Data sources, software, generated media, AI use |

Pages show only results computed from the supplied records or the engine. Unfinished features say so with `web.ui.showPending`.
>>>>>>> main
