# Official test report (2016-2025)

**Official test – model frozen before seeing test data; some test years appeared in earlier exploratory analyses (see DECISIONS.md).**

The headline model (D) was chosen by the pre-declared rule on walk-forward + validation only and frozen in DECISIONS.md (Entries 3-7) before this run. Earlier exploratory analyses touched some 2016-2025 years (2018/2022 payout totals, early 2022/2023 budget tests); nothing from them was used to choose or tune any model.

**Headline model: D Tweedie GLM, uncalibrated** (alpha 0.001; rule: lowest drought-year statewide absolute $ error among candidates beating B3 (0.257) and B4 (0.289) on capture; within 5% of the lowest error: ['D']; simplest wins). Secondary, reported in full: A, B, C. Baselines: Z0 (predict zero), B1 (drought-bin average), B2a (USDA binary trigger), B2b (tiered LFP-style trigger),
B3 (liability only), B4 (liability x D2+ last map). All models were trained on 2000-2015 (5835 rows) and predict 3682 rows. Calibration is nested (the multiplier for a year uses only earlier years, including the test
years already passed) and was applied only to A, B4 and B3's T2, as decided on walk-forward + validation. **X** = estimated insurance payouts, **Y** = estimated deductible exposure, **Z** = illustrative relief allocation under a 95%
coverage assumption (inspired by USDA ERP 2022). Metric definitions are in `validation_report.md`.

**Which state-years count as drought, and why.** A state-year is a *drought state-year* when the actual statewide drought payout was at least 3% of insured dollars. This grouping rule was fixed before any test result existed and is
used only to split the tables. In 2016-2025 that gives 3 drought state-year(s): IA 2023, NE 2022, NE 2023; the other 17 are quiet.

## 1. Headline table: D Tweedie GLM vs B2a and B2b first, then A, B, C and B1, B3, B4, Z0 (T1: X, estimated insurance payouts)
Statewide abs. error = mean over state-years of |Σ predicted - Σ actual|; Under-budgeted = Σ over state-years of max(0, actual - predicted); Worst shortfall = largest single state-year shortfall; County WAPE and Top-20 capture over counties (crops summed); Σpred/Σactual < 1 under-budgets.

**All state-years (20)**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual | Range coverage | Range width | Upper-bound misses |
|---|---|---|---|---|---|---|---|---|---|---|
| D Tweedie GLM | $114.3M | $991.8M | $481.1M | 0.96 | **54.4%** | 0.746 | **1.09** | 40% (8/20) | $274.1M | 2 |
| B2a USDA binary trigger | $119.8M | $917.5M | $338.5M | 1.42 | 26.4% | 0.569 | 1.17 | – | – | – |
| B2b tiered LFP-style trigger | $135.1M | $1,134.8M | $373.5M | 1.30 | 28.5% | 0.570 | 1.13 | – | – | – |
| A hurdle | $106.9M | $1,743.4M | $650.3M | **0.85** | 53.1% | 0.743 | 0.58 | 60% (12/20) | $276.7M | 3 |
| B boosting | $106.0M | $860.9M | $395.9M | 0.96 | 51.7% | **0.797** | 1.12 | 40% (8/20) | $255.8M | 2 |
| C look-alikes | $119.0M | $640.7M | $292.3M | 1.15 | 48.9% | 0.748 | 1.34 | 90% (18/20) | $519.4M | 0 |
| B1 drought-bin average | $133.4M | **$270.9M** | $270.4M | 1.44 | 33.9% | 0.627 | 1.66 | – | – | – |
| B3 liability only | $242.7M | $1,115.0M | $570.5M | 1.82 | 23.9% | 0.500 | 1.81 | – | – | – |
| B4 liability x D2+ last map | **$95.1M** | $492.4M | **$194.9M** | 1.22 | 40.3% | 0.612 | 1.28 | – | – | – |
| Z0 predict zero | $162.2M | $3,244.5M | $860.0M | 1.00 | 20.6% | 0.500 | 0.00 | – | – | – |
| *Random counties / best possible* | – | – | – | – | *21.3% / 72.9%* | – | – | – | – | – |

