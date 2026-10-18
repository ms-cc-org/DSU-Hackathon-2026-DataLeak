# Budget miss summary: statewide drought payout, official test and supporting runs

**Definitions.** Statewide = sum over all counties and both crops for that state and year. Actual = RMA drought indemnities (the T1 label, in $). *Average miss per state-year* = mean over state-years of |predicted statewide payout − actual statewide payout|.
*Miss as % of actual* = Σ|predicted − actual| ÷ Σ actual. *Miss vs Z0* = model miss ÷ Z0 miss, where Z0 predicts zero so its miss is the actual payout itself (Z0 = 100%, 1.00×); a value below 1.00× is real skill, and anything near 1.00× means the model barely beat predicting nothing.
Bold = lowest miss % among the models in the table (Z0 excluded). All numbers are computed from saved outputs (`test_state_years.csv`, `exploratory_more_years.md`); nothing was retrained or rerun.
**Periods 4-7 are supporting, not an independent test** (these years are part of the official 2016-2025 test, and periods 6-7 use models retrained after the test). Model calibration: in periods 1-5, A and B4 are the official nested-calibrated predictions as saved (D, B, C, B1, B2a and Z0 are uncalibrated); the Middle and Yours rows in periods 6-7 come from the exploratory run (uncalibrated), and the "official" rows there are exact (D and B2a are uncalibrated in the official run). Exploratory A and B4 numbers in `exploratory_more_years.md` are uncalibrated and therefore differ slightly from the official ones shown here.

## 1. Official test 2016-2025, official models (trained 2000-2015)
B0 was not part of the official run, so it has no saved predictions for 2016-2025 and is shown as n/a there; for 2022-2025 and 2024-2025 the only saved B0 numbers are the per-state averages of the exploratory run (B0 fitted on 2000-2015), marked *, with combined values and % derived from them (rounded to $0.1M).

### IA + NE combined
**Total actual payouts: $3,244.5M | state-years: 20**

Actual statewide payout per state-year: IA 2016: $1.4M, IA 2017: $109.1M, IA 2018: $25.2M, IA 2019: $2.9M, IA 2020: $213.5M, IA 2021: $55.9M, IA 2022: $257.5M, IA 2023: $716.0M, IA 2024: $58.5M, IA 2025: $14.6M, NE 2016: $10.5M, NE 2017: $36.1M, NE 2018: $11.7M, NE 2019: $1.1M, NE 2020: $55.8M, NE 2021: $94.0M, NE 2022: $860.0M, NE 2023: $612.5M, NE 2024: $77.3M, NE 2025: $30.9M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (headline) | 114.3 | 70% | 0.70× |
| A hurdle | 106.9 | 66% | 0.66× |
| B boosting | 106.0 | 65% | 0.65× |
| C look-alikes | 119.0 | 73% | 0.73× |
| B0 state x crop mean | n/a | n/a | n/a |
| B1 drought-bin average | 133.4 | 82% | 0.82× |
| B2a USDA binary trigger | 119.8 | 74% | 0.74× |
| B4 liability x D2+ last map | **95.1** | **59%** | **0.59×** |
| Z0 predict zero (control) | 162.2 | 100% | 1.00× |

### Iowa
**Total actual payouts: $1,454.5M | state-years: 10**

Actual statewide payout per state-year: IA 2016: $1.4M, IA 2017: $109.1M, IA 2018: $25.2M, IA 2019: $2.9M, IA 2020: $213.5M, IA 2021: $55.9M, IA 2022: $257.5M, IA 2023: $716.0M, IA 2024: $58.5M, IA 2025: $14.6M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (headline) | 142.2 | 98% | 0.98× |
| A hurdle | **81.1** | **56%** | **0.56×** |
| B boosting | 144.3 | 99% | 0.99× |
| C look-alikes | 167.0 | 115% | 1.15× |
| B0 state x crop mean | n/a | n/a | n/a |
| B1 drought-bin average | 184.4 | 127% | 1.27× |
| B2a USDA binary trigger | 133.6 | 92% | 0.92× |
| B4 liability x D2+ last map | 131.8 | 91% | 0.91× |
| Z0 predict zero (control) | 145.4 | 100% | 1.00× |

