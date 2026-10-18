# App pages

The root `app.py` registers four connected tabs through `st.Page` and `st.navigation` in a top bar.

| Tab | File | What it shows |
|---|---|---|
| Story | `1_overview.py` | Project story, dataset counts and a selectable state drought map. |
| Explore 3D | `2_county_risk.py` | Historical county records, ranked cards, charts, and a 3D viewer with state and crop controls. |
| Planner | `3_planner.py` | County/crop loss scenarios for 2026–2030, defaulting to 2026 with uniform projected-year labels. The state-fund section is removed. |
| Insurance | `3_scenarios.py` | Actual fitted model D predictions for future scenarios, historical footprint what-ifs and replay, with exact inputs, model C analog context and provenance exports. |

History and Planner cover California, Delaware, Iowa, Nebraska and the four dataset crops where records support them. The county selector contains the 230 counties with master records; the map has 253 boundary counties, including 23 with no master records. A missing state-crop pair or thin county history produces a clear message, not a zero loss.

Planner defaults to 2026. All selectable years (2026–2030) use the same “(projected)” label. The displayed loss recalculates from the selected year’s trend yield, latest acreage and assumed price. The separate 3D viewer retains its existing year behavior.

Insurance defaults to 2026, the first year after the supplied data. It uses an assumed insured exposure year and complete historical climate footprints with the unchanged D artifact. Its direct predictions are payout share and damaged-acre share; X/Y/Z are calculations. A target-year change alone does not change D's predictions. Historical replay uses the test artifact for 2016–2025; historical footprint what-ifs use the full fit and are labeled in sample.

Insurance displays its completed predictions in a separate interactive 3D county map. The legacy allocation code remains on disk but is not embedded in Planner or linked through active navigation.

Unregistered compatibility pages: `4_budget_allocation.py` reuses the state fund component and `6_credits.py` retains legacy credit content; current credits are in README.md. No trained model output is silently substituted for a missing state/crop estimate.

The Evidence tab, its page file and links to it have been removed. Saved model reports remain developer documentation under `app/model/results/`; replay comparisons still load historical outcomes.
