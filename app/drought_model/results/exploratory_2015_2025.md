# EXPLORATORY, after the official test: frozen M1 over 2015-2025

**These years were already scored once (2016-2025 in the official test, 2015 in the official validation window); this is not an independent test and does not replace `test_report.md`. Every table below is exploratory, after the official test.** No model, feature, setting or artifact was changed (DECISIONS.md Entry 4).

Schemes: **Fixed** = train on 2000-2014, predict 2015-2025 once. **Walk-forward** = for each Y in 2015..2025 train on 2000..Y-1, predict Y (so later years see the 2016-2025 labels of earlier years). M1 settings are exactly the frozen ones; imputers, scalers and base rates are refit per fold; rain normals and irrigation averages are built from strictly earlier years. Task A is a ranking only (no probabilities). Baselines are refit on the same training years as M1.

## Task A: outlook after Aug 13, pooled 2015-2025 (exploratory, after the official test)

| Scheme / window | Method | AUC | Exact level | Within 1 |
|---|---|---|---|---|
| Fixed: train 2000-2014, 2015-2025 | Persistence | 0.500 (const.) | 58.2% | 93.2% |
| Fixed: train 2000-2014, 2015-2025 | Climatology | 0.518 | 24.9% | 60.6% |
| Fixed: train 2000-2014, 2015-2025 | Most common level | 0.500 (const.) | 26.1% | 54.2% |
| Fixed: train 2000-2014, 2015-2025 | M1 (frozen) | 0.676 | 59.2% | 96.4% |
| Walk-forward: train 2000..Y-1, 2015-2025 | Persistence | 0.500 (const.) | 58.2% | 93.2% |
| Walk-forward: train 2000..Y-1, 2015-2025 | Climatology | 0.532 | 24.1% | 59.8% |
| Walk-forward: train 2000..Y-1, 2015-2025 | Most common level | 0.500 (const.) | 26.1% | 54.2% |
| Walk-forward: train 2000..Y-1, 2015-2025 | M1 (frozen) | 0.679 | 58.5% | 96.0% |

### Task A: compared with the official 2016-2025 numbers, same years (exploratory, after the official test)

| Scheme / window | Method | AUC | Exact level | Within 1 |
|---|---|---|---|---|
| Official: train 2000-2015, 2016-2025 (test_report.md) | Persistence | 0.500 (const.) | 57.9% | 92.5% |
| Official: train 2000-2015, 2016-2025 (test_report.md) | Climatology | 0.514 | 21.9% | 57.9% |
| Official: train 2000-2015, 2016-2025 (test_report.md) | M1 (frozen) | 0.676 | 59.3% | 95.8% |
| Fixed: train 2000-2014, 2016-2025 only | Persistence | 0.500 (const.) | 57.9% | 92.5% |
| Fixed: train 2000-2014, 2016-2025 only | Climatology | 0.513 | 22.0% | 58.1% |
| Fixed: train 2000-2014, 2016-2025 only | Most common level | 0.500 (const.) | 22.0% | 49.7% |
| Fixed: train 2000-2014, 2016-2025 only | M1 (frozen) | 0.682 | 59.2% | 96.0% |
| Walk-forward: train 2000..Y-1, 2016-2025 only | Persistence | 0.500 (const.) | 57.9% | 92.5% |
| Walk-forward: train 2000..Y-1, 2016-2025 only | Climatology | 0.529 | 21.2% | 57.2% |
| Walk-forward: train 2000..Y-1, 2016-2025 only | Most common level | 0.500 (const.) | 22.0% | 49.7% |
| Walk-forward: train 2000..Y-1, 2016-2025 only | M1 (frozen) | 0.684 | 58.4% | 95.6% |

### Task A: 2015 called out separately (exploratory, after the official test; 2015 is the one year the official test did not cover)

| Scheme / window | Method | AUC | Exact level | Within 1 |
|---|---|---|---|---|
| Fixed: train 2000-2014, 2015 only | Persistence | 0.500 (const.) | 61.5% | 100.0% |
| Fixed: train 2000-2014, 2015 only | Climatology | 0.797 | 53.1% | 84.9% |
| Fixed: train 2000-2014, 2015 only | Most common level | 0.500 (const.) | 66.7% | 99.5% |
| Fixed: train 2000-2014, 2015 only | M1 (frozen) | 0.640 | 59.4% | 100.0% |
| Walk-forward: train 2000..Y-1, 2015 only | Persistence | 0.500 (const.) | 61.5% | 100.0% |
| Walk-forward: train 2000..Y-1, 2015 only | Climatology | 0.797 | 53.1% | 84.9% |
| Walk-forward: train 2000..Y-1, 2015 only | Most common level | 0.500 (const.) | 66.7% | 99.5% |
| Walk-forward: train 2000..Y-1, 2015 only | M1 (frozen) | 0.640 | 59.4% | 100.0% |

