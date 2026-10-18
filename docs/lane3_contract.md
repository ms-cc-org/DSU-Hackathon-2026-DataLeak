# Lane 3: state fund allocation contract

The budget officer selects one state and scenario year and enters one fund. **All supported crops in that state share the fund in proportion to estimated crop-value loss.** This is the user-confirmed rule. Its weights use the historical crop-loss lookup. Supported IA/NE runs also attach the trained model D's corn/soybean predictions as distinctly labeled context; insurance payouts do not replace crop-loss weights. Numerical workflows need no database, provider key or network service, and never train D in a request. Optional imagery tiles require internet.

## Functions and data flow

```python
from web.allocation_data import buildStateEstimates
from src.allocation import allocateFund

estimates = buildStateEstimates(
    state="IA", year=2026, level="Predict",
    prices={"CORN": 4.0, "SOYBEANS": 10.0, "WHEAT": 5.5, "SORGHUM": 4.0},
)
result = allocateFund(estimates, fundUsd=10_000_000.0)
```

| Function | Purpose |
|---|---|
| `buildStateEstimates(state: str, year: int, level: str, prices: dict[str, float]) -> pd.DataFrame` | Cached adapter returning every supplied boundary county × all four crops for the chosen state, including unavailable combinations. Uses `recordsForCrop` and `scenarioFromRecords` from the same lookup as the county Planner. |
| `allocateFund(estimates: pd.DataFrame, fundUsd: float) -> dict` | Pure arithmetic and validation. Consumes a single state/year table; returns `countyCropTable`, `countyTable`, `cropTable` and `summary`. Does not load data, calculate scenarios, or modify the caller's table. |
| `renderStateFundPlanner() -> None` | Renders the form, calculates on submission and retains the last result with its inputs in Streamlit session state. Embedded in the active Planner; the older unregistered budget page calls the same component. |

States: CA, DE, IA, NE. Crops: CORN, SOYBEANS, WHEAT (winter wheat), SORGHUM. Projection years: 2026–2030. `D0`–`D4` applies the same hypothetical drought level to every county/crop; `Predict` uses each county/crop's own 2000–2025 drought frequencies. Prices are dollars per bushel and are editable assumptions, not current market quotes. State form controls are independent of the single-county form.

The default projection year is the next calendar year within the supported horizon: **2027 in October 2026**. This is shared by the county Planner, state fund form and 3D scenario view through `src/projections.py`. Outside the horizon, the default stays within the supported years and is not mislabeled as next year. A future year's loss uses that year's extended yield trend, historical drought/loss patterns, latest reported acreage and assumed prices. No future drought observations or automatic weather forecast enter the calculation. The year is preserved through county estimates, allocation tables and CSV export.

## Dollar basis, eligibility and policy

```text
estimated crop-value loss = projected trend yield × central loss fraction
                           × latest reported planted acres × assumed price

county/crop fund share = positive estimated county/crop loss
                        ÷ sum of positive estimated losses across ALL crops in the selected state

illustrative county/crop allocation = state fund × county/crop fund share
county allocation = sum of that county's supported crop allocations
```

The existing lookup fits a hindsight trend using at least ten reported yields and needs at least five years with usable yield/trend/drought history. For a selected drought level, at least two exact historical matches are needed for its ordinary estimate. Otherwise it falls back to the nearest three historical years with a warning. Fallback estimates remain in the fund weights and are flagged as uncertain. This is not a weather forecast, validated loss model, or official payment policy.

Missing crop records, insufficient usable history/trend, nonpositive projected yield, or missing planted acres leave the estimate unavailable. Such rows stay in the output with a reason, missing loss and missing allocation. Known zero losses remain eligible records with zero allocation. Positive estimates share the fund without an additional drought trigger, minimum award, per-crop budget or loss cap. A zero price or zero planted acres produces a known zero dollar estimate. Acreage can be old: its latest reported year is displayed in detail and exported.

When positive estimates exist, the **entire** fund is distributed. If it exceeds covered loss, the UI warns that the uncapped allocations exceed the estimates proportionally. With no positive estimates, all of the fund remains unallocated. A total containing missing county/crop combinations is only the loss in covered records; it is not a complete estimate of statewide need.

Funds are rounded half up to cents. Largest remainder distributes residual cents; ties sort by FIPS then crop, so input row order cannot change awards. County and crop totals sum these integer cents; no money is created or lost by independently rounding county awards.

