# Architecture overview

This document describes the **current repository layout** after grouping related files. The root `app.py` launches four connected tabs. Planner keeps the all-state/all-crop loss lookup and agreed fund rule; Insurance exposes fitted model D with auditable future/historical scenarios, replay and source labels. Supported fund runs attach insurance context. Insurance uses a 3D county payout map; fund maps offer USGS imagery or local county outlines. Saved model reports remain in the repository.

## How the pieces connect

```text
app.py → web/pages/ → web/render3d.py → src/data_loader.py → data/
                    → web/scenario_lookup.py → web/render3d.py
                    → web/allocation_ui.py → web/allocation_data.py → web/scenario_lookup.py
                                           → src/allocation.py (pure proportional fund rule)
Insurance → web/insurance_ui.py → web/insurance_data.py → src/insurance_scenarios.py → src/engine.py
Planner fund → web/insurance_data.py → model D context joined by FIPS/crop
src/engine.py → app/model/artifacts/ ← app/model/build_artifacts.py
Insurance replay → web/model_evidence.py → saved historical outcomes
result maps → web/maps.py → local county geometry + public USGS imagery (optional network)
```

`data/processed/` contains supplied source panels, and `data/derived/` is reserved for new feature tables. `usda_budget_data/` contains prepared RMA insurance model rows. `app/model/` owns the current model research, saved artifacts, and official test reports; `web/` owns presentation.

## Root and submission

| File or folder | Purpose |
|---|---|
| `app.py` | Starts Streamlit and registers Story, Explore 3D, Planner and Insurance. It stays at the root so `python -m streamlit run app.py` remains the launch command. |
| `README.md` | Gives challenge context, setup and run steps, data credits, and the team's current AI-use disclosure. It links to the project scope and this overview. |
| `requirements.txt` | Pins Python packages used by the starter data, app, analysis, and notebook. Add a package here when code first depends on it. |
| `.env.example` | Shows where future provider configuration would be documented without storing a credential. Actual secrets belong in the ignored `.env`. |
| `.gitignore` | Excludes local secrets, environments, generated caches, and `docs/dev/` planning files from Git. |
| `LICENSE` | States the license for repository code and documentation. Dataset credits are in the README. |
| `.github/` | Holds repository-hosted workflow and submission configuration. |
| `.github/ISSUE_TEMPLATE/` | Contains the hackathon submission issue template. |
| `.github/ISSUE_TEMPLATE/submission.yml` | Defines the fields for the team's final GitHub issue submission. |

## Web application