### Task A: one row per year, Fixed: train 2000-2014 (exploratory, after the official test)

| Year | M1 AUC | M1 exact | M1 within 1 | Persistence exact | Persistence within 1 | Climatology AUC |
|---|---|---|---|---|---|---|
| 2015 | 0.640 | 59.4% | 100.0% | 61.5% | 100.0% | 0.797 |
| 2016 | 0.827 | 74.0% | 100.0% | 79.2% | 100.0% | 0.865 |
| 2017 | 0.721 | 68.8% | 94.3% | 67.7% | 92.7% | 0.494 |
| 2018 | 0.697 | 77.1% | 100.0% | 83.3% | 99.5% | 0.323 |
| 2019 | 0.806 | 72.9% | 100.0% | 78.1% | 100.0% | 0.454 |
| 2020 | 0.800 | 22.4% | 81.8% | 20.3% | 76.6% | 0.825 |
| 2021 | 0.668 | 52.1% | 97.9% | 57.3% | 94.8% | 0.726 |
| 2022 | 0.686 | 56.8% | 99.5% | 46.4% | 92.7% | 0.600 |
| 2023 | 0.831 | 62.5% | 89.6% | 60.9% | 89.1% | 0.520 |
| 2024 | 0.779 | 40.6% | 96.9% | 19.3% | 79.7% | 0.798 |
| 2025 | 0.414 | 65.1% | 100.0% | 66.1% | 100.0% | 0.604 |

### Task A: one row per year, Walk-forward: train 2000..Y-1 (exploratory, after the official test)

| Year | M1 AUC | M1 exact | M1 within 1 | Persistence exact | Persistence within 1 | Climatology AUC |
|---|---|---|---|---|---|---|
| 2015 | 0.640 | 59.4% | 100.0% | 61.5% | 100.0% | 0.797 |
| 2016 | 0.844 | 72.4% | 100.0% | 79.2% | 100.0% | 0.868 |
| 2017 | 0.727 | 67.7% | 93.8% | 67.7% | 92.7% | 0.501 |
| 2018 | 0.672 | 77.1% | 100.0% | 83.3% | 99.5% | 0.311 |
| 2019 | 0.792 | 74.0% | 100.0% | 78.1% | 100.0% | 0.443 |
| 2020 | 0.809 | 20.3% | 79.2% | 20.3% | 76.6% | 0.839 |
| 2021 | 0.626 | 52.6% | 98.4% | 57.3% | 94.8% | 0.743 |
| 2022 | 0.690 | 56.8% | 99.5% | 46.4% | 92.7% | 0.607 |
| 2023 | 0.853 | 63.0% | 90.6% | 60.9% | 89.1% | 0.545 |
| 2024 | 0.811 | 37.5% | 94.8% | 19.3% | 79.7% | 0.859 |
| 2025 | 0.482 | 63.0% | 100.0% | 66.1% | 100.0% | 0.752 |

## Task B: in-season severity (weather + soil), pooled 2015-2025 (exploratory, after the official test)

| Scheme / window | Method | AUC | Brier | Exact level | Within 1 |
|---|---|---|---|---|---|
| Fixed: train 2000-2014, 2015-2025 | Persistence | 0.500 (const.) | 0.533 | 45.9% | 77.5% |
| Fixed: train 2000-2014, 2015-2025 | Climatology | 0.688 | 0.228 | 21.8% | 58.3% |
| Fixed: train 2000-2014, 2015-2025 | Most common level | 0.500 (const.) | 0.265 | 30.3% | 71.4% |
| Fixed: train 2000-2014, 2015-2025 | M1 (frozen) | 0.870 | 0.155 | 56.3% | 91.0% |
| Walk-forward: train 2000..Y-1, 2015-2025 | Persistence | 0.500 (const.) | 0.533 | 45.9% | 77.5% |
| Walk-forward: train 2000..Y-1, 2015-2025 | Climatology | 0.685 | 0.231 | 24.2% | 63.3% |
| Walk-forward: train 2000..Y-1, 2015-2025 | Most common level | 0.500 (const.) | 0.262 | 30.3% | 71.4% |
| Walk-forward: train 2000..Y-1, 2015-2025 | M1 (frozen) | 0.875 | 0.147 | 58.0% | 91.3% |

