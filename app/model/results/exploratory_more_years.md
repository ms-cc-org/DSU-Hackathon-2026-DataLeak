# EXPLORATORY – post-test. These years were already seen in the official 2016–2025 test; this is not an independent test and doesn't replace the official result.

**Question.** Does training on more recent years improve predictions on the same later years? Nothing in the official results files, models, settings or features was changed.

**Runs.** *Official*: models trained on 2000-2015; their saved official predictions for 2022-2025 (and the 2024-2025 subset), no retraining. *Middle*: retrained on 2000-2021, predict 2022-2025. *Yours*: retrained on 2000-2023, predict 2024-2025.
Models D (alpha 0.001), A, B, C with the frozen `results/params.json` settings, no retuning; baselines B0, B1, B2a, B4, Z0. Preprocessing is the existing fold-safe pipeline (normals and irrigation averages from earlier years in the data build; imputers, scalers, bins, look-alike pools fitted on the training years of each run).
**All columns are uncalibrated** so the runs are comparable: the official nested calibration (applied to A and B4 only) was divided back out of the saved Official predictions for those two models; D, B, C, B1, B2a and Z0 were uncalibrated in the official run already.
B0 was not part of the official run, so its Official column is B0 fitted on 2000-2015 here.

**Metrics (the only two reported).** *Statewide budget error*: for each state, the average over its state-years of |predicted statewide payout − actual|, in $M, and the total absolute miss ÷ total actual payouts (%). *Top-20 capture*: share of actual drought payouts landing in the 20 counties (crops summed) with the highest predicted payout,
averaged over the state-years, as in the official report. Rows for D and B2a are in bold.

**Read with care.** Each Iowa or Nebraska cell rests on only 4 state-years (2022-2025) or 2 (2024-2025), so differences between runs are mostly noise; the drought state-years in 2022-2025 are IA 2023, NE 2022, NE 2023, and 2024-2025 has none. The Middle and Yours runs train on years that include
the test-window neighbours (2016-2023), which the official run never saw.

### Table 1. Test years 2022-2025: Official vs Middle

| State | Model | Official (2000-2015): avg miss/state-yr | Official (2000-2015): miss ÷ actual | Official (2000-2015): top-20 capture | Middle (2000-2021): avg miss/state-yr | Middle (2000-2021): miss ÷ actual | Middle (2000-2021): top-20 capture |
|---|---|---|---|---|---|---|---|
| Iowa | **D Tweedie GLM (headline)** | **$115.7M** | **44%** | **41.9%** | **$137.9M** | **53%** | **40.6%** |
| Iowa | A hurdle | $102.6M | 39% | 42.0% | $182.1M | 70% | 43.3% |
| Iowa | B boosting | $103.4M | 40% | 33.7% | $175.1M | 67% | 33.1% |
| Iowa | C look-alikes | $73.6M | 28% | 39.5% | $159.5M | 61% | 34.6% |
| Iowa | B0 state x crop mean | $288.5M | 110% | 32.4% | $235.9M | 90% | 32.3% |
| Iowa | B1 drought-bin average | $209.4M | 80% | 40.5% | $115.8M | 44% | 40.5% |
| Iowa | **B2a USDA binary trigger** | **$137.8M** | **53%** | **36.4%** | **$146.6M** | **56%** | **36.4%** |
| Iowa | B4 liability x D2+ last map | $89.0M | 34% | 37.3% | $78.0M | 30% | 37.3% |
| Iowa | Z0 predict zero | $261.6M | 100% | 23.8% | $261.6M | 100% | 23.8% |
| Nebraska | **D Tweedie GLM (headline)** | **$185.1M** | **47%** | **54.0%** | **$230.6M** | **58%** | **51.8%** |
| Nebraska | A hurdle | $311.2M | 79% | 51.4% | $318.5M | 81% | 52.5% |
| Nebraska | B boosting | $149.8M | 38% | 56.2% | $229.0M | 58% | 56.0% |
| Nebraska | C look-alikes | $133.3M | 34% | 51.5% | $183.7M | 46% | 54.9% |
| Nebraska | B0 state x crop mean | $315.2M | 80% | 18.2% | $323.0M | 82% | 18.2% |
| Nebraska | B1 drought-bin average | $191.3M | 48% | 20.1% | $187.0M | 47% | 20.1% |
| Nebraska | **B2a USDA binary trigger** | **$223.5M** | **57%** | **17.8%** | **$221.4M** | **56%** | **17.8%** |
| Nebraska | B4 liability x D2+ last map | $135.3M | 34% | 39.4% | $126.5M | 32% | 39.4% |
| Nebraska | Z0 predict zero | $395.2M | 100% | 16.5% | $395.2M | 100% | 16.5% |

