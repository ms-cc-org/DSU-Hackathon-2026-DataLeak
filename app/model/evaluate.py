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
from gbm import GBM
from hurdle import Hurdle

MODELS = ["B0", "B1", "A", "B", "C"]
LABEL = {"B0": "B0 average", "B1": "B1 drought-map rule", "A": "A hurdle", "B": "B boosting",
         "C": "C look-alikes", "Random": "Random counties", "Oracle": "Oracle (perfect ranking)"}
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


def state_year_md(pts, cov, class_of, years):
    """Section C table: actual, each model's prediction and (A, B, C) 80% range with ✓ inside / ✗ outside."""
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
        rows.append(row)
    return pd.DataFrame(rows)


def verdict_text(pooled, m_val, verdict, rng_pooled, best_range):
    P, V = pooled[pooled.group == "all"].set_index("model"), m_val[m_val.group == "all"].set_index("model")
    ch = verdict["chosen"]
    c, b1 = P.loc[ch], P.loc["B1"]
    d_cap, wape_red = c.capture_top20 - b1.capture_top20, 1 - c.wape / b1.wape
    if d_cap > CAPTURE_NOISE and wape_red > WAPE_NOISE:
        kind = "a clear win"
    elif d_cap < -CAPTURE_NOISE and wape_red < -WAPE_NOISE:
        kind = "a loss"
    elif abs(d_cap) <= CAPTURE_NOISE and abs(wape_red) <= WAPE_NOISE:
        kind = "a tie"
    else:
        kind = "mixed (better on one measure, within noise or worse on the other)"
    near = [m for m in SIMPLEST_FIRST if P.loc[m, "capture_top20"] >= P.loc[RANGED, "capture_top20"].max() - CAPTURE_NOISE
            and P.loc[m, "wape"] <= P.loc[RANGED, "wape"].min() * (1 + WAPE_NOISE)]
    others = [m for m in RANGED if m != ch]
    cv = rng_pooled.set_index("model").range_cov
    D = pooled[pooled.group == "drought"].set_index("model")
    if len(near) == 1:
        rule = (f"Applying the plan's rule (take the simpler model when two are within noise): no simpler model is within noise of {ch} on both "
                f"measures ({'; '.join(f'{m}: capture {P.loc[m, 'capture_top20']:.1%}, WAPE {P.loc[m, 'wape']:.2f}' for m in others)}), so {ch} is chosen.")
    elif near:
        rule = (f"Applying the plan's rule, {', '.join(near)} are within noise of the best on both measures, so the simplest of them, {ch}, is chosen.")
    else:
        rule = "No model is near-best on both measures, so the lowest combined rank is chosen."
    s = [f"**{LABEL[ch]} wins.** Over the 20 pooled out-of-sample state-years (walk-forward 2006-2012 + validation 2013-2015) it puts "
         f"{c.capture_top20:.1%} of actual drought payouts in its top-20 counties (B1: {b1.capture_top20:.1%}, random: "
         f"{P.loc['Random', 'capture_top20']:.1%}) and its county-level dollar error (WAPE) is {c.wape:.2f} versus {b1.wape:.2f} for B1, "
         f"{wape_red:.0%} lower.",
         f"Against B1 (the drought-map rule) this is **{kind}**: capture is {d_cap * 100:+.1f} points and dollar error {wape_red:.0%} lower, "
         f"judged against noise bands of {CAPTURE_NOISE * 100:.0f} capture points and {WAPE_NOISE:.0%} of WAPE.",
         rule,
         f"Caveats: only {int(D.loc[ch, 'state_years'])} of the 20 state-years are drought years (Iowa and Nebraska 2012, Iowa 2013), where "
         f"{LABEL[ch]} under-budgets (Σpred/Σactual {D.loc[ch, 'calibration']:.2f}), and on validation alone (2013-2015) it has capture "
         f"{V.loc[ch, 'capture_top20']:.1%} vs {V.loc['B1', 'capture_top20']:.1%} for B1 and WAPE {V.loc[ch, 'wape']:.2f} vs {V.loc['B1', 'wape']:.2f}, "
         "with its one drought state-year (Iowa 2013) beginning after Aug 15 and invisible to every model.",
         "Budget ranges are rough: pooled 80%-range coverage is " + ", ".join(f"{m} {cv[m] * 100:.0f}%" for m in RANGED)
         + f" (target ~80%), so {best_range} is used in budget.py and labelled rough."]
    return " ".join(s)


