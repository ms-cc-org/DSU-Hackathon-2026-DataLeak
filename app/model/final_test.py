"""Section 5: the final held-out test (2016-2025). Run ONCE, after the model is final.

    python app/model/final_test.py --i-am-sure

(Run it as a script from the repo root; `python -m app.model.final_test` does not work here because `app/` is not a package and
the root-level `data/` folder would shadow `data.py`.)

Retrains every model on 2000-2015 with the hyper-parameters tuned in evaluate.py and the calibration factors k from
results/calibration.csv (walk-forward 2006-2012; no re-tuning, no re-fitting of k), predicts 2016-2025, and writes
results/test_report.md plus csv files. The model is frozen: do not change anything after seeing these results; report failures too.
Expected hard case, declared in advance: Iowa 2020 (derecho: wind loss, mostly not drought-coded).
"""
import argparse
import json
import pathlib
import sys

import numpy as np
import pandas as pd

from budget import residual_pool
from data import RESULTS, load_usable
from evaluate import (CAPTURE_NOISE, LABEL, MODELS, RANGED, RESAMPLED, WAPE_NOISE, apply_k, attach_coverage, budget_range_rows,
                      f_cov, f_pct, fit_predict, known_misses, md, metrics, range_rows, state_year_points)
from data import add_year_class

OFFICIAL = "Version 1 – official test, model frozen before seeing test data"
EXPECTED_MISS = ("IA", 2020)


def ref_table(m, chosen):
    """Capture, WAPE, AUC, calibration, range coverage per model; chosen model starred; B0 and B1 first, then the rest."""
    r = m[m.model.isin(MODELS)].set_index("model")
    order = ["B0", "B1", chosen] + [x for x in MODELS if x not in ("B0", "B1", chosen)]
    rows = []
    for name in order:
        x = r.loc[name]
        rows.append({"Model": ("★ " + LABEL[name] + " (chosen)") if name == chosen else LABEL[name],
                     "Budget capture (top-20)": f_pct(x.capture_top20, 1), "WAPE": f"{x.wape:.2f}",
                     "Any-payout AUC": "–" if pd.isna(x.auc_any_payout) else f"{x.auc_any_payout:.3f}",
                     "Calibration (Σpred/Σactual)": f"{x.calibration:.2f}",
                     "80% range coverage": f_cov(x) if name in RANGED else "–"})
    rnd = m[m.model == "Random"]
    if len(rnd):
        rows.append({"Model": "*Random counties (reference)*", "Budget capture (top-20)": f"*{f_pct(rnd.capture_top20.iloc[0], 1)}*",
                     "WAPE": "–", "Any-payout AUC": "–", "Calibration (Σpred/Σactual)": "–", "80% range coverage": "–"})
    return md(pd.DataFrame(rows))


def verdict_text(m, chosen, bud, tot_chosen):
    g = lambda grp, model: m[(m.group == grp) & (m.model == model)].iloc[0]
    c, b1, rnd = g("all", chosen), g("all", "B1"), m[(m.group == "all") & (m.model == "Random")].iloc[0]
    d_cap, wape_red = c.capture_top20 - b1.capture_top20, 1 - c.wape / b1.wape
    if d_cap > CAPTURE_NOISE and wape_red > WAPE_NOISE:
        kind = "a clear win"
    elif d_cap < -CAPTURE_NOISE and wape_red < -WAPE_NOISE:
        kind = "a loss"
    elif abs(d_cap) <= CAPTURE_NOISE and abs(wape_red) <= WAPE_NOISE:
        kind = "a tie"
    else:
        kind = "mixed (better on one measure, within noise or worse on the other)"
    s = [f"Against B1 (the drought-map rule) the frozen model, {LABEL[chosen]}, is {kind} on the held-out years: budget capture {c.capture_top20:.1%} vs "
         f"{b1.capture_top20:.1%} (random {rnd.capture_top20:.1%}) and county-level dollar error (WAPE) {c.wape:.2f} vs {b1.wape:.2f} "
         f"({abs(wape_red):.0%} {'lower' if wape_red > 0 else 'higher'}), judged against noise bands of {CAPTURE_NOISE * 100:.0f} capture points and {WAPE_NOISE:.0%} of WAPE."]
    parts = []
    for grp, name in [("drought", "drought years"), ("quiet", "quiet years")]:
        sub = m[(m.group == grp) & (m.model == chosen)]
        if len(sub):
            x, y = sub.iloc[0], g(grp, "B1")
            parts.append(f"{name} ({int(x.state_years)} state-year{'s' if int(x.state_years) != 1 else ''}): capture {x.capture_top20:.1%} vs {y.capture_top20:.1%}, WAPE {x.wape:.2f} vs {y.wape:.2f}, "
                         f"Σpred/Σactual {x.calibration:.2f} vs {y.calibration:.2f}")
    s.append("Split by year type, " + "; ".join(parts) + ".")
    s.append(f"Overall calibration is {c.calibration:.2f} for {LABEL[chosen]} vs {b1.calibration:.2f} for B1 (1.00 = the statewide budget is the right size).")
    s.append(f"The rough 80% budget range contained the actual statewide payout in {int(bud.inside.sum())} of {len(bud)} state-years ({bud.inside.mean():.0%}; target about 80%).")
    if EXPECTED_MISS in tot_chosen.index:
        e = tot_chosen.loc[EXPECTED_MISS]
        s.append(f"Iowa 2020, the derecho year declared in advance as an expected miss (wind, not drought), was predicted at ${e.pred / 1e6:,.1f}M against ${e.actual / 1e6:,.1f}M actual.")
    return " ".join(s)


