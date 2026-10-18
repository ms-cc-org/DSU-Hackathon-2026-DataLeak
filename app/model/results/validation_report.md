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
of these (C), widened where needed so the headline model's (B) calibrated point estimate lies inside it.

Tuned on walk-forward only (criterion: pooled county-year dollar WAPE of T1, before calibration): `{"B": {"max_iter": 200, "max_depth": 4}, "C": {"k": 10, "drought_weight": 1.0}, "D": {"alpha": 0.01}}`.

## Calibration

Each model and target gets one multiplier k = Σ actual / Σ predicted, computed from that model's **walk-forward predictions (2006-2012) only**
(T2: damaged acres instead of dollars), saved in `results/calibration.csv` and applied in evaluation and in `budget.py`. k > 1 means the model
under-budgeted over 2006-2012 (dominated by the 2012 drought).

| Model | k for T1 (payout $) | k for T2 (damaged acres) |
|---|---|---|
| B0 average | 1.996 | 1.265 |
| B1 drought-map rule | 1.881 | 1.271 |
| B2 USDA ERP trigger rule | 3.386 | 3.072 |
| A hurdle | 0.611 | 0.567 |
| B boosting | 1.183 | 0.938 |
| C look-alikes | 1.132 | 1.056 |
| D Tweedie GLM | 1.246 | 0.904 |
| G TabPFN v2 | 1.416 | 1.139 |

Budget capture and AUC are unchanged by a constant multiplier. Confirmed: the largest before/after difference over every split, target, group and
model is 0.00e+00 for capture and 1.11e-16 for AUC.

**Validation (2013-2015), before → after calibration, T1 payout share** (k from walk-forward, so this is out-of-sample):

| Model | Calibration (Σpred/Σactual) | WAPE | Budget capture | AUC | 80% range coverage |
|---|---|---|---|---|---|
| B0 average | 1.61 → 3.21 | 1.68 → 2.87 | 20.9% → 20.9% | 0.550 → 0.550 | – |
| B1 drought-map rule | 1.39 → 2.61 | 1.71 → 2.65 | 25.0% → 25.0% | 0.612 → 0.612 | – |
| B2 USDA ERP trigger rule | 1.56 → 5.29 | 1.69 → 5.23 | 34.0% → 34.0% | 0.609 → 0.609 | – |
| A hurdle | 0.41 → 0.25 | 0.96 → 0.94 | 38.1% → 38.1% | 0.722 → 0.722 | 67% → 67% |
| B boosting | 0.54 → 0.64 | 0.90 → 0.92 | 30.0% → 30.0% | 0.724 → 0.724 | 33% → 33% |
| C look-alikes | 0.74 → 0.84 | 1.04 → 1.08 | 32.8% → 32.8% | 0.658 → 0.658 | 67% → 67% |
| D Tweedie GLM | 0.36 → 0.45 | 0.92 → 0.93 | 45.2% → 45.2% | 0.745 → 0.745 | 67% → 67% |
| G TabPFN v2 | 0.49 → 0.69 | 0.90 → 0.94 | 41.2% → 41.2% | 0.735 → 0.735 | 50% → 33% |

**Validation, before → after, T2 damaged-acre share:**

| Model | Calibration (Σpred/Σactual) | WAPE | Budget capture | AUC | 80% range coverage |
|---|---|---|---|---|---|
| B0 average | 1.21 → 1.53 | 1.40 → 1.58 | 17.1% → 17.1% | 0.505 → 0.505 | – |
| B1 drought-map rule | 0.92 → 1.17 | 1.30 → 1.47 | 22.3% → 22.3% | 0.606 → 0.606 | – |
| B2 USDA ERP trigger rule | 0.93 → 2.87 | 1.20 → 2.97 | 32.0% → 32.0% | 0.602 → 0.602 | – |
| A hurdle | 0.34 → 0.20 | 0.93 → 0.92 | 34.5% → 34.5% | 0.722 → 0.722 | 67% → 83% |
| B boosting | 0.50 → 0.46 | 0.86 → 0.86 | 27.7% → 27.7% | 0.736 → 0.736 | 67% → 67% |
| C look-alikes | 0.66 → 0.70 | 0.97 → 0.98 | 32.1% → 32.1% | 0.669 → 0.669 | 50% → 50% |
| D Tweedie GLM | 0.31 → 0.28 | 0.90 → 0.91 | 38.6% → 38.6% | 0.739 → 0.739 | 67% → 67% |
| G TabPFN v2 | 0.48 → 0.54 | 0.88 → 0.89 | 39.2% → 39.2% | 0.759 → 0.759 | 50% → 50% |

Walk-forward "after" figures in the tables below are in-sample for k (k was fitted on those very predictions), so only the validation columns test
the calibration. In the budget range, the chosen model's point estimate fell inside the C range in 20 of 20 state-years
and the range was widened in the other 0; coverage of the widened budget range: walk-forward 12/14,
validation 4/6.

## A. Summary (T1 payout share, all state-years, calibrated)