| File or folder | Purpose |
|---|---|
| `web/` | Groups all presentation code and visual assets away from the data and model modules. It is imported by the root entry point and page scripts. |
| `web/__init__.py` | Marks `web` as a Python package so shared UI helpers have stable imports. |
| `web/pages/` | Holds four active tab scripts and two unregistered compatibility/credits pages. |
| `web/pages/1_overview.py` | Displays the project story, dataset counts and an animated state-selectable historical drought map. |
| `web/pages/2_county_risk.py` | Shows state/crop county rankings, yearly charts and a 3D viewer for historical records across the supplied dataset. |
| `web/pages/3_planner.py` | Runs the county crop-value-loss scenario for 2026–2030 and embeds the separate state fund workflow. Both use the historical prototype lookup with visible coverage limits. |
| `web/pages/3_scenarios.py` | Active Insurance entry point at `/insurance`. Delegates to the shared model UI for future ensembles, historical footprint what-ifs and replay. |
| `web/pages/4_budget_allocation.py` | Unregistered compatibility page that calls the same state fund component embedded in Planner. It contains no separate allocation logic. |
| `web/pages/6_credits.py` | Unregistered legacy credits page; current project credits are in README.md. |
| `web/pages/README.md` | Describes the four active tabs, cross-page connections and differing analytical coverage. |
| `web/credits.py` | Retains source, tool and AI-use credit content for the unregistered legacy credits page. |
| `web/ui.py` | Holds shared theme styling, labels, price assumptions, hero, stats and fallback messages. |
| `web/render3d.py` | Builds historical county data and embeds the bundled three.js viewer. Its county scene is illustrative; it has no satellite imagery tiles. |
| `web/scenario_lookup.py` | Computes the historical drought-level lookup and crop-value-loss range for one county/crop. The county Planner and bulk allocation adapter share the same record extraction and calculation. |
| `web/allocation_data.py` | Builds cached state scenarios across every supplied boundary county and all four crops using the existing lookup. Missing combinations remain explicit with reasons, warnings, acreage years and price assumptions. |
| `web/allocation_ui.py` | Collects a state fund and all-crop scenario assumptions and renders county totals, crop shares, missing-data explanations and a CSV download. It retains the last calculated snapshot in Streamlit session state. |
| `web/insurance_ui.py` | Renders reactive Insurance selections, the statewide payout total above the 3D county map, predicted shares and calculated X/Y/Z. Selection changes after the initial run refresh every result view and discard stale output on failure. Model identity remains in source/input breakdowns and provenance downloads. |
| `web/insurance_map.py` | Joins completed insurance predictions to all supplied state counties and aggregates selected crops with exposure-weighted shares. Embeds the 3D map using the existing bundled three.js runtime. |
| `web/assets/viewer/insurance_map.html` | Draws the interactive 3D state payout map with county heights, orbit/zoom, aerial/reset views, hover values and a county/crop breakdown. Missing estimates remain grey and WebGL failures leave the numerical tables usable. |
| `tests/test_insurance_map.py` | Verifies county payout conservation, weighted shares, selected crops and all boundaries for Iowa/Nebraska, including missing versus zero estimates. |
| `web/insurance_data.py` | Caches fitted-model inference for Insurance and supported state fund context, recording the requested selection and actual included crops. It never fits a model or predicts unsupported states/crops. |
| `web/model_evidence.py` | Loads saved historical insurance outcomes for replay comparisons. The removed Evidence page and report renderer no longer appear in the app. |
| `web/maps.py` | Joins result values to every supplied boundary in a state and renders transparent overlays on USGS imagery. Its local outline alternative needs no tile requests; missing values remain missing. |
| `web/assets/` | Holds the bundled three.js viewer, local fonts, brand SVG and optional decorative media. Assets must not supply analytical results. |
| `web/assets/README.md` | Defines the role and evidence boundary for visual assets. |
| `web/assets/PROMPTS.md` | Will record prompts and provenance if generated visual media is later used. No generated assets are recorded yet. |

## Data and core logic