def write_report(ctx):
    L, unit = LABEL, "$"
    split_names = [("walk-forward", "Walk-forward (2006-2012)"), ("validation", "Validation (2013-2015)"),
                   ("pooled", "Pooled walk-forward + validation (basis for the verdict)")]
    M = ctx["metrics"]
    sel = lambda t, split, grp: M[(M.target == t) & (M.split == split) & (M.group == grp)]
    cls = ctx["class_of"]
    drought_sy = {sp: sorted(f"{s} {y}" for (s, y), c in cls.items() if c == "drought" and y in ctx["years"][sp]) for sp in ctx["years"]}
    out = [f"""# Validation report: walk-forward 2006-2012 and validation 2013-2015

Models are fitted on training years only (2000-2012 for validation; each fold's earlier years for walk-forward). **`testing/` was not
read.** Amounts are predicted drought payout = predicted T1 x insured liability (dollars), summed over crops per county-year; T2 amounts
are predicted damaged acres = T2 x insured acres. Rows used: {ctx['n_train']} training and {ctx['n_val']} validation (insured, liability > 0,
RMA year available; zero payouts kept). Raw numbers: `validation_results.csv` (all metrics) and `validation_state_years.csv` (per state-year).

How to read the tables. *Statewide total error* = mean over state-years of |predicted - actual| / actual for the statewide total.
*Weighted MAE* = mean absolute error per county-year in dollars (acres for T2); in absolute dollars, so big counties weigh more.
*Budget capture* = share of actual drought payouts landing in the 20 counties with the highest predicted payout, averaged over state-years
(random = what picking 20 counties by chance gives). *Any-payout AUC* = ranking of rows with any payout above rows with none.
*Calibration* = Σ predicted / Σ actual (<1 under-budgets). *80% range coverage* = share of state-years whose actual statewide total
falls inside the 10th-90th percentile range (target ~80%; k/n shown). **Bold = best in column** (calibration: closest to 1; coverage: closest to 80%).
A "drought year" is a state-year whose actual statewide drought payout is >= 3% of insured dollars; all others are "quiet".
Percent errors on statewide totals are huge in quiet years (a tiny actual total makes any miss a big percentage), so read them next to the dollar columns.

How the 80% ranges are built. A and B: whole past years' residuals (walk-forward 2006-2012, out-of-sample) are resampled one year at a
time, the same year's residual applied to every county together (droughts hit counties together; never row by row), and the 10th-90th
percentile of the resulting statewide totals is taken (own year left out). C: 10th-90th percentile of the liability-weighted shares of its
k nearest look-alikes, every county at the same quantile. B0 and B1 have no range.

Tuned on walk-forward only (criterion: pooled county-year dollar WAPE of T1): `{json.dumps(ctx['params'])}`.
"""]
    out.append("## A. Summary (T1 payout share, all state-years)\n")
    for sp, title in split_names:
        out.append(f"**{title}**, {int(sel('t1', sp, 'all').state_years.iloc[0])} state-years\n\n{summary_md(sel('t1', sp, 'all'), unit)}\n")
    out.append("## B. Drought years vs quiet years (T1)\n")
    for sp, title in split_names[:2]:
        for grp, gt in [("drought", "drought years"), ("quiet", "quiet years")]:
            t = sel("t1", sp, grp)
            if len(t):
                names = ", ".join(drought_sy[sp]) if grp == "drought" else "all other state-years"
                out.append(f"**{title}: {gt}** ({int(t.state_years.iloc[0])} state-year{"s" if int(t.state_years.iloc[0]) != 1 else ""}: {names})\n\n{summary_md(t, unit)}\n")
    out.append("Where a group holds only one or two state-years (validation drought years), treat the figures as anecdotes: range coverage "
               "there is 0 or 1 out of 1.\n")
    out.append("## C. Statewide drought payout per state-year ($M): actual, each model's prediction, and the 80% range\n"
               "Cell = prediction [low–high of the 80% range] ✓ if the actual falls inside the range, ✗ if outside. "
               "Ranges for A, B, C only. T1 payout in $M.\n")
    for sp, title in split_names[:2]:
        out.append(f"**{title}**\n\n{md(state_year_md(ctx['pts'], ctx['cov_t1'], cls, ctx['years'][sp]))}\n")
    out.append("## D. Both targets\n\nT1 (payout share) is table A. T2 (damaged-acre share) uses the same layout; amounts are acres. "
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
    out.append("State-years where **every** model's statewide T1 total was off by more than 50% (walk-forward + validation):\n")
    out.append(md(mis) if len(mis) else "None.")
    out.append("""
- **Iowa 2013 is a known limitation, not tuned for.** The 2013 drought started after the Aug 15 decision date. Statewide D2+ area (weekly
  Drought Monitor in `data/processed/drought`) was 0% on every weekly map from late May through Aug 13, then rose to 21% on Aug 27 and 42%
  on Sep 10; the model inputs end Aug 14. Note that April 2013 maps still carried leftover 2012 drought ({a2:.0f}% mean D2+ area on Apr 2),
  which the Apr 1 - Aug 14 features include; it had cleared by late May. No feature, model or hyper-parameter was changed to catch 2013.
- **Expected miss in the final test: Iowa 2020 (derecho).** The Aug 10, 2020 derecho caused wind losses that are mostly coded to a cause
  other than drought, so drought-payout models cannot predict them. Final-test results for 2020 Iowa should be read with that in mind.
""".format(a2=(ctx["facts"] or {}).get("apr2", float("nan"))))
    out.append("## F. Verdict\n\n" + ctx["verdict_text"] + "\n")
    out.append("## Appendix\n")
    out.append("### Full T1 metric detail, pooled walk-forward + validation (includes out-of-pocket / relief calibration)\n\n"
               + metric_tables(M[(M.target == "t1") & (M.split == "pooled")].drop(columns="split")))
    out.append(f"### Strategy A coefficients (standardised features, largest first)\n`p_any_logit` = effect on the log-odds that drought "
               f"costs anything; `log_share_if_cost` = effect on log(payout share) when it does. Note `yield_prev5_mean_missing` and "
               f"`acres_planted_prev3_mean_missing` are only true for 2000-2002, so they can act as a weak year proxy in training.\n\n{md(ctx['coefs'])}\n")
    out.append(f"### Strategy B permutation importance on validation (drop in weighted R²)\n{md(ctx['imp'].head(10))}\n\n"
               "Partial dependence curves: `results/gbm_partial_dependence_validation.csv`.\n")
    out.append(f"### Strategy C look-alikes for the three largest validation payouts\n{md(ctx['ex'][['county_name', 'state_alpha', 'crop', 'year', 'actual_$M', 'pred_$M', 'why']])}\n")
    out.append(f"### Tuning grid (walk-forward WAPE, lower is better)\n{md(ctx['tune'].sort_values(['model', 'wape']))}\n")
    (RESULTS / "validation_report.md").write_text("\n".join(out))


def main():
    RESULTS.mkdir(exist_ok=True)
    train, val = load_usable("training"), load_usable("validation")
    print(f"usable rows: training {len(train)}, validation {len(val)}")

    params, tune_tbl = tune(train)
    tune_tbl.to_csv(RESULTS / "tuning.csv", index=False)
    json.dump(params, open(RESULTS / "params.json", "w"), indent=2)
    print("tuned params:", params)

    wf = walk_forward(train, params)
    vp = fit_predict(train, val, params)
    vp["split"] = "validation"
    oos = pd.concat([wf, vp], ignore_index=True)
    frames = {"walk-forward": wf, "validation": vp, "pooled": oos}
    years = {k: set(int(y) for y in f.year.unique()) for k, f in frames.items()}

    pools = {t: {m: residual_pool(wf, m, t) for m in ["A", "B"]} for t in SPEC}
    all_metrics, cov_all = [], {}
    for t in SPEC:
        cov = range_rows(oos, pools[t], t)
        cov_all[t] = cov
        for name, frame in frames.items():
            m = attach_coverage(metrics(frame, t=t), cov[cov.year.isin(years[name])])
            m.insert(0, "split", name)
            all_metrics.append(m)
    M = pd.concat(all_metrics, ignore_index=True)
    M.to_csv(RESULTS / "validation_results.csv", index=False)

    pts = {t: state_year_points(oos, t) for t in SPEC}
    sy_rows = []
    for t in SPEC:
        p = pts[t].rename(columns={"state_alpha": "state", "pred": "point"})
        c = cov_all[t][["model", "state", "year", "low", "high", "inside"]]
        sy_rows.append(p.merge(c, on=["model", "state", "year"], how="left").assign(target=t))
    pd.concat(sy_rows).to_csv(RESULTS / "validation_state_years.csv", index=False)
    statewide_totals(oos).to_csv(RESULTS / "validation_budget_totals.csv", index=False)

    keep = (KEY + ["state_alpha", "split", "liability", "insured_acres", "t1_actual", "t2_actual"]
            + [f"t{i}_{m}" for i in (1, 2) for m in MODELS] + ["t1_C_lo", "t1_C_hi", "t2_C_lo", "t2_C_hi"])
    oos[keep].to_csv(RESULTS / "oos_predictions.csv", index=False)

    pooled_t1 = M[(M.target == "t1") & (M.split == "pooled")]
    verdict = choose(pooled_t1)
    verdict["params"] = params
    json.dump(verdict, open(RESULTS / "chosen_model.json", "w"), indent=2)

    rng_pooled = pooled_t1[(pooled_t1.group == "all") & pooled_t1.model.isin(RANGED)][["model", "range_cov", "range_k", "range_n"]]
    best_range = (rng_pooled.assign(gap=(rng_pooled.range_cov - 0.8).abs()).sort_values(["gap", "model"]).model.iloc[0])
    json.dump({"method": best_range, "label": RANGE_LABEL, "pooled_coverage": {r.model: r.range_cov for r in rng_pooled.itertuples()},
               "target": 0.8, "note": "no method is tuned to hit 80%; the closest on walk-forward + validation is used and labelled rough"},
              open(RESULTS / "range_method.json", "w"), indent=2)

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
    ex["pred_$M"] = c.predict(ex) * ex.liability / 1e6
    ex["actual_$M"] = ex.drought_indemnity / 1e6

    classed = add_year_class(oos)
    class_of = classed.drop_duplicates(["state_alpha", "year"]).set_index(["state_alpha", "year"]).sy_class.to_dict()
    liab = oos.groupby(["state_alpha", "year"]).liability.sum()
    misses, facts = known_misses(pts["t1"], liab)
    vt = verdict_text(pooled_t1, M[(M.target == "t1") & (M.split == "validation")], verdict, rng_pooled, best_range)
    write_report(dict(metrics=M, params=params, n_train=len(train), n_val=len(val), class_of=class_of, years=years,
                      pts=pts["t1"], cov_t1=cov_all["t1"], misses=misses, facts=facts, verdict_text=vt, coefs=coefs,
                      imp=imp, ex=ex, tune=tune_tbl))
    print(json.dumps(verdict, indent=2))
    print("range method:", best_range)
    print("report ->", RESULTS / "validation_report.md")


if __name__ == "__main__":
    sys.exit(main())