**Walk-forward (2006-2012)**, 14 state-years

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 15,331% | $4,054,550 | 28.9% | 0.553 | **1.00** | – |
| B1 drought-map rule | 7,495% | $2,420,553 | 30.5% | 0.688 | 1.00 | – |
| B2 USDA ERP trigger rule | **87%** | $1,987,313 | 23.6% | 0.589 | 1.00 | – |
| A hurdle | 303% | $1,467,811 | 47.1% | 0.808 | 1.00 | 36% (5/14) |
| B boosting | 924% | **$1,460,804** | 49.7% | **0.815** | 1.00 | 43% (6/14) |
| C look-alikes | 1,517% | $1,752,218 | 43.4% | 0.737 | 1.00 | **86% (12/14)** |
| D Tweedie GLM | 1,288% | $1,679,839 | **51.7%** | 0.775 | 1.00 | 36% (5/14) |
| G TabPFN v2 | 903% | $1,494,210 | 50.6% | 0.758 | 1.00 | 43% (6/14) |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

**Validation (2013-2015)**, 6 state-years

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 4,228% | $5,826,862 | 20.9% | 0.550 | 3.21 | – |
| B1 drought-map rule | 901% | $5,380,206 | 25.0% | 0.612 | 2.61 | – |
| B2 USDA ERP trigger rule | 720% | $10,622,656 | 34.0% | 0.609 | 5.29 | – |
| A hurdle | **65%** | $1,911,492 | 38.1% | 0.722 | 0.25 | **67% (4/6)** |
| B boosting | 173% | **$1,861,355** | 30.0% | 0.724 | 0.64 | 33% (2/6) |
| C look-alikes | 479% | $2,204,795 | 32.8% | 0.658 | **0.84** | 67% (4/6) |
| D Tweedie GLM | 223% | $1,897,582 | **45.2%** | **0.745** | 0.45 | 67% (4/6) |
| G TabPFN v2 | 179% | $1,912,247 | 41.2% | 0.735 | 0.69 | 33% (2/6) |
| *Random counties (reference)* | – | – | *21.3%* | – | – | – |

**Pooled walk-forward + validation (basis for the verdict)**, 20 state-years

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 12,000% | $4,588,801 | 26.5% | 0.566 | 1.57 | – |
| B1 drought-map rule | 5,517% | $3,312,720 | 28.9% | 0.653 | 1.41 | – |
| B2 USDA ERP trigger rule | 277% | $4,590,378 | 26.8% | 0.594 | 2.10 | – |
| A hurdle | **232%** | $1,601,555 | 44.4% | 0.780 | 0.81 | 45% (9/20) |
| B boosting | 699% | **$1,581,547** | 43.8% | **0.788** | 0.91 | 40% (8/20) |
| C look-alikes | 1,206% | $1,888,644 | 40.2% | 0.711 | **0.96** | **80% (16/20)** |
| D Tweedie GLM | 968% | $1,745,476 | **49.8%** | 0.762 | 0.86 | 45% (9/20) |
| G TabPFN v2 | 686% | $1,620,224 | 47.8% | 0.748 | 0.92 | 40% (8/20) |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

## B. Drought years vs quiet years (T1, calibrated)

**Walk-forward (2006-2012): drought years** (2 state-years: IA 2012, NE 2012)

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 84% | $13,967,614 | 28.9% | 0.350 | 0.15 | – |
| B1 drought-map rule | 34% | $10,344,764 | 29.3% | 0.350 | 0.63 | – |
| B2 USDA ERP trigger rule | 11% | $11,364,920 | 29.4% | 0.317 | **1.02** | – |
| A hurdle | 18% | $8,096,100 | 42.9% | 0.514 | 0.94 | 0% (0/2) |
| B boosting | 15% | **$7,829,050** | 39.2% | 0.716 | 0.92 | 50% (1/2) |
| C look-alikes | **9%** | $9,378,191 | 30.8% | 0.599 | 0.89 | **100% (2/2)** |
| D Tweedie GLM | 19% | $8,075,245 | 40.0% | 0.095 | 0.82 | 0% (0/2) |
| G TabPFN v2 | 25% | $7,872,093 | **44.9%** | **0.737** | 0.90 | 50% (1/2) |
| *Random counties (reference)* | – | – | *21.3%* | – | – | – |

**Walk-forward (2006-2012): quiet years** (12 state-years: all other state-years)

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 17,872% | $2,389,085 | 28.9% | 0.626 | 10.10 | – |
| B1 drought-map rule | 8,738% | $1,089,228 | 30.7% | 0.622 | 4.95 | – |
| B2 USDA ERP trigger rule | **100%** | $411,808 | 22.7% | 0.516 | **0.83** | – |
| A hurdle | 350% | **$354,211** | 47.8% | 0.770 | 1.61 | 42% (5/12) |
| B boosting | 1,076% | $390,893 | 51.5% | **0.775** | 1.87 | 42% (5/12) |
| C look-alikes | 1,768% | $471,001 | 45.5% | 0.680 | 2.18 | **83% (10/12)** |
| D Tweedie GLM | 1,500% | $605,365 | **53.7%** | 0.730 | 2.91 | 42% (5/12) |
| G TabPFN v2 | 1,050% | $422,680 | 51.6% | 0.706 | 2.11 | 42% (5/12) |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