| File or folder | Purpose |
|---|---|
| `src/` | Holds source data access, the earlier Iowa-corn filter and the separate Lane 2 RMA engine. Active tabs call `src.data_loader` through the web presentation modules. |
| `src/data_loader.py` | Loads the supplied master table, source panels, and county GeoJSON from stable repository paths. These are organizer-provided helpers. |
| `src/data.py` | Earlier Iowa-corn filter retained for analysis; active tabs use all-state loaders instead. |
| `src/features.py` | Reserves construction of drought/weather/soil features known by August 15. No derived feature table has been built. |
| `src/engine.py` | Loads fitted D/C artifacts once and exposes stable `predict`, `scenario`, and `replay` contracts for insured payout and budget illustrations. |
| `src/insurance_scenarios.py` | Adapts the unchanged D engine to future historical-footprint ensembles, historical what-ifs and replay with exact input/provenance records. It averages complete runs and calculates spread from statewide totals per run. |
| `src/allocation.py` | Pure proportional allocation of one state fund across positive county/crop loss estimates. It validates inputs, balances integer cents, preserves unavailable rows and rolls up counties and crops. |
| `src/projections.py` | Chooses the next calendar year as the default when it is within the supported horizon and labels projected years consistently. The county Planner, state fund form and 3D scenario view share these calendar settings. |
| `src/build/` | Holds organizer scripts that collected, joined, and checked the supplied dataset. They are reference/pipeline code, not required for the app's current read path. |
| `src/build/NASS_data_pull.py` | Pulls USDA NASS crop yield and acreage records for the source dataset. |
| `src/build/ACIS_data_pull.py` | Pulls the daily county weather panel from NOAA ACIS. |
| `src/build/USDM_data_pull.py` | Pulls weekly U.S. Drought Monitor county conditions. |
| `src/build/SSURGO_data_pull.py` | Pulls county soil measures from NRCS SSURGO. |
| `src/build/MODIS_gee_pull.py` | Builds the annual county vegetation-index extension from MODIS through Earth Engine. |
| `src/build/NASS_irrigation_pull.py` | Pulls the NASS irrigation extension used mainly for retrospective comparisons. |
| `src/build/build_master.py` | Joins source data into the county–crop–year master table. |
| `src/build/validate_sources.py` | Runs the organizer's sanity checks on source and joined data. |
| `data/` | Holds supplied data, source panels, the county geometry, and future derived features in separate subfolders. The supplied inputs should not be overwritten. |
| `data/master_dataset.csv` | Human-readable version of the 2000–2025 county–crop–year master table. It is an alternative to the parquet file. |
| `data/master_dataset.parquet` | Compact master table used by the existing loader and Overview. Its season totals are not August 15 features. |
| `data/counties.geojson` | County boundaries keyed by FIPS for eventual county overlays. It contains geometry, not satellite imagery. |
| `data/data_dictionary.md` | Defines master fields, units, missingness, season windows, and interpretation warnings. Consult it before modeling. |
| `data/processed/` | Groups supplied source panels and collection logs by provider. These are inputs to future date-safe feature construction. |
| `data/processed/master_build_log.json` | Records information from the organizer's master-table build. |
| `data/processed/acis/` | Contains the daily NOAA ACIS county weather panel and its collection-failure log. |
| `data/processed/acis/weather_daily.parquet` | Stores daily temperature and precipitation observations used for an August 15 cutoff. |
| `data/processed/acis/acis_failures.json` | Records ACIS collection failures for coverage review. |
| `data/processed/drought/` | Contains weekly U.S. Drought Monitor observations and their failure log. |
| `data/processed/drought/drought_weekly.parquet` | Stores dated county drought categories and coverage used for as-of drought features. |
| `data/processed/drought/usdm_failures.json` | Records U.S. Drought Monitor collection failures. |
| `data/processed/nass/` | Contains long-form crop statistics and their collection-failure log. |
| `data/processed/nass/nass_raw.parquet` | Stores NASS yield and acreage records before the master-table join. |
| `data/processed/nass/nass_failures.json` | Records NASS collection failures. |
| `data/processed/soil/` | Contains static county soil measures and their collection-failure log. |
| `data/processed/soil/soil_county.parquet` | Stores county water-storage and productivity context. |
| `data/processed/soil/ssurgo_failures.json` | Records SSURGO collection failures. |
| `data/processed/modis/` | Contains the annual county vegetation-index extension in two formats. The calendar-year values are retrospective, not August 15 inputs. |
| `data/processed/modis/modis_ndvi_county.csv` | Human-readable annual county MODIS vegetation-index table. |
| `data/processed/modis/modis_ndvi_county.parquet` | Compact version of the same annual county vegetation-index table. |
| `data/processed/irrigation/` | Contains the historical NASS irrigation extension and its collection-failure log. |
| `data/processed/irrigation/nass_irrigation.parquet` | Stores historical irrigated-share and yield comparisons, mainly for Nebraska. |
| `data/processed/irrigation/irrigation_failures.json` | Records irrigation-data collection failures. |
| `data/derived/` | Reserved for reproducible feature tables created from supplied inputs. It is distinct from `data/processed/`, which contains organizer-provided source panels. |
| `data/derived/README.md` | States where derived data belongs and how its inputs, schema, and cutoff should be recorded. |

## Analysis and evidence

