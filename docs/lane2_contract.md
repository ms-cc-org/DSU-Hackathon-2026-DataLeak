# Lane 2 prediction engine contract

## Purpose and provenance

`src.engine` is the app and Lane 3 entry point for current model D. It loads fitted artifacts once per Python process and never trains on a request. D is the existing Tweedie GLM (alpha 0.001, power 1.5, uncalibrated), using the feature order and preprocessing from `app/model/data.py` and `app/model/tweedie.py`. C is the existing k=25, drought-weight=1.0 historical-neighbor model used for the scenario range and closest years. This integration does not change either model's features or settings.

Run `.venv/bin/python app/model/build_artifacts.py` once after the RMA training/validation data and saved official test predictions are present. The script creates:

| Artifact | Contents |
|---|---|
| `app/model/artifacts/d_test.joblib` | Separate fitted D models for T1 and T2, C neighbor pools for each, training bounds and ordered feature list; fit on insured 2000–2015 rows. |
| `app/model/artifacts/d_full.joblib` | The same objects and settings refit on insured 2000–2025 rows for live historical scenarios. |
| `app/model/artifacts/scenario_inputs.parquet` | August 15 county-crop-year inputs with historical insured exposure where known; no outcome labels. |
| `app/model/artifacts/build_report.json` | Fit row counts and statewide reproduction differences. |

The ignored `usda_budget_data/testing/` input folder is absent from this checkout. The builder recreates its August 15 inputs with the existing `organize_usda_data.build_inputs()` logic, uses `results/test_predictions.csv` as the official test outcome/exposure source, and writes `results/test_state_years.csv` by aggregating its saved D predictions. This reference is derived from the already saved official test output; it is not an independent run of `final_test.py`. The build fails if the new test artifact differs by $1 or more on IA 2023 or NE 2022 statewide X.

## Public functions

```python
from src.engine import predict, replay, scenario

countyTable = predict(features_df, model="full")
scenarioResult = scenario(
    base_year=2023,
    footprint_year=2012,
    state="IA",
    crop="CORN",
    counties=None,
    acres_scale=1.0,
    price_scale=1.0,
)
replayResult = replay(2023)
```

### `predict(features_df, model="full") -> pandas.DataFrame`

The input needs one row per FIPS × crop × year; five-character FIPS text; county name, state, crop and year; every ordered feature in the artifact; insured liability in USD, insured acres, and average coverage in (0, 1]. `full_crop_value` in USD is optional and otherwise derived as liability / average coverage. `county`/`state` or `county_name`/`state_alpha` are accepted as identifiers. Missing model feature values pass through D's training-fitted imputer. Nonpositive or missing exposures are rejected rather than interpreted as zero.

| Output column | Meaning and unit |
|---|---|
| `fips`, `county`, `state`, `crop`, `year` | County-crop-year identifiers; FIPS remains text. |
| `pred_payout_share` | D T1 estimate, share of insured liability, clipped to [0, 1]. |
| `pred_damaged_acre_share` | D T2 estimate, share of insured acres, clipped to [0, 1]. |
| `liability` | Historical insured liability, USD. |
| `insured_acres` | Historical insured acres. |
| `avg_coverage` | Liability / full insured crop value, unitless share. |
| `X_payout_usd` | **Estimated insurance payouts** = predicted T1 × liability. Headline. |
| `Y_deductible_exposure_usd` | **Estimated deductible exposure** = predicted T2 × insured acres × full value per acre × (1 − coverage). Supporting estimate. |
| `Z_relief_95pct_usd` | **Illustrative relief allocation under a 95% coverage assumption** = predicted T2 × insured acres × full value per acre × max(0, 0.95 − coverage). Supporting illustration, not a program payout forecast. |
| `out_of_range`, `out_of_range_features` | Boolean and list of input model features below/above that artifact's training min/max; missing features are imputed and not counted as beyond range. |

`model="test"` uses the 2000–2015 artifact. `model="full"` uses the 2000–2025 artifact. The return columns stay the same when the model is reviewed or later replaced.

### `scenario(base_year, footprint_year, state="IA", crop="CORN", counties=None, acres_scale=1.0, price_scale=1.0) -> dict`

The base year supplies every insured county row's liability, insured acres, coverage, soil, irrigation and history features. The footprint year supplies **all modeled drought and weather features** for the selected counties. `counties=None` applies it to all insured counties in the state/crop base year; a FIPS sequence applies it only to those counties, leaving the others at base-year conditions. The result still covers all insured base-year counties for a comparable statewide total. Both years must have prebuilt August 15 inputs.

The function always uses `d_full.joblib`. `acres_scale` and `price_scale` are positive multipliers applied to X/Y/Z dollars and the statewide X range **after** D inference. They do not change the fitted model inputs, payout shares, insured liability or insured-acre columns. Their product scales X exactly. The result dictionary contains `county_table`, `statewide_totals` (X/Y/Z USD), `historical_scenario_range_x_usd` (low/high and method), `closest_historical_years` (three C neighbor-pool years ranked by liability-weighted proximity), `out_of_range_summary`, and scenario metadata.

The statewide X range is C's historical-neighbor spread as implemented in `app/model/budget.py`, widened if needed to include D's point estimate. It is a rough historical range, not a calibrated probability interval. The closest-year ranking is an explanatory similarity score, not a forecast probability.

### `replay(year) -> dict`

For 2016–2025, replay uses `d_test.joblib` and labels its estimates `out-of-sample`. For 2000–2015, it uses `d_full.joblib` and labels them `in-sample`. The result contains the county table, a state totals DataFrame, model name, label, year and out-of-range summary. Replay includes every insured Iowa/Nebraska corn/soybean row in that historical year.

## Reporting boundary

The existing official report evaluates Iowa and Nebraska, corn and soybeans together. `app/model/results/iowa_corn_test_slice.md` compares D, B2a and B2b on Iowa corn only using existing saved test predictions, with no retraining. Any Lane 3 allocation rule must label its source amount and must not relabel X as total crop-value loss or Z as an actual government payment.
