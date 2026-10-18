# Decisions log (append-only)

Entries are added at the bottom with a timestamp. Earlier entries are never edited, so this file shows what was decided before what.

---

## Entry 1: written 2026-10-17 22:20 EDT (system clock), before anything else was done in this step

**State at the time of writing.** `usda_budget_data/testing/` has never been read. `final_test.py` has never been run (no `test_*` file
exists in `app/model/results/`). Every number in this repo comes from training 2000-2012, walk-forward 2006-2012 or validation 2013-2015.
A separate code audit is running; the final test waits for it and for the user's explicit go-ahead.

**What was known when the plan below was decided** (so nobody can say it was decided after seeing test results; there are none):
- Calibrated pooled walk-forward + validation results (T1): D Tweedie has the best budget capture (49.8%), B boosting the lowest dollar
  error (WAPE 0.662), G TabPFN v2 is the only model inside the selection rule's noise band on both measures (capture 47.8% vs 49.8% best; WAPE
  0.679 vs 0.662 best). G passes the capture band by 0.0004 (threshold 0.47777, G 0.47816). The user judged this "a margin within noise".
- Before D and G existed the user had said: "If D or G doesn't win under the rule, keep B." G did win under the rule, by that margin.
- The user's decision (below) is that deployability, not that margin, decides between G and B.

### A. Version 1: official test (2016-2025)

Decided by the user, 2026-10-17:

1. Freeze three models with their current settings: **G (TabPFN v2), B (boosting), D (Tweedie)**. All three run in the one-shot test and all are reported.
2. Add baseline **B2 "USDA ERP trigger rule"**: a county qualifies if, by Aug 15, it had D2+ on any part of the county for 8 consecutive weekly maps,
   or reached D3+. Qualifying counties get a predicted cost in proportion to liability (scaled with the same calibration approach as B1);
   others get 0. Report it next to B0 and B1 on walk-forward and validation. **No model is changed because of it.**
3. **Deployability check for G, CPU only:** install size and time for torch + tabpfn, time to predict all IA + NE county-crops for one year, and
   whether it installs cleanly from `requirements.txt`.
4. **Headline rule:** "G is the headline model if CPU prediction for one year takes under 10 s and it installs from requirements.txt;
   otherwise B. The pre-registered selection rule picked G by a margin within noise, so deployability decides. B and D are secondary and fully
   reported." The result is filled in below (a later entry) and recorded in `results/chosen_model.json`.
5. **`final_test.py` is not run until the user gives the go-ahead.** The code audit must finish first.

Operational definitions added by Claude when writing this entry (interpretations; fixed here, before the measurements):
- *B2 window and counting.* Weekly Drought Monitor maps dated Apr 1 through Aug 14 of the same year, the same window the models' inputs use.
  "D2+ on any part of the county" = D2 + D3 + D4 area share > 0. "8 consecutive weekly maps" = 8 maps in a row, one week apart, within that window.
  "Reached D3+" = D3 + D4 area share > 0 on any map in the window. The trigger is a 0/1 flag per county-year, the same for both crops.
  Predicted share for a qualifying row = the training-period liability-weighted mean of the target among qualifying rows of the same state x crop
  (all qualifying rows if that cell is empty); 0 for non-qualifying rows; then multiplied by the model's calibration factor k from walk-forward
  2006-2012, exactly as for B1 (for T2 the same construction with the damaged-acre share). Only maps up to 2015 are read until the final test.
- *"CPU prediction for one year".* Wall-clock seconds for the T1 and T2 `predict()` calls together (the app needs both) on all IA + NE county-crops
  of one year (about 370 rows), CPU only (no MPS/CUDA), with the setting G was evaluated with (TabPFN v2 weights, n_estimators=8), model already
  fitted on 2000-2012 with weights already loaded; median of 3 runs. Weight loading and `fit()` time are reported separately. The 10 s limit is
  applied to this sum; the T1-only figure is shown too.
- *"Installs from requirements.txt".* In a fresh virtual environment, `pip install -r requirements.txt` with the line `tabpfn==9.2.0` enabled
  completes with no errors, `pip check` is clean, the repo's existing pins keep their versions, and `import tabpfn; TabPFNRegressor` works
  (weights download needs no Hugging Face login). If G becomes the headline model that line is enabled in `requirements.txt`.

