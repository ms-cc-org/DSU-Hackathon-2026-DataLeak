> **Note added when copying (not part of the audit):** this is the audit's report as written on 2026-10-17 against the code at commit a5c10b9 (before the revision in DECISIONS.md Entries 3-4). The `audit/` scripts, logs and tables it cites are not included here. Its findings drove the revision; see DECISIONS.md for which were fixed and which were not.

# Audit of the drought cost model (branch `drought-model-clean`)

Auditor: Claude (Sonnet 5.5), 2026-10-17. Nothing was committed or pushed, no existing file was modified; every script, log and output of this audit is in `audit/`
(scripts `audit/check_*.py`, logs `audit/out_*.txt`, tables `audit/out_committed/`, `audit/out_wip/`).
`usda_budget_data/testing/` was never read and `final_test.py` was never run (it was only read as source code).

## 0. What was audited (read this first)

| Item | Detail |
|---|---|
| Worktree | `../DataLeak-audit`, **detached** at `0482638` (`git worktree add ../DataLeak-audit drought-model-clean` was refused because the branch is checked out in the main copy; I added `--detach`). It has no `testing/` folder, so the held-out data physically cannot be read from it. |
| **Committed code** (variant `committed`) | `app/model/` at `0482638`: models **B0, B1, A, B, C** only. There is **no Tweedie, no TabPFN, no D, no G, no B2** in the committed branch. |
| **WIP snapshot** (variant `wip`) | The main copy has **uncommitted** work that your brief describes: `tweedie.py` (D), `tabpfn_model.py` (G), `erp.py` + `B2`, a rewritten `final_test.py`, `DECISIONS.md`, and re-generated results. You chose "Both", so I copied main's `app/model/` as it was at 22:25 on 2026-10-17 into `audit/wip_snapshot/` (SHA-1 of every file in `audit/wip_snapshot/SHA1.txt`) and ran the model-dependent checks on both. If the other session has edited files since, the snapshot does not include those edits. |
| Names in this report | **D = Tweedie GLM (power 1.5)**, **G = TabPFN v2**, **B2 = USDA ERP trigger rule** exist only in the snapshot. In the *committed* `evaluate.py` "D" is only a report section ("both targets") and "G" is a report-only dollar-target side check (`GBMDollars`), not TabPFN. |
| `MODEL_PLAN.md` | Not in the repo; read from `~/Downloads/MODEL_PLAN.md`. `app/model/README.md` differs between the committed branch and main (main has uncommitted edits). |
| Python | main's `.venv` (Python 3.13, pandas 2.3.3, numpy 2.4.6, scikit-learn 1.9.1, torch 2.14.1, tabpfn 9.2.0). G runs on **MPS (Apple GPU)**, not CPU. |
| Not possible as asked | Check 6 for **2018 and 2022**: their label files are in `usda_budget_data/testing/`, which I must not read. I recomputed the raw 2018/2022 totals but could not compare them with the labels; I ran the same label check for **every year 2000-2015** instead. |

## Verdicts at a glance

| # | Check | Verdict |
|---|---|---|
| 1 | Shuffle test | **PASS** (with a corrected expectation: the null level for capture is **28.7 %**, not 21 %; see below) |
| 2 | Cheat test | **PASS** for B; **PASS with explanation** for D (log-link GLM cannot use a raw copy of the target) |
| 3 | Fold leakage | **PASS** for every fitted object; **CONCERN** for three things that are not fold-nested (k, hyper-parameter choice, range pools) |
| 4 | Feature leakage | **PASS** on the Aug-15 window and on all label columns; **CONCERN** on normals/irrigation (not fold-causal, immaterial), a 1999 start year, and Drought Monitor release dates |
| 5 | Joins and rows | **PASS** (one county missing from the universe, see 6) |
| 6 | Labels vs raw colsom | **CONCERN**: 2018/2022 not comparable (testing/ is off limits); for 2000-2015 every difference is one Iowa county (W Pottawattamie, FIPS 19156), 0.8 % of 2012 and up to 1.7 % of other years |
| 7 | Hand check | **PASS** (all numbers reproduce to 1e-16) |
| 8 | Model A back-transform | **CONCERN**: formula is implemented as documented, but the smearing factor over-scales the conditional amount about 2x; k absorbs it |
| 9 | Monotonic constraints | **PASS**; constraints help slightly (AUC +0.04, WAPE -0.06 on walk-forward), capture unchanged |
| 10 | Metric definitions | **PASS**; one definitional **CONCERN** (AUC compares different scores across models) |
| 11 | Sample weights | **PASS** for A, B, C, D; G ignores them (documented); T2 weighting inconsistency |
| 12 | Calibration k | **FAIL** (not nested): pooled calibrated WAPE is flattered by 0.02-0.10 (A +0.07, B +0.05, D +0.10, G +0.06); capture/AUC unchanged, WAPE order B < A < G unchanged (D falls below C) |
| 13 | Range method | **PASS** for C's neighbours; **CONCERN** for how widening and range selection are applied |
| 14 | Reproducibility | **PASS** (committed: 15/15 files byte-identical; snapshot: all models exact except G, GPU jitter <= 0.003 WAPE; shipped snapshot results are stale, B2 missing) |

## Check-by-check evidence

### 1. Shuffle test: PASS (corrected expectation)

Method (`audit/check_shuffle.py`, `check_shuffle_10.py`, `check_shuffle_g.py`): in every walk-forward fold Y (2006-2012) the models are fit on years < Y with the training labels
(T1 and T2 together) **permuted**, and scored with the pipeline's own `evaluate.metrics` on the **true** labels of year Y. Uncalibrated, pooled over the 7 folds.

