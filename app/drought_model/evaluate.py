"""Walk-forward evaluation of the drought-severity baselines and models (Task A and Task B).   python app/drought_model/evaluate.py

Protocol (fixed in DECISIONS.md Entry 1 before any result was seen): for Y = 2006..2015 train on 2000..Y-1 and predict Y; 2006-2012 is "walk-forward",
2013-2015 is "validation" (reported separately, never used for selection). Selection per task: best walk-forward AUC for worse; within 0.02 -> simplest (M1 < M3 < M2).
Only years <= 2015 are read. Writes results/*.csv, results/chosen_models.json and results/validation_report.md.
"""
import json

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

import models as M
from common import LEVELS, RESULTS, TASKS, load_pre_test, task_rows

WF, VAL = range(2006, 2013), range(2013, 2016)
TIE_BAND = 0.02
ALLM = list(M.BASELINES.items()) + [(k, v) for k, v in M.MODELS.items()]
LABEL = {"Persistence": "Persistence", "Climatology": "Climatology", "Most common level": "Most common level", "M1": "M1 logistic", "M2": "M2 gradient boosting", "M3": "M3 kNN look-alikes"}


def walk_forward(df, task):
    t = TASKS[task]
    rows = []
    for y in range(2006, 2016):
        tr, te = task_rows(df[df.year < y], task), task_rows(df[df.year == y], task)
        out = te[["fips", "county_name", "state_alpha", "year", t["start"], t["y"], t["worse"]]].copy()
        out = out.rename(columns={t["start"]: "start", t["y"]: "y", t["worse"]: "worse"})
        for key, cls in ALLM:
            m = cls().fit(tr, t)
            out[f"p_{key}"], out[f"lvl_{key}"] = m.proba(te, t), m.level(te, t)
        rows.append(out)
    return pd.concat(rows, ignore_index=True)


def metrics_for(oos, years):
    s = oos[oos.year.isin(list(years))]
    res = {}
    for key, _ in ALLM:
        p, lv = s[f"p_{key}"].to_numpy(), s[f"lvl_{key}"].to_numpy()
        auc = 0.5 if key in ("Persistence", "Most common level") else roc_auc_score(s.worse, p)   # constant within every fold: no ranking information
        res[key] = {"n": len(s), "auc": auc, "brier": float(np.mean((p - s.worse) ** 2)),
                    "exact": float((lv == s.y).mean()), "within1": float((np.abs(lv - s.y) <= 1).mean())}
    return res


def select(wf_metrics):
    cand = {k: wf_metrics[k]["auc"] for k in M.MODELS}
    best = max(cand.values())
    tied = [k for k in M.SIMPLEST_FIRST if cand[k] >= best - TIE_BAND]
    return tied[0], tied, cand


def deciles(oos, key):
    q = pd.qcut(oos[f"p_{key}"].rank(method="first"), 10, labels=False)
    g = oos.groupby(q).agg(n=("worse", "size"), mean_pred=(f"p_{key}", "mean"), actual_rate=("worse", "mean"))
    return g.reset_index(drop=True).rename_axis("decile").reset_index().assign(decile=lambda d: d.decile + 1)


def importance(df, task, key, repeats=10):
    """Permutation importance (drop in AUC) of model `key` trained 2000-2012 and scored on 2013-2015."""
    t = TASKS[task]
    tr, te = task_rows(df[df.year <= 2012], task), task_rows(df[df.year.isin(list(VAL))], task)
    m = M.MODELS[key]().fit(tr, t)
    base = roc_auc_score(te[t["worse"]].astype(int), m.proba(te, t))
    rng = np.random.default_rng(0)
    rows = []
    for f in t["feats"]:
        drops = []
        for _ in range(repeats):
            x = te.copy()
            x[f] = rng.permutation(x[f].to_numpy())
            drops.append(base - roc_auc_score(te[t["worse"]].astype(int), m.proba(x, t)))
        rows.append({"feature": f, "auc_drop_mean": np.mean(drops), "auc_drop_sd": np.std(drops)})
    return pd.DataFrame(rows).sort_values("auc_drop_mean", ascending=False).reset_index(drop=True), base


class _M2Free(M.M2HGB):
    def _fit(self, X, y):
        from sklearn.ensemble import HistGradientBoostingClassifier
        self.m_ = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, min_samples_leaf=30, max_iter=200, early_stopping=False, random_state=0).fit(X, y)


