# Planning band for statewide X on the 2016-2025 state-years (exploratory, after the official test)

**exploratory, after the official test.** The band was proposed after the official test (DECISIONS.md Entry 9) and is a one-time check, not a selection step: D and its test report are unchanged. Band = D's statewide estimate x [0.063, 1.978] (5th and 95th percentile of actual / D over the out-of-sample state-years 2006-2015; `results/ratio_band.json`). 'Existing C range' = the saved widened historical scenario range in `results/test_budget_range.csv`. Coverage uses the unclipped state-year dollars; the 20 test state-years are the same ones as in the official report.

## Coverage and width (exploratory, after the official test)

| State-years | n | Actual inside planning band | Actual inside C range | Mean width, band | Mean width, C | Median width, band | Median width, C |
|---|---|---|---|---|---|---|---|
| All state-years | 20 | 18 of 20 | 18 of 20 | $339.6M | $519.4M | $122.3M | $238.8M |
| Drought state-years (IA 2023, NE 2022, NE 2023) | 3 | 2 of 3 | 3 of 3 | $797.5M | $1,221.4M | $917.3M | $1,174.9M |
| Quiet state-years | 17 | 16 of 17 | 15 of 17 | $258.7M | $395.5M | $91.6M | $196.9M |

## Misses and the 2 x D rule of thumb (exploratory, after the official test)

| State-years | n | Actual above the top of the band | Actual below the bottom | Actual <= 2 x D |
|---|---|---|---|---|
| All state-years | 20 | 1 of 20 | 1 of 20 | 19 of 20 |
| Drought state-years (IA 2023, NE 2022, NE 2023) | 3 | 1 of 3 | 0 of 3 | 2 of 3 |
| Quiet state-years | 17 | 0 of 17 | 1 of 17 | 17 of 17 |

Years above the top of the band: NE 2023 (actual $612.5M vs top $260.0M, D $131.5M).

## Per state-year (exploratory, after the official test)

| State-year | Class | Actual | D | Band low | Band high | Inside band | C low | C high | Inside C |
|---|---|---|---|---|---|---|---|---|---|
| IA 2016 | quiet | $1.4M | $21.6M | $1.4M | $42.8M | yes | $1.1M | $85.1M | yes |
| IA 2017 | quiet | $109.1M | $338.5M | $21.5M | $669.5M | yes | $25.9M | $817.5M | yes |
| IA 2018 | quiet | $25.2M | $46.6M | $3.0M | $92.2M | yes | $3.9M | $170.1M | yes |
| IA 2019 | quiet | $2.9M | $135.1M | $8.6M | $267.2M | NO | $12.4M | $692.6M | NO |
| IA 2020 | quiet | $213.5M | $325.8M | $20.7M | $644.4M | yes | $52.4M | $1,186.9M | yes |
| IA 2021 | quiet | $55.9M | $499.7M | $31.7M | $988.3M | yes | $78.8M | $1,439.0M | NO |
| IA 2022 | quiet | $257.5M | $466.2M | $29.6M | $922.1M | yes | $44.2M | $1,030.7M | yes |
| IA 2024 | quiet | $58.5M | $47.8M | $3.0M | $94.6M | yes | $0.8M | $197.7M | yes |
| IA 2025 | quiet | $14.6M | $7.8M | $0.5M | $15.3M | yes | $0.1M | $15.9M | yes |
| NE 2016 | quiet | $10.5M | $21.3M | $1.3M | $42.1M | yes | $1.2M | $72.5M | yes |
| NE 2017 | quiet | $36.1M | $57.4M | $3.6M | $113.5M | yes | $4.6M | $126.6M | yes |
| NE 2018 | quiet | $11.7M | $5.9M | $0.4M | $11.8M | yes | $0.4M | $41.5M | yes |
| NE 2019 | quiet | $1.1M | $9.7M | $0.6M | $19.2M | yes | $0.1M | $39.9M | yes |
| NE 2020 | quiet | $55.8M | $70.4M | $4.5M | $139.2M | yes | $11.7M | $281.4M | yes |
| NE 2021 | quiet | $94.0M | $157.0M | $10.0M | $310.5M | yes | $12.1M | $386.2M | yes |
| NE 2024 | quiet | $77.3M | $47.4M | $3.0M | $93.8M | yes | $4.3M | $212.3M | yes |
| NE 2025 | quiet | $30.9M | $39.4M | $2.5M | $78.0M | yes | $5.7M | $187.5M | yes |
| IA 2023 | drought | $716.0M | $479.2M | $30.4M | $947.7M | yes | $36.0M | $1,433.8M | yes |
| NE 2022 | drought | $860.0M | $639.2M | $40.6M | $1,264.1M | yes | $87.8M | $1,262.7M | yes |
| NE 2023 | drought | $612.5M | $131.5M | $8.3M | $260.0M | NO | $30.8M | $1,122.4M | yes |

## Reading the numbers

- The band contains the actual payout in 18 of 20 state-years (2 of 3 drought, 16 of 17 quiet); the existing C range contains it in 18 of 20.
- Mean width $339.6M vs $519.4M for the C range; median $122.3M vs $238.8M.
- Actual payout was at most 2 x D in 19 of 20 state-years.
