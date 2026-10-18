# HARVEST architecture

HARVEST is a local Streamlit app backed by files and saved models. The website has four tabs and no database.

```text
app.py → web/pages/ → shared presentation and local data
  Insurance → insurance_ui → insurance_data → insurance_scenarios → engine → fitted artifacts
             result → totals / county table / 3D map / input audit / downloads
  Planner   → scenario_lookup → render3d county history → supplied records
  Explore   → render3d → bundled three.js viewer
```

## Entry points and presentation

| File/folder | Responsibility |
|---|---|
| `app.py` | Starts HARVEST and registers Story, Explore 3D, Insurance, Planner in that order. |
| `.streamlit/config.toml` | Sets the shared theme and local font serving. |
| `requirements.txt`, `.env.example`, `.gitignore` | Pin dependencies, describe optional rebuild credentials and exclude secrets/caches/local notes. |
| `web/pages/1_overview.py` | Project story, dataset counts and animated historical drought map. |
| `web/pages/2_county_risk.py` | Historical rankings/charts and the interactive 3D viewer. |
| `web/pages/3_scenarios.py` | Insurance page entry point; delegates to the shared insurance UI. |
| `web/pages/3_planner.py` | County crop-loss controls and results; defaults to 2026 with uniform projected-year labels. |
| `web/ui.py` | Shared styling, HARVEST header, crop names, prices, formatting and decorative hero helpers. |
| `web/render3d.py` | Builds county history payloads and embeds the bundled historical/scenario viewer. |
| `web/assets/viewer/viewer.html` | Interactive state/county scenes, historical timeline and illustrative crop-loss sandbox. |
| `web/assets/viewer/insurance_map.html` | Extrudes counties using completed insurance payout predictions; provides orbit/zoom, county selection and crop details. |
| `web/assets/viewer/vendor/` | Bundled three.js r169 and helpers with their MIT license; avoids network imports. |
| `web/assets/brand.svg`, `static/fonts/` | HARVEST icon/accessibility label and bundled licensed fonts. |
| `web/assets/README.md`, `web/pages/README.md` | Short folder guides pointing to the central documentation. |

## Prediction and data flow

| File/folder | Responsibility |
|---|---|
| `web/insurance_ui.py` | Reactive selectors, displayed predictions, source explanations, historical comparisons and downloads. Clears stale results on failure. |
| `web/insurance_data.py` | Caches inference by the full selection and records the requested selection/included crops in the manifest. |
| `src/insurance_scenarios.py` | Applies climate footprints, scales exposure, runs future/historical/replay modes and aggregates complete scenarios. |
| `src/engine.py` | Loads fitted D/C bundles once and provides the stable `predict`, `scenario`, `replay` API. |
| `web/insurance_map.py` | Joins completed predictions to all supplied state boundaries and computes county totals/weighted shares. |
| `web/model_evidence.py` | Reads observed historical insurance outcomes for replay comparisons. |
| `web/scenario_lookup.py` | Separate county crop-value-loss lookup from historical yield shortfalls. |
| `src/data_loader.py` | Reads the supplied master, daily weather, weekly drought, soil, irrigation, MODIS and boundary files. |
| `src/projections.py` | Calendar defaults for the separate 3D viewer and legacy fund form; Planner independently defaults to 2026. |
| `src/reserve_band.py` | Reads the saved statewide payout planning-band factors. This backend range is not displayed in Insurance. |
| `organize_usda_data.py` | Builds decision-date insured exposure/features and insurance outcome tables from RMA and supplied panels. |
| `organize_drought_severity.py` | Builds weather/soil and outlook inputs for the separate drought-severity experiments. |

## Models, analysis and retained code

| File/folder | Responsibility |
|---|---|
| `app/model/data.py` | Insurance feature order, target names, data joins and fitted preprocessing. |
| `app/model/tweedie.py`, `analog.py`, `budget.py` | D's share predictions, C's historical neighbors, and X/Y/Z conversion/range calculations. |
| `app/model/baselines.py`, `erp.py` | Comparison baselines and USDA-style drought trigger calculations. |
| `app/model/hurdle.py`, `gbm.py`, `tabpfn_model.py` | Alternative model candidates; they do not supply the live headline prediction. |
| `app/model/build_artifacts.py`, `artifacts/` | Offline artifact builder and saved D/C fits, ordered features, bounds, scenario inputs and reproduction report. |
| `app/model/evaluate.py`, `final_test.py`, `deploy_check.py` | Model evaluation, guarded official test and deployment checks. The official test has already run. |
| `app/model/ratio_band*.py`, `iowa_corn_slice.py`, `make_test_report.py`, `exploratory_more_years.py` | Supporting planning-band, slice/report and exploratory evaluation scripts. |
| `app/model/DECISIONS*.md`, `results/` | Original modeling decisions and frozen evaluation outputs; retained separately from condensed app guidance. |
| `app/drought_model/` | Separate drought-severity candidates, evaluation, saved Task B fit and weather what-if helper. Not connected to HARVEST's pages. |
| `analysis/notebooks/`, `analysis/models/`, `analysis/validation/` | Starter/research material; production insurance artifacts live in `app/model/`. |
| `src/allocation.py`, `web/allocation_data.py`, `web/allocation_ui.py`, `web/pages/4_budget_allocation.py` | Legacy state-fund implementation. Not registered or embedded in the active site. |
| `web/credits.py`, `web/pages/6_credits.py` | Legacy credits page/content. Current public credits are in the root README and data guide. |
| `web/maps.py` | Shared county joins and retained imagery/outline map helpers; Insurance uses its separate 3D renderer. |
| `src/data.py`, `src/features.py` | Older Iowa-corn helper and placeholder feature boundary; active insurance features come from `organize_usda_data.py`. |

## Storage and maintenance

| Folder | Responsibility |
|---|---|
| `data/` | Supplied master, county boundaries, processed source panels and detailed data dictionary. `raw/` is ignored; `derived/` is reserved for derived outputs. |
| `src/build/` | Optional source-pull scripts, source validation and master rebuild; normal app use needs no downloads. |
| `usda_budget_data/` | Prepared insurance training/validation tables; held-out input files are ignored. |
| `drought_severity_data/` | Prepared inputs/labels for the separate drought-severity work. |
| `tests/` | Numerical engine/scenario tests, model-to-display reconciliation, county maps, Planner controls and legacy allocation checks. |
| `docs/project/` | Current scope and condensed event requirements. |
| `docs/engineering/` | This architecture guide, prediction contract and verification procedure. |
| `docs/data/` | Data summary, credits and original source-pipeline diagram. |
| `docs/dev/` | Ignored archive of superseded documentation and original planning PDFs. |

Model semantics and units are defined once in [predictions](predictions.md); behavior checks are in [verification](verification.md).
