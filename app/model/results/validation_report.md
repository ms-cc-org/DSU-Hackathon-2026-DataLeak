# Validation report: walk-forward 2006-2012 and validation 2013-2015

Models are fitted on training years only (2000-2012 for validation; each fold's earlier years for walk-forward). **`testing/` was not
read.** Amounts are predicted drought payout = predicted T1 x insured liability (dollars), summed over crops per county-year; T2 amounts
are predicted damaged acres = T2 x insured acres. Rows used: 4734 training and 1101 validation (insured, liability > 0,
RMA year available; zero payouts kept). Raw numbers: `validation_results.csv` (all metrics) and `validation_state_years.csv` (per state-year).

How to read the tables. *Statewide total error* = mean over state-years of |predicted - actual| / actual for the statewide total.
*Weighted MAE* = mean absolute error per county-year in dollars (acres for T2); in absolute dollars, so big counties weigh more.
*Budget capture* = share of actual drought payouts landing in the 20 counties with the highest predicted payout, averaged over state-years
(random = what picking 20 counties by chance gives). *Any-payout AUC* = ranking of rows with any payout above rows with none.
*Calibration* = Σ predicted / Σ actual (<1 under-budgets). *80% range coverage* = share of state-years whose actual statewide total
falls inside the 10th-90th percentile range (target ~80%; k/n shown). **Bold = best in column** (calibration: closest to 1; coverage: closest to 80%).
A "drought year" is a state-year whose actual statewide drought payout is >= 3% of insured dollars; all others are "quiet".
Percent errors on statewide totals are huge in quiet years (a tiny actual total makes any miss a big percentage), so read them next to the dollar columns.

How the 80% ranges are built. A and B: whole past years' residuals (walk-forward 2006-2012, out-of-sample) are resampled one year at a
time, the same year's residual applied to every county together (droughts hit counties together; never row by row), and the 10th-90th
percentile of the resulting statewide totals is taken (own year left out). C: 10th-90th percentile of the liability-weighted shares of its
k nearest look-alikes, every county at the same quantile. B0 and B1 have no range.

Tuned on walk-forward only (criterion: pooled county-year dollar WAPE of T1): `{"B": {"max_iter": 200, "max_depth": 4}, "C": {"k": 10, "drought_weight": 1.0}}`.

## A. Summary (T1 payout share, all state-years)

**Walk-forward (2006-2012)**, 14 state-years

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 7,645% | $3,157,692 | 28.9% | 0.553 | 0.50 | – |
| B1 drought-map rule | 3,951% | $2,206,885 | 30.5% | 0.688 | 0.53 | – |
| A hurdle | **523%** | $2,156,648 | 47.1% | 0.808 | 1.64 | 43% (6/14) |
| B boosting | 776% | **$1,407,913** | **49.7%** | **0.815** | 0.85 | 36% (5/14) |
| C look-alikes | 1,334% | $1,680,927 | 43.4% | 0.737 | **0.88** | **86% (12/14)** |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

**Validation (2013-2015)**, 6 state-years

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 2,085% | $3,413,176 | 20.9% | 0.550 | 1.61 | – |
| B1 drought-map rule | 448% | $3,475,465 | 25.0% | 0.612 | 1.39 | – |
| A hurdle | **95%** | $1,960,595 | **38.1%** | 0.722 | 0.41 | **67% (4/6)** |
| B boosting | 141% | **$1,830,438** | 30.0% | **0.724** | 0.54 | 33% (2/6) |
| C look-alikes | 419% | $2,112,146 | 32.8% | 0.658 | **0.74** | 67% (4/6) |
| *Random counties (reference)* | – | – | *21.3%* | – | – | – |

**Pooled walk-forward + validation (basis for the verdict)**, 20 state-years

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 5,977% | $3,234,706 | 26.5% | 0.566 | 0.79 | – |
| B1 drought-map rule | 2,900% | $2,589,289 | 28.9% | 0.653 | 0.75 | – |
| A hurdle | **395%** | $2,097,549 | **44.4%** | 0.780 | 1.32 | 50% (10/20) |
| B boosting | 586% | **$1,535,280** | 43.8% | **0.788** | 0.77 | 35% (7/20) |
| C look-alikes | 1,060% | $1,810,915 | 40.2% | 0.711 | **0.85** | **80% (16/20)** |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

## B. Drought years vs quiet years (T1)

**Walk-forward (2006-2012): drought years** (2 state-years: IA 2012, NE 2012)

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 92% | $14,991,991 | 28.9% | 0.350 | 0.07 | – |
| B1 drought-map rule | 65% | $11,947,662 | 29.3% | 0.350 | 0.34 | – |
| A hurdle | 48% | $11,627,530 | **42.9%** | 0.514 | 1.54 | 50% (1/2) |
| B boosting | 25% | **$7,772,245** | 39.2% | **0.716** | 0.78 | 0% (0/2) |
| C look-alikes | **20%** | $9,180,109 | 30.8% | 0.599 | **0.79** | **100% (2/2)** |
| *Random counties (reference)* | – | – | *21.3%* | – | – | – |

**Walk-forward (2006-2012): quiet years** (12 state-years: all other state-years)

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 8,903% | $1,169,445 | 28.9% | 0.626 | 5.06 | – |
| B1 drought-map rule | 4,599% | $570,364 | 30.7% | 0.622 | 2.63 | – |
| A hurdle | **603%** | $565,472 | 47.8% | 0.770 | 2.63 | 42% (5/12) |
| B boosting | 902% | **$338,659** | **51.5%** | **0.775** | **1.58** | 42% (5/12) |
| C look-alikes | 1,553% | $421,011 | 45.5% | 0.680 | 1.93 | **83% (10/12)** |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

**Validation (2013-2015): drought years** (1 state-year: IA 2013)

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | **54%** | **$5,961,505** | 35.8% | – | **0.46** | – |
| B1 drought-map rule | 61% | $7,882,012 | 35.3% | – | 0.39 | – |
| A hurdle | 80% | $7,754,820 | 34.8% | – | 0.20 | **0% (0/1)** |
| B boosting | 67% | $6,944,152 | 36.0% | – | 0.33 | 0% (0/1) |
| C look-alikes | 58% | $6,303,476 | **42.4%** | – | 0.42 | 0% (0/1) |
| *Random counties (reference)* | – | – | *20.2%* | – | – | – |

**Validation (2013-2015): quiet years** (5 state-years: all other state-years)

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 2,491% | $2,870,628 | 18.0% | 0.590 | 5.18 | – |
| B1 drought-map rule | 525% | $2,537,297 | 22.9% | 0.583 | 4.49 | – |
| A hurdle | **97%** | **$726,986** | **38.8%** | **0.677** | **1.06** | **80% (4/5)** |
| B boosting | 156% | $741,712 | 28.8% | 0.666 | 1.18 | 40% (2/5) |
| C look-alikes | 491% | $1,219,798 | 30.9% | 0.628 | 1.73 | 80% (4/5) |
| *Random counties (reference)* | – | – | *21.6%* | – | – | – |

Where a group holds only one or two state-years (validation drought years), treat the figures as anecdotes: range coverage there is 0 or 1 out of 1.

## C. Statewide drought payout per state-year ($M): actual, each model's prediction, and the 80% range
Cell = prediction [low–high of the 80% range] ✓ if the actual falls inside the range, ✗ if outside. Ranges for A, B, C only. T1 payout in $M.

**Walk-forward (2006-2012)**

| state | year | class | actual $M | B0 average | B1 drought-map rule | A hurdle (pred [80% range]) | B boosting (pred [80% range]) | C look-alikes (pred [80% range]) |
|---|---|---|---|---|---|---|---|---|
| IA | 2006 | quiet | 48.0 | 76.2 | 87.9 | 214.1 [165.0–216.1] ✗ | 133.6 [129.2–203.8] ✗ | 97.3 [12.0–226.9] ✓ |
| IA | 2007 | quiet | 34.5 | 103.4 | 71.0 | 33.6 [22.7–98.1] ✓ | 39.4 [29.2–189.1] ✓ | 43.7 [6.9–100.5] ✓ |
| IA | 2008 | quiet | 24.2 | 143.7 | 89.1 | 10.4 [4.5–110.1] ✓ | 11.5 [5.4–231.4] ✓ | 45.9 [0.1–180.8] ✓ |
| IA | 2009 | quiet | 1.5 | 90.9 | 54.6 | 11.9 [11.8–93.9] ✗ | 5.0 [6.7–187.3] ✗ | 29.5 [0.1–93.6] ✓ |
| IA | 2010 | quiet | 0.1 | 81.1 | 47.8 | 3.5 [7.3–93.4] ✗ | 8.5 [9.8–194.1] ✗ | 14.4 [0.7–37.8] ✗ |
| IA | 2011 | quiet | 64.7 | 110.5 | 62.7 | 81.9 [50.4–199.4] ✓ | 34.2 [24.7–327.2] ✓ | 41.7 [5.0–108.3] ✓ |
| IA | 2012 | drought | 1,837.7 | 102.4 | 518.3 | 3,265.0 [3,024.7–3,274.3] ✗ | 1,606.5 [1,490.6–1,630.1] ✗ | 1,345.1 [324.2–2,500.8] ✓ |
| NE | 2006 | quiet | 64.5 | 108.1 | 146.1 | 249.0 [219.6–247.6] ✗ | 122.0 [111.7–200.4] ✗ | 154.9 [32.6–320.1] ✓ |
| NE | 2007 | quiet | 10.3 | 167.1 | 52.3 | 31.5 [13.4–87.7] ✗ | 26.3 [15.0–152.6] ✗ | 39.0 [6.8–83.2] ✓ |
| NE | 2008 | quiet | 27.9 | 187.3 | 47.8 | 33.4 [15.7–106.5] ✓ | 12.8 [4.8–208.2] ✓ | 26.0 [1.0–89.1] ✓ |
| NE | 2009 | quiet | 2.1 | 120.0 | 30.8 | 30.2 [11.9–99.2] ✗ | 22.1 [13.0–174.1] ✗ | 24.3 [3.7–63.5] ✗ |
| NE | 2010 | quiet | 0.9 | 105.5 | 25.6 | 3.5 [0.0–81.4] ✓ | 6.3 [0.7–169.7] ✓ | 9.8 [0.4–31.9] ✓ |
| NE | 2011 | quiet | 6.0 | 147.0 | 33.1 | 46.8 [20.5–160.4] ✗ | 28.6 [11.4–286.2] ✗ | 22.5 [1.2–62.0] ✓ |
| NE | 2012 | drought | 1,201.0 | 121.6 | 499.9 | 1,427.4 [1,151.0–1,419.4] ✓ | 752.6 [659.7–757.4] ✗ | 1,041.2 [330.2–2,127.2] ✓ |

**Validation (2013-2015)**

| state | year | class | actual $M | B0 average | B1 drought-map rule | A hurdle (pred [80% range]) | B boosting (pred [80% range]) | C look-alikes (pred [80% range]) |
|---|---|---|---|---|---|---|---|---|
| IA | 2013 | drought | 868.3 | 402.9 | 339.6 | 171.5 [119.2–253.6] ✗ | 290.0 [223.7–523.8] ✗ | 367.7 [97.9–696.1] ✗ |
| IA | 2014 | quiet | 79.6 | 343.1 | 136.5 | 12.9 [7.3–118.8] ✓ | 16.5 [9.9–239.2] ✓ | 28.5 [1.3–83.7] ✓ |
| IA | 2015 | quiet | 3.8 | 307.1 | 53.2 | 15.5 [9.0–109.7] ✗ | 20.1 [14.0–219.9] ✗ | 79.2 [9.5–219.0] ✗ |
| NE | 2013 | quiet | 166.2 | 303.4 | 887.4 | 230.9 [131.5–300.0] ✓ | 232.7 [171.5–453.3] ✗ | 300.0 [77.2–662.3] ✓ |
| NE | 2014 | quiet | 20.7 | 254.4 | 150.1 | 25.0 [9.4–113.3] ✓ | 40.1 [22.7–234.7] ✗ | 54.2 [7.8–135.9] ✓ |
| NE | 2015 | quiet | 7.9 | 233.9 | 22.4 | 10.4 [1.4–98.0] ✓ | 18.3 [6.9–201.2] ✓ | 19.5 [0.7–64.3] ✓ |

## D. Both targets

T1 (payout share) is table A. T2 (damaged-acre share) uses the same layout; amounts are acres. Out-of-pocket and relief calibration (which use T2) are in the appendix.

**T2 damaged-acre share: Walk-forward (2006-2012)**, all state-years

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 4,064% | 15,960 | 34.3% | 0.556 | 0.79 | – |
| B1 drought-map rule | 2,364% | 11,164 | 35.0% | 0.683 | 0.79 | – |
| A hurdle | **408%** | 11,205 | 46.7% | 0.810 | 1.76 | 50% (7/14) |
| B boosting | 447% | **6,709** | **50.4%** | **0.819** | 1.07 | 36% (5/14) |
| C look-alikes | 876% | 8,433 | 43.8% | 0.742 | **0.95** | **86% (12/14)** |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

**T2 damaged-acre share: Validation (2013-2015)**, all state-years

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 969% | 18,249 | 17.1% | 0.505 | 1.21 | – |
| B1 drought-map rule | 261% | 17,024 | 22.3% | 0.606 | **0.92** | – |
| A hurdle | **62%** | 12,208 | **34.5%** | 0.722 | 0.34 | **67% (4/6)** |
| B boosting | 90% | **11,226** | 27.7% | **0.736** | 0.50 | 67% (4/6) |
| C look-alikes | 259% | 12,632 | 32.1% | 0.669 | 0.66 | 50% (3/6) |
| *Random counties (reference)* | – | – | *21.3%* | – | – | – |

**T2 damaged-acre share: Pooled walk-forward + validation (basis for the verdict)**, all state-years

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 3,135% | 16,650 | 29.1% | 0.571 | **0.93** | – |
| B1 drought-map rule | 1,733% | 12,931 | 31.2% | 0.656 | 0.83 | – |
| A hurdle | **305%** | 11,508 | 43.0% | 0.781 | 1.30 | 55% (11/20) |
| B boosting | 340% | **8,071** | **43.6%** | **0.794** | 0.88 | 45% (9/20) |
| C look-alikes | 691% | 9,699 | 40.3% | 0.717 | 0.85 | **75% (15/20)** |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

**T2: Walk-forward (2006-2012): drought years**

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 90% | 60,472 | 31.7% | 0.105 | 0.09 | – |
| B1 drought-map rule | 60% | 46,068 | 32.3% | 0.105 | 0.38 | – |
| A hurdle | 41% | 38,935 | **40.6%** | 0.466 | 1.46 | 50% (1/2) |
| B boosting | **11%** | **25,234** | 38.9% | 0.741 | **0.91** | 0% (0/2) |
| C look-alikes | 29% | 32,398 | 37.4% | **0.787** | 0.68 | **100% (2/2)** |
| *Random counties (reference)* | – | – | *21.3%* | – | – | – |

**T2: Walk-forward (2006-2012): quiet years**

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 4,726% | 8,482 | 34.7% | 0.636 | 3.86 | – |
| B1 drought-map rule | 2,748% | 5,300 | 35.5% | 0.617 | 2.58 | – |
| A hurdle | **470%** | 6,547 | 47.7% | 0.772 | 3.09 | 50% (6/12) |
| B boosting | 520% | **3,597** | **52.4%** | **0.781** | **1.76** | 42% (5/12) |
| C look-alikes | 1,017% | 4,407 | 44.8% | 0.687 | 2.10 | **83% (10/12)** |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

**T2: Validation (2013-2015): drought years**

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 67% | **39,524** | 32.7% | – | 0.33 | – |
| B1 drought-map rule | 72% | 48,738 | 27.6% | – | 0.28 | – |
| A hurdle | 83% | 48,583 | 26.0% | – | 0.17 | **0% (0/1)** |
| B boosting | 70% | 42,751 | 31.2% | – | 0.30 | 0% (0/1) |
| C look-alikes | **62%** | 39,622 | **35.0%** | – | **0.38** | 0% (0/1) |
| *Random counties (reference)* | – | – | *20.2%* | – | – | – |

**T2: Validation (2013-2015): quiet years**

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 1,149% | 13,720 | 14.0% | 0.504 | 3.83 | – |
| B1 drought-map rule | 298% | 10,272 | 21.2% | 0.575 | 2.84 | – |
| A hurdle | **58%** | **4,464** | **36.2%** | 0.677 | 0.88 | **80% (4/5)** |
| B boosting | 94% | 4,514 | 27.0% | **0.679** | **1.08** | 80% (4/5) |
| C look-alikes | 298% | 6,886 | 31.5% | 0.638 | 1.50 | 60% (3/5) |
| *Random counties (reference)* | – | – | *21.6%* | – | – | – |

## E. Known misses

State-years where **every** model's statewide T1 total was off by more than 50% (walk-forward + validation):

| state | year | actual $M | direction | B0 average $M | B1 drought-map rule $M | A hurdle $M | B boosting $M | C look-alikes $M | likely reason |
|---|---|---|---|---|---|---|---|---|---|
| IA | 2006 | 47.998 | over | 76.170 | 87.855 | 214.080 | 133.604 | 97.290 | Quiet year: actual payout only 1.07% of insured $ ($48.0M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| IA | 2008 | 24.158 | mixed | 143.723 | 89.127 | 10.398 | 11.510 | 45.947 | Models disagree in sign; payout depends on local conditions the Aug-15 inputs only weakly capture. |
| IA | 2009 | 1.542 | over | 90.937 | 54.643 | 11.896 | 4.955 | 29.521 | Quiet year: actual payout only 0.02% of insured $ ($1.5M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| IA | 2010 | 0.103 | over | 81.140 | 47.752 | 3.547 | 8.471 | 14.395 | Quiet year: actual payout only 0.00% of insured $ ($0.1M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| IA | 2013 | 868.315 | under | 402.851 | 339.567 | 171.486 | 290.033 | 367.683 | Drought began after the Aug 15 decision date, so no Aug-15 input could show it (Iowa mean D2+ area was 0% on every weekly map from May 28 through Aug 13, then 21% on Aug 27, 32% on Sep 3 and 42% on Sep 10). Known limitation: not tuned for. |
| IA | 2014 | 79.575 | mixed | 343.083 | 136.524 | 12.944 | 16.537 | 28.468 | Models disagree in sign; payout depends on local conditions the Aug-15 inputs only weakly capture. |
| IA | 2015 | 3.763 | over | 307.092 | 53.201 | 15.543 | 20.084 | 79.202 | Quiet year: actual payout only 0.03% of insured $ ($3.8M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2006 | 64.488 | over | 108.112 | 146.101 | 249.026 | 122.037 | 154.871 | Quiet year: actual payout only 2.45% of insured $ ($64.5M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2007 | 10.262 | over | 167.072 | 52.260 | 31.522 | 26.254 | 39.039 | Quiet year: actual payout only 0.24% of insured $ ($10.3M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2009 | 2.149 | over | 120.006 | 30.842 | 30.239 | 22.134 | 24.276 | Quiet year: actual payout only 0.04% of insured $ ($2.1M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2010 | 0.885 | over | 105.505 | 25.647 | 3.509 | 6.250 | 9.835 | Quiet year: actual payout only 0.02% of insured $ ($0.9M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2011 | 5.989 | over | 147.038 | 33.142 | 46.778 | 28.598 | 22.535 | Quiet year: actual payout only 0.08% of insured $ ($6.0M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |

- **Iowa 2013 is a known limitation, not tuned for.** The 2013 drought started after the Aug 15 decision date. Statewide D2+ area (weekly
  Drought Monitor in `data/processed/drought`) was 0% on every weekly map from late May through Aug 13, then rose to 21% on Aug 27 and 42%
  on Sep 10; the model inputs end Aug 14. Note that April 2013 maps still carried leftover 2012 drought (46% mean D2+ area on Apr 2),
  which the Apr 1 - Aug 14 features include; it had cleared by late May. No feature, model or hyper-parameter was changed to catch 2013.
- **Expected miss in the final test: Iowa 2020 (derecho).** The Aug 10, 2020 derecho caused wind losses that are mostly coded to a cause
  other than drought, so drought-payout models cannot predict them. Final-test results for 2020 Iowa should be read with that in mind.

## F. Verdict

**B boosting wins.** Over the 20 pooled out-of-sample state-years (walk-forward 2006-2012 + validation 2013-2015) it puts 43.8% of actual drought payouts in its top-20 counties (B1: 28.9%, random: 21.5%) and its county-level dollar error (WAPE) is 0.64 versus 1.08 for B1, 41% lower. Against B1 (the drought-map rule) this is **a clear win**: capture is +15.0 points and dollar error 41% lower, judged against noise bands of 2 capture points and 5% of WAPE. Applying the plan's rule (take the simpler model when two are within noise): no simpler model is within noise of B on both measures (A: capture 44.4%, WAPE 0.88; C: capture 40.2%, WAPE 0.76), so B is chosen. Caveats: only 3 of the 20 state-years are drought years (Iowa and Nebraska 2012, Iowa 2013), where B boosting under-budgets (Σpred/Σactual 0.68), and on validation alone (2013-2015) it has capture 30.0% vs 25.0% for B1 and WAPE 0.90 vs 1.71, with its one drought state-year (Iowa 2013) beginning after Aug 15 and invisible to every model. Budget ranges are rough: pooled 80%-range coverage is A 50%, B 35%, C 80% (target ~80%), so C is used in budget.py and labelled rough.

## Appendix

### Full T1 metric detail, pooled walk-forward + validation (includes out-of-pocket / relief calibration)

**All state-years**

| model | state-yrs | Σpred/Σactual | state total err (x actual) | top-20 capture | county MAE $M | wape | AUC any payout | acres calib | out-of-pocket calib | relief calib | 80% range cov |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 average | 20 | 0.785 | 59.766 | 0.265 | 3.235 | 1.354 | 0.566 | 0.925 | 0.766 | 0.776 | – |
| B1 drought-map rule | 20 | 0.751 | 29.004 | 0.289 | 2.589 | 1.084 | 0.653 | 0.831 | 0.739 | 0.752 | – |
| A hurdle | 20 | 1.322 | 3.948 | 0.444 | 2.098 | 0.878 | 0.780 | 1.303 | 1.136 | 1.153 | 0.500 |
| B boosting | 20 | 0.767 | 5.857 | 0.438 | 1.535 | 0.643 | 0.788 | 0.881 | 0.842 | 0.853 | 0.350 |
| C look-alikes | 20 | 0.847 | 10.597 | 0.402 | 1.811 | 0.758 | 0.711 | 0.853 | 0.765 | 0.778 | 0.800 |
| Random counties | 20 | – | – | 0.215 | – | – | – | – | – | – | – |
| Oracle (perfect ranking) | 20 | – | – | 0.778 | – | – | – | – | – | – | – |

**Drought years (statewide payout >= 3% of insured $)**

| model | state-yrs | Σpred/Σactual | state total err (x actual) | top-20 capture | county MAE $M | wape | AUC any payout | acres calib | out-of-pocket calib | relief calib | 80% range cov |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 average | 3 | 0.160 | 0.793 | 0.312 | 11.877 | 0.872 | 0.579 | 0.166 | 0.158 | 0.156 | – |
| B1 drought-map rule | 3 | 0.348 | 0.637 | 0.313 | 10.545 | 0.775 | 0.234 | 0.349 | 0.353 | 0.357 | – |
| A hurdle | 3 | 1.245 | 0.589 | 0.402 | 10.292 | 0.756 | 0.352 | 1.064 | 1.027 | 1.040 | 0.333 |
| B boosting | 3 | 0.678 | 0.388 | 0.381 | 7.487 | 0.550 | 0.615 | 0.721 | 0.752 | 0.761 | 0.000 |
| C look-alikes | 3 | 0.705 | 0.326 | 0.347 | 8.188 | 0.601 | 0.452 | 0.591 | 0.594 | 0.602 | 0.667 |
| Random counties | 3 | – | – | 0.210 | – | – | – | – | – | – | – |
| Oracle (perfect ranking) | 3 | – | – | 0.527 | – | – | – | – | – | – | – |

**Quiet years**

| model | state-yrs | Σpred/Σactual | state total err (x actual) | top-20 capture | county MAE $M | wape | AUC any payout | acres calib | out-of-pocket calib | relief calib | 80% range cov |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 average | 17 | 5.121 | 70.173 | 0.257 | 1.669 | 4.696 | 0.620 | 3.847 | 3.847 | 3.849 | – |
| B1 drought-map rule | 17 | 3.550 | 34.010 | 0.284 | 1.148 | 3.229 | 0.605 | 2.683 | 2.692 | 2.712 | – |
| A hurdle | 17 | 1.856 | 4.541 | 0.451 | 0.613 | 1.724 | 0.741 | 2.223 | 1.691 | 1.715 | 0.529 |
| B boosting | 17 | 1.382 | 6.822 | 0.448 | 0.457 | 1.286 | 0.742 | 1.495 | 1.295 | 1.312 | 0.412 |
| C look-alikes | 17 | 1.831 | 12.409 | 0.412 | 0.656 | 1.844 | 0.663 | 1.863 | 1.635 | 1.651 | 0.824 |
| Random counties | 17 | – | – | 0.215 | – | – | – | – | – | – | – |
| Oracle (perfect ranking) | 17 | – | – | 0.822 | – | – | – | – | – | – | – |

### Strategy A coefficients (standardised features, largest first)
`p_any_logit` = effect on the log-odds that drought costs anything; `log_share_if_cost` = effect on log(payout share) when it does. Note `yield_prev5_mean_missing` and `acres_planted_prev3_mean_missing` are only true for 2000-2002, so they can act as a weak year proxy in training.

| feature | p_any_logit | log_share_if_cost |
|---|---|---|
| tmax_jul_mean | 2.604 | 1.398 |
| yield_prev5_mean_missing | 1.405 | 1.057 |
| dsci_mean | 1.281 | 0.808 |
| heat32_days | -1.126 | -0.544 |
| precip_ratio_vs_normal | -1.051 | -0.685 |
| d2_weeks_50pct | -1.041 | -0.200 |
| d2_pct_last_map | 1.005 | 0.126 |
| irr_share_train_mean | -0.773 | -0.946 |
| d2_max_pct | 0.881 | 0.470 |
| acres_planted_prev3_mean_missing | 0.857 | -0.535 |
| gdd | -0.710 | -0.436 |
| droughty_pct | 0.032 | 0.624 |

### Strategy B permutation importance on validation (drop in weighted R²)
| feature | importance | std |
|---|---|---|
| precip_ratio_vs_normal | 0.164 | 0.030 |
| gdd | 0.124 | 0.038 |
| tmax_jul_mean | 0.098 | 0.023 |
| irr_share_train_mean | 0.058 | 0.019 |
| d2_pct_last_map | 0.049 | 0.004 |
| dsci_mean | 0.041 | 0.021 |
| d2_max_pct | 0.040 | 0.023 |
| heat32_days | 0.040 | 0.004 |
| d3_pct_last_map | 0.013 | 0.001 |
| d2_weeks_50pct | 0.010 | 0.004 |

Partial dependence curves: `results/gbm_partial_dependence_validation.csv`.

### Strategy C look-alikes for the three largest validation payouts
| county_name | state_alpha | crop | year | actual_$M | pred_$M | why |
|---|---|---|---|---|---|---|
| Carroll County | IA | CORN | 2013 | 40.190 | 1.509 | looks like Benton, IA 2003, Tama, IA 2003, Jasper, IA 2003 |
| Greene County | IA | CORN | 2013 | 34.416 | 1.167 | looks like Tama, IA 2003, Clinton, IA 2003, Jasper, IA 2003 |
| Webster County | IA | CORN | 2013 | 32.461 | 1.551 | looks like Clinton, IA 2003, Benton, IA 2003, Delaware, IA 2003 |

### Tuning grid (walk-forward WAPE, lower is better)
| model | max_iter | max_depth | wape | k | drought_weight |
|---|---|---|---|---|---|
| B | 200 | 4 | 0.554 | – | – |
| B | 400 | 3 | 0.560 | – | – |
| B | 400 | 4 | 0.562 | – | – |
| B | 200 | 3 | 0.594 | – | – |
| B | 100 | 4 | 0.602 | – | – |
| B | 100 | 3 | 0.665 | – | – |
| C | – | – | 0.661 | 10 | 1 |
| C | – | – | 0.672 | 25 | 1 |
| C | – | – | 0.689 | 25 | 2 |
| C | – | – | 0.691 | 10 | 2 |
| C | – | – | 0.694 | 25 | 3 |
| C | – | – | 0.698 | 10 | 3 |
| C | – | – | 0.705 | 50 | 1 |
| C | – | – | 0.719 | 50 | 3 |
| C | – | – | 0.726 | 50 | 2 |