### B. Version 2: planned now, run only after Version 1 is done and reported

Decided by the user, 2026-10-17 (the user states the feature list was planned at about 9 PM, before any test):

- Same model architectures and settings as frozen in v1; **no changes based on v1 results**.
- New features: D0+/D1+ on the last map; 4-week change in D1+ and in DSCI; weeks since D1+ > 25%; Jul 1-Aug 14 precip ratio; 30-day precip ratio;
  prior Sep-Mar precip ratio; heat Jul 10-Aug 5; same-year average coverage, revenue-plan share, liability per acre.
- Backtest 1: train through 2021, test 2022-2025. Backtest 2: train through 2022, test 2023-2025.
- In each backtest the winning model is picked **only** from walk-forward years inside that backtest's training range (for example predict
  2017-2021 year by year), then that chosen model is reported on its test years. All models' test results are also shown side by side, labelled
  "not used for selection".
- Calibration is nested: each year's k comes only from earlier years.
- All v2 results are labelled "v2: retrained with more years and new features (planned before the v1 test)".

Note for later: v2's backtests use 2016-2025 labels, which are the v1 test years. v2 therefore runs only after the v1 test is done and reported,
and its results are labelled as above. v2 is not run in the current step.

---

## Entry 2: written 2026-10-17 23:17 EDT (system clock): results of the Entry 1 checks. No test result exists.

**Still true:** `usda_budget_data/testing/` has not been read; `final_test.py` has not been run (it also refuses to run without `--i-am-sure`); no
model, feature or setting was changed because of B2 or the deployability check. The go-ahead and the code audit are still pending.

### A.2 B2 "USDA ERP trigger rule" (calibrated like B1, T1 payout share; walk-forward 2006-2012, validation 2013-2015, pooled)

| split | model | budget capture (top-20) | WAPE | AUC | calibration (Σpred/Σactual) | statewide total error |
|---|---|---|---|---|---|---|
| walk-forward | B0 | 28.9% | 1.59 | 0.553 | 1.00 | 15,331% |
| walk-forward | B1 | 30.5% | 0.95 | 0.688 | 1.00 | 7,495% |
| walk-forward | B2 | 23.6% | 0.78 | 0.589 | 1.00 | 87% |
| validation | B0 | 20.9% | 2.87 | 0.550 | 3.21 | 4,228% |
| validation | B1 | 25.0% | 2.65 | 0.612 | 2.61 | 901% |
| validation | B2 | 34.0% | 5.23 | 0.609 | 5.29 | 720% |
| pooled | B0 | 26.5% | 1.92 | 0.566 | 1.57 | 12,000% |
| pooled | B1 | 28.9% | 1.39 | 0.653 | 1.41 | 5,517% |
| pooled | B2 | 26.8% | 1.92 | 0.594 | 2.10 | 277% |

(Random counties: capture 21.5% walk-forward, 21.3% validation.) B2 triggers for 22% of training county-years and 25% of validation ones (86% in 2012, 62% in 2013, 0% in 2009-2011 and 2015).
Its calibration factor k is 3.39 for T1, the largest of any model: the rule fires on many county-years that
pay little. It beats B0/B1 on budget capture in validation (34% vs 21%/25%) but is worse than B0/B1 on dollar error there.

### A.3 G deployability, CPU only (`results/g_deployability.json`, `app/model/deploy_check.py`)

- Install, fresh venv, `pip install --no-cache-dir -r requirements.txt` with `tabpfn==9.2.0` enabled: **succeeded in 68 s**, `pip check` clean, the repo's pins
  unchanged (numpy 2.4.6, pandas 2.3.3, scikit-learn 1.9.1, ...). Whole venv 1.9 GB; the tabpfn-related packages add about 960 MB (torch 583 MB, mlx 234 MB,
  sympy 72 MB, networkx 18 MB, ...). Weights: one 42 MB file (TabPFN v2 regressor), downloaded without a Hugging Face login.
