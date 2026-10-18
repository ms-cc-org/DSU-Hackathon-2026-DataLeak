# Drought cost model (implements MODEL_PLAN.md)

Predicts, from what is known on Aug 15, what a drought costs each Iowa / Nebraska county (corn, soybeans)
and turns it into a relief budget. Only pandas, numpy, scikit-learn (see `requirements.txt`).
This file documents the model code; the repo's main README.md is untouched.

## Run it (from the repo root, venv active)

```bash
python app/model/evaluate.py                  # tune, walk-forward + validation -> results/validation_report.md (+ validation_results.csv)
python app/model/final_test.py --i-am-sure    # ONCE, at the very end: reads testing/ -> results/test_report.md
```
`final_test.py` refuses to run without `--i-am-sure`, and `data.load_split("testing")` raises unless that flag path
is used. `evaluate.py` never touches `testing/`. Data folder: `$USDA_DATA_DIR`, else `<repo>/usda_budget_data`,
else `<repo>/app/usda_budget_data`.

## Files

| File | Role |
|---|---|
| `data.py` | load + join (`fips` always text) + filter + feature list, `Preprocessor` (median impute, missing flags, standardise) |
| `baselines.py` | B0 (state x crop mean), B1 (state x crop x `d2_weeks_50pct` bin, isotonic) |
| `hurdle.py` | Strategy A: logistic P(cost > 0) x log-linear amount, smearing, coefficients |
| `gbm.py` | Strategy B: `HistGradientBoostingRegressor(loss="poisson")` with monotonic constraints |
| `analog.py` | Strategy C: k nearest training county-years (same crop), neighbour range + explanation |
| `evaluate.py` | tuning, walk-forward 2006-2012, validation 2013-2015, metrics, model choice, report |
| `final_test.py` | plan section 5 |
| `budget.py` | plan sections 6-7: X, Y, Z, ranges, extrapolation warning (import this from Streamlit) |
| `results/` | generated reports and csv files |

Each model has `fit(train, target)`, `predict(df)` (expected share) and `score(df)` (ranking score).
Targets: T1 `drought_payout_share`, T2 `drought_loss_acre_share`. Sample weight = `liability`.

## Choices made where the plan left room

- Rows: `insured == True`, `liability > 0`, `rma_year_available`; zero payouts kept. Five training rows have tiny negative
  payout shares (reversals, about 0.0005% of dollars): clipped to 0 for fitting, actuals untouched in evaluation.
- A: balanced class weights as specified, then the intercept is shifted back to the real base rate so P is a real
  probability. Part 2 uses a ridge penalty of 1 on standardised features (about OLS here) because the drought columns are collinear.
- Tuning criterion (fixed in advance): pooled walk-forward county-year dollar WAPE of T1. Grid: B `max_iter` {100,200,400} x
  `max_depth` {3,4}; C `k` {10,25,50} x drought-feature weight {1,2,3}.
- "Drought year" in reports = state-year whose actual statewide drought payout is >= 3% of insured dollars (grouping only).
- Model choice rule (fixed in advance): among A/B/C, near-best = top-20 capture within 0.02 and WAPE within 5% of the best;
  take the simplest near-best (A over C over B). `results/chosen_model.json` records the outcome.
- Ranges (rough 10th-90th percentile): A and B resample WHOLE past years' residuals (walk-forward 2006-2012; every county of a year
  moves together, never row by row); C uses its look-alikes' liability-weighted 10th-90th percentile with all counties at the same
  quantile. The method closest to 80% coverage on walk-forward + validation is written to `results/range_method.json` and used by
  `budget.statewide_range()`, always labelled rough. Nothing is tuned to reach 80%.
- Known miss, not tuned for: Iowa 2013 (drought began after Aug 15). Expected miss in the final test: Iowa 2020 derecho (wind).

## Leakage checklist (plan section 8)

- [x] No labels column is a feature: `data.FEATURES` is an explicit list; `assert_no_leak` rejects `FORBIDDEN` names.
- [x] Inputs are already clipped to before Aug 15 by `organize_usda_data.py`; nothing else is added.
- [x] Scalers, imputers, bins, neighbour pools are fitted inside `fit()` on the training rows of that fold only.
- [x] `fips`, `year`, county name are never features.
- [x] `testing/` untouched until `final_test.py --i-am-sure`.
- Budget arithmetic (`budget.py`) uses `liability`, `insured_acres`, `avg_coverage`, `full_crop_value` from labels.csv; these are
  Aug-15 exposure numbers used after prediction, never as model inputs.

## What the validation run showed (full tables in `results/validation_report.md`)

Pooled out-of-sample, walk-forward 2006-2012 + validation 2013-2015 (20 state-years), T1 payout share:

| | top-20 capture | dollar WAPE | 80% range coverage |
|---|---|---|---|
| B0 average | 26.5% | 1.35 | - |
| B1 drought-map rule | 28.9% | 1.08 | - |
| A hurdle | 44.4% | 0.88 | 50% |
| B boosting (chosen) | 43.8% | 0.64 | 35% |
| C look-alikes | 40.2% | 0.76 | 80% |
| random counties | 21.5% | | |

B clearly beats B1 (about +15 capture points, 41% lower dollar error). A matches B on capture but has higher dollar error, so there
is no simpler model within noise and B is chosen. Caveats:

- Only three of the 20 state-years are drought years (Iowa and Nebraska 2012, Iowa 2013). In those B under-budgets (0.68 of actual).
- Iowa 2013 is missed by every model: the drought began after Aug 15 (statewide D2+ area 0% from May 28 through Aug 13, 21% on
  Aug 27, 42% on Sep 10). Not tuned for.
- Ranges are rough. Whole-year resampling of 7 walk-forward years gives A and B lopsided, narrow ranges (50% and 35% coverage); the
  look-alike spread (C) reaches 80% pooled (86% walk-forward, 67% validation, only 6 state-years), so `budget.py` uses it.
- `yield_prev5_mean` / `acres_planted_prev3_mean` are missing only for 2000-2002, so A's missing-flag columns (and B's native
  NaN splits) can act as a weak year proxy during training. This follows the plan as written; changing it would be a post-hoc decision.
- Quiet years are over-budgeted by every model (B about 1.6x in walk-forward).
