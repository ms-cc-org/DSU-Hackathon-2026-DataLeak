# Drought-severity model: validation report (walk-forward 2006-2012, validation 2013-2015)

Only years <= 2015 were used. Models and settings were fixed in `DECISIONS.md` before any result was seen; nothing was tuned. Walk-forward = train on 2000..Y-1, predict Y. AUC and Brier are for `worse` (did the worst level get worse than the start level); exact / within-1 are for the predicted level 0-5 (model level = start level + the training median step when P(worse) >= 0.5). Persistence cannot rank (it predicts no change), so its AUC is 0.5 by construction.

## Summary for the pitch (5 lines)

1. In-season (Task B), weather + soil with the April-1 drought level predict whether a county's drought gets worse by Aug 13 with AUC 0.86 (walk-forward) and 0.78 (2013-2015), against 0.50 for county climatology.
2. After Aug 13 (Task A), the best model reaches AUC 0.65 (walk-forward) and 0.69 (2013-2015) for 'does it get worse', against 0.54 for climatology; it does NOT beat simply assuming no change on exact level, so the honest message is that the Aug-15 drought map is already the best forecast of the level.
3. The chosen models are M1 logistic (A) and M1 logistic (B), picked by a rule fixed before looking, with the simpler model winning ties.
4. The simulation helper turns Task B into a what-if tool: for Iowa 2012, scaling precipitation to 60% raises the mean chance of worsening from 0.74 to 0.92 (flagging any input outside what the model has seen).
5. All numbers use only years up to 2015 with maps limited to those released by Aug 15; the 2016-2025 test is untouched and runs only on request (`final_test.py --i-am-sure`).

## Task A: outlook after Aug 13

Start level = `level_last_map`. Label rate of `worse`: walk-forward 27%, validation 32%.

| Method | WF AUC | WF Brier | WF exact level | WF within 1 | Val AUC | Val Brier | Val exact level | Val within 1 |
|---|---|---|---|---|---|---|---|---|
| Persistence | 0.500 (const.) | 0.272 | 62.8% | 96.9% | 0.500 (const.) | 0.321 | 63.9% | 93.6% |
| Climatology | 0.544 | 0.341 | 26.3% | 59.7% | 0.450 | 0.340 | 34.2% | 65.8% |
| Most common level | 0.500 (const.) | 0.216 | 26.9% | 67.5% | 0.500 (const.) | 0.221 | 41.3% | 66.3% |
| M1 logistic | 0.650 | 0.231 | 58.9% | 96.3% | 0.694 | 0.245 | 54.3% | 98.8% |
| M2 gradient boosting | 0.611 | 0.254 | 57.5% | 94.5% | 0.650 | 0.223 | 60.4% | 95.8% |
| M3 kNN look-alikes | 0.517 | 0.232 | 58.3% | 96.1% | 0.607 | 0.261 | 50.9% | 93.9% |

**Chosen model: M1 logistic.** Rule (fixed in advance): best walk-forward AUC; models within 0.02 of the best are tied and the simplest wins (M1 < M3 < M2). Walk-forward AUC: M1 logistic 0.650, M2 gradient boosting 0.611, M3 kNN look-alikes 0.517; tied set: ['M1 logistic']. Validation AUC of the chosen model: 0.694. Beats climatology on AUC: **yes** (0.650 vs 0.544); beats persistence on exact level (walk-forward): **no** (58.9% vs 62.8%).

### Worsening rate per state-year, predicted vs actual (M1 logistic and the others)

| State-year | Actual worsening rate | Climatology | Most common level | M1 logistic | M2 gradient boosting | M3 kNN look-alikes |
|---|---|---|---|---|---|---|
| IA 2012 | 16% | 1% | 34% | 10% | 75% | 14% |
| IA 2013 | 93% | 31% | 34% | 68% | 57% | 65% |
| NE 2012 | 73% | 4% | 34% | 13% | 64% | 1% |

Correlation of predicted and actual state-year worsening rate over all 20 state-years (2006-2015): Climatology -0.05, Most common level -0.49, M1 logistic 0.21, M2 gradient boosting 0.26, M3 kNN look-alikes 0.22.

### Calibration by decile of predicted risk (M1 logistic, pooled 2006-2015)

| Decile | n | Mean predicted | Actual rate |
|---|---|---|---|
| 1 | 192 | 0.01 | 0.03 |
| 2 | 192 | 0.03 | 0.19 |
| 3 | 192 | 0.06 | 0.16 |
| 4 | 192 | 0.12 | 0.28 |
| 5 | 192 | 0.19 | 0.31 |
| 6 | 192 | 0.28 | 0.31 |
| 7 | 192 | 0.40 | 0.35 |
| 8 | 192 | 0.53 | 0.40 |
| 9 | 192 | 0.71 | 0.50 |
| 10 | 192 | 0.92 | 0.35 |

### Permutation importance (M1 logistic, trained 2000-2012, scored 2013-2015, validation AUC 0.695; drop in AUC when the feature is shuffled)