class _M2NoLevelSign(M.M2HGB):
    def _fit(self, X, y):
        from sklearn.ensemble import HistGradientBoostingClassifier
        cst = [0 if f in ("level_last_map", "level_apr1", "prev_fall_level", "nbr_level_last") else c for f, c in zip(self.feats_, M.monotone(self.feats_))]
        self.m_ = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, min_samples_leaf=30, max_iter=200, early_stopping=False, random_state=0, monotonic_cst=cst).fit(X, y)


def m2_diagnostics(df):
    """DIAGNOSTIC ONLY (never used for selection): M2 as specified vs M2 without monotone constraints vs M2 without the +1 sign on the start/level features; and the sign of M1's start-level coefficient."""
    rows, signs = [], {}
    for task in TASKS:
        t = TASKS[task]
        for label, cls in [("M2 as specified (monotone constraints)", M.M2HGB), ("M2 without constraints", _M2Free), ("M2 constraints, but no sign forced on level inputs", _M2NoLevelSign)]:
            P = []
            for y in range(2006, 2016):
                tr, te = task_rows(df[df.year < y], task), task_rows(df[df.year == y], task)
                P.append(pd.DataFrame({"year": te.year, "w": te[t["worse"]].astype(int), "p": cls().fit(tr, t).proba(te, t)}))
            P = pd.concat(P)
            f = lambda q: roc_auc_score(q.w, q.p)
            rows.append({"task": task, "variant": label, "wf_auc": f(P[P.year <= 2012]), "val_auc": f(P[P.year >= 2013]), "pooled_auc": f(P)})
        m1 = M.M1Logit().fit(task_rows(df[df.year <= 2012], task), t)
        names = list(m1.imp_.get_feature_names_out(m1.feats_))
        coef = pd.Series(m1.m_.coef_[0], index=names)
        signs[task] = float(coef[t["start"]])
    return pd.DataFrame(rows), signs


def fmt_table(wf_m, val_m):
    lines = ["| Method | WF AUC | WF Brier | WF exact level | WF within 1 | Val AUC | Val Brier | Val exact level | Val within 1 |", "|---|---|---|---|---|---|---|---|---|"]
    for key, _ in ALLM:
        a, b = wf_m[key], val_m[key]
        auc = lambda x: "0.500 (const.)" if key in ("Persistence", "Most common level") else f"{x['auc']:.3f}"
        lines.append(f"| {LABEL[key]} | {auc(a)} | {a['brier']:.3f} | {a['exact']:.1%} | {a['within1']:.1%} | {auc(b)} | {b['brier']:.3f} | {b['exact']:.1%} | {b['within1']:.1%} |")
    return "\n".join(lines)


def state_year_table(oos, task):
    keys = [k for k, _ in ALLM if k != "Persistence"]
    sy = oos.groupby(["state_alpha", "year"]).agg(actual_rate=("worse", "mean"), **{k: (f"p_{k}", "mean") for k in keys}).reset_index()
    pick = sy[((sy.state_alpha == "IA") & sy.year.isin([2012, 2013])) | ((sy.state_alpha == "NE") & (sy.year == 2012))]
    cols = ["state_alpha", "year", "actual_rate"] + keys
    lines = ["| State-year | Actual worsening rate | " + " | ".join(LABEL[k] for k in keys) + " |", "|---|---|" + "---|" * len(keys)]
    for d in pick.to_dict("records"):
        lines.append(f"| {d['state_alpha']} {d['year']} | {d['actual_rate']:.0%} | " + " | ".join(f"{d[k]:.0%}" for k in keys) + " |")
    corr = {k: float(np.corrcoef(sy.actual_rate, sy[k])[0, 1]) for k in keys}
    return "\n".join(lines), sy, corr


