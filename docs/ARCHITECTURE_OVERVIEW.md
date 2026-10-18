# Architecture overview

This document describes the **current repository layout** after grouping related files. The root `app.py` remains the launch command; the Overview reads supplied data, and the Scenario page calls Lane 2's offline-fitted prediction engine. The allocation page and satellite map still need wiring.

## How the pieces connect

```text
app.py → web/pages/ → src/data.py → src/data_loader.py → data/
                    → src/engine.py → app/model/artifacts/ ← app/model/build_artifacts.py
                                               ↑                    ↑
                                        app/model/ models   usda_budget_data/ + source panels
                    → src/allocation.py (Lane 3 boundary)
                    → web/render3d.py (map boundary)
```

`data/processed/` contains supplied source panels, and `data/derived/` is reserved for new feature tables. `usda_budget_data/` contains prepared RMA insurance model rows. `app/model/` owns the current model research, saved artifacts, and official test reports; `web/` owns presentation.

## Root and submission

| File or folder | Purpose |
|---|---|
| `app.py` | Starts the Streamlit app and registers six pages from `web/pages/`. It stays at the root so `python -m streamlit run app.py` remains the launch command. |
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
| `web/pages/` | Holds the six page scripts registered by `app.py`. Pages are organized in navigation order. |
| `web/pages/1_overview.py` | Displays project context, counts, and a descriptive chart from reported Iowa corn yields. It does not produce a loss prediction. |
| `web/pages/2_county_risk.py` | Reserves the historical county-risk view and a future satellite county map. It currently labels the unfinished view. |
| `web/pages/3_scenarios.py` | Runs Iowa-corn historical-footprint scenarios through `src.engine` and displays statewide X/Y/Z, county estimates, a rough range, and analog years. |
| `web/pages/4_budget_allocation.py` | Reserves statewide funding and county-allocation comparisons. It currently shows no calculated payment or recommendation. |
| `web/pages/5_method_and_data.py` | Explains the August 15 data cutoff and model limitations. Its old placeholders need Lane 4 wording updates to display the new RMA test results. |
| `web/pages/6_credits.py` | Lists the starter data sources and placeholders for later imagery, price, RMA, team, and AI credits. It must be completed as those sources are added. |
| `web/pages/README.md` | Describes what the six pages currently do and which results remain pending. |
| `web/ui.py` | Provides the shared `showPending` message used by unfinished pages. It keeps placeholder wording consistent. |
| `web/render3d.py` | Marks the future satellite-map and illustrative 3D-view boundary. No renderer or imagery tiles are included. |
| `web/assets/` | Reserves one home for optional decorative media and any locally bundled viewer library. Assets must not supply analytical results. |
| `web/assets/README.md` | Defines the role and evidence boundary for visual assets. |
| `web/assets/PROMPTS.md` | Will record prompts and provenance if generated visual media is later used. No generated assets are recorded yet. |

## Data and core logic

| File or folder | Purpose |
|---|---|
| `src/` | Holds data access and app-facing analytical logic, separate from Streamlit pages. Overview uses the Iowa corn history filter, and Scenarios calls the cached Lane 2 engine. |
| `src/data_loader.py` | Loads the supplied master table, source panels, and county GeoJSON from stable repository paths. These are organizer-provided helpers. |
| `src/data.py` | Filters the master table to Iowa corn while retaining missing-yield records and five-character FIPS. Overview uses this module for real descriptive data. |
| `src/features.py` | Reserves construction of drought/weather/soil features known by August 15. No derived feature table has been built. |
| `src/engine.py` | Loads fitted D/C artifacts once and exposes stable `predict`, `scenario`, and `replay` contracts for insured payout and budget illustrations. |
| `src/allocation.py` | Reserves funding-need and county-allocation policy rules. It remains empty until the relief policy is defined. |
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

## Documentation and local planning

| File or folder | Purpose |
|---|---|
| `docs/` | Holds public project scope, this architecture record, event guidance, and data specifications. Its `dev/` subfolder is local-only. |
| `docs/ARCHITECTURE_OVERVIEW.md` | Explains each folder and file in the grouped repository, plus the current/planned data flow. |
| `docs/PROJECT_SCOPE.md` | Tracks the ultimate goal, confirmed decisions, core moving parts, current state, and open decisions. |
| `docs/lane2_contract.md` | Specifies the fitted artifacts, prediction function signatures, output units, scenario semantics, and handoff to Lane 3. |
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
| `docs/dev/Drought Relief Allocation Planner Project Plan (1).pdf` | Describes the proposed user decision, model, validation, 3D demo, and build schedule. Its claimed prototype is not present in this checkout. |
| `docs/dev/Website Architecture Drought Relief Allocation Planner.pdf` | Describes proposed pages, module boundaries, two modes, viewer, and demo constraints. It is a plan rather than a record of completed code. |
| `docs/dev/Team To-Do List Conflict-Free Task Lanes.pdf` | Proposes teammate file ownership, handoff shapes, and merge times. Those proposals do not change the actual code layout on their own. |

Generated `__pycache__/`, `.DS_Store`, virtual environments, and real `.env` files are excluded from the architecture because they are not project source.
