# HARVEST prediction contract

## What the app estimates

| Workflow | Learned/estimated quantity | Dollar output | Coverage |
|---|---|---|---|
| Insurance | D predicts payout share and damaged-acre share | X: insurance payouts; Y: deductible exposure; Z: illustrative 95% relief | IA/NE, corn/soybeans, insured records |
| Planner | Historical yield shortfall below a county trend | Trend yield × loss fraction × latest planted acres × assumed price | Four supplied states/crops where usable history exists |

D is a **Tweedie GLM, alpha 0.001, power 1.5, uncalibrated**. Its 25 ordered features are drought, weather, soil, irrigation, crop history and state/crop indicators. The exact order and training bounds are saved with the artifact; missing features use its training-fitted imputer. C supplies historical neighbors/ranges, not the headline prediction. Baselines and other candidates remain in the [model reports](../../app/model/results/test_report.md).

## Artifacts

| File in `app/model/artifacts/` | Purpose |
|---|---|
| `d_test.joblib` | D fits for both targets and C neighbor pools trained on 2000–2015; used for held-out 2016–2025 replay. |
| `d_full.joblib` | Same settings refit on 2000–2025 for scenario use. Historical years are in sample for this fit. |
| `scenario_inputs.parquet` | Prebuilt August 15 features/exposure, without outcome labels. |
| `build_report.json` | Fit counts and reproduction differences against saved official statewide predictions. |

If artifacts are missing, run `python app/model/build_artifacts.py` once from the repository root after preparing the source data and saved official outputs. It must reproduce IA 2023 and NE 2022 statewide D payouts within $1. Do not train inside a request or rerun the already completed official test as a routine check. Original model protocol: [model README](../../app/model/README.md) and [decisions](../../app/model/DECISIONS.md).

## Engine API

Existing public names/keywords are preserved:

```python
predict(features_df, model="full")
scenario(base_year, footprint_year, state="IA", crop="CORN",
         counties=None, acres_scale=1.0, price_scale=1.0)
replay(year)
```

`predict` needs one row per county/crop/year: five-character FIPS, county/state, crop/year, all ordered features, positive insured liability (USD), insured acres and average coverage in (0, 1]. `full_crop_value` (USD) defaults to liability / coverage. Duplicate keys and invalid exposure are rejected.

| Returned columns | Meaning / units |
|---|---|
| `fips`, `county`, `state`, `crop`, `year` | Identifiers; FIPS remains text. |
| `pred_payout_share`, `pred_damaged_acre_share` | Direct predictions, unitless fractions in [0, 1]. |
| `liability`, `insured_acres`, `avg_coverage` | Original insured exposure: USD, acres, fraction. |
| `X_payout_usd`, `Y_deductible_exposure_usd`, `Z_relief_95pct_usd` | Calculated amounts in USD. |
| `out_of_range`, `out_of_range_features` | Boolean/list for features outside training min/max. Missing values are separately imputed, not counted as out of range. |

`scenario` uses the full fit: base-year exposure/non-climate features plus **all** drought/weather fields from the footprint year. A county selection substitutes only those counties; the returned county table still covers the base-year state/crop. Positive acreage/value multipliers scale dollar conversion afterward, leaving learned shares unchanged. Returns county table, X/Y/Z totals, C range, three closest historical years, range flags and metadata.

`replay` uses the test fit for 2016–2025 (out of sample), otherwise the full fit for 2000–2015 (in sample). It returns county rows, state totals and provenance. Engine scenario/replay also return `reserve_band_x_usd`; replay keys this range by state.

## Website adapter and assumptions

`src.insurance_scenarios` exposes:

```python
projectInsurance(targetYear, state="IA", baseYear=None, footprintYears=None,
                 crops=None, acresScale=1.0, priceScale=1.0)
historicalInsuranceScenario(baseYear, footprintYear, state="IA", crops=None,
                            acresScale=1.0, priceScale=1.0)
replayInsurance(year, state="IA", crops=None)
```

Future years are 2026–2030, default 2026; exposure defaults to 2025. Each selected historical climate year supplies its complete spatial pattern across selected counties/crops. With all seasons selected, every 2000–2025 footprint receives equal weight. County outputs are means; statewide percentiles are computed from complete scenario totals, never by summing county percentiles.

Adapters return `countyTable`, `drawTable`, `modelInputs`, `scenarioTotals`, `totals`, `metadata`, `range`, `flaggedRows`, `imputedInputRows`. The UI cache adds requested `selection` and included `crops` to the manifest. Exported rows retain source, artifact, training/exposure/footprint years, scaling and flags. Scenario exposure columns (`scenarioLiabilityUsd`, `scenarioInsuredAcres`, `scenarioFullCropValueUsd`) reflect the selected multipliers; original exposure columns stay unchanged.

After the first run, any control change refreshes all outputs together. Map heights/colors use county X summed across **only the selected crops**; county/state shares use liability/acreage weights. Grey counties lack estimates. A failed refresh removes stale metrics, map and downloads. Prediction/source breakdowns identify D; main headings say “Predicted results.”

## Dollar formulas and wording

```text
X = payout share × scenario insured liability
damaged acres = damaged-acre share × scenario insured acres
full value per acre = scenario full crop value / scenario insured acres
Y = damaged acres × full value per acre × (1 − average coverage)
Z = damaged acres × full value per acre × max(0, 0.95 − average coverage)
```

**X = estimated insurance payouts** (headline). **Y = estimated deductible exposure**. **Z = illustrative relief allocation under a 95% coverage assumption**, not an actual program payment. X is not total crop-value loss. The Planner's separate historical lookup is not validated by D's evaluation.

Three ranges have different meanings: the website ensemble's 10th–90th spread is historical climate sensitivity; C's range is a rough historical-neighbor range widened around D; the backend planning band is statewide X × approximately [0.063, 1.978], derived from 2006–2015 out-of-sample misses. None is a guaranteed forecast interval. D has no year trend feature, so changing only a future year label leaves predictions unchanged.

The separate drought-severity Task A/B models are not connected to these calculations. Their outputs cannot directly replace D's required weekly/area drought features. Follow [verification](verification.md) for any model-related change.
