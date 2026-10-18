# Drought cost model

Predicts, from what is known on Aug 15, what a drought costs each Iowa / Nebraska county (corn, soybeans) and turns it into a budget picture. This file documents the model code;
the repo's main README.md is untouched. Decisions are logged, in order, in [DECISIONS.md](DECISIONS.md); the external audit is in [results/AUDIT_REPORT.md](results/AUDIT_REPORT.md).

**Wording.** X = estimated insurance payouts (predicted payout share x insured liability). Y = estimated deductible exposure. Z = illustrative relief allocation under a 95% coverage
assumption (inspired by USDA ERP 2022); it is not a prediction of any program payment.

## Run it (repo root, venv active)

```bash
python organize_usda_data.py --downloads ~/Downloads --repo . --out ./usda_budget_data   # rebuild the data from the RMA files
python app/model/evaluate.py                  # tune, walk-forward 2006-2012 + validation 2013-2015 -> results/validation_report.md
python app/model/final_test.py --i-am-sure    # ONCE, only when told to: reads the held-out 2016-2025 data -> results/test_report.md
python app/model/ratio_band.py                # planning band for statewide X (exploratory, Entry 9) -> results/ratio_band.json
python app/model/ratio_band_eval.py           # one-time check of that band on 2016-2025 (reads the json) -> results/ratio_band_eval.md
python -m unittest tests.test_engine          # band tests

# Lane 2 deployment after the official test output exists:
python app/model/build_artifacts.py            # fit D and C once; save artifacts/ and verify statewide X
python app/model/iowa_corn_slice.py            # report Iowa corn only from saved test predictions
```
`final_test.py` refuses to run without `--i-am-sure`; `data.load_split("testing")` raises otherwise. Run it as a script (`python -m app.model...` does not work: `app/` is not a package
and the root `data/` folder would shadow `data.py`). Data folder: `$USDA_DATA_DIR`, else `<repo>/usda_budget_data`, else `<repo>/app/usda_budget_data`. `usda_budget_data/testing/` is gitignored.

The official test has already produced `results/test_predictions.csv` and `results/test_report.md` in this checkout. The ignored testing input folder is absent here. `build_artifacts.py` recreates its August 15 inputs from the checked-in source panels, joins the saved test output for exposure and observed labels, and fails if D's IA 2023 or NE 2022 statewide X differs from the saved official predictions by $1 or more. `results/test_state_years.csv` is generated from those saved predictions as a numeric reference. The app imports only `src.engine`, which loads artifacts once and never fits during a request. See [the contract](../../docs/lane2_contract.md).

## Models

| Name | What it is |
|---|---|
| Z0 | predict zero |
| B1 | drought-bin average (state x crop x `d2_weeks_50pct` bin, isotonic), fitted on the fold's training rows |
| B2a | USDA binary trigger: D2+ on any part of the county for 8 consecutive weekly maps, or any D3+ (maps Apr 1 - Aug 13); `erp.py` |
| B2b | tiered LFP-style trigger: weight 1 = D2 for 8 consecutive weeks, 3 = any D3, 4 = D3 for 4+ weeks or any D4, 5 = D4 for 4+ weeks; allocation = weight x liability |
| B3 | liability only (same share for every row) |
| B4 | liability x D2+ area share on the last map |
| A | two-part hurdle model (`hurdle.py`) |
| B | gradient boosting, Poisson loss, monotone constraints (`gbm.py`) |
| C | k nearest historical look-alikes (`analog.py`) |
| D | Tweedie GLM, power 1.5 (`tweedie.py`) |

G (TabPFN v2, `tabpfn_model.py`) is an experiment only (too slow on CPU, not bit-reproducible on the GPU); see `results/g_deployability.json` and the report's section 9.
Targets: T1 payout share (X), T2 damaged-acre share. Sample weight = liability.

## Protocol (fixed before running, see DECISIONS.md Entries 3-4)

- Out-of-sample years 2006-2015: walk-forward 2006-2012 (fit on years < Y) and validation 2013-2015 (fit on 2000-2012). Hyper-parameters are tuned on walk-forward only.
- Fold safety: imputers, scalers, bins, look-alike pools are fitted inside `fit()`; rain normals and irrigation averages in the data use strictly earlier years only; drought maps only if released by Aug 15 (map_date <= Aug 13).
- Nested calibration: the multiplier for year Y comes only from earlier years; kept for a model-target only if it lowers statewide absolute error (`results/calibration.csv`).
- Historical scenario range (rough 10th-90th percentile of past outcomes): A, B, D resample whole earlier years' residuals (years < Y, at least 3); C uses its look-alikes' spread. `budget.statewide_range()` returns the best-covering method widened to contain the headline model's point estimate.
- Headline rule: among A, B, C, D the lowest statewide absolute $ error on drought state-years, provided top-20 capture beats B3 and B4; ties within 5% go to the simpler model (D < A < C < B).
- Metrics, overall and for drought state-years only: statewide absolute $ error, $ under-budgeted, worst state-year shortfall, county WAPE, top-20 county capture (counties, crops summed; ties by FIPS), best possible capture, calibration, AUC (the model's own predicted amount), for T1, T2 and Z.

## Files

`data.py` (loading, feature lists), `erp.py` (trigger flags), `baselines.py`, `hurdle.py`, `gbm.py`, `analog.py`, `tweedie.py`, `evaluate.py`, `final_test.py`, `budget.py` (X, Y, Z arithmetic, calibration factors, ranges, extrapolation warning; import this from the app),
`results/` (reports and csv files), `DECISIONS.md`.

## Known limitations

- Only 3 of the 20 out-of-sample state-years are drought years (Iowa and Nebraska 2012, Iowa 2013); drought-year numbers are anecdotes.
- Iowa 2013 is an emerging drought (D1+ 34% on the Aug 13 map) that intensified after the forecast date; no model sees it.
- `yield_prev5_mean`, `acres_planted_prev3_mean` and the first two years' rain normals are missing in 2000-2002, so their missing flags can act as weak year proxies.
- Hyper-parameters are tuned on the same walk-forward folds that are reported (slightly optimistic).
- Ranges are rough: A, B, D ranges exist only from 2009 and cover poorly; C's range is wide.

## Planning band for statewide X (exploratory, after the official test)

`reserve_band_x_usd` = D's statewide X x [q05, q95], the 5th and 95th percentile of actual / D over the out-of-sample state-years 2006-2015 (`results/ratio_band.json`, built by `ratio_band.py` from `results/oos_predictions.csv` only).
It applies to statewide X only (not Y, Z or single counties), is reported as exploratory, and never changes D. `ratio_band_eval.py` checks it once on 2016-2025. For real future use, re-run `ratio_band.py` each year after the
final RMA claims are in, using only out-of-sample years before the forecast year (and log the change in DECISIONS.md first). `src/engine.py` has `load_ratio_band()` and `reserve_band_x_usd(plan_usd)`; call the latter after acres_scale x price_scale.