- Weight loading + `fit()`: 0.42 s (T1), 0.36 s (T2).
- **CPU prediction of one year** (367 IA + NE county-crops, n_estimators=8, 8 cores, macOS-26.6.2-arm64-arm-64bit-Mach-O): T1 median 163.33 s,
  T2 median 189.28 s, **sum 352.61 s (about 5.9 minutes)** against the 10 s limit. Limit exceeded by about 35x.
- Reproducibility: two CPU runs gave bit-identical predictions. Three runs on the Apple GPU (MPS) did not (max difference in predicted share
  0.0011, about 4% of the mean share). The model's evaluation used MPS.

### A.4 Headline rule applied

Rule (Entry 1): G is the headline if CPU prediction for one year takes under 10 s and it installs from requirements.txt; otherwise B.
Install: passes. CPU prediction: 352.61 s, fails. **Headline model for the v1 test: B (boosting).** Recorded in
`results/chosen_model.json` (`chosen` = `headline` = B; `frozen_models` = G, B, D; `selection_rule_pick` kept separately). `requirements.txt` keeps
`tabpfn` commented out because G is not the headline.

### Observed since Entry 1: the selection rule's pick is not stable

The pre-declared rule (near-best on top-20 capture within 0.02 and WAPE within 5%; simplest wins; fallback: lowest combined rank) was applied in three
evaluation runs with identical code and data: the pick was G, then D, then G. Cause: G's TabPFN predictions on MPS change in the 3rd decimal between runs,
and G sits on the capture threshold (this run: G 0.4779 vs threshold 0.4778; best capture 0.4978 (D); best WAPE 0.6620 (B), G 0.6782).
This supports the user's reading that G's win was "a margin within noise" and the choice to let deployability decide. It also means G's test numbers on MPS
cannot be reproduced exactly; the final test will run all three frozen models, with G on whatever device is used (recorded in the report).

### Open items before the v1 test

1. The user's go-ahead. 2. The separate code audit. 3. Decide the device for G in the test (CPU is bit-reproducible but slow: about 6 minutes for one year's T1 + T2 here, so roughly an hour
for the ten test years; MPS is faster but not bit-reproducible). 4. Entries 1-2 and the code are still uncommitted at the time of writing.

---

## Entry 3: written 2026-10-17 23:50 EDT (system clock), BEFORE any work on this revision

**Entry 3: plan revised after external review and code audit. One final test on 2016–2025 after these fixes. Headline chosen by the rule below on
walk-forward + validation only. Disclosure: some 2016–2025 years appeared in earlier exploratory analyses (2018/2022 payout totals, early 2022/2023
budget tests). The v2 split backtests are cancelled; the new features are added before the single test.**

State at writing: `final_test.py` has not been run (no `test_*` file in `results/`); nothing in this repo's evaluation has used 2016–2025 labels. Last commit a5c10b9.

### What this entry replaces
- Entry 1 A.1 (freeze G, B, D) and A.4 (deployability headline rule): replaced by item 12 below. G is not rerun; its earlier run is reported as an experiment only.
- Entry 1 B ("Version 2") and its split backtests: cancelled. The new features go in before the single v1 test.
- Entry 1's B2 window (maps through Aug 14): maps are now limited to those released by Aug 15, i.e. map_date <= Aug 13.