**Validation (2013-2015): drought years** (1 state-year: IA 2013)

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | **7%** | **$5,929,928** | 35.8% | – | **0.93** | – |
| B1 drought-map rule | 26% | $8,377,526 | 35.3% | – | 0.74 | – |
| B2 USDA ERP trigger rule | 213% | $27,554,178 | 40.2% | – | 3.13 | – |
| A hurdle | 88% | $7,970,940 | 34.8% | – | 0.12 | **0% (0/1)** |
| B boosting | 60% | $6,793,497 | 36.0% | – | 0.40 | 0% (0/1) |
| C look-alikes | 52% | $6,288,523 | **42.4%** | – | 0.48 | 0% (0/1) |
| D Tweedie GLM | 75% | $7,187,429 | 40.7% | – | 0.25 | 0% (0/1) |
| G TabPFN v2 | 57% | $6,713,372 | 42.2% | – | 0.43 | 0% (0/1) |
| *Random counties (reference)* | – | – | *20.2%* | – | – | – |

**Validation (2013-2015): quiet years** (5 state-years: all other state-years)

| Model | Statewide total error (% off) | Weighted MAE ($ per county-year) | Budget capture (top-20 counties) | Any-payout AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 5,072% | $5,804,919 | 18.0% | 0.590 | 10.34 | – |
| B1 drought-map rule | 1,076% | $4,742,067 | 22.9% | 0.583 | 8.45 | – |
| B2 USDA ERP trigger rule | 822% | $7,017,880 | 32.8% | 0.604 | 12.00 | – |
| A hurdle | **61%** | **$621,416** | 38.8% | 0.677 | 0.65 | **80% (4/5)** |
| B boosting | 195% | $811,286 | 28.8% | 0.666 | 1.39 | 40% (2/5) |
| C look-alikes | 564% | $1,335,356 | 30.9% | 0.628 | 1.96 | 80% (4/5) |
| D Tweedie GLM | 252% | $771,357 | **46.1%** | **0.697** | **1.08** | 80% (4/5) |
| G TabPFN v2 | 203% | $890,072 | 41.0% | 0.690 | 1.50 | 40% (2/5) |
| *Random counties (reference)* | – | – | *21.6%* | – | – | – |

Where a group holds only one or two state-years (validation drought years), treat the figures as anecdotes: range coverage there is 0 or 1 out of 1.

## C. Statewide drought payout per state-year ($M): actual, each calibrated model's prediction, and the 80% range
Cell = prediction [low–high of the 80% range] ✓ if the actual falls inside the range, ✗ if outside. Ranges for A, B, C use each model's own method; the last column is the budget range (C range widened to include B's point estimate). T1 payout in $M.

**Walk-forward (2006-2012)**

