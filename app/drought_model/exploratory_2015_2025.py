"""EXPLORATORY, after the official test: accuracy of the frozen M1 spec over 2015-2025 (DECISIONS.md Entry 4). Not an independent test; changes nothing frozen.

    python app/drought_model/exploratory_2015_2025.py --i-am-sure

Schemes: (a) fixed, train 2000-2014 and predict 2015-2025; (b) walk-forward, for each Y in 2015..2025 train on 2000..Y-1 and predict Y. 2015-2025 are built in memory through
organize_drought_severity.build_tables(include_test=True, i_am_sure=True) (the guarded path). Writes only results/exploratory_2015_2025.md and results/exploratory_2015_2025_predictions.csv.
Task A is reported as a ranking only (no probabilities, DECISIONS.md Entry 3).
"""
import argparse
import re
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

import models as M
from common import O, REPO, RESULTS, TASKS, task_rows

TAG = "exploratory, after the official test"
YEARS = list(range(2015, 2026))
METHODS = ["Persistence", "Climatology", "Most common level", "M1 (frozen)"]
SCHEMES = {"fixed": "Fixed: train 2000-2014", "wf": "Walk-forward: train 2000..Y-1"}


def fit_predict(tr, te, t):
    """-> DataFrame with M1 and baseline predictions for te (fitted on tr only)."""
    out = te[["fips", "county_name", "state_alpha", "year"]].copy()
    out["start"], out["y"], out["worse"] = te[t["start"]].astype(int), te[t["y"]].astype(int), te[t["worse"]].astype(int)
    for key, cls in [("Persistence", M.Persistence), ("Climatology", M.Climatology), ("Most common level", M.MostCommon), ("M1 (frozen)", M.M1Logit)]:
        m = cls().fit(tr, t)
        out[f"p_{key}"], out[f"lvl_{key}"] = m.proba(te, t), m.level(te, t)
    if t is TASKS["B"]:                                              # Task B only: how many inputs fall outside the fold's training range
        lo, hi = tr[t["feats"]].min(), tr[t["feats"]].max()
        x = te[t["feats"]]
        out["n_outside_range"] = ((x < lo) | (x > hi)).sum(axis=1).to_numpy()
    return out


def run_scheme(feat, task, scheme):
    t = TASKS[task]
    rows = task_rows(feat, task)
    if scheme == "fixed":
        return fit_predict(rows[rows.year <= 2014], rows[rows.year.isin(YEARS)], t)
    return pd.concat([fit_predict(rows[rows.year < y], rows[rows.year == y], t) for y in YEARS], ignore_index=True)


def mets(d, task):
    res = {}
    for k in METHODS:
        p, lv = d[f"p_{k}"].to_numpy(), d[f"lvl_{k}"].to_numpy()
        auc = 0.5 if k in ("Persistence", "Most common level") else (roc_auc_score(d.worse, p) if d.worse.nunique() == 2 else np.nan)
        res[k] = {"auc": auc, "brier": float(np.mean((p - d.worse) ** 2)), "exact": float((lv == d.y).mean()), "within1": float((np.abs(lv - d.y) <= 1).mean()), "n": len(d)}
    return res


def fmt_mets(rows, task):
    """rows: list of (label, mets dict) -> markdown. Task A: no Brier (ranking only)."""
    head = "| Scheme / window | Method | AUC | " + ("Brier | " if task == "B" else "") + "Exact level | Within 1 |"
    lines = [head, "|---|---|---|" + ("---|" if task == "B" else "") + "---|---|"]
    for lab, m in rows:
        for k in METHODS:
            r = m[k]
            auc = "0.500 (const.)" if k in ("Persistence", "Most common level") else f"{r['auc']:.3f}"
            lines.append(f"| {lab} | {k} | {auc} | " + (f"{r['brier']:.3f} | " if task == "B" else "") + f"{r['exact']:.1%} | {r['within1']:.1%} |")
    return "\n".join(lines)


def parse_official(task):
    """Official 2016-2025 test numbers (frozen M1 and baselines) read from results/test_report.md."""
    txt = (RESULTS / "test_report.md").read_text()
    sec = txt.split(f"## Task {task}:")[1].split("\n## ")[0]
    out = {}
    for name, key in [("Persistence", "Persistence"), ("Climatology", "Climatology"), ("M1 logistic (frozen)", "M1 (frozen)")]:
        row = [l for l in sec.splitlines() if l.startswith(f"| {name} |")][0]
        c = [x.strip() for x in row.strip("|").split("|")]
        v = c[1:]
        if task == "B":
            out[key] = {"auc": 0.5 if "const" in v[0] else float(v[0]), "brier": float(v[1]), "exact": float(v[2].strip("%")) / 100, "within1": float(v[3].strip("%")) / 100}
        else:
            out[key] = {"auc": 0.5 if "const" in v[0] else float(v[0]), "brier": np.nan, "exact": float(v[1].strip("%")) / 100, "within1": float(v[2].strip("%")) / 100}
    return out


