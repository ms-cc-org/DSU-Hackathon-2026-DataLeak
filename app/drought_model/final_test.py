"""The held-out test (2016-2025) for the drought-severity models. Run ONCE, only when told to, after the models are frozen:

    python app/drought_model/final_test.py --i-am-sure

Refuses to run without --i-am-sure. Retrains the frozen models (results/chosen_models.json: M1 for both tasks, plus the baselines) on 2000-2015 and scores 2016-2025 once;
2016-2025 maps, weather and labels are built in memory by organize_drought_severity.build_tables(include_test=True, i_am_sure=True), which is the only place they are loaded.
Writes results/test_report.md. Nothing is tuned or changed after seeing the results.
Reporting decision (DECISIONS.md Entry 3): Task A is reported as a ranking (AUC) plus level accuracies only, with no probabilities shown; Task B shows Brier, calibration deciles and predicted worsening rates.
"""
import argparse
import json
import pathlib
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

import models as M
from common import O, REPO, RESULTS, TASKS, load_pre_test, task_rows
from evaluate import metrics_for

LABEL = {"Persistence": "Persistence", "Climatology": "Climatology", "Most common level": "Most common level", "M1": "M1 logistic", "M2": "M2 gradient boosting", "M3": "M3 kNN look-alikes"}
HIGHLIGHT = {("IA", 2023), ("NE", 2022), ("NE", 2023)}
CONST_AUC = ("Persistence", "Most common level")


def score(tr, te, t, key):
    cls = M.BASELINES.get(key) or M.MODELS[key]
    m = cls().fit(tr, t)
    p, lv = m.proba(te, t), m.level(te, t)
    y, w = te[t["y"]].to_numpy().astype(int), te[t["worse"]].astype(int).to_numpy()
    auc = 0.5 if key in CONST_AUC else roc_auc_score(w, p)
    return {"auc": auc, "brier": float(np.mean((p - w) ** 2)), "exact": float((lv == y).mean()), "within1": float((np.abs(lv - y) <= 1).mean())}, p