| Feature | AUC drop |
|---|---|
| level_last_map | 0.139 |
| precip_30d | 0.103 |
| wb_apr1 | 0.080 |
| nbr_level_last | 0.065 |
| dsci_last | 0.048 |
| precip_apr1_to_cutoff | 0.038 |
| tmax_mean_30d | 0.036 |
| wb_90d | 0.033 |
| dry_days_30d | 0.024 |
| precip_60d | 0.017 |

## Task B: in-season severity (weather + soil)

Start level = `level_apr1`. Label rate of `worse`: walk-forward 45%, validation 12%.

| Method | WF AUC | WF Brier | WF exact level | WF within 1 | Val AUC | Val Brier | Val exact level | Val within 1 |
|---|---|---|---|---|---|---|---|---|
| Persistence | 0.500 (const.) | 0.452 | 51.4% | 75.4% | 0.500 (const.) | 0.120 | 87.8% | 99.5% |
| Climatology | 0.504 | 0.363 | 23.2% | 58.0% | 0.766 | 0.181 | 15.5% | 54.5% |
| Most common level | 0.500 (const.) | 0.256 | 14.0% | 62.6% | 0.500 (const.) | 0.201 | 22.6% | 64.1% |
| M1 logistic | 0.860 | 0.149 | 53.2% | 83.5% | 0.775 | 0.093 | 88.0% | 99.8% |
| M2 gradient boosting | 0.764 | 0.205 | 49.3% | 78.6% | 0.481 | 0.160 | 83.2% | 99.5% |
| M3 kNN look-alikes | 0.792 | 0.186 | 47.2% | 82.1% | 0.691 | 0.109 | 86.6% | 99.3% |

**Chosen model: M1 logistic.** Rule (fixed in advance): best walk-forward AUC; models within 0.02 of the best are tied and the simplest wins (M1 < M3 < M2). Walk-forward AUC: M1 logistic 0.860, M2 gradient boosting 0.764, M3 kNN look-alikes 0.792; tied set: ['M1 logistic']. Validation AUC of the chosen model: 0.775. Beats climatology on AUC: **yes** (0.860 vs 0.504); beats persistence on exact level (walk-forward): **yes** (53.2% vs 51.4%).

### Worsening rate per state-year, predicted vs actual (M1 logistic and the others)

| State-year | Actual worsening rate | Climatology | Most common level | M1 logistic | M2 gradient boosting | M3 kNN look-alikes |
|---|---|---|---|---|---|---|
| IA 2012 | 93% | 40% | 41% | 74% | 83% | 77% |
| IA 2013 | 7% | 18% | 45% | 8% | 35% | 25% |
| NE 2012 | 100% | 64% | 41% | 96% | 96% | 98% |

Correlation of predicted and actual state-year worsening rate over all 20 state-years (2006-2015): Climatology 0.22, Most common level -0.15, M1 logistic 0.84, M2 gradient boosting 0.69, M3 kNN look-alikes 0.81.

### Calibration by decile of predicted risk (M1 logistic, pooled 2006-2015)

| Decile | n | Mean predicted | Actual rate |
|---|---|---|---|
| 1 | 192 | 0.00 | 0.04 |
| 2 | 192 | 0.02 | 0.07 |
| 3 | 192 | 0.04 | 0.11 |
| 4 | 192 | 0.09 | 0.15 |
| 5 | 192 | 0.16 | 0.14 |
| 6 | 192 | 0.28 | 0.28 |
| 7 | 192 | 0.44 | 0.38 |
| 8 | 192 | 0.60 | 0.58 |
| 9 | 192 | 0.79 | 0.78 |
| 10 | 192 | 0.97 | 0.99 |

### Permutation importance (M1 logistic, trained 2000-2012, scored 2013-2015, validation AUC 0.783; drop in AUC when the feature is shuffled)

| Feature | AUC drop |
|---|---|
| level_apr1 | 0.266 |
| wb_apr1 | 0.128 |
| precip_apr1_to_cutoff_ratio | 0.050 |
| precip_90d_ratio | 0.043 |
| precip_apr1_to_cutoff | 0.043 |
| precip_30d | 0.028 |
| wb_90d | 0.024 |
| irr_share | 0.015 |
| prev_fall_level | 0.009 |
| precip_30d_ratio | 0.008 |

## Note on M2 and the monotone constraints (diagnostic only, not used for selection)

M2 was run exactly as specified, including +1 monotone constraints on the start/level inputs. The data disagree with that sign: the standardised M1 coefficient of the start level is -3.64 for Task A (`level_last_map`) and -2.08 for Task B (`level_apr1`), i.e. a county that is already at a high level is LESS likely to get worse (ceiling and persistence), so forcing a positive effect hurts. AUC, walk-forward / 2013-2015 / pooled 2006-2015:

