# App pages

The root `app.py` registers four tabs through `st.Page` and `st.navigation` (top bar).

| Tab | File | Owner | What it shows |
|---|---|---|---|
| Story | `1_overview.py` | Lane 4 | Dusk hero, dataset stats, three method chapters beside the pinned drought map, evidence band, footer |
| Explore 3D | `2_county_risk.py` | Lane 4 | The 3D viewer inline (History and Scenario modes, year card), counties ranked by expected annual loss, yearly charts |
| Planner | `3_planner.py` | Lane 4 | Step 1 county scenario (prototype lookup); step 2 allocation controls (pending until `src/allocation.py` has a function) |
| Evidence | `5_method_and_data.py` | Lane 4 | Method and data notes, saved validation results, then the credits (`web/credits.py`) |

Superseded, kept on disk and not registered: `3_scenarios.py` and `4_budget_allocation.py` (Lane 3; replaced by the
Planner tab) and `6_credits.py` (its content is on the Evidence tab).

Pages show only results computed from the supplied records or the documented prototype lookup. Anything not built yet
shows the "Not available yet" state from `web.ui.showPending`.