def per_year(d, task):
    lines = ["| Year | M1 AUC | M1 exact | M1 within 1 | Persistence exact | Persistence within 1 | Climatology AUC |", "|---|---|---|---|---|---|---|"]
    for y, g in d.groupby("year"):
        m = mets(g, task)
        a = lambda r: "–" if np.isnan(r["auc"]) else f"{r['auc']:.3f}"
        lines.append(f"| {y} | {a(m['M1 (frozen)'])} | {m['M1 (frozen)']['exact']:.1%} | {m['M1 (frozen)']['within1']:.1%} | {m['Persistence']['exact']:.1%} | {m['Persistence']['within1']:.1%} | {a(m['Climatology'])} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--i-am-sure", action="store_true", help="2015-2025 are built in memory (exploratory, after the official test)")
    a = ap.parse_args()
    if not a.i_am_sure:
        print("Refusing to run without --i-am-sure (it builds 2015-2025 through the guarded path).")
        return 2
    feat = O.build_tables(REPO, include_test=True, i_am_sure=True)["feat"]      # guarded path; nothing is written to drought_severity_data/
    print("built", feat.year.min(), "-", feat.year.max(), len(feat), "rows")
    R, official = {}, {t: parse_official(t) for t in TASKS}
    for task in TASKS:
        for sc in SCHEMES:
            R[(task, sc)] = run_scheme(feat, task, sc)

    md = [f"# EXPLORATORY, after the official test: frozen M1 over 2015-2025\n",
          f"**These years were already scored once (2016-2025 in the official test, 2015 in the official validation window); this is not an independent test and does not replace `test_report.md`. Every table below is {TAG}.** No model, feature, setting or artifact was changed (DECISIONS.md Entry 4).\n",
          "Schemes: **Fixed** = train on 2000-2014, predict 2015-2025 once. **Walk-forward** = for each Y in 2015..2025 train on 2000..Y-1, predict Y (so later years see the 2016-2025 labels of earlier years). "
          "M1 settings are exactly the frozen ones; imputers, scalers and base rates are refit per fold; rain normals and irrigation averages are built from strictly earlier years. Task A is a ranking only (no probabilities). "
          "Baselines are refit on the same training years as M1.\n"]
    for task in TASKS:
        t = TASKS[task]
        rows = []
        for sc, name in SCHEMES.items():
            rows.append((f"{name}, 2015-2025", mets(R[(task, sc)], task)))
        md.append(f"## {t['name']}, pooled 2015-2025 ({TAG})\n\n" + fmt_mets(rows, task) + "\n")
        # same years as the official test
        cmp_rows = [("Official: train 2000-2015, 2016-2025 (test_report.md)", {k: {**v, "n": 0} for k, v in official[task].items()} | {"Most common level": {"auc": 0.5, "brier": np.nan, "exact": np.nan, "within1": np.nan, "n": 0}})]
        for sc, name in SCHEMES.items():
            cmp_rows.append((f"{name}, 2016-2025 only", mets(R[(task, sc)][R[(task, sc)].year >= 2016], task)))
        cmp_txt = fmt_mets(cmp_rows, task).replace("| NaN", "| –").replace("nan%", "–")
        cmp_txt = "\n".join(l for l in cmp_txt.splitlines() if not (l.startswith("| Official") and "| Most common level |" in l))
        md.append(f"### Task {task}: compared with the official 2016-2025 numbers, same years ({TAG})\n\n" + cmp_txt + "\n")
        y15 = [(f"{name}, 2015 only", mets(R[(task, sc)][R[(task, sc)].year == 2015], task)) for sc, name in SCHEMES.items()]
        md.append(f"### Task {task}: 2015 called out separately ({TAG}; 2015 is the one year the official test did not cover)\n\n" + fmt_mets(y15, task) + "\n")
        for sc, name in SCHEMES.items():
            md.append(f"### Task {task}: one row per year, {name} ({TAG})\n\n" + per_year(R[(task, sc)], task) + "\n")
    # Task B per state-year, calibration, for-the-map
    fb, wb = R[("B", "fixed")], R[("B", "wf")]
    sy = fb.groupby(["state_alpha", "year"]).agg(actual=("worse", "mean"), fixed=("p_M1 (frozen)", "mean")).join(wb.groupby(["state_alpha", "year"]).agg(wf=("p_M1 (frozen)", "mean"))).reset_index()
    lines = [f"| State-year | Actual worsening rate | Fixed: predicted | Walk-forward: predicted |", "|---|---|---|---|"]
    for r in sy.itertuples():
        b = "**" if r.year == 2015 else ""
        lines.append(f"| {b}{r.state_alpha} {r.year}{b} | {b}{r.actual:.0%}{b} | {b}{r.fixed:.0%}{b} | {b}{r.wf:.0%}{b} |")
    sy16 = sy[sy.year >= 2016]
    md.append(f"## Task B: predicted vs actual worsening rate per state-year ({TAG}; 2015 in bold)\n\n" + "\n".join(lines) +
              f"\n\nCorrelation of predicted and actual state-year rate across the {len(sy)} state-years of 2015-2025: Fixed {np.corrcoef(sy.actual, sy.fixed)[0, 1]:.2f}, Walk-forward {np.corrcoef(sy.actual, sy.wf)[0, 1]:.2f} "
              f"(2016-2025 only, {len(sy16)} state-years: Fixed {np.corrcoef(sy16.actual, sy16.fixed)[0, 1]:.2f}, Walk-forward {np.corrcoef(sy16.actual, sy16.wf)[0, 1]:.2f}; the official test reported 0.78).\n")
    for sc, name in SCHEMES.items():
        d = R[("B", sc)]
        q = pd.qcut(d["p_M1 (frozen)"].rank(method="first"), 10, labels=False)
        g = d.groupby(q).agg(n=("worse", "size"), mean_pred=("p_M1 (frozen)", "mean"), actual=("worse", "mean"))
        md.append(f"### Task B calibration by decile, {name}, 2015-2025 ({TAG})\n\n| Decile | n | Mean predicted | Actual rate |\n|---|---|---|---|\n" +
                  "\n".join(f"| {i + 1} | {int(r.n)} | {r.mean_pred:.2f} | {r.actual:.2f} |" for i, r in enumerate(g.itertuples())) + "\n")
    # for the map
    lines = ["| Year | Fixed: exact | within 1 | off by 2+ | counties with an input outside range | Walk-forward: exact | within 1 | off by 2+ | outside range | Persistence: exact | within 1 | off by 2+ |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for y in YEARS:
        cells = []
        for d in (fb, wb):
            g = d[d.year == y]
            err = np.abs(g["lvl_M1 (frozen)"] - g.y)
            cells += [f"{(err == 0).mean():.0%}", f"{(err <= 1).mean():.0%}", f"{(err >= 2).mean():.0%}", f"{(g.n_outside_range > 0).mean():.0%}"]
        g = fb[fb.year == y]
        perr = np.abs(g["lvl_Persistence"] - g.y)
        cells += [f"{(perr == 0).mean():.0%}", f"{(perr <= 1).mean():.0%}", f"{(perr >= 2).mean():.0%}"]
        lines.append(f"| {y} | " + " | ".join(cells) + " |")
    allm = []
    for d, name in ((fb, "Fixed"), (wb, "Walk-forward")):
        err = np.abs(d["lvl_M1 (frozen)"] - d.y)
        allm.append(f"{name}: exact {(err == 0).mean():.0%}, within one {(err <= 1).mean():.0%}, off by 2+ {(err >= 2).mean():.0%}, counties with an input outside the training range {(d.n_outside_range > 0).mean():.0%}")
    md.append(f"## For the map: Task B simulation level vs the observed level, per year ({TAG})\n\nThe simulation helper's predicted level (start level plus the training median step when P(worse) >= 0.5) with observed weather (precip x 1.0), compared with the observed worst level Apr 1-Aug 13. "
              "'Outside range' = share of counties with at least one Task B input beyond the fold's training min/max. Persistence = keeping the Apr 1 level.\n\n" + "\n".join(lines) + "\n\nPooled 2015-2025: " + "; ".join(allm) + ".\n")
    (RESULTS / "exploratory_2015_2025.md").write_text("\n".join(md))
    # CSV of county-year predictions (Task A: no probabilities, only a within-year rank percentile)
    csv = []
    for (task, sc), d in R.items():
        c = d[["fips", "county_name", "state_alpha", "year", "start", "y", "worse", "lvl_M1 (frozen)", "lvl_Persistence", "lvl_Climatology"]].copy()
        c.columns = ["fips", "county_name", "state_alpha", "year", "start_level", "actual_level", "actual_worse", "pred_level_M1", "pred_level_persistence", "pred_level_climatology"]
        c.insert(0, "task", task)
        c.insert(0, "scheme", sc)
        c["p_worse_M1"] = d["p_M1 (frozen)"] if task == "B" else np.nan
        c["rank_pct_within_year_M1"] = d.groupby("year")["p_M1 (frozen)"].rank(pct=True)
        c["n_inputs_outside_training_range"] = d["n_outside_range"] if task == "B" else np.nan
        c["label"] = TAG
        csv.append(c)
    pd.concat(csv, ignore_index=True).to_csv(RESULTS / "exploratory_2015_2025_predictions.csv", index=False)
    print("wrote exploratory_2015_2025.md and exploratory_2015_2025_predictions.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