| state | year | class | actual $M | B0 average | B1 drought-map rule | B2 USDA ERP trigger rule | A hurdle (pred [80% range]) | B boosting (pred [80% range]) | C look-alikes (pred [80% range]) | D Tweedie GLM (pred [80% range]) | G TabPFN v2 (pred [80% range]) | Budget range |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IA | 2006 | quiet | 48.0 | 152.0 | 165.3 | 0.0 | 130.7 [128.6–178.4] ✗ | 158.1 [151.0–201.3] ✗ | 110.2 [13.6–256.9] ✓ | 225.9 [199.9–275.5] ✗ | 182.6 [177.4–210.9] ✗ | [13.6–256.9] ✓ |
| IA | 2007 | quiet | 34.5 | 206.5 | 133.5 | 0.0 | 20.5 [17.4–184.0] ✓ | 46.6 [30.2–160.6] ✓ | 49.5 [7.9–113.8] ✓ | 55.9 [24.1–264.9] ✓ | 36.9 [23.0–135.9] ✓ | [7.9–113.8] ✓ |
| IA | 2008 | quiet | 24.2 | 286.9 | 167.6 | 0.0 | 6.4 [3.1–230.9] ✓ | 13.6 [6.2–186.6] ✓ | 52.0 [0.1–204.7] ✓ | 37.4 [12.8–324.4] ✓ | 10.8 [3.1–159.4] ✓ | [0.1–204.7] ✓ |
| IA | 2009 | quiet | 1.5 | 181.5 | 102.8 | 0.0 | 7.3 [13.4–197.8] ✗ | 5.9 [5.4–149.5] ✗ | 33.4 [0.1–106.0] ✓ | 59.6 [33.9–292.0] ✗ | 12.2 [8.2–135.4] ✗ | [0.1–106.0] ✓ |
| IA | 2010 | quiet | 0.1 | 162.0 | 89.8 | 0.0 | 2.2 [9.4–199.5] ✗ | 10.0 [8.9–155.2] ✗ | 16.3 [0.8–42.8] ✗ | 10.4 [5.8–274.8] ✗ | 9.5 [6.8–136.2] ✗ | [0.8–42.8] ✗ |
| IA | 2011 | quiet | 64.7 | 220.6 | 117.9 | 0.0 | 50.0 [43.5–363.7] ✓ | 40.5 [27.3–265.1] ✓ | 47.2 [5.7–122.6] ✓ | 97.5 [30.4–502.7] ✓ | 77.1 [41.8–268.2] ✓ | [5.7–122.6] ✓ |
| IA | 2012 | drought | 1,837.7 | 204.3 | 974.8 | 1,709.2 | 1,993.9 [1,878.1–2,018.7] ✗ | 1,900.5 [1,745.7–1,919.6] ✓ | 1,522.9 [367.1–2,831.4] ✓ | 1,595.7 [1,323.0–1,579.8] ✗ | 2,006.7 [1,826.9–2,014.0] ✓ | [367.1–2,831.4] ✓ |
| NE | 2006 | quiet | 64.5 | 215.8 | 274.8 | 190.9 | 152.1 [143.8–206.6] ✗ | 144.4 [131.5–203.9] ✗ | 175.3 [36.9–362.4] ✓ | 197.2 [178.9–244.5] ✗ | 135.5 [120.7–213.6] ✗ | [36.9–362.4] ✓ |
| NE | 2007 | quiet | 10.3 | 333.5 | 98.3 | 20.2 | 19.3 [12.4–146.4] ✗ | 31.1 [17.5–135.0] ✗ | 44.2 [7.7–94.2] ✓ | 26.9 [12.5–159.9] ✗ | 40.5 [22.8–166.3] ✗ | [7.7–94.2] ✓ |
| NE | 2008 | quiet | 27.9 | 373.9 | 89.9 | 25.0 | 20.4 [13.0–190.1] ✓ | 15.2 [5.5–178.1] ✓ | 29.5 [1.1–100.9] ✓ | 29.6 [10.4–205.8] ✓ | 27.3 [11.0–215.5] ✓ | [1.1–100.9] ✓ |
| NE | 2009 | quiet | 2.1 | 239.6 | 58.0 | 0.0 | 18.5 [13.5–163.7] ✗ | 26.2 [14.4–154.0] ✗ | 27.5 [4.1–71.9] ✗ | 45.2 [30.6–191.4] ✗ | 24.1 [11.5–176.5] ✗ | [4.1–71.9] ✗ |
| NE | 2010 | quiet | 0.9 | 210.6 | 48.2 | 0.0 | 2.1 [0.2–156.2] ✓ | 7.4 [0.7–144.5] ✓ | 11.1 [0.4–36.1] ✓ | 9.3 [0.4–169.8] ✓ | 5.1 [0.8–169.8] ✓ | [0.4–36.1] ✓ |
| NE | 2011 | quiet | 6.0 | 293.5 | 62.3 | 0.0 | 28.6 [19.4–273.1] ✗ | 33.8 [11.9–249.7] ✗ | 25.5 [1.4–70.2] ✓ | 33.2 [10.0–297.4] ✗ | 38.3 [15.9–301.8] ✗ | [1.4–70.2] ✓ |
| NE | 2012 | drought | 1,201.0 | 242.7 | 940.2 | 1,378.2 | 871.7 [744.9–874.7] ✗ | 890.3 [761.6–892.6] ✗ | 1,178.8 [373.9–2,408.4] ✓ | 899.6 [695.8–891.3] ✗ | 716.9 [581.4–712.8] ✗ | [373.9–2,408.4] ✓ |

**Validation (2013-2015)**

| state | year | class | actual $M | B0 average | B1 drought-map rule | B2 USDA ERP trigger rule | A hurdle (pred [80% range]) | B boosting (pred [80% range]) | C look-alikes (pred [80% range]) | D Tweedie GLM (pred [80% range]) | G TabPFN v2 (pred [80% range]) | Budget range |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IA | 2013 | drought | 868.3 | 804.2 | 638.7 | 2,722.0 | 104.7 [91.6–368.0] ✗ | 343.1 [252.9–507.7] ✗ | 416.3 [110.9–788.2] ✗ | 213.9 [115.1–540.4] ✗ | 372.4 [297.7–521.6] ✗ | [110.9–788.2] ✗ |
| IA | 2014 | quiet | 79.6 | 684.9 | 256.8 | 0.0 | 7.9 [4.7–244.3] ✓ | 19.6 [11.5–194.3] ✓ | 32.2 [1.5–94.8] ✓ | 47.6 [21.7–341.2] ✓ | 16.1 [8.8–166.1] ✓ | [1.5–94.8] ✓ |
| IA | 2015 | quiet | 3.8 | 613.0 | 100.1 | 0.0 | 9.5 [5.8–224.2] ✗ | 23.8 [16.3–179.8] ✗ | 89.7 [10.8–247.9] ✗ | 43.4 [19.1–309.7] ✗ | 26.3 [15.9–160.8] ✗ | [10.8–247.9] ✗ |
| NE | 2013 | quiet | 166.2 | 605.5 | 1,669.2 | 2,865.8 | 141.0 [100.9–347.9] ✓ | 275.3 [193.3–451.7] ✗ | 339.7 [87.4–749.9] ✓ | 162.1 [87.5–377.3] ✓ | 315.1 [227.2–530.2] ✗ | [87.4–749.9] ✓ |
| NE | 2014 | quiet | 20.7 | 507.8 | 282.3 | 473.9 | 15.3 [6.3–192.8] ✓ | 47.5 [26.4–211.7] ✗ | 61.3 [8.8–153.8] ✓ | 31.2 [10.7–215.6] ✓ | 41.1 [21.0–235.3] ✗ | [8.8–153.8] ✓ |
| NE | 2015 | quiet | 7.9 | 466.9 | 42.1 | 0.0 | 6.3 [1.2–177.6] ✓ | 21.7 [7.8–178.1] ✓ | 22.1 [0.8–72.8] ✓ | 16.9 [3.0–198.5] ✓ | 19.8 [6.4–203.5] ✓ | [0.8–72.8] ✓ |

