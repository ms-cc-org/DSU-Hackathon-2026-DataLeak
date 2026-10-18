# Drought Relief Allocation Planner scope

## End goal

Build an evidence-backed August 15 decision tool for a drought-relief budget officer. The intended geographic and crop scope is every state, crop, and county represented in the supplied dataset, with clear handling for combinations with little or no data. The officer can inspect county history, test drought scenarios, compare a fund, and review county allocations. Fund allocation maps retain a satellite imagery basemap; Insurance uses the requested 3D county payout view.

The active Planner estimates **crop-value loss** from a historical lookup and distributes one state fund across all supported crops in proportion to those estimates. The active **Insurance** tab runs trained model D: it predicts payout share and damaged-acre share and converts them into X (insurance payouts), Y (deductible exposure), and Z (illustrative relief under a 95% coverage assumption). Insurance covers Iowa/Nebraska corn and soybeans, and its results are attached as distinctly labeled context to supported fund runs. Future insurance scenarios reuse historical climate footprints with assumed exposure; historical replay and saved test reports are also connected. The [prediction contract](PREDICTION_CONTRACT.md) distinguishes predictions, assumptions and arithmetic. Z and fund allocations are not official payments, and the crop-loss lookup remains an unvalidated prototype.

## Moving parts and current state

| Part | Intended responsibility | Current state |
|---|---|---|
| Supplied and RMA data | County crop history, dated drought and weather, soil, insured liability and acres, insurance-loss labels | Organizer data is under `data/`; prepared Iowa and Nebraska corn/soybean RMA rows are under `usda_budget_data/`. |
| August 15 inputs | Use only drought maps released by August 15 and weather observed before it | `organize_usda_data.py` builds the RMA model inputs; Lane 2 stores a prebuilt inference copy in `app/model/artifacts/`. |
| Prediction and scenario logic | Connect all-dataset crop loss and supported insurance model predictions with visible provenance | Planner and 3D use the labeled historical lookup. Insurance uses `src/insurance_scenarios.py` over the unchanged fitted D engine for future ensembles, historical footprints and replay. |
| Validation | Show existing D test results and baseline comparisons separately from unvalidated future/lookup estimates | Saved reports remain in `app/model/results/` for the team. Insurance replay retains observed historical comparisons; there is no standalone Evidence page. |
| Funding and allocation | Share one state fund across all supported crops in proportion to estimated crop-value loss | Exact-cent allocations retain their agreed basis. IA/NE runs attach model D corn/soybean context with distinct shares/dollar columns and a link to exact inputs. Unsupported insurance coverage stays blank. |
| User interface | County exploration, loss planning and insurance predictions | Four active tabs: Story, Explore 3D, Planner and Insurance. Source labels and input/output exports identify which numbers came from D, the lookup or policy arithmetic. |
| County visualization | Satellite/aerial basemap and county result overlays | Insurance shows a Planner-style 3D state map with every supplied county, heights/colors from completed payout predictions, and a formatted statewide payout total above it. County selection shows the selected-crop payout breakdown; missing estimates remain grey. Fund allocation maps retain USGS imagery and offline outlines. |

## Confirmed analytical contract