def run_final(train_splits, eval_split, out_dir, allow_test=False, label=OFFICIAL):
    cfg = json.load(open(RESULTS / "chosen_model.json"))
    method = json.load(open(RESULTS / "range_method.json"))["method"]
    params, chosen = cfg["params"], cfg["chosen"]
    train = load_usable(*train_splits)
    test = load_usable(eval_split, allow_test=allow_test)
    cal = pd.read_csv(RESULTS / "calibration.csv")
    pred = apply_k(fit_predict(train, test, params), cal)                    # k from walk-forward 2006-2012

    oos = pd.read_csv(RESULTS / "oos_predictions.csv", dtype={"fips": str})   # calibrated walk-forward + validation predictions
    cov = range_rows(pred, {c: residual_pool(oos, c) for c in RESAMPLED}, "t1")
    m = pd.concat([attach_coverage(metrics(pred), cov)])
    bud = budget_range_rows(cov, chosen, method)
    pts = state_year_points(pred, "t1")
    cls = add_year_class(pred).drop_duplicates(["state_alpha", "year"]).set_index(["state_alpha", "year"]).sy_class
    liab = pred.groupby(["state_alpha", "year"]).liability.sum()
    misses, _ = known_misses(pts, liab)

    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    m.to_csv(out_dir / "test_metrics.csv", index=False)
    pred.drop(columns=[c for c in pred if c.startswith("score")]).to_csv(out_dir / "test_predictions.csv", index=False)
    cov.to_csv(out_dir / "test_range_coverage.csv", index=False)
    bud.reset_index().to_csv(out_dir / "test_budget_range.csv", index=False)

    years = f"{int(test.year.min())}-{int(test.year.max())}"
    tr_years = f"{int(train.year.min())}-{int(train.year.max())}"
    # statewide totals table: actual, frozen model's prediction, budget range, inside / outside, other models for reference
    p = pts.pivot_table(index=["state_alpha", "year"], columns="model", values="pred")
    act = pts.drop_duplicates(["state_alpha", "year"]).set_index(["state_alpha", "year"]).actual
    rows = []
    for (s, y), b in bud.sort_index(level=["state", "year"]).iterrows():
        row = {"state": s, "year": y, "type": cls[(s, y)], "actual $M": f"{act[(s, y)] / 1e6:,.1f}",
               f"{LABEL[chosen]} prediction $M": f"{p.loc[(s, y), chosen] / 1e6:,.1f}",
               "budget range $M (rough 80%)": f"{b.budget_low / 1e6:,.1f}–{b.budget_high / 1e6:,.1f}",
               "actual vs range": "inside ✓" if b.inside else "outside ✗"}
        for n in MODELS:
            if n != chosen:
                row[LABEL[n] + " $M"] = f"{p.loc[(s, y), n] / 1e6:,.1f}"
        rows.append(row)
    tot_chosen = pts[pts.model == chosen].set_index(["state_alpha", "year"])
    expected = ""
    if EXPECTED_MISS in tot_chosen.index:
        e = tot_chosen.loc[EXPECTED_MISS]
        expected = (f"- **Iowa 2020 (declared in advance as an expected miss).** The Aug 10, 2020 derecho caused wind losses that are mostly not coded as drought, "
                    f"so a drought-payout model should not predict them. {LABEL[chosen]} predicted ${e.pred / 1e6:,.1f}M against ${e.actual / 1e6:,.1f}M actual "
                    f"({'outside' if not bud.loc[EXPECTED_MISS].inside else 'inside'} its budget range).")
    text = f"""# Final test report ({years}): {label}

Models retrained on {tr_years} ({len(train)} rows) with the hyper-parameters from `results/params.json` (tuned on training walk-forward only)
and the calibration factors `results/calibration.csv` (k from walk-forward 2006-2012), predicting {len(test)} rows. Nothing was tuned or changed using these years.
**Headline model: {LABEL[chosen]}** (`results/chosen_model.json`: {cfg.get('headline_result', cfg['reason'])}). **Frozen for this test: {', '.join(LABEL[m] for m in cfg.get('frozen_models', [chosen]))}**;
all other models (baselines B0, B1, B2 and strategies A, C) are shown for reference. Budget range = the `{method}` range method, widened where needed so the headline
model's point estimate lies inside it, and rough. Amounts are drought payout in dollars (T1 x liability), summed over crops per county-year.
G (if present) is Built with PriorLabs-TabPFN (TabPFN v2 weights, Prior Labs License 1.1).

## 1. Summary, all state-years (T1 payout share)
{ref_table(m[m.group == 'all'], chosen)}

## 2. Statewide drought payout per state-year ($M)
{md(pd.DataFrame(rows))}

## 3. Drought years vs quiet years
Drought year = actual statewide payout >= 3% of insured dollars (grouping only). Quiet = all other state-years.

**Drought years**

{ref_table(m[m.group == 'drought'], chosen) if (m.group == 'drought').any() else 'No drought state-years in this window.'}

**Quiet years**

{ref_table(m[m.group == 'quiet'], chosen) if (m.group == 'quiet').any() else 'No quiet state-years in this window.'}

## 4. Known misses
State-years where every model's statewide total was off by more than 50%, with a one-line likely reason:

{md(misses.drop(columns=[c for c in misses if c.endswith(' $M') and c not in ('actual $M', LABEL[chosen] + ' $M')])) if len(misses) else 'None.'}

{expected}

## 5. Verdict vs B1
{verdict_text(m[m.target == 't1'] if 'target' in m else m, chosen, bud, tot_chosen)}
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
