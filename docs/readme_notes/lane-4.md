# Lane 4 notes: app, 3D, and assets

Branch: `lane-4-app`. Files owned: `app.py`, `web/render3d.py`, `web/ui.py`, `web/pages/1_overview.py`,
`2_county_risk.py`, `5_method_and_data.py`, `6_credits.py`, `web/assets/`, `README.md`, `requirements.txt`,
`.env.example`, `.gitignore`, `.streamlit/config.toml` (theme).

## What is built

- **Scope:** all four states (California, Delaware, Iowa, Nebraska), all 253 counties in the boundary file (23 have no
  records and show as "No data"), and all four crops. Iowa corn is the default.
- **Look and motion:**
  - A dark theme that matches the viewer (`.streamlit/config.toml`).
  - Shared motion injected once from `app.py`: fade-up entrances, card hover lift, a title shine and a soft glow on primary buttons. All of it is switched off for visitors who ask their system to reduce motion.
  - Overview: an animated banner drawn in CSS and SVG (inside its own frame, because `st.html` strips SVG), count-up stats, and an animated drought map of all four states with a state switch.

- **3D viewer** (`web/assets/viewer/viewer.html`, embedded by `web/render3d.py`):
  - **Layout:** the canvas on the left and a side panel on the right. The panel can be hidden, and stacks below the canvas on phones.
  - **Camera views:** three named views (State, Aerial, Soil Cutaway) with eased 1.2 s flights. Keys 1-3 select them, and space plays or pauses the years.
  - **Scene:** a procedural county diorama, plus an extruded map of all four states in Mode 1. The map shows all states or one, and heights are scaled to the counties shown.
  - **Crops:** a crop selector in both modes. Mode 2 lists only the crops a county reports.
  - **Offline:** three.js r169 is bundled and inlined, so the viewer needs no network.
- **County risk page:**
  - Counties ranked by expected annual loss, never by average `yield_anomaly_pct`.
  - Drought and cost charts by year.
  - A Visualize button that opens the viewer in Mode 1.
- **Evidence** tab (formerly Method and data, with the credits). Method and data automatically shows CSV and PNG files saved in
  `analysis/validation/results/`, and uses `docs/coverage.csv` if Lane 1 saves it.
- **Caching:** `st.cache_data` on the county tables and the viewer payload. The first load of a page takes about 4 s, and later loads are instant.

## Data handling

- Only rows with `yield_status == "reported"` carry a yield. Missing values stay null and show as "No data", never zero.
- FIPS stays text.
- One helper per language converts the shifted drought scale: `web/ui.py: droughtLabel()` in Python and `levelName()` in the viewer.
- Mode 1 uses the master's full-season drought fields only to describe past years.
- Mode 2 drought levels are the peak level from the crop's season start to Aug 15, taken only from weekly maps inside that window (`loadSeasonPeak`). Corn and soybeans start May 1 and sorghum June 1. Winter wheat is harvested before Aug 15, so it uses its whole Sep-Jun season, and its 2000 season is empty because the Drought Monitor archive starts in Jan 2000.
- Loss is yield below each county's linear trend fitted on 2000-2025. That is hindsight, and it is labeled so.

## Handoffs

- **Lane 3:** the Scenarios and Budget allocation pages are superseded by the **Planner** tab (`web/pages/3_planner.py`).
  Your files stay on disk, unregistered, so nothing you wrote is lost. Step 2 of the Planner calls
  `src/allocation.py: allocate(losses, fund, rule, trigger, minimum_share)` as soon as it exists, following the
  interface in the team to-do list:
  - Input: a DataFrame with `fips`, `county`, `expected_loss`.
  - Output: a table with `county`, `expected_loss`, `amount`, `reason`.

  Until then it shows "Not available yet" and no amounts. The rule and trigger labels it passes are
  "Proportional to expected loss", "Equal split", "Trigger only", "Tiered", "Weeks in D2+" and
  "Expected loss above a threshold".