### Decided by the user (2026-10-17)
Data: (1) merge RMA county 19156 into 19155 summing at coverage-level rows before aggregation; (2) drought maps only if map_date <= Aug 13; (3) document the rain
normal window correctly (1999-2012) and add a per-year irrigated-share column so earlier years can be averaged; (4) new features d0_pct_last_map,
d1_pct_last_map, 4-week change in d1_pct and in dsci, 30-day precip ratio before the cutoff; rebuild, report row counts, confirm testing/ is gitignored.
Models/evaluation: (5) fold-safe preprocessing from years < Y for each walk-forward year Y; (6) nested calibration only, kept per model only if it lowers
statewide $ error; (7) baselines Z0 zero, B1 bin average, B2a USDA binary trigger, B2b tiered LFP-style trigger, B3 liability only, B4 liability x d2_pct_last_map,
headline comparison vs B2a/B2b; (8) models A, B, C, D on the new features; (9) metrics overall AND drought state-years: statewide absolute $ error, $ under-budgeted,
worst state-year shortfall, county WAPE, top-20 capture (counties, crops summed), best possible capture, calibration, for T1, T2 and Z, with one consistent AUC input,
consistent T2 scoring, deterministic tie-breaks; (10) "historical scenario range", coverage for drought vs quiet separately plus width and upper-bound misses;
(11) feature ablation of B, old vs new features; (12) selection rule: among A, B, C, D the lowest statewide absolute $ error on drought state-years, provided top-20 capture
beats B3 AND B4; ties within 5% go to the simpler model; (13) wording: X = estimated insurance payouts, Y = estimated deductible exposure, Z = illustrative relief
allocation under a 95% coverage assumption (inspired by USDA ERP 2022), Iowa 2013 = an emerging drought (D1 34% by Aug 13) that intensified after the forecast date,
derecho removed from expected misses; (14) copy the audit's AUDIT_REPORT.md into app/model/results/; (15) final_test.py uses the widened budget range and runs as
`python app/model/final_test.py --i-am-sure`; (16) trigger agreement analysis (significant payout = drought_payout_share >= 0.02; precision/recall for B2a and the headline model
flagging the same number of counties per state-year; 2x2 table per split with county-year counts and actual $; highlight the two disagreement cells).
Timebox: stop and report by 1:30 AM; ask before committing; wait for the user's go-ahead before the final test.

### Interpretations fixed by Claude before running (so they cannot be tuned afterwards)
- *Fold safety by construction.* The organizer computes each row's rain normal as the mean precip_mm of strictly earlier years (weather data from 1999; needs >= 3 earlier
  years, else missing) and its irrigated-share average as the mean of strictly earlier NASS years; the per-year columns (precip_mm, irr_share_year) are kept. Imputers, scalers,
  B1 bins, kNN pools and models are fitted in fit() on the fold's training rows only.
- *New features.* d0_pct_last_map = D0+ area share (100 - none_pct) and d1_pct_last_map = D1+ area share on the last map with map_date <= Aug 13; 4-week changes = last map minus
  the map 28 days earlier (missing if absent); precip_30d_ratio = precipitation Jul 16-Aug 14 divided by the mean of the same window in strictly earlier years (>= 3 years).
  "Old" features for the ablation = the pre-revision column list, rebuilt with the corrected cutoffs and normals.
- *Nested calibration.* For each scored year Y, k = sum(actual) / sum(predicted) over the out-of-sample predictions of earlier years only (walk-forward 2006-2012, then validation
  2013-2015 as they pass); k = 1 when there are none (2006). A model-target keeps calibration only if nested-calibrated statewide absolute $ error over 2006-2015 is lower than uncalibrated.
  In the final test k for year Y uses the 2006-2015 predictions plus the already-passed test years' predictions and realised labels.
- *Ranges.* A, B, D: the historical scenario range resamples whole earlier years' residuals (years < Y only, at least 3 such years, else no range); C: its neighbours' spread.
  The budget range is the best-covering method (closest to 80% pooled), widened to contain the headline model's point estimate.
- *B2a/B2b.* B2a = the existing trigger (D2+ on any part for 8 consecutive weekly maps, or D3+ on any part), maps Apr 1 - Aug 13, share = training liability-weighted mean among triggering
  rows per state x crop, else 0. B2b weight = the highest tier met: 1 = D2+ for 8 consecutive maps; 3 = any D3+; 4 = D3+ for 4+ consecutive maps or any D4; 5 = D4 for 4+ consecutive maps; 0 otherwise;
  predicted $ = weight x liability x c, with c fitted on training rows as sum(actual $) / sum(weight x liability) over rows with weight > 0. B3 = constant training liability-weighted mean
  share x liability. B4 = c x liability x d2_pct_last_map / 100 with c fitted on training rows. Z0 = 0. All then pass through the same nested-calibration decision.
- *Metrics.* Statewide absolute $ error = mean over state-years of |sum predicted - sum actual|; $ under-budgeted = sum over state-years of max(0, actual - predicted); worst shortfall = the
  largest single state-year max(0, actual - predicted); county WAPE = sum |error| / sum actual over county-years (crops summed); top-20 capture on counties with crops summed, ties broken by
  county FIPS ascending (never by actual values); AUC input = the model's own predicted amount for every model (T1 for payouts, T2 for acres, Z for relief). Z = illustrative relief $ built
  from T2 as in budget.py. A drought state-year = actual statewide drought payout >= 3% of insured $ (unchanged).
