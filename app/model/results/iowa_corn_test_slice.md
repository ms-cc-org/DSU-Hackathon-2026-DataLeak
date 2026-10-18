# Iowa corn official test slice (2016–2025)

Source: `results/test_predictions.csv` only. These are existing official-test predictions; no model was retrained or selected using this slice. X means estimated drought insurance payouts (predicted T1 share × insured liability).

Each year contains Iowa corn county-crop rows only. Dollar error is the absolute difference between statewide predicted and observed drought indemnity. Top-20 capture is the share of actual Iowa corn drought indemnity in the 20 counties with the highest predicted dollars; ties use FIPS ascending. Observed payout can be zero, in which case capture is undefined.

| Year | Model | Counties | Actual X | Predicted X | Statewide $ error | Top-20 capture |
|---:|---|---:|---:|---:|---:|---:|
| 2016 | B2a USDA trigger | 99 | $1,143,202 | $0 | $1,143,202 | 20.2% |
| 2016 | B2b tiered trigger | 99 | $1,143,202 | $0 | $1,143,202 | 20.2% |
| 2016 | D Tweedie | 99 | $1,143,202 | $15,806,940 | $14,663,738 | 50.9% |
| 2017 | B2a USDA trigger | 99 | $76,841,695 | $0 | $76,841,695 | 20.2% |
| 2017 | B2b tiered trigger | 99 | $76,841,695 | $0 | $76,841,695 | 20.2% |
| 2017 | D Tweedie | 99 | $76,841,695 | $231,519,129 | $154,677,434 | 45.6% |
| 2018 | B2a USDA trigger | 99 | $10,900,719 | $16,650,666 | $5,749,947 | 43.9% |
| 2018 | B2b tiered trigger | 99 | $10,900,719 | $7,402,707 | $3,498,012 | 43.9% |
| 2018 | D Tweedie | 99 | $10,900,719 | $31,857,669 | $20,956,950 | 67.0% |
| 2019 | B2a USDA trigger | 99 | $1,518,191 | $0 | $1,518,191 | 13.9% |
| 2019 | B2b tiered trigger | 99 | $1,518,191 | $0 | $1,518,191 | 13.9% |
| 2019 | D Tweedie | 99 | $1,518,191 | $100,821,814 | $99,303,623 | 19.0% |
| 2020 | B2a USDA trigger | 99 | $151,573,597 | $153,135,973 | $1,562,376 | 42.4% |
| 2020 | B2b tiered trigger | 99 | $151,573,597 | $100,990,919 | $50,582,677 | 42.4% |
| 2020 | D Tweedie | 99 | $151,573,597 | $238,793,216 | $87,219,620 | 50.2% |
| 2021 | B2a USDA trigger | 99 | $42,237,275 | $574,940,725 | $532,703,449 | 44.0% |
| 2021 | B2b tiered trigger | 99 | $42,237,275 | $294,613,089 | $252,375,814 | 46.5% |
| 2021 | D Tweedie | 99 | $42,237,275 | $343,787,213 | $301,549,937 | 59.4% |
| 2022 | B2a USDA trigger | 99 | $167,069,727 | $246,723,528 | $79,653,802 | 51.6% |
| 2022 | B2b tiered trigger | 99 | $167,069,727 | $127,216,921 | $39,852,806 | 51.6% |
| 2022 | D Tweedie | 99 | $167,069,727 | $311,845,104 | $144,775,377 | 59.1% |
| 2023 | B2a USDA trigger | 99 | $559,446,236 | $454,812,604 | $104,633,632 | 32.0% |
| 2023 | B2b tiered trigger | 99 | $559,446,236 | $218,757,505 | $340,688,731 | 28.7% |
| 2023 | D Tweedie | 99 | $559,446,236 | $357,705,081 | $201,741,155 | 44.4% |
| 2024 | B2a USDA trigger | 99 | $29,735,707 | $327,940,106 | $298,204,399 | 31.9% |
| 2024 | B2b tiered trigger | 99 | $29,735,707 | $251,397,980 | $221,662,273 | 35.0% |
| 2024 | D Tweedie | 99 | $29,735,707 | $34,399,500 | $4,663,793 | 40.5% |
| 2025 | B2a USDA trigger | 99 | $12,995,578 | $0 | $12,995,578 | 28.9% |
| 2025 | B2b tiered trigger | 99 | $12,995,578 | $0 | $12,995,578 | 28.9% |
| 2025 | D Tweedie | 99 | $12,995,578 | $5,861,832 | $7,133,746 | 18.8% |

## Worst statewide miss by model

- **D Tweedie:** 2021, $301,549,937 over observed X.
- **B2a USDA trigger:** 2021, $532,703,449 over observed X.
- **B2b tiered trigger:** 2023, $340,688,731 under observed X.

The selected headline D was chosen from pooled model evaluation, not from this Iowa-corn-only slice. This slice should be reviewed before claiming Iowa corn performance in the app.