**Drought state-years only**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual | Range coverage | Range width | Upper-bound misses |
|---|---|---|---|---|---|---|---|---|---|---|
| D Tweedie GLM | $312.9M | $938.7M | $481.1M | 0.65 | 47.7% | 0.732 | 0.57 | 33% (1/3) | $251.0M | 2 |
| B2a USDA binary trigger | $211.8M | $508.7M | $338.5M | 0.97 | 26.6% | 0.409 | 0.83 | – | – | – |
| B2b tiered LFP-style trigger | $417.8M | $641.1M | $373.5M | 1.00 | 37.2% | 0.415 | **0.99** | – | – | – |
| A hurdle | $518.7M | $1,556.2M | $650.3M | 0.79 | 42.9% | 0.763 | 0.29 | 0% (0/3) | $265.4M | 3 |
| B boosting | $273.7M | $821.2M | $395.9M | **0.63** | **48.6%** | 0.740 | 0.62 | 33% (1/3) | $213.6M | 2 |
| C look-alikes | $210.7M | $632.0M | $292.3M | 0.70 | 43.4% | **0.791** | 0.71 | 100% (3/3) | $1,221.4M | 0 |
| B1 drought-bin average | $192.4M | **$270.4M** | $270.4M | 0.87 | 30.1% | 0.528 | 1.02 | – | – | – |
| B3 liability only | $371.7M | $1,115.0M | $570.5M | 0.77 | 28.4% | 0.500 | 0.49 | – | – | – |
| B4 liability x D2+ last map | **$180.7M** | $318.2M | **$194.9M** | 0.82 | 42.7% | 0.654 | 0.96 | – | – | – |
| Z0 predict zero | $729.5M | $2,188.5M | $860.0M | 1.00 | 21.7% | 0.500 | 0.00 | – | – | – |
| *Random counties / best possible* | – | – | – | – | *21.6% / 64.4%* | – | – | – | – | – |

**Quiet state-years only**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual | Range coverage | Range width | Upper-bound misses |
|---|---|---|---|---|---|---|---|---|---|---|
| D Tweedie GLM | $79.3M | $53.1M | $29.9M | 1.58 | **55.6%** | 0.718 | 2.18 | 41% (7/17) | $278.2M | 0 |
| B2a USDA binary trigger | $103.6M | $408.9M | $109.1M | 2.34 | 26.4% | 0.537 | 1.89 | – | – | – |
| B2b tiered LFP-style trigger | $85.2M | $493.7M | $109.1M | 1.92 | 27.0% | 0.537 | 1.44 | – | – | – |
| A hurdle | **$34.2M** | $187.1M | $56.0M | **0.98** | 54.9% | 0.717 | **1.20** | 71% (12/17) | $278.7M | 0 |
| B boosting | $76.4M | $39.6M | $19.4M | 1.66 | 52.2% | **0.778** | 2.16 | 41% (7/17) | $263.2M | 0 |
| C look-alikes | $102.9M | $8.6M | $8.6M | 2.09 | 49.9% | 0.721 | 2.64 | 88% (15/17) | $395.5M | 0 |
| B1 drought-bin average | $123.1M | $0.6M | $0.6M | 2.64 | 34.6% | 0.590 | 2.98 | – | – | – |
| B3 liability only | $219.9M | **$0.0M** | **$0.0M** | 4.02 | 23.1% | 0.500 | 4.54 | – | – | – |
| B4 liability x D2+ last map | $80.0M | $174.1M | $73.6M | 2.06 | 39.9% | 0.578 | 1.96 | – | – | – |
| Z0 predict zero | $62.1M | $1,056.0M | $257.5M | 1.00 | 20.4% | 0.500 | 0.00 | – | – | – |
| *Random counties / best possible* | – | – | – | – | *21.2% / 74.5%* | – | – | – | – | – |

## 2. Statewide X per state-year ($M)
D's scenario range = the historical scenario range of C (look-alike spread, calibrated like C) widened where needed so that D Tweedie GLM's point estimate lies inside it; rough 10th-90th percentile of past outcomes.