**Expectation that needs correcting.** Capture ranks counties by *predicted dollars = predicted share x liability*, so even a model with no signal ranks big-liability counties first.
Random county picking gives **21.5 %**, but ranking by liability alone (a constant payout share) gives **28.7 %**; B0 with real labels is 28.9 %. The no-signal level for capture is therefore about 29 %, not 21 %.
AUC is on shares, so its null is 0.5, except that models with a state/crop term can reach about 0.55-0.60 because Iowa and Nebraska have different zero-payout rates (B0 = 0.567 under the null).

| Labels | B0 | B1 | A | B | C | B2 | D | G |
|---|---|---|---|---|---|---|---|---|
| Real, capture | 0.289 | 0.305 | 0.471 | 0.497 | 0.434 | 0.236 | 0.517 | 0.507 |
| Real, AUC | 0.553 | 0.688 | 0.808 | 0.815 | 0.737 | 0.589 | 0.775 | 0.758 |
| **Strict null** (labels permuted across all rows of the fold), capture, mean of 10 seeds | 0.288 | 0.292 | 0.273 | 0.296 | 0.278 | 0.237 | 0.285 | 0.295 (1 seed) |
| Strict null, AUC | 0.567 | 0.593 | 0.490 | 0.612 | 0.529 | 0.589 | 0.541 | 0.558 (1 seed) |
| Within-year shuffle, capture (3 seeds) | 0.286 | 0.309 | 0.366 | 0.354 | 0.353 | 0.237 | 0.370 | 0.304 (1 seed) |
| Within-year shuffle, AUC | 0.570 | 0.704 | 0.771 | 0.810 | 0.748 | 0.589 | 0.827 | 0.832 (1 seed) |

Reference rows: random 0.215, liability-only ranking 0.287, oracle 0.768. Seeds' standard deviations are 0.001-0.03 (`audit/out_committed/shuffle_summary.csv`, `audit/out_wip/*`).

* Strict null: every model falls to the liability-ranking level (0.24-0.30) and AUC 0.49-0.61. B's AUC of 0.612 (sd 0.045) is the highest, about 0.045 above the B0 composition floor; it is not a leak (a feature-free shuffle cannot create signal) but it shows B fits noise somewhat.
* **Within-year shuffle does not reach the null**: B1 keeps AUC 0.70, B/D keep 0.35-0.37 capture and 0.81-0.83 AUC. That is *not* leakage: shuffling inside a year keeps each year's overall payout level, and drought years (2002-3, 2012) have both high drought features and high payouts, so a model legitimately learns "drought years pay more" from year-level covariation. Only the strict null removes it. If you meant the within-year version, expect those numbers.
* Same checks on the committed branch (B0, B1, A, B, C) give identical numbers because the model code is identical (`analog.py`, `hurdle.py`, `gbm.py`, `budget.py` are byte-identical between the branch and the snapshot; `baselines.py` and `data.py` only add B2).

### 2. Cheat test: PASS (B), PASS with explanation (D)

`audit/check_cheat.py`: the row's true target (T1 / T2 respectively) is appended as a feature, walk-forward 2006-2012, uncalibrated.

| Model | capture | AUC | WAPE | row corr(pred, actual) |
|---|---|---|---|---|
| Oracle (perfect ranking) | **0.768** | | | |
| **B + true T1** | **0.767** | 0.999 | 0.149 | 0.950 |
| D + true T1 (raw value, standardised) | 0.511 | 0.807 | 0.546 | 0.916 |
| D + log(T1 + 1e-4) | 0.751 | 0.965 | 0.191 | 0.972 |
| B0 (no cheat) | 0.289 | 0.553 | 1.242 | |

The pipeline can learn: B reaches the oracle. D with the raw copy falls short for a model-form reason, not a pipeline bug: a log-link GLM predicts `exp(a + b*z)`, convex in the feature, so large true shares are pushed to the clip at 1.0 (ties) and tiny positive shares cannot be told from zeros. Feed it the log of the target (which the log link can represent as `mu proportional to T1`) and it reaches 0.751. Not run for G (your brief asked B and D).

### 3. Fold leakage: PASS (every fitted object); CONCERN (three things are not nested)

Enforcement in code (committed line numbers, identical in the snapshot unless noted):

```python
# evaluate.py:195-201  walk-forward: fit on years < Y, predict year Y
for y in years:
    p = fit_predict(train[train.year < y], train[train.year == y], params)
# evaluate.py:210-212  tuning uses the same rule
te = train[train.year == y].reset_index(drop=True)
te["t1_x"] = make_model(name, {name: combo}).fit(train[train.year < y], T1).predict(te)
# evaluate.py:704,713-715  validation: `train`=load_usable("training") only; models fit on it, predict `val`
```
and inside each model, everything is fitted in `fit()` on the frame it is given: `Preprocessor.fit` (`data.py:97-104`, median/mean/std/missing flags; used by A, C, D), B0/B1 tables and isotonic bins (`baselines.py:21-54`), C's NearestNeighbors pool (`analog.py:32-42`), A's scaler/logit/ridge/smearing (`hurdle.py:33-55`), B's trees (`gbm.py:24-28`), D (`tweedie.py:20-26`), G's context rows (`tabpfn_model.py:34-38`), B2's training means (`baselines.py` snapshot, `B2.fit`).

Evidence, run on the real code (`audit/check_folds.py`, `check_folds_g.py`): every model class's `fit`/`predict` was wrapped; `predict` asserts `max(train year) < min(predicted year)`.
**Committed: 281 `predict()` calls, snapshot: 254 calls, over the whole `tune()` grid, the 7 walk-forward folds and the validation fit; all passed, the assertion never fired.** For G (TabPFN) the context rows handed to `fit` were 2,180 / 2,544 / 2,908 / 3,272 / 3,636 / 4,001 / 4,367 rows (years 2000..Y-1) for folds 2006..2012 and 4,734 for validation. I also recomputed the fitted statistics independently for each fold: scaler median/mean/std, B0 table, kNN pool years; all equal what the models stored (and differ from the full-2000-2012 statistics, so the test has power). Calibration k, the Tweedie `alpha`, and the B/C hyper-parameters are not fold objects; see below.