### Nebraska
**Total actual payouts: $1,790.0M | state-years: 10**

Actual statewide payout per state-year: NE 2016: $10.5M, NE 2017: $36.1M, NE 2018: $11.7M, NE 2019: $1.1M, NE 2020: $55.8M, NE 2021: $94.0M, NE 2022: $860.0M, NE 2023: $612.5M, NE 2024: $77.3M, NE 2025: $30.9M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (headline) | 86.4 | 48% | 0.48× |
| A hurdle | 132.6 | 74% | 0.74× |
| B boosting | 67.7 | 38% | 0.38× |
| C look-alikes | 71.1 | 40% | 0.40× |
| B0 state x crop mean | n/a | n/a | n/a |
| B1 drought-bin average | 82.5 | 46% | 0.46× |
| B2a USDA binary trigger | 106.0 | 59% | 0.59× |
| B4 liability x D2+ last map | **58.4** | **33%** | **0.33×** |
| Z0 predict zero (control) | 179.0 | 100% | 1.00× |

## 2. Official test, drought state-years only (IA 2023, NE 2022, NE 2023)
A state-year is a drought state-year when the actual statewide payout is at least 3% of insured dollars.

### IA + NE combined
**Total actual payouts: $2,188.5M | state-years: 3**

Actual statewide payout per state-year: IA 2023: $716.0M, NE 2022: $860.0M, NE 2023: $612.5M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (headline) | 312.9 | 43% | 0.43× |
| A hurdle | 518.7 | 71% | 0.71× |
| B boosting | 273.7 | 38% | 0.38× |
| C look-alikes | 210.7 | 29% | 0.29× |
| B0 state x crop mean | n/a | n/a | n/a |
| B1 drought-bin average | 192.4 | 26% | 0.26× |
| B2a USDA binary trigger | 211.8 | 29% | 0.29× |
| B4 liability x D2+ last map | **180.7** | **25%** | **0.25×** |
| Z0 predict zero (control) | 729.5 | 100% | 1.00× |

### Iowa
**Total actual payouts: $716.0M | state-years: 1**

Actual statewide payout per state-year: IA 2023: $716.0M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (headline) | 236.8 | 33% | 0.33× |
| A hurdle | 346.0 | 48% | 0.48× |
| B boosting | 263.3 | 37% | 0.37× |
| C look-alikes | 142.6 | 20% | 0.20× |
| B0 state x crop mean | n/a | n/a | n/a |
| B1 drought-bin average | 186.8 | 26% | 0.26× |
| B2a USDA binary trigger | 170.2 | 24% | 0.24× |
| B4 liability x D2+ last map | **123.3** | **17%** | **0.17×** |
| Z0 predict zero (control) | 716.0 | 100% | 1.00× |

### Nebraska
**Total actual payouts: $1,472.5M | state-years: 2**

Actual statewide payout per state-year: NE 2022: $860.0M, NE 2023: $612.5M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (headline) | 350.9 | 48% | 0.48× |
| A hurdle | 605.1 | 82% | 0.82× |
| B boosting | 279.0 | 38% | 0.38× |
| C look-alikes | 244.7 | 33% | 0.33× |
| B0 state x crop mean | n/a | n/a | n/a |
| B1 drought-bin average | **195.2** | **27%** | **0.27×** |
| B2a USDA binary trigger | 232.6 | 32% | 0.32× |
| B4 liability x D2+ last map | 209.5 | 28% | 0.28× |
| Z0 predict zero (control) | 736.3 | 100% | 1.00× |

## 3. Official test, quiet state-years only (the other 17)

### IA + NE combined
**Total actual payouts: $1,056.0M | state-years: 17**