| state | year | type | actual X $M | D Tweedie GLM $M | B2a USDA binary trigger $M | D Tweedie GLM scenario range $M | actual vs range | B2b tiered LFP-style trigger $M | A hurdle $M | B boosting $M | C look-alikes $M |
|---|---|---|---|---|---|---|---|---|---|---|---|
| IA | 2016 | quiet | 1.4 | 21.6 | 0.0 | 1.1–85.1 | inside ✓ | 0.0 | 6.1 | 25.0 | 29.0 |
| IA | 2017 | quiet | 109.1 | 338.5 | 0.0 | 25.9–817.5 | inside ✓ | 0.0 | 223.5 | 205.0 | 333.7 |
| IA | 2018 | quiet | 25.2 | 46.6 | 21.5 | 3.9–170.1 | inside ✓ | 13.6 | 20.9 | 68.3 | 56.3 |
| IA | 2019 | quiet | 2.9 | 135.1 | 0.0 | 12.4–692.6 | outside ✗ | 0.0 | 66.2 | 83.9 | 252.1 |
| IA | 2020 | quiet | 213.5 | 325.8 | 179.9 | 52.4–1,186.9 | inside ✓ | 149.8 | 207.7 | 257.4 | 477.2 |
| IA | 2021 | quiet | 55.9 | 499.7 | 690.6 | 78.8–1,439.0 | outside ✗ | 457.9 | 266.3 | 798.4 | 635.7 |
| IA | 2022 | quiet | 257.5 | 466.2 | 298.2 | 44.2–1,030.7 | inside ✓ | 201.0 | 243.1 | 385.3 | 390.3 |
| IA | 2023 | drought | 716.0 | 479.2 | 545.8 | 36.0–1,433.8 | inside ✓ | 342.5 | 370.0 | 452.7 | 573.4 |
| IA | 2024 | quiet | 58.5 | 47.8 | 384.1 | 0.8–197.7 | inside ✓ | 371.5 | 21.6 | 40.9 | 68.8 |
| IA | 2025 | quiet | 14.6 | 7.8 | 0.0 | 0.1–15.9 | inside ✓ | 0.0 | 3.4 | 19.2 | 6.0 |
| NE | 2016 | quiet | 10.5 | 21.3 | 0.0 | 1.2–72.5 | inside ✓ | 0.0 | 6.0 | 21.9 | 25.5 |
| NE | 2017 | quiet | 36.1 | 57.4 | 0.0 | 4.6–126.6 | inside ✓ | 0.0 | 35.7 | 43.3 | 57.2 |
| NE | 2018 | quiet | 11.7 | 5.9 | 0.0 | 0.4–41.5 | inside ✓ | 0.0 | 1.2 | 10.0 | 15.1 |
| NE | 2019 | quiet | 1.1 | 9.7 | 0.0 | 0.1–39.9 | inside ✓ | 0.0 | 2.6 | 6.6 | 14.3 |
| NE | 2020 | quiet | 55.8 | 70.4 | 0.0 | 11.7–281.4 | inside ✓ | 0.0 | 33.3 | 54.9 | 116.3 |
| NE | 2021 | quiet | 94.0 | 157.0 | 43.0 | 12.1–386.2 | inside ✓ | 52.5 | 74.5 | 145.0 | 158.1 |
| NE | 2022 | drought | 860.0 | 639.2 | 521.4 | 87.8–1,262.7 | inside ✓ | 592.4 | 209.6 | 697.9 | 567.7 |
| NE | 2023 | drought | 612.5 | 131.5 | 739.3 | 30.8–1,122.4 | inside ✓ | 1,225.0 | 52.6 | 216.6 | 415.4 |
| NE | 2024 | quiet | 77.3 | 47.4 | 0.0 | 4.3–212.3 | inside ✓ | 0.0 | 21.4 | 57.9 | 81.0 |
| NE | 2025 | quiet | 30.9 | 39.4 | 382.2 | 5.7–187.5 | inside ✓ | 270.2 | 29.7 | 52.8 | 71.0 |

