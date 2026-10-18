# Final test (official, run once): drought-severity models, test years 2016-2025

**Frozen before this run** (DECISIONS.md Entry 3): M1 logistic for Task A and for Task B (results/chosen_models.json), features and settings exactly as in the code. Trained on 2000-2015, scored once on 2016-2025. Baselines are fitted on the same training years. Validation = the 2013-2015 walk-forward numbers from `validation_report.md` (each year predicted from the years before it). Note: drought conditions by year for 2016-2025 were already discussed during the project, so treat this as a confirmatory test, not a blind one. Task A is a RANKING only: its probabilities are not calibrated (balanced class weights), so none are displayed, and Brier / calibration / predicted rates are shown for Task B only.

## Task A: outlook after Aug 13

Rows scored: 1920 county-years; actual worsening rate 39% (validation 2013-2015: 32%). Start level = `level_last_map`.

| Method | Test AUC | Test exact level | Test within 1 | Val AUC | Val exact level | Val within 1 |
|---|---|---|---|---|---|---|
| Persistence | 0.500 (const.) | 57.9% | 92.5% | 0.500 (const.) | 63.9% | 93.6% |
| Climatology | 0.514 | 21.9% | 57.9% | 0.450 | 34.2% | 65.8% |
| Most common level | 0.500 (const.) | 22.0% | 49.7% | 0.500 (const.) | 41.3% | 66.3% |
| M1 logistic (frozen) | 0.676 | 59.3% | 95.8% | 0.694 | 54.3% | 98.8% |

### Worsening rate per state-year and how well M1 ranks its counties (no probabilities shown; bold = IA 2023, NE 2022, NE 2023)

| State-year | Actual worsening rate | Within-state-year AUC (M1 ranking) | Counties |
|---|---|---|---|
| IA 2016 | 3% | 1.00 | 99 |
| IA 2017 | 49% | 0.61 | 99 |
| IA 2018 | 21% | 0.70 | 99 |
| IA 2019 | 24% | 0.80 | 99 |
| IA 2020 | 79% | 0.86 | 99 |
| IA 2021 | 47% | 0.84 | 99 |
| IA 2022 | 49% | 0.50 | 99 |
| **IA 2023** | **65%** | **0.90** | 99 |
| IA 2024 | 94% | 0.70 | 99 |
| IA 2025 | 54% | 0.57 | 99 |
| NE 2016 | 16% | 0.68 | 93 |
| NE 2017 | 9% | 0.85 | 93 |
| NE 2018 | 12% | 0.57 | 93 |
| NE 2019 | 4% | 0.96 | 93 |
| NE 2020 | 81% | 0.78 | 93 |
| NE 2021 | 38% | 0.68 | 93 |
| **NE 2022** | **57%** | **0.86** | 93 |
| **NE 2023** | **10%** | **0.62** | 93 |
| NE 2024 | 60% | 0.83 | 93 |
| NE 2025 | 10% | 0.59 | 93 |

## Task B: in-season severity (weather + soil)

Rows scored: 1920 county-years; actual worsening rate 57% (validation 2013-2015: 12%). Start level = `level_apr1`.

| Method | Test AUC | Test Brier | Test exact level | Test within 1 | Val AUC | Val Brier | Val exact level | Val within 1 |
|---|---|---|---|---|---|---|---|---|
| Persistence | 0.500 (const.) | 0.573 | 41.8% | 75.3% | 0.500 (const.) | 0.120 | 87.8% | 99.5% |
| Climatology | 0.691 | 0.219 | 20.2% | 56.6% | 0.766 | 0.181 | 15.5% | 54.5% |
| Most common level | 0.500 (const.) | 0.279 | 28.3% | 68.5% | 0.500 (const.) | 0.201 | 22.6% | 64.1% |
| M1 logistic (frozen) | 0.870 | 0.161 | 53.4% | 89.8% | 0.775 | 0.093 | 88.0% | 99.8% |

### Calibration by decile of predicted risk (frozen M1, test years)

| Decile | n | Mean predicted | Actual rate |
|---|---|---|---|
| 1 | 192 | 0.01 | 0.08 |
| 2 | 192 | 0.05 | 0.14 |
| 3 | 192 | 0.13 | 0.30 |
| 4 | 192 | 0.24 | 0.39 |
| 5 | 192 | 0.36 | 0.59 |
| 6 | 192 | 0.50 | 0.66 |
| 7 | 192 | 0.66 | 0.80 |
| 8 | 192 | 0.80 | 0.88 |
| 9 | 192 | 0.89 | 0.92 |
| 10 | 192 | 0.96 | 0.99 |

### Worsening rate per state-year, predicted vs actual (bold = the drought years IA 2023, NE 2022, NE 2023)

| State-year | Actual worsening rate | Predicted worsening rate (M1) |
|---|---|---|
| IA 2016 | 81% | 42% |
| IA 2017 | 90% | 74% |
| IA 2018 | 49% | 48% |
| IA 2019 | 73% | 34% |
| IA 2020 | 94% | 74% |
| IA 2021 | 86% | 68% |
| IA 2022 | 55% | 52% |
| **IA 2023** | **71%** | **69%** |
| IA 2024 | 0% | 6% |
| IA 2025 | 22% | 10% |
| NE 2016 | 61% | 43% |
| NE 2017 | 63% | 69% |
| NE 2018 | 33% | 42% |
| NE 2019 | 13% | 17% |
| NE 2020 | 90% | 79% |
| NE 2021 | 69% | 81% |
| **NE 2022** | **48%** | **42%** |
| **NE 2023** | **41%** | **10%** |
| NE 2024 | 44% | 44% |
| NE 2025 | 60% | 14% |

Correlation of predicted and actual state-year rate over the 20 state-years: 0.78.

## Reading the numbers

- Task B (in-season): frozen M1 AUC 0.870 on the test years (validation 0.775) vs climatology 0.691; exact level 53.4% vs persistence 41.8%; Brier 0.161 vs climatology 0.219.
- Task A (outlook, ranking only): frozen M1 AUC 0.676 (validation 0.694) vs climatology 0.514; exact level 59.3% vs persistence 57.9%, within one level 95.8% vs 92.5%.
