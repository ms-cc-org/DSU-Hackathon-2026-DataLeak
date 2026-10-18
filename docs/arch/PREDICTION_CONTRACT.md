# Connected prediction and planning contract

## What is predicted

| Workflow | Direct prediction or estimate | Calculated output | Scope |
|---|---|---|---|
| Insurance model D | T1: drought insurance payout share; T2: drought-damaged insured-acre share | X: estimated insurance payouts; damaged acres; Y: deductible exposure; Z: illustrative relief under 95% coverage | Iowa and Nebraska; corn and soybeans; insured records only |
| Crop-loss Planner | Historical lookup of yield loss below trend; linear projection of trend yield | Estimated crop-value loss = trend yield × loss fraction × latest planted acreage × assumed price | All supplied states and crops where history supports an estimate |
| Imagery map | No prediction | Geographic imagery with calculated result overlays | Supplied county boundaries; imagery requires network access |

The active app has four tabs: Story, Explore 3D, Planner and Insurance. Insurance is registered at `/insurance`; it is no longer a hidden page. Story and the county Planner link to it. The state-fund section has been removed from Planner. The historical crop-loss lookup and the trained insurance model answer different questions and use separately disclosed assumptions.

## Insurance user inputs

- Mode: future insurance scenario, historical footprint scenario, or historical replay.
- State: IA or NE. Crop selection: corn, soybeans, or both insured crops together.
- Future target year: 2026–2030, default **2026**, the first year after the supplied data ends. The separate crop-loss Planner also defaults to 2026 and uses uniform projected-year labels.
- Insured exposure base year: a saved year from 2000–2025; future scenarios default to 2025.
- Climate assumption: repeat a selected historical season or evaluate every 2000–2025 historical season once with equal weight. Historical footprint mode uses a single historical footprint with the target year's insured exposure.
- Positive insured-acre and insured crop-value multipliers. They scale exposure/dollar conversion after inference, not model features or learned shares. A value multiplier is not a forecast market price.

After the first **Run predictions**, every change to state, crop, mode, year, climate footprint, exposure year or multiplier automatically refreshes the inference result. Headline X/Y/Z, weighted shares, the 3D county map, crop breakdowns, audit inputs, historical comparisons and downloads all use that same selected result. A failed refresh removes the old predictions and exports instead of leaving stale values visible; a later valid change retries inference. The result caption names the included crops, exports include crop-specific filenames, and the manifest records both the selection and actual included crops.

All climate features are copied together from a historical footprint for each county/crop. Each ensemble member uses the same historical year across the selected counties and crops, preserving the observed spatial pattern. The base year's insured exposure, coverage, soil, irrigation and lagged crop-history features remain assumptions. Missing model features use the saved training-fitted imputer and are explicitly listed in the input audit. Missing insured county/crop rows are outside the run, not zero payouts.

The future ensemble is a historical sensitivity exercise. Its mean is not a calibrated forecast of next year's weather or a set of learned future drought probabilities. D has no year feature: changing only 2026 to 2027 with identical assumptions does not change predicted shares or dollars. The target year is a scenario label; future feature trajectories would require additional modeled assumptions.

## Fitted models and provenance

Model D remains a Tweedie GLM, alpha 0.001, power 1.5, uncalibrated. Features, preprocessing and fit settings were not changed. Fitted bundles load once per process; no request trains a model.

- Future and historical what-if scenarios use `d_full.joblib`, fitted on 2000–2025.
- Replay for 2016–2025 uses `d_test.joblib`, fitted on 2000–2015, and is labeled out of sample.
- Replay before 2016 uses the full artifact and is labeled in sample.
- Historical footprint scenarios use the full fit and are explicitly labeled in-sample what-ifs, not held-out replays.
- Model C provides nearest historical years and its existing rough payout range for the inspected input footprint. That range is separate from the future ensemble spread and is not a calibrated interval.

Each model result identifies the artifact, training years, mode, target year, exposure base year, footprint years, model settings and multipliers. The county prediction CSV includes both directly predicted shares, X/Y/Z, raw base exposure, scenario-scaled exposure, flags and source labels. Separate downloads provide every exact model input and a JSON run manifest.

## Dollar formulas

```text
X = predicted payout share × scenario insured liability
damaged acres = predicted damaged-acre share × scenario insured acres
full value per acre = scenario full insured crop value / scenario insured acres
Y = damaged acres × full value per acre × (1 − average coverage)
Z = damaged acres × full value per acre × max(0, 0.95 − average coverage)
```