### Task B: compared with the official 2016-2025 numbers, same years (exploratory, after the official test)

| Scheme / window | Method | AUC | Brier | Exact level | Within 1 |
|---|---|---|---|---|---|
| Official: train 2000-2015, 2016-2025 (test_report.md) | Persistence | 0.500 (const.) | 0.573 | 41.8% | 75.3% |
| Official: train 2000-2015, 2016-2025 (test_report.md) | Climatology | 0.691 | 0.219 | 20.2% | 56.6% |
| Official: train 2000-2015, 2016-2025 (test_report.md) | M1 (frozen) | 0.870 | 0.161 | 53.4% | 89.8% |
| Fixed: train 2000-2014, 2016-2025 only | Persistence | 0.500 (const.) | 0.573 | 41.8% | 75.3% |
| Fixed: train 2000-2014, 2016-2025 only | Climatology | 0.698 | 0.216 | 20.9% | 56.3% |
| Fixed: train 2000-2014, 2016-2025 only | Most common level | 0.500 (const.) | 0.273 | 28.3% | 68.5% |
| Fixed: train 2000-2014, 2016-2025 only | M1 (frozen) | 0.871 | 0.158 | 53.6% | 90.1% |
| Walk-forward: train 2000..Y-1, 2016-2025 only | Persistence | 0.500 (const.) | 0.573 | 41.8% | 75.3% |
| Walk-forward: train 2000..Y-1, 2016-2025 only | Climatology | 0.697 | 0.220 | 23.6% | 61.8% |
| Walk-forward: train 2000..Y-1, 2016-2025 only | Most common level | 0.500 (const.) | 0.269 | 28.3% | 68.5% |
| Walk-forward: train 2000..Y-1, 2016-2025 only | M1 (frozen) | 0.874 | 0.150 | 55.4% | 90.5% |

### Task B: 2015 called out separately (exploratory, after the official test; 2015 is the one year the official test did not cover)

| Scheme / window | Method | AUC | Brier | Exact level | Within 1 |
|---|---|---|---|---|---|
| Fixed: train 2000-2014, 2015 only | Persistence | 0.500 (const.) | 0.130 | 87.0% | 100.0% |
| Fixed: train 2000-2014, 2015 only | Climatology | 0.507 | 0.345 | 30.2% | 78.1% |
| Fixed: train 2000-2014, 2015 only | Most common level | 0.500 (const.) | 0.189 | 50.0% | 100.0% |
| Fixed: train 2000-2014, 2015 only | M1 (frozen) | 0.780 | 0.116 | 83.3% | 100.0% |
| Walk-forward: train 2000..Y-1, 2015 only | Persistence | 0.500 (const.) | 0.130 | 87.0% | 100.0% |
| Walk-forward: train 2000..Y-1, 2015 only | Climatology | 0.507 | 0.345 | 30.2% | 78.1% |
| Walk-forward: train 2000..Y-1, 2015 only | Most common level | 0.500 (const.) | 0.189 | 50.0% | 100.0% |
| Walk-forward: train 2000..Y-1, 2015 only | M1 (frozen) | 0.780 | 0.116 | 83.3% | 100.0% |

### Task B: one row per year, Fixed: train 2000-2014 (exploratory, after the official test)

| Year | M1 AUC | M1 exact | M1 within 1 | Persistence exact | Persistence within 1 | Climatology AUC |
|---|---|---|---|---|---|---|
| 2015 | 0.780 | 83.3% | 100.0% | 87.0% | 100.0% | 0.507 |
| 2016 | 0.770 | 37.0% | 96.9% | 28.6% | 77.6% | 0.757 |
| 2017 | 0.864 | 43.8% | 90.6% | 20.3% | 63.5% | 0.676 |
| 2018 | 0.785 | 66.1% | 100.0% | 58.3% | 94.8% | 0.442 |
| 2019 | 0.876 | 64.1% | 91.7% | 56.2% | 87.5% | 0.240 |
| 2020 | 0.773 | 34.4% | 75.0% | 7.8% | 51.6% | 0.601 |
| 2021 | 0.830 | 37.0% | 82.8% | 22.4% | 52.6% | 0.709 |
| 2022 | 0.923 | 60.4% | 93.8% | 44.8% | 79.2% | 0.732 |
| 2023 | 0.911 | 45.8% | 80.7% | 43.8% | 63.0% | 0.883 |
| 2024 | 0.979 | 85.9% | 96.9% | 77.1% | 92.7% | 0.975 |
| 2025 | 0.773 | 61.5% | 92.7% | 58.9% | 90.1% | 0.846 |

