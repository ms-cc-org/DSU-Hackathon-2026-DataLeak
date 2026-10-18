# usda_budget_data (data guide)

Built by `organize_usda_data.py`. One row = one county x crop x year (Iowa + Nebraska, corn + soybeans).

| Folder | Years | Use |
|---|---|---|
| training | 2000-2012 | fit models |
| validation | 2013-2015 | compare / tune models |
| testing | 2016-2025 | final check, run once at the end |

Each county folder is named `FIPS_County_ST` (FIPS first, because county names repeat across states).
`all_inputs.csv` / `all_labels.csv` in each split stack every county. Join inputs to labels on
`fips, crop, year` (fips is 5-character text: always read it with `dtype={"fips": str}`).

## inputs.csv: only what is known before 08-15 of that year
- Drought (weekly maps, Apr 1 to Aug 14): `d2_weeks_50pct` weeks with D2+ on >=50% of county,
  `d3_weeks_50pct`, `d2_max_pct`, `dsci_mean`, `d2_pct_last_map`, `d3_pct_last_map`.
- Weather (daily, May 1 to Aug 14; heat counted from Jun 1): `precip_mm`, `precip_ratio_vs_normal`
  (normal = 2000-2012 average), `heat32_days`, `heat35_days`, `tmax_jul_mean`, `gdd` (base 10 C, cap 30 C).
- Soil: `aws_100cm_mm`, `droughty_pct`, `nccpi` (crop-specific).
- Irrigation: `irr_share_train_mean` (2000-2012 average; 0 where unknown), `irr_known` (1 = real value).
- History: `acres_planted_prev3_mean`, `yield_prev5_mean` (previous years only).

## labels.csv: what actually happened (never use as model inputs)
- From RMA cause of loss: `drought_indemnity`, `heat_indemnity` (heat + hot wind), `other_indemnity`,
  `drought_loss_acres` (acres where a drought loss was determined). Add-on/area plans excluded.
- From RMA coverage level (sobcov): `insured`, `liability` (insured $), `insured_acres`, `avg_coverage`.
- `drought_payout_share` = drought_indemnity / liability  <- suggested model target
- `drought_loss_acre_share` = drought_loss_acres / insured_acres  <- second target (needed for out-of-pocket)
- `drought_payout_per_acre`; `full_crop_value` = insured $ / coverage level (insured part + deductible).
- `out_of_pocket_drought_loss` = deductible on the acres with a drought loss (paid by farmers, estimate).
- `est_drought_damage` = drought payout + out_of_pocket_drought_loss = estimated total drought loss on
  insured acres. Slightly low: losses smaller than the deductible never file a claim.
- `est_drought_loss_share` = est_drought_damage / full_crop_value  <- alternative target (total cost)
- `relief_gap_to_95pct` = extra paid if the drought loss were recomputed at 95% coverage (how USDA's
  Emergency Relief Program Track 1 worked for 2022). Simplified, county-level, upper-end estimate.
- Blank = no insurance record or RMA file missing for that year (not zero). 0 = insured, no drought claim.
- `possible_out_of_pocket_loss` = insured, no drought payout, yield >=10% below its 5-year average, and
  some D2+ drought by 08-15: damage likely stayed inside the deductible.
- `rma_year_available` False = that year's colsom file was not found.