Not nested (CONCERN, none is a label leak):
* **Calibration k**: one constant per model fitted on all of 2006-2012, see check 12 (FAIL).
* **Hyper-parameters** (B `max_iter, max_depth`; C `k, drought_weight`; D `alpha`) are chosen by minimum WAPE over the same 7 walk-forward folds that are then reported as "walk-forward". `tuning.csv`: B best 0.554 vs grid median 0.578 (worst 0.665); C best 0.661 vs 0.694; **D best 0.635 (alpha=0.01) vs median 0.763 (worst 1.049)**. So tuned walk-forward WAPE is optimistic by roughly 0.02-0.03 for B and C and up to 0.13 for D against an average grid choice; the validation years are untouched by tuning and are the honest figure. D's best `alpha` is the **smallest value on the grid**, so the grid may be truncated.
* **80 % range pools for A, B, D, G** are leave-one-year-out over the walk-forward years (`budget.py:50-65`, `exclude_year`), so for walk-forward year Y they use residuals of years > Y too. For validation and test years they use all of 2006-2012 (causal), so only the walk-forward coverage numbers are slightly non-causal.

### 4. Feature leakage: PASS on the window and labels; CONCERNs below

* **No label column is a feature.** `data.FEATURES` is an explicit list; `FEATURES ∩ columns(all_labels.csv) = ∅` (`audit/out_history_wip.txt`); `assert_no_leak` also rejects `fips, year, county_name, precip_mm`, T1, T2. The only input columns not used are `county_name, crop, decision_date, fips, precip_mm, state_alpha, year`.
* **Aug-15 window.** I rebuilt all drought and weather features from the raw repo parquet files with independent code (`audit/check_features.py`) for **all 5,920 training+validation rows**: `d2_weeks_50pct, d3_weeks_50pct` max diff 0; `d2_max_pct, dsci_mean, d2_pct_last_map, d3_pct_last_map` <= 6e-14; `precip_mm` 1e-13, `precip_ratio_vs_normal` 2e-16, `heat32_days, heat35_days` 0, `tmax_jul_mean, gdd` <= 2e-13. The window matters (extending it to Aug 22 would change `d2_weeks_50pct` in 979 of 5,920 rows, and 235,980 raw weather rows dated Aug 15-Sep 29 exist and are excluded).
* **Three spot checks** (recomputed from raw maps / daily weather):

| County-year | maps used | `d2_weeks_50pct` file / recompute | `precip_ratio_vs_normal` file / recompute | `heat35_days` file / recompute |
|---|---|---|---|---|
| Richardson NE corn 2012 | 20 (Apr 3-Aug 14) | 4 / 4 | 0.5462 / 0.5462 (199.7 mm / 365.6 mm) | 24 / 24 |
| Story IA corn 2013 | 20 (Apr 2-Aug 13) | 2 / 2 | 1.1102 / 1.1102 (484.1 / 436.1) | 0 / 0 |
| Lancaster NE soy 2006 | 19 (Apr 4-Aug 8) | 4 / 4 | 0.7963 / 0.7963 (281.1 / 353.0) | 17 / 17 |