| File or folder | Purpose |
|---|---|
| `analysis/` | Groups exploratory notebooks with future saved models and validation outputs. It keeps research artifacts separate from the app and supplied data. |
| `analysis/notebooks/` | Holds exploratory notebooks; moving it here does not change the app's data path. |
| `analysis/notebooks/starter_notebook.ipynb` | Walks through a starter Iowa drought analysis and example county map. Its import path points back to the repository root. |
| `analysis/models/` | An older reserved location for documented trained models. Current Lane 2 artifacts live in `app/model/artifacts/`. |
| `analysis/models/README.md` | Lists the training, version, and evidence details that should accompany a saved model. |
| `analysis/validation/` | An older reserved validation location. Current RMA model results live in `app/model/results/`. |
| `analysis/validation/README.md` | States the August 15 cutoff, earlier-year training, baseline, and sample-count requirements for future validation. |

## RMA model and verification

| File or folder | Purpose |
|---|---|
| `organize_usda_data.py` | Builds August 15 county model inputs and RMA insurance labels in training, validation, and testing splits. |
| `usda_budget_data/` | Holds prepared Iowa/Nebraska corn/soybean RMA inputs and labels. `testing/` is intentionally ignored; the official test predictions remain under `app/model/results/`. |
| `usda_budget_data/DATA_README.md` | Defines split years, decision-time fields, RMA labels, and X/Y/Z interpretation. |
| `usda_budget_data/manifest.json` | Records source-year availability and split row counts. |
| `app/model/` | Owns model fitting, baselines, evaluation, budget math, artifacts, and reports. Its files are script-style modules rather than a Python package. |
| `app/model/data.py` | Defines feature order, target names, dataset loading, filters, and fold-fitted preprocessing. |
| `app/model/tweedie.py` | Implements current model D for T1 payout share and T2 damaged-acre share. |
| `app/model/analog.py` | Implements model C's nearest historical county-year pool and quantile spread. |
| `app/model/baselines.py`, `erp.py` | Implement zero, drought-bin, liability, and USDA-style eligibility-trigger comparisons. |
| `app/model/hurdle.py`, `gbm.py`, `tabpfn_model.py` | Implement other evaluated model candidates or experiments. |
| `app/model/evaluate.py`, `final_test.py`, `deploy_check.py` | Produce walk-forward/validation results, the held-out official test, and deployment diagnostics. |
| `app/model/budget.py` | Converts predicted shares to X/Y/Z and computes C-based historical ranges, calibration helpers, and range flags. |
| `app/model/build_artifacts.py` | Fits and saves D and C outside the app request path, rebuilding ignored testing inputs when necessary and verifying D against saved official predictions. |
| `app/model/iowa_corn_slice.py` | Calculates an Iowa-corn-only comparison from existing official-test predictions, without refitting. |
| `app/model/artifacts/` | Stores the 2000–2015 test and 2000–2025 full model bundles, prebuilt inference inputs, and the artifact build report. |
| `app/model/results/` | Holds the existing model evaluation, official-test predictions/reports, the regenerated state-year reference, and the Iowa-corn slice. |
| `app/model/README.md`, `DECISIONS.md` | Explain model design, data boundaries, evaluation protocol, and the decision history. |
| `tests/test_engine.py` | Checks artifact reproduction, scenario nonnegativity, out-of-range flags, and dollar scaling using standard-library unittest. |
| `tests/test_allocation.py` | Checks proportional all-crop shares, county/crop totals, exact cent balancing, zero and missing losses, uncapped funds and rejected inputs. |
| `tests/test_allocation_data.py` | Checks actual coverage in all four states, agreement with the single-county Planner, price changes, drought fallback flags and missing acreage. |
| `tests/test_allocation_ui.py` | Uses Streamlit AppTest through the active navigation to test form submissions for all four states, display-only crop filtering and recalculation. |
| `tests/test_projections.py` | Checks calendar year defaults, 2027 projected yield and dollar conversion, and next-year allocation/CSV output for every state. These check functionality rather than predictive accuracy. |
| `tests/test_insurance_scenarios.py` | Checks D reproduction, climate replacement, scenario scaling, replay and auditable exports. An 18-case mode/state/crop matrix independently reconciles county shares, X/Y/Z and CSV values with the frozen artifacts and formulas. |
| `tests/test_connected_app.py` | Exercises all four pages and the fund-to-insurance handoff using Streamlit AppTest. After-run selection tests reconcile metrics, county/crop tables and the 3D payload; failed refreshes must remove stale results and recover. |
| `tests/test_maps.py` | Checks supplied boundaries, unavailable values, imagery attribution/layer order and the local outline alternative. |

