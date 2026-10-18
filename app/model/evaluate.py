"""Walk-forward + validation evaluation of baselines B0, B1 and strategies A, B, C, for both targets.

    python app/model/evaluate.py

Protocol (fixed before looking at any results):
  * Tuning (GBM: max_iter, max_depth; look-alikes: k, drought weight) uses ONLY walk-forward inside
    training (predict Y=2006..2012 from 2000..Y-1). Criterion: pooled county-year dollar WAPE of T1.
  * Walk-forward predictions + validation (train 2000-2012, predict 2013-2015) are pooled for model choice.
  * Choice rule: among A, B, C, a model is "near-best" if its top-20 budget capture is within 0.02 of the best
    and its dollar WAPE within 5% (relative) of the best; pick the simplest near-best one (A over C over B).
  * 80% ranges: A and B resample WHOLE past years' residuals (all counties of a year together; walk-forward
    years 2006-2012, own year left out); C uses its neighbours' spread. The method closest to 80% coverage on
    walk-forward + validation is recorded in results/range_method.json and used by budget.py, labelled "rough".
  * Calibration: every model x target gets k = sum(actual) / sum(predicted) fitted on its WALK-FORWARD predictions (2006-2012)
    only (results/calibration.csv) and its predictions are multiplied by k. Constant scaling, so capture and AUC cannot change.
    Walk-forward "after" numbers are therefore in-sample for k; validation is the honest check.
  * testing/ is never read here (data.load_split refuses it). Nothing is tuned for any particular year.
Outputs go to app/model/results/ (validation_report.md, validation_results.csv, ...).
"""
import itertools
import json
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from analog import Analog
from baselines import B0, B1
from budget import RANGE_LABEL, budget_components, residual_pool, total_range
from data import CARRY, KEY, REPO, RESULTS, T1, T2, add_year_class, load_usable
from gbm import GBM, GBMDollars
from hurdle import Hurdle

MODELS = ["B0", "B1", "A", "B", "C"]
LABEL = {"B0": "B0 average", "B1": "B1 drought-map rule", "A": "A hurdle", "B": "B boosting",
         "C": "C look-alikes", "Random": "Random counties", "Oracle": "Oracle (perfect ranking)",
         "BD": "B$ ($ target, uncalibrated)", "BDc": "B$ ($ target, calibrated)"}
SIMPLEST_FIRST = ["A", "C", "B"]
RANGED = ["A", "B", "C"]
WF_YEARS = list(range(2006, 2013))
TOP_N = 20
CAPTURE_NOISE, WAPE_NOISE = 0.02, 0.05
DEFAULT_PARAMS = {"B": {"max_iter": 200, "max_depth": 3}, "C": {"k": 25, "drought_weight": 2.0}}
TUNE_GRID = {"B": {"max_iter": [100, 200, 400], "max_depth": [3, 4]},
             "C": {"k": [10, 25, 50], "drought_weight": [1.0, 2.0, 3.0]}}
SPEC = {"t1": {"target": T1, "weight": "liability", "actual": "drought_indemnity", "unit": "$",
               "title": "T1 payout share (drought payout / insured $)"},
        "t2": {"target": T2, "weight": "insured_acres", "actual": "drought_loss_acres", "unit": "acres",
               "title": "T2 damaged-acre share (damaged acres / insured acres)"}}
GROUPS = ["all", "drought", "quiet"]


def make_model(name, params):
    return {"B0": B0, "B1": B1, "A": Hurdle,
            "B": lambda: GBM(**params.get("B", {})), "C": lambda: Analog(**params.get("C", {}))}[name]()


def fit_predict(train, test, params, names=MODELS):
    """Fit each model on train for both targets; return a frame of actuals + predictions for test."""
    out = test[KEY + CARRY].reset_index(drop=True).copy()
    out["t1_actual"], out["t2_actual"] = test[T1].to_numpy(), test[T2].to_numpy()
    for n in names:
        m1, m2 = make_model(n, params).fit(train, T1), make_model(n, params).fit(train, T2)
        out[f"t1_{n}"], out[f"t2_{n}"] = m1.predict(test), m2.predict(test)
        out[f"score_{n}"], out[f"score2_{n}"] = m1.score(test), m2.score(test)
        if n == "C":
            out["t1_C_lo"], out["t1_C_hi"] = m1.quantiles(test)
            out["t2_C_lo"], out["t2_C_hi"] = m2.quantiles(test)
    return out


# ------------------------------------------------------------------ metrics
def actual_amount(df, t):
    return df[SPEC[t]["actual"]].fillna(0)


def county_year(pred, col, t="t1"):
    d = pred.assign(_p=pred[col].to_numpy() * pred[SPEC[t]["weight"]].to_numpy(), _a=actual_amount(pred, t).to_numpy())
    return d.groupby(["state_alpha", "fips", "year"], as_index=False).agg(pred=("_p", "sum"), actual=("_a", "sum"))


def state_year_table(cy, n=TOP_N):
    rows = []
    for (s, y), g in cy.groupby(["state_alpha", "year"]):
        a = g.actual.sum()
        rows.append({"state": s, "year": y, "pred": g.pred.sum(), "actual": a,
                     "capture": g.nlargest(n, "pred").actual.sum() / a if a > 0 else np.nan,
                     "random": min(1.0, n / len(g)),
                     "oracle": g.nlargest(n, "actual").actual.sum() / a if a > 0 else np.nan})
    return pd.DataFrame(rows)


def metrics(pred, names=MODELS, t="t1"):
    """One row per model x group (all / drought / quiet state-years). Amounts in $ (T1) or acres (T2)."""
    pred = add_year_class(pred)
    rows = []
    for grp in GROUPS:
        sub = pred if grp == "all" else pred[pred.sy_class == grp]
        if sub.empty:
            continue
        for m in names:
            cy = county_year(sub, f"{t}_{m}", t)
            sy = state_year_table(cy)
            ok = sy.actual > 0
            pos = sub[f"{t}_actual"] > 0
            score = sub[f"score_{m}"] if t == "t1" else sub[f"score2_{m}"]
            row = {"target": t, "model": m, "group": grp, "state_years": len(sy),
                   "calibration": cy.pred.sum() / cy.actual.sum() if cy.actual.sum() > 0 else np.nan,
                   "state_total_abs_err": ((sy.pred - sy.actual).abs() / sy.actual)[ok].mean(),
                   "capture_top20": sy.capture.mean(),
                   "county_mae": (cy.pred - cy.actual).abs().mean(),
                   "wape": (cy.pred - cy.actual).abs().sum() / cy.actual.sum() if cy.actual.sum() > 0 else np.nan,
                   "auc_any_payout": roc_auc_score(pos, score) if pos.nunique() == 2 else np.nan}
            if t == "t1":
                comp = budget_components(sub, sub[f"t1_{m}"], sub[f"t2_{m}"])
                for key, c_pred, c_act in [("calib_damaged_acres", comp.damaged_acres, sub.drought_loss_acres),
                                           ("calib_out_of_pocket", comp.out_of_pocket, sub.out_of_pocket_drought_loss),
                                           ("calib_relief", comp.relief_need, sub.relief_gap_to_95pct)]:
                    act = c_act.fillna(0).sum()
                    row[key] = c_pred.sum() / act if act > 0 else np.nan
            rows.append(row)
        for ref in ["random", "oracle"]:
            rows.append({"target": t, "model": ref.capitalize(), "group": grp, "state_years": len(sy),
                         "capture_top20": sy[ref][sy.actual > 0].mean()})
    return pd.DataFrame(rows)


