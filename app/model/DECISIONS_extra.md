# Post-test decisions, preserved separately from main

## Entry 8: written 2026-10-18 01:06 EDT (system clock): second request to "run the final test once"; it was NOT run again

The user re-sent the pre-test instructions with extra deliverables. Facts: (1) the alpha edge check and the headline freeze were already done (Entries 6-7: alpha was at the lower edge, 0.01; extended one step; chosen alpha became 0.001; headline stayed D, uncalibrated);
(2) the official test already ran once, on 2026-10-18 around 00:41 EDT, after the commit that contains Entries 6-7, and its report was committed (originally 8ed713b; the same content is now in main). Running `final_test.py` again would be a second look at the held-out years
and would break the one-shot rule, so it was not run again. The extra deliverables (test_predictions.csv in the requested layout, test_state_years.csv, the per-state-year table with the closest value in bold, the scoreboard, the chart) are built by
`app/model/make_test_report.py` purely from the saved outputs of that one run (`test_predictions_raw_shares.csv`, `test_budget_range.csv`, `test_metrics.csv`); no model is refit and no setting changes. The script checks that its numbers equal the saved metrics.

---

## Entry 9: written 2026-10-18 04:26 EDT (system clock), before anything was run: exploratory planning band for statewide X

Planning band for statewide X = D's statewide estimate x [5th, 95th] percentile of actual/D, computed ONLY from out-of-sample state-years 2006-2015 in results/oos_predictions.csv.
Proposed after the official test; reported as exploratory; it never changes D. Plan fixed now: per state-year (IA, NE; 20 in all) actual = sum(drought_indemnity), D = sum(t1_D x liability), both clipped to >= $100,000,
r = log(actual / D), q05 / q95 = exp of the 5th / 95th percentile of r (numpy linear method). `ratio_band.py` (build time) reads only oos_predictions.csv, asserts years 2006..2015 and 20 state-years, and writes
results/ratio_band.json. `ratio_band_eval.py` (one-time check, afterwards) applies the saved band to the 2016-2025 state-years already in test_predictions.csv and writes results/ratio_band_eval.md, labelled exploratory,
after the official test; it does not write the json. The band applies to statewide X only (not Y, Z or single counties). Nothing in D, its artifacts, test_report.md or any training code changes.
Frozen-file hashes recorded before running (test_report.md, test_predictions.csv, test_budget_range.csv, chosen_model.json, params.json, oos_predictions.csv).