## D. Both targets (calibrated)

T1 (payout share) is table A. T2 (damaged-acre share) uses the same layout; amounts are acres. Out-of-pocket and relief calibration (which use T2) are in the appendix.

**T2 damaged-acre share: Walk-forward (2006-2012)**, all state-years

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 5,161% | 17,730 | 34.3% | 0.556 | **1.00** | – |
| B1 drought-map rule | 3,020% | 11,927 | 35.0% | 0.683 | 1.00 | – |
| B2 USDA ERP trigger rule | **79%** | 8,800 | 23.7% | 0.588 | 1.00 | – |
| A hurdle | 218% | 7,043 | 46.7% | 0.810 | 1.00 | 43% (6/14) |
| B boosting | 418% | **6,616** | 50.4% | **0.819** | 1.00 | 36% (5/14) |
| C look-alikes | 928% | 8,522 | 43.8% | 0.742 | 1.00 | **86% (12/14)** |
| D Tweedie GLM | 599% | 8,560 | **51.0%** | 0.789 | 1.00 | 43% (6/14) |
| G TabPFN v2 | 457% | 6,757 | 50.0% | 0.760 | 1.00 | 36% (5/14) |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

**T2 damaged-acre share: Validation (2013-2015)**, all state-years

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 1,244% | 20,687 | 17.1% | 0.505 | 1.53 | – |
| B1 drought-map rule | 349% | 19,166 | 22.3% | 0.606 | **1.17** | – |
| B2 USDA ERP trigger rule | 364% | 38,862 | 32.0% | 0.602 | 2.87 | – |
| A hurdle | **59%** | 12,090 | 34.5% | 0.722 | 0.20 | **83% (5/6)** |
| B boosting | 82% | **11,221** | 27.7% | 0.736 | 0.46 | 67% (4/6) |
| C look-alikes | 275% | 12,777 | 32.1% | 0.669 | 0.70 | 50% (3/6) |
| D Tweedie GLM | 95% | 11,840 | 38.6% | 0.739 | 0.28 | 67% (4/6) |
| G TabPFN v2 | 105% | 11,600 | **39.2%** | **0.759** | 0.54 | 50% (3/6) |
| *Random counties (reference)* | – | – | *21.3%* | – | – | – |

**T2 damaged-acre share: Pooled walk-forward + validation (basis for the verdict)**, all state-years

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 3,986% | 18,622 | 29.1% | 0.571 | 1.17 | – |
| B1 drought-map rule | 2,219% | 14,109 | 31.2% | 0.656 | **1.06** | – |
| B2 USDA ERP trigger rule | **164%** | 17,862 | 26.2% | 0.594 | 1.61 | – |
| A hurdle | 170% | 8,564 | 43.0% | 0.781 | 0.74 | 55% (11/20) |
| B boosting | 318% | **8,004** | 43.6% | **0.794** | 0.83 | 45% (9/20) |
| C look-alikes | 732% | 9,805 | 40.3% | 0.717 | 0.90 | **75% (15/20)** |
| D Tweedie GLM | 448% | 9,549 | **47.3%** | 0.769 | 0.77 | 50% (10/20) |
| G TabPFN v2 | 351% | 8,217 | 46.8% | 0.756 | 0.85 | 40% (8/20) |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

**T2: Walk-forward (2006-2012): drought years**

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 87% | 58,935 | 31.7% | 0.105 | 0.12 | – |
| B1 drought-map rule | 49% | 42,484 | 32.3% | 0.105 | 0.48 | – |
| B2 USDA ERP trigger rule | **11%** | 39,014 | 32.6% | 0.094 | **1.07** | – |
| A hurdle | 20% | 27,261 | 40.6% | 0.466 | 0.83 | 0% (0/2) |
| B boosting | 17% | 25,735 | 38.9% | 0.741 | 0.85 | 0% (0/2) |
| C look-alikes | 25% | 31,611 | 37.4% | **0.787** | 0.72 | **100% (2/2)** |
| D Tweedie GLM | 33% | 30,345 | 40.1% | 0.180 | 0.67 | 0% (0/2) |
| G TabPFN v2 | 24% | **24,837** | **42.9%** | 0.729 | 0.80 | 0% (0/2) |
| *Random counties (reference)* | – | – | *21.3%* | – | – | – |

