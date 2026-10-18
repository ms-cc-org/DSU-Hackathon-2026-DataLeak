"""Section 5: the final held-out test (2016-2025). Run ONCE, after the model is final.

    python app/model/final_test.py --i-am-sure

Retrains B0, B1, A, B, C on 2000-2015 with the hyper-parameters tuned in evaluate.py and the calibration factors k from results/calibration.csv
(walk-forward 2006-2012; no re-tuning, no re-fitting of k),
predicts 2016-2025, computes the same metrics and writes results/test_report.md (+ csv files).
Do not change the model after seeing these results; report failures too. Expected hard cases:
2020 Iowa (derecho: a wind loss, mostly not drought-coded) and quiet years.
"""
import argparse
import json
import pathlib
import sys

import pandas as pd

from budget import residual_pool
from data import RESULTS, load_usable
from evaluate import (LABEL, MODELS, apply_k, fit_predict, md, metric_tables, metrics, range_rows, statewide_totals,
                      totals_wide)


def run_final(train_splits, eval_split, out_dir, allow_test=False):
    params_file = json.load(open(RESULTS / "chosen_model.json"))
    params, chosen = params_file["params"], params_file["chosen"]
    train = load_usable(*train_splits)
    test = load_usable(eval_split, allow_test=allow_test)
    pred = apply_k(fit_predict(train, test, params), pd.read_csv(RESULTS / "calibration.csv"))   # k from walk-forward 2006-2012

    m = metrics(pred)
    tot = statewide_totals(pred)
    oos = pd.read_csv(RESULTS / "oos_predictions.csv", dtype={"fips": str})
    cov = range_rows(pred, {c: residual_pool(oos, c) for c in ["A", "B"]}, "t1")   # A, B: whole-year residuals; C: neighbours
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    m.to_csv(out_dir / "test_metrics.csv", index=False)
    tot.to_csv(out_dir / "test_statewide_totals.csv", index=False)
    cov.to_csv(out_dir / "test_range_coverage.csv", index=False)

    years = f"{int(test.year.min())}-{int(test.year.max())}"
    tr_years = f"{int(train.year.min())}-{int(train.year.max())}"
    hard = tot[(tot.state_alpha == "IA") & (tot.year == 2020)]
    hard_txt = (md(hard.assign(**{c: hard[c] / 1e6 for c in ["X_pred", "X_actual"]})[["model", "year", "X_pred", "X_actual"]]
                   .rename(columns={"X_pred": "predicted $M", "X_actual": "actual $M"}))
                if len(hard) else "2020 Iowa is not in this evaluation split.")
    ch = cov[cov.model == chosen]   # chosen model's rough 80% range per state-year
    cov_sum = cov.groupby("model").inside.agg(["mean", "size"]).reset_index().rename(
        columns={"mean": "share inside 80% range", "size": "state-years"})
    text = f"""# Final test report ({years})

Models retrained on {tr_years} ({len(train)} rows) with the hyper-parameters from `results/params.json` (tuned on
training walk-forward only), predicting {len(test)} rows. Chosen model from validation: **{chosen} ({LABEL[chosen]})**
({params_file['reason']}). Do not change the model after seeing this report.

{metric_tables(m)}
## Statewide drought payout per state-year ($M, predicted vs actual)
{md(totals_wide(tot, MODELS, classes=("drought", "quiet")))}

## Hard case: Iowa 2020 (derecho)
{hard_txt}

## 80% range check for the statewide payout total (rough ranges: A, B whole-year residual resampling; C neighbour spread)
{md(cov_sum)}

Chosen model, per state-year ($):

{md(ch[['state', 'year', 'low', 'point', 'high', 'actual', 'inside']])}
"""
    (out_dir / "test_report.md").write_text(text)
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--i-am-sure", action="store_true",
                    help="confirm that the model is final and the held-out 2016-2025 data may be read")
    a = ap.parse_args()
    if not a.i_am_sure:
        print("Refusing to run: this reads the held-out testing/ split, which must be used once, at the very end.\n"
              "Re-run with --i-am-sure when the model is final.")
        return 2
    run_final(("training", "validation"), "testing", RESULTS, allow_test=True)
    print("wrote", RESULTS / "test_report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