Actual statewide payout per state-year: IA 2016: $1.4M, IA 2017: $109.1M, IA 2018: $25.2M, IA 2019: $2.9M, IA 2020: $213.5M, IA 2021: $55.9M, IA 2022: $257.5M, IA 2024: $58.5M, IA 2025: $14.6M, NE 2016: $10.5M, NE 2017: $36.1M, NE 2018: $11.7M, NE 2019: $1.1M, NE 2020: $55.8M, NE 2021: $94.0M, NE 2024: $77.3M, NE 2025: $30.9M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (headline) | 79.3 | 128% | 1.28× |
| A hurdle | **34.2** | **55%** | **0.55×** |
| B boosting | 76.4 | 123% | 1.23× |
| C look-alikes | 102.9 | 166% | 1.66× |
| B0 state x crop mean | n/a | n/a | n/a |
| B1 drought-bin average | 123.1 | 198% | 1.98× |
| B2a USDA binary trigger | 103.6 | 167% | 1.67× |
| B4 liability x D2+ last map | 80.0 | 129% | 1.29× |
| Z0 predict zero (control) | 62.1 | 100% | 1.00× |

### Iowa
**Total actual payouts: $738.5M | state-years: 9**

Actual statewide payout per state-year: IA 2016: $1.4M, IA 2017: $109.1M, IA 2018: $25.2M, IA 2019: $2.9M, IA 2020: $213.5M, IA 2021: $55.9M, IA 2022: $257.5M, IA 2024: $58.5M, IA 2025: $14.6M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (headline) | 131.7 | 161% | 1.61× |
| A hurdle | **51.7** | **63%** | **0.63×** |
| B boosting | 131.1 | 160% | 1.60× |
| C look-alikes | 169.7 | 207% | 2.07× |
| B0 state x crop mean | n/a | n/a | n/a |
| B1 drought-bin average | 184.2 | 224% | 2.24× |
| B2a USDA binary trigger | 129.6 | 158% | 1.58× |
| B4 liability x D2+ last map | 132.8 | 162% | 1.62× |
| Z0 predict zero (control) | 82.1 | 100% | 1.00× |

### Nebraska
**Total actual payouts: $317.5M | state-years: 8**

Actual statewide payout per state-year: NE 2016: $10.5M, NE 2017: $36.1M, NE 2018: $11.7M, NE 2019: $1.1M, NE 2020: $55.8M, NE 2021: $94.0M, NE 2024: $77.3M, NE 2025: $30.9M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (headline) | 20.3 | 51% | 0.51× |
| A hurdle | **14.5** | **37%** | **0.37×** |
| B boosting | 14.9 | 37% | 0.37× |
| C look-alikes | 27.6 | 70% | 0.70× |
| B0 state x crop mean | n/a | n/a | n/a |
| B1 drought-bin average | 54.3 | 137% | 1.37× |
| B2a USDA binary trigger | 74.4 | 187% | 1.87× |
| B4 liability x D2+ last map | 20.7 | 52% | 0.52× |
| Z0 predict zero (control) | 39.7 | 100% | 1.00× |

## 4. Supporting, not an independent test: 2022-2025, official models
B0 was not part of the official run, so it has no saved predictions for 2016-2025 and is shown as n/a there; for 2022-2025 and 2024-2025 the only saved B0 numbers are the per-state averages of the exploratory run (B0 fitted on 2000-2015), marked *, with combined values and % derived from them (rounded to $0.1M).

### IA + NE combined
**Total actual payouts: $2,627.2M | state-years: 8**

