# App pages

The root `app.py` registers four connected tabs through `st.Page` and `st.navigation` in a top bar.

| Tab | File | What it shows |
|---|---|---|
| Story | `1_overview.py` | Project story, dataset counts and a selectable state drought map. |
| Explore 3D | `2_county_risk.py` | Historical county records, ranked cards, charts, and a 3D viewer with state and crop controls. |
| Planner | `3_planner.py` | A county crop-value-loss scenario and a separate state fund shared across all supported crops, with county totals, crop shares, coverage and a CSV export. |
| Insurance | `3_scenarios.py` | Actual fitted model D predictions for future scenarios, historical footprint what-ifs and replay, with exact inputs, model C analog context and provenance exports. |

History and Planner cover California, Delaware, Iowa, Nebraska and the four dataset crops where records support them. The county selector contains the 230 counties with master records; the map has 253 boundary counties, including 23 with no master records. A missing state-crop pair or thin county history produces a clear message, not a zero loss.

The state fund uses `web/allocation_data.py` to run the same prototype lookup for every boundary county and all four crops, then calls `src/allocation.py` for proportional shares with exact cent balancing. Missing estimates stay visible without calculated allocations; nearest-year fallback estimates remain included with warnings. Its form is independent of the county scenario. A crop detail filter never changes the shared fund weights. See `docs/lane3_contract.md` for the policy and columns.

County, state fund and 3D scenario years default to the next calendar year within 2026–2030, using `src/projections.py` (2027 as of October 2026). The county result shows a central dollar estimate when matching history supports it, along with the historical range. Future-year estimates extend the yield trend and retain historical drought frequencies and latest acreage; they are loss projections, not future weather observations.

Insurance defaults to 2026, the first year after the supplied data. It uses an assumed insured exposure year and complete historical climate footprints with the unchanged D artifact. Its direct predictions are payout share and damaged-acre share; X/Y/Z are calculations. A target-year change alone does not change D's predictions. Historical replay uses the test artifact for 2016–2025; historical footprint what-ifs use the full fit and are labeled in sample.

IA/NE state fund runs attach D corn/soybean context without changing the agreed crop-loss allocation basis. The model result is available immediately on Insurance; its inputs and climate assumptions remain distinct from the crop-loss form. Insurance shows completed payout predictions in an interactive 3D county map with the statewide USD total above it. Allocation maps retain USGS imagery with local county outlines as an offline alternative. See `docs/PREDICTION_CONTRACT.md`.

Unregistered compatibility pages: `4_budget_allocation.py` reuses the state fund component and `6_credits.py` retains legacy credit content; current credits are in README.md. No trained model output is silently substituted for a missing state/crop estimate.

The Evidence tab, its page file and links to it have been removed. Saved model reports remain developer documentation under `app/model/results/`; replay comparisons still load historical outcomes.