X is estimated insurance payouts, not total crop-value loss. Y is estimated deductible exposure, not an observed bill. Z is an illustrative allocation under a 95% coverage assumption, not an official USDA/state payment. Statewide payout share is liability-weighted; statewide damaged-acre share is acreage-weighted.

For a future ensemble, each county/crop's headline quantities are means across the complete historical-footprint runs. Statewide totals are summed inside each run before calculating the 10th–90th percentile spread. Individual county percentiles are not summed to manufacture a statewide interval. A single footprint has no ensemble uncertainty range.

## Retained allocation code

The state-fund section is removed from the active Planner. Allocation modules and their proportional rule remain on disk as legacy code; the active site does not collect a fund or distribute county allocations. Planner is a county/crop loss scenario tool, defaulting to 2026. Insurance remains a separate prediction workflow.

## Geography and evidence

Insurance displays a 3D state map using completed county payout predictions, with the statewide USD total above it. County height and amber intensity scale linearly with X relative to the largest county in the completed run; all supplied counties remain visible, unavailable estimates are grey, and selection exposes crop payouts and exposure-weighted shares. It uses the Planner viewer’s bundled three.js runtime and local boundaries, with no imagery network dependency. Main labels say “Predicted results”; model D remains identified in source explanations and exports.

County allocation maps use transparent county overlays on public USGS imagery. Imagery is background context, not a predicted image or model input. The selected metric is unavailable for grey counties. The county-outline alternative uses local geometry and makes no imagery requests. Plotly's documented public imagery layer and attribution are used; no provider key is required: [Plotly tile layers](https://plotly.com/python/tile-map-layers/).

Saved insurance reports remain under `app/model/results/` for developer review, including statewide errors, top-20 capture, range coverage, baseline comparisons, state-year actuals and the Iowa corn slice. The website has no Evidence tab or links to it; Insurance replay still shows historical actuals. The complete official report exposes its evaluation caveats. Those reports do not validate the separate all-crop lookup or the hypothetical future ensemble. The all-crop lookup's missing held-out validation remains visible.

## Public adapter functions

```python
from src.insurance_scenarios import (
    projectInsurance, historicalInsuranceScenario, replayInsurance,
)

future = projectInsurance(2026, state="IA", baseYear=2025)
historicalWhatIf = historicalInsuranceScenario(2023, 2012, state="IA", crops=["CORN"])
heldOutReplay = replayInsurance(2023, state="IA")
```

`projectInsurance` accepts optional `footprintYears`, `crops`, `acresScale` and `priceScale`. `footprintYears=None` evaluates all saved historical seasons once. All adapters return `countyTable`, `drawTable`, `modelInputs`, `scenarioTotals`, `totals`, `metadata`, `range`, `flaggedRows` and `imputedInputRows`. The original `src.engine` contract remains available and unchanged.

Run `python -m unittest discover -s tests -v`. Tests cover original D reproduction, exact feature substitution, unchanged predictions under year-only relabeling, scenario scaling, ensemble aggregation, input/output exports, all-crop fund conservation, supported/unsupported scope, four-page navigation, replay actuals and map configuration. Functional verification does not establish future predictive accuracy.


## Required verification for insurance/model changes

A model or insurance UI change must be checked through selection → saved inference → aggregation → displayed metrics/map/table → exported predictions and assumptions. Rendering a page successfully is insufficient. Change controls **after** a result exists, without another run click, and confirm the resulting crop/state/year and values across every surface. Cover both states, corn/soybeans/all crops and future/historical-footprint/replay modes; retain failure recovery and Planner navigation checks.

`tests/test_insurance_scenarios.py` compares every county's two predicted shares directly with the frozen D artifacts, then independently calculates X/Y/Z and damaged acres from the audited exposures and documented formulas. It covers 18 mode/state/crop combinations (the future cases use all historical footprints), reconciles weighted statewide shares and verifies CSV content. `tests/test_connected_app.py` verifies the rendered metrics, county/crop table and embedded 3D payload after changing selections, plus stale-result removal on errors. Dollar comparisons use sub-cent tolerances and displayed amounts use the same whole-dollar formatting as the UI. These checks establish faithful presentation of the model output, not future forecast accuracy.