## Documentation and local planning

| File or folder | Purpose |
|---|---|
| `docs/` | Holds public project scope, this architecture record, event guidance, and data specifications. Its `dev/` subfolder is local-only. |
| `docs/ARCHITECTURE_OVERVIEW.md` | Explains each folder and file in the grouped repository, plus the current/planned data flow. |
| `docs/PROJECT_SCOPE.md` | Tracks the ultimate goal, confirmed decisions, core moving parts, current state, and open decisions. |
| `docs/lane2_contract.md` | Specifies the fitted artifacts, prediction function signatures, output units, scenario semantics, and handoff to Lane 3. |
| `docs/lane3_contract.md` | Defines the confirmed state/all-crop fund policy, scenario data adapter, cent balancing, field meanings and coverage limitations. |
| `docs/PREDICTION_CONTRACT.md` | Authoritative description of what is predicted, assumed and calculated, including the connected future insurance adapter and input/output provenance. |
| `docs/VERIFICATION.md` | Records the final automated and browser checks of the connected prediction, allocation, evidence and map flow. |
| `docs/readme_notes/lane-3.md` | Records the allocation handoff and supersedes older frontend notes that described fund allocation as removed. |
| `docs/dataset_specification.md` | Gives the organizer's formal master-data fields, filters, units, and validation checks. |
| `docs/technical_implementation_plan.md` | Explains the organizer's dataset design, source choices, pipeline, and event mechanics. |
| `docs/Data to Harvest Hackathon at Delaware State University.md` | Preserves the longer event concept, including proposed challenge context. The current student briefing is the stronger source for submission details. |
| `docs/Pipeline-diagram.jpg` | Shows the organizer's data pipeline visually. |
| `docs/briefing/` | Groups student and mentor event instructions. |
| `docs/briefing/Student-briefing.md` | States the active challenge, deliverables, judging rubric, deadline, and dataset caveats. |
| `docs/briefing/Mentor-Briefing.md` | Gives mentors checkpoint and coaching guidance for the hackathon. |
| `docs/readme_notes/` | Provides a shared staging area for team members' README contributions. |
| `docs/readme_notes/README.md` | Describes the method, credit, dependency, and AI-use notes teammates can contribute. |
| `docs/dev/` | Holds ignored, local project planning PDFs and research notes; these are absent from a clean clone. They are context, not implemented code. |
| `docs/dev/README.md` | Summarizes the hackathon decision, provided data, project direction, and local documentation. |
| `docs/dev/scope.md` | Tracks local scope details and completion states. The public `docs/PROJECT_SCOPE.md` is the tracked counterpart. |
| `docs/dev/project-understanding.md` | Reconciles direct user decisions, planning PDFs, and observed repository state. |
| `docs/dev/Drought Relief Allocation Planner Project Plan (1).pdf` | Describes the proposed user decision, model, validation, 3D demo, and build schedule. The current viewer implementation lives under `web/`, not the PDF's proposed `prototype/` path. |
| `docs/dev/Website Architecture Drought Relief Allocation Planner.pdf` | Describes proposed pages, module boundaries, two modes, viewer, and demo constraints. It is a plan rather than a record of completed code. |
| `docs/dev/Team To-Do List Conflict-Free Task Lanes.pdf` | Proposes teammate file ownership, handoff shapes, and merge times. Those proposals do not change the actual code layout on their own. |

Generated `__pycache__/`, `.DS_Store`, virtual environments, and real `.env` files are excluded from the architecture because they are not project source.
