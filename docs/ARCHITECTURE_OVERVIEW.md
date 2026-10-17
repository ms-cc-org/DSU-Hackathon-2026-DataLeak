# Architecture overview

This document describes the **current repository layout** after grouping related files. The root `app.py` remains the launch command; the running Overview reads supplied data, while the feature, prediction, allocation, validation, and satellite-map paths are still scaffolds.

## How the pieces connect

```text
app.py → web/pages/ → src/data.py → src/data_loader.py → data/
                         planned: src/features.py → src/engine.py → src/allocation.py
                         evidence: analysis/validation/ and analysis/models/
                         display: web/render3d.py → web/pages/
```

`data/processed/` contains supplied source panels, and `data/derived/` is reserved for new feature tables. `analysis/` holds exploratory notebooks and future model/validation artifacts; `web/` owns everything used to present the tool.

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
| `web/pages/3_scenarios.py` | Reserves the hypothetical drought, acreage, and corn-price workflow. It currently shows no model estimate. |
| `web/pages/4_budget_allocation.py` | Reserves statewide funding and county-allocation comparisons. It currently shows no calculated payment or recommendation. |
| `web/pages/5_method_and_data.py` | Explains the proposed August 15 data cutoff and separates crop-value loss from insurance and relief payments. It explicitly says that no backtest result exists yet. |
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
| `src/` | Holds data access and future analytical logic, separate from Streamlit pages. The app currently calls only the Iowa corn history filter. |
| `src/data_loader.py` | Loads the supplied master table, source panels, and county GeoJSON from stable repository paths. These are organizer-provided helpers. |
| `src/data.py` | Filters the master table to Iowa corn while retaining missing-yield records and five-character FIPS. Overview uses this module for real descriptive data. |
| `src/features.py` | Reserves construction of drought/weather/soil features known by August 15. No derived feature table has been built. |
| `src/engine.py` | Reserves yield-trend, loss-model, historical-analog, and scenario-dollar logic. No model exists in this module yet. |
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
| `analysis/models/` | Reserves a location for documented trained models. There is no model artifact yet. |
| `analysis/models/README.md` | Lists the training, version, and evidence details that should accompany a saved model. |
| `analysis/validation/` | Reserves walk-forward backtest code and results. It is separate from the interactive demo. |
| `analysis/validation/README.md` | States the August 15 cutoff, earlier-year training, baseline, and sample-count requirements for future validation. |

## Documentation and local planning

| File or folder | Purpose |
|---|---|
| `docs/` | Holds public project scope, this architecture record, event guidance, and data specifications. Its `dev/` subfolder is local-only. |
| `docs/ARCHITECTURE_OVERVIEW.md` | Explains each folder and file in the grouped repository, plus the current/planned data flow. |
| `docs/PROJECT_SCOPE.md` | Tracks the ultimate goal, confirmed decisions, core moving parts, current state, and open decisions. |
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
