# Repository map

This map records the current scaffold and the purpose of each major folder. See [project scope](PROJECT_SCOPE.md) for the end goal and open decisions.

| Location | Purpose and important files |
|---|---|
| `app.py` | Streamlit entry point; registers the six pages in `app_pages/`. |
| `app_pages/` | `1_overview.py` shows reported Iowa corn history; `2_county_risk.py`, `3_scenarios.py`, `4_budget_allocation.py`, `5_method_and_data.py`, and `6_credits.py` are clearly labeled page scaffolds. |
| `src/data_loader.py` | Starter loaders for the master, daily weather, weekly drought, NASS, soil, MODIS, irrigation, and county GeoJSON files. |
| `src/data.py` | Project-specific Iowa corn read/filter boundary used by Overview. |
| `src/features.py` | Future August 15 feature assembly from daily/weekly panels and soil. |
| `src/engine.py` | Future yield-shortfall and scenario crop-value-loss logic. |
| `src/allocation.py` | Future funding-need and county allocation policy logic. |
| `src/render3d.py` | Future satellite county map and optional illustrative 3D scene. |
| `src/ui.py` | Shared Streamlit presentation helpers. |
| `src/build/` | Organizer pipeline reference, not the app's runtime path. `NASS_data_pull.py`, `ACIS_data_pull.py`, `USDM_data_pull.py`, `SSURGO_data_pull.py`, `MODIS_gee_pull.py`, and `NASS_irrigation_pull.py` collect sources; `build_master.py` joins them; `validate_sources.py` checks them. |
| `data/` | Supplied master CSV/parquet, `data_dictionary.md`, and `counties.geojson`. `data/processed/` groups source panels and failure logs under `acis/`, `drought/`, `nass/`, `soil/`, `modis/`, and `irrigation/`. Do not overwrite these inputs with derived tables. |
| `data_processed/` | Reserved for reproducible feature and other derived tables. Only its README exists now. |
| `models/` | Reserved for documented saved final models. Only its README exists now. |
| `validation/` | Reserved for backtest scripts and results. Only its README exists now. |
| `assets/` | Reserved for optional decorative media and a locally bundled 3D viewer. `PROMPTS.md` will record generated asset provenance. No media is included. |
| `notebooks/` | `starter_notebook.ipynb` explores the supplied data. |
| `docs/` | Public scope, this repository map, data specification, implementation notes, briefing, and event description. `docs/readme_notes/` is a staging area for team contributions to the public README. |
| `docs/dev/` | Local planning PDFs and research notes. This folder is ignored by Git and is not part of a clean clone. |
| `.github/ISSUE_TEMPLATE/` | Team submission form template. |
| `requirements.txt` | Pinned Python dependencies for the starter and page scaffold; update when a new package is actually introduced. |
| `.env.example` / `.gitignore` | Configuration template and ignore rules; `.env` holds any eventual secrets and is not committed. |

The architecture PDFs mention a separate `prototype/` viewer. It is not present in this checkout, so the app does not depend on it.