**T2: Walk-forward (2006-2012): quiet years**

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 6,007% | 10,808 | 34.7% | 0.636 | 4.88 | – |
| B1 drought-map rule | 3,515% | 6,794 | 35.5% | 0.617 | 3.28 | – |
| B2 USDA ERP trigger rule | **90%** | 3,724 | 22.3% | 0.516 | **0.70** | – |
| A hurdle | 251% | 3,646 | 47.7% | 0.772 | 1.75 | 50% (6/12) |
| B boosting | 485% | **3,404** | 52.4% | **0.781** | 1.65 | 42% (5/12) |
| C look-alikes | 1,079% | 4,643 | 44.8% | 0.687 | 2.22 | **83% (10/12)** |
| D Tweedie GLM | 693% | 4,900 | **52.9%** | 0.747 | 2.44 | 50% (6/12) |
| G TabPFN v2 | 529% | 3,719 | 51.2% | 0.709 | 1.89 | 42% (5/12) |
| *Random counties (reference)* | – | – | *21.5%* | – | – | – |

**T2: Validation (2013-2015): drought years**

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | **58%** | **37,074** | 32.7% | – | **0.42** | – |
| B1 drought-map rule | 64% | 48,203 | 27.6% | – | 0.36 | – |
| B2 USDA ERP trigger rule | 89% | 114,110 | 29.4% | – | 1.89 | – |
| A hurdle | 91% | 50,943 | 26.0% | – | 0.09 | **0% (0/1)** |
| B boosting | 72% | 43,288 | 31.2% | – | 0.28 | 0% (0/1) |
| C look-alikes | 60% | 39,198 | 35.0% | – | 0.40 | 0% (0/1) |
| D Tweedie GLM | 85% | 48,127 | 31.8% | – | 0.15 | 0% (0/1) |
| G TabPFN v2 | 67% | 43,242 | **35.2%** | – | 0.33 | 0% (0/1) |
| *Random counties (reference)* | – | – | *20.2%* | – | – | – |

**T2: Validation (2013-2015): quiet years**

| Model | Statewide total error (% off) | Weighted MAE (acres per county-year) | Budget capture (top-20 counties) | Any-damage AUC | Calibration (Σpred / Σactual) | 80% range coverage |
|---|---|---|---|---|---|---|
| B0 average | 1,481% | 17,198 | 14.0% | 0.504 | 4.85 | – |
| B1 drought-map rule | 406% | 12,984 | 21.2% | 0.575 | 3.61 | – |
| B2 USDA ERP trigger rule | 419% | 22,842 | 32.5% | 0.595 | 5.83 | – |
| A hurdle | **53%** | **3,819** | 36.2% | 0.677 | 0.50 | 100% (5/5) |
| B boosting | 84% | 4,393 | 27.0% | 0.679 | **1.01** | **80% (4/5)** |
| C look-alikes | 318% | 7,152 | 31.5% | 0.638 | 1.58 | 60% (3/5) |
| D Tweedie GLM | 97% | 4,114 | 39.9% | 0.682 | 0.65 | 80% (4/5) |
| G TabPFN v2 | 112% | 4,864 | **40.0%** | **0.724** | 1.18 | 60% (3/5) |
| *Random counties (reference)* | – | – | *21.6%* | – | – | – |

## E. Known misses

State-years where **every** calibrated model's statewide T1 total was off by more than 50% (walk-forward + validation):

