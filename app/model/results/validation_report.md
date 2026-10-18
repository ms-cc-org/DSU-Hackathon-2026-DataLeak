# Validation report: nested-calibrated models, walk-forward 2006-2012 and validation 2013-2015

**Headline model: D Tweedie GLM** (lowest drought-year statewide absolute $ error among candidates beating B3 (0.257) and B4 (0.289) on capture; within 5% of the lowest error: ['D']; simplest wins). Everything here comes from out-of-sample years 2006-2015; `testing/` was not read and `final_test.py` has not been run.
Predictions are calibrated with NESTED factors (k for year Y comes only from earlier years' predictions and outcomes; k = 1 in 2006), and calibration is kept for a model-target
only if it lowers statewide absolute $ error (section 4). Preprocessing, B1 bins, look-alike pools and rain/irrigation averages use only earlier years (DECISIONS.md, Entries 3-4).
Wording: **X** = estimated insurance payouts (T1 x liability), **Y** = estimated deductible exposure, **Z** = illustrative relief allocation under a 95% coverage assumption (inspired by
USDA ERP 2022), not a prediction of any program payment. Raw numbers: `validation_results.csv`, `validation_state_years.csv`, `validation_predictions.csv`, `calibration.csv`, `trigger_agreement_*.csv`.

Metric definitions: *Statewide abs. error* = mean over state-years of |Σ predicted - Σ actual|; *Under-budgeted (total)* = Σ over state-years of max(0, actual - predicted); *Worst state-year
shortfall* = the largest single state-year max(0, actual - predicted); *County WAPE* = Σ|error| / Σ actual over county-years (crops summed); *Top-20 capture* = share of actual payouts in the 20
counties (crops summed) with the highest predicted payout, averaged over state-years, ties broken by county FIPS; *AUC* uses each model's own predicted amount; *Σpred/Σactual* is calibration
(<1 under-budgets). AUC inside the drought-only tables is not informative (almost every county pays in a drought year, so few zero-payout rows remain). A drought state-year = actual statewide payout >= 3% of insured $ (walk-forward: IA 2012, NE 2012; validation: IA 2013). Bold = best in column.
The historical scenario range is the 10th-90th percentile (A, B, D from whole earlier years' residuals, years < Y and at least 3 of them, so only 2009+; C from its look-alikes' spread); it is a
description of past outcomes, not a probability statement. Tuned on walk-forward only: `{"B": {"max_iter": 400, "max_depth": 3}, "C": {"k": 25, "drought_weight": 1.0}, "D": {"alpha": 0.001}}`.

## 1. Headline vs current USDA practice (B2a binary trigger, B2b tiered trigger)

Selection rule (fixed in Entry 3): lowest drought-year statewide absolute $ error among candidates beating B3 (0.257) and B4 (0.289) on capture; within 5% of the lowest error: ['D']; simplest wins.

| model | drought_stat_abs_err | capture_all | beats_B3_and_B4 |
|---|---|---|---|
| A | 456,998,925 | 0.505 | yes |
| B | 469,707,648 | 0.510 | yes |
| C | 445,213,007 | 0.435 | yes |
| D | 230,977,363 | 0.529 | yes |

**Pooled 2006-2015 (walk-forward + validation), all state-years** (20 state-years)

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual | Range coverage | Range width | Upper-bound misses |
|---|---|---|---|---|---|---|---|---|---|---|
| D Tweedie GLM | **$57.1M** | **$755.3M** | **$416.8M** | **0.66** | **52.9%** | **0.784** | **0.92** | 36% (5/14) | $170.6M | 2 |
| B2a USDA binary trigger | $166.1M | $2,521.8M | $1,358.6M | 1.02 | 26.8% | 0.594 | 0.62 | – | – | – |
| B2b tiered LFP-style trigger | $167.1M | $2,224.8M | $1,128.5M | 1.05 | 26.5% | 0.595 | 0.75 | – | – | – |
| *Random counties / best possible* | – | – | – | – | *21.5% / 77.8%* | – | – | – | – | – |

**Walk-forward 2006-2012, all state-years** (14 state-years)

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual | Range coverage | Range width | Upper-bound misses |
|---|---|---|---|---|---|---|---|---|---|---|
| D Tweedie GLM | **$44.5M** | **$265.7M** | **$262.0M** | **0.58** | **55.5%** | **0.796** | **1.03** | 12% (1/8) | $59.7M | 1 |
| B2a USDA binary trigger | $169.2M | $2,369.0M | $1,358.6M | 0.79 | 23.7% | 0.589 | 0.29 | – | – | – |
| B2b tiered LFP-style trigger | $148.9M | $2,084.9M | $1,128.5M | 0.74 | 23.5% | 0.589 | 0.38 | – | – | – |
| *Random counties / best possible* | – | – | – | – | *21.5% / 76.9%* | – | – | – | – | – |

**Validation 2013-2015, all state-years** (6 state-years)

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual | Range coverage | Range width | Upper-bound misses |
|---|---|---|---|---|---|---|---|---|---|---|
| D Tweedie GLM | **$86.5M** | $489.6M | $416.8M | **0.87** | **47.0%** | **0.779** | **0.60** | 67% (4/6) | $318.4M | 1 |
| B2a USDA binary trigger | $158.7M | $152.8M | **$79.6M** | 1.69 | 34.0% | 0.609 | 1.56 | – | – | – |
| B2b tiered LFP-style trigger | $209.7M | **$139.9M** | $79.6M | 1.96 | 33.3% | 0.603 | 1.85 | – | – | – |
| *Random counties / best possible* | – | – | – | – | *21.3% / 80.0%* | – | – | – | – | – |

**Pooled 2006-2015 (walk-forward + validation), drought state-years only** (3 state-years)

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual | Range coverage | Range width | Upper-bound misses |
|---|---|---|---|---|---|---|---|---|---|---|
| D Tweedie GLM | **$231.0M** | **$678.8M** | **$416.8M** | **0.54** | **43.2%** | 0.093 | **0.83** | 33% (1/3) | $190.9M | 2 |
| B2a USDA binary trigger | $738.0M | $2,214.1M | $1,358.6M | 0.83 | 33.4% | 0.264 | 0.44 | – | – | – |
| B2b tiered LFP-style trigger | $641.0M | $1,922.9M | $1,128.5M | 0.80 | 31.6% | **0.420** | 0.51 | – | – | – |
| *Random counties / best possible* | – | – | – | – | *21.0% / 52.8%* | – | – | – | – | – |

**Walk-forward 2006-2012, drought state-years only** (2 state-years)

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual | Range coverage | Range width | Upper-bound misses |
|---|---|---|---|---|---|---|---|---|---|---|
| D Tweedie GLM | **$138.0M** | **$262.0M** | **$262.0M** | **0.48** | **45.7%** | 0.143 | **0.92** | 50% (1/2) | $113.9M | 1 |
| B2a USDA binary trigger | $1,076.3M | $2,152.6M | $1,358.6M | 0.76 | 30.0% | 0.317 | 0.30 | – | – | – |
| B2b tiered LFP-style trigger | $937.2M | $1,874.3M | $1,128.5M | 0.70 | 30.0% | **0.467** | 0.39 | – | – | – |
| *Random counties / best possible* | – | – | – | – | *21.3% / 51.8%* | – | – | – | – | – |

**Validation 2013-2015, drought state-years only** (1 state-years)

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual | Range coverage | Range width | Upper-bound misses |
|---|---|---|---|---|---|---|---|---|---|---|
| D Tweedie GLM | $416.8M | $416.8M | $416.8M | **0.75** | 38.3% | – | 0.52 | 0% (0/1) | $344.9M | 1 |
| B2a USDA binary trigger | $61.5M | $61.5M | $61.5M | 1.10 | **40.2%** | – | 0.93 | – | – | – |
| B2b tiered LFP-style trigger | **$48.6M** | **$48.6M** | **$48.6M** | 1.13 | 34.9% | – | **0.94** | – | – | – |
| *Random counties / best possible* | – | – | – | – | *20.2% / 54.7%* | – | – | – | – | – |

## 2. All models, T1 (X: estimated insurance payouts)

**Pooled 2006-2015 (walk-forward + validation), all state-years**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual | Range coverage | Range width | Upper-bound misses |
|---|---|---|---|---|---|---|---|---|---|---|
| Z0 predict zero | $224.8M | $4,496.2M | $1,862.5M | 1.00 | 22.4% | 0.500 | 0.00 | – | – | – |
| B1 drought-bin average | $179.8M | $2,203.7M | $1,366.3M | 1.10 | 29.3% | 0.652 | 0.82 | – | – | – |
| B2a USDA binary trigger | $166.1M | $2,521.8M | $1,358.6M | 1.02 | 26.8% | 0.594 | 0.62 | – | – | – |
| B2b tiered LFP-style trigger | $167.1M | $2,224.8M | $1,128.5M | 1.05 | 26.5% | 0.595 | 0.75 | – | – | – |
| B3 liability only | $277.8M | $3,253.0M | $1,714.4M | 1.34 | 25.7% | 0.546 | 0.79 | – | – | – |
| B4 liability x D2+ last map | $106.3M | $1,649.8M | $868.3M | 0.81 | 28.9% | 0.608 | 0.74 | – | – | – |
| A hurdle | $84.6M | $1,327.3M | $700.1M | 0.67 | 50.5% | 0.784 | 0.79 | 29% (4/14) | $164.0M | 2 |
| B boosting | $87.0M | $1,523.2M | $631.5M | **0.62** | 51.0% | 0.769 | 0.71 | 21% (3/14) | $157.0M | 3 |
| C look-alikes | $93.7M | $1,400.0M | $555.9M | 0.74 | 43.5% | 0.746 | 0.79 | 85% (17/20) | $378.3M | 1 |
| D Tweedie GLM | **$57.1M** | **$755.3M** | **$416.8M** | 0.66 | **52.9%** | **0.784** | **0.92** | 36% (5/14) | $170.6M | 2 |
| *Random counties / best possible* | – | – | – | – | *21.5% / 77.8%* | – | – | – | – | – |

**Walk-forward 2006-2012, all state-years**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual | Range coverage | Range width | Upper-bound misses |
|---|---|---|---|---|---|---|---|---|---|---|
| Z0 predict zero | $239.3M | $3,349.7M | $1,862.5M | 1.00 | 22.8% | 0.500 | 0.00 | – | – | – |
| B1 drought-bin average | $187.4M | $2,160.4M | $1,366.3M | 0.89 | 31.0% | 0.685 | 0.49 | – | – | – |
| B2a USDA binary trigger | $169.2M | $2,369.0M | $1,358.6M | 0.79 | 23.7% | 0.589 | 0.29 | – | – | – |
| B2b tiered LFP-style trigger | $148.9M | $2,084.9M | $1,128.5M | 0.74 | 23.5% | 0.589 | 0.38 | – | – | – |
| B3 liability only | $286.8M | $2,833.7M | $1,714.4M | 1.24 | 29.0% | 0.561 | 0.51 | – | – | – |
| B4 liability x D2+ last map | $66.5M | $669.6M | $293.9M | 0.70 | 29.9% | 0.639 | 0.88 | – | – | – |
| A hurdle | $60.8M | $487.3M | $426.9M | 0.59 | 50.6% | **0.799** | 0.96 | 0% (0/8) | $51.2M | 1 |
| B boosting | $87.9M | $1,093.6M | $631.5M | **0.56** | 55.0% | 0.791 | 0.71 | 12% (1/8) | $31.6M | 2 |
| C look-alikes | $83.8M | $885.2M | $555.9M | 0.67 | 46.2% | 0.759 | 0.82 | 86% (12/14) | $413.4M | 0 |
| D Tweedie GLM | **$44.5M** | **$265.7M** | **$262.0M** | 0.58 | **55.5%** | 0.796 | **1.03** | 12% (1/8) | $59.7M | 1 |
| *Random counties / best possible* | – | – | – | – | *21.5% / 76.9%* | – | – | – | – | – |

**Validation 2013-2015, all state-years**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual | Range coverage | Range width | Upper-bound misses |
|---|---|---|---|---|---|---|---|---|---|---|
| Z0 predict zero | $191.1M | $1,146.5M | $868.3M | 1.00 | 21.6% | 0.500 | 0.00 | – | – | – |
| B1 drought-bin average | $162.2M | **$43.3M** | **$43.3M** | 1.70 | 25.3% | 0.618 | 1.77 | – | – | – |
| B2a USDA binary trigger | $158.7M | $152.8M | $79.6M | 1.69 | 34.0% | 0.609 | 1.56 | – | – | – |
| B2b tiered LFP-style trigger | $209.7M | $139.9M | $79.6M | 1.96 | 33.3% | 0.603 | 1.85 | – | – | – |
| B3 liability only | $256.7M | $419.3M | $419.3M | 1.64 | 18.0% | 0.500 | 1.61 | – | – | – |
| B4 liability x D2+ last map | $199.1M | $980.3M | $868.3M | 1.16 | 26.5% | 0.531 | 0.33 | – | – | – |
| A hurdle | $140.3M | $840.0M | $700.1M | 0.88 | **50.1%** | 0.759 | 0.27 | 67% (4/6) | $314.5M | 1 |
| B boosting | **$84.9M** | $429.6M | $365.8M | **0.82** | 41.5% | 0.718 | 0.69 | 33% (2/6) | $324.2M | 1 |
| C look-alikes | $117.0M | $514.7M | $468.0M | 0.97 | 37.2% | 0.726 | **0.71** | 83% (5/6) | $296.5M | 1 |
| D Tweedie GLM | $86.5M | $489.6M | $416.8M | 0.87 | 47.0% | **0.779** | 0.60 | 67% (4/6) | $318.4M | 1 |
| *Random counties / best possible* | – | – | – | – | *21.3% / 80.0%* | – | – | – | – | – |

**Pooled 2006-2015 (walk-forward + validation), drought state-years only**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual | Range coverage | Range width | Upper-bound misses |
|---|---|---|---|---|---|---|---|---|---|---|
| Z0 predict zero | $1,310.6M | $3,931.9M | $1,862.5M | 1.00 | 25.7% | 0.500 | 0.00 | – | – | – |
| B1 drought-bin average | $734.2M | $2,202.5M | $1,366.3M | 0.80 | 33.8% | 0.225 | 0.44 | – | – | – |
| B2a USDA binary trigger | $738.0M | $2,214.1M | $1,358.6M | 0.83 | 33.4% | 0.264 | 0.44 | – | – | – |
| B2b tiered LFP-style trigger | $641.0M | $1,922.9M | $1,128.5M | 0.80 | 31.6% | 0.420 | 0.51 | – | – | – |
| B3 liability only | $1,084.3M | $3,253.0M | $1,714.4M | 0.87 | 32.2% | **0.676** | 0.17 | – | – | – |
| B4 liability x D2+ last map | $460.9M | $1,382.6M | $868.3M | 0.69 | 28.4% | 0.324 | 0.65 | – | – | – |
| A hurdle | $457.0M | $1,127.0M | $700.1M | 0.61 | **43.7%** | 0.310 | 0.78 | 0% (0/3) | $128.5M | 2 |
| B boosting | $469.7M | $1,409.1M | $631.5M | 0.55 | 41.0% | 0.201 | 0.64 | 0% (0/3) | $166.0M | 3 |
| C look-alikes | $445.2M | $1,335.6M | $555.9M | 0.62 | 33.8% | 0.374 | 0.66 | 67% (2/3) | $1,719.0M | 1 |
| D Tweedie GLM | **$231.0M** | **$678.8M** | **$416.8M** | **0.54** | 43.2% | 0.093 | **0.83** | 33% (1/3) | $190.9M | 2 |
| *Random counties / best possible* | – | – | – | – | *21.0% / 52.8%* | – | – | – | – | – |

**Walk-forward 2006-2012, drought state-years only**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual | Range coverage | Range width | Upper-bound misses |
|---|---|---|---|---|---|---|---|---|---|---|
| Z0 predict zero | $1,531.8M | $3,063.6M | $1,862.5M | 1.00 | 25.9% | 0.500 | 0.00 | – | – | – |
| B1 drought-bin average | $1,079.6M | $2,159.2M | $1,366.3M | 0.76 | 32.2% | 0.222 | 0.30 | – | – | – |
| B2a USDA binary trigger | $1,076.3M | $2,152.6M | $1,358.6M | 0.76 | 30.0% | 0.317 | 0.30 | – | – | – |
| B2b tiered LFP-style trigger | $937.2M | $1,874.3M | $1,128.5M | 0.70 | 30.0% | 0.467 | 0.39 | – | – | – |
| B3 liability only | $1,416.8M | $2,833.7M | $1,714.4M | 0.93 | 30.0% | 0.500 | 0.08 | – | – | – |
| B4 liability x D2+ last map | $257.2M | $514.3M | $293.9M | 0.60 | 30.0% | 0.500 | 0.83 | – | – | – |
| A hurdle | $335.4M | $426.9M | $426.9M | 0.54 | 45.2% | 0.477 | **0.94** | 0% (0/2) | $72.8M | 1 |
| B boosting | $521.7M | $1,043.4M | $631.5M | 0.51 | 41.1% | 0.272 | 0.66 | 0% (0/2) | $67.3M | 2 |
| C look-alikes | $433.8M | $867.7M | $555.9M | 0.58 | 31.5% | **0.509** | 0.72 | 100% (2/2) | $2,183.3M | 0 |
| D Tweedie GLM | **$138.0M** | **$262.0M** | **$262.0M** | **0.48** | **45.7%** | 0.143 | 0.92 | 50% (1/2) | $113.9M | 1 |
| *Random counties / best possible* | – | – | – | – | *21.3% / 51.8%* | – | – | – | – | – |

**Validation 2013-2015, drought state-years only**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual | Range coverage | Range width | Upper-bound misses |
|---|---|---|---|---|---|---|---|---|---|---|
| Z0 predict zero | $868.3M | $868.3M | $868.3M | 1.00 | 25.2% | – | 0.00 | – | – | – |
| B1 drought-bin average | **$43.3M** | **$43.3M** | **$43.3M** | 0.93 | 37.0% | – | **0.95** | – | – | – |
| B2a USDA binary trigger | $61.5M | $61.5M | $61.5M | 1.10 | 40.2% | – | 0.93 | – | – | – |
| B2b tiered LFP-style trigger | $48.6M | $48.6M | $48.6M | 1.13 | 34.9% | – | 0.94 | – | – | – |
| B3 liability only | $419.3M | $419.3M | $419.3M | **0.66** | 36.6% | – | 0.52 | – | – | – |
| B4 liability x D2+ last map | $868.3M | $868.3M | $868.3M | 1.00 | 25.2% | – | 0.00 | – | – | – |
| A hurdle | $700.1M | $700.1M | $700.1M | 0.86 | 40.9% | – | 0.19 | 0% (0/1) | $239.9M | 1 |
| B boosting | $365.8M | $365.8M | $365.8M | 0.71 | **40.9%** | – | 0.58 | 0% (0/1) | $363.4M | 1 |
| C look-alikes | $468.0M | $468.0M | $468.0M | 0.74 | 38.4% | – | 0.46 | 0% (0/1) | $790.6M | 1 |
| D Tweedie GLM | $416.8M | $416.8M | $416.8M | 0.75 | 38.3% | – | 0.52 | 0% (0/1) | $344.9M | 1 |
| *Random counties / best possible* | – | – | – | – | *20.2% / 54.7%* | – | – | – | – | – |

**Quiet state-years only, pooled**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual | Range coverage | Range width | Upper-bound misses |
|---|---|---|---|---|---|---|---|---|---|---|
| Z0 predict zero | $33.2M | $564.4M | $166.2M | **1.00** | 21.9% | 0.500 | 0.00 | – | – | – |
| B1 drought-bin average | $82.0M | $1.2M | $1.2M | 3.15 | 28.5% | 0.603 | 3.47 | – | – | – |
| B2a USDA binary trigger | $65.1M | $307.7M | $79.6M | 2.30 | 25.6% | 0.542 | 1.87 | – | – | – |
| B2b tiered LFP-style trigger | $83.5M | $301.8M | $79.6M | 2.81 | 25.5% | 0.542 | 2.45 | – | – | – |
| B3 liability only | $135.5M | **$0.0M** | **$0.0M** | 4.66 | 24.5% | 0.606 | 5.08 | – | – | – |
| B4 liability x D2+ last map | $43.7M | $267.2M | $79.6M | 1.71 | 29.0% | 0.558 | 1.37 | – | – | – |
| A hurdle | **$18.9M** | $200.2M | $75.1M | 1.06 | 51.7% | 0.739 | **0.86** | 36% (4/11) | $173.7M | 0 |
| B boosting | $19.5M | $114.1M | $63.9M | 1.10 | 52.7% | 0.722 | 1.18 | 27% (3/11) | $154.6M | 0 |
| C look-alikes | $31.7M | $64.4M | $46.8M | 1.63 | 45.2% | 0.696 | 1.73 | 88% (15/17) | $141.7M | 0 |
| D Tweedie GLM | $26.4M | $76.5M | $55.9M | 1.48 | **54.6%** | **0.741** | 1.52 | 36% (4/11) | $165.1M | 0 |
| *Random counties / best possible* | – | – | – | – | *21.5% / 82.2%* | – | – | – | – | – |

## 3. T2 (damaged acres) and Z (illustrative relief allocation)

**T2 damaged acres: Pooled 2006-2015 (walk-forward + validation), all state-years**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual |
|---|---|---|---|---|---|---|---|
| Z0 predict zero | 1,144k ac | 22,881k ac | 8,186k ac | 1.00 | 22.4% | 0.500 | 0.00 |
| B1 drought-bin average | 920k ac | 10,475k ac | 5,683k ac | 1.06 | 30.1% | 0.649 | 0.89 |
| B2a USDA binary trigger | 791k ac | 13,389k ac | 5,584k ac | 0.91 | 26.3% | 0.593 | 0.52 |
| B2b tiered LFP-style trigger | 880k ac | 12,885k ac | 5,248k ac | 0.99 | 26.2% | 0.594 | 0.64 |
| B3 liability only | 1,344k ac | 15,773k ac | 8,002k ac | 1.29 | 28.1% | 0.562 | 0.80 |
| B4 liability x D2+ last map | 717k ac | 10,317k ac | 5,533k ac | 0.87 | 28.9% | 0.607 | 0.73 |
| A hurdle | 568k ac | 9,350k ac | 4,649k ac | 0.69 | 48.8% | 0.790 | 0.68 |
| B boosting | **374k ac** | 5,457k ac | **2,984k ac** | **0.57** | 48.6% | 0.775 | 0.85 |
| C look-alikes | 656k ac | 9,134k ac | 3,726k ac | 0.79 | 43.7% | 0.754 | 0.78 |
| D Tweedie GLM | 453k ac | **4,245k ac** | 3,309k ac | 0.71 | **51.4%** | **0.795** | **1.02** |
| *Random counties / best possible* | – | – | – | – | *21.5% / 75.1%* | – | – |

**T2 damaged acres: Validation 2013-2015, all state-years**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual |
|---|---|---|---|---|---|---|---|
| Z0 predict zero | 1,230k ac | 7,377k ac | 5,533k ac | 1.00 | 22.1% | 0.500 | 0.00 |
| B1 drought-bin average | 883k ac | **1,988k ac** | **1,988k ac** | 1.25 | 23.2% | 0.610 | 1.18 |
| B2a USDA binary trigger | 885k ac | 2,886k ac | 2,118k ac | 1.20 | 32.0% | 0.602 | **0.94** |
| B2b tiered LFP-style trigger | 1,315k ac | 3,184k ac | 2,416k ac | 1.48 | 32.8% | 0.601 | 1.21 |
| B3 liability only | 1,856k ac | 3,106k ac | 3,106k ac | 1.68 | 15.9% | 0.671 | 1.67 |
| B4 liability x D2+ last map | 1,164k ac | 6,475k ac | 5,533k ac | 1.05 | 28.1% | 0.530 | 0.19 |
| A hurdle | 959k ac | 5,752k ac | 4,649k ac | 0.87 | **45.6%** | 0.764 | 0.22 |
| B boosting | **611k ac** | 3,486k ac | 2,984k ac | **0.76** | 36.6% | 0.726 | 0.55 |
| C look-alikes | 804k ac | 3,738k ac | 3,324k ac | 0.92 | 34.7% | 0.738 | 0.64 |
| D Tweedie GLM | 691k ac | 4,000k ac | 3,309k ac | 0.83 | 42.7% | **0.782** | 0.48 |
| *Random counties / best possible* | – | – | – | – | *21.3% / 75.7%* | – | – |

**T2 damaged acres: Pooled 2006-2015 (walk-forward + validation), drought state-years only**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual |
|---|---|---|---|---|---|---|---|
| Z0 predict zero | 6,060k ac | 18,180k ac | 8,186k ac | 1.00 | 24.5% | 0.500 | 0.00 |
| B1 drought-bin average | 3,453k ac | 10,358k ac | 5,683k ac | 0.75 | 28.7% | 0.204 | 0.43 |
| B2a USDA binary trigger | 3,470k ac | 10,410k ac | 5,584k ac | 0.78 | 32.1% | 0.178 | 0.43 |
| B2b tiered LFP-style trigger | 3,345k ac | 10,035k ac | 5,248k ac | 0.76 | 31.3% | 0.420 | 0.45 |
| B3 liability only | 5,150k ac | 15,450k ac | 8,002k ac | 0.88 | 32.8% | **0.676** | 0.15 |
| B4 liability x D2+ last map | 2,664k ac | 7,992k ac | 5,533k ac | 0.66 | 29.6% | 0.324 | 0.56 |
| A hurdle | 2,498k ac | 7,493k ac | 4,649k ac | 0.57 | 38.4% | 0.350 | 0.59 |
| B boosting | 1,501k ac | 4,503k ac | **2,984k ac** | **0.45** | 40.3% | 0.360 | 0.75 |
| C look-alikes | 2,845k ac | 8,535k ac | 3,726k ac | 0.61 | 32.5% | 0.431 | 0.53 |
| D Tweedie GLM | **1,314k ac** | **3,524k ac** | 3,309k ac | 0.49 | **40.5%** | 0.175 | **0.83** |
| *Random counties / best possible* | – | – | – | – | *21.0% / 47.8%* | – | – |

**T2 damaged acres: Validation 2013-2015, drought state-years only**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual |
|---|---|---|---|---|---|---|---|
| Z0 predict zero | 5,533k ac | 5,533k ac | 5,533k ac | 1.00 | 23.3% | – | 0.00 |
| B1 drought-bin average | **1,988k ac** | **1,988k ac** | **1,988k ac** | 0.81 | 29.3% | – | **0.64** |
| B2a USDA binary trigger | 2,118k ac | 2,118k ac | 2,118k ac | 0.94 | 29.4% | – | 0.62 |
| B2b tiered LFP-style trigger | 2,416k ac | 2,416k ac | 2,416k ac | 0.95 | 29.7% | – | 0.56 |
| B3 liability only | 3,106k ac | 3,106k ac | 3,106k ac | **0.65** | 32.7% | – | 0.44 |
| B4 liability x D2+ last map | 5,533k ac | 5,533k ac | 5,533k ac | 1.00 | 23.3% | – | 0.00 |
| A hurdle | 4,649k ac | 4,649k ac | 4,649k ac | 0.86 | **35.0%** | – | 0.16 |
| B boosting | 2,984k ac | 2,984k ac | 2,984k ac | 0.70 | 33.6% | – | 0.46 |
| C look-alikes | 3,324k ac | 3,324k ac | 3,324k ac | 0.73 | 24.4% | – | 0.40 |
| D Tweedie GLM | 3,309k ac | 3,309k ac | 3,309k ac | 0.75 | 34.2% | – | 0.40 |
| *Random counties / best possible* | – | – | – | – | *20.2% / 46.9%* | – | – |

**Z illustrative relief allocation, 95% coverage assumption: Pooled 2006-2015 (walk-forward + validation), all state-years**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual |
|---|---|---|---|---|---|---|---|
| Z0 predict zero | $169.4M | $3,387.5M | $1,330.3M | 1.00 | 23.1% | 0.500 | 0.00 |
| B1 drought-bin average | $130.8M | $1,647.5M | $948.0M | 1.01 | 30.8% | 0.753 | 0.80 |
| B2a USDA binary trigger | $118.1M | $1,957.2M | $927.5M | 0.91 | 26.5% | 0.599 | 0.54 |
| B2b tiered LFP-style trigger | $134.4M | $1,889.2M | $874.3M | 0.99 | 26.8% | 0.599 | 0.68 |
| B3 liability only | $188.3M | $2,499.9M | $1,301.8M | 1.21 | 26.9% | 0.669 | 0.64 |
| B4 liability x D2+ last map | $89.3M | $1,414.4M | $730.7M | 0.80 | 29.1% | 0.610 | 0.69 |
| A hurdle | $79.3M | $1,454.0M | $618.7M | 0.64 | 48.1% | 0.845 | 0.61 |
| B boosting | **$49.9M** | $811.7M | **$423.0M** | **0.53** | 48.3% | 0.847 | 0.82 |
| C look-alikes | $89.5M | $1,377.5M | $614.7M | 0.74 | 43.3% | 0.819 | 0.71 |
| D Tweedie GLM | $53.3M | **$694.9M** | $446.0M | 0.62 | **49.7%** | **0.858** | **0.90** |
| *Random counties / best possible* | – | – | – | – | *21.5% / 74.7%* | – | – |

**Z illustrative relief allocation, 95% coverage assumption: Validation 2013-2015, all state-years**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual |
|---|---|---|---|---|---|---|---|
| Z0 predict zero | $163.6M | $981.4M | $730.7M | 1.00 | 23.2% | 0.500 | 0.00 |
| B1 drought-bin average | $124.5M | **$256.3M** | **$256.3M** | 1.27 | 25.8% | 0.754 | 1.24 |
| B2a USDA binary trigger | $125.2M | $346.7M | $265.0M | 1.27 | 33.3% | 0.616 | **1.06** |
| B2b tiered LFP-style trigger | $200.8M | $407.6M | $325.9M | 1.62 | 34.4% | 0.615 | 1.40 |
| B3 liability only | $221.9M | $413.8M | $413.8M | 1.53 | 19.4% | 0.706 | 1.51 |
| B4 liability x D2+ last map | $156.1M | $833.9M | $730.7M | 1.07 | 28.0% | 0.532 | 0.26 |
| A hurdle | $127.8M | $766.6M | $618.7M | 0.87 | **44.9%** | 0.848 | 0.22 |
| B boosting | **$83.2M** | $481.8M | $423.0M | **0.76** | 39.0% | 0.837 | 0.53 |
| C look-alikes | $110.1M | $522.4M | $474.6M | 0.90 | 36.3% | 0.810 | 0.61 |
| D Tweedie GLM | $92.7M | $540.6M | $446.0M | 0.82 | 40.2% | **0.859** | 0.47 |
| *Random counties / best possible* | – | – | – | – | *21.3% / 75.2%* | – | – |

**Z illustrative relief allocation, 95% coverage assumption: Pooled 2006-2015 (walk-forward + validation), drought state-years only**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual |
|---|---|---|---|---|---|---|---|
| Z0 predict zero | $940.4M | $2,821.1M | $1,330.3M | 1.00 | 24.8% | 0.500 | 0.00 |
| B1 drought-bin average | $542.4M | $1,627.2M | $948.0M | 0.75 | 24.8% | **1.000** | 0.42 |
| B2a USDA binary trigger | $540.9M | $1,622.7M | $927.5M | 0.77 | 28.8% | 0.672 | 0.42 |
| B2b tiered LFP-style trigger | $521.3M | $1,563.9M | $874.3M | 0.75 | 28.9% | 0.672 | 0.45 |
| B3 liability only | $817.9M | $2,453.6M | $1,301.8M | 0.89 | 28.2% | 1.000 | 0.13 |
| B4 liability x D2+ last map | $371.7M | $1,115.1M | $730.7M | 0.65 | 27.5% | 0.647 | 0.60 |
| A hurdle | $400.8M | $1,202.4M | $618.7M | 0.56 | **38.3%** | 0.950 | 0.57 |
| B boosting | $229.1M | $687.2M | **$423.0M** | **0.44** | 38.1% | 0.992 | 0.76 |
| C look-alikes | $434.0M | $1,301.9M | $614.7M | 0.60 | 29.4% | 0.997 | 0.54 |
| D Tweedie GLM | **$198.8M** | **$596.4M** | $446.0M | 0.47 | 36.7% | 0.972 | **0.79** |
| *Random counties / best possible* | – | – | – | – | *21.0% / 46.8%* | – | – |

**Z illustrative relief allocation, 95% coverage assumption: Validation 2013-2015, drought state-years only**

| Model | Statewide abs. error | Under-budgeted (total) | Worst state-year shortfall | County WAPE | Top-20 capture | AUC | Σpred/Σactual |
|---|---|---|---|---|---|---|---|
| Z0 predict zero | $730.7M | $730.7M | $730.7M | 1.00 | 23.1% | – | 0.00 |
| B1 drought-bin average | **$256.3M** | **$256.3M** | **$256.3M** | 0.82 | 25.0% | – | **0.65** |
| B2a USDA binary trigger | $265.0M | $265.0M | $265.0M | 0.95 | 27.1% | – | 0.64 |
| B2b tiered LFP-style trigger | $325.9M | $325.9M | $325.9M | 0.94 | 27.3% | – | 0.55 |
| B3 liability only | $413.8M | $413.8M | $413.8M | **0.65** | 25.3% | – | 0.43 |
| B4 liability x D2+ last map | $730.7M | $730.7M | $730.7M | 1.00 | 23.1% | – | 0.00 |
| A hurdle | $618.7M | $618.7M | $618.7M | 0.86 | **34.2%** | – | 0.15 |
| B boosting | $423.0M | $423.0M | $423.0M | 0.71 | 30.3% | – | 0.42 |
| C look-alikes | $474.6M | $474.6M | $474.6M | 0.73 | 22.5% | – | 0.35 |
| D Tweedie GLM | $446.0M | $446.0M | $446.0M | 0.74 | 28.7% | – | 0.39 |
| *Random counties / best possible* | – | – | – | – | *20.2% / 45.7%* | – | – |

## 4. Nested calibration

k for year Y = Σ actual / Σ predicted over earlier out-of-sample years. Calibration is applied to a model-target only if it lowers its statewide absolute error over 2006-2015 (uncalibrated vs nested-calibrated shown). `k_latest` (all of 2006-2015) is what `budget.py` uses for new years.

| model | target | use_calibration | raw_stat_abs_err | nested_stat_abs_err | k_latest | k_applied_to_new_years |
|---|---|---|---|---|---|---|
| Z0 predict zero | t1 | no | $224.8M | $224.8M | 1 | 1 |
| Z0 predict zero | t2 | no | 1,144k ac | 1,144k ac | 1 | 1 |
| B1 drought-bin average | t1 | no | $179.8M | $284.4M | 1.220 | 1 |
| B1 drought-bin average | t2 | no | 920k ac | 970k ac | 1.126 | 1 |
| B2a USDA binary trigger | t1 | no | $166.1M | $289.7M | 1.621 | 1 |
| B2a USDA binary trigger | t2 | no | 791k ac | 1,182k ac | 1.920 | 1 |
| B2b tiered LFP-style trigger | t1 | no | $167.1M | $306.8M | 1.327 | 1 |
| B2b tiered LFP-style trigger | t2 | no | 880k ac | 1,253k ac | 1.556 | 1 |
| B3 liability only | t1 | no | $277.8M | $278.2M | 1.268 | 1 |
| B3 liability only | t2 | yes | 1,422k ac | 1,344k ac | 1.094 | 1.094 |
| B4 liability x D2+ last map | t1 | yes | $125.7M | $106.3M | 0.938 | 0.938 |
| B4 liability x D2+ last map | t2 | yes | 938k ac | 717k ac | 0.861 | 0.861 |
| A hurdle | t1 | yes | $106.8M | $84.6M | 0.943 | 0.943 |
| A hurdle | t2 | yes | 608k ac | 568k ac | 0.956 | 0.956 |
| B boosting | t1 | no | $87.0M | $106.2M | 1.409 | 1 |
| B boosting | t2 | no | 374k ac | 558k ac | 1.177 | 1 |
| C look-alikes | t1 | no | $93.7M | $143.7M | 1.259 | 1 |
| C look-alikes | t2 | no | 656k ac | 821k ac | 1.290 | 1 |
| D Tweedie GLM | t1 | no | $57.1M | $127.9M | 1.089 | 1 |
| D Tweedie GLM | t2 | no | 453k ac | 793k ac | 0.976 | 1 |

## 5. Historical scenario range (10th-90th percentile; rough)

Coverage by state-year type, pooled 2006-2015 (A, B, D have ranges only from 2009):

| model | state-years | n | inside | coverage | mean width | actual above upper bound | actual below lower bound |
|---|---|---|---|---|---|---|---|
| A hurdle | all | 14 | 4 | 29% | $164.0M | 2 | 8 |
| A hurdle | drought | 3 | 0 | 0% | $128.5M | 2 | 1 |
| A hurdle | quiet | 11 | 4 | 36% | $173.7M | 0 | 7 |
| B boosting | all | 14 | 3 | 21% | $157.0M | 3 | 8 |
| B boosting | drought | 3 | 0 | 0% | $166.0M | 3 | 0 |
| B boosting | quiet | 11 | 3 | 27% | $154.6M | 0 | 8 |
| C look-alikes | all | 20 | 17 | 85% | $378.3M | 1 | 2 |
| C look-alikes | drought | 3 | 2 | 67% | $1,719.0M | 1 | 0 |
| C look-alikes | quiet | 17 | 15 | 88% | $141.7M | 0 | 2 |
| D Tweedie GLM | all | 14 | 5 | 36% | $170.6M | 2 | 7 |
| D Tweedie GLM | drought | 3 | 1 | 33% | $190.9M | 2 | 0 |
| D Tweedie GLM | quiet | 11 | 4 | 36% | $165.1M | 0 | 7 |

Best-covering method (closest to 80% overall): **C**. The budget range is that method's range widened to contain D Tweedie GLM's point estimate: it contained the actual statewide payout in 17 of 20 state-years; the headline point estimate was inside the raw range in 20 of 20 (widened in 0). Upper-bound misses (actual above the range) are the costly ones for a budget: see the column above.

### Statewide X per state-year ($M): actual, headline, USDA triggers and the other candidates

| state | year | type | actual X $M | D Tweedie GLM $M | B2a USDA binary trigger $M | B2b tiered LFP-style trigger $M | A hurdle $M | B boosting $M | C look-alikes $M | budget range $M | actual vs range |
|---|---|---|---|---|---|---|---|---|---|---|---|
| IA | 2006 | quiet | 48.1 | 155.3 | 0.0 | 0.0 | 103.6 | 96.7 | 82.3 | 6.0–223.0 | inside ✓ |
| IA | 2007 | quiet | 34.9 | 40.0 | 0.0 | 0.0 | 10.1 | 31.5 | 35.0 | 2.5–95.9 | inside ✓ |
| IA | 2008 | quiet | 25.1 | 21.3 | 0.0 | 0.0 | 4.7 | 10.9 | 11.1 | 0.0–34.3 | inside ✓ |
| IA | 2009 | quiet | 1.5 | 22.8 | 0.0 | 0.0 | 3.3 | 5.9 | 19.0 | 2.0–47.5 | outside ✗ |
| IA | 2010 | quiet | 0.1 | 5.3 | 0.0 | 0.0 | 1.7 | 6.8 | 7.3 | 0.1–20.2 | inside ✓ |
| IA | 2011 | quiet | 64.7 | 168.3 | 0.0 | 0.0 | 83.1 | 48.5 | 107.3 | 5.8–297.4 | inside ✓ |
| IA | 2012 | drought | 1,862.5 | 1,876.7 | 503.9 | 734.0 | 2,106.5 | 1,231.0 | 1,306.6 | 339.9–2,786.6 | inside ✓ |
| IA | 2013 | drought | 868.3 | 451.5 | 806.8 | 819.7 | 168.2 | 502.6 | 400.3 | 67.1–857.6 | outside ✗ |
| IA | 2014 | quiet | 79.6 | 23.7 | 0.0 | 0.0 | 4.4 | 15.7 | 32.8 | 0.5–81.5 | inside ✓ |
| IA | 2015 | quiet | 3.8 | 20.2 | 0.0 | 0.0 | 5.7 | 11.1 | 38.6 | 0.5–103.7 | inside ✓ |
| NE | 2006 | quiet | 64.5 | 91.1 | 56.4 | 63.5 | 75.1 | 86.0 | 159.0 | 16.4–402.0 | inside ✓ |
| NE | 2007 | quiet | 10.3 | 21.1 | 6.0 | 7.7 | 16.9 | 25.1 | 38.3 | 3.4–93.6 | inside ✓ |
| NE | 2008 | quiet | 27.9 | 28.4 | 7.4 | 4.3 | 12.6 | 11.5 | 24.2 | 0.7–60.2 | inside ✓ |
| NE | 2009 | quiet | 2.1 | 23.5 | 0.0 | 0.0 | 8.8 | 15.0 | 30.6 | 2.7–78.3 | outside ✗ |
| NE | 2010 | quiet | 0.9 | 5.6 | 0.0 | 0.0 | 1.8 | 8.2 | 13.3 | 0.4–33.7 | inside ✓ |
| NE | 2011 | quiet | 6.0 | 42.4 | 0.0 | 0.0 | 23.3 | 26.8 | 28.4 | 1.6–76.8 | inside ✓ |
| NE | 2012 | drought | 1,201.0 | 939.1 | 407.1 | 455.2 | 774.2 | 789.2 | 889.3 | 196.5–2,116.4 | inside ✓ |
| NE | 2013 | quiet | 166.2 | 151.0 | 846.4 | 1,173.0 | 115.7 | 213.4 | 278.9 | 32.7–665.7 | inside ✓ |
| NE | 2014 | quiet | 20.7 | 33.7 | 140.0 | 132.0 | 12.7 | 45.0 | 59.5 | 2.8–149.8 | inside ✓ |
| NE | 2015 | quiet | 7.9 | 6.3 | 0.0 | 0.0 | 1.8 | 9.1 | 8.9 | 0.0–24.1 | inside ✓ |

## 6. Feature ablation: B with the old features vs the new features

Old = the pre-revision column list (corrected map cutoff, prior-year normals); new = old + d0/d1 last-map shares, 4-week changes in D1+ and DSCI, 30-day precip ratio. Same hyper-parameters, nested calibration as in B.

| features | split | state-years | statewide abs. error | county WAPE | top-20 capture | AUC | Σpred/Σactual |
|---|---|---|---|---|---|---|---|
| B new features | pooled | all | $87.0M | 0.622 | 51.0% | 0.769 | 0.71 |
| B new features | pooled | drought | $469.7M | 0.554 | 41.0% | 0.201 | 0.64 |
| B new features | validation | all | $84.9M | 0.817 | 41.5% | 0.718 | 0.69 |
| B new features | validation | drought | $365.8M | 0.713 | 40.9% | nan | 0.58 |
| B old features | pooled | all | $73.1M | 0.702 | 43.4% | 0.760 | 0.89 |
| B old features | pooled | drought | $302.5M | 0.601 | 35.3% | 0.272 | 0.80 |
| B old features | validation | all | $137.2M | 0.964 | 32.5% | 0.689 | 0.65 |
| B old features | validation | drought | $546.5M | 0.783 | 29.7% | nan | 0.37 |

## 7. Trigger agreement: B2a vs the headline model

Significant payout = drought payout share >= 2% of insured value in a county-crop-year. The model flags its top N counties of each state-year by predicted payout, N = the number of counties B2a makes eligible that state-year (crops summed; ties by FIPS). Precision / recall are over county-crop-years; the 2x2 counts county-years (crops summed) and their actual drought payouts.

**Pooled 2006-2015 (walk-forward + validation)**

| flagging rule | flagged county-crop-years | significant county-crop-years | true positives | precision | recall |
|---|---|---|---|---|---|
| B2a trigger | 675 | 647 | 379 | 0.561 | 0.586 |
| D Tweedie GLM (top N) | 695 | 647 | 388 | 0.558 | 0.600 |

|  | D Tweedie GLM high | D Tweedie GLM low |
|---|---|---|
| trigger eligible | 279 county-years, $3,163.6M | 79 county-years, $189.0M |
| trigger not eligible | 79 county-years, $408.3M | 1434 county-years, $735.3M |

Disagreement cells: model high / trigger no = 79 county-years, $408.3M total, $5.17M per county-year; model low / trigger yes = 79 county-years, $189.0M total, $2.39M per county-year. Actual payouts favoured: **model-high/trigger-no** (larger mean payout per county-year).

**Walk-forward 2006-2012**

| flagging rule | flagged county-crop-years | significant county-crop-years | true positives | precision | recall |
|---|---|---|---|---|---|
| B2a trigger | 402 | 447 | 300 | 0.746 | 0.671 |
| D Tweedie GLM (top N) | 419 | 447 | 309 | 0.737 | 0.691 |

|  | D Tweedie GLM high | D Tweedie GLM low |
|---|---|---|
| trigger eligible | 161 county-years, $2,619.3M | 55 county-years, $124.8M |
| trigger not eligible | 55 county-years, $299.2M | 1036 county-years, $306.4M |

Disagreement cells: model high / trigger no = 55 county-years, $299.2M total, $5.44M per county-year; model low / trigger yes = 55 county-years, $124.8M total, $2.27M per county-year. Actual payouts favoured: **model-high/trigger-no** (larger mean payout per county-year).

**Validation 2013-2015**

| flagging rule | flagged county-crop-years | significant county-crop-years | true positives | precision | recall |
|---|---|---|---|---|---|
| B2a trigger | 273 | 200 | 79 | 0.289 | 0.395 |
| D Tweedie GLM (top N) | 276 | 200 | 79 | 0.286 | 0.395 |

|  | D Tweedie GLM high | D Tweedie GLM low |
|---|---|---|
| trigger eligible | 118 county-years, $544.3M | 24 county-years, $64.3M |
| trigger not eligible | 24 county-years, $109.1M | 398 county-years, $428.9M |

Disagreement cells: model high / trigger no = 24 county-years, $109.1M total, $4.55M per county-year; model low / trigger yes = 24 county-years, $64.3M total, $2.68M per county-year. Actual payouts favoured: **model-high/trigger-no** (larger mean payout per county-year).

## 8. Known misses

State-years where B1 and all four candidates (A, B, C, D) were off by more than 50% (statewide X):

| state | year | actual $M | direction | B1 drought-bin average $M | A hurdle $M | B boosting $M | C look-alikes $M | D Tweedie GLM $M | likely reason |
|---|---|---|---|---|---|---|---|---|---|
| IA | 2006 | 48.074 | over | 89.075 | 103.575 | 96.741 | 82.333 | 155.278 | Quiet year: actual payout only 1.07% of insured $ ($48.1M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| IA | 2009 | 1.542 | over | 55.296 | 3.284 | 5.949 | 18.982 | 22.841 | Quiet year: actual payout only 0.02% of insured $ ($1.5M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| IA | 2010 | 0.103 | over | 48.353 | 1.711 | 6.800 | 7.341 | 5.269 | Quiet year: actual payout only 0.00% of insured $ ($0.1M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| IA | 2014 | 79.575 | mixed | 152.570 | 4.443 | 15.700 | 32.793 | 23.666 | Models disagree in sign; payout depends on local conditions the Aug-15 inputs only weakly capture. |
| IA | 2015 | 3.763 | over | 53.270 | 5.699 | 11.067 | 38.638 | 20.231 | Quiet year: actual payout only 0.03% of insured $ ($3.8M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2007 | 10.262 | over | 52.260 | 16.918 | 25.148 | 38.329 | 21.133 | Quiet year: actual payout only 0.24% of insured $ ($10.3M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2009 | 2.149 | over | 30.842 | 8.781 | 15.042 | 30.561 | 23.504 | Quiet year: actual payout only 0.04% of insured $ ($2.1M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2010 | 0.885 | over | 25.647 | 1.814 | 8.190 | 13.349 | 5.626 | Quiet year: actual payout only 0.02% of insured $ ($0.9M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |
| NE | 2011 | 5.989 | over | 33.142 | 23.260 | 26.818 | 28.406 | 42.357 | Quiet year: actual payout only 0.08% of insured $ ($6.0M), so a small absolute miss is a large % miss; models likely over-read mild drought signals. |

**Iowa 2013 is a known limitation, not tuned for.** It is an emerging drought: D1+ already covered 34% of Iowa on the Aug 13 map (D2+ 0%), and it intensified after the forecast date (D2+ 21% on Aug 27, 42% on Sep 10). Actual X was $868M; D Tweedie GLM $451M, B2a USDA binary trigger $807M, B2b tiered LFP-style trigger $820M, A hurdle $168M, B boosting $503M, C look-alikes $400M. No feature, model or setting was changed to catch 2013. Note that B2a / B2b look close here for an unrelated reason: they trigger in {f13['trig_apr']} of {f13['n_ia']} Iowa counties only because the April-May maps still carried 2012's drought; on maps from Jun 1 on, {f13['trig_jun']} counties trigger.

The Aug 10, 2020 derecho is not treated as an expected miss: wind is not part of the drought label.

## 9. G (TabPFN v2): earlier experiment, not rerun

G was evaluated once with the pre-revision data and calibration (commit a5c10b9: old map cutoff Aug 14, in-sample k, old normals); it is not a candidate here (CPU prediction 353 s per year, MPS runs not bit-reproducible). Its T1 results then:

| split | capture_top20 | wape | auc_any_payout | calibration |
|---|---|---|---|---|
| walk-forward | 0.506 | 0.588 | 0.758 | 1 |
| validation | 0.412 | 0.941 | 0.735 | 0.690 |
| pooled | 0.478 | 0.678 | 0.748 | 0.920 |

## Appendix

### Strategy A coefficients
| feature | p_any_logit | log_share_if_cost |
|---|---|---|
| tmax_jul_mean | 2.609 | 1.225 |
| precip_30d_ratio_missing | 1.488 | 0.630 |
| precip_ratio_vs_normal_missing | 1.488 | 0.630 |
| d0_pct_last_map | 1.171 | 0.643 |
| acres_planted_prev3_mean_missing | 0.537 | -1.152 |
| heat32_days | -1.120 | -0.614 |
| d2_pct_last_map | 1.110 | 0.067 |
| irr_known | 0.988 | 0.517 |
| yield_prev5_mean_missing | 0.268 | 0.871 |
| d2_max_pct | 0.844 | 0.450 |
| irr_share_prior_mean | -0.747 | -0.758 |
| gdd | -0.701 | -0.277 |

### Tuning grid (walk-forward WAPE, uncalibrated)
| model | max_iter | max_depth | wape | k | drought_weight | alpha |
|---|---|---|---|---|---|---|
| B | 400 | 3 | 0.556 | – | – | – |
| B | 400 | 4 | 0.595 | – | – | – |
| B | 200 | 3 | 0.603 | – | – | – |
| B | 200 | 4 | 0.612 | – | – | – |
| B | 100 | 3 | 0.668 | – | – | – |
| B | 100 | 4 | 0.671 | – | – | – |
| C | – | – | 0.668 | 25 | 1 | – |
| C | – | – | 0.679 | 50 | 1 | – |
| C | – | – | 0.685 | 10 | 1 | – |
| C | – | – | 0.705 | 25 | 3 | – |
| C | – | – | 0.706 | 25 | 2 | – |
| C | – | – | 0.717 | 50 | 2 | – |
| C | – | – | 0.722 | 50 | 3 | – |
| C | – | – | 0.745 | 10 | 2 | – |
| C | – | – | 0.756 | 10 | 3 | – |
| D | – | – | 0.585 | – | – | 0.001 |
| D | – | – | 0.587 | – | – | 0.010 |
| D | – | – | 0.680 | – | – | 0.100 |
| D | – | – | 0.993 | – | – | 1 |
