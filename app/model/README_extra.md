# Post-test planning band for statewide X


`reserve_band_x_usd` = D's statewide X x [q05, q95], the 5th and 95th percentile of actual / D over the out-of-sample state-years 2006-2015 (`results/ratio_band.json`, built by `ratio_band.py` from `results/oos_predictions.csv` only).
It applies to statewide X only (not Y, Z or single counties), is reported as exploratory, and never changes D. `ratio_band_eval.py` checks it once on 2016-2025. For real future use, re-run `ratio_band.py` each year after the
final RMA claims are in, using only out-of-sample years before the forecast year (and log the change in DECISIONS_extra.md first). `src/reserve_band.py` has `load_ratio_band()` and `reserve_band_x_usd(plan_usd)`; call the latter after acres_scale x price_scale.