- *Selection rule (item 12) details.* Evaluated on pooled walk-forward + validation (2006-2015) with nested-calibrated predictions: candidate error = statewide absolute $ error averaged over
  the drought state-years in that pool; capture condition uses all pooled state-years (top-20 capture of the candidate must exceed both B3's and B4's); candidates within 5% of the lowest
  error are tied and the simplest wins, order D < A < C < B. If no candidate meets the capture condition, the highest-capture candidate is the headline and the report says the rule was not met.
- *Trigger agreement (item 16).* Counties flagged by B2a in a state-year = counties whose trigger is on; the model flags its top N counties of that state-year by predicted $ (crops summed, ties by FIPS),
  N = B2a's count (0 flags none). Precision/recall are over county-crop-years (a flagged county flags both crops; "significant" = share >= 0.02 for that county-crop-year). The 2x2 tables count
  county-years (crops summed) and sum their actual drought payouts; the favoured side of each disagreement cell is the one with the larger mean payout per county-year. The yield-loss add-on is optional.
- *Final test.* One run, 2016-2025, after the single headline is chosen by item 12; models A, B, C, D and all baselines are reported.

---

## Entry 4: written 2026-10-17 23:54 EDT (system clock), before the revised evaluation was run

Addendum to Entry 3. One extra audit fix is applied that Entry 3 did not list: Model A's back-transform factor changes from the Duan smearing mean of exp(residual) to the ratio
estimator sum(w*y) / sum(w*exp(fit)) over the positive rows (audit "Should fix" 6: the old factor over-scaled the conditional amount about 2x and was hidden by k). No other model
change. Audit items deliberately NOT changed (reported as limitations): hyper-parameters are tuned on the same walk-forward folds that are reported (7); history features act as year
proxies in 2000-2002 (10); the 0.02 / 5% noise bands stay as fixed in Entry 3. Still true: `final_test.py` has not been run and no 2016-2025 result exists.

---

## Entry 5: written 2026-10-18 00:05 EDT (system clock): results of the revised evaluation (walk-forward 2006-2012 + validation 2013-2015 only)

The data was rebuilt (training 4810 rows / 190 counties / 4734 with RMA labels; validation 1110 / 190 / 1101; testing 3700 / 190 / 3682, row count only), and `usda_budget_data/testing/` is
gitignored. Evaluation was run with the Entry 3-4 protocol. The headline model chosen by the pre-declared rule is recorded in `results/chosen_model.json` (see `results/validation_report.md`
section 1 for the rule table). The audit report is copied to `results/AUDIT_REPORT.md`. `final_test.py` has not been run; it waits for the user's go-ahead. Nothing is committed.

---

## Entry 6: written 2026-10-18 00:36 EDT (system clock), before the alpha edge check was run

Instruction (user): check D's chosen alpha; if it is at either edge of the grid, extend the grid one step in that direction (x10 or /10), rerun the walk-forward selection for D only, record the
result, and say whether the chosen alpha or the headline numbers changed; if it is not at an edge, confirm that. Facts at writing: the committed grid is alpha in {0.01, 0.1, 1.0} and the chosen
alpha is 0.01, i.e. the LOWER edge. Plan fixed now: extend the grid by one step to {0.001, 0.01, 0.1, 1.0} and re-tune D only (criterion unchanged: pooled county-year dollar WAPE of T1 over
walk-forward 2006-2012, uncalibrated); B's and C's grids and choices are untouched. If the chosen alpha changes, the evaluation is regenerated so params.json, calibration, the headline table
and the reports are consistent. Only one step is taken even if the new edge value wins. If the pre-declared headline rule would then pick a model other than D, the final test does not run:
the user is asked first. `final_test.py` has not been run and no 2016-2025 result exists.

---

## Entry 7: written 2026-10-18 00:38 EDT (system clock): alpha edge check done; headline frozen

