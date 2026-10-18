# Lane 4 notes: app, 3D, and assets

Branch: `lane-4-app`. Files owned: `app.py`, `web/render3d.py`, `web/ui.py`, `web/pages/1_overview.py`,
`2_county_risk.py`, `5_method_and_data.py`, `6_credits.py`, `web/assets/`, `README.md`, `requirements.txt`,
`.env.example`, `.gitignore`.

## What is built

- **3D viewer** (`web/assets/viewer/viewer.html`, embedded by `web/render3d.py`):
  - **Layout:** the canvas on the left and a side panel on the right. The panel can be hidden, and stacks below the canvas on phones.
  - **Camera views:** three named views (State, Aerial, Soil Cutaway) with eased 1.2 s flights. Keys 1-3 select them, and space plays or pauses the years.
  - **Scene:** a procedural county diorama, plus an extruded Iowa state map in Mode 1.
  - **Offline:** three.js r169 is bundled and inlined, so the viewer needs no network.
- **County risk page:**
  - Counties ranked by expected annual loss, never by average `yield_anomaly_pct`.
  - Drought and cost charts by year.
  - A Visualize button that opens the viewer in Mode 1.
- **Overview, Method and data, Credits** pages. Method and data automatically shows CSV and PNG files saved in
  `analysis/validation/results/`, and uses `docs/coverage.csv` if Lane 1 saves it.
- **Caching:** `st.cache_data` on the county tables and the viewer payload. The first load of a page takes about 4 s, and later loads are instant.

## Data handling

- Only rows with `yield_status == "reported"` carry a yield. Missing values stay null and show as "No data", never zero.
- FIPS stays text.
- One helper per language converts the shifted drought scale: `web/ui.py: droughtLabel()` in Python and `levelName()` in the viewer.
- Mode 1 uses the master's full-season drought fields only to describe past years.
- Mode 2 drought levels are the peak level from May 1 to Aug 15, taken from weekly maps dated on or before Aug 15 (`loadAsOfSeverity`).
- Loss is yield below each county's linear trend fitted on 2000-2025. That is hindsight, and it is labeled so.

## Handoffs

- **Lane 3 (Scenarios page):** the 3D sandbox is ready. To add it to `web/pages/3_scenarios.py`:

  ```python
  from web.render3d import showViewer
  showViewer("sandbox", "19123")   # county FIPS as text
  ```

  The sandbox has its own inputs in the side panel: county, crop, year 2000-2030 (2026-2030 labeled projected),
  drought level D0-D4, Predict for projected years, and price.
- **Lane 2 (engine):** the sandbox currently runs a prototype lookup in the browser:
  - It takes past years whose Aug 15 drought level matches the input, and reports their median loss and min-max range.
  - It falls back to the nearest 3 years with a warning when there are fewer than 2 matches or the input is out of range.
  - "Predict" weights each level by its 2000-2025 frequency.

  When `src/engine.py` has the scenario function, the sandbox numbers should come from it. Message Lane 4 with the function
  name and output shape, and Lane 4 will pass its results into the viewer.
- **Lane 1:** the County risk page and the viewer read `src/data_loader.py` directly. If `src/data.py` gains a
  shared clean-table function, Lane 4 will switch to it.
- **Docs owner:** `docs/ARCHITECTURE_OVERVIEW.md` and `docs/PROJECT_SCOPE.md` still describe `web/render3d.py`
  as "not implemented" and say maps need a satellite basemap. The team's architecture doc chose a three.js
  map that works offline instead. Please update those rows, or tell Lane 4 if a satellite basemap is still required.

## Higgsfield

Not generated: the free plan blocks generation (see `web/assets/PROMPTS.md`). The app runs without media.

## Backup demo recording (manual)

Record the screen yourself (macOS: Shift-Command-5) following this path:

1. Overview.
2. County risk: the top cards, then pick Mahaska County.
3. Visualize: Play through 2010-2013, pause on 2012, then Soil Cutaway.
4. State view: hover a county, then click it to fly in.
5. Scenarios (once Lane 3 adds the sandbox): set year 2026, choose Predict, then D3.
6. Budget allocation.
7. Method and data.