Historical scenario range coverage by model (own ranges, before widening):

| model | state-years | n | inside | coverage | mean width | actual above upper bound | actual below lower bound |
|---|---|---|---|---|---|---|---|
| A hurdle | all | 20 | 12 | 60% | $276.7M | 3 | 5 |
| A hurdle | drought | 3 | 0 | 0% | $265.4M | 3 | 0 |
| A hurdle | quiet | 17 | 12 | 71% | $278.7M | 0 | 5 |
| B boosting | all | 20 | 8 | 40% | $255.8M | 2 | 10 |
| B boosting | drought | 3 | 1 | 33% | $213.6M | 2 | 0 |
| B boosting | quiet | 17 | 7 | 41% | $263.2M | 0 | 10 |
| C look-alikes | all | 20 | 18 | 90% | $519.4M | 0 | 2 |
| C look-alikes | drought | 3 | 3 | 100% | $1,221.4M | 0 | 0 |
| C look-alikes | quiet | 17 | 15 | 88% | $395.5M | 0 | 2 |
| D Tweedie GLM | all | 20 | 8 | 40% | $274.1M | 2 | 10 |
| D Tweedie GLM | drought | 3 | 1 | 33% | $251.0M | 2 | 0 |
| D Tweedie GLM | quiet | 17 | 7 | 41% | $278.2M | 0 | 10 |

The widened range around D Tweedie GLM's point contained the actual in 18 of 20 state-years; the point was inside C's raw range in 20.

## 3. T2 (damaged acres) and Z (illustrative relief allocation, 95% coverage assumption)
**T2, all state-years**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual |
|---|---|---|---|---|---|---|---|
| D Tweedie GLM | 696k ac | 6,647k ac | 2,337k ac | 0.90 | **52.2%** | 0.752 | 1.03 |
| B2a USDA binary trigger | 818k ac | 11,262k ac | 2,525k ac | 1.13 | 25.6% | 0.572 | 0.71 |
| B2b tiered LFP-style trigger | 853k ac | 11,733k ac | 3,430k ac | 1.05 | 27.1% | 0.570 | 0.69 |
| A hurdle | 704k ac | 11,211k ac | 2,910k ac | **0.80** | 51.6% | 0.758 | 0.60 |
| B boosting | 685k ac | 6,955k ac | 2,894k ac | 0.89 | 50.8% | **0.802** | **0.99** |
| C look-alikes | 736k ac | 5,415k ac | 2,310k ac | 1.05 | 46.1% | 0.758 | 1.19 |
| B1 drought-bin average | 714k ac | **5,325k ac** | **2,040k ac** | 1.11 | 35.6% | 0.631 | 1.17 |
| B3 liability only | 1,191k ac | 9,116k ac | 3,136k ac | 1.41 | 27.2% | 0.340 | 1.27 |
| B4 liability x D2+ last map | **514k ac** | 6,004k ac | 2,274k ac | 0.99 | 38.1% | 0.612 | 0.92 |
| Z0 predict zero | 1,048k ac | 20,968k ac | 4,659k ac | 1.00 | 20.4% | 0.500 | 0.00 |
| *Random counties / best possible* | – | – | – | – | *21.3% / 70.4%* | – | – |