### Task B: one row per year, Walk-forward: train 2000..Y-1 (exploratory, after the official test)

| Year | M1 AUC | M1 exact | M1 within 1 | Persistence exact | Persistence within 1 | Climatology AUC |
|---|---|---|---|---|---|---|
| 2015 | 0.780 | 83.3% | 100.0% | 87.0% | 100.0% | 0.507 |
| 2016 | 0.762 | 38.5% | 96.4% | 28.6% | 77.6% | 0.732 |
| 2017 | 0.869 | 44.3% | 91.1% | 20.3% | 63.5% | 0.710 |
| 2018 | 0.820 | 69.3% | 100.0% | 58.3% | 94.8% | 0.435 |
| 2019 | 0.906 | 71.4% | 93.8% | 56.2% | 87.5% | 0.308 |
| 2020 | 0.813 | 40.1% | 75.0% | 7.8% | 51.6% | 0.625 |
| 2021 | 0.887 | 39.1% | 83.3% | 22.4% | 52.6% | 0.767 |
| 2022 | 0.896 | 56.8% | 93.2% | 44.8% | 79.2% | 0.753 |
| 2023 | 0.896 | 45.8% | 78.1% | 43.8% | 63.0% | 0.876 |
| 2024 | 0.978 | 84.9% | 97.4% | 77.1% | 92.7% | 0.966 |
| 2025 | 0.754 | 64.1% | 96.4% | 58.9% | 90.1% | 0.783 |

## Task B: predicted vs actual worsening rate per state-year (exploratory, after the official test; 2015 in bold)

| State-year | Actual worsening rate | Fixed: predicted | Walk-forward: predicted |
|---|---|---|---|
| **IA 2015** | **12%** | **31%** | **31%** |
| IA 2016 | 81% | 42% | 42% |
| IA 2017 | 90% | 76% | 79% |
| IA 2018 | 49% | 47% | 54% |
| IA 2019 | 73% | 34% | 45% |
| IA 2020 | 94% | 75% | 83% |
| IA 2021 | 86% | 69% | 73% |
| IA 2022 | 55% | 53% | 58% |
| IA 2023 | 71% | 70% | 72% |
| IA 2024 | 0% | 6% | 8% |
| IA 2025 | 22% | 12% | 16% |
| **NE 2015** | **14%** | **19%** | **19%** |
| NE 2016 | 61% | 40% | 43% |
| NE 2017 | 63% | 71% | 74% |
| NE 2018 | 33% | 42% | 44% |
| NE 2019 | 13% | 17% | 24% |
| NE 2020 | 90% | 81% | 81% |
| NE 2021 | 69% | 82% | 83% |
| NE 2022 | 48% | 46% | 36% |
| NE 2023 | 41% | 13% | 9% |
| NE 2024 | 44% | 43% | 47% |
| NE 2025 | 60% | 16% | 16% |

Correlation of predicted and actual state-year rate across the 22 state-years of 2015-2025: Fixed 0.79, Walk-forward 0.79 (2016-2025 only, 20 state-years: Fixed 0.78, Walk-forward 0.78; the official test reported 0.78).

### Task B calibration by decile, Fixed: train 2000-2014, 2015-2025 (exploratory, after the official test)

| Decile | n | Mean predicted | Actual rate |
|---|---|---|---|
| 1 | 212 | 0.01 | 0.08 |
| 2 | 211 | 0.05 | 0.10 |
| 3 | 211 | 0.12 | 0.22 |
| 4 | 211 | 0.22 | 0.36 |
| 5 | 211 | 0.34 | 0.47 |
| 6 | 211 | 0.47 | 0.60 |
| 7 | 211 | 0.64 | 0.73 |
| 8 | 211 | 0.78 | 0.87 |
| 9 | 211 | 0.89 | 0.91 |
| 10 | 212 | 0.96 | 1.00 |

