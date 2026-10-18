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
                      k_table, known_misses, largest_misses, md, metrics, range_rows, state_year_points, summary_md, trigger_agreement, two_by_two)

OFFICIAL = "Official test – model frozen before seeing test data; some test years appeared in earlier exploratory analyses (see DECISIONS.md)."
DISCLOSURE = ("The headline model (D) was chosen by the pre-declared rule on walk-forward + validation only and frozen in DECISIONS.md (Entries 3-7) before this run. "
              "Earlier exploratory analyses touched some 2016-2025 years (2018/2022 payout totals, early 2022/2023 budget tests); nothing from them was used to choose or tune any model.")


def verdict_text(M, hl, bud):
    """3-5 plain sentences: headline vs current practice (B2a binary trigger, B2b tiered trigger)."""
    g = lambda grp, m, col: M[(M.target == "t1") & (M.group == grp) & (M.model == m)][col].iloc[0]
    has_dr = ((M.target == "t1") & (M.group == "drought") & (M.model == hl)).any()
    wins = {(grp, trig): (g(grp, hl, "stat_abs_err") < g(grp, trig, "stat_abs_err"), g(grp, hl, "capture_top20") > g(grp, trig, "capture_top20"))
            for grp in (("all", "drought") if has_dr else ("all",)) for trig in ("B2a", "B2b")}
    n = len(wins)
    err_w, cap_w = sum(v[0] for v in wins.values()), sum(v[1] for v in wins.values())
    kind = "a clear win" if err_w == n and cap_w == n else "a loss" if err_w == 0 and cap_w == 0 else "a mixed result"
    ny = int(g("all", hl, "state_years"))
    s = [f"Across the {ny} test state-years, the {LABEL[hl]} budget for a state was off by {f_amt(g('all', hl, 'stat_abs_err'), '$')} on average, against {f_amt(g('all', 'B2a', 'stat_abs_err'), '$')} for the USDA binary trigger (B2a) "
         f"and {f_amt(g('all', 'B2b', 'stat_abs_err'), '$')} for the tiered trigger (B2b)."]
    if has_dr:
        s.append(f"In the drought years alone that average miss was {f_amt(g('drought', hl, 'stat_abs_err'), '$')} for {LABEL[hl]} versus {f_amt(g('drought', 'B2a', 'stat_abs_err'), '$')} and {f_amt(g('drought', 'B2b', 'stat_abs_err'), '$')}, "
                 f"and it left {f_amt(g('drought', hl, 'under_budget_total'), '$')} of payouts un-budgeted against {f_amt(g('drought', 'B2a', 'under_budget_total'), '$')} and {f_amt(g('drought', 'B2b', 'under_budget_total'), '$')}.")
    s.append(f"For finding where the money goes, {LABEL[hl]}'s top 20 counties held {f_pct(g('all', hl, 'capture_top20'), 1)} of actual payouts versus {f_pct(g('all', 'B2a', 'capture_top20'), 1)} and "
             f"{f_pct(g('all', 'B2b', 'capture_top20'), 1)} for the triggers (a perfect ranking would hold {f_pct(g('all', hl, 'best_capture'), 1)}).")
    s.append(f"Its worst single state-year shortfall was {f_amt(g('all', hl, 'worst_shortfall'), '$')} (B2a {f_amt(g('all', 'B2a', 'worst_shortfall'), '$')}, B2b {f_amt(g('all', 'B2b', 'worst_shortfall'), '$')}), and its rough "
             f"scenario range contained the actual statewide payout in {int(bud.inside.sum())} of {len(bud)} state-years.")
    s.append(f"Against current practice this is **{kind}**: lower statewide error in {err_w} of {n} comparisons and better top-20 capture in {cap_w} of {n} (comparisons: {', '.join(f'{a}/{t}' for a, t in wins)}).")
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
    liab = cal.groupby(["state_alpha", "year"]).liability.sum()
    misses, _ = known_misses(pts, liab)
    own_misses = largest_misses(pts, liab, hl)
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
        for m in [hl, "B2a"]:
            row[LABEL[m] + " $M"] = f"{p[m] / 1e6:,.1f}"
        row[f"{LABEL[hl]} scenario range $M"] = f"{b.budget_low / 1e6:,.1f}–{b.budget_high / 1e6:,.1f}"
        row["actual vs range"] = "inside ✓" if b.inside else "outside ✗"
        for m in ["B2b"] + [x for x in CANDIDATES if x != hl]:
            row[LABEL[m] + " $M"] = f"{p[m] / 1e6:,.1f}"
        rows.append(row)
    rc = []
    for m in RANGED:
        for grp in ("all", "drought", "quiet"):
            x = cov[cov.model == m]
            x = x if grp == "all" else x[x.sy_class == grp]
            rc.append({"model": LABEL[m], "state-years": grp, "n": len(x), "inside": int(x.inside.sum()), "coverage": f_pct(x.inside.mean()) if len(x) else "–",
                       "mean width": f_amt(x.width.mean(), "$") if len(x) else "–", "actual above upper bound": int(x.upper_miss.sum()), "actual below lower bound": int(x.lower_miss.sum())})
    order = [hl, "B2a", "B2b", "A", "B", "C", "B1", "B3", "B4", "Z0"]
    order = [m for m in order if m in MODELS] + [m for m in MODELS if m not in order]
    def tab(t, grp, unit="$", ranged=False):
        d = sel(t, grp)
        return summary_md(d, unit, order, ranged=ranged) if (d.model == hl).any() else "No such state-years in this window."
    n_all = int(sel("t1", "all").state_years.iloc[0])
    text = f"""# Official test report ({years})

**{label}**

{DISCLOSURE}

**Headline model: {LABEL[hl]}, uncalibrated** (alpha {params['D']['alpha']}; rule: {cfg['reason']}). Secondary, reported in full: A, B, C. Baselines: Z0 (predict zero), B1 (drought-bin average), B2a (USDA binary trigger), B2b (tiered LFP-style trigger),
B3 (liability only), B4 (liability x D2+ last map). All models were trained on {int(train.year.min())}-{int(train.year.max())} ({len(train)} rows) and predict {len(test)} rows. Calibration is nested (the multiplier for a year uses only earlier years, including the test
years already passed) and was applied only to A, B4 and B3's T2, as decided on walk-forward + validation. **X** = estimated insurance payouts, **Y** = estimated deductible exposure, **Z** = illustrative relief allocation under a 95%
coverage assumption (inspired by USDA ERP 2022). Metric definitions are in `validation_report.md`.

**Which state-years count as drought, and why.** A state-year is a *drought state-year* when the actual statewide drought payout was at least 3% of insured dollars. This grouping rule was fixed before any test result existed and is
used only to split the tables. In 2016-2025 that gives {int(sel('t1', 'drought').state_years.iloc[0]) if (sel('t1', 'drought').model == hl).any() else 0} drought state-year(s): {drought_list}; the other {n_all - (int(sel('t1', 'drought').state_years.iloc[0]) if (sel('t1', 'drought').model == hl).any() else 0)} are quiet.

## 1. Headline table: {LABEL[hl]} vs B2a and B2b first, then A, B, C and B1, B3, B4, Z0 (T1: X, estimated insurance payouts)
Statewide abs. error = mean over state-years of |Σ predicted - Σ actual|; Under-budgeted = Σ over state-years of max(0, actual - predicted); Worst shortfall = largest single state-year shortfall; County WAPE and Top-20 capture over counties (crops summed); Σpred/Σactual < 1 under-budgets.

**All state-years ({n_all})**

{tab('t1', 'all', ranged=True)}

**Drought state-years only**

{tab('t1', 'drought', ranged=True)}

**Quiet state-years only**

{tab('t1', 'quiet', ranged=True)}

## 2. Statewide X per state-year ($M)
D's scenario range = the historical scenario range of C (look-alike spread, calibrated like C) widened where needed so that {LABEL[hl]}'s point estimate lies inside it; rough 10th-90th percentile of past outcomes.

{md(pd.DataFrame(rows))}

Historical scenario range coverage by model (own ranges, before widening):

{md(pd.DataFrame(rc))}

The widened range around {LABEL[hl]}'s point contained the actual in {int(bud.inside.sum())} of {len(bud)} state-years; the point was inside C's raw range in {int(bud.point_inside.sum())}.

## 3. T2 (damaged acres) and Z (illustrative relief allocation, 95% coverage assumption)
**T2, all state-years**

{tab('t2', 'all', 'acres')}

**T2, drought state-years only**

{tab('t2', 'drought', 'acres')}

**Z, all state-years**

{tab('z', 'all', '$')}

**Z, drought state-years only**

{tab('z', 'drought', '$')}

## 4. Trigger agreement (B2a vs {LABEL[hl]}; significant payout = share >= {SIG_SHARE:.0%} of insured value)
{LABEL[hl]} flags its top N counties per state-year, N = the number of counties B2a makes eligible that state-year.

{md(pr.reset_index().rename(columns={'index': 'flagging rule'}))}

{md(tbl)}

{note}

## 5. Known misses
State-years where B1 and all four candidates (A, B, C, D) were off by more than 50% (statewide X):

{md(misses) if len(misses) else 'None.'}

{LABEL[hl]}'s five largest dollar misses:

{md(own_misses)}

## 6. Verdict vs current practice (B2a / B2b)
{verdict_text(M, hl, bud)}
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