- **Lane 2 (engine):** the Planner and the viewer's Scenario mode use one prototype lookup, `web/scenario_lookup.py`
  (Python) and `runEngine` in the viewer (JavaScript). Both read the same county records, so they show identical numbers:
  - It takes past years whose Aug 15 drought level matches the input, and reports their median loss and min-max range.
  - It falls back to the nearest 3 years with a warning when there are fewer than 2 matches or the input is out of range.
  - "Predict" weights each level by its 2000-2025 frequency.

  When `src/engine.py` has a scenario function, message Lane 4 with its name and output shape.
- **Lane 1:** the pages and the viewer read `src/data_loader.py` directly. If `src/data.py` gains a shared clean-table
  function, Lane 4 will switch to it.
- **Docs owner:** `docs/ARCHITECTURE_OVERVIEW.md` and `docs/PROJECT_SCOPE.md` still describe `web/render3d.py` as
  "not implemented" and list six pages. Please update them for the four tabs.

## Layout pass (branch `lane-4-layout`)

What changed:

- **Navigation:** four tabs in a top bar (Story, Explore 3D, Planner, Evidence) with pill styling, the brand mark and
  name on the left, and "Iowa · corn · Aug 15 decision" on the right. The sidebar starts collapsed and keeps its caption.
  Tabs have short URLs (`/explore`, `/planner`, `/evidence`).
- **Tokens:** the "dusk field" colors, drought ramp and pill shapes live in `.streamlit/config.toml` and one CSS injector
  (`web/ui.py: applyStyle`). The existing motion is kept and switched off under reduced motion.
- **Fonts:** Bricolage Grotesque, DM Sans and JetBrains Mono are bundled in `static/fonts/` (SIL OFL) and served by
  Streamlit (`enableStaticServing`), so no network is needed. Each font stack has a system fallback.
- **Story:**
  - The dusk hero is drawn in SVG inside its own frame. The two CTAs are real `st.page_link`s pulled up over the hero.
  - Below it: the stats row, three chapters, the drought map, the evidence band and the footer.
  - **The sticky pin worked:** the map column stays in view while the chapters scroll (checked at 1440x900). It only
    applies at 900px and wider; on phones the columns stack.
- **Explore 3D:**
  - The viewer is inline at full width: a 586px canvas with the year card under it and a 360px panel beside it.
  - The slider is sized so its thumb sits under each bar's center. Measured offsets were 0.0px at 1440 and at 390 wide.
  - Play now stops at 2025 instead of looping.
  - The old Visualize button is gone. A card's "Open in 3D" button loads that county into the viewer.
- **Planner:** step 1 uses `web/scenario_lookup.py`; step 2 is pending (see Handoffs).
- **Evidence:** the Method and data content, then the credits (`web/credits.py`).

Things to know:

- **"None" color:** the drought ramp has no color for "no drought" (it starts at D0), so "None" uses a muted sage `#5E7F6B`.
  "No data" is `#2A333C`.
- **Hero frame:** the spec asked for `components.html`. This Streamlit version marks it deprecated, so the hero and the viewer
  use `st.iframe`, which does the same thing.
- **Phone navigation:** at phone width Streamlit folds the top tabs into its menu button (the » icon). This is Streamlit's
  own behavior.
- **Explore 3D on phones:** the viewer frame has a fixed height, so the side panel scrolls inside the frame below the year card.
- **Evidence band:** the cards read `analysis/validation/results/` and `docs/coverage.csv`, which don't exist, so they show
  "Not validated yet". Lane 2's tested results are in `app/model/results/` (test_report.md, validation_report.md). That
  model predicts **insurance payouts**, not the crop-value loss this app shows, so I did not wire its numbers into the
  evidence band or the Planner. Decide with Lane 2 whether and how to present them.
- **Decision label:** "Iowa · corn" in the top bar matches the default view, but the app covers four states and four crops.

## Higgsfield

Not generated: the free plan blocks generation (see `web/assets/PROMPTS.md`). The app runs without media.

## Backup demo recording (manual)

Record the screen yourself (macOS: Shift-Command-5) following this path:

1. Story: scroll the chapters past the pinned map.
2. Explore 3D: Play through 2010-2013, pause on 2012, click a bar, then Soil Cutaway.
3. State view: hover a county, then click it to fly in. Switch to Scenario.
4. Planner: Mahaska County, corn, 2026, Predict, then D3.
5. Evidence.
