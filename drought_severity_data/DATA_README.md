# drought_severity_data (data guide)

Built by `organize_drought_severity.py` on 2026-10-18T03:12:39. One row = one county x year, Iowa + Nebraska (all counties). Drought is the same for corn and soybeans, so there is no crop column.

| Folder | Years | Use |
|---|---|---|
| training | 2000-2012 | fit models |
| validation | 2013-2015 | compare / confirm models |
| testing | 2016-2025 | NOT BUILT (only with `--include-test --i-am-sure`, for the final test) |

Always read CSVs with `dtype={"fips": str}`. Join inputs to labels on `fips, year`.

## Level scale
0 = none, 1 = D0, 2 = D1, 3 = D2, 4 = D3, 5 = D4. A level counts on a weekly map when its category (D0..D4 are non-cumulative % of area) covers more than 1.0% of the county.

## Task A: drought outlook (does it get worse after the decision date?)
- **Labels** (`labels_outlook.csv`), from maps dated **08-14-09-30** (all after the cutoff): `y_A` worst level (0-5); `worse_A` = 1 if `y_A` > `level_last_map`; `change_A` = `y_A` - `level_last_map`.
- **Inputs** (`inputs_outlook.csv`): map state on the last map dated by Aug 13 (`level_last_map` is also the persistence baseline, `dsci_last`, `d0plus_pct_last`, `d1plus_pct_last`),
  `dsci_change_4wk` (last map minus the map 28 days earlier), `level_apr1` (worst level on maps dated Mar 25-Apr 7), `prev_fall_level` (worst level Aug 14-Dec 31 of the previous year),
  `nbr_level_last` (mean `level_last_map` of the other counties with a centroid within 70 km), plus the weather, soil and irrigation columns below.

## Task B: in-season drought from weather + soil
- **Labels** (`labels_weather_soil.csv`), from maps dated 04-01-08-13: `y_B` worst level; `worse_B` = 1 if `y_B` > `level_apr1`; `change_B` = `y_B` - `level_apr1`; `weeks_d2plus_to_cutoff`.
- **Inputs** (`inputs_weather_soil.csv`): weather, soil and irrigation columns plus `level_apr1` and `prev_fall_level`. NO map dated after Apr 7 of the year is used (asserted in checks.md).

## Weather columns (daily weather, only days <= Aug 13 of the year)
`precip_30d / 60d / 90d` (the 30, 60, 90 days ending Aug 13), `precip_apr1_to_cutoff`, `winter_precip` (Oct 1 of the previous year to Mar 31), `tmax_mean_30d`, `heat32_days_apr1_to_cutoff` (tmax >= 32 C),
`dry_days_30d` (days < 1 mm), `wb_30d / wb_90d / wb_apr1` = precipitation - ET0 (Hargreaves, FAO-56 Ra from the county centroid latitude: ET0 = 0.0023 * 0.408 * Ra * (Tmean + 17.8) * sqrt(max(Tmax - Tmin, 0))),
and `*_ratio` = window / the county's mean of the same window over strictly earlier years (weather starts in 1999; at least 3 earlier years, else blank).
Static: `aws_100cm_mm`, `droughty_pct`, `irr_share` (mean over strictly earlier years of the county's irrigated share, blank for the first year), `is_nebraska`.

## Leakage rules (enforced by the script, see checks.md)
- Label columns never appear in any inputs file; Task A labels only use maps dated after every map the inputs use; Task B inputs use no map dated after Apr 7.
- Normals and irrigation averages use strictly earlier years; imputers and scalers are fitted per fold in the model code.
- Nothing from 2016-2025 is loaded unless `--include-test --i-am-sure` (final test only).
- Not used: MODIS NDVI, the master dataset's season weather/drought columns, same-year yield or harvest.