def main():
    RESULTS.mkdir(exist_ok=True)
    df = load_pre_test()
    print("rows", len(df), "years", df.year.min(), df.year.max())
    out, chosen, report = {}, {}, {}
    for task in TASKS:
        oos = walk_forward(df, task)
        oos.to_csv(RESULTS / f"oos_predictions_{task}.csv", index=False)
        wf_m, val_m, all_m = metrics_for(oos, WF), metrics_for(oos, VAL), metrics_for(oos, range(2006, 2016))
        best, tied, cand = select(wf_m)
        beats_clim = wf_m[best]["auc"] > wf_m["Climatology"]["auc"]
        beats_pers_lvl = wf_m[best]["exact"] > wf_m["Persistence"]["exact"]
        dec = deciles(oos, best)
        imp, base_auc = importance(df, task, best)
        dec.to_csv(RESULTS / f"calibration_deciles_{task}.csv", index=False)
        imp.to_csv(RESULTS / f"permutation_importance_{task}.csv", index=False)
        sy_md, sy, corr = state_year_table(oos, task)
        chosen[task] = {"chosen": best, "tied_within_0.02": tied, "walk_forward_auc": cand, "beats_climatology_auc": bool(beats_clim),
                        "beats_persistence_exact_level_walk_forward": bool(beats_pers_lvl), "validation_auc": {k: val_m[k]["auc"] for k in M.MODELS}}
        report[task] = dict(wf=wf_m, val=val_m, all=all_m, best=best, tied=tied, cand=cand, dec=dec, imp=imp, base_auc=base_auc, sy_md=sy_md, corr=corr, oos=oos)
        print(task, "chosen", best, {k: round(v, 3) for k, v in cand.items()}, "| clim AUC", round(wf_m["Climatology"]["auc"], 3))
    json.dump(chosen, open(RESULTS / "chosen_models.json", "w"), indent=2)
    import simulate
    sim = simulate.example_ia_2012(train_through=2011)       # out-of-sample example for the validation report
    diag, signs = m2_diagnostics(df)
    diag.to_csv(RESULTS / "m2_diagnostics.csv", index=False)
    write_report(report, chosen, sim, diag, signs)
    print("report ->", RESULTS / "validation_report.md")


