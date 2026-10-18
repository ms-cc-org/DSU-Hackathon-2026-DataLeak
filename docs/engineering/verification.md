# HARVEST verification

## Focused checks

From the repository root with the virtual environment active:

```bash
python -m unittest discover -s tests -p 'test_connected_app.py' -v
python -m unittest discover -s tests -p 'test_planner_ui.py' -v
python -m unittest discover -s tests -p 'test_insurance_scenarios.py' -v
python -m unittest discover -s tests -p 'test_insurance_map.py' -v
python -m unittest discover -s tests -p 'test_engine.py' -v
python -m compileall -q app.py src web tests
git diff --check
```

The broader legacy projection/allocation tests still contain requests for the removed `Predict` lookup option. A focused pass must not be described as a full-suite pass.

## Required for model-related changes

1. Check selection → audited inputs → saved inference → aggregation → displayed metrics/map/table → exported values. A page rendering successfully is insufficient.
2. Test IA/NE × corn/soybeans/all crops × future/historical footprint/replay. Change controls **after** a result exists, without another Run click; every surface must update to the new scope.
3. Compare each county's two shares directly with the frozen D artifacts. Independently calculate X/Y/Z and damaged acres from exposure; reconcile statewide totals and exposure-weighted shares. Use sub-cent dollar tolerances.
4. Check CSV/manifest crop, year, artifact and assumptions. Confirm scaling changes dollars/exposure while leaving learned shares unchanged.
5. Verify missing estimates remain missing and refresh failures remove stale outputs. Retain input/range warnings and recovery behavior.
6. Keep the original official payout reproduction checks. Do not change D's features/settings or rerun the one-shot official test to fix a UI issue.

`test_insurance_scenarios.py` covers 18 mode/state/crop combinations against frozen fits/formulas. `test_connected_app.py` checks the reactive page lifecycle and embedded map payload; `test_planner_ui.py` checks default/selected-year dollar results. Functional agreement means faithful use of the model, not proven forecast accuracy.

## Browser check

Confirm HARVEST in the browser title/header; navigation is Story, Explore 3D, Insurance, Planner. Planner opens at **2026 (projected)**, uses the same label pattern for every year and has no fund section/source banner. Insurance must update county/crop totals and its 3D map when a crop changes. Check county selection, aerial/orbit controls, numerical tables, exports and console errors. Restart an older Streamlit process when imported UI modules remain cached.

Reference values for Iowa 2026, exposure 2025, all historical footprints, 1× multipliers:

| Crop selection | Statewide X | Plymouth County X |
|---|---:|---:|
| Corn | $143,831,222.52 | $4,193,830.94 |
| Soybeans | $62,241,849.11 | $2,065,440.85 |
| Both | $206,073,071.63 | $6,259,271.79 |

The UI rounds to whole dollars. Stored artifact reproduction differences are recorded in `app/model/artifacts/build_report.json`; original evaluations remain in `app/model/results/`. Update this record with the checks actually performed, and keep historical screenshots/logs out of active product documentation.

## Latest check — October 18, 2026

HARVEST branding/documentation cleanup: **10 connected-app tests and 2 Planner tests passed**. Python compilation, `git diff --check` and 37 local documentation links passed. The browser title/header show HARVEST with the four tabs in the correct order and no console errors. Model code/settings/artifacts are unchanged; this was a focused app check, not a full-suite run. Original documentation/PDFs were archived locally and verified before consolidation.
