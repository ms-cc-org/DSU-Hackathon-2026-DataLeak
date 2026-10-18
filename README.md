# HARVEST

County crop history, drought scenarios and insurance payout predictions for agricultural planners.

## Run locally

Python 3.11+ is required. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open [HARVEST](http://localhost:8501). On Windows, activate with `.venv\Scripts\Activate.ps1`. The app uses local files; no database or API key is needed. The bundled 3D views work offline and require WebGL.

Insurance requires the saved files in `app/model/artifacts/`. If missing, follow the [artifact instructions](docs/engineering/predictions.md#artifacts); model fitting is an offline step, never part of a page request.

## Pages

| Tab | Purpose |
|---|---|
| Story | Project introduction and historical drought map. |
| Explore 3D | County history, crop comparisons and interactive state/county scenes. |
| Insurance | Predicted insurance payouts, county maps, crop breakdowns and downloadable inputs/results. |
| Planner | County crop-loss scenarios for 2026–2030; defaults to 2026. |

History and Planner cover California, Delaware, Iowa and Nebraska, with corn, soybeans, winter wheat and sorghum where records exist. Insurance covers **Iowa/Nebraska corn and soybeans only**. The dataset ends in 2025. Future results use assumptions to make historical climate prediction. They are not weather forecasts. Missing historical records are not zero losses.

After the first Insurance run, changing a selection refreshes every result view. Planner uses a separate historical crop-loss lookup.

## Documentation and checks

Start with the [documentation index](docs/README.md): scope, architecture, prediction contract, data guide, verification and event requirements.

```bash
python -m unittest discover -s tests -p 'test_connected_app.py' -v
python -m unittest discover -s tests -p 'test_planner_ui.py' -v
```

See the [verification guide](docs/engineering/verification.md) for model-to-display checks and known test limitations.

## Credits and AI use

Data: USDA NASS and RMA; U.S. Drought Monitor; NOAA ACIS; NRCS SSURGO; NASA MODIS; U.S. Census county boundaries. Required source acknowledgements are in the [data guide](docs/data/dataset.md#sources-and-credits).

The app uses Streamlit, pandas, NumPy, Plotly, scikit-learn and bundled three.js r169 (MIT). Bricolage Grotesque, DM Sans and JetBrains Mono are bundled under the SIL Open Font License. Code is [MIT licensed](LICENSE).

**Claude Code** assisted with modeling, the 3D viewer, initial pages and styling. **OpenAI Codex** assisted with repository organization, insurance integration, UI fixes, documentation and verification. Verification includes saved-model reproduction, independent dollar calculations, reactive selection tests and browser checks. The team remains responsible for explaining the code and its limits. No generated media is included; the hero is drawn with SVG/CSS.
