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