## County/crop output fields

`allocateFund` requires the first six columns below; the state adapter supplies the other scenario fields. Additional fields survive allocation unchanged.

| Column | Meaning and units |
|---|---|
| `fips`, `county`, `state` | Five-character FIPS text preserving leading zeros, county name, state abbreviation. |
| `crop`, `year` | Dataset crop code and scenario year. One row per county/crop/year; duplicate rows and mixed state/year funds are rejected. |
| `estimatedLossUsd` | Central estimated crop-value loss in dollars; missing is unavailable, not zero. |
| `lossLowUsd`, `lossHighUsd` | Dollar values of the lookup's historical low/high; not a calibrated confidence interval. Allocation uses the central estimate only. |
| `scenarioLevel`, `pricePerBushel` | D0–D4 or Predict; price assumption in dollars per bushel for that crop. |
| `trendYield`, `acres`, `acreageYear`, `historyYears` | Projected bushels per acre; latest reported planted acres and their year; usable historical year count. |
| `confident`, `warnings`, `unavailableReason` | Whether matching history meets the lookup's rule; fallback explanation; reason an estimate cannot be made. `confident` is not a statistical validation claim. |
| `eligible` | True when the dollar estimate is available, including known zero loss and flagged fallback estimates. |
| `lossShare` | Fraction of covered positive estimated loss (0–1); missing for unavailable estimates. |
| `allocationCents`, `allocationUsd` | Balanced integer cents and equivalent dollars; missing for unavailable estimates. |
| `fundUsd`, `allocationRule`, `allocationReason` | Rounded state fund, `proportionalCropValueLoss`, and explanation of inclusion or exclusion. |

`countyTable` rolls up by FIPS/county/state/year; `cropTable` rolls up by state/crop/year. Both include `estimatedLossUsd`, `allocationCents`, `allocationUsd`, `estimatedCropRows`, `unavailableCropRows`, and `coverage` (`complete`, `partial`, `unavailable`). Here complete means all supplied crop records in that group have estimates, not complete coverage outside the dataset. Wholly unavailable totals remain missing. Partial totals sum only available estimates.

`summary` contains `fundUsd`, `allocatedUsd`, `unallocatedUsd`, `estimatedLossUsd`, `fundingGapUsd` (covered loss above fund, floored at zero), `fundToLossRatio`, `estimatedCropRows`, `unavailableCropRows`, and `positiveCropRows`. Loss and gap are missing if there are no estimates; the ratio is missing if there is no positive loss. The CSV download includes all county/crop rows, inputs, warnings, exclusions, rule and calculated allocations. A crop detail filter changes only the display, never the fund weights.

## Verification

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Tests check sharing across crops, county/crop rollups, cent balancing and deterministic ties, zero/missing estimates, zero and oversized funds, invalid and duplicate inputs, all four states' actual data coverage, equality with the single-county lookup, price changes, drought fallback flags, missing acreage, and the active Streamlit submission flow. Existing Lane 2 tests continue to check saved model D reproduction without refitting it.

Dedicated next-year tests check the 2027 yield extension and dollar formula, all four states' 2027 estimates through allocation and CSV serialization, and selecting 2027 in the active county/state forms. Connected-app tests also check that D context is joined only for supported crops, leaves fund allocations unchanged and is inspectable on Insurance. These establish functional correctness, not forecast accuracy; current results are in [verification](VERIFICATION.md).

## Connected insurance context

For supported states the fund calculation invokes D with latest saved insured exposure and every historical climate footprint once with equal weight. That ensemble has separate assumptions from the fund's D0–D4/Predict lookup; the UI says so explicitly. `insurancePayoutShare` and `insuranceDamagedAcreShare` are learned shares; `insurancePayoutUsd` is calculated from the payout share and assumed insured liability. The detail export includes `insurancePredictionSource`, `insuranceFootprintYears` and `insuranceExposureYear`. Wheat/sorghum insurance cells remain missing. CA/DE fund calculations remain usable and state that D does not cover them. Missing insurance artifacts produce a visible context error without discarding a valid crop-loss allocation.

The core fund export also identifies `predictionSource` (historical lookup) and `allocationSource` (policy arithmetic). County totals can show separately labeled insurance payouts, and maps show the selected fund allocation metric over public USGS imagery with an offline outline option. The [connected prediction contract](PREDICTION_CONTRACT.md) documents the full provenance.
