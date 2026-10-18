"""The official held-out test (2016-2025). Run ONCE, after the model is frozen and the user has given the go-ahead:

    python app/model/final_test.py --i-am-sure

(Run it as a script from the repo root; `python -m app.model.final_test` does not work here because `app/` is not a package and the root-level
`data/` folder would shadow `data.py`.)

Trains A, B, C, D and the baselines on 2000-2015 with the hyper-parameters tuned in evaluate.py (no re-tuning), predicts 2016-2025, applies NESTED calibration (the
multiplier for year Y uses only earlier years: the 2006-2015 out-of-sample history plus the already-passed test years; only for model-targets where evaluate.py found
calibration helpful), builds the historical scenario ranges (whole earlier years' residuals, years < Y), widens the budget range to contain the headline model's point
estimate, and writes results/test_report.md plus csv files. Nothing is tuned or changed after seeing the results; failures are reported too.
"""
import argparse
import json
import pathlib
import sys

import numpy as np
import pandas as pd

from data import RESULTS, add_year_class, load_usable
from evaluate import (BASELINES, CANDIDATES, LABEL, MODELS, RANGED, SIG_SHARE, add_z, apply_k, attach_range, budget_range_rows, f_amt, f_pct, fit_predict, history,
                      k_table, known_misses, md, metrics, range_rows, state_year_points, summary_md, trigger_agreement, two_by_two)

OFFICIAL = "Version 1 – official test, model frozen before seeing test data"
DISCLOSURE = ("Disclosure: some 2016–2025 years appeared in earlier exploratory analyses (2018/2022 payout totals, early 2022/2023 budget tests). "
              "The headline model was chosen by the pre-declared rule on walk-forward + validation only (DECISIONS.md, Entries 3-4).")


def verdict_text(M, hl):
    g = lambda grp, m, col: M[(M.target == "t1") & (M.group == grp) & (M.model == m)][col].iloc[0]
    better = {}
    for grp in ("all", "drought"):
        for trig in ("B2a", "B2b"):
            better[(grp, trig)] = (g(grp, hl, "stat_abs_err") < g(grp, trig, "stat_abs_err"), g(grp, hl, "capture_top20") > g(grp, trig, "capture_top20"))
    err_wins = sum(v[0] for v in better.values())
    cap_wins = sum(v[1] for v in better.values())
    kind = ("a clear win" if err_wins == 4 and cap_wins == 4 else "a loss" if err_wins == 0 and cap_wins == 0 else "mixed")
    s = []
    for grp, name in (("drought", "drought state-years"), ("all", "all state-years")):
        s.append(f"On {name}, {LABEL[hl]} has a statewide absolute error of {f_amt(g(grp, hl, 'stat_abs_err'), '$')} against {f_amt(g(grp, 'B2a', 'stat_abs_err'), '$')} for B2a and "
                 f"{f_amt(g(grp, 'B2b', 'stat_abs_err'), '$')} for B2b, top-20 capture {f_pct(g(grp, hl, 'capture_top20'), 1)} against {f_pct(g(grp, 'B2a', 'capture_top20'), 1)} and "
                 f"{f_pct(g(grp, 'B2b', 'capture_top20'), 1)} (best possible {f_pct(g(grp, hl, 'best_capture'), 1)}), and under-budgets by {f_amt(g(grp, hl, 'under_budget_total'), '$')} in total "
                 f"against {f_amt(g(grp, 'B2a', 'under_budget_total'), '$')} and {f_amt(g(grp, 'B2b', 'under_budget_total'), '$')}.")
    s.append(f"Against the current-practice triggers the result is **{kind}** (lower error in {err_wins} of 4 comparisons, higher capture in {cap_wins} of 4; comparisons are drought / all state-years x B2a / B2b); "
             f"B1 (statewide absolute error {f_amt(g('all', 'B1', 'stat_abs_err'), '$')}, capture {f_pct(g('all', 'B1', 'capture_top20'), 1)} over all state-years) is a sanity check only.")
    s.append(f"The headline model's worst single state-year shortfall is {f_amt(g('all', hl, 'worst_shortfall'), '$')} (B2a {f_amt(g('all', 'B2a', 'worst_shortfall'), '$')}, B2b {f_amt(g('all', 'B2b', 'worst_shortfall'), '$')}).")
    return " ".join(s)