Actual statewide payout per state-year: IA 2022: $257.5M, IA 2023: $716.0M, IA 2024: $58.5M, IA 2025: $14.6M, NE 2022: $860.0M, NE 2023: $612.5M, NE 2024: $77.3M, NE 2025: $30.9M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (headline) | 150.4 | 46% | 0.46× |
| A hurdle | 209.5 | 64% | 0.64× |
| B boosting | 126.6 | 39% | 0.39× |
| C look-alikes | 103.5 | 32% | 0.32× |
| B0 state x crop mean * | 301.9 | 92% | 0.92× |
| B1 drought-bin average | 200.3 | 61% | 0.61× |
| B2a USDA binary trigger | 180.6 | 55% | 0.55× |
| B4 liability x D2+ last map | **103.2** | **31%** | **0.31×** |
| Z0 predict zero (control) | 328.4 | 100% | 1.00× |

### Iowa
**Total actual payouts: $1,046.5M | state-years: 4**

Actual statewide payout per state-year: IA 2022: $257.5M, IA 2023: $716.0M, IA 2024: $58.5M, IA 2025: $14.6M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (headline) | 115.7 | 44% | 0.44× |
| A hurdle | 102.1 | 39% | 0.39× |
| B boosting | 103.4 | 40% | 0.40× |
| C look-alikes | **73.6** | **28%** | **0.28×** |
| B0 state x crop mean * | 288.5 | 110% | 1.10× |
| B1 drought-bin average | 209.4 | 80% | 0.80× |
| B2a USDA binary trigger | 137.8 | 53% | 0.53× |
| B4 liability x D2+ last map | 80.4 | 31% | 0.31× |
| Z0 predict zero (control) | 261.6 | 100% | 1.00× |

### Nebraska
**Total actual payouts: $1,580.7M | state-years: 4**

Actual statewide payout per state-year: NE 2022: $860.0M, NE 2023: $612.5M, NE 2024: $77.3M, NE 2025: $30.9M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (headline) | 185.1 | 47% | 0.47× |
| A hurdle | 316.9 | 80% | 0.80× |
| B boosting | 149.8 | 38% | 0.38× |
| C look-alikes | 133.3 | 34% | 0.34× |
| B0 state x crop mean * | 315.2 | 80% | 0.80× |
| B1 drought-bin average | 191.3 | 48% | 0.48× |
| B2a USDA binary trigger | 223.5 | 57% | 0.57× |
| B4 liability x D2+ last map | **126.0** | **32%** | **0.32×** |
| Z0 predict zero (control) | 395.2 | 100% | 1.00× |

## 5. Supporting, not an independent test: 2024-2025, official models
B0 was not part of the official run, so it has no saved predictions for 2016-2025 and is shown as n/a there; for 2022-2025 and 2024-2025 the only saved B0 numbers are the per-state averages of the exploratory run (B0 fitted on 2000-2015), marked *, with combined values and % derived from them (rounded to $0.1M).

### IA + NE combined
**Total actual payouts: $181.3M | state-years: 4**

Actual statewide payout per state-year: IA 2024: $58.5M, IA 2025: $14.6M, NE 2024: $77.3M, NE 2025: $30.9M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (headline) | **14.0** | **31%** | **0.31×** |
| A hurdle | 26.3 | 58% | 0.58× |
| B boosting | 15.9 | 35% | 0.35× |
| C look-alikes | 15.7 | 35% | 0.35× |
| B0 state x crop mean * | 275.8 | 608% | 6.08× |
| B1 drought-bin average | 229.1 | 506% | 5.06× |
| B2a USDA binary trigger | 192.2 | 424% | 4.24× |
| B4 liability x D2+ last map | 39.5 | 87% | 0.87× |
| Z0 predict zero (control) | 45.3 | 100% | 1.00× |

### Iowa
**Total actual payouts: $73.0M | state-years: 2**

Actual statewide payout per state-year: IA 2024: $58.5M, IA 2025: $14.6M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (headline) | **8.7** | **24%** | **0.24×** |
| A hurdle | 24.0 | 66% | 0.66× |
| B boosting | 11.1 | 31% | 0.31× |
| C look-alikes | 9.5 | 26% | 0.26× |
| B0 state x crop mean * | 354.4 | 970% | 9.70× |
| B1 drought-bin average | 270.8 | 741% | 7.41× |
| B2a USDA binary trigger | 170.1 | 466% | 4.66× |
| B4 liability x D2+ last map | 36.5 | 100% | 1.00× |
| Z0 predict zero (control) | 36.5 | 100% | 1.00× |