**T2, drought state-years only**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual |
|---|---|---|---|---|---|---|---|
| D Tweedie GLM | 1,847k ac | 5,541k ac | 2,337k ac | 0.65 | **40.9%** | 0.748 | 0.50 |
| B2a USDA binary trigger | 1,748k ac | 5,244k ac | 2,525k ac | 0.84 | 28.0% | 0.426 | 0.53 |
| B2b tiered LFP-style trigger | 2,321k ac | 4,994k ac | 3,430k ac | 0.87 | 35.1% | 0.415 | 0.73 |
| A hurdle | 2,628k ac | 7,884k ac | 2,910k ac | 0.76 | 39.6% | 0.793 | 0.29 |
| B boosting | 1,903k ac | 5,708k ac | 2,894k ac | **0.63** | 40.9% | 0.746 | 0.49 |
| C look-alikes | 1,668k ac | 5,005k ac | 2,310k ac | 0.68 | 37.5% | **0.823** | 0.55 |
| B1 drought-bin average | **1,211k ac** | 3,632k ac | **2,040k ac** | 0.70 | 32.3% | 0.570 | 0.67 |
| B3 liability only | 2,556k ac | 7,668k ac | 3,136k ac | 0.78 | 33.6% | 0.435 | 0.31 |
| B4 liability x D2+ last map | 1,373k ac | **3,211k ac** | 2,274k ac | 0.73 | 40.7% | 0.654 | **0.79** |
| Z0 predict zero | 3,701k ac | 11,104k ac | 4,659k ac | 1.00 | 23.1% | 0.500 | 0.00 |
| *Random counties / best possible* | – | – | – | – | *21.6% / 59.3%* | – | – |

**Z, all state-years**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual |
|---|---|---|---|---|---|---|---|
| D Tweedie GLM | $94.8M | $1,062.1M | $408.1M | 0.84 | **51.7%** | 0.820 | 0.93 |
| B2a USDA binary trigger | $110.8M | $1,527.4M | $389.6M | 1.09 | 25.7% | 0.575 | 0.73 |
| B2b tiered LFP-style trigger | $124.6M | $1,565.3M | $540.3M | 1.06 | 27.3% | 0.574 | 0.80 |
| A hurdle | $104.5M | $1,788.6M | $489.0M | **0.79** | 51.2% | 0.828 | 0.53 |
| B boosting | $92.9M | $1,073.3M | $450.6M | 0.83 | 49.9% | **0.865** | 0.91 |
| C look-alikes | $92.5M | $823.2M | $366.6M | 0.95 | 46.3% | 0.818 | 1.06 |
| B1 drought-bin average | $91.1M | **$730.9M** | **$331.7M** | 1.04 | 33.6% | 0.717 | 1.11 |
| B3 liability only | $164.3M | $1,508.6M | $533.0M | 1.28 | 26.6% | 0.647 | 1.09 |
| B4 liability x D2+ last map | **$70.9M** | $801.0M | $363.9M | 0.95 | 38.6% | 0.614 | **0.94** |
| Z0 predict zero | $158.1M | $3,162.1M | $729.0M | 1.00 | 20.7% | 0.500 | 0.00 |
| *Random counties / best possible* | – | – | – | – | *21.3% / 70.1%* | – | – |

**Z, drought state-years only**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual |
|---|---|---|---|---|---|---|---|
| D Tweedie GLM | $312.4M | $937.1M | $408.1M | 0.66 | 40.0% | 0.949 | 0.53 |
| B2a USDA binary trigger | $277.8M | $833.5M | $389.6M | 0.83 | 27.8% | 0.622 | 0.58 |
| B2b tiered LFP-style trigger | $411.8M | $773.6M | $540.3M | 0.90 | 33.4% | 0.601 | 0.84 |
| A hurdle | $469.8M | $1,409.5M | $489.0M | 0.76 | 37.5% | 0.955 | 0.29 |
| B boosting | $312.7M | $938.0M | $450.6M | **0.63** | **41.9%** | **0.971** | 0.53 |
| C look-alikes | $262.4M | $787.3M | $366.6M | 0.67 | 37.7% | 0.967 | 0.60 |
| B1 drought-bin average | **$186.4M** | $559.2M | **$331.7M** | 0.71 | 31.8% | 0.894 | 0.72 |
| B3 liability only | $449.8M | $1,349.5M | $533.0M | 0.77 | 31.9% | 0.938 | 0.32 |
| B4 liability x D2+ last map | $236.4M | **$464.5M** | $363.9M | 0.76 | 40.8% | 0.715 | **0.89** |
| Z0 predict zero | $662.9M | $1,988.7M | $729.0M | 1.00 | 23.9% | 0.500 | 0.00 |
| *Random counties / best possible* | – | – | – | – | *21.6% / 57.9%* | – | – |

