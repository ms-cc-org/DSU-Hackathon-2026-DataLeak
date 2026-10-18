# Drought Relief Allocation Planner scope

## End goal

Build an evidence-backed August 15 decision tool for a drought-relief budget officer. The officer can inspect county history, apply a historical drought and weather footprint to a base year's insured exposure, see estimated drought insurance payouts, compare a statewide budget, and review county allocations. County and state maps require a satellite imagery basemap.

**X, estimated insurance payouts, is the headline dollar figure.** Y, estimated deductible exposure, and Z, an illustrative relief allocation under a 95% coverage assumption, are supporting figures. Z is not a prediction of an official USDA or state payment. A historical-footprint scenario is an assumption about conditions, not a weather forecast.

## Moving parts and current state

| Part | Intended responsibility | Current state |
|---|---|---|
| Supplied and RMA data | County crop history, dated drought and weather, soil, insured liability and acres, insurance-loss labels | Organizer data is under `data/`; prepared Iowa and Nebraska corn/soybean RMA rows are under `usda_budget_data/`. |
| August 15 inputs | Use only drought maps released by August 15 and weather observed before it | `organize_usda_data.py` builds the RMA model inputs; Lane 2 stores a prebuilt inference copy in `app/model/artifacts/`. |
| Prediction engine | Fit D offline and return county X/Y/Z with range flags | `app/model/build_artifacts.py` creates test and full D/C bundles; `src/engine.py` provides cached `predict`, `scenario`, and `replay`. |
| Validation | Compare D with simple USDA-style baselines, including a held-out historical test | Existing `app/model/results/` reports cover pooled Iowa/Nebraska corn/soybean testing; `iowa_corn_test_slice.md` isolates Iowa corn. |
| Funding and allocation | Compare a fund with modeled payouts and apply explicit county allocation rules | `src/allocation.py` and the budget page remain a Lane 3 boundary; policy rules are not yet implemented. |
| User interface | History, scenarios, budget, method, and credits pages | Overview and the Iowa-corn historical-footprint Scenario page now render data; the allocation page still needs Lane 3 wiring. |
| County visualization | Satellite basemap and county overlays | Boundary exists; provider and final map wiring remain open. |

## Confirmed analytical contract

- The initial app decision view is Iowa corn. The current model is trained on Iowa and Nebraska, corn and soybeans; Iowa-corn results must be reported separately.
- D is the current model: Tweedie GLM with alpha 0.001, power 1.5, uncalibrated. Its features and settings remain fixed for this Lane 2 integration. C supplies historical neighbors and a rough scenario range.
- `d_test.joblib` uses 2000–2015 fit rows and replays 2016–2025 out of sample. `d_full.joblib` refits the same settings on 2000–2025 for live historical-footprint scenarios; those years are in sample for that fit.
- A scenario retains the base year's insured exposures and non-climate features, substitutes **all modeled drought and weather fields** from a footprint year for selected counties, and applies acreage and price multipliers only to dollar conversion.
- X = predicted payout share × insured liability. Y and Z use predicted damaged acres, full crop value per insured acre, and average coverage as documented in [the Lane 2 contract](lane2_contract.md). All three are estimates.
- County identifiers are five-character FIPS text. Missing insurance records are not zero payouts. Full-season weather and hindsight fields must not enter decision-time predictions.

## Decisions still needed

1. Define Lane 3's fund amount, eligibility trigger, county share rule, and whether it uses X or a distinct relief policy amount.
2. Choose a satellite imagery provider and resolve network access, attribution, and any credentials for the demo.
3. Decide when and how model D will be replaced or retained after review. Keep the Lane 2 output columns stable for the app and Lane 3.

## Scope guardrails

Do not call X total crop-value loss, Y a measured deductible bill, or Z an actual program payout. Do not present historical-footprint scenarios as a forecast. Show held-out results separately from in-sample replays, and display the known uncertainty and model misses. Additional crops and states can be exposed only with their own clearly scoped evaluation.
