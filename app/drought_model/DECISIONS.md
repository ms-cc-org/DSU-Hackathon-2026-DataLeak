# Drought-severity model: decisions log (append-only)

## Entry 1: written 2026-10-18 03:10 EDT (system clock), BEFORE any code was run or any result seen

Scope: a drought-severity model (Task A: outlook after Aug 13; Task B: in-season severity from weather + soil + two map-state inputs), separate from the insurance-cost model in app/model/ (untouched).
Nothing is committed or pushed. Rows from 2016-2025 (maps, weather, labels) are not loaded anywhere: every loader filters year <= 2015 at read time (parquet filters) unless `final_test.py --i-am-sure` is used.
drought_severity_data/testing/ and usda_budget_data/testing/ are never opened; the builder does not write a testing/ folder unless run with `--include-test --i-am-sure`.

### Data (organize_drought_severity.py, rebuilt to compute everything from the raw repo files)
- Level rule: highest D-category covering > 1% of the county (D0..D4 are non-cumulative percentages); 0 none, 1 D0 ... 5 D4. Only IA and NE; one row per county-year (all 192 IA + NE counties; fips is 5-character text).
- Maps: only maps dated <= Aug 13 for inputs. Weather: only days <= Aug 13 of the decision year (prior-year days are allowed for the winter window).
- Task A: y_A = worst level on maps Aug 14 - Sep 30; worse_A = y_A > level_last_map (last map dated <= Aug 13). Task B: y_B = worst level on maps Apr 1 - Aug 13; level_apr1 = worst level on maps Mar 25 - Apr 7;
  worse_B = y_B > level_apr1; change_B = y_B - level_apr1. Task B inputs may use level_apr1 and prev_fall_level (worst level on maps Aug 14 - Dec 31 of the previous year) but no map dated after Apr 7 of the year (asserted).
- Task A map-state inputs: level_last_map, dsci_last, d0plus_pct_last, d1plus_pct_last, dsci_change_4wk (last map minus the map 28 days earlier), level_apr1, prev_fall_level, nbr_level_last (mean level_last_map of the other counties whose centroid is within 70 km; haversine on area-weighted polygon centroids).
- Weather (windows end Aug 13): precip_30d / 60d / 90d (the 30, 60, 90 days ending Aug 13), precip_apr1_to_cutoff, winter_precip (Oct 1 of the previous year to Mar 31), tmax_mean_30d, heat32_days_apr1_to_cutoff (days with tmax >= 32 C), dry_days_30d (days < 1 mm),
  water balance wb_30d, wb_90d, wb_apr1 = precipitation - ET0 over the window; ET0 = Hargreaves with FAO-56 Ra from the county centroid latitude and day of year: 0.0023 * 0.408 * Ra * (Tmean + 17.8) * sqrt(max(Tmax - Tmin, 0)).