### Table 2. Test years 2024-2025: Official vs Middle vs Yours

| State | Model | Official (2000-2015): avg miss/state-yr | Official (2000-2015): miss ÷ actual | Official (2000-2015): top-20 capture | Middle (2000-2021): avg miss/state-yr | Middle (2000-2021): miss ÷ actual | Middle (2000-2021): top-20 capture | Yours (2000-2023): avg miss/state-yr | Yours (2000-2023): miss ÷ actual | Yours (2000-2023): top-20 capture |
|---|---|---|---|---|---|---|---|---|---|---|
| Iowa | **D Tweedie GLM (headline)** | **$8.7M** | **24%** | **34.6%** | **$11.7M** | **32%** | **30.6%** | **$6.4M** | **18%** | **38.2%** |
| Iowa | A hurdle | $25.4M | 70% | 34.9% | $28.0M | 77% | 39.0% | $26.0M | 71% | 36.5% |
| Iowa | B boosting | $11.1M | 31% | 16.6% | $18.9M | 52% | 24.2% | $12.4M | 34% | 28.0% |
| Iowa | C look-alikes | $9.5M | 26% | 31.3% | $5.8M | 16% | 30.3% | $6.9M | 19% | 34.4% |
| Iowa | B0 state x crop mean | $354.4M | 970% | 25.1% | $247.3M | 677% | 25.0% | $265.7M | 727% | 25.0% |
| Iowa | B1 drought-bin average | $270.8M | 741% | 32.0% | $202.1M | 553% | 32.0% | $206.8M | 566% | 32.0% |
| Iowa | **B2a USDA binary trigger** | **$170.1M** | **466%** | **32.8%** | **$121.4M** | **332%** | **32.8%** | **$107.5M** | **294%** | **32.8%** |
| Iowa | B4 liability x D2+ last map | $36.5M | 100% | 27.0% | $36.5M | 100% | 27.0% | $36.5M | 100% | 27.0% |
| Iowa | Z0 predict zero | $36.5M | 100% | 27.0% | $36.5M | 100% | 27.0% | $36.5M | 100% | 27.0% |
| Nebraska | **D Tweedie GLM (headline)** | **$19.2M** | **36%** | **58.3%** | **$19.5M** | **36%** | **57.3%** | **$24.0M** | **44%** | **61.5%** |
| Nebraska | A hurdle | $31.5M | 58% | 59.2% | $29.1M | 54% | 59.3% | $36.4M | 67% | 59.9% |
| Nebraska | B boosting | $20.7M | 38% | 64.1% | $26.9M | 50% | 64.5% | $32.2M | 60% | 64.4% |
| Nebraska | C look-alikes | $21.9M | 40% | 58.3% | $23.1M | 43% | 63.2% | $23.2M | 43% | 62.4% |
| Nebraska | B0 state x crop mean | $197.1M | 364% | 13.2% | $122.5M | 226% | 13.2% | $190.2M | 352% | 13.2% |
| Nebraska | B1 drought-bin average | $187.5M | 346% | 16.9% | $181.1M | 335% | 16.9% | $192.1M | 355% | 17.3% |
| Nebraska | **B2a USDA binary trigger** | **$214.3M** | **396%** | **11.5%** | **$211.7M** | **391%** | **11.5%** | **$213.3M** | **394%** | **11.5%** |
| Nebraska | B4 liability x D2+ last map | $39.3M | 73% | 35.6% | $41.8M | 77% | 35.6% | $42.1M | 78% | 35.6% |
| Nebraska | Z0 predict zero | $54.1M | 100% | 12.8% | $54.1M | 100% | 12.8% | $54.1M | 100% | 12.8% |

## Takeaway

More recent training years did not reliably help D: on 2022-2025, retraining through 2021 made D's statewide error worse in both states (Iowa $116M → $138M a year, Nebraska $185M → $231M, with top-20 capture roughly flat at 41.9% → 40.6% and 54.0% → 51.8%), and on 2024-2025 the picture was mixed (Iowa best with training through 2023, $6.4M vs $8.7M, but Nebraska worst, $24.0M vs $19.2M, while capture rose in both states with the 2000-2023 window, to 38.2% and 61.5%). D stayed ahead of the USDA binary trigger B2a on top-20 capture in every run and state (Nebraska 52-62% vs 12-18%) and on dollar error in every comparison except Nebraska 2022-2025 with the Middle window ($231M vs $221M); in 2024-2025 B2a misses by $107-214M a year because it fires in non-drought years. With only 2-4 state-years per cell and all of these years already seen in the official test, the differences between training windows are within noise, so this is no clear evidence that retraining on recent years would improve D.