* Rain normals and irrigation averages use only years <= 2012 (verified: recomputation with `year <= 2012` matches to 2e-16, `irr_share_train_mean` to 1e-16). CONCERNs:
  1. **The documented 2000-2012 normal is really 1999-2012.** `weather_daily.parquet` starts 1999-01-01 and `organize_usda_data.py:204` filters `year <= TRAIN_END`. With a strict 2000-2012 normal the ratio is 0.5479 instead of 0.5462 for Richardson 2012. `DATA_README.md` and the README text say 2000-2012. Harmless for leakage (1999 is earlier), wrong as documentation.
  2. **Normals and irrigation averages are not fold-causal.** For a walk-forward fold Y < 2013 the same 2000(1999)-2012 normal is used for training rows *and* the test row, so it includes years >= Y (for fold 2006, 6 later years including 2012). Rebuilt per fold from years < Y only (`check_causal_features.py`): capture A +0.007, B +0.023, C +0.007, D +0.017; AUC +0.002 to +0.009; WAPE A +0.033, B +0.016, C +0.002, D +0.008. Mean |prediction change| 0.001-0.004 of a share. Conclusion: not material, but fix the build (or document) for hygiene. Validation and test years are unaffected (their normal is from <= 2012).
  3. **Drought Monitor release dates.** Maps are valid Tuesday and released Thursday; `organize_usda_data.py:178` keeps maps dated < Aug 15, so in years where the last map is dated Aug 13/14 it is released Aug 15/16. Maps released **after** the decision date are used in 2001 and 2007 and 2012 (Aug 14 map, released Aug 16) and in 2018 (a test year); Aug 13 maps (released the morning of Aug 15) in 2002, 2013, 2019, 2024. Strictly keeping only maps released before Aug 15 changes features in 2002 (43 % of rows change `d2_weeks_50pct`), 2007 (6 %), **2012 (100 % of rows, -1 week; mean |DSCI| change 11.9)** and 2013 (26 %) (`audit/check_usdm_release.py`). One-day timing effect; I have not re-fit models to measure it, but 2012 carries 91 % of the walk-forward dollars so it is the year where it would matter.
  4. **History features can act as a weak year proxy** (README already says so): `yield_prev5_mean` is missing for 100 % of 2000-2002 rows and `acres_planted_prev3_mean` for 100 % of 2000 (`audit/out_history_wip.txt`). Dropping both features from A, B, D (walk-forward, uncalibrated): capture A 0.471 -> 0.476, B 0.497 -> 0.516, D 0.517 -> 0.514; AUC A +0.007, B +0.018, D +0.019. They add nothing; remove them or keep as is, results do not depend on them. (A's WAPE blows up to 2.37 without them because its level is unstable, see check 8.)

### 5. Joins and rows: PASS

(`audit/check_data.py`) Training: 4,810 input rows = 4,810 label rows = `manifest.json` `rows`; validation 1,110 = 1,110 = manifest. 190 counties both splits (= manifest). Join `fips, crop, year`: 4,810 `both`, 0 `left_only`, 0 `right_only` (validation 1,110/0/0), `validate="one_to_one"` in `data.py:61`. Duplicate (fips, crop, year): **0** in inputs and labels. `fips` length set = {5} everywhere; `data.py:62` asserts it and all readers use `dtype={"fips": str}`.
Filters (`data.usable`, `data.py:69-73`): training 4,810 -> **4,734** usable (76 rows `insured` is NaN / `liability` NaN: no coverage record), validation 1,110 -> **1,101** (9 dropped). `rma_year_available` is True for every row 2000-2015, so that filter removes nothing in these splits (it will matter only if a testing year's colsom file were missing). No row with `insured` False exists (the field is True or blank). **Real zeros are kept**: 796 training rows (16.8 %) and 245 validation rows (22.3 %) have a drought payout of exactly 0. Negative payout shares exist (5 training, 4 validation: reversals), clipped to 0 for fitting only (`data.py:80-82`) and left as-is in evaluation. No share > 1. Drought dollars in dropped rows: $0 of $4.27 B (training) and $1.15 B (validation), because those rows have no payout at all.

### 6. Labels vs raw colsom: CONCERN

I re-parsed the raw `~/Downloads/colsom_YYYY.zip` files independently (`audit/check_data.py`; cause code 11 = DROUGHT; plan not matching SCO/ECO/STAX/ARP/AYP/GRP/GRIP/MP/HIP/PACE; cause 55 and county 999 excluded; Iowa+Nebraska corn+soybeans) and summed `drought_indemnity` from the label files (`audit/out_check6_labels_vs_raw.csv`).

* **2018 and 2022: not comparable.** Their label files are in `usda_budget_data/testing/`, which I was told never to read. Raw totals for the record: **2018 = $36,942,890** (IA $25,243,676, NE $11,699,213); **2022 = $1,117,429,701** (IA $257,464,936, NE $859,964,765). The three 2022 raw copies (`colsom_2022.txt`, `.zip`, `(1).zip`) are identical (3,991 rows, same total), so `find_files` picking either one is fine.
* **2000-2015 (16 years): the label files equal the raw totals except for one Iowa county.** Every difference (e.g. 2012: raw $3,063,560,674, labels $3,038,746,236, diff **$24,814,438 = 0.81 %**; 2003 $3,175,974 = 0.95 %; 2008 $907,243 = 1.7 %; 2001 1.2 %; years with zero difference: 2009, 2010, 2013, 2014, 2015) equals exactly the drought payout of **FIPS 19156 "W Pottawattamie"**, which RMA reports separately from 19155 Pottawattamie and which is not in the master dataset, so it is not in the 190-county universe (`audit/out_missing_counties.txt`: $31,545,451 over 2000-2012). Its insured liability is also missing. Effect on the metrics: Iowa's actual statewide totals are low by up to 1.7 % (0.8 % in the dominant year 2012); that county can never be predicted or captured. Estimated effect on pooled WAPE or capture: < 0.01. Fix: add 19156 to 19155 (or to the master data) and rebuild, **before** freezing, because rebuilding later would change every number.

### 7. Hand check: PASS

Richardson NE (FIPS 31147), 2012, model B, fold = train 2000-2011 (`audit/check_handcalc.py`, plain sklearn, own code path; B params max_iter 200, max_depth 4, k_B(T1) = 1.183014 from `calibration.csv`).

| Crop | liability | indemnity | actual share | B raw share | B x k | predicted $ |
|---|---|---|---|---|---|---|
| corn | $61,621,630 | $11,881,418.72 | 0.192812 | 0.269006 | 0.318238 | $19,610,330 |
| soybeans | $37,198,464 | $1,472,778.38 | 0.039592 | 0.094801 | 0.112151 | $4,171,848 |
| county-year | | $13,354,197 | | | | **$23,782,174** |

Saved `oos_predictions.csv` shares equal the hand refit to 7e-17. County-year absolute error = $10,427,977. Contribution to **walk-forward WAPE 0.5745** ($1,909,270,398 error / $3,323,487,120 actual, 1,307 county-years): 0.314 percentage points; to **pooled WAPE 0.6620**: 0.233 points. Capture: Richardson is B's **8th-ranked** NE-2012 county (cutoff for top-20 $17.0 M) and truly ranks 32nd, holds 1.11 % of NE 2012 payouts; NE 2012 capture = $585,001,346 / $1,201,040,591 = **0.4871**. My own per-state-year capture means: walk-forward **0.4975**, validation 0.2996, pooled 0.4381 vs reported 0.497486 / 0.299645 / 0.438133, and WAPE 0.574478 / 0.915626 / 0.661981: exact.

### 8. Model A (hurdle): CONCERN

`audit/check_modelA.py`, `check_modelA_smear.py`. The back-transformation is implemented as documented: `smear_ = Σ w·exp(resid) / Σ w` over training positives (`hurdle.py:54`), `conditional = exp(fit)·smear_` (`:64`), `predict = clip(P·conditional, 0, 1)` (`:67`). I recomputed the weighted Duan factor independently: it matches in every fold (3.09, 3.42, 3.34, 3.02, 3.18, 3.22, 3.29; 3.09 for validation).

**But the factor over-corrects.** Duan's estimator is only consistent if residuals are independent of the fitted value; here the log residuals are large (sd about 1.5) and heteroscedastic. In-sample, the weighted mean of `exp(fit)·smear` over the positives is **1.8-2.3x the weighted mean of the actual shares** (without smearing 0.60-0.74x). A ratio estimator (`Σ w y / Σ w exp(fit)`) gets it to 1.0 in-sample and gives k = 1.21 instead of 0.61; **after k the two variants are identical**: WAPE 0.670 pooled, capture 0.444, AUC 0.780 (`out_modelA_smear_committed.txt`). So the factor mis-scales A by a roughly constant amount that k removes; it does not change capture, AUC or the post-k WAPE.

**Why A's calibration swings 1.32 / 0.41 / 0.25** (rows of `validation_results.csv`: pooled uncalibrated 1.322; validation uncalibrated 0.407; validation calibrated 0.248 = 0.407 x k 0.611):
1. Σpred/Σactual is a dollar-weighted statistic dominated by one or two years. 2012 is **91.4 %** of the walk-forward dollars, where A predicts a share of 0.210 vs 0.136 actual (1.54x); that drives walk-forward 1.64 and the pooled 1.32.
2. The validation total is dominated by **Iowa 2013** (the drought that started after Aug 15), where A predicts 0.017 vs 0.044 (0.39x) -> 0.41.
3. k = 0.611 is the inverse of the 2012 over-prediction, so applying it to a year A already under-predicts pushes 0.41 down to 0.25.
4. Year by year A's raw Σpred/Σactual (2006..2015) is 4.1, 1.45, 0.84, 11.4, 7.1, 1.8, 1.54, 0.39, 0.38, 2.2: the amount-given-payout term (`cond_bias` 0.4-9.1x) drives it; the P(any) term is near 1 except 2008-2010 (0.80, 1.54, 2.72). `max_cond` is 2.8 in 2012 and 1.16 in 2006 (clipped at 1 by `predict`).
5. Intercept shift (`hurdle.py:48`) assumes balanced class weights imply a 50 % prior, but balanced x liability weights imply 0.44-0.56; the logit error is up to 0.23, yet the in-sample mean P / prior is 1.000-1.003, so it has no practical effect.

### 9. Monotonic constraints: PASS

`gbm.py:11` (committed and snapshot identical). Constrained features and signs, with the training Spearman correlation against T1 (`audit/out_monotone_committed.txt`):

| Feature | sign | Spearman(all / IA / NE) | makes sense? |
|---|---|---|---|
| `d2_weeks_50pct` | +1 | +0.58 / +0.56 / +0.58 | yes: more drought weeks, more payout |
| `d3_weeks_50pct` | +1 | +0.41 / +0.36 / +0.43 | yes |
| `d2_max_pct` | +1 | +0.62 / +0.58 / +0.65 | yes |
| `dsci_mean` | +1 | +0.65 / +0.69 / +0.60 | yes |
| `heat35_days` | +1 | +0.46 / +0.47 / +0.47 | yes |
| `precip_ratio_vs_normal` | -1 | -0.62 / -0.59 / -0.66 | yes: more rain, less payout |
| `aws_100cm_mm` | -1 | +0.02 / -0.01 / +0.08 | physically plausible (more soil water, less loss) but the data show ~no relation |
| `irr_share_train_mean` | -1 | +0.06 / n.a. (IA constant 0) / -0.23 | plausible; pooled sign is flipped by the state mix, within Nebraska it is negative |

Not constrained although they correlate positively: `d2_pct_last_map` (+0.52), `d3_pct_last_map` (+0.39), `heat32_days` (+0.43), `tmax_jul_mean` (+0.47). The shipped partial-dependence curves are monotone in the right direction for all six plotted features.
**B run once without constraints** (same params, seed, weights; uncalibrated; "cal" = with each variant's own walk-forward k):

| | capture | AUC | WAPE | WAPE cal | Σpred/Σactual |
|---|---|---|---|---|---|
| Walk-forward, constrained | 0.497 | 0.815 | 0.554 | 0.574 | 0.845 |
| Walk-forward, unconstrained | 0.502 | 0.778 | 0.613 | 0.632 | 0.667 |
| Validation, constrained | 0.300 | 0.724 | 0.900 | 0.916 | 0.539 |
| Validation, unconstrained | 0.298 | 0.702 | 0.940 | 0.996 | 0.479 |

Constraints cost nothing in capture (+0.005 / -0.002 without them) and improve AUC by 0.02-0.04 and WAPE by 0.04-0.08. Keep them.

### 10. Metric definitions: PASS; one CONCERN

(`evaluate.py`, committed line numbers; the snapshot differs only by a few shifted lines.)

```python
# 78-80  county-year: predicted $ = predicted share x liability (T1) or x insured_acres (T2), crops SUMMED per county-year
d = pred.assign(_p=pred[col] * pred[weight], _a=actual_amount(pred, t))   # actual = drought_indemnity.fillna(0)
cy = d.groupby(["state_alpha", "fips", "year"]).agg(pred=sum, actual=sum)
# 83-91  state-year table: capture = top-20 COUNTIES (corn+soy combined) by predicted $, per state-year
"capture": g.nlargest(20, "pred").actual.sum() / a if a > 0 else nan   ;   "random": min(1, 20/len(g))   ;   "oracle": top-20 by actual
# 109,111,113-114
"calibration":    cy.pred.sum() / cy.actual.sum()
"capture_top20":  sy.capture.mean()                                  # unweighted mean over state-years (14 WF + 6 validation = 20)
"wape":           (cy.pred - cy.actual).abs().sum() / cy.actual.sum() # county-year, dollar-weighted
"auc_any_payout": roc_auc_score(pos, score)                         # pos = t1_actual > 0; ROW level (county x crop x year), unweighted, pooled
# 177 (range_rows)  80% coverage: share of state-years with  low <= actual statewide total <= high
```
* **Capture is across crops** (a county's corn and soybean dollars are added, then 20 counties are picked per state-year), unweighted over state-years: quiet years with tiny totals count as much as 2012. Only 3 of 20 state-years are drought years, so the mean is mostly quiet-year ranking.
* **Random** = 20 / number of counties in the state-year (89-99), i.e. 21.5 % pooled.
* **Calibration**, **WAPE**: county-year totals; dollar-weighted by construction. AUC and capture are not weighted by liability; model *training* is (check 11).
* **Capture and AUC are unchanged by calibration**: verified on the shipped results, max |before-after| over 126 rows (committed) / 162 rows (snapshot) = **0.0 for capture, 1.1e-16 for AUC**. Reason: k is one positive constant per model x target, and A's AUC score is its uncalibrated P(any).
* **CONCERN (definition)**: AUC scores differ by model: A uses its part-1 probability P(any), every other model uses its predicted share. "Any payout" is positive in 78-83 % of rows, so AUC mostly measures separating tiny shares from zeros. Not comparable across A and the rest. Tied predictions (B0/B1/B2 produce ties) are broken by row order in `nlargest`; B2 predicts exactly 0 for every non-triggering county, so its top-20 is partly arbitrary.

### 11. Sample weights: PASS (G ignores them; T2 mismatch)

| Model | training weights | where |
|---|---|---|
| B0, B1 | liability-weighted means; isotonic weights = bin liability | `baselines.py:14-54` |
| A | `norm_weights` (liability / mean) in the logit (multiplies the balanced class weights), the ridge, and the smearing mean | `hurdle.py:36,46,52,54` |
| B | `sample_weight=norm_weights(train)` | `gbm.py:27` |
| C | neighbours chosen unweighted; prediction = liability-weighted mean of the k neighbours; spread = liability-weighted quantiles | `analog.py:61,13-19` |
| D | `sample_weight=norm_weights(train)` | `tweedie.py:25` |
| **G** | **none** (`TabPFNRegressor.fit` takes no weights; stated in the file's docstring) | `tabpfn_model.py:36` |
| B2 | liability-weighted mean of triggering rows | `baselines.py` snapshot |

Inconsistency (should fix): the **T2 models are also fit with liability weights** (`norm_weights` is always liability) while T2 is evaluated and calibrated in *insured acres*. Evaluation (WAPE, capture, calibration) is dollar/acre weighted, AUC unweighted. `GBMDollars` (side check) is unweighted by design. G's missing weights matter for comparison: G treats a $0.5 M county like a $60 M one while the metric does not.

### 12. Calibration k: FAIL (not nested; flatters the pooled numbers)

`evaluate.fit_calibration` (`:399-408`) computes **one k per model x target from all 7 walk-forward years** and `apply_k` (`:411-424`) multiplies it into the walk-forward predictions it was fitted on and the validation predictions. So:
* Walk-forward "after" numbers are in-sample for k (the code says so, `evaluate.py:15-16`); validation is out-of-sample for k (fine).
* The headline **pooled** figures mix both. I divided each model's k back out of `oos_predictions.csv` and re-calibrated with a **strictly nested** k (for year Y: Σactual/Σpred over walk-forward years < Y; k = 1 for 2006), `audit/check_calibration_ranges.py`:

| Pooled WF+validation, T1 | WAPE reported | WAPE nested | Σpred/Σactual reported | nested | capture |
|---|---|---|---|---|---|
| A | 0.670 | 0.740 (+0.070) | 0.807 | 0.586 | 0.444 |
| B | 0.662 | 0.709 (+0.047) | 0.907 | 0.577 | 0.438 |
| C | 0.791 | 0.809 (+0.018) | 0.959 | 0.579 | 0.402 |
| D | 0.731 | 0.834 (+0.103) | 0.859 | 0.412 | 0.498 |
| G | 0.679 | 0.741 (+0.062) | 0.920 | 0.543 | 0.478 |
| B0 | 1.921 | 1.529 (-0.391) | 1.567 | 0.969 | 0.265 |
| B1 | 1.387 | 1.368 (-0.019) | 1.412 | 0.856 | 0.289 |

* **Capture and AUC are untouched** (a constant factor). The WAPE order of the leading models is unchanged (B < A < G) but D drops from fourth to last (0.834 vs C 0.809); the baselines' WAPE actually looks better nested because their reported k (2.0) is far too high for 2013-15.
* k is dominated by one year: **2012 = 91.4 % of walk-forward actual dollars** (2006 3.4 %, 2011 2.1 %, 2008 1.6 %, 2007 1.4 %, 2009 0.1 %, 2010 0.03 %). So k is effectively "the 2012 ratio"; reported calibration of 0.91-0.96 for B, C, G is mostly an artifact.
* **Choice rule**: on the committed code the rule gives B on uncalibrated predictions and A (A and B both near-best) under both the reported and the nested k. On the snapshot the rule picks **G** under all three, but the margin is razor thin: G passes the capture band by 0.0004 (0.47816 vs threshold 0.47777) and, **under nested k, passes the WAPE band by 0.003** (0.741 vs ceiling 0.7445). A paired bootstrap over years (`audit/check_selection_noise.py`) shows D − G capture = +0.020 with a 90 % interval of [-0.022, +0.065] (D, the best capture, is not distinguishable from G) and B − G WAPE = -0.017 [-0.070, -0.004] (B has the lower dollar error, also with B − G capture = -0.040 [-0.095, +0.017]); the declared "noise" bands (0.02 capture, 5 % WAPE) are of the same size as the sampling noise, so the choice between D, G and B is not statistically supported by 20 state-years (3 drought years).
* For the final test k is applied to years it never saw, which is the honest use; the problem is only that the validation-phase selection numbers are optimistic.

### 13. Range method: PASS (C neighbours) / CONCERN (widening, selection)

* **C's range uses training-only neighbours.** `Analog.fit` builds `pool_` from the frame given (`analog.py:32-42`); `quantiles` takes the liability-weighted 10th/90th percentile of those neighbours' shares (`:65-68`). Verified on every walk-forward fold and the validation fit (`check_calibration_ranges.py`): all neighbour years < Y, **0 violations**; the pool never contains the test row.
* **Widening is not applied the same way everywhere.** `widen_to_include` (`budget.py:129-135`) is used by the *budget range* (`evaluate.budget_range_rows`, `:434-444`, and `budget.statewide_range`, `:138-152`): best coverage method, widened to contain the headline model's calibrated point. It is **not** applied to the per-model ranges in the report tables and in the `range_cov` metric (`range_rows`, `:157-178`), which are raw. In the **committed** `final_test.py:47` the "chosen model, per state-year" table is the chosen model's *own raw* range (`cov[cov.model == chosen]`), not the widened best-method budget range the app shows. The **snapshot's** `final_test.py:93` calls `budget_range_rows(cov, chosen, method)`, so the snapshot fixes this.
* Coverage (T1, pooled 20 state-years): A 9/20, B 8/20, C 16/20, D 9/20, G 8/20, **budget 16/20 = C**. Widening did not change the count (chosen A on the committed code: point inside the range in 18/20; chosen G on the snapshot 20/20).
* Selection issue: C is chosen as "the best of five methods" using the same 20 state-years on which its 80 % is reported, with only 3 drought state-years; expect lower honest coverage. `final_test` reads the residual pools from `oos_predictions.csv`, so that file must come from the final `evaluate.py` run (see check 14).

### 14. Reproducibility: PASS (committed: byte-identical; snapshot: all models except G exact, G within 0.003 WAPE; shipped snapshot results are stale)

**Committed branch: PASS, byte-identical.** I copied `app/model/` (committed code) to a scratch directory with an empty `results/`, symlinked the data, and ran `python app/model/evaluate.py` from a fresh process (~8 min; seeds are fixed: `GBM(seed=0)`, `random_state=0`; nothing else is random). All **15 result files are byte-identical** to the committed ones: `calibration.csv, chosen_model.json, gbm_partial_dependence_validation.csv, gbm_permutation_importance_validation.csv, hurdle_coefficients.csv, oos_predictions.csv, params.json, range_method.json, side_check_dollar_target.csv, tuning.csv, validation_budget_totals.csv, validation_predictions.csv, validation_report.md, validation_results.csv, validation_state_years.csv` (`audit/out_repro_committed.txt`). The summary numbers therefore match exactly (pooled calibrated: A capture 0.444 / WAPE 0.670, B 0.438 / 0.662, C 0.402 / 0.791).

**Snapshot (uncommitted code, with D, G, B2): PASS for every model except G; results files are stale.** Same procedure, ~25 min including G on MPS (`audit/out_repro_wip.txt`):
* B0, B1, A, B, C, D reproduce **exactly** (k, predictions, metrics, range coverage; `tuning.csv`, `params.json`, `chosen_model.json`, `range_method.json` byte-identical).
* **G (TabPFN v2) is not bit-reproducible** although `random_state=0`: row-level predictions moved by up to 0.007 (T1 share) and 0.020 (T2 share); k_T1[G] 1.413034 -> 1.414929; uncalibrated G walk-forward WAPE 0.5936 -> 0.5930, AUC 0.7582 -> 0.7582, capture 0.5065 -> 0.5065; pooled calibrated capture 0.47816 -> 0.47816, WAPE 0.67927 -> 0.67828; the largest change in any capture or WAPE cell of `validation_results.csv` is 0.019 (a small drought/quiet subgroup) and 0.003, so the pick (G) did not change. It runs on the Apple GPU (MPS) in this environment; I did not test a CPU run.
* **The shipped snapshot results do not match the snapshot code**: `results/` was generated before B2 existed (`calibration.csv` has 14 rows instead of 16, `oos_predictions.csv` has no `t*_B2` columns, `validation_results.csv` 324 rows instead of 360). Consequence, verified: `evaluate.apply_k` raises `KeyError: ('B2', 't1')` on that `calibration.csv` (`audit/out_stale_results_wip.txt`), i.e. **`final_test.py` would crash** until `evaluate.py` is re-run; and `final_test.py` reads the 80 % residual pools from `oos_predictions.csv`, so those must come from the final run. After re-running, the only differences are the added B2 rows and G's jitter above.

## Findings

### Must fix before the final test (bugs / process errors that change or block results)

1. **Re-run `evaluate.py` on the final code and keep those results (snapshot).** The shipped `results/` predate B2: `calibration.csv` has no B2 row, so `final_test.py` fails with `KeyError: ('B2', 't1')`; `oos_predictions.csv` (used for the A/B/D/G range pools in the final test) and `chosen_model.json` must come from the same run as the code. If someone works around the crash by dropping B2, the model set changes. Effect on results once re-run: B2 rows added; G moves by ~0.001-0.003 in WAPE (item 5 of "Should fix").
2. **Calibration k is fitted on the walk-forward years it is then scored on, and the pooled figures use it** (`evaluate.py:399-424`, check 12). Pooled calibrated WAPE is too low by A +0.070, B +0.047, C +0.018, D +0.103, G +0.062 (e.g. B 0.662 -> 0.709, D 0.731 -> 0.834, G 0.679 -> 0.741) and the pooled Σpred/Σactual of 0.81-0.96 is really 0.41-0.59 once k is nested. Capture and AUC are unchanged, the order B < A < G by WAPE is unchanged (D falls below C), but G's WAPE margin in the selection rule drops from 0.016 to 0.003 and its capture margin is 0.0004. Report and select with nested k (or validation-only numbers). The k that the final test applies (walk-forward 2006-2012, 91 % of it 2012) is out-of-sample for 2016-2025, so the test itself is not biased by this.
3. **(Committed branch only) `final_test.py:47` reports the chosen model's own raw range, not the widened best-method budget range the app uses (`budget.statewide_range`).** The snapshot's `final_test.py` fixes this (`budget_range_rows`). Make sure the snapshot version is what gets committed. Effect: coverage figures only (e.g. A/B 40-45 % raw vs 80 % budget range).

No finding changes capture, AUC or the model ordering. I found **no label leakage**: no model, scaler, imputer, bin set, neighbour pool, TabPFN context set, `alpha` or hyper-parameter choice sees a row from year >= Y in a fold, and testing/ is untouched.

### Should fix (correctness or clarity, conclusions unchanged)

1. **W Pottawattamie (FIPS 19156) is missing** from the universe: labels short by $24.8 M (0.81 %) in Iowa 2012, up to 1.7 % in other Iowa years (check 6). Effect on pooled WAPE / capture < 0.01. Rebuild the data once, before freezing.
2. **Rain normal is 1999-2012, documented 2000-2012** (`organize_usda_data.py:204`, weather file starts 1999). Fix the code or `DATA_README.md`.
3. **Rain normals and irrigation averages are not fold-causal** (use years >= Y inside walk-forward folds). Fold-causal rerun: capture +0.007 to +0.023, AUC +0.002 to +0.009, WAPE +0.002 to +0.033 (A, B, C, D). Immaterial; build per-fold or note.
4. **Drought Monitor release timing**: maps dated Aug 13/14 are used although released Aug 15/16 (2001, 2007, 2012, 2018 after the decision date; 2002, 2013, 2019, 2024 on it). Excluding them changes the 2012 features for every county (-1 week of D2, mean |DSCI| 11.9) and 43 % / 26 % / 6 % of rows in 2002 / 2013 / 2007. Not measured on model output; 2012 is 91 % of the walk-forward dollars.
5. **G is not bit-reproducible** (GPU, `random_state` fixed) and ignores sample weights; the 0.0004 capture margin that makes G "near-best" is far inside run-to-run and sampling noise (D − G capture +0.020, 90 % interval [-0.022, +0.065]). Do not present G's selection as more than a tie with D/B.
6. **Model A's smearing factor over-scales the conditional amount by about 2x** in-sample (3.1-3.4 factor; ratio estimator needs 1.21 vs 0.61 for k). Absorbed by k (post-k metrics identical), but A's uncalibrated Σpred/Σactual (1.64 / 0.41) and its WAPE without k (0.85-0.96, 2.37 when history features are dropped) are fragile. Replace with `Σ w y / Σ w exp(fit)`.
7. **Hyper-parameters are chosen on the same walk-forward folds that are reported** (optimistic by ~0.02-0.03 WAPE for B and C, up to 0.13 for D vs the grid median); D's `alpha=0.01` is the smallest grid value.
8. **Range method**: widening exists only in the budget range; per-model coverage tables are raw; C was selected as the best of five methods on the same 20 state-years (3 drought years) it is judged on; A/B/D/G walk-forward pools include later years.
9. **T2 models are trained with liability weights but scored in acres**; AUC compares A's P(any) with other models' predicted shares; B2's zero predictions tie in the top-20; the noise bands 0.02 / 5 % in `choose()` are as large as the sampling noise.
10. **History features** (`yield_prev5_mean`, `acres_planted_prev3_mean`) are year proxies in 2000-2002 and add nothing (dropping them: capture +0.005 to +0.019 for A, B; ~0 for D).
11. **Docs**: `MODEL_PLAN.md` is not in the repo; the committed README/`DATA_README` describe the committed model set; main's README has uncommitted edits. Say in the shuffle section that the null capture level is 28.7 %, not 21.5 %.

### OK (checks that passed)

* **Shuffle test (1)**: strict null drives all models to capture 0.24-0.30 (liability-ranking level 0.287, random 0.215) and AUC 0.49-0.61; same for G.
* **Cheat test (2)**: B + true target = capture 0.767 vs oracle 0.768, AUC 0.999; D reaches 0.751 with a log-form copy.
* **Fold leakage (3)**: every scaler, imputer, bin set, kNN pool, B0/B1 table, Tweedie/Hurdle/GBM fit and TabPFN context set uses only rows < Y (281 / 254 asserted predict() calls, independent recomputation per fold).
* **Features (4)**: all drought and weather features reproduce from the raw parquet files for all 5,920 rows (max diff <= 2e-13); three spot checks match exactly; no label column is a feature; rain normals and irrigation averages use only years <= 2012.
* **Joins and rows (5)**: 0 duplicate keys, 5-character fips, row counts equal the manifest, filters and zeros as specified.
* **Labels (6)** apart from the W Pottawattamie gap: over 2000-2015 every state x crop x year total matches the raw colsom files to within $1 except Iowa, and the Iowa total differences equal that one county's payouts year by year (e.g. $24,814,438 in 2012). I compared totals per state x crop x year, not county by county.
* **Hand check (7)** reproduces B's Richardson NE 2012 prediction, WAPE and capture exactly.
* **Monotonic constraints (9)**: signs are physically sensible and match the data except two weak ones; they help AUC and WAPE and cost no capture.
* **Metric definitions (10)**: capture and AUC are exactly invariant to calibration (0.0 and 1.1e-16).
* **Sample weights (11)**: liability weights are applied in A, B, C (prediction), D, B0, B1, B2; G's omission is documented.
* **Range method (13)**: C's neighbours are training-only (0 violations).
* **Reproducibility (14)**: committed code reproduces all 15 result files byte-for-byte; the snapshot reproduces except G's GPU jitter.