def side_by_side(task, keys, test, val, show_brier):
    head = "| Method | Test AUC | " + ("Test Brier | " if show_brier else "") + "Test exact level | Test within 1 | Val AUC | " + ("Val Brier | " if show_brier else "") + "Val exact level | Val within 1 |"
    lines = [head, "|---|" + "---|" * (head.count("|") - 2)]
    for k in keys:
        a, b = test[k], val[k]
        auc = lambda x: "0.500 (const.)" if k in CONST_AUC else f"{x['auc']:.3f}"
        cells = [LABEL[k] + (" (frozen)" if k == "M1" else ""), auc(a)] + ([f"{a['brier']:.3f}"] if show_brier else []) + [f"{a['exact']:.1%}", f"{a['within1']:.1%}", auc(b)] \
            + ([f"{b['brier']:.3f}"] if show_brier else []) + [f"{b['exact']:.1%}", f"{b['within1']:.1%}"]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def run_final(train_years, eval_years, out_path, include_test=False, label="Final test"):
    chosen = json.load(open(RESULTS / "chosen_models.json"))
    if include_test:
        df = O.build_tables(REPO, include_test=True, i_am_sure=True)["feat"]       # loads 2016-2025: only reachable through --i-am-sure
    else:
        df = load_pre_test()                                                        # <= 2015 only (used for the dry run on validation)
    out = [f"# {label}: drought-severity models, test years {eval_years[0]}-{eval_years[1]}\n",
           f"**Frozen before this run** (DECISIONS.md Entry 3): M1 logistic for Task A and for Task B (results/chosen_models.json), features and settings exactly as in the code. Trained on {train_years[0]}-{train_years[1]}, scored once on {eval_years[0]}-{eval_years[1]}. "
           "Baselines are fitted on the same training years. Validation = the 2013-2015 walk-forward numbers from `validation_report.md` (each year predicted from the years before it). "
           "Note: drought conditions by year for 2016-2025 were already discussed during the project, so treat this as a confirmatory test, not a blind one. "
           "Task A is a RANKING only: its probabilities are not calibrated (balanced class weights), so none are displayed, and Brier / calibration / predicted rates are shown for Task B only.\n"]
    summary = {}
    for task, t in TASKS.items():
        tr = task_rows(df[(df.year >= train_years[0]) & (df.year <= train_years[1])], task)
        te = task_rows(df[(df.year >= eval_years[0]) & (df.year <= eval_years[1])], task)
        keys = ["Persistence", "Climatology", "Most common level", "M1"]
        test, probs = {}, {}
        for k in keys:
            test[k], probs[k] = score(tr, te, t, k)
        oos = pd.read_csv(RESULTS / f"oos_predictions_{task}.csv", dtype={"fips": str})
        val = {k: v for k, v in metrics_for(oos, range(2013, 2016)).items() if k in keys}
        te = te.assign(p=probs["M1"], worse_i=te[t["worse"]].astype(float))
        summary[task] = {"test": test, "val": val}
        sec = [f"## {t['name']}\n", f"Rows scored: {len(te)} county-years; actual worsening rate {te.worse_i.mean():.0%} (validation 2013-2015: {oos[oos.year.isin([2013, 2014, 2015])].worse.mean():.0%}). "
                                    f"Start level = `{t['start']}`.\n", side_by_side(task, keys, test, val, show_brier=(task == "B")) + "\n"]
        sy_rows = []
        for (st, yr), g in te.groupby(["state_alpha", "year"]):
            auc = roc_auc_score(g.worse_i.astype(int), g.p) if g.worse_i.nunique() == 2 else np.nan
            sy_rows.append({"state": st, "year": int(yr), "actual": g.worse_i.mean(), "predicted": g.p.mean(), "auc": auc, "n": len(g)})
        sy = pd.DataFrame(sy_rows)
        if task == "B":
            lines = ["| State-year | Actual worsening rate | Predicted worsening rate (M1) |", "|---|---|---|"]
            for r in sy.itertuples():
                b = "**" if (r.state, r.year) in HIGHLIGHT else ""
                lines.append(f"| {b}{r.state} {r.year}{b} | {b}{r.actual:.0%}{b} | {b}{r.predicted:.0%}{b} |")
            q = pd.qcut(te.p.rank(method="first"), 10, labels=False)
            dec = te.groupby(q).agg(n=("p", "size"), mean_pred=("p", "mean"), actual=("worse_i", "mean"))
            dl = ["| Decile | n | Mean predicted | Actual rate |", "|---|---|---|---|"] + [f"| {i + 1} | {int(r.n)} | {r.mean_pred:.2f} | {r.actual:.2f} |" for i, r in enumerate(dec.itertuples())]
            corr = float(np.corrcoef(sy.actual, sy.predicted)[0, 1])
            sec += [f"### Calibration by decile of predicted risk (frozen M1, test years)\n\n" + "\n".join(dl) + "\n",
                    f"### Worsening rate per state-year, predicted vs actual (bold = the drought years IA 2023, NE 2022, NE 2023)\n\n" + "\n".join(lines) +
                    f"\n\nCorrelation of predicted and actual state-year rate over the {len(sy)} state-years: {corr:.2f}.\n"]
        else:
            lines = ["| State-year | Actual worsening rate | Within-state-year AUC (M1 ranking) | Counties |", "|---|---|---|---|"]
            for r in sy.itertuples():
                b = "**" if (r.state, r.year) in HIGHLIGHT else ""
                a = "–" if np.isnan(r.auc) else f"{r.auc:.2f}"
                lines.append(f"| {b}{r.state} {r.year}{b} | {b}{r.actual:.0%}{b} | {b}{a}{b} | {r.n} |")
            sec += ["### Worsening rate per state-year and how well M1 ranks its counties (no probabilities shown; bold = IA 2023, NE 2022, NE 2023)\n\n" + "\n".join(lines) + "\n"]
        out += sec
    # plain comparison lines
    sa, sb = summary["A"], summary["B"]
    out.append("## Reading the numbers\n\n"
               f"- Task B (in-season): frozen M1 AUC {sb['test']['M1']['auc']:.3f} on the test years (validation {sb['val']['M1']['auc']:.3f}) vs climatology {sb['test']['Climatology']['auc']:.3f}; exact level {sb['test']['M1']['exact']:.1%} vs persistence {sb['test']['Persistence']['exact']:.1%}; Brier {sb['test']['M1']['brier']:.3f} vs climatology {sb['test']['Climatology']['brier']:.3f}.\n"
               f"- Task A (outlook, ranking only): frozen M1 AUC {sa['test']['M1']['auc']:.3f} (validation {sa['val']['M1']['auc']:.3f}) vs climatology {sa['test']['Climatology']['auc']:.3f}; exact level {sa['test']['M1']['exact']:.1%} vs persistence {sa['test']['Persistence']['exact']:.1%}, "
               f"within one level {sa['test']['M1']['within1']:.1%} vs {sa['test']['Persistence']['within1']:.1%}.\n")
    pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(out_path).write_text("\n".join(out))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--i-am-sure", action="store_true", help="confirm the models are frozen and the held-out 2016-2025 data may be built and scored")
    a = ap.parse_args()
    if not a.i_am_sure:
        print("Refusing to run: this loads the held-out 2016-2025 maps, weather and labels, which must be used once, at the very end.\nRe-run with --i-am-sure when the models are final.")
        return 2
    run_final((2000, 2015), (2016, 2025), RESULTS / "test_report.md", include_test=True, label="Final test (official, run once)")
    print("wrote", RESULTS / "test_report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