**Alpha check.** D's chosen alpha was 0.01, the lower edge of the grid {0.01, 0.1, 1.0}. The grid was extended one step to {0.001, 0.01, 0.1, 1.0} and the walk-forward selection rerun
(pooled county-year dollar WAPE of T1, uncalibrated): 0.001 -> 0.5845, 0.01 -> 0.5865, 0.1 -> 0.6797, 1.0 -> 0.9929. **The chosen alpha changed to 0.001**; the curve is flat at the bottom (0.002 WAPE
between the two smallest values), and 0.001 is the new lower edge. As instructed, the grid is not extended further. Only D's rows changed (B, C, A and all baselines are identical).
D, pooled 2006-2015, all state-years: statewide abs. error $71.4M -> $57.1M, under-budgeted $1,061M -> $755M, worst shortfall $483M -> $417M, county WAPE 0.652 -> 0.657, top-20 capture 52.8% -> 52.9%,
Σpred/Σactual 0.85 -> 0.92. Drought state-years only: statewide abs. error $334M -> $231M, capture 44.2% -> 43.2%. Validation: statewide abs. error $95.8M -> $86.5M, capture 49.3% -> 47.0%.
The pre-declared headline rule still picks D (drought-year error $231M vs C $445M, A $457M, B $470M; all four beat B3 and B4 on capture), and nested calibration still does not help D (T1 raw $57.1M vs $127.9M calibrated;
T2 likewise), so D stays uncalibrated.

**Headline frozen: D (Tweedie GLM), uncalibrated. Secondary, reported in full: A, B, C. Baselines: Z0, B1, B2a, B2b, B3, B4. Range: C's historical scenario range widened around D's point.**
Frozen settings: `results/params.json` (B: max_iter 400, max_depth 3; C: k 25, drought weight 1.0; D: alpha 0.001), `results/calibration.csv` (nested calibration only for A, B4, and B3's T2), `results/chosen_model.json`,
`results/range_method.json` (C). `final_test.py` has not been run at the time of writing; it is run once after the commit that contains this entry, and nothing is changed after it runs.

---

## Entry 8: written 2026-10-18 01:06 EDT (system clock): second request to "run the final test once"; it was NOT run again

The user re-sent the pre-test instructions with extra deliverables. Facts: (1) the alpha edge check and the headline freeze were already done (Entries 6-7: alpha was at the lower edge, 0.01; extended one step; chosen alpha became 0.001; headline stayed D, uncalibrated);
(2) the official test already ran once, on 2026-10-18 around 00:41 EDT, after the commit that contains Entries 6-7, and its report was committed (originally 8ed713b; the same content is now in main). Running `final_test.py` again would be a second look at the held-out years
and would break the one-shot rule, so it was not run again. The extra deliverables (test_predictions.csv in the requested layout, test_state_years.csv, the per-state-year table with the closest value in bold, the scoreboard, the chart) are built by
`app/model/make_test_report.py` purely from the saved outputs of that one run (`test_predictions_raw_shares.csv`, `test_budget_range.csv`, `test_metrics.csv`); no model is refit and no setting changes. The script checks that its numbers equal the saved metrics.

---

## Entry 9: written 2026-10-18 04:26 EDT (system clock), before anything was run: exploratory planning band for statewide X

Planning band for statewide X = D's statewide estimate x [5th, 95th] percentile of actual/D, computed ONLY from out-of-sample state-years 2006-2015 in results/oos_predictions.csv.
Proposed after the official test; reported as exploratory; it never changes D. Plan fixed now: per state-year (IA, NE; 20 in all) actual = sum(drought_indemnity), D = sum(t1_D x liability), both clipped to >= $100,000,
r = log(actual / D), q05 / q95 = exp of the 5th / 95th percentile of r (numpy linear method). `ratio_band.py` (build time) reads only oos_predictions.csv, asserts years 2006..2015 and 20 state-years, and writes
results/ratio_band.json. `ratio_band_eval.py` (one-time check, afterwards) applies the saved band to the 2016-2025 state-years already in test_predictions.csv and writes results/ratio_band_eval.md, labelled exploratory,
after the official test; it does not write the json. The band applies to statewide X only (not Y, Z or single counties). Nothing in D, its artifacts, test_report.md or any training code changes.
Frozen-file hashes recorded before running (test_report.md, test_predictions.csv, test_budget_range.csv, chosen_model.json, params.json, oos_predictions.csv).