### Nebraska
**Total actual payouts: $108.2M | state-years: 2**

Actual statewide payout per state-year: NE 2024: $77.3M, NE 2025: $30.9M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (headline) | **19.2** | **36%** | **0.36×** |
| A hurdle | 28.6 | 53% | 0.53× |
| B boosting | 20.7 | 38% | 0.38× |
| C look-alikes | 21.9 | 40% | 0.40× |
| B0 state x crop mean * | 197.1 | 364% | 3.64× |
| B1 drought-bin average | 187.5 | 346% | 3.46× |
| B2a USDA binary trigger | 214.3 | 396% | 3.96× |
| B4 liability x D2+ last map | 42.6 | 79% | 0.79× |
| Z0 predict zero (control) | 54.1 | 100% | 1.00× |

*Middle and Yours values are derived from the per-state averages saved in `exploratory_more_years.md` (rounded to $0.1M; combined = sum of the states' misses ÷ the number of state-years); Z0 is exact.*

## 6. Supporting, not an independent test: 2022-2025, Middle window next to the official models

### IA + NE combined
**Total actual payouts: $2,627.2M | state-years: 8**

Actual statewide payout per state-year: IA 2022: $257.5M, IA 2023: $716.0M, IA 2024: $58.5M, IA 2025: $14.6M, NE 2022: $860.0M, NE 2023: $612.5M, NE 2024: $77.3M, NE 2025: $30.9M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (official, trained 2000-2015) | **150.4** | **46%** | **0.46×** |
| D Tweedie GLM (Middle, trained 2000-2021) | 184.2 | 56% | 0.56× |
| B2a USDA binary trigger (official, trained 2000-2015) | 180.6 | 55% | 0.55× |
| B2a USDA binary trigger (Middle, trained 2000-2021) | 184.0 | 56% | 0.56× |
| Z0 predict zero (control) | 328.4 | 100% | 1.00× |

### Iowa
**Total actual payouts: $1,046.5M | state-years: 4**

Actual statewide payout per state-year: IA 2022: $257.5M, IA 2023: $716.0M, IA 2024: $58.5M, IA 2025: $14.6M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (official, trained 2000-2015) | **115.7** | **44%** | **0.44×** |
| D Tweedie GLM (Middle, trained 2000-2021) | 137.9 | 53% | 0.53× |
| B2a USDA binary trigger (official, trained 2000-2015) | 137.8 | 53% | 0.53× |
| B2a USDA binary trigger (Middle, trained 2000-2021) | 146.6 | 56% | 0.56× |
| Z0 predict zero (control) | 261.6 | 100% | 1.00× |

### Nebraska
**Total actual payouts: $1,580.7M | state-years: 4**

Actual statewide payout per state-year: NE 2022: $860.0M, NE 2023: $612.5M, NE 2024: $77.3M, NE 2025: $30.9M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (official, trained 2000-2015) | **185.1** | **47%** | **0.47×** |
| D Tweedie GLM (Middle, trained 2000-2021) | 230.6 | 58% | 0.58× |
| B2a USDA binary trigger (official, trained 2000-2015) | 223.5 | 57% | 0.57× |
| B2a USDA binary trigger (Middle, trained 2000-2021) | 221.4 | 56% | 0.56× |
| Z0 predict zero (control) | 395.2 | 100% | 1.00× |

## 7. Supporting, not an independent test: 2024-2025, Middle and Yours windows next to the official models

### IA + NE combined
**Total actual payouts: $181.3M | state-years: 4**

Actual statewide payout per state-year: IA 2024: $58.5M, IA 2025: $14.6M, NE 2024: $77.3M, NE 2025: $30.9M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (official, trained 2000-2015) | **14.0** | **31%** | **0.31×** |
| D Tweedie GLM (Middle, trained 2000-2021) | 15.6 | 34% | 0.34× |
| D Tweedie GLM (Yours, trained 2000-2023) | 15.2 | 34% | 0.34× |
| B2a USDA binary trigger (official, trained 2000-2015) | 192.2 | 424% | 4.24× |
| B2a USDA binary trigger (Middle, trained 2000-2021) | 166.6 | 367% | 3.67× |
| B2a USDA binary trigger (Yours, trained 2000-2023) | 160.4 | 354% | 3.54× |
| Z0 predict zero (control) | 45.3 | 100% | 1.00× |

### Iowa
**Total actual payouts: $73.0M | state-years: 2**

Actual statewide payout per state-year: IA 2024: $58.5M, IA 2025: $14.6M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (official, trained 2000-2015) | 8.7 | 24% | 0.24× |
| D Tweedie GLM (Middle, trained 2000-2021) | 11.7 | 32% | 0.32× |
| D Tweedie GLM (Yours, trained 2000-2023) | **6.4** | **18%** | **0.18×** |
| B2a USDA binary trigger (official, trained 2000-2015) | 170.1 | 466% | 4.66× |
| B2a USDA binary trigger (Middle, trained 2000-2021) | 121.4 | 332% | 3.32× |
| B2a USDA binary trigger (Yours, trained 2000-2023) | 107.5 | 294% | 2.94× |
| Z0 predict zero (control) | 36.5 | 100% | 1.00× |

### Nebraska
**Total actual payouts: $108.2M | state-years: 2**

Actual statewide payout per state-year: NE 2024: $77.3M, NE 2025: $30.9M

| Model | Average miss per state-year ($M) | Miss as % of actual | Miss vs Z0 (model miss ÷ Z0 miss) |
|---|---|---|---|
| D Tweedie GLM (official, trained 2000-2015) | **19.2** | **36%** | **0.36×** |
| D Tweedie GLM (Middle, trained 2000-2021) | 19.5 | 36% | 0.36× |
| D Tweedie GLM (Yours, trained 2000-2023) | 24.0 | 44% | 0.44× |
| B2a USDA binary trigger (official, trained 2000-2015) | 214.3 | 396% | 3.96× |
| B2a USDA binary trigger (Middle, trained 2000-2021) | 211.7 | 391% | 3.91× |
| B2a USDA binary trigger (Yours, trained 2000-2023) | 213.3 | 394% | 3.94× |
| Z0 predict zero (control) | 54.1 | 100% | 1.00× |

## Three plain sentences

(a) D's small miss in 2024-2025 is mostly the model and not just small payouts: it misses $14.0M a state-year, 31% of the $181M actually paid, against $45.3M (100%) for predicting zero, while the methods that over-predict in quiet years miss by 4-6 times the payout (B0 608%, B1 506%, B2a 424%); the payouts are small, though, and over all 17 quiet state-years of 2016-2025 D's miss (128% of actual) was worse than predicting zero (A was the only one clearly better, at 55%).
(b) In the official 2016-2025 test the lowest miss as a share of actual payouts was B4 (liability × D2+ area on the last map) both overall (59%, against B 65%, A 66%, D 70%, B2a 74%) and in the three drought state-years (25%, against B1 26%, C and B2a 29%, D 43%); D comes first only in the supporting 2024-2025 window (31%), and B4 or C come first in the 2022-2025 window (31% and 32% against D 46%).
(c) More training years did not change D's miss beyond noise: its miss rose from 46% to 56% of actual on 2022-2025 with training through 2021 and from 31% to 34% on 2024-2025 with training through 2021 or 2023, but D's own state-year misses range from $7M to $481M, so the Iowa and Nebraska shifts of $22M and $45M a year are well inside the standard errors of $62M and $110M for four-year means, and none of the changes is an improvement.