def state_year_points(pred, t="t1", names=MODELS):
    """Per state-year: actual statewide amount and each model's predicted amount."""
    rows = []
    for m in names:
        cy = county_year(pred, f"{t}_{m}", t).groupby(["state_alpha", "year"], as_index=False)[["pred", "actual"]].sum()
        cy.insert(0, "model", m)
        rows.append(cy)
    return pd.concat(rows, ignore_index=True)


def statewide_totals(pred, names=MODELS):
    """Per state-year: insurance pays (X), out-of-pocket (Y) and relief need (Z), predicted vs actual."""
    pred = add_year_class(pred)
    rows = []
    for m in names:
        comp = budget_components(pred, pred[f"t1_{m}"], pred[f"t2_{m}"])
        d = pd.concat([pred[["state_alpha", "year", "sy_class"]], comp], axis=1)
        d["X_actual"], d["Y_actual"], d["Z_actual"] = (pred.drought_indemnity, pred.out_of_pocket_drought_loss.fillna(0),
                                                       pred.relief_gap_to_95pct.fillna(0))
        g = d.groupby(["state_alpha", "year", "sy_class"], as_index=False).sum()
        g = g.rename(columns={"insurance_pays": "X_pred", "out_of_pocket": "Y_pred", "relief_need": "Z_pred"})
        g.insert(0, "model", m)
        rows.append(g[["model", "state_alpha", "year", "sy_class", "X_pred", "X_actual", "Y_pred", "Y_actual",
                       "Z_pred", "Z_actual"]])
    return pd.concat(rows, ignore_index=True)


# ------------------------------------------------------------------ 80% ranges
def range_rows(pred, pools, t="t1"):
    """One row per model (A, B, C) x state x year: low / point / high statewide amount and whether the actual falls inside.
    A, B: whole past years' residuals from `pools[model]` resampled together (own year left out).
    C: neighbours' spread, every county at the same quantile (counties assumed hit together)."""
    w = SPEC[t]["weight"]
    cls = add_year_class(pred).drop_duplicates(["state_alpha", "year"]).set_index(["state_alpha", "year"]).sy_class
    rows = []
    for y in sorted(pred.year.unique()):
        d = pred[pred.year == y]
        actual = actual_amount(d, t).groupby(d.state_alpha).sum()
        for m in ["A", "B"]:
            for s, (lo, hi) in total_range(d, d[f"{t}_{m}"], pools[m], weight=w, exclude_year=y).items():
                rows.append({"model": m, "state": s, "year": y, "low": lo, "high": hi, "actual": float(actual[s]),
                             "point": float((d[f"{t}_{m}"] * d[w])[d.state_alpha == s].sum())})
        for s, g in d.groupby("state_alpha"):
            rows.append({"model": "C", "state": s, "year": y, "low": float((g[f"{t}_C_lo"] * g[w]).sum()),
                         "high": float((g[f"{t}_C_hi"] * g[w]).sum()), "actual": float(actual[s]),
                         "point": float((g[f"{t}_C"] * g[w]).sum())})
    r = pd.DataFrame(rows)
    r["sy_class"] = [cls[(s, y)] for s, y in zip(r.state, r.year)]
    r["inside"] = (r.actual >= r.low) & (r.actual <= r.high)
    return r


def attach_coverage(m, cov):
    m = m.copy()
    m["range_k"], m["range_n"] = np.nan, np.nan
    for grp in m.group.unique():
        for mod in RANGED:
            c = cov[cov.model == mod]
            c = c if grp == "all" else c[c.sy_class == grp]
            idx = (m.model == mod) & (m.group == grp)
            m.loc[idx, "range_k"], m.loc[idx, "range_n"] = float(c.inside.sum()), float(len(c))
    m["range_cov"] = m.range_k / m.range_n.replace(0, np.nan)
    return m


# ------------------------------------------------------------------ walk-forward, tuning, choice
def walk_forward(train, params, years=WF_YEARS):
    out = []
    for y in years:
        p = fit_predict(train[train.year < y], train[train.year == y], params)
        p["split"] = "walk-forward"
        out.append(p)
    return pd.concat(out, ignore_index=True)


def tune(train):
    rows, best = [], dict(DEFAULT_PARAMS)
    for name, grid in TUNE_GRID.items():
        for vals in itertools.product(*grid.values()):
            combo = dict(zip(grid, vals))
            parts = []
            for y in WF_YEARS:
                te = train[train.year == y].reset_index(drop=True)
                te["t1_x"] = make_model(name, {name: combo}).fit(train[train.year < y], T1).predict(te)
                parts.append(te)
            cy = county_year(pd.concat(parts), "t1_x")
            rows.append({"model": name, **combo, "wape": (cy.pred - cy.actual).abs().sum() / cy.actual.sum()})
        t = pd.DataFrame([r for r in rows if r["model"] == name])
        best[name] = {k: (int(v) if k in ("max_iter", "max_depth", "k") else float(v))
                      for k, v in t.loc[t.wape.idxmin(), list(grid)].items()}
    return best, pd.DataFrame(rows)


def choose(pooled):
    """Apply the pre-declared choice rule to the pooled walk-forward + validation 'all' metrics (T1)."""
    m = pooled[pooled.group == "all"].set_index("model")
    cand = ["A", "B", "C"]
    cap_best, wape_best = m.loc[cand, "capture_top20"].max(), m.loc[cand, "wape"].min()
    near = [c for c in SIMPLEST_FIRST if m.loc[c, "capture_top20"] >= cap_best - CAPTURE_NOISE
            and m.loc[c, "wape"] <= wape_best * (1 + WAPE_NOISE)]
    if near:
        chosen, why = near[0], (f"near-best on both metrics (capture within {CAPTURE_NOISE}, WAPE within "
                                f"{WAPE_NOISE:.0%} of best); simplest of {near}")
    else:
        rank = m.loc[cand, "capture_top20"].rank(ascending=False) + m.loc[cand, "wape"].rank()
        chosen = min(cand, key=lambda c: (rank[c], SIMPLEST_FIRST.index(c)))
        why = "no model near-best on both metrics; lowest combined rank (capture rank + WAPE rank)"
    b1 = m.loc["B1"]
    beats = bool(m.loc[chosen, "capture_top20"] > b1.capture_top20 + CAPTURE_NOISE
                 and m.loc[chosen, "wape"] < b1.wape * (1 - WAPE_NOISE))
    return {"chosen": chosen, "reason": why, "beats_B1_outside_noise": beats}