| Task | M2 variant | WF AUC | Val AUC | Pooled AUC |
|---|---|---|---|---|
| A | M2 as specified (monotone constraints) | 0.611 | 0.650 | 0.620 |
| A | M2 without constraints | 0.558 | 0.699 | 0.611 |
| A | M2 constraints, but no sign forced on level inputs | 0.626 | 0.694 | 0.652 |
| B | M2 as specified (monotone constraints) | 0.764 | 0.481 | 0.734 |
| B | M2 without constraints | 0.831 | 0.726 | 0.839 |
| B | M2 constraints, but no sign forced on level inputs | 0.853 | 0.735 | 0.864 |

This explains why M2 as specified does not reproduce the exploratory Task B AUC of about 0.87 (it gets 0.76 walk-forward and 0.48 on 2013-2015); Task A reproduces (about 0.6). The variants were NOT adopted and do not change the choice: M1 stays within 0.02 of (or ahead of) the best M2 variant in both tasks, so the pre-declared rule picks M1 either way. Changing the constraint is a modelling decision for the model builder, to be made before the final test.

## Simulation helper (Task B), example

Counties: 99. Mean start level (level_apr1, observed): 1.11. Observed in 2012: mean worst level Apr 1-Aug 13 = 3.82, share of counties that got worse than their Apr 1 level = 93%.

| Scenario | Mean P(worse) | Counties with P >= 0.5 | Mean predicted level | Counties with a feature outside the training range |
|---|---|---|---|---|
| 2012 weather as observed (precip x 1.0) | 0.74 | 73% | 1.84 | 4 |
| precip x 0.6, same temperatures | 0.92 | 100% | 2.11 | 88 |

Closest historical years (most frequent among each county's 3 nearest own years): observed weather 2001 (55), 2006 (54), 2002 (47); precip x 0.6: 2003 (73), 2006 (53), 2002 (38).
Features outside the training min/max under precip x 0.6 (counties affected): {'precip_90d_ratio': 78, 'precip_60d_ratio': 45, 'precip_apr1_to_cutoff_ratio': 38, 'precip_60d': 3}.
Scaling precipitation to 60% moves mean P(worse) from 0.74 to 0.92 (+0.18) and the number of counties predicted to worsen from 72 to 99 of 99.

## Leakage and sanity checks (from the data build, `drought_severity_data/checks.md`)

- **PASS** weekly drought categories are non-overlapping (none + D0..D4 sum to ~100%)
- **PASS** drought maps loaded only for 2000-2015
- **PASS** every Task A map input (level_last_map, dsci_last, d0/d1 share, dsci_change_4wk) comes from a map dated <= 08-13
- **PASS** outlook-label maps all start on/after 08-14 (after every input map)
- **PASS** level_apr1 uses maps dated <= 04-07 only (latest map date used: 04-07), so Task B sees no map after Apr 7
- **PASS** prev_fall_level uses maps from the PREVIOUS calendar year only (all dated before Jan 1 of the decision year)
- **PASS** every weather window ends <= Aug 13 of its year (latest in-season month-day used: 813; winter window ends Mar 31)
- neighbors: 0-11 other counties within 70 km per county (median 8)
- **PASS** Task A inputs contain no label columns
- **PASS** Task B inputs contain no label columns
- **PASS** Task B inputs contain only the two allowed map-derived columns ['level_apr1', 'prev_fall_level'] (found: ['level_apr1', 'prev_fall_level']); both use maps dated <= Apr 7 of the year or before Jan 1
- **PASS** Task A inputs contain the map-state features
- **PASS** row alignment: Task A inputs has the same county-year in every row
- **PASS** row alignment: Task B inputs has the same county-year in every row
- **PASS** row alignment: Task A labels has the same county-year in every row
- **PASS** row alignment: Task B labels has the same county-year in every row
- **PASS** one row per county x year
- **PASS** every fips is a 5-character string
- **PASS** no row after 2015 in any output (2016+ excluded unless the final-test flags were given)
- **PASS** almost every county-year has >= 15 input maps (Apr 1 - Aug 13)
- **PASS** almost every county-year has >= 6 outlook maps (Aug 14 - Sep 30)
- **PASS** labels exist for almost every row (missing: worse_A 0.00%, worse_B 0.00%)
- **PASS** level_last_map always comes from a map dated by 08-13
- Task B: strongest single input vs y_B |correlation| = 0.72 (level_apr1); near 1.0 would suggest a hidden copy of the label
- **PASS** no Task B input is a near-copy of the label
- cross-check vs master max_drought_severity (corn, May 1 - Sep 30): 100.0% of 3040 county-years agree exactly (differences come from the master's own season window)
- **PASS** level definition matches the repo's master dataset for > 80% of county-years


- Model code: every imputer, scaler, base rate, county distribution and neighbour pool is fitted in `fit()` on the fold's training years only; normals and irrigation averages in the data use strictly earlier years; the loaders read only years <= 2015 and `final_test.py` is the only way to build 2016-2025 (and refuses without `--i-am-sure`).