- *_ratio versions (precip_30d, 60d, 90d, apr1_to_cutoff, winter) divide by the county's mean of the same window over STRICTLY EARLIER years (weather starts in 1999; at least 3 earlier years, else blank). This is fold-safe for every walk-forward fold, because a fold that trains on years < Y only ever has earlier years for the year it predicts.
- Static: aws_100cm_mm, droughty_pct, irr_share (mean of the county's irrigated_share over the strictly earlier years, averaged over crops; blank for 2000), is_nebraska.
- Not used: MODIS NDVI, the master dataset's season weather/drought columns, any same-year yield or harvest. The master's max_drought_severity is used only for a cross-check of the level definition, read with a year <= 2015 filter.

### Models (app/drought_model/), fixed now
- Baselines: persistence (level: A = level_last_map, B = level_apr1; worse: predict "no worsening", AUC 0.5 by construction, Brier = base rate); climatology (per-county share of training years at each level of y; P(worse) = share of the county's training years with level > start level; level prediction = the county's most common training level, ties to the lower level);
  always-most-common-level (the global mode of y in the training years; P(worse) = training base rate).
- M1 LogisticRegression (median impute + missing flags, standardise, class_weight balanced, C=1, then the intercept shifted back to the training base rate so that probabilities are calibrated). M2 HistGradientBoostingClassifier (max_depth 3, learning_rate 0.05, min_samples_leaf 30, max_iter 200, early stopping off, random_state 0)
  with monotonic constraints: +1 for heat32_days_apr1_to_cutoff, tmax_mean_30d, dry_days_30d, level_last_map, level_apr1, prev_fall_level, nbr_level_last, dsci_last, dsci_change_4wk, d0plus_pct_last, d1plus_pct_last; -1 for precip_* (including ratios and winter), wb_*, aws_100cm_mm, irr_share; 0 for everything else.
  M3 kNN look-alikes (k=25, standardised, imputed). No tuning of any model.
- Level prediction for any model = start level + step_hat if P(worse) >= 0.5 else start level, with step_hat = the training median of the positive steps (y - start level among worse rows, at least 1), capped at level 5.
- Evaluation: walk-forward for Y = 2006..2015, train on 2000..Y-1; 2006-2012 is "walk-forward" and 2013-2015 is "validation" (reported separately, never used for selection). Metrics: AUC and Brier for worse_A / worse_B; exact-level and within-one-level accuracy against persistence; calibration by decile; predicted vs actual worsening rate per state-year
  (IA 2012, NE 2012, IA 2013 highlighted); permutation importance of the selected model (trained 2000-2012, scored on 2013-2015, 10 repeats, AUC).
- Selection, per task: the model with the best walk-forward (2006-2012) AUC for worse; models within 0.02 AUC of the best are tied and the simplest wins (order M1 < M3 < M2). If a task's best model cannot beat the baselines (persistence for levels, climatology for worse), the report says so plainly.
- Simulation helper (Task B only): scales daily precipitation and shifts tmax/tmin for the simulated state-year before building features, then scores with a Task B model trained on years before that year (default) so a historical example is out of sample.
- final_test.py: retrains the frozen models on 2000-2015 and scores 2016-2025 once; refuses to run without --i-am-sure; it is NOT run in this work.
- Quick exploratory reference from the user (worse_B AUC about 0.87, worse_A about 0.60 with HGB): reproduce, do not tune toward it.

---

## Entry 2: written 2026-10-18 03:17 EDT, after the first complete walk-forward run (years <= 2015 only)

Run exactly as fixed in Entry 1; no setting was changed after seeing results. Chosen by the pre-declared rule: M1 logistic for Task A (walk-forward AUC 0.650 vs M2 0.611, M3 0.517) and M1 logistic for Task B (0.860 vs M3 0.792, M2 0.764).
Findings recorded here so they cannot be argued away later: (1) Task A beats climatology on AUC but does NOT beat persistence on exact level (58.9% vs 62.8% walk-forward); (2) M2 as specified (including +1 monotone constraints on the start/level inputs) gets Task B walk-forward AUC 0.764 and 0.481 on 2013-2015, not the exploratory ~0.87;
a diagnostic (not used for selection) shows the +1 sign on the start level contradicts the data (standardised M1 coefficient -3.6 for level_last_map in Task A and -2.1 for level_apr1 in Task B) and that M2 without that sign reaches 0.853 walk-forward in Task B; the constraint is left as specified and the question is passed to the model builder to decide before the final test;
(2b) the pooled AUC of a predictor that is constant within each fold (persistence, most-common-level) is reported as 0.5, because pooling constants across folds would measure fold-to-fold drift, not ranking; (3) the validation window (2013-2015) has a 12% worsening rate in Task B versus 45% in walk-forward, so its AUCs rest on few positives.
`final_test.py` has not been run; 2016-2025 was never loaded; drought_severity_data/testing/ does not exist. Nothing is committed.

---

## Entry 3: written 2026-10-18 03:24 EDT (system clock), BEFORE anything below was run; no 2016-2025 result exists

Decided by the model builder, after reading Entry 2:
1. **The +1 monotone constraint on the start level (level_last_map / level_apr1) in M2 was a specification error.** The data and the M1 coefficients show that a high start level is LESS likely to worsen (ceiling and persistence): standardised M1 coefficients -3.64 (Task A) and -2.08 (Task B).
   M2 was not chosen, so nothing changes; the unconstrained and sign-fixed M2 results in validation_report.md stay diagnostic only and are not adopted.
2. **M1 uses balanced class weights (with the intercept shifted back to the training base rate), and its Task A probabilities are not calibrated** (top decile: 0.92 predicted vs 0.35 actual). Decision: no model change.
   Task A is reported as a RANKING only (AUC; plus the level accuracies, which show no probabilities) and its probabilities are not displayed anywhere (no Brier score, calibration deciles or predicted worsening rates for Task A in the test report).
   Task B P(worse) is reported with its calibration table.
3. **Frozen: M1 for Task A and for Task B, with the features and settings exactly as they are in the code now** (results/chosen_models.json; models.py; organize_drought_severity.py).
4. **Test report content (fixed before the run):** for Task B: AUC, Brier, exact-level and within-one accuracy for persistence, climatology, most-common-level and the frozen M1, test next to validation (2013-2015); calibration deciles; predicted vs actual worsening rate per state-year, with IA 2023, NE 2022 and NE 2023 highlighted.
   For Task A: AUC and the two level accuracies in the same layout, actual worsening rate per state-year and the within-state-year AUC (ranking only); no probabilities. Resolution of the instruction conflict: "Brier" and "predicted vs actual rate" are shown for Task B only because Entry 3 item 2 forbids displaying Task A probabilities.
5. **Process:** the 2000-2015 Task B fit artifact (artifacts/task_b_full.joblib) and simulate.py's default are code changes that use years <= 2015 only; they are made BEFORE the one-shot test so that nothing in the repo changes after the test runs. `final_test.py --i-am-sure` is then run exactly once; nothing is changed afterwards.
   Nothing is committed or pushed.

---

## Entry 4: written 2026-10-18 03:34 EDT (system clock), BEFORE the exploratory evaluation below was run. EXPLORATORY, after the official test

**Purpose.** Report the accuracy of the frozen M1 spec (Task B in-season, Task A outlook) over 2015-2025, including 2015 (which the official test, 2016-2025, did not cover). This is exploratory, after the official test: 2016-2025 were already scored once, so none of this is an independent test and it does not replace `results/test_report.md`.
**Schemes (both with the M1 settings exactly as frozen in Entry 3; nothing is retuned).** (a) Fixed: train on 2000-2014, predict 2015-2025. (b) Walk-forward: for each Y in 2015..2025, train on 2000..Y-1 and predict Y. Imputers, scalers and base rates are refit per fold on the fold's training years inside `fit()`;
rain normals and irrigation averages are built by the data code from strictly earlier years only, so they are fold-safe by construction. Inputs use maps <= Aug 13 and weather days <= Aug 13 as in the data build.
**Guarded path.** The 2015-2025 inputs and labels are built in memory through the existing guarded call (`organize_drought_severity.build_tables(include_test=True, i_am_sure=True)`, i.e. the --include-test --i-am-sure path); the script also requires --i-am-sure. Nothing is written to drought_severity_data/.
**Reporting.** Task B: AUC, Brier, exact level, within one level, calibration deciles. Task A: ranking only (AUC, exact level, within one level; no probabilities, no Brier, no calibration, per Entry 3); its CSV column is a within-year rank percentile, not a probability.
Per-year rows 2015-2025, Task B per state-year predicted vs actual worsening rates with the correlation across state-years, 2015 called out separately, and a "for the map" summary (how often the Task B predicted level is exact / within one / off by 2+, and the share of counties with an input outside the fold's training range, per year). Every table is labelled "exploratory, after the official test".
**Rule.** No model choice, feature, setting, artifact or official result may change because of this. Files touched: only results/exploratory_2015_2025.md, results/exploratory_2015_2025_predictions.csv and this log (plus the script exploratory_2015_2025.py). The SHA-1 of results/test_report.md, artifacts/task_b_full.joblib and results/chosen_models.json is recorded before the run and re-checked after it. Nothing is committed or pushed.

---