### Task B calibration by decile, Walk-forward: train 2000..Y-1, 2015-2025 (exploratory, after the official test)

| Decile | n | Mean predicted | Actual rate |
|---|---|---|---|
| 1 | 212 | 0.01 | 0.11 |
| 2 | 211 | 0.06 | 0.14 |
| 3 | 211 | 0.14 | 0.17 |
| 4 | 211 | 0.25 | 0.27 |
| 5 | 211 | 0.37 | 0.48 |
| 6 | 211 | 0.52 | 0.63 |
| 7 | 211 | 0.67 | 0.73 |
| 8 | 211 | 0.82 | 0.86 |
| 9 | 211 | 0.91 | 0.94 |
| 10 | 212 | 0.97 | 1.00 |

## For the map: Task B simulation level vs the observed level, per year (exploratory, after the official test)

The simulation helper's predicted level (start level plus the training median step when P(worse) >= 0.5) with observed weather (precip x 1.0), compared with the observed worst level Apr 1-Aug 13. 'Outside range' = share of counties with at least one Task B input beyond the fold's training min/max. Persistence = keeping the Apr 1 level.

| Year | Fixed: exact | within 1 | off by 2+ | counties with an input outside range | Walk-forward: exact | within 1 | off by 2+ | outside range | Persistence: exact | within 1 | off by 2+ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2015 | 83% | 100% | 0% | 1% | 83% | 100% | 0% | 1% | 87% | 100% | 0% |
| 2016 | 37% | 97% | 3% | 0% | 39% | 96% | 4% | 0% | 29% | 78% | 22% |
| 2017 | 44% | 91% | 9% | 1% | 44% | 91% | 9% | 0% | 20% | 64% | 36% |
| 2018 | 66% | 100% | 0% | 1% | 69% | 100% | 0% | 0% | 58% | 95% | 5% |
| 2019 | 64% | 92% | 8% | 1% | 71% | 94% | 6% | 1% | 56% | 88% | 12% |
| 2020 | 34% | 75% | 25% | 0% | 40% | 75% | 25% | 0% | 8% | 52% | 48% |
| 2021 | 37% | 83% | 17% | 1% | 39% | 83% | 17% | 1% | 22% | 53% | 47% |
| 2022 | 60% | 94% | 6% | 3% | 57% | 93% | 7% | 2% | 45% | 79% | 21% |
| 2023 | 46% | 81% | 19% | 4% | 46% | 78% | 22% | 0% | 44% | 63% | 37% |
| 2024 | 86% | 97% | 3% | 0% | 85% | 97% | 3% | 0% | 77% | 93% | 7% |
| 2025 | 61% | 93% | 7% | 0% | 64% | 96% | 4% | 0% | 59% | 90% | 10% |

Pooled 2015-2025: Fixed: exact 56%, within one 91%, off by 2+ 9%, counties with an input outside the training range 1%; Walk-forward: exact 58%, within one 91%, off by 2+ 9%, counties with an input outside the training range 0%.

## Summary (exploratory, after the official test)

1. Over 2015-2025 the frozen M1 models score the same as in the official test: Task B AUC 0.87 (fixed) and 0.875 (walk-forward) against 0.870 officially, exact level 56-58% against 53% and within one level 91% against 90%; Task A AUC 0.68 against 0.676, with exact level 58-59% against 58% for persistence. Adding 2015 changes little because it was a calm year (Task B AUC 0.78; persistence's 87% exact level edges M1's 83% there, but M1's Brier is better, 0.116 vs 0.130).
2. Retraining every year helps Task B slightly (Brier 0.147 vs 0.155, exact level 58.0% vs 56.3%) and Task A not at all, so a model frozen on 2000-2015 is a sound choice for the app; the state-year worsening-rate correlation is 0.79 (official 0.78), but it still misses Nebraska 2023 (13% predicted vs 41% actual) and Nebraska 2025 (16% vs 60%), and the mid-range probabilities run low (the 0.34 decile actually worsened 47% of the time).
3. For the map, the simulation level is exact for about 56-58% of counties, within one level for 91% and off by 2+ for 9% (keeping the April level would be off by 2+ for 22%), and only 0-4% of counties a year have an input outside the training range, so out-of-range flags are rare in observed-weather years.