def run_final(train_splits, eval_split, out_dir, allow_test=False, label=OFFICIAL):
    cfg = json.load(open(RESULTS / "chosen_model.json"))
    method = json.load(open(RESULTS / "range_method.json"))["method"]
    params, hl = cfg["params"], cfg["chosen"]
    train = load_usable(*train_splits)
    test = load_usable(eval_split, allow_test=allow_test)
    raw = fit_predict(train, test, params)

    # nested calibration: k for each test year from the 2006-2015 history plus the test years already passed
    hist = pd.read_csv(RESULTS / "calibration_history.csv")
    hist = hist[hist.year < int(test.year.min())]          # only years before the first scored year
    ktab = k_table(pd.concat([hist, history(raw)], ignore_index=True))
    cal_tbl = pd.read_csv(RESULTS / "calibration.csv")
    use = {(r.model, r.target): bool(r.use_calibration) for r in cal_tbl.itertuples()}
    cal = add_z(apply_k(raw, ktab, use))

    # historical scenario ranges: residual pools = calibrated 2006-2015 predictions + earlier test years
    hist_oos = pd.read_csv(RESULTS / "oos_predictions.csv", dtype={"fips": str})
    hist_oos = hist_oos[hist_oos.year < int(test.year.min())]
    cov = range_rows(pd.concat([hist_oos, cal], ignore_index=True))
    cov = cov[cov.year.isin(set(test.year))]
    M = pd.concat([attach_range(metrics(cal, MODELS, "t1"), cov).assign(split="test")] +
                  [metrics(cal, MODELS, t).assign(split="test") for t in ("t2", "z")], ignore_index=True)
    pts = state_year_points(cal, "t1")
    bud = budget_range_rows(cov, pts[pts.model == hl].set_index(["state_alpha", "year"]).pred, method)
    cls = add_year_class(cal).drop_duplicates(["state_alpha", "year"]).set_index(["state_alpha", "year"]).sy_class
    misses, _ = known_misses(pts, cal.groupby(["state_alpha", "year"]).liability.sum())
    cd, pr = trigger_agreement(cal, hl)
    tbl, note = two_by_two(cd, LABEL[hl])

    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    M.to_csv(out_dir / "test_metrics.csv", index=False)
    cal.drop(columns=[c for c in cal if c in ("_one",)]).to_csv(out_dir / "test_predictions.csv", index=False)
    cov.to_csv(out_dir / "test_range_coverage.csv", index=False)
    bud.reset_index().to_csv(out_dir / "test_budget_range.csv", index=False)
    cd.to_csv(out_dir / "test_trigger_agreement_county_years.csv", index=False)
    ktab[ktab.year.isin(set(test.year))].to_csv(out_dir / "test_nested_k.csv", index=False)

    years = f"{int(test.year.min())}-{int(test.year.max())}"
    sel = lambda t, grp: M[(M.target == t) & (M.group == grp)]
    drought_list = ", ".join(sorted(f"{s} {y}" for (s, y), v in cls.items() if v == "drought")) or "none"
    rows = []
    for (s, y), b in bud.sort_index(level=["state", "year"]).iterrows():
        row = {"state": s, "year": y, "type": cls[(s, y)], "actual X $M": f"{b.actual / 1e6:,.1f}"}
        p = pts[(pts.state_alpha == s) & (pts.year == y)].set_index("model").pred
        for m in [hl, "B2a", "B2b"] + [x for x in CANDIDATES if x != hl]:
            row[LABEL[m] + " $M"] = f"{p[m] / 1e6:,.1f}"
        row["budget range $M"] = f"{b.budget_low / 1e6:,.1f}–{b.budget_high / 1e6:,.1f}"
        row["actual vs range"] = "inside ✓" if b.inside else "outside ✗"
        rows.append(row)
    rc = []
    for m in RANGED:
        for grp in ("all", "drought", "quiet"):
            x = cov[cov.model == m]
            x = x if grp == "all" else x[x.sy_class == grp]
            rc.append({"model": LABEL[m], "state-years": grp, "n": len(x), "inside": int(x.inside.sum()), "coverage": f_pct(x.inside.mean()) if len(x) else "–",
                       "mean width": f_amt(x.width.mean(), "$") if len(x) else "–", "actual above upper bound": int(x.upper_miss.sum()), "actual below lower bound": int(x.lower_miss.sum())})
    text = f"""# Final test report ({years}): {label}

{DISCLOSURE}

**Headline model: {LABEL[hl]}** (chosen by the pre-declared rule on walk-forward + validation: {cfg['reason']}). Candidates A, B, C, D and the baselines (Z0 predict zero, B1 bin average, B2a USDA binary trigger,
B2b tiered LFP-style trigger, B3 liability only, B4 liability x D2+ last map) were trained on 2000-2015 ({len(train)} rows) and predict {len(test)} rows. Calibration is nested (k for a year uses only earlier years,
including the test years already passed; applied only where evaluate.py found it helpful). **X** = estimated insurance payouts, **Y** = estimated deductible exposure, **Z** = illustrative relief allocation under a 95%
coverage assumption (inspired by USDA ERP 2022). Drought state-years in this window (actual statewide payout >= 3% of insured $): {drought_list}. The "historical scenario range" is the rough 10th-90th percentile of past outcomes;
the budget range is the `{method}` range widened to contain the headline model's point estimate. Metric definitions are in `validation_report.md`.

## 1. Headline vs current USDA practice (B2a, B2b)
**All state-years** ({int(sel('t1', 'all').state_years.iloc[0])})

{summary_md(sel('t1', 'all'), '$', [hl, 'B2a', 'B2b'])}

**Drought state-years only**

{summary_md(sel('t1', 'drought'), '$', [hl, 'B2a', 'B2b']) if (sel('t1', 'drought').model == hl).any() else 'No drought state-years in this window.'}

## 2. All models, T1 (X)
**All state-years**

{summary_md(sel('t1', 'all'), '$')}

**Drought state-years only**

{summary_md(sel('t1', 'drought'), '$') if (sel('t1', 'drought').model == hl).any() else 'No drought state-years in this window.'}

**Quiet state-years only**

{summary_md(sel('t1', 'quiet'), '$') if (sel('t1', 'quiet').model == hl).any() else 'No quiet state-years in this window.'}

## 3. T2 (damaged acres) and Z (illustrative relief allocation)
**T2, all state-years**

{summary_md(sel('t2', 'all'), 'acres', ranged=False)}

**Z, all state-years**

{summary_md(sel('z', 'all'), '$', ranged=False)}

**Z, drought state-years only**

{summary_md(sel('z', 'drought'), '$', ranged=False) if (sel('z', 'drought').model == hl).any() else 'No drought state-years in this window.'}

## 4. Statewide X per state-year ($M)
{md(pd.DataFrame(rows))}

## 5. Historical scenario range coverage
{md(pd.DataFrame(rc))}

Budget range ({method} widened around {LABEL[hl]}'s point estimate): actual inside in {int(bud.inside.sum())} of {len(bud)} state-years; the point estimate was inside the raw range in {int(bud.point_inside.sum())}.

## 6. Trigger agreement (B2a vs {LABEL[hl]}, significant payout = share >= {SIG_SHARE:.0%})
{md(pr.reset_index().rename(columns={'index': 'flagging rule'}))}

{md(tbl)}

{note}

## 7. Known misses
State-years where B1 and all four candidates were off by more than 50% (statewide X):

{md(misses) if len(misses) else 'None.'}

## 8. Verdict vs current USDA practice
{verdict_text(M, hl)}
"""
    (out_dir / "test_report.md").write_text(text)
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--i-am-sure", action="store_true", help="confirm that the model is frozen and the held-out 2016-2025 data may be read")
    a = ap.parse_args()
    if not a.i_am_sure:
        print("Refusing to run: this reads the held-out testing/ split, which must be used once, at the very end.\nRe-run with --i-am-sure when the model is final.")
        return 2
    run_final(("training", "validation"), "testing", RESULTS, allow_test=True)
    print("wrote", RESULTS / "test_report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