- Iowa corn is the default view, not the full product scope. The supplied data covers California, Delaware, Iowa, Nebraska and corn, soybeans, winter wheat, sorghum. The master has 230 counties; the boundary file has 253, so 23 map counties have no master records. Some state-crop combinations also have no records.
- The active Planner estimates crop-value loss with a prototype lookup and a 2000–2025 hindsight trend, including a labeled linear extension for 2026–2030. It must not be presented as validated or as an insurance payout.
- Next-calendar-year loss projections work through the county Planner, 3D scenario view and all-crop state fund. Their default is the next calendar year when it falls within 2026–2030 (2027 as of October 2026), rather than always the first year after the dataset. The county Planner displays the central dollar loss and historical range. Changing the projected year extends trend yield; drought frequencies and latest acreage remain historical assumptions, not future weather observations.
- Confirmed Lane 3 policy: one user-entered fund per selected state and scenario year, shared across **all supported crops together**, proportional to each county/crop's central crop-value-loss estimate. County allocations add the shares of their supported crops. A crop display filter never changes the fund denominator.
- State scenarios apply a single chosen hypothetical D0–D4 level to all county/crop combinations (D2 by default). Crop prices are independent editable assumptions in dollars per bushel; acreage is the latest reported planted acres, with its year retained in the export. The state form has independent controls from the county scenario.
- No extra drought eligibility trigger, minimum award, per-crop fund, or loss cap is applied by this initial proportional rule. The whole fund is distributed when positive estimates exist, even if the fund exceeds covered estimated loss; that case is explicitly flagged. With no positive estimates, the fund remains unallocated.
- Every supplied boundary county × each of the four crops remains visible. Missing crop records, insufficient usable history/trend, missing acreage or nonpositive projected yield mean an unavailable estimate and no calculated allocation, not zero loss. Nearest-year fallback estimates are included but flagged as uncertain. County totals with missing crops are marked partial; aggregate loss is only for covered records.
- The current RMA model is trained on Iowa and Nebraska corn and soybeans only; Iowa-corn results must be reported separately. It cannot supply the all-state, all-crop allocation by itself.
- Future insurance scenarios default to 2026, the first year after the dataset ends, and use the full artifact with explicit historical climate and insured exposure assumptions. All historical seasons can be evaluated with equal weight; their spread is sensitivity, not calibrated future weather probabilities. D has no year feature, so year-only relabeling cannot change its predictions. Historical footprint scenarios use the full fit and are labeled in sample; held-out replay remains separate.
- D is the current model: Tweedie GLM with alpha 0.001, power 1.5, uncalibrated. Its features and settings remain fixed for this Lane 2 integration. C supplies historical neighbors and a rough scenario range.
- `d_test.joblib` uses 2000–2015 fit rows and replays 2016–2025 out of sample. `d_full.joblib` refits the same settings on 2000–2025 for live historical-footprint scenarios; those years are in sample for that fit.
- A scenario retains the base year's insured exposures and non-climate features, substitutes **all modeled drought and weather fields** from a footprint year for selected counties, and applies acreage and price multipliers only to dollar conversion.
- X = predicted payout share × insured liability. Y and Z use predicted damaged acres, full crop value per insured acre, and average coverage as documented in [the Lane 2 contract](lane2_contract.md). All three are estimates.
- County identifiers are five-character FIPS text. Missing insurance records are not zero payouts. Full-season weather and hindsight fields must not enter decision-time predictions.

## Remaining limitations and future decisions

1. Model accuracy, missing crop coverage and future weather prediction remain analytical limitations. The functional connections do not validate the all-crop lookup or future ensemble.
2. Keep D's features/settings fixed for this integration and its output contract stable if a future review replaces it. Do not extend it to untrained states/crops or change the confirmed fund basis without a new decision.
3. Additional allocation rules, eligibility triggers, minimum awards, loss caps and causal effects of relief remain outside the confirmed initial rule. Imagery needs internet; county outlines and all numerical workflows remain usable locally.

## Scope guardrails

Do not call X total crop-value loss, Y a measured deductible bill, or Z an actual program payout. Do not present either scenario path as a weather forecast. Show held-out results separately from in-sample replays, and display the known uncertainty and model misses. All states and crops may be explored from supplied records, but thin coverage and the prototype status must stay visible; RMA model outputs remain limited to their evaluated crop/state combinations.

## Insurance result presentation

Main headings, controls and metrics use “Insurance predictions” and “Predicted results.” Model D remains identified in prediction/source breakdowns, exact-input explanations and exported provenance. The 3D map displays X from the completed run, sums included crops by county, and computes county shares with insured exposure weights; it does not run the crop-loss lookup or change any model settings. It replaces the former 2D insurance payout map.

Insurance selections refresh every result view automatically after the first run. Displayed totals, county details, input audit and downloads must share the active crop/state/scenario scope. All future model-related changes must reconcile the displayed values with saved-model inference and the documented dollar formulas as specified in `docs/PREDICTION_CONTRACT.md`; stale predictions must disappear on refresh failure.

## Website cleanup

The Evidence tab, its page file, report renderer and cross-page links are removed. Story no longer carries the related report cards. Saved model evaluations remain in the repository, while Insurance retains the source details and historical comparisons needed to interpret its predictions. The active navigation is Story, Explore 3D, Planner and Insurance.

The top navigation shows the brand and page tabs without the former state/crop/decision-date tagline.
