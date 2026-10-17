# Drought Relief Allocation Planner scope

## End goal

Build a usable, evidence-backed tool for an Iowa drought-relief budget officer making an August 15 decision. The officer should be able to inspect county corn history, enter a hypothetical drought/acreage/price scenario, see expected corn crop-value loss, consider statewide funding need, and compare county allocations and a release trigger. County/state displays require a satellite-imagery basemap. A historical backtest must show how the method performed on years it did not use to learn.

Crop-value loss is an estimate, not an insurance claim or an official relief payment. The scenario describes assumed drought conditions; it does not forecast weather.

## Moving parts and current state

| Part | Intended responsibility | Current state |
|---|---|---|
| Supplied data | Iowa corn yield/acreage, weekly drought, daily weather, soil, county boundaries | Present under `data/`; overview reads real Iowa corn history. |
| August 15 features | Rebuild county/year weather and drought measures using only observations available by the decision date | Module boundary in `src/features.py`; no feature table yet. |
| Loss engine | Fit a training-only yield trend, estimate yield shortfall, and convert it to scenario dollars using entered acres and price | Module boundary in `src/engine.py`; no trained model or prediction yet. |
| Validation | Walk-forward test and simple baselines with counts, error, and county-priority metrics | `validation/` exists; no result yet. |
| Funding and allocation | Translate loss into funding need and divide a chosen fund under explicit, comparable rules | Module boundary in `src/allocation.py`; policy still undecided. |
| User interface | History, scenarios, budget, method, and credits pages | Six pages are wired; only Overview shows descriptive data. |
| County visualization | Satellite basemap, county overlays, and optional illustrative 3D scene | Module boundary in `src/render3d.py`; provider and viewer not selected. |
| Handoff | Run instructions, sources, AI-use disclosure, reproducible artifacts, pitch | README and folder placeholders exist; final handoff not complete. |

## Confirmed choices

- Iowa corn is the initial crop and geography; August 15 is the decision date.
- The scenario cost target is **expected corn crop-value loss for a selected county** from hypothetical drought, planted acres, and corn price.
- The officer needs both statewide funding planning and county allocation support.
- Full public USDA RMA data may be used as a separate insurance-loss comparison. It is not the crop-value-loss training target.
- Maps showing county or state data need a satellite basemap.

## Decisions needed before analytical implementation

1. Define the drought scenario input and whether it describes observations through August 15 or assumed conditions afterward.
2. Decide whether one scenario applies across Iowa or whether counties receive different inputs.
3. Define how much predicted crop-value loss counts as relief funding need, including any eligibility, offsets, caps, triggers, minimum shares, and whether a fixed appropriation is also compared.
4. Choose a satellite imagery provider and resolve its access/attribution needs against the desired offline demo. Locate the separate 3D prototype if it should be reused.
5. Confirm whether scenarios through 2030 and soybean exploration are actually in scope; both appear in planning PDFs but have not been requested as initial build requirements.

## Scope guardrails

Keep the first evidence path at Iowa county scale. Do not present missing yields as zero, use full-season fields as August 15 predictors, display a prediction as an observed fact, call crop-value loss a relief payment, or claim performance before validation. Add visual polish and extra crops only after the core decision and evidence work. The [data dictionary](../data/data_dictionary.md) and [student briefing](briefing/Student-briefing.md) supply the dataset and event constraints.