| state | year | actual $M | direction | B0 average $M | B1 drought-map rule $M | A hurdle $M | B boosting $M | C look-alikes $M | D Tweedie GLM $M | G TabPFN v2 $M | likely reason |
|---|---|---|---|---|---|---|---|---|---|---|---|
| IA | 2006 | 47.998 | over | 152.049 | 165.250 | 130.736 | 158.056 | 110.153 | 225.922 | 182.559 | Quiet year: actual payout only 1.07% of insured $ ($48.0M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| IA | 2009 | 1.542 | over | 181.527 | 102.780 | 7.265 | 5.862 | 33.424 | 59.632 | 12.187 | Quiet year: actual payout only 0.02% of insured $ ($1.5M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| IA | 2010 | 0.103 | over | 161.971 | 89.819 | 2.166 | 10.021 | 16.299 | 10.351 | 9.505 | Quiet year: actual payout only 0.00% of insured $ ($0.1M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| IA | 2015 | 3.763 | over | 613.012 | 100.068 | 9.492 | 23.760 | 89.673 | 43.386 | 26.266 | Quiet year: actual payout only 0.03% of insured $ ($3.8M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2006 | 64.488 | over | 215.811 | 274.809 | 152.077 | 144.371 | 175.348 | 197.214 | 135.460 | Quiet year: actual payout only 2.45% of insured $ ($64.5M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2007 | 10.262 | over | 333.506 | 98.299 | 19.250 | 31.059 | 44.201 | 26.921 | 40.541 | Quiet year: actual payout only 0.24% of insured $ ($10.3M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2009 | 2.149 | over | 239.554 | 58.013 | 18.467 | 26.185 | 27.486 | 45.199 | 24.062 | Quiet year: actual payout only 0.04% of insured $ ($2.1M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2010 | 0.885 | over | 210.607 | 48.240 | 2.143 | 7.394 | 11.135 | 9.258 | 5.149 | Quiet year: actual payout only 0.02% of insured $ ($0.9M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2011 | 5.989 | over | 293.514 | 62.338 | 28.567 | 33.832 | 25.514 | 33.241 | 38.325 | Quiet year: actual payout only 0.08% of insured $ ($6.0M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |

- **Iowa 2013 is a known limitation, not tuned for.** The 2013 drought started after the Aug 15 decision date. Statewide D2+ area (weekly
  Drought Monitor in `data/processed/drought`) was 0% on every weekly map from late May through Aug 13, then rose to 21% on Aug 27 and 42%
  on Sep 10; the model inputs end Aug 14. Note that April 2013 maps still carried leftover 2012 drought (46% mean D2+ area on Apr 2),
  which the Apr 1 - Aug 14 features include; it had cleared by late May. No feature, model or hyper-parameter was changed to catch 2013, and
  calibration (a constant per model) cannot fix it either.
- **Expected miss in the final test: Iowa 2020 (derecho).** The Aug 10, 2020 derecho caused wind losses that are mostly coded to a cause
  other than drought, so drought-payout models cannot predict them. Final-test results for 2020 Iowa should be read with that in mind.

## F. Verdict

**Calibration did not clearly help**: on validation (out-of-sample for k) Σpred/Σactual moved closer to 1 for B boosting, C look-alikes, D Tweedie GLM, G TabPFN v2 and further from 1 for B0 average, B1 drought-map rule, B2 USDA ERP trigger rule, A hurdle; for B boosting it went 0.54 → 0.64 with dollar error (WAPE) 0.90 → 0.92, and for G TabPFN v2 0.49 → 0.69 with WAPE 0.90 → 0.94; budget capture and AUC are unchanged (largest change 0.0e+00 and 1.1e-16). Under the plan's rule G TabPFN v2 still wins: no simpler model is within noise of it on both capture (2 points) and WAPE (5%) once all models are calibrated (A: capture 44.4%, WAPE 0.67; B: capture 43.8%, WAPE 0.66; C: capture 40.2%, WAPE 0.79; D: capture 49.8%, WAPE 0.73). Against B1 (also calibrated) G TabPFN v2 has pooled capture 47.8% vs 28.9% and WAPE 0.68 vs 1.39 (51% lower). What looks off: k is fitted on walk-forward predictions, so the pooled walk-forward 'after' figures are in-sample for k and only validation tests it; k comes from a window dominated by the 2012 drought, so it over-corrects quiet years: B0 average Σpred/Σactual 1.61 → 3.21, B1 drought-map rule Σpred/Σactual 1.39 → 2.61, B2 USDA ERP trigger rule Σpred/Σactual 1.56 → 5.29, A hurdle Σpred/Σactual 0.41 → 0.25 on validation; G TabPFN v2 still under-budgets on validation (0.69), mostly Iowa 2013, which no Aug-15 input can show; 0 of 20 state-years needed the C range widened to contain B's point estimate. Ranges stay rough: pooled 80%-range coverage after calibration is A 45%, B 40%, C 80%, D 45%, G 40% and 80% for the budget range (C, widened around B's point).

**Headline model for the v1 test: B boosting.** G fails the speed test: CPU prediction of one year (367 IA+NE county-crops, T1+T2) took a median 353 s (T1 163 s, T2 189 s) against the 10 s limit, on 8 cores; it does install cleanly from requirements.txt. So B is the headline model. (see `app/model/DECISIONS.md`)

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
| B2 USDA ERP trigger rule | 20 | 2.100 | 2.773 | 0.268 | 4.590 | 1.921 | 0.594 | 1.517 | 1.572 | 1.583 | – |
| A hurdle | 20 | 0.807 | 2.316 | 0.444 | 1.602 | 0.670 | 0.780 | 0.739 | 0.645 | 0.654 | 0.450 |
| B boosting | 20 | 0.907 | 6.987 | 0.438 | 1.582 | 0.662 | 0.788 | 0.826 | 0.789 | 0.801 | 0.400 |
| C look-alikes | 20 | 0.959 | 12.057 | 0.402 | 1.889 | 0.791 | 0.711 | 0.901 | 0.808 | 0.822 | 0.800 |
| D Tweedie GLM | 20 | 0.859 | 9.684 | 0.498 | 1.745 | 0.731 | 0.762 | 0.765 | 0.613 | 0.624 | 0.450 |
| G TabPFN v2 | 20 | 0.920 | 6.858 | 0.478 | 1.620 | 0.678 | 0.748 | 0.852 | 0.791 | 0.800 | 0.400 |
| Random counties | 20 | – | – | 0.215 | – | – | – | – | – | – | – |
| Oracle (perfect ranking) | 20 | – | – | 0.778 | – | – | – | – | – | – | – |

**Drought years (statewide payout >= 3% of insured $)**

| model | state-yrs | Σpred/Σactual | state total err (x actual) | top-20 capture | county MAE $M | wape | AUC any payout | acres calib | out-of-pocket calib | relief calib | 80% range cov |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 average | 3 | 0.320 | 0.587 | 0.312 | 11.195 | 0.822 | 0.579 | 0.210 | 0.200 | 0.198 | – |
| B1 drought-map rule | 3 | 0.654 | 0.317 | 0.313 | 9.666 | 0.710 | 0.234 | 0.444 | 0.449 | 0.454 | – |
| B2 USDA ERP trigger rule | 3 | 1.487 | 0.784 | 0.330 | 16.949 | 1.245 | 0.264 | 1.206 | 1.206 | 1.204 | – |
| A hurdle | 3 | 0.760 | 0.413 | 0.402 | 8.053 | 0.592 | 0.352 | 0.603 | 0.582 | 0.590 | 0.000 |
| B boosting | 3 | 0.802 | 0.299 | 0.381 | 7.472 | 0.549 | 0.615 | 0.676 | 0.705 | 0.714 | 0.333 |
| C look-alikes | 3 | 0.798 | 0.237 | 0.347 | 8.312 | 0.611 | 0.452 | 0.624 | 0.627 | 0.636 | 0.667 |
| D Tweedie GLM | 3 | 0.693 | 0.379 | 0.402 | 7.769 | 0.571 | 0.061 | 0.513 | 0.474 | 0.481 | 0.000 |
| G TabPFN v2 | 3 | 0.792 | 0.355 | 0.440 | 7.472 | 0.549 | 0.635 | 0.654 | 0.666 | 0.672 | 0.333 |
| Random counties | 3 | – | – | 0.210 | – | – | – | – | – | – | – |
| Oracle (perfect ranking) | 3 | – | – | 0.527 | – | – | – | – | – | – | – |

**Quiet years**

| model | state-yrs | Σpred/Σactual | state total err (x actual) | top-20 capture | county MAE $M | wape | AUC any payout | acres calib | out-of-pocket calib | relief calib | 80% range cov |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 average | 17 | 10.222 | 141.073 | 0.257 | 3.392 | 9.543 | 0.620 | 4.868 | 4.868 | 4.871 | – |
| B1 drought-map rule | 17 | 6.677 | 64.844 | 0.284 | 2.162 | 6.082 | 0.605 | 3.410 | 3.422 | 3.447 | – |
| B2 USDA ERP trigger rule | 17 | 6.352 | 3.125 | 0.257 | 2.351 | 6.615 | 0.542 | 2.717 | 3.423 | 3.460 | – |
| A hurdle | 17 | 1.133 | 2.652 | 0.451 | 0.433 | 1.217 | 0.741 | 1.261 | 0.959 | 0.973 | 0.529 |
| B boosting | 17 | 1.635 | 8.168 | 0.448 | 0.514 | 1.447 | 0.742 | 1.403 | 1.215 | 1.231 | 0.412 |
| C look-alikes | 17 | 2.073 | 14.142 | 0.412 | 0.725 | 2.039 | 0.663 | 1.968 | 1.727 | 1.743 | 0.824 |
| D Tweedie GLM | 17 | 2.006 | 11.327 | 0.515 | 0.654 | 1.840 | 0.718 | 1.736 | 1.317 | 1.330 | 0.529 |
| G TabPFN v2 | 17 | 1.809 | 8.006 | 0.485 | 0.560 | 1.575 | 0.699 | 1.612 | 1.421 | 1.438 | 0.412 |
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
| model | max_iter | max_depth | wape | k | drought_weight | alpha |
|---|---|---|---|---|---|---|
| B | 200 | 4 | 0.554 | – | – | – |
| B | 400 | 3 | 0.560 | – | – | – |
| B | 400 | 4 | 0.562 | – | – | – |
| B | 200 | 3 | 0.594 | – | – | – |
| B | 100 | 4 | 0.602 | – | – | – |
| B | 100 | 3 | 0.665 | – | – | – |
| C | – | – | 0.661 | 10 | 1 | – |
| C | – | – | 0.672 | 25 | 1 | – |
| C | – | – | 0.689 | 25 | 2 | – |
| C | – | – | 0.691 | 10 | 2 | – |
| C | – | – | 0.694 | 25 | 3 | – |
| C | – | – | 0.698 | 10 | 3 | – |
| C | – | – | 0.705 | 50 | 1 | – |
| C | – | – | 0.719 | 50 | 3 | – |
| C | – | – | 0.726 | 50 | 2 | – |
| D | – | – | 0.635 | – | – | 0.010 |
| D | – | – | 0.763 | – | – | 0.100 |
| D | – | – | 1.048 | – | – | 1 |
