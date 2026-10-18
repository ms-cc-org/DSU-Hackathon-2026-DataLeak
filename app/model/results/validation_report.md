# Validation report: walk-forward 2006-2012 and validation 2013-2015 (calibrated)

Models are fitted on training years only (2000-2012 for validation; each fold's earlier years for walk-forward). **`testing/` was not
read.** Every model's predictions are multiplied by its calibration factor k (see "Calibration"); all tables below use the calibrated
predictions unless marked "before". Amounts are predicted drought payout = predicted T1 x insured liability (dollars), summed over crops per
county-year; T2 amounts are predicted damaged acres = T2 x insured acres. Rows used: 4734 training and 1101 validation
(insured, liability > 0, RMA year available; zero payouts kept). Raw numbers: `validation_results.csv` (all metrics, before and after
calibration), `validation_state_years.csv` (per state-year), `validation_predictions.csv` (every county x crop x year x model).

How to read the tables. *Statewide total error* = mean over state-years of |predicted - actual| / actual for the statewide total.
*Weighted MAE* = mean absolute error per county-year in dollars (acres for T2); in absolute dollars, so big counties weigh more.
*Budget capture* = share of actual drought payouts landing in the 20 counties with the highest predicted payout, averaged over state-years
(random = what picking 20 counties by chance gives). *Any-payout AUC* = ranking of rows with any payout above rows with none.
*Calibration* = Σ predicted / Σ actual (<1 under-budgets). *80% range coverage* = share of state-years whose actual statewide total
falls inside the 10th-90th percentile range (target ~80%; k/n shown). **Bold = best in column** (calibration: closest to 1; coverage: closest to 80%).
A "drought year" is a state-year whose actual statewide drought payout is >= 3% of insured dollars; all others are "quiet".
Percent errors on statewide totals are huge in quiet years (a tiny actual total makes any miss a big percentage), so read them next to the dollar columns.

How the 80% ranges are built. A and B: whole past years' residuals (walk-forward 2006-2012, out-of-sample, of the CALIBRATED predictions) are
resampled one year at a time, the same year's residual applied to every county together (droughts hit counties together; never row by row), and the
10th-90th percentile of the resulting statewide totals is taken (own year left out). C: 10th-90th percentile of the liability-weighted shares of its
k nearest look-alikes (scaled by C's calibration factor), every county at the same quantile. B0 and B1 have no range. The budget range is the best
of these (C), widened where needed so the chosen model's (A) calibrated point estimate lies inside it.

Tuned on walk-forward only (criterion: pooled county-year dollar WAPE of T1, before calibration): `{"B": {"max_iter": 200, "max_depth": 4}, "C": {"k": 10, "drought_weight": 1.0}}`.

## Calibration

Each model and target gets one multiplier k = Σ actual / Σ predicted, computed from that model's **walk-forward predictions (2006-2012) only**
(T2: damaged acres instead of dollars), saved in `results/calibration.csv` and applied in evaluation and in `budget.py`. k > 1 means the model
under-budgeted over 2006-2012 (dominated by the 2012 drought).

| Model | k for T1 (payout $) | k for T2 (damaged acres) |
|---|---|---|
| B0 average | 1.996 | 1.265 |
| B1 drought-map rule | 1.881 | 1.271 |
| A hurdle | 0.611 | 0.567 |
| B boosting | 1.183 | 0.938 |
| C look-alikes | 1.132 | 1.056 |

Budget capture and AUC are unchanged by a constant multiplier. Confirmed: the largest before/after difference over every split, target, group and
model is 0.00e+00 for capture and 1.11e-16 for AUC.

**Validation (2013-2015), before → after calibration, T1 payout share** (k from walk-forward, so this is out-of-sample):

| Model | Calibration (Σpred/Σactual) | WAPE | Budget capture | AUC | 80% range coverage |
|---|---|---|---|---|---|
| B0 average | 1.61 → 3.21 | 1.68 → 2.87 | 20.9% → 20.9% | 0.550 → 0.550 | – |
| B1 drought-map rule | 1.39 → 2.61 | 1.71 → 2.65 | 25.0% → 25.0% | 0.612 → 0.612 | – |
| A hurdle | 0.41 → 0.25 | 0.96 → 0.94 | 38.1% → 38.1% | 0.722 → 0.722 | 67% → 67% |
| B boosting | 0.54 → 0.64 | 0.90 → 0.92 | 30.0% → 30.0% | 0.724 → 0.724 | 33% → 33% |
| C look-alikes | 0.74 → 0.84 | 1.04 → 1.08 | 32.8% → 32.8% | 0.658 → 0.658 | 67% → 67% |

**Validation, before → after, T2 damaged-acre share:**

| Model | Calibration (Σpred/Σactual) | WAPE | Budget capture | AUC | 80% range coverage |
|---|---|---|---|---|---|
| B0 average | 1.21 → 1.53 | 1.40 → 1.58 | 17.1% → 17.1% | 0.505 → 0.505 | – |
| B1 drought-map rule | 0.92 → 1.17 | 1.30 → 1.47 | 22.3% → 22.3% | 0.606 → 0.606 | – |
| A hurdle | 0.34 → 0.20 | 0.93 → 0.92 | 34.5% → 34.5% | 0.722 → 0.722 | 67% → 83% |
| B boosting | 0.50 → 0.46 | 0.86 → 0.86 | 27.7% → 27.7% | 0.736 → 0.736 | 67% → 67% |
| C look-alikes | 0.66 → 0.70 | 0.97 → 0.98 | 32.1% → 32.1% | 0.669 → 0.669 | 50% → 50% |

Walk-forward "after" figures in the tables below are in-sample for k (k was fitted on those very predictions), so only the validation columns test
the calibration. In the budget range, the chosen model's point estimate fell inside the C range in 18 of 20 state-years
and the range was widened in the other 2; coverage of the widened budget range: walk-forward 12/14,
validation 4/6.

## A. Summary (T1 payout share, all state-years, calibrated)

**Walk-forward (2006-2012)**, 14 state-years

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 15,331% | $4,054,550 | 28.9% | 0.553 | **1.00** | – |
| B1 drought-map rule | 7,495% | $2,420,553 | 30.5% | 0.688 | 1.00 | – |
| A hurdle | **303%** | $1,467,811 | 47.1% | 0.808 | 1.00 | 36% (5/14) |
| B boosting | 924% | **$1,460,804** | **49.7%** | **0.815** | 1.00 | 43% (6/14) |
| C look-alikes | 1,517% | $1,752,218 | 43.4% | 0.737 | 1.00 | **86% (12/14)** |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

**Validation (2013-2015)**, 6 state-years

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 4,228% | $5,826,862 | 20.9% | 0.550 | 3.21 | – |
| B1 drought-map rule | 901% | $5,380,206 | 25.0% | 0.612 | 2.61 | – |
| A hurdle | **65%** | $1,911,492 | **38.1%** | 0.722 | 0.25 | **67% (4/6)** |
| B boosting | 173% | **$1,861,355** | 30.0% | **0.724** | 0.64 | 33% (2/6) |
| C look-alikes | 479% | $2,204,795 | 32.8% | 0.658 | **0.84** | 67% (4/6) |
| *Random counties (reference)* | – | – | *21.3%* | – | – | – |

**Pooled walk-forward + validation (basis for the verdict)**, 20 state-years

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 12,000% | $4,588,801 | 26.5% | 0.566 | 1.57 | – |
| B1 drought-map rule | 5,517% | $3,312,720 | 28.9% | 0.653 | 1.41 | – |
| A hurdle | **232%** | $1,601,555 | **44.4%** | 0.780 | 0.81 | 45% (9/20) |
| B boosting | 699% | **$1,581,547** | 43.8% | **0.788** | 0.91 | 40% (8/20) |
| C look-alikes | 1,206% | $1,888,644 | 40.2% | 0.711 | **0.96** | **80% (16/20)** |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

## B. Drought years vs quiet years (T1, calibrated)

**Walk-forward (2006-2012): drought years** (2 state-years: IA 2012, NE 2012)

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 84% | $13,967,614 | 28.9% | 0.350 | 0.15 | – |
| B1 drought-map rule | 34% | $10,344,764 | 29.3% | 0.350 | 0.63 | – |
| A hurdle | 18% | $8,096,100 | **42.9%** | 0.514 | **0.94** | 0% (0/2) |
| B boosting | 15% | **$7,829,050** | 39.2% | **0.716** | 0.92 | 50% (1/2) |
| C look-alikes | **9%** | $9,378,191 | 30.8% | 0.599 | 0.89 | **100% (2/2)** |
| *Random counties (reference)* | – | – | *21.3%* | – | – | – |

**Walk-forward (2006-2012): quiet years** (12 state-years: all other state-years)

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 17,872% | $2,389,085 | 28.9% | 0.626 | 10.10 | – |
| B1 drought-map rule | 8,738% | $1,089,228 | 30.7% | 0.622 | 4.95 | – |
| A hurdle | **350%** | **$354,211** | 47.8% | 0.770 | **1.61** | 42% (5/12) |
| B boosting | 1,076% | $390,893 | **51.5%** | **0.775** | 1.87 | 42% (5/12) |
| C look-alikes | 1,768% | $471,001 | 45.5% | 0.680 | 2.18 | **83% (10/12)** |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

**Validation (2013-2015): drought years** (1 state-year: IA 2013)

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | **7%** | **$5,929,928** | 35.8% | – | **0.93** | – |
| B1 drought-map rule | 26% | $8,377,526 | 35.3% | – | 0.74 | – |
| A hurdle | 88% | $7,970,940 | 34.8% | – | 0.12 | **0% (0/1)** |
| B boosting | 60% | $6,793,497 | 36.0% | – | 0.40 | 0% (0/1) |
| C look-alikes | 52% | $6,288,523 | **42.4%** | – | 0.48 | 0% (0/1) |
| *Random counties (reference)* | – | – | *20.2%* | – | – | – |

**Validation (2013-2015): quiet years** (5 state-years: all other state-years)

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 5,072% | $5,804,919 | 18.0% | 0.590 | 10.34 | – |
| B1 drought-map rule | 1,076% | $4,742,067 | 22.9% | 0.583 | 8.45 | – |
| A hurdle | **61%** | **$621,416** | **38.8%** | **0.677** | **0.65** | **80% (4/5)** |
| B boosting | 195% | $811,286 | 28.8% | 0.666 | 1.39 | 40% (2/5) |
| C look-alikes | 564% | $1,335,356 | 30.9% | 0.628 | 1.96 | 80% (4/5) |
| *Random counties (reference)* | – | – | *21.6%* | – | – | – |

Where a group holds only one or two state-years (validation drought years), treat the figures as anecdotes: range coverage there is 0 or 1 out of 1.

## C. Statewide drought payout per state-year ($M): actual, each calibrated model's prediction, and the 80% range
Cell = prediction [low–high of the 80% range] ✓ if the actual falls inside the range, ✗ if outside. Ranges for A, B, C use each model's own method; the last column is the budget range (C range widened to include A's point estimate). T1 payout in $M.

**Walk-forward (2006-2012)**

| state | year | class | actual $M | B0 average | B1 drought-map rule | A hurdle (pred [80% range]) | B boosting (pred [80% range]) | C look-alikes (pred [80% range]) | Budget range |
|---|---|---|---|---|---|---|---|---|---|
| IA | 2006 | quiet | 48.0 | 152.0 | 165.3 | 130.7 [128.6–178.4] ✗ | 158.1 [151.0–201.3] ✗ | 110.2 [13.6–256.9] ✓ | [13.6–256.9] ✓ |
| IA | 2007 | quiet | 34.5 | 206.5 | 133.5 | 20.5 [17.4–184.0] ✓ | 46.6 [30.2–160.6] ✓ | 49.5 [7.9–113.8] ✓ | [7.9–113.8] ✓ |
| IA | 2008 | quiet | 24.2 | 286.9 | 167.6 | 6.4 [3.1–230.9] ✓ | 13.6 [6.2–186.6] ✓ | 52.0 [0.1–204.7] ✓ | [0.1–204.7] ✓ |
| IA | 2009 | quiet | 1.5 | 181.5 | 102.8 | 7.3 [13.4–197.8] ✗ | 5.9 [5.4–149.5] ✗ | 33.4 [0.1–106.0] ✓ | [0.1–106.0] ✓ |
| IA | 2010 | quiet | 0.1 | 162.0 | 89.8 | 2.2 [9.4–199.5] ✗ | 10.0 [8.9–155.2] ✗ | 16.3 [0.8–42.8] ✗ | [0.8–42.8] ✗ |
| IA | 2011 | quiet | 64.7 | 220.6 | 117.9 | 50.0 [43.5–363.7] ✓ | 40.5 [27.3–265.1] ✓ | 47.2 [5.7–122.6] ✓ | [5.7–122.6] ✓ |
| IA | 2012 | drought | 1,837.7 | 204.3 | 974.8 | 1,993.9 [1,878.1–2,018.7] ✗ | 1,900.5 [1,745.7–1,919.6] ✓ | 1,522.9 [367.1–2,831.4] ✓ | [367.1–2,831.4] ✓ |
| NE | 2006 | quiet | 64.5 | 215.8 | 274.8 | 152.1 [143.8–206.6] ✗ | 144.4 [131.5–203.9] ✗ | 175.3 [36.9–362.4] ✓ | [36.9–362.4] ✓ |
| NE | 2007 | quiet | 10.3 | 333.5 | 98.3 | 19.3 [12.4–146.4] ✗ | 31.1 [17.5–135.0] ✗ | 44.2 [7.7–94.2] ✓ | [7.7–94.2] ✓ |
| NE | 2008 | quiet | 27.9 | 373.9 | 89.9 | 20.4 [13.0–190.1] ✓ | 15.2 [5.5–178.1] ✓ | 29.5 [1.1–100.9] ✓ | [1.1–100.9] ✓ |
| NE | 2009 | quiet | 2.1 | 239.6 | 58.0 | 18.5 [13.5–163.7] ✗ | 26.2 [14.4–154.0] ✗ | 27.5 [4.1–71.9] ✗ | [4.1–71.9] ✗ |
| NE | 2010 | quiet | 0.9 | 210.6 | 48.2 | 2.1 [0.2–156.2] ✓ | 7.4 [0.7–144.5] ✓ | 11.1 [0.4–36.1] ✓ | [0.4–36.1] ✓ |
| NE | 2011 | quiet | 6.0 | 293.5 | 62.3 | 28.6 [19.4–273.1] ✗ | 33.8 [11.9–249.7] ✗ | 25.5 [1.4–70.2] ✓ | [1.4–70.2] ✓ |
| NE | 2012 | drought | 1,201.0 | 242.7 | 940.2 | 871.7 [744.9–874.7] ✗ | 890.3 [761.6–892.6] ✗ | 1,178.8 [373.9–2,408.4] ✓ | [373.9–2,408.4] ✓ |

**Validation (2013-2015)**

| state | year | class | actual $M | B0 average | B1 drought-map rule | A hurdle (pred [80% range]) | B boosting (pred [80% range]) | C look-alikes (pred [80% range]) | Budget range |
|---|---|---|---|---|---|---|---|---|---|
| IA | 2013 | drought | 868.3 | 804.2 | 638.7 | 104.7 [91.6–368.0] ✗ | 343.1 [252.9–507.7] ✗ | 416.3 [110.9–788.2] ✗ | [104.7–788.2] ✗ |
| IA | 2014 | quiet | 79.6 | 684.9 | 256.8 | 7.9 [4.7–244.3] ✓ | 19.6 [11.5–194.3] ✓ | 32.2 [1.5–94.8] ✓ | [1.5–94.8] ✓ |
| IA | 2015 | quiet | 3.8 | 613.0 | 100.1 | 9.5 [5.8–224.2] ✗ | 23.8 [16.3–179.8] ✗ | 89.7 [10.8–247.9] ✗ | [9.5–247.9] ✗ |
| NE | 2013 | quiet | 166.2 | 605.5 | 1,669.2 | 141.0 [100.9–347.9] ✓ | 275.3 [193.3–451.7] ✗ | 339.7 [87.4–749.9] ✓ | [87.4–749.9] ✓ |
| NE | 2014 | quiet | 20.7 | 507.8 | 282.3 | 15.3 [6.3–192.8] ✓ | 47.5 [26.4–211.7] ✗ | 61.3 [8.8–153.8] ✓ | [8.8–153.8] ✓ |
| NE | 2015 | quiet | 7.9 | 466.9 | 42.1 | 6.3 [1.2–177.6] ✓ | 21.7 [7.8–178.1] ✓ | 22.1 [0.8–72.8] ✓ | [0.8–72.8] ✓ |

## D. Both targets (calibrated)

T1 (payout share) is table A. T2 (damaged-acre share) uses the same layout; amounts are acres. Out-of-pocket and relief calibration (which use T2) are in the appendix.

**T2 damaged-acre share: Walk-forward (2006-2012)**, all state-years

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 5,161% | 17,730 | 34.3% | 0.556 | **1.00** | – |
| B1 drought-map rule | 3,020% | 11,927 | 35.0% | 0.683 | 1.00 | – |
| A hurdle | **218%** | 7,043 | 46.7% | 0.810 | 1.00 | 43% (6/14) |
| B boosting | 418% | **6,616** | **50.4%** | **0.819** | 1.00 | 36% (5/14) |
| C look-alikes | 928% | 8,522 | 43.8% | 0.742 | 1.00 | **86% (12/14)** |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

**T2 damaged-acre share: Validation (2013-2015)**, all state-years

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 1,244% | 20,687 | 17.1% | 0.505 | 1.53 | – |
| B1 drought-map rule | 349% | 19,166 | 22.3% | 0.606 | **1.17** | – |
| A hurdle | **59%** | 12,090 | **34.5%** | 0.722 | 0.20 | **83% (5/6)** |
| B boosting | 82% | **11,221** | 27.7% | **0.736** | 0.46 | 67% (4/6) |
| C look-alikes | 275% | 12,777 | 32.1% | 0.669 | 0.70 | 50% (3/6) |
| *Random counties (reference)* | – | – | *21.3%* | – | – | – |

**T2 damaged-acre share: Pooled walk-forward + validation (basis for the verdict)**, all state-years

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 3,986% | 18,622 | 29.1% | 0.571 | 1.17 | – |
| B1 drought-map rule | 2,219% | 14,109 | 31.2% | 0.656 | **1.06** | – |
| A hurdle | **170%** | 8,564 | 43.0% | 0.781 | 0.74 | 55% (11/20) |
| B boosting | 318% | **8,004** | **43.6%** | **0.794** | 0.83 | 45% (9/20) |
| C look-alikes | 732% | 9,805 | 40.3% | 0.717 | 0.90 | **75% (15/20)** |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

**T2: Walk-forward (2006-2012): drought years**

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 87% | 58,935 | 31.7% | 0.105 | 0.12 | – |
| B1 drought-map rule | 49% | 42,484 | 32.3% | 0.105 | 0.48 | – |
| A hurdle | 20% | 27,261 | **40.6%** | 0.466 | 0.83 | 0% (0/2) |
| B boosting | **17%** | **25,735** | 38.9% | 0.741 | **0.85** | 0% (0/2) |
| C look-alikes | 25% | 31,611 | 37.4% | **0.787** | 0.72 | **100% (2/2)** |
| *Random counties (reference)* | – | – | *21.3%* | – | – | – |

**T2: Walk-forward (2006-2012): quiet years**

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 6,007% | 10,808 | 34.7% | 0.636 | 4.88 | – |
| B1 drought-map rule | 3,515% | 6,794 | 35.5% | 0.617 | 3.28 | – |
| A hurdle | **251%** | 3,646 | 47.7% | 0.772 | 1.75 | 50% (6/12) |
| B boosting | 485% | **3,404** | **52.4%** | **0.781** | **1.65** | 42% (5/12) |
| C look-alikes | 1,079% | 4,643 | 44.8% | 0.687 | 2.22 | **83% (10/12)** |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

**T2: Validation (2013-2015): drought years**

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | **58%** | **37,074** | 32.7% | – | **0.42** | – |
| B1 drought-map rule | 64% | 48,203 | 27.6% | – | 0.36 | – |
| A hurdle | 91% | 50,943 | 26.0% | – | 0.09 | **0% (0/1)** |
| B boosting | 72% | 43,288 | 31.2% | – | 0.28 | 0% (0/1) |
| C look-alikes | 60% | 39,198 | **35.0%** | – | 0.40 | 0% (0/1) |
| *Random counties (reference)* | – | – | *20.2%* | – | – | – |

**T2: Validation (2013-2015): quiet years**

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 1,481% | 17,198 | 14.0% | 0.504 | 4.85 | – |
| B1 drought-map rule | 406% | 12,984 | 21.2% | 0.575 | 3.61 | – |
| A hurdle | **53%** | **3,819** | **36.2%** | 0.677 | 0.50 | 100% (5/5) |
| B boosting | 84% | 4,393 | 27.0% | **0.679** | **1.01** | **80% (4/5)** |
| C look-alikes | 318% | 7,152 | 31.5% | 0.638 | 1.58 | 60% (3/5) |
| *Random counties (reference)* | – | – | *21.6%* | – | – | – |

## E. Known misses

State-years where **every** calibrated model's statewide T1 total was off by more than 50% (walk-forward + validation):

| state | year | actual $M | direction | B0 average $M | B1 drought-map rule $M | A hurdle $M | B boosting $M | C look-alikes $M | likely reason |
|---|---|---|---|---|---|---|---|---|---|
| IA | 2006 | 47.998 | over | 152.049 | 165.250 | 130.736 | 158.056 | 110.153 | Quiet year: actual payout only 1.07% of insured $ ($48.0M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| IA | 2009 | 1.542 | over | 181.527 | 102.780 | 7.265 | 5.862 | 33.424 | Quiet year: actual payout only 0.02% of insured $ ($1.5M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| IA | 2010 | 0.103 | over | 161.971 | 89.819 | 2.166 | 10.021 | 16.299 | Quiet year: actual payout only 0.00% of insured $ ($0.1M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| IA | 2014 | 79.575 | mixed | 684.855 | 256.794 | 7.905 | 19.563 | 32.232 | Models disagree in sign; payout depends on local conditions the Aug-15 inputs only weakly capture. |
| IA | 2015 | 3.763 | over | 613.012 | 100.068 | 9.492 | 23.760 | 89.673 | Quiet year: actual payout only 0.03% of insured $ ($3.8M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2006 | 64.488 | over | 215.811 | 274.809 | 152.077 | 144.371 | 175.348 | Quiet year: actual payout only 2.45% of insured $ ($64.5M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2007 | 10.262 | over | 333.506 | 98.299 | 19.250 | 31.059 | 44.201 | Quiet year: actual payout only 0.24% of insured $ ($10.3M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2009 | 2.149 | over | 239.554 | 58.013 | 18.467 | 26.185 | 27.486 | Quiet year: actual payout only 0.04% of insured $ ($2.1M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2010 | 0.885 | over | 210.607 | 48.240 | 2.143 | 7.394 | 11.135 | Quiet year: actual payout only 0.02% of insured $ ($0.9M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2011 | 5.989 | over | 293.514 | 62.338 | 28.567 | 33.832 | 25.514 | Quiet year: actual payout only 0.08% of insured $ ($6.0M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |

- **Iowa 2013 is a known limitation, not tuned for.** The 2013 drought started after the Aug 15 decision date. Statewide D2+ area (weekly
  Drought Monitor in `data/processed/drought`) was 0% on every weekly map from late May through Aug 13, then rose to 21% on Aug 27 and 42%
  on Sep 10; the model inputs end Aug 14. Note that April 2013 maps still carried leftover 2012 drought (46% mean D2+ area on Apr 2),
  which the Apr 1 - Aug 14 features include; it had cleared by late May. No feature, model or hyper-parameter was changed to catch 2013, and
  calibration (a constant per model) cannot fix it either.
- **Expected miss in the final test: Iowa 2020 (derecho).** The Aug 10, 2020 derecho caused wind losses that are mostly coded to a cause
  other than drought, so drought-payout models cannot predict them. Final-test results for 2020 Iowa should be read with that in mind.

## F. Verdict

**Calibration did not clearly help**: on validation (out-of-sample for k) Σpred/Σactual moved closer to 1 for B boosting, C look-alikes and further from 1 for B0 average, B1 drought-map rule, A hurdle; for B boosting it went 0.54 → 0.64 with dollar error (WAPE) 0.90 → 0.92, and for A hurdle 0.41 → 0.25 with WAPE 0.96 → 0.94; budget capture and AUC are unchanged (largest change 0.0e+00 and 1.1e-16). Under the plan's rule the pick is A hurdle: models A, B are within noise of the best on both capture (2 points) and WAPE (5%) once all models are calibrated, so the simplest of them wins; before calibration it was B boosting. Against B1 (also calibrated) A hurdle has pooled capture 44.4% vs 28.9% and WAPE 0.67 vs 1.39 (52% lower). What looks off: k is fitted on walk-forward predictions, so the pooled walk-forward 'after' figures are in-sample for k and only validation tests it; k comes from a window dominated by the 2012 drought, so it over-corrects quiet years: B0 average Σpred/Σactual 1.61 → 3.21, B1 drought-map rule Σpred/Σactual 1.39 → 2.61, A hurdle Σpred/Σactual 0.41 → 0.25 on validation; the pick moved from B boosting to A hurdle mainly because k_A rescales its 2012 over-prediction in-sample; on validation alone WAPE is 0.94 for A vs 0.92 for B; A hurdle still under-budgets on validation (0.25), mostly Iowa 2013, which no Aug-15 input can show; 2 of 20 state-years needed the C range widened to contain A's point estimate. Ranges stay rough: pooled 80%-range coverage after calibration is A 45%, B 40%, C 80% and 80% for the budget range (C, widened around A's point).

## G. Side check (report only; no model switched): boosting on payout dollars with liability as a feature
Same hyper-parameters as B, trained on drought payout in dollars (Poisson loss, `liability` added as a feature) instead of share x liability. Its k from
walk-forward is 2.068. The share version of B is the calibrated one used everywhere else.

| split | model | WAPE | budget capture | calibration | AUC | county MAE $M |
|---|---|---|---|---|---|---|
| walk-forward | B boosting: share target, calibrated | 0.574 | 0.497 | 1.000 | 0.815 | 1.461 |
| walk-forward | B$ ($ target, uncalibrated) | 0.707 | 0.512 | 0.483 | 0.746 | 1.797 |
| walk-forward | B$ ($ target, calibrated) | 0.697 | 0.512 | 1 | 0.746 | 1.771 |
| validation | B boosting: share target, calibrated | 0.916 | 0.300 | 0.637 | 0.724 | 1.861 |
| validation | B$ ($ target, uncalibrated) | 0.894 | 0.318 | 0.247 | 0.624 | 1.818 |
| validation | B$ ($ target, calibrated) | 0.905 | 0.318 | 0.511 | 0.624 | 1.840 |

## Appendix

### Full T1 metric detail, pooled walk-forward + validation, calibrated (includes out-of-pocket / relief calibration)

**All state-years**

| model | state-yrs | Σpred/Σactual | state total err (x actual) | top-20 capture | county MAE $M | wape | AUC any payout | acres calib | out-of-pocket calib | relief calib | 80% range cov |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 average | 20 | 1.567 | 120.000 | 0.265 | 4.589 | 1.921 | 0.566 | 1.171 | 0.969 | 0.982 | – |
| B1 drought-map rule | 20 | 1.412 | 55.165 | 0.289 | 3.313 | 1.387 | 0.653 | 1.056 | 0.939 | 0.956 | – |
| A hurdle | 20 | 0.807 | 2.316 | 0.444 | 1.602 | 0.670 | 0.780 | 0.739 | 0.645 | 0.654 | 0.450 |
| B boosting | 20 | 0.907 | 6.987 | 0.438 | 1.582 | 0.662 | 0.788 | 0.826 | 0.789 | 0.801 | 0.400 |
| C look-alikes | 20 | 0.959 | 12.057 | 0.402 | 1.889 | 0.791 | 0.711 | 0.901 | 0.808 | 0.822 | 0.800 |
| Random counties | 20 | – | – | 0.215 | – | – | – | – | – | – | – |
| Oracle (perfect ranking) | 20 | – | – | 0.778 | – | – | – | – | – | – | – |

**Drought years (statewide payout >= 3% of insured $)**

| model | state-yrs | Σpred/Σactual | state total err (x actual) | top-20 capture | county MAE $M | wape | AUC any payout | acres calib | out-of-pocket calib | relief calib | 80% range cov |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 average | 3 | 0.320 | 0.587 | 0.312 | 11.195 | 0.822 | 0.579 | 0.210 | 0.200 | 0.198 | – |
| B1 drought-map rule | 3 | 0.654 | 0.317 | 0.313 | 9.666 | 0.710 | 0.234 | 0.444 | 0.449 | 0.454 | – |
| A hurdle | 3 | 0.760 | 0.413 | 0.402 | 8.053 | 0.592 | 0.352 | 0.603 | 0.582 | 0.590 | 0.000 |
| B boosting | 3 | 0.802 | 0.299 | 0.381 | 7.472 | 0.549 | 0.615 | 0.676 | 0.705 | 0.714 | 0.333 |
| C look-alikes | 3 | 0.798 | 0.237 | 0.347 | 8.312 | 0.611 | 0.452 | 0.624 | 0.627 | 0.636 | 0.667 |
| Random counties | 3 | – | – | 0.210 | – | – | – | – | – | – | – |
| Oracle (perfect ranking) | 3 | – | – | 0.527 | – | – | – | – | – | – | – |

**Quiet years**

| model | state-yrs | Σpred/Σactual | state total err (x actual) | top-20 capture | county MAE $M | wape | AUC any payout | acres calib | out-of-pocket calib | relief calib | 80% range cov |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 average | 17 | 10.222 | 141.073 | 0.257 | 3.392 | 9.543 | 0.620 | 4.868 | 4.868 | 4.871 | – |
| B1 drought-map rule | 17 | 6.677 | 64.844 | 0.284 | 2.162 | 6.082 | 0.605 | 3.410 | 3.422 | 3.447 | – |
| A hurdle | 17 | 1.133 | 2.652 | 0.451 | 0.433 | 1.217 | 0.741 | 1.261 | 0.959 | 0.973 | 0.529 |
| B boosting | 17 | 1.635 | 8.168 | 0.448 | 0.514 | 1.447 | 0.742 | 1.403 | 1.215 | 1.231 | 0.412 |
| C look-alikes | 17 | 2.073 | 14.142 | 0.412 | 0.725 | 2.039 | 0.663 | 1.968 | 1.727 | 1.743 | 0.824 |
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

### Strategy C look-alikes for the three largest validation payouts (calibrated)
| county_name | state_alpha | crop | year | actual_$M | pred_$M | why |
|---|---|---|---|---|---|---|
| Carroll County | IA | CORN | 2013 | 40.190 | 1.709 | looks like Benton, IA 2003, Tama, IA 2003, Jasper, IA 2003 |
| Greene County | IA | CORN | 2013 | 34.416 | 1.322 | looks like Tama, IA 2003, Clinton, IA 2003, Jasper, IA 2003 |
| Webster County | IA | CORN | 2013 | 32.461 | 1.756 | looks like Clinton, IA 2003, Benton, IA 2003, Delaware, IA 2003 |

### Tuning grid (walk-forward WAPE before calibration, lower is better)
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