## 4. Trigger agreement (B2a vs D Tweedie GLM; significant payout = share >= 2% of insured value)
D Tweedie GLM flags its top N counties per state-year, N = the number of counties B2a makes eligible that state-year.

| flagging rule | flagged county-crop-years | significant county-crop-years | true positives | precision | recall |
|---|---|---|---|---|---|
| B2a trigger | 650 | 592 | 272 | 0.418 | 0.459 |
| D Tweedie GLM (top N) | 655 | 592 | 306 | 0.467 | 0.517 |

|  | D Tweedie GLM high | D Tweedie GLM low |
|---|---|---|
| trigger eligible | 252 county-years, $1,633.9M | 84 county-years, $195.9M |
| trigger not eligible | 84 county-years, $506.3M | 1463 county-years, $908.3M |

Disagreement cells: model high / trigger no = 84 county-years, $506.3M total, $6.03M per county-year; model low / trigger yes = 84 county-years, $195.9M total, $2.33M per county-year. Actual payouts favoured: **model-high/trigger-no** (larger mean payout per county-year).

## 5. Known misses
State-years where B1 and all four candidates (A, B, C, D) were off by more than 50% (statewide X):

| state | year | actual $M | direction | B1 drought-bin average $M | A hurdle $M | B boosting $M | C look-alikes $M | D Tweedie GLM $M | likely reason |
|---|---|---|---|---|---|---|---|---|---|
| IA | 2016 | 1.420 | over | 77.887 | 6.095 | 24.972 | 28.996 | 21.627 | Quiet year: actual payout only 0.01% of insured $ ($1.4M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| IA | 2019 | 2.861 | over | 85.510 | 66.234 | 83.932 | 252.056 | 135.090 | Quiet year: actual payout only 0.02% of insured $ ($2.9M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| IA | 2021 | 55.931 | over | 714.065 | 266.335 | 798.435 | 635.695 | 499.699 | Quiet year: actual payout only 0.39% of insured $ ($55.9M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2019 | 1.092 | over | 19.658 | 2.585 | 6.600 | 14.334 | 9.717 | Quiet year: actual payout only 0.02% of insured $ ($1.1M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |

D Tweedie GLM's five largest dollar misses:

| state | year | actual $M | D Tweedie GLM $M | miss $M | direction | likely reason |
|---|---|---|---|---|---|---|
| NE | 2023 | 612.550 | 131.481 | -481.069 | under | Loss not visible in Aug-15 inputs (late-season drought or a loss coded to another cause). |
| IA | 2021 | 55.931 | 499.699 | 443.768 | over | Quiet year: actual payout only 0.39% of insured $ ($55.9M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| IA | 2023 | 715.965 | 479.177 | -236.788 | under | Loss not visible in Aug-15 inputs (late-season drought or a loss coded to another cause). |
| IA | 2017 | 109.081 | 338.487 | 229.406 | over | Quiet year: actual payout only 0.94% of insured $ ($109.1M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2022 | 859.965 | 639.171 | -220.794 | under | Loss not visible in Aug-15 inputs (late-season drought or a loss coded to another cause). |

## 6. Verdict vs current practice (B2a / B2b)
Across the 20 test state-years, the D Tweedie GLM budget for a state was off by $114.3M on average, against $119.8M for the USDA binary trigger (B2a) and $135.1M for the tiered trigger (B2b). In the drought years alone that average miss was $312.9M for D Tweedie GLM versus $211.8M and $417.8M, and it left $938.7M of payouts un-budgeted against $508.7M and $641.1M. For finding where the money goes, D Tweedie GLM's top 20 counties held 54.4% of actual payouts versus 26.4% and 28.5% for the triggers (a perfect ranking would hold 72.9%). Its worst single state-year shortfall was $481.1M (B2a $338.5M, B2b $373.5M), and its rough scenario range contained the actual statewide payout in 18 of 20 state-years. Against current practice this is **a mixed result**: lower statewide error in 3 of 4 comparisons and better top-20 capture in 4 of 4 (comparisons: all/B2a, all/B2b, drought/B2a, drought/B2b).