# ------------------------------------------------------------------ formatting
def fmt(v):
    if isinstance(v, (bool, np.bool_)):
        return "yes" if v else "no"
    if isinstance(v, (float, np.floating)):
        return "–" if np.isnan(v) else (f"{v:,.0f}" if abs(v) >= 1e4 or (abs(v) >= 1 and v == round(v)) else f"{v:.3f}")
    return str(v)


def md(df):
    lines = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "|".join("---" for _ in df.columns) + "|"]
    lines += ["| " + " | ".join(fmt(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(lines)


def f_pct(v, d=0):
    return "–" if pd.isna(v) else f"{v * 100:,.{d}f}%"


def f_amt(v, unit):
    return "–" if pd.isna(v) else (f"${v:,.0f}" if unit == "$" else f"{v:,.0f}")


def f_cov(row):
    return "–" if pd.isna(row.range_cov) else f"{row.range_cov * 100:.0f}% ({int(row.range_k)}/{int(row.range_n)})"


def summary_md(m, unit="$"):
    """Summary table for one split x target x group. Bold = best in column (random/oracle rows excluded)."""
    r = m[m.model.isin(MODELS)].set_index("model")
    cols = [("state_total_abs_err", "Statewide total error (% off)", "min", lambda v, x: f_pct(v)),
            ("county_mae", f"Weighted MAE ({unit} per county-year)", "min", lambda v, x: f_amt(v, unit)),
            ("capture_top20", "Budget capture (top-20 counties)", "max", lambda v, x: f_pct(v, 1)),
            ("auc_any_payout", "Any-payout AUC" if unit == "$" else "Any-damage AUC", "max", lambda v, x: "–" if pd.isna(v) else f"{v:.3f}"),
            ("calibration", "Calibration (Σpred / Σactual)", "one", lambda v, x: "–" if pd.isna(v) else f"{v:.2f}"),
            ("range_cov", "80% range coverage", "eighty", lambda v, x: f_cov(x))]
    best = {}
    for key, _, rule, _f in cols:
        s = r[key].dropna()
        if key == "range_cov":
            s = s[s.index.isin(RANGED)]
        if len(s):
            best[key] = (s.idxmin() if rule == "min" else s.idxmax() if rule == "max"
                         else (s - (1 if rule == "one" else 0.8)).abs().idxmin())
    lines = ["| Model | " + " | ".join(c[1] for c in cols) + " |", "|---|" + "---|" * len(cols)]
    for name in MODELS:
        if name not in r.index:
            continue
        cells = []
        for key, _, _, f in cols:
            text = f(r.loc[name, key], r.loc[name])
            cells.append(f"**{text}**" if best.get(key) == name and text != "–" else text)
        lines.append(f"| {LABEL[name]} | " + " | ".join(cells) + " |")
    rnd = m[m.model == "Random"]
    if len(rnd):
        lines.append(f"| *Random counties (reference)* | – | – | *{f_pct(rnd.capture_top20.iloc[0], 1)}* | – | – | – |")
    return "\n".join(lines)


# metric_view / metric_tables / totals_wide: the wide T1 detail tables (appendix, and final_test.py)
def metric_view(m):
    m = m.copy()
    m["model"] = m.model.map(LABEL)
    m["county_mae"] = m.county_mae / 1e6
    return m.drop(columns=[c for c in ["target", "range_k", "range_n"] if c in m]).rename(columns={
        "county_mae": "county MAE $M", "state_years": "state-yrs", "calibration": "Σpred/Σactual",
        "state_total_abs_err": "state total err (x actual)", "capture_top20": "top-20 capture",
        "auc_any_payout": "AUC any payout", "calib_damaged_acres": "acres calib",
        "calib_out_of_pocket": "out-of-pocket calib", "calib_relief": "relief calib", "range_cov": "80% range cov"})


def metric_tables(m):
    out = []
    for grp, title in [("all", "All state-years"), ("drought", "Drought years (statewide payout >= 3% of insured $)"),
                       ("quiet", "Quiet years")]:
        t = m[m.group == grp].drop(columns="group")
        if len(t):
            out.append(f"**{title}**\n\n{md(metric_view(t))}\n")
    return "\n".join(out)


def totals_wide(tot, names, classes=("drought",)):
    t = tot[tot.sy_class.isin(classes)]
    w = t.pivot_table(index=["state_alpha", "year"], columns="model", values="X_pred").reindex(columns=names) / 1e6
    w.insert(0, "actual", t.drop_duplicates(["state_alpha", "year"]).set_index(["state_alpha", "year"]).X_actual / 1e6)
    w = w.reset_index()
    w.columns = ["state", "year", "actual $M"] + [LABEL[n] + " $M" for n in names]
    return w


# ------------------------------------------------------------------ report pieces
def drought_facts_ia2013():
    """Statewide mean D2+ share of Iowa county area on selected 2013 weekly maps (repo's processed Drought Monitor data)."""
    f = REPO / "data" / "processed" / "drought" / "drought_weekly.parquet"
    if not f.exists():
        return None
    d = pd.read_parquet(f)
    d["fips"] = d.fips.astype(str).str.zfill(5)
    x = d[d.fips.str.startswith("19") & (d.map_date.dt.year == 2013)].copy()
    x["d2p"] = x.D2 + x.D3 + x.D4
    s = x.groupby("map_date").d2p.mean()
    at = lambda day: float(s.loc[pd.Timestamp(f"2013-{day}")])
    last_pos = s[(s.index <= "2013-08-13") & (s > 0)].index.max()
    return {"apr2": at("04-02"), "first_zero": s[s.index > last_pos].index.min().strftime("%b %d"),
            "aug13": at("08-13"), "aug27": at("08-27"), "sep3": at("09-03"), "sep10": at("09-10")}


def known_misses(pts, liab):
    """State-years where all five models were off by more than 50% (T1 payout $), with a one-line likely reason."""
    w = pts.pivot_table(index=["state_alpha", "year"], columns="model", values="pred")[MODELS]
    act = pts.drop_duplicates(["state_alpha", "year"]).set_index(["state_alpha", "year"]).actual
    rel = w.sub(act, axis=0).div(act, axis=0)
    bad = rel[(rel.abs() > 0.5).all(axis=1)]
    facts = drought_facts_ia2013()
    rows = []
    for (s, y), r in bad.iterrows():
        share = act[(s, y)] / liab[(s, y)]
        direction = "over" if (r > 0).all() else "under" if (r < 0).all() else "mixed"
        if (s, y) == ("IA", 2013):
            reason = ("Drought began after the Aug 15 decision date, so no Aug-15 input could show it "
                      + (f"(Iowa mean D2+ area was 0% on every weekly map from {facts['first_zero']} through Aug 13, then "
                         f"{facts['aug27']:.0f}% on Aug 27, {facts['sep3']:.0f}% on Sep 3 and {facts['sep10']:.0f}% on Sep 10). "
                         if facts else ". ")
                      + "Known limitation: not tuned for.")
        elif direction == "over":
            reason = (f"Quiet year: actual payout only {share:.2%} of insured $ (${act[(s, y)] / 1e6:,.1f}M), so a small absolute "
                      "miss is a large % miss; models likely over-read mild drought signals.")
        elif direction == "under":
            reason = "Loss not visible in Aug-15 inputs (late-season drought or a loss coded to another cause)."
        else:
            reason = "Models disagree in sign; payout depends on local conditions the Aug-15 inputs only weakly capture."
        rows.append({"state": s, "year": y, "actual $M": act[(s, y)] / 1e6, "direction": direction,
                     **{LABEL[m] + " $M": w.loc[(s, y), m] / 1e6 for m in MODELS}, "likely reason": reason})
    return pd.DataFrame(rows), facts


def state_year_md(pts, cov, class_of, years, bud=None, budget_label="budget range"):
    """Section C table: actual, each model's prediction and (A, B, C) 80% range with ✓ inside / ✗ outside; optional budget range."""
    rows = []
    for (s, y), g in pts[pts.year.isin(years)].groupby(["state_alpha", "year"]):
        a = g.actual.iloc[0]
        row = {"state": s, "year": y, "class": class_of[(s, y)], "actual $M": f"{a / 1e6:,.1f}"}
        p = g.set_index("model").pred
        for m in MODELS:
            cell = f"{p[m] / 1e6:,.1f}"
            if m in RANGED:
                c = cov[(cov.model == m) & (cov.state == s) & (cov.year == y)].iloc[0]
                cell += f" [{c.low / 1e6:,.1f}–{c.high / 1e6:,.1f}] {'✓' if c.inside else '✗'}"
            row[LABEL[m] + (" (pred [80% range])" if m in RANGED else "")] = cell
        if bud is not None:
            b = bud.loc[(s, y)]
            row[budget_label] = f"[{b.budget_low / 1e6:,.1f}–{b.budget_high / 1e6:,.1f}] {'✓' if b.inside else '✗'}"
        rows.append(row)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ calibration
def fit_calibration(wf):
    """k = sum(actual) / sum(predicted) per model x target, from walk-forward predictions only (T2: damaged acres)."""
    rows = []
    for t, sp in SPEC.items():
        act = actual_amount(wf, t).sum()
        for m in MODELS:
            pred = (wf[f"{t}_{m}"] * wf[sp["weight"]]).sum()
            rows.append({"target": t, "model": m, "k": act / pred, "unit": sp["unit"], "walk_forward_actual": act,
                         "walk_forward_predicted": pred, "walk_forward_rows": len(wf), "fit_years": "2006-2012"})
    return pd.DataFrame(rows)


def apply_k(frame, cal):
    """Multiply every model's predictions (and C's neighbour quantiles) by its k. Ranking scores of B0/B1/B/C follow the
    rescaled predictions; A's score is its part-1 probability, which is not rescaled."""
    k = {(r.model, r.target): r.k for r in cal.itertuples()}
    out = frame.copy()
    for m in MODELS:
        for t in SPEC:
            out[f"{t}_{m}"] = frame[f"{t}_{m}"] * k[(m, t)]
        if m != "A":
            out[f"score_{m}"], out[f"score2_{m}"] = out[f"t1_{m}"], out[f"t2_{m}"]
    for t in SPEC:
        for q in ("lo", "hi"):
            out[f"{t}_C_{q}"] = frame[f"{t}_C_{q}"] * k[("C", t)]
    return out


def invariance(Mb, Ma):
    """Largest before/after difference in budget capture and AUC (should be ~0: constant scaling keeps rankings)."""
    keys = ["split", "target", "group", "model"]
    j = Mb.merge(Ma, on=keys, suffixes=("_b", "_a"))
    return {c: float(np.nanmax(np.abs(j[f"{c}_b"] - j[f"{c}_a"]))) for c in ["capture_top20", "auc_any_payout"]}


def budget_range_rows(cov, chosen, method):
    """The budget range: the best validated range method, widened where needed so the chosen model's calibrated point
    estimate lies inside it. cov = range_rows(...) for T1."""
    r = cov[cov.model == method].set_index(["state", "year"])
    out = r[["low", "high", "actual", "sy_class"]].copy()
    out["point"] = cov[cov.model == chosen].set_index(["state", "year"]).point
    out["point_inside"] = (out.point >= out.low) & (out.point <= out.high)
    out["budget_low"], out["budget_high"] = np.minimum(out.low, out.point), np.maximum(out.high, out.point)
    out["widened"] = ~out.point_inside
    out["inside"] = (out.actual >= out.budget_low) & (out.actual <= out.budget_high)
    return out


def validation_predictions(vp_raw, vp_cal, cal):
    """One row per county x crop x year x model: predicted vs actual share, dollars and damaged acres (calibrated)."""
    k = {(r.model, r.target): r.k for r in cal.itertuples()}
    base = ["fips", "county_name", "state_alpha", "crop", "year", "liability", "insured_acres"]
    rows = []
    for m in MODELS:
        d = vp_cal[base].copy()
        d.insert(5, "model", m)
        d["k_t1"], d["k_t2"] = k[(m, "t1")], k[(m, "t2")]
        d["pred_share_t1_uncalibrated"], d["pred_share_t1"] = vp_raw[f"t1_{m}"], vp_cal[f"t1_{m}"]
        d["actual_share_t1"] = vp_cal.t1_actual
        d["pred_usd"], d["actual_usd"] = vp_cal[f"t1_{m}"] * vp_cal.liability, vp_cal.drought_indemnity.fillna(0)
        d["pred_share_t2_uncalibrated"], d["pred_share_t2"] = vp_raw[f"t2_{m}"], vp_cal[f"t2_{m}"]
        d["actual_share_t2"] = vp_cal.t2_actual
        d["pred_damaged_acres"] = vp_cal[f"t2_{m}"] * vp_cal.insured_acres
        d["actual_damaged_acres"] = vp_cal.drought_loss_acres.fillna(0)
        rows.append(d)
    return pd.concat(rows, ignore_index=True)


def side_check(train, val, wfc, vpc, params):
    """Optional report-only check: boosting on drought payout in dollars with liability as a feature (GBMDollars), next to
    the calibrated share version of B. The dollar model gets its own k from walk-forward, like every other model."""
    usd = []
    for y in WF_YEARS:
        te = train[train.year == y]
        usd.append(GBMDollars(**params["B"]).fit(train[train.year < y]).predict_usd(te))
    wf_usd = np.concatenate(usd)
    vp_usd = GBMDollars(**params["B"]).fit(train).predict_usd(val)
    k = wfc.drought_indemnity.fillna(0).sum() / wf_usd.sum()
    out = {}
    for name, frame, u in [("walk-forward", wfc, wf_usd), ("validation", vpc, vp_usd)]:
        f = frame.copy()
        f["t1_BD"], f["t1_BDc"] = u / f.liability, k * u / f.liability
        f["t2_BD"] = f["t2_BDc"] = f["t2_B"]
        f["score_BD"], f["score_BDc"] = f.t1_BD, f.t1_BDc
        f["score2_BD"] = f["score2_BDc"] = f["score2_B"]
        out[name] = metrics(f, names=["B", "BD", "BDc"], t="t1")
        out[name].insert(0, "split", name)
    return pd.concat(out.values(), ignore_index=True), k


def pick(M, model, t="t1", split="validation", grp="all"):
    r = M[(M.target == t) & (M.split == split) & (M.group == grp) & (M.model == model)]
    return r.iloc[0]


def verdict_text(ctx):
    """3-5 sentences: did calibration help, does the chosen model win under the plan's rule, what looks off."""
    Ma, Mb, ch, vd = ctx["metrics"], ctx["metrics_before"], ctx["verdict"]["chosen"], ctx["verdict"]
    P = Ma[(Ma.target == "t1") & (Ma.split == "pooled") & (Ma.group == "all")].set_index("model")
    ba = {m: (pick(Mb, m), pick(Ma, m)) for m in MODELS}
    closer = [m for m in MODELS if abs(ba[m][1].calibration - 1) < abs(ba[m][0].calibration - 1)]
    cb, ca = ba[ch]
    helped = abs(ca.calibration - 1) < abs(cb.calibration - 1) and ca.wape < cb.wape
    worse = [LABEL[m] for m in MODELS if ba[m][1].wape > ba[m][0].wape * 1.05]
    b1 = P.loc["B1"]
    c = P.loc[ch]
    near = [m for m in SIMPLEST_FIRST if P.loc[m, "capture_top20"] >= P.loc[RANGED, "capture_top20"].max() - CAPTURE_NOISE
            and P.loc[m, "wape"] <= P.loc[RANGED, "wape"].min() * (1 + WAPE_NOISE)]
    inv = ctx["invariance"]
    bud = ctx["bud"]
    rc = ctx["rng_cov"]
    further = [m for m in MODELS if abs(ba[m][1].calibration - 1) > abs(ba[m][0].calibration - 1)]
    bb, bA = ba["B"]
    s = []
    s.append(f"**Calibration {'helped' if helped else 'did not clearly help'}**: on validation (out-of-sample for k) Σpred/Σactual moved closer to 1 for "
             f"{', '.join(LABEL[m] for m in closer) or 'no model'} and further from 1 for {', '.join(LABEL[m] for m in further) or 'no model'}; "
             f"for B boosting it went {bb.calibration:.2f} → {bA.calibration:.2f} with dollar error (WAPE) {bb.wape:.2f} → {bA.wape:.2f}"
             + (f", and for {LABEL[ch]} {cb.calibration:.2f} → {ca.calibration:.2f} with WAPE {cb.wape:.2f} → {ca.wape:.2f}" if ch != "B" else "")
             + f"; budget capture and AUC are unchanged (largest change {inv['capture_top20']:.1e} and {inv['auc_any_payout']:.1e}).")
    flipped = ch != ctx["verdict_before"]["chosen"]
    if len(near) == 1 and near[0] == ch:
        rule = (f"Under the plan's rule {LABEL[ch]} {'still ' if not flipped else ''}wins: no simpler model is within noise of it on both "
                f"capture ({CAPTURE_NOISE * 100:.0f} points) and WAPE ({WAPE_NOISE:.0%}) once all models are calibrated "
                f"({'; '.join(f'{m}: capture {P.loc[m, 'capture_top20']:.1%}, WAPE {P.loc[m, 'wape']:.2f}' for m in RANGED if m != ch)}).")
    else:
        rule = (f"Under the plan's rule the pick is {LABEL[ch]}: models {', '.join(near) if near else '(none)'} are within noise of the best on both "
                f"capture ({CAPTURE_NOISE * 100:.0f} points) and WAPE ({WAPE_NOISE:.0%}) once all models are calibrated, so the simplest of them wins"
                + (f"; before calibration it was {LABEL[ctx['verdict_before']['chosen']]}." if flipped else "."))
    s.append(rule)
    s.append(f"Against B1 (also calibrated) {LABEL[ch]} has pooled capture {c.capture_top20:.1%} vs {b1.capture_top20:.1%} and WAPE {c.wape:.2f} vs {b1.wape:.2f} "
             f"({1 - c.wape / b1.wape:.0%} lower).")
    flags = ["k is fitted on walk-forward predictions, so the pooled walk-forward 'after' figures are in-sample for k and only validation tests it"]
    if further:
        flags.append("k comes from a window dominated by the 2012 drought, so it over-corrects quiet years: "
                     + ", ".join(f"{LABEL[m]} Σpred/Σactual {ba[m][0].calibration:.2f} → {ba[m][1].calibration:.2f}" for m in further) + " on validation")
    if flipped:
        va_, vb_ = pick(Ma, ch), pick(Ma, ctx["verdict_before"]["chosen"])
        flags.append(f"the pick moved from {LABEL[ctx['verdict_before']['chosen']]} to {LABEL[ch]} mainly because k_{ch} rescales its 2012 over-prediction in-sample; "
                     f"on validation alone WAPE is {va_.wape:.2f} for {ch} vs {vb_.wape:.2f} for {ctx['verdict_before']['chosen']}")
    if abs(ca.calibration - 1) > 0.25:
        flags.append(f"{LABEL[ch]} still {'under' if ca.calibration < 1 else 'over'}-budgets on validation ({ca.calibration:.2f}), mostly Iowa 2013, which no Aug-15 input can show")
    flags.append(f"{int((~bud.point_inside).sum())} of {len(bud)} state-years needed the {ctx['best_range']} range widened to contain {ch}'s point estimate")
    s.append("What looks off: " + "; ".join(flags) + ".")
    s.append("Ranges stay rough: pooled 80%-range coverage after calibration is " + ", ".join(f"{m} {rc[m] * 100:.0f}%" for m in RANGED)
             + f" and {ctx['bud_cov_pooled'] * 100:.0f}% for the budget range ({ctx['best_range']}, widened around {ch}'s point).")
    return " ".join(s)


def before_after_md(Mb, Ma, t, unit):
    rows = []
    for m in MODELS:
        b, a = pick(Mb, m, t), pick(Ma, m, t)
        cov = "–" if m not in RANGED else f"{f_cov(b).split(' ')[0]} → {f_cov(a).split(' ')[0]}"
        rows.append({"Model": LABEL[m], "Calibration (Σpred/Σactual)": f"{b.calibration:.2f} → {a.calibration:.2f}",
                     "WAPE": f"{b.wape:.2f} → {a.wape:.2f}", "Budget capture": f"{f_pct(b.capture_top20, 1)} → {f_pct(a.capture_top20, 1)}",
                     "AUC": f"{b.auc_any_payout:.3f} → {a.auc_any_payout:.3f}", "80% range coverage": cov})
    return md(pd.DataFrame(rows))


def write_report(ctx):
    unit = "$"
    split_names = [("walk-forward", "Walk-forward (2006-2012)"), ("validation", "Validation (2013-2015)"),
                   ("pooled", "Pooled walk-forward + validation (basis for the verdict)")]
    M, Mb = ctx["metrics"], ctx["metrics_before"]
    sel = lambda t, split, grp: M[(M.target == t) & (M.split == split) & (M.group == grp)]
    cls = ctx["class_of"]
    ch, cal, bud = ctx["verdict"]["chosen"], ctx["cal"], ctx["bud"]
    drought_sy = {sp: sorted(f"{s} {y}" for (s, y), c in cls.items() if c == "drought" and y in ctx["years"][sp]) for sp in ctx["years"]}
    kt = cal.pivot(index="model", columns="target", values="k").reindex(MODELS)
    kt_tbl = pd.DataFrame({"Model": [LABEL[m] for m in MODELS], "k for T1 (payout $)": kt.t1.round(3).to_numpy(),
                           "k for T2 (damaged acres)": kt.t2.round(3).to_numpy()})
    inv = ctx["invariance"]
    pt_in = int(bud.point_inside.sum())
    out = [f"""# Validation report: walk-forward 2006-2012 and validation 2013-2015 (calibrated)

Models are fitted on training years only (2000-2012 for validation; each fold's earlier years for walk-forward). **`testing/` was not
read.** Every model's predictions are multiplied by its calibration factor k (see "Calibration"); all tables below use the calibrated
predictions unless marked "before". Amounts are predicted drought payout = predicted T1 x insured liability (dollars), summed over crops per
county-year; T2 amounts are predicted damaged acres = T2 x insured acres. Rows used: {ctx['n_train']} training and {ctx['n_val']} validation
(insured, liability > 0, RMA year available; zero payouts kept). Raw numbers: `validation_results.csv` (all metrics, before and after
calibration), `validation_state_years.csv` (per state-year), `validation_predictions.csv` (every county x crop x year x model).

How to read the tables. *Statewide total error* = mean over state-years of |predicted - actual| / actual for the statewide total.
*Weighted MAE* = mean absolute error per county-year in dollars (acres for T2); in absolute dollars, so big counties weigh more.
*Budget capture* = share of actual drought payouts landing in the 20 counties with the highest predicted payout, averaged over state-years
(random = what picking 20 counties by chance gives). *Any-payout AUC* = ranking of rows with any payout above rows with none.
*Calibration* = Σ predicted / Σ actual (<1 under-budgets). *80% range coverage* = share of state-years whose actual statewide total
falls inside the 10th-90th percentile range (target ~80%; k/n shown). **Bold = best in column** (calibration: closest to 1; coverage: closest to 80%).
A "drought year" is a state-year whose actual statewide drought payout is >= 3% of insured dollars; all others are "quiet".
Percent errors on statewide totals are huge in quiet years (a tiny actual total makes any miss a big percentage), so read them next to the dollar columns.

How the 80% ranges are built. A and B: whole past years' residuals (walk-forward 2006-2012, out-of-sample, of the CALIBRATED predictions) are
resampled one year at a time, the same year's residual applied to every county together (droughts hit counties together; never row by row), and the
10th-90th percentile of the resulting statewide totals is taken (own year left out). C: 10th-90th percentile of the liability-weighted shares of its
k nearest look-alikes (scaled by C's calibration factor), every county at the same quantile. B0 and B1 have no range. The budget range is the best
of these ({ctx['best_range']}), widened where needed so the chosen model's ({ch}) calibrated point estimate lies inside it.

Tuned on walk-forward only (criterion: pooled county-year dollar WAPE of T1, before calibration): `{json.dumps(ctx['params'])}`.

## Calibration

Each model and target gets one multiplier k = Σ actual / Σ predicted, computed from that model's **walk-forward predictions (2006-2012) only**
(T2: damaged acres instead of dollars), saved in `results/calibration.csv` and applied in evaluation and in `budget.py`. k > 1 means the model
under-budgeted over 2006-2012 (dominated by the 2012 drought).

{md(kt_tbl)}

Budget capture and AUC are unchanged by a constant multiplier. Confirmed: the largest before/after difference over every split, target, group and
model is {inv['capture_top20']:.2e} for capture and {inv['auc_any_payout']:.2e} for AUC.

**Validation (2013-2015), before → after calibration, T1 payout share** (k from walk-forward, so this is out-of-sample):

{before_after_md(Mb, M, 't1', '$')}

**Validation, before → after, T2 damaged-acre share:**

{before_after_md(Mb, M, 't2', 'acres')}

Walk-forward "after" figures in the tables below are in-sample for k (k was fitted on those very predictions), so only the validation columns test
the calibration. In the budget range, the chosen model's point estimate fell inside the {ctx['best_range']} range in {pt_in} of {len(bud)} state-years
and the range was widened in the other {len(bud) - pt_in}; coverage of the widened budget range: walk-forward {ctx['bud_cov']['walk-forward']},
validation {ctx['bud_cov']['validation']}.
"""]
    out.append("## A. Summary (T1 payout share, all state-years, calibrated)\n")
    for sp, title in split_names:
        out.append(f"**{title}**, {int(sel('t1', sp, 'all').state_years.iloc[0])} state-years\n\n{summary_md(sel('t1', sp, 'all'), unit)}\n")
    out.append("## B. Drought years vs quiet years (T1, calibrated)\n")
    for sp, title in split_names[:2]:
        for grp, gt in [("drought", "drought years"), ("quiet", "quiet years")]:
            t = sel("t1", sp, grp)
            if len(t):
                n = int(t.state_years.iloc[0])
                names = ", ".join(drought_sy[sp]) if grp == "drought" else "all other state-years"
                out.append(f"**{title}: {gt}** ({n} state-year{'s' if n != 1 else ''}: {names})\n\n{summary_md(t, unit)}\n")
    out.append("Where a group holds only one or two state-years (validation drought years), treat the figures as anecdotes: range coverage "
               "there is 0 or 1 out of 1.\n")
    out.append("## C. Statewide drought payout per state-year ($M): actual, each calibrated model's prediction, and the 80% range\n"
               "Cell = prediction [low–high of the 80% range] ✓ if the actual falls inside the range, ✗ if outside. Ranges for A, B, C use each model's own "
               f"method; the last column is the budget range ({ctx['best_range']} range widened to include {ch}'s point estimate). T1 payout in $M.\n")
    for sp, title in split_names[:2]:
        out.append(f"**{title}**\n\n{md(state_year_md(ctx['pts'], ctx['cov_t1'], cls, ctx['years'][sp], bud, 'Budget range'))}\n")
    out.append("## D. Both targets (calibrated)\n\nT1 (payout share) is table A. T2 (damaged-acre share) uses the same layout; amounts are acres. "
               "Out-of-pocket and relief calibration (which use T2) are in the appendix.\n")
    for sp, title in split_names:
        out.append(f"**T2 damaged-acre share: {title}**, all state-years\n\n{summary_md(sel('t2', sp, 'all'), 'acres')}\n")
    for sp, title in split_names[:2]:
        for grp, gt in [("drought", "drought years"), ("quiet", "quiet years")]:
            t = sel("t2", sp, grp)
            if len(t):
                out.append(f"**T2: {title}: {gt}**\n\n{summary_md(t, 'acres')}\n")
    out.append("## E. Known misses\n")
    mis = ctx["misses"]
    out.append("State-years where **every** calibrated model's statewide T1 total was off by more than 50% (walk-forward + validation):\n")
    out.append(md(mis) if len(mis) else "None.")
    out.append("""
- **Iowa 2013 is a known limitation, not tuned for.** The 2013 drought started after the Aug 15 decision date. Statewide D2+ area (weekly
  Drought Monitor in `data/processed/drought`) was 0% on every weekly map from late May through Aug 13, then rose to 21% on Aug 27 and 42%
  on Sep 10; the model inputs end Aug 14. Note that April 2013 maps still carried leftover 2012 drought ({a2:.0f}% mean D2+ area on Apr 2),
  which the Apr 1 - Aug 14 features include; it had cleared by late May. No feature, model or hyper-parameter was changed to catch 2013, and
  calibration (a constant per model) cannot fix it either.
- **Expected miss in the final test: Iowa 2020 (derecho).** The Aug 10, 2020 derecho caused wind losses that are mostly coded to a cause
  other than drought, so drought-payout models cannot predict them. Final-test results for 2020 Iowa should be read with that in mind.
""".format(a2=(ctx["facts"] or {}).get("apr2", float("nan"))))
    out.append("## F. Verdict\n\n" + ctx["verdict_text"] + "\n")
    sc = ctx["side"]
    side_rows = []
    for sp in ["walk-forward", "validation"]:
        for m in ["B", "BD", "BDc"]:
            r = sc[(sc.split == sp) & (sc.model == m) & (sc.group == "all")].iloc[0]
            side_rows.append({"split": sp, "model": {"B": "B boosting: share target, calibrated", "BD": LABEL["BD"], "BDc": LABEL["BDc"]}[m],
                              "WAPE": r.wape, "budget capture": r.capture_top20, "calibration": r.calibration, "AUC": r.auc_any_payout,
                              "county MAE $M": r.county_mae / 1e6})
    out.append(f"""## G. Side check (report only; no model switched): boosting on payout dollars with liability as a feature
Same hyper-parameters as B, trained on drought payout in dollars (Poisson loss, `liability` added as a feature) instead of share x liability. Its k from
walk-forward is {ctx['side_k']:.3f}. The share version of B is the calibrated one used everywhere else.

{md(pd.DataFrame(side_rows))}
""")
    out.append("## Appendix\n")
    out.append("### Full T1 metric detail, pooled walk-forward + validation, calibrated (includes out-of-pocket / relief calibration)\n\n"
               + metric_tables(M[(M.target == "t1") & (M.split == "pooled")].drop(columns="split")))
    out.append(f"### Strategy A coefficients (standardised features, largest first)\n`p_any_logit` = effect on the log-odds that drought "
               f"costs anything; `log_share_if_cost` = effect on log(payout share) when it does. Note `yield_prev5_mean_missing` and "
               f"`acres_planted_prev3_mean_missing` are only true for 2000-2002, so they can act as a weak year proxy in training.\n\n{md(ctx['coefs'])}\n")
    out.append(f"### Strategy B permutation importance on validation (drop in weighted R²)\n{md(ctx['imp'].head(10))}\n\n"
               "Partial dependence curves: `results/gbm_partial_dependence_validation.csv`.\n")
    out.append(f"### Strategy C look-alikes for the three largest validation payouts (calibrated)\n{md(ctx['ex'][['county_name', 'state_alpha', 'crop', 'year', 'actual_$M', 'pred_$M', 'why']])}\n")
    out.append(f"### Tuning grid (walk-forward WAPE before calibration, lower is better)\n{md(ctx['tune'].sort_values(['model', 'wape']))}\n")
    (RESULTS / "validation_report.md").write_text("\n".join(out))


def build_metrics(frames, oos_frame, years, pools):
    all_m, covs = [], {}
    for t in SPEC:
        cov = range_rows(oos_frame, pools[t], t)
        covs[t] = cov
        for name, frame in frames.items():
            m = attach_coverage(metrics(frame, t=t), cov[cov.year.isin(years[name])])
            m.insert(0, "split", name)
            all_m.append(m)
    return pd.concat(all_m, ignore_index=True), covs


def main():
    RESULTS.mkdir(exist_ok=True)
    train, val = load_usable("training"), load_usable("validation")
    print(f"usable rows: training {len(train)}, validation {len(val)}")

    params, tune_tbl = tune(train)
    tune_tbl.to_csv(RESULTS / "tuning.csv", index=False)
    json.dump(params, open(RESULTS / "params.json", "w"), indent=2)
    print("tuned params:", params)

    # raw predictions: walk-forward 2006-2012, and validation from models trained on all of 2000-2012
    wf = walk_forward(train, params)
    vp = fit_predict(train, val, params)
    vp["split"] = "validation"
    oos = pd.concat([wf, vp], ignore_index=True)
    years = {"walk-forward": set(wf.year.astype(int)), "validation": set(vp.year.astype(int)), "pooled": set(oos.year.astype(int))}

    # calibration: k from walk-forward predictions only, applied everywhere
    cal = fit_calibration(wf)
    cal.to_csv(RESULTS / "calibration.csv", index=False)
    wfc, vpc = apply_k(wf, cal), apply_k(vp, cal)
    oosc = pd.concat([wfc, vpc], ignore_index=True)
    print(cal.pivot(index="model", columns="target", values="k").reindex(MODELS).round(3))

    raw_frames = {"walk-forward": wf, "validation": vp, "pooled": oos}
    cal_frames = {"walk-forward": wfc, "validation": vpc, "pooled": oosc}
    pools_raw = {t: {m: residual_pool(wf, m, t) for m in ["A", "B"]} for t in SPEC}
    pools_cal = {t: {m: residual_pool(wfc, m, t) for m in ["A", "B"]} for t in SPEC}
    Mb, _ = build_metrics(raw_frames, oos, years, pools_raw)
    Ma, cov_cal = build_metrics(cal_frames, oosc, years, pools_cal)
    inv = invariance(Mb, Ma)
    print("calibration leaves capture / AUC unchanged; max diffs:", inv)
    pd.concat([Mb.assign(calibrated=False), Ma.assign(calibrated=True)]).to_csv(RESULTS / "validation_results.csv", index=False)

    pooled_t1 = Ma[(Ma.target == "t1") & (Ma.split == "pooled")]
    verdict = choose(pooled_t1)
    verdict_before = choose(Mb[(Mb.target == "t1") & (Mb.split == "pooled")])
    verdict.update(params=params, chosen_before_calibration=verdict_before["chosen"],
                   note="pre-declared rule applied to pooled calibrated metrics; walk-forward part is in-sample for k, see validation_report.md section F")
    json.dump(verdict, open(RESULTS / "chosen_model.json", "w"), indent=2)
    ch = verdict["chosen"]

    rng_pooled = pooled_t1[(pooled_t1.group == "all") & pooled_t1.model.isin(RANGED)][["model", "range_cov", "range_k", "range_n"]]
    best_range = rng_pooled.assign(gap=(rng_pooled.range_cov - 0.8).abs()).sort_values(["gap", "model"]).model.iloc[0]
    bud = budget_range_rows(cov_cal["t1"], ch, best_range)
    bud_cov = {sp: f"{int(bud[bud.index.get_level_values('year').isin(years[sp])].inside.sum())}/{int(bud.index.get_level_values('year').isin(years[sp]).sum())}"
               for sp in ["walk-forward", "validation"]}
    bud_cov_pooled = float(bud.inside.mean())
    json.dump({"method": best_range, "label": RANGE_LABEL, "pooled_coverage": {r.model: r.range_cov for r in rng_pooled.itertuples()},
               "target": 0.8, "chosen_point_inside_range": f"{int(bud.point_inside.sum())}/{len(bud)}",
               "budget_range_coverage_pooled": bud_cov_pooled,
               "note": "no method is tuned to hit 80%; the closest on calibrated walk-forward + validation is used, widened to include the "
                       "chosen model's point estimate, and labelled rough"},
              open(RESULTS / "range_method.json", "w"), indent=2)

    # saved predictions
    keep = (KEY + ["state_alpha", "split", "liability", "insured_acres", "t1_actual", "t2_actual"]
            + [f"t{i}_{m}" for i in (1, 2) for m in MODELS] + ["t1_C_lo", "t1_C_hi", "t2_C_lo", "t2_C_hi"])
    oosc[keep].to_csv(RESULTS / "oos_predictions.csv", index=False)       # calibrated; walk-forward + validation
    validation_predictions(vp, vpc, cal).to_csv(RESULTS / "validation_predictions.csv", index=False)
    pts_cal = {t: state_year_points(oosc, t) for t in SPEC}
    sy_rows = []
    for t in SPEC:
        p = pts_cal[t].rename(columns={"state_alpha": "state", "pred": "point"})
        c = cov_cal[t][["model", "state", "year", "low", "high", "inside"]]
        sy_rows.append(p.merge(c, on=["model", "state", "year"], how="left").assign(target=t, calibrated=True))
    b = bud.reset_index().rename(columns={"budget_low": "blow", "budget_high": "bhigh"})
    sy_rows.append(pd.DataFrame({"model": "Budget", "state": b.state, "year": b.year, "point": b.point, "actual": b.actual,
                                 "low": b.blow, "high": b.bhigh, "inside": b.inside, "target": "t1", "calibrated": True}))
    pd.concat(sy_rows).to_csv(RESULTS / "validation_state_years.csv", index=False)
    statewide_totals(oosc).to_csv(RESULTS / "validation_budget_totals.csv", index=False)

    # explanations (unchanged by calibration)
    a = Hurdle().fit(train, T1)
    coef = a.coefficients()
    coef.to_csv(RESULTS / "hurdle_coefficients.csv", index=False)
    coefs = coef.assign(_m=coef.fillna(0).drop(columns="feature").abs().max(axis=1)).sort_values("_m", ascending=False).drop(columns="_m").head(12)
    g = GBM(**params["B"]).fit(train, T1)
    imp = g.importance(val, T1)
    imp.to_csv(RESULTS / "gbm_permutation_importance_validation.csv", index=False)
    g.partial_dependence(val, ["d2_weeks_50pct", "d3_weeks_50pct", "d2_max_pct", "dsci_mean", "heat35_days",
                               "precip_ratio_vs_normal"]).to_csv(RESULTS / "gbm_partial_dependence_validation.csv", index=False)
    c = Analog(**params["C"]).fit(train, T1)
    ex = val.nlargest(3, "drought_indemnity").reset_index(drop=True)
    ex["why"] = c.explain(ex)
    ex["pred_$M"] = c.predict(ex) * float(cal[(cal.model == "C") & (cal.target == "t1")].k.iloc[0]) * ex.liability / 1e6
    ex["actual_$M"] = ex.drought_indemnity / 1e6

    side, side_k = side_check(train, val, wfc, vpc, params)
    side.to_csv(RESULTS / "side_check_dollar_target.csv", index=False)

    class_of = add_year_class(oosc).drop_duplicates(["state_alpha", "year"]).set_index(["state_alpha", "year"]).sy_class.to_dict()
    liab = oosc.groupby(["state_alpha", "year"]).liability.sum()
    misses, facts = known_misses(pts_cal["t1"], liab)
    ctx = dict(metrics=Ma, metrics_before=Mb, params=params, n_train=len(train), n_val=len(val), class_of=class_of, years=years,
               pts=pts_cal["t1"], cov_t1=cov_cal["t1"], misses=misses, facts=facts, coefs=coefs, imp=imp, ex=ex, tune=tune_tbl,
               verdict=verdict, verdict_before=verdict_before, cal=cal, invariance=inv, bud=bud, bud_cov=bud_cov,
               bud_cov_pooled=bud_cov_pooled, best_range=best_range, side=side, side_k=side_k,
               rng_cov=rng_pooled.set_index("model").range_cov)
    ctx["verdict_text"] = verdict_text(ctx)
    write_report(ctx)
    print(json.dumps({k: verdict[k] for k in ("chosen", "chosen_before_calibration", "reason")}, indent=2))
    print("range method:", best_range, "| point inside range:", f"{int(bud.point_inside.sum())}/{len(bud)}")
    print("report ->", RESULTS / "validation_report.md")


if __name__ == "__main__":
    sys.exit(main())