def write_report(R, chosen, sim_text, diag, signs):
    checks = (RESULTS.parents[2] / "drought_severity_data" / "checks.md").read_text()
    A, B = R["A"], R["B"]
    pct = lambda x: f"{x:.0%}"
    out = ["# Drought-severity model: validation report (walk-forward 2006-2012, validation 2013-2015)\n",
           "Only years <= 2015 were used. Models and settings were fixed in `DECISIONS.md` before any result was seen; nothing was tuned. "
           "Walk-forward = train on 2000..Y-1, predict Y. AUC and Brier are for `worse` (did the worst level get worse than the start level); exact / within-1 are for the predicted level 0-5 "
           "(model level = start level + the training median step when P(worse) >= 0.5). Persistence cannot rank (it predicts no change), so its AUC is 0.5 by construction.\n"]
    for task, r in (("A", A), ("B", B)):
        t = TASKS[task]
        out.append(f"## {t['name']}\n\nStart level = `{t['start']}`. Label rate of `worse`: walk-forward {r['oos'][r['oos'].year.isin(list(WF))].worse.mean():.0%}, validation {r['oos'][r['oos'].year.isin(list(VAL))].worse.mean():.0%}.\n")
        out.append(fmt_table(r["wf"], r["val"]) + "\n")
        c = chosen[task]
        out.append(f"**Chosen model: {LABEL[r['best']]}.** Rule (fixed in advance): best walk-forward AUC; models within {TIE_BAND} of the best are tied and the simplest wins (M1 < M3 < M2). "
                   f"Walk-forward AUC: " + ", ".join(f"{LABEL[k]} {v:.3f}" for k, v in r["cand"].items()) + f"; tied set: {[LABEL[k] for k in r['tied']]}. "
                   f"Validation AUC of the chosen model: {r['val'][r['best']]['auc']:.3f}. "
                   f"Beats climatology on AUC: **{'yes' if c['beats_climatology_auc'] else 'no'}** ({r['wf'][r['best']]['auc']:.3f} vs {r['wf']['Climatology']['auc']:.3f}); "
                   f"beats persistence on exact level (walk-forward): **{'yes' if c['beats_persistence_exact_level_walk_forward'] else 'no'}** "
                   f"({r['wf'][r['best']]['exact']:.1%} vs {r['wf']['Persistence']['exact']:.1%}).\n")
        out.append(f"### Worsening rate per state-year, predicted vs actual ({LABEL[r['best']]} and the others)\n\n{r['sy_md']}\n\n"
                   f"Correlation of predicted and actual state-year worsening rate over all 20 state-years (2006-2015): " + ", ".join(f"{LABEL[k]} {v:.2f}" for k, v in r["corr"].items()) + ".\n")
        d = r["dec"]
        out.append(f"### Calibration by decile of predicted risk ({LABEL[r['best']]}, pooled 2006-2015)\n\n| Decile | n | Mean predicted | Actual rate |\n|---|---|---|---|\n" +
                   "\n".join(f"| {int(x.decile)} | {int(x.n)} | {x.mean_pred:.2f} | {x.actual_rate:.2f} |" for x in d.itertuples()) + "\n")
        out.append(f"### Permutation importance ({LABEL[r['best']]}, trained 2000-2012, scored 2013-2015, validation AUC {r['base_auc']:.3f}; drop in AUC when the feature is shuffled)\n\n| Feature | AUC drop |\n|---|---|\n" +
                   "\n".join(f"| {x.feature} | {x.auc_drop_mean:.3f} |" for x in r["imp"].head(10).itertuples()) + "\n")
    dm = lambda task, v: diag[(diag.task == task) & (diag.variant == v)].iloc[0]
    out.append("## Note on M2 and the monotone constraints (diagnostic only, not used for selection)\n\n"
               f"M2 was run exactly as specified, including +1 monotone constraints on the start/level inputs. The data disagree with that sign: the standardised M1 coefficient of the start level is "
               f"{signs['A']:.2f} for Task A (`level_last_map`) and {signs['B']:.2f} for Task B (`level_apr1`), i.e. a county that is already at a high level is LESS likely to get worse "
               f"(ceiling and persistence), so forcing a positive effect hurts. AUC, walk-forward / 2013-2015 / pooled 2006-2015:\n\n"
               "| Task | M2 variant | WF AUC | Val AUC | Pooled AUC |\n|---|---|---|---|---|\n" +
               "\n".join(f"| {r.task} | {r.variant} | {r.wf_auc:.3f} | {r.val_auc:.3f} | {r.pooled_auc:.3f} |" for r in diag.itertuples()) +
               f"\n\nThis explains why M2 as specified does not reproduce the exploratory Task B AUC of about 0.87 (it gets {dm('B', 'M2 as specified (monotone constraints)').wf_auc:.2f} walk-forward and {dm('B', 'M2 as specified (monotone constraints)').val_auc:.2f} on 2013-2015); Task A reproduces "
               f"(about 0.6). The variants were NOT adopted and do not change the choice: M1 stays within {TIE_BAND} of (or ahead of) the best M2 variant in both tasks, so the pre-declared rule picks M1 either way. "
               "Changing the constraint is a modelling decision for the model builder, to be made before the final test.\n")
    out.append(f"## Simulation helper (Task B), example\n\n{sim_text.split(chr(10), 1)[1].strip()}\n")
    out.append("## Leakage and sanity checks (from the data build, `drought_severity_data/checks.md`)\n\n" + checks.split("\n", 2)[2] + "\n")
    out.append("- Model code: every imputer, scaler, base rate, county distribution and neighbour pool is fitted in `fit()` on the fold's training years only; normals and irrigation averages in the data use strictly earlier years; "
               "the loaders read only years <= 2015 and `final_test.py` is the only way to build 2016-2025 (and refuses without `--i-am-sure`).\n")
    ra, rb = A, B
    a_ok, b_ok = chosen["A"]["beats_climatology_auc"] and chosen["A"]["beats_persistence_exact_level_walk_forward"], chosen["B"]["beats_climatology_auc"]
    summary = [
        f"1. In-season (Task B), weather + soil with the April-1 drought level predict whether a county's drought gets worse by Aug 13 with AUC {rb['wf'][rb['best']]['auc']:.2f} (walk-forward) and {rb['val'][rb['best']]['auc']:.2f} (2013-2015), against {rb['wf']['Climatology']['auc']:.2f} for county climatology.",
        f"2. After Aug 13 (Task A), the best model reaches AUC {ra['wf'][ra['best']]['auc']:.2f} (walk-forward) and {ra['val'][ra['best']]['auc']:.2f} (2013-2015) for 'does it get worse', against {ra['wf']['Climatology']['auc']:.2f} for climatology; "
        + ("it beats persistence on exact level." if chosen["A"]["beats_persistence_exact_level_walk_forward"] else "it does NOT beat simply assuming no change on exact level, so the honest message is that the Aug-15 drought map is already the best forecast of the level."),
        f"3. The chosen models are {LABEL[ra['best']]} (A) and {LABEL[rb['best']]} (B), picked by a rule fixed before looking, with the simpler model winning ties.",
        f"4. The simulation helper turns Task B into a what-if tool: for Iowa 2012, scaling precipitation to 60% raises the mean chance of worsening from {sim_text.split('| 2012 weather as observed (precip x 1.0) | ')[1].split(' |')[0]} to {sim_text.split('| precip x 0.6, same temperatures | ')[1].split(' |')[0]} (flagging any input outside what the model has seen).",
        "5. All numbers use only years up to 2015 with maps limited to those released by Aug 15; the 2016-2025 test is untouched and runs only on request (`final_test.py --i-am-sure`).",
    ]
    out.insert(2, "## Summary for the pitch (5 lines)\n\n" + "\n".join(summary) + "\n")
    (RESULTS / "validation_report.md").write_text("\n".join(out))


if __name__ == "__main__":
    main()
