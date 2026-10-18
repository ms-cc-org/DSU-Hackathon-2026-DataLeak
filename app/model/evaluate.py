"""Walk-forward + validation evaluation of baselines (Z0, B1, B2a, B2b, B3, B4) and strategies A, B, C, D.   python app/model/evaluate.py

Protocol (fixed in DECISIONS.md, Entries 3-4, before this version was run):
  * Out-of-sample years 2006-2015: walk-forward 2006-2012 (fit on years < Y) and validation 2013-2015 (fit on 2000-2012). Hyper-parameters are tuned on walk-forward only.
  * Every preprocessing object is fitted inside fit() on the fold's training rows; rain normals / irrigation averages are built from strictly earlier years by organize_usda_data.py.
  * Calibration is NESTED: the multiplier k for year Y = sum(actual)/sum(predicted) over earlier out-of-sample years only (k = 1 for 2006). A model-target keeps calibration only if
    nested calibration lowers its statewide absolute $ error over 2006-2015.
  * "Historical scenario range" (A, B, D: whole earlier years' residuals, years < Y, at least 3; C: neighbour spread), 10th-90th percentile.
  * Selection rule: among A, B, C, D the lowest statewide absolute $ error on drought state-years, provided top-20 capture beats B3 and B4; ties within 5% go to the simpler model (D < A < C < B).
  * testing/ is never read (data.load_split refuses it).
"""
import itertools
import json
import subprocess
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from analog import Analog
from baselines import B1, B2a, B2b, B3, B4, Z0
from budget import budget_components, residual_pool, total_range
from data import CARRY, FEATURES_OLD, KEY, REPO, RESULTS, T1, T2, add_year_class, load_usable
from gbm import GBM
from hurdle import Hurdle
from tweedie import Tweedie

BASELINES = ["Z0", "B1", "B2a", "B2b", "B3", "B4"]
CANDIDATES = ["A", "B", "C", "D"]
MODELS = BASELINES + CANDIDATES
LABEL = {"Z0": "Z0 predict zero", "B1": "B1 drought-bin average", "B2a": "B2a USDA binary trigger", "B2b": "B2b tiered LFP-style trigger",
         "B3": "B3 liability only", "B4": "B4 liability x D2+ last map", "A": "A hurdle", "B": "B boosting", "C": "C look-alikes",
         "D": "D Tweedie GLM", "Random": "Random counties", "Oracle": "Best possible"}
SIMPLEST_FIRST = ["D", "A", "C", "B"]
RESAMPLED = ["A", "B", "D"]
RANGED = CANDIDATES
WF_YEARS = list(range(2006, 2013))
TOP_N, TIE_BAND, MIN_POOL_YEARS, SIG_SHARE = 20, 0.05, 3, 0.02
DEFAULT_PARAMS = {"B": {"max_iter": 200, "max_depth": 3}, "C": {"k": 25, "drought_weight": 2.0}, "D": {"alpha": 0.1}}
TUNE_GRID = {"B": {"max_iter": [100, 200, 400], "max_depth": [3, 4]},
             "C": {"k": [10, 25, 50], "drought_weight": [1.0, 2.0, 3.0]},
             "D": {"alpha": [0.01, 0.1, 1.0]}}
SPEC = {"t1": {"weight": "liability", "actual": "drought_indemnity", "unit": "$", "name": "T1 payout share (X, estimated insurance payouts)"},
        "t2": {"weight": "insured_acres", "actual": "drought_loss_acres", "unit": "acres", "name": "T2 damaged-acre share"},
        "z": {"weight": "_one", "actual": "relief_gap_to_95pct", "unit": "$", "name": "Z illustrative relief allocation (95% coverage assumption)"}}
GROUPS = ["all", "drought", "quiet"]


def make_model(name, params):
    factories = {"Z0": Z0, "B1": B1, "B2a": B2a, "B2b": B2b, "B3": B3, "B4": B4, "A": Hurdle,
                 "B": lambda: GBM(**params.get("B", {})), "C": lambda: Analog(**params.get("C", {})), "D": lambda: Tweedie(**params.get("D", {}))}
    return factories[name]()


def names_in(frame):
    return [m for m in MODELS if f"t1_{m}" in frame]


def fit_predict(train, test, params, names=MODELS):
    """Fit each model on train for both targets; frame of actuals + raw (uncalibrated) predictions for test."""
    out = test[KEY + CARRY].reset_index(drop=True).copy()
    out["t1_actual"], out["t2_actual"], out["_one"] = test[T1].to_numpy(), test[T2].to_numpy(), 1.0
    for n in names:
        m1, m2 = make_model(n, params).fit(train, T1), make_model(n, params).fit(train, T2)
        out[f"t1_{n}"], out[f"t2_{n}"] = m1.predict(test), m2.predict(test)
        if n == "C":
            out["t1_C_lo"], out["t1_C_hi"] = m1.quantiles(test)
            out["t2_C_lo"], out["t2_C_hi"] = m2.quantiles(test)
    return out


def walk_forward(train, params, names=MODELS, years=WF_YEARS):
    return pd.concat([fit_predict(train[train.year < y], train[train.year == y], params, names) for y in years], ignore_index=True)


# ------------------------------------------------------------------ metrics
def actual_amount(df, t):
    return df[SPEC[t]["actual"]].fillna(0)


def county_year(df, col, t="t1"):
    d = df.assign(_p=df[col].to_numpy() * df[SPEC[t]["weight"]].to_numpy(), _a=actual_amount(df, t).to_numpy())
    return d.groupby(["state_alpha", "fips", "year"], as_index=False).agg(pred=("_p", "sum"), actual=("_a", "sum"))


def _top(g, col, n=TOP_N):
    """Top-n counties by `col`, ties broken by county FIPS ascending (never by actual values for predictions)."""
    return g.sort_values([col, "fips"], ascending=[False, True]).head(n)


def sy_table(cy):
    rows = []
    for (s, y), g in cy.groupby(["state_alpha", "year"]):
        a = g.actual.sum()
        rows.append({"state": s, "year": y, "pred": g.pred.sum(), "actual": a,
                     "capture": _top(g, "pred").actual.sum() / a if a > 0 else np.nan,
                     "best": _top(g, "actual").actual.sum() / a if a > 0 else np.nan,
                     "random": min(1.0, TOP_N / len(g))})
    return pd.DataFrame(rows)


def metrics(frame, names, t="t1"):
    """One row per model x group (all / drought / quiet state-years). Money in $ (T1, Z) or acres (T2)."""
    frame = add_year_class(frame)
    rows = []
    for grp in GROUPS:
        sub = frame if grp == "all" else frame[frame.sy_class == grp]
        if sub.empty:
            continue
        pos = actual_amount(sub, t) > 0
        for m in names:
            cy = county_year(sub, f"{t}_{m}", t)
            sy = sy_table(cy)
            short = (sy.actual - sy.pred).clip(lower=0)
            rows.append({"target": t, "model": m, "group": grp, "state_years": len(sy),
                         "stat_abs_err": (sy.pred - sy.actual).abs().mean(), "under_budget_total": short.sum(), "worst_shortfall": short.max(),
                         "county_wape": (cy.pred - cy.actual).abs().sum() / cy.actual.sum() if cy.actual.sum() > 0 else np.nan,
                         "capture_top20": sy.capture.mean(), "best_capture": sy.best.mean(),
                         "calibration": cy.pred.sum() / cy.actual.sum() if cy.actual.sum() > 0 else np.nan,
                         "auc": roc_auc_score(pos, sub[f"{t}_{m}"]) if pos.nunique() == 2 else np.nan})
        rows.append({"target": t, "model": "Random", "group": grp, "state_years": len(sy), "capture_top20": sy.random[sy.actual > 0].mean()})
    return pd.DataFrame(rows)


def stat_err(frame, t, m, factor=None):
    """Mean over state-years of |sum predicted - sum actual| (optionally with a per-row calibration factor)."""
    f = 1.0 if factor is None else factor
    d = pd.DataFrame({"s": frame.state_alpha.to_numpy(), "y": frame.year.to_numpy(), "p": (frame[f"{t}_{m}"] * frame[SPEC[t]["weight"]] * f).to_numpy(),
                      "a": actual_amount(frame, t).to_numpy()}).groupby(["s", "y"]).sum()
    return float((d.p - d.a).abs().mean())


# ------------------------------------------------------------------ nested calibration
def history(frame):
    """Per model x target x year: sum of actual and of raw predicted amounts."""
    rows = []
    for t in ("t1", "t2"):
        w, act = SPEC[t]["weight"], actual_amount(frame, t).to_numpy()
        for m in names_in(frame):
            d = pd.DataFrame({"year": frame.year.to_numpy(), "actual": act, "pred": (frame[f"{t}_{m}"] * frame[w]).to_numpy()}).groupby("year", as_index=False).sum()
            rows.append(d.assign(model=m, target=t))
    return pd.concat(rows, ignore_index=True)


def k_table(hist):
    """k for each model x target x year from EARLIER years only (1.0 when there are none or the earlier predictions sum to 0)."""
    out = []
    for (m, t), g in hist.groupby(["model", "target"]):
        g = g.sort_values("year")
        ca, cp = g.actual.cumsum().shift(1), g.pred.cumsum().shift(1)
        out.append(pd.DataFrame({"model": m, "target": t, "year": g.year.to_numpy(), "k": (ca / cp).where(cp > 0).fillna(1.0).to_numpy()}))
    return pd.concat(out, ignore_index=True)


def apply_k(frame, ktab, use):
    """Multiply predictions by the model's nested k for the row's year where use[(model, target)]; C's neighbour quantiles with C's k."""
    out = frame.copy()
    kk = {(m, t): g.set_index("year").k for (m, t), g in ktab.groupby(["model", "target"])}
    for m in names_in(frame):
        for t in ("t1", "t2"):
            f = frame.year.map(kk[(m, t)]).fillna(1.0).to_numpy() if use.get((m, t), False) else 1.0
            out[f"{t}_{m}"] = frame[f"{t}_{m}"] * f
            if m == "C":
                for q in ("lo", "hi"):
                    out[f"{t}_C_{q}"] = frame[f"{t}_C_{q}"] * f
    return out


def decide_use(oos_raw, ktab):
    kk = {(m, t): g.set_index("year").k for (m, t), g in ktab.groupby(["model", "target"])}
    use, rows = {}, []
    for m in names_in(oos_raw):
        for t in ("t1", "t2"):
            raw = stat_err(oos_raw, t, m)
            cal = stat_err(oos_raw, t, m, oos_raw.year.map(kk[(m, t)]).fillna(1.0).to_numpy())
            use[(m, t)] = bool(cal < raw)
            rows.append({"model": m, "target": t, "use_calibration": use[(m, t)], "raw_stat_abs_err": raw, "nested_stat_abs_err": cal, "unit": SPEC[t]["unit"]})
    return use, pd.DataFrame(rows)


def add_z(frame):
    """Z = illustrative relief allocation under a 95% coverage assumption, from each model's (calibrated) T2 prediction (budget.py)."""
    out = frame.copy()
    out["z_actual"] = frame.relief_gap_to_95pct.fillna(0)
    for m in names_in(frame):
        out[f"z_{m}"] = budget_components(frame, frame[f"t1_{m}"], frame[f"t2_{m}"]).relief_need
    return out


# ------------------------------------------------------------------ historical scenario range (T1)
def range_rows(frame, pool_min=MIN_POOL_YEARS):
    """Per model (A, B, D from whole earlier years' residuals; C from neighbours) x state x year: low / point / high, whether the actual is inside."""
    cls = add_year_class(frame).drop_duplicates(["state_alpha", "year"]).set_index(["state_alpha", "year"]).sy_class
    pools = {m: residual_pool(frame, m, "t1") for m in RESAMPLED}
    rows = []
    for y in sorted(frame.year.unique()):
        d = frame[frame.year == y]
        actual = actual_amount(d, "t1").groupby(d.state_alpha).sum()
        for m in RESAMPLED:
            pool = pools[m][pools[m].year < y]
            if pool.year.nunique() < pool_min:
                continue
            for s, (lo, hi) in total_range(d, d[f"t1_{m}"], pool, weight="liability").items():
                rows.append({"model": m, "state": s, "year": y, "low": lo, "high": hi, "actual": float(actual[s]),
                             "point": float((d[f"t1_{m}"] * d.liability)[d.state_alpha == s].sum())})
        for s, g in d.groupby("state_alpha"):
            rows.append({"model": "C", "state": s, "year": y, "low": float((g.t1_C_lo * g.liability).sum()), "high": float((g.t1_C_hi * g.liability).sum()),
                         "actual": float(actual[s]), "point": float((g.t1_C * g.liability).sum())})
    r = pd.DataFrame(rows)
    r["sy_class"] = [cls[(s, y)] for s, y in zip(r.state, r.year)]
    r["inside"] = (r.actual >= r.low) & (r.actual <= r.high)
    r["upper_miss"], r["lower_miss"] = r.actual > r.high, r.actual < r.low
    r["width"] = r.high - r.low
    return r


def attach_range(m, cov):
    m = m.copy()
    for col in ("range_k", "range_n", "range_width", "range_upper_miss", "range_lower_miss"):
        m[col] = np.nan
    for grp in m.group.unique():
        for mod in RANGED:
            c = cov[cov.model == mod]
            c = c if grp == "all" else c[c.sy_class == grp]
            i = (m.model == mod) & (m.group == grp)
            if len(c):
                m.loc[i, ["range_k", "range_n", "range_width", "range_upper_miss", "range_lower_miss"]] = [
                    float(c.inside.sum()), float(len(c)), float(c.width.mean()), float(c.upper_miss.sum()), float(c.lower_miss.sum())]
    m["range_cov"] = m.range_k / m.range_n
    return m


def budget_range_rows(cov, point, method):
    """Budget range: the best validated method, widened so the headline model's calibrated point estimate lies inside it.
    `point` = Series (state, year) -> headline model's predicted statewide X."""
    r = cov[cov.model == method].set_index(["state", "year"])
    out = r[["low", "high", "actual", "sy_class"]].copy()
    out["point"] = point.rename_axis(["state", "year"]).reindex(out.index)
    out["point_inside"] = (out.point >= out.low) & (out.point <= out.high)
    out["budget_low"], out["budget_high"] = np.minimum(out.low, out.point), np.maximum(out.high, out.point)
    out["widened"] = ~out.point_inside
    out["inside"] = (out.actual >= out.budget_low) & (out.actual <= out.budget_high)
    return out


# ------------------------------------------------------------------ tuning and selection
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
        best[name] = {k: (int(v) if k in ("max_iter", "max_depth", "k") else float(v)) for k, v in t.loc[t.wape.idxmin(), list(grid)].items()}
    return best, pd.DataFrame(rows)


def select_headline(M):
    """Item 12 (Entry 3): lowest drought-state-year statewide absolute $ error among A, B, C, D, provided pooled top-20 capture beats B3 and B4;
    candidates within 5% of the lowest error tie and the simplest (D < A < C < B) wins; if none qualifies the highest-capture candidate is used."""
    P = M[(M.target == "t1") & (M.split == "pooled")]
    cap = P[P.group == "all"].set_index("model").capture_top20
    err = P[P.group == "drought"].set_index("model").stat_abs_err
    bar = max(cap["B3"], cap["B4"])
    rows = pd.DataFrame({"drought_stat_abs_err": err[CANDIDATES], "capture_all": cap[CANDIDATES]})
    rows["beats_B3_and_B4"] = rows.capture_all > bar
    elig = rows[rows.beats_B3_and_B4]
    if len(elig):
        low = elig.drought_stat_abs_err.min()
        tied = [m for m in SIMPLEST_FIRST if m in elig.index and elig.loc[m, "drought_stat_abs_err"] <= low * (1 + TIE_BAND)]
        chosen, why = tied[0], (f"lowest drought-year statewide absolute $ error among candidates beating B3 ({cap['B3']:.3f}) and B4 ({cap['B4']:.3f}) on capture; "
                                f"within {TIE_BAND:.0%} of the lowest error: {tied}; simplest wins")
        met = True
    else:
        chosen, why, met = rows.capture_all.idxmax(), "rule NOT met: no candidate beats both B3 and B4 on top-20 capture; highest-capture candidate used", False
    return {"chosen": chosen, "rule_met": met, "reason": why}, rows


# ------------------------------------------------------------------ trigger agreement (item 16)
def trigger_agreement(frame, model):
    """B2a (USDA binary trigger) vs `model` flagging the same number of counties per state-year. County-year 2x2 + precision / recall for significant payouts."""
    f = frame.assign(_p=frame[f"t1_{model}"] * frame.liability)
    cd = f.groupby(["state_alpha", "fips", "year"], as_index=False).agg(pred=("_p", "sum"), actual=("drought_indemnity", "sum"), trigger=("erp_trigger", "max"))
    cd["model_high"] = False
    for (s, y), g in cd.groupby(["state_alpha", "year"]):
        n = int(g.trigger.sum())
        if n:
            cd.loc[_top(g, "pred", n).index, "model_high"] = True
    rows = f.merge(cd[["state_alpha", "fips", "year", "model_high"]], on=["state_alpha", "fips", "year"])
    rows["sig"] = rows.t1_actual >= SIG_SHARE
    pr = {}
    for name, flag in [("B2a trigger", rows.erp_trigger == 1), (f"{LABEL[model]} (top N)", rows.model_high)]:
        tp = int((rows.sig & flag).sum())
        pr[name] = {"flagged county-crop-years": int(flag.sum()), "significant county-crop-years": int(rows.sig.sum()), "true positives": tp,
                    "precision": tp / flag.sum() if flag.sum() else np.nan, "recall": tp / rows.sig.sum() if rows.sig.sum() else np.nan}
    return cd, pd.DataFrame(pr).T


def two_by_two(cd, label):
    def cell(t, h):
        g = cd[(cd.trigger == t) & (cd.model_high == h)]
        return len(g), g.actual.sum(), (g.actual.mean() if len(g) else np.nan)
    c = {(t, h): cell(t, h) for t in (1, 0) for h in (True, False)}
    tbl = pd.DataFrame({"": ["trigger eligible", "trigger not eligible"],
                        f"{label} high": [f"{c[(1, True)][0]} county-years, ${c[(1, True)][1] / 1e6:,.1f}M", f"{c[(0, True)][0]} county-years, ${c[(0, True)][1] / 1e6:,.1f}M"],
                        f"{label} low": [f"{c[(1, False)][0]} county-years, ${c[(1, False)][1] / 1e6:,.1f}M", f"{c[(0, False)][0]} county-years, ${c[(0, False)][1] / 1e6:,.1f}M"]})
    a, b = c[(0, True)], c[(1, False)]
    fav = ("model-high/trigger-no" if (a[2] > b[2] if not (np.isnan(a[2]) or np.isnan(b[2])) else False) else
           "model-low/trigger-yes" if not (np.isnan(a[2]) or np.isnan(b[2])) else "n/a (a cell is empty)")
    note = (f"Disagreement cells: model high / trigger no = {a[0]} county-years, ${a[1] / 1e6:,.1f}M total, ${(a[2] / 1e6 if a[0] else float('nan')):,.2f}M per county-year; "
            f"model low / trigger yes = {b[0]} county-years, ${b[1] / 1e6:,.1f}M total, ${(b[2] / 1e6 if b[0] else float('nan')):,.2f}M per county-year. "
            f"Actual payouts favoured: **{fav}** (larger mean payout per county-year).")
    return tbl, note


# ------------------------------------------------------------------ misses, facts
def drought_facts_ia2013():
    f = REPO / "data" / "processed" / "drought" / "drought_weekly.parquet"
    if not f.exists():
        return None
    d = pd.read_parquet(f, filters=[("map_date", ">=", pd.Timestamp("2013-01-01")), ("map_date", "<=", pd.Timestamp("2013-12-31"))])
    d["fips"] = d.fips.astype(str).str.zfill(5)
    x = d[d.fips.str.startswith("19")].copy()
    x["d1p"], x["d2p"] = x.D1 + x.D2 + x.D3 + x.D4, x.D2 + x.D3 + x.D4
    g1, g2 = x.groupby("map_date").d1p.mean(), x.groupby("map_date").d2p.mean()
    at = lambda s, day: float(s.loc[pd.Timestamp(f"2013-{day}")])
    # how many Iowa counties would B2a trigger on maps from Apr 1 vs only from Jun 1 (the spring maps still carried 2012's drought)
    x = x[x.map_date <= pd.Timestamp("2013-08-13")].sort_values(["fips", "map_date"])
    x["d2"], x["d3"] = x.d2p > 0, (x.D3 + x.D4) > 0

    def trig(start):
        y = x[x.map_date >= pd.Timestamp(start)]
        def run(v):
            best = cur = 0
            for b in v:
                cur = cur + 1 if b else 0
                best = max(best, cur)
            return best
        r, d3 = y.groupby("fips").d2.apply(run), y.groupby("fips").d3.any()
        return int(((r >= 8) | d3).sum()), int(y.fips.nunique())
    (t_apr, n_ia), (t_jun, _) = trig("2013-04-01"), trig("2013-06-01")
    return {"d1_aug13": at(g1, "08-13"), "d2_aug13": at(g2, "08-13"), "d2_aug27": at(g2, "08-27"), "d2_sep10": at(g2, "09-10"),
            "trig_apr": t_apr, "trig_jun": t_jun, "n_ia": n_ia}


def known_misses(pts, liab):
    """State-years where A, B, C, D and B1 were ALL off by more than 50% (T1 payout $), with a one-line likely reason."""
    miss_models = ["B1"] + CANDIDATES
    w = pts.pivot_table(index=["state_alpha", "year"], columns="model", values="pred")[miss_models]
    act = pts.drop_duplicates(["state_alpha", "year"]).set_index(["state_alpha", "year"]).actual
    rel = w.sub(act, axis=0).div(act, axis=0)
    bad = rel[(rel.abs() > 0.5).all(axis=1)]
    facts = drought_facts_ia2013()
    rows = []
    for (s, y), r in bad.iterrows():
        share = act[(s, y)] / liab[(s, y)]
        direction = "over" if (r > 0).all() else "under" if (r < 0).all() else "mixed"
        if (s, y) == ("IA", 2013) and facts:
            reason = (f"An emerging drought: D1+ covered {facts['d1_aug13']:.0f}% of Iowa by Aug 13 (D2+ {facts['d2_aug13']:.0f}%) and it intensified after the forecast date "
                      f"(D2+ {facts['d2_aug27']:.0f}% on Aug 27, {facts['d2_sep10']:.0f}% on Sep 10). Known limitation: not tuned for.")
        elif direction == "over":
            reason = (f"Quiet year: actual payout only {share:.2%} of insured $ (${act[(s, y)] / 1e6:,.1f}M), so a small absolute miss is a large % miss; models likely over-read mild drought signals.")
        elif direction == "under":
            reason = "Loss not visible in Aug-15 inputs (late-season drought or a loss coded to another cause)."
        else:
            reason = "Models disagree in sign; payout depends on local conditions the Aug-15 inputs only weakly capture."
        rows.append({"state": s, "year": y, "actual $M": act[(s, y)] / 1e6, "direction": direction,
                     **{LABEL[m] + " $M": w.loc[(s, y), m] / 1e6 for m in miss_models}, "likely reason": reason})
    return pd.DataFrame(rows), facts


def state_year_points(frame, t="t1", names=MODELS):
    rows = []
    for m in names:
        cy = county_year(frame, f"{t}_{m}", t).groupby(["state_alpha", "year"], as_index=False)[["pred", "actual"]].sum()
        rows.append(cy.assign(model=m))
    return pd.concat(rows, ignore_index=True)


# ------------------------------------------------------------------ formatting
def fmt(v):
    if isinstance(v, (bool, np.bool_)):
        return "yes" if v else "no"
    if isinstance(v, (float, np.floating)):
        return "–" if np.isnan(v) else (f"{v:,.0f}" if abs(v) >= 1e4 or (abs(v) >= 1 and v == round(v)) else f"{v:.3f}")
    return str(v)


def md(df):
    lines = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "|".join("---" for _ in df.columns) + "|"]
    return "\n".join(lines + ["| " + " | ".join(fmt(v) for v in r) + " |" for r in df.itertuples(index=False)])


def f_pct(v, d=0):
    return "–" if pd.isna(v) else f"{v * 100:,.{d}f}%"


def f_amt(v, unit):
    if pd.isna(v):
        return "–"
    return f"${v / 1e6:,.1f}M" if unit == "$" else f"{v / 1e3:,.0f}k ac"


def summary_md(m, unit="$", models=None, ranged=True):
    """One table per split x target x group; bold = best of the column among the models shown (calibration: closest to 1)."""
    r = m[m.model.isin(models or MODELS)].set_index("model")
    order = [x for x in (models or MODELS) if x in r.index]
    cols = [("stat_abs_err", "Statewide abs. error", "min", lambda x: f_amt(x, unit)), ("under_budget_total", "Under-budgeted (total)", "min", lambda x: f_amt(x, unit)),
            ("worst_shortfall", "Worst state-year shortfall", "min", lambda x: f_amt(x, unit)), ("county_wape", "County WAPE", "min", lambda x: "–" if pd.isna(x) else f"{x:.2f}"),
            ("capture_top20", "Top-20 capture", "max", lambda x: f_pct(x, 1)), ("auc", "AUC", "max", lambda x: "–" if pd.isna(x) else f"{x:.3f}"),
            ("calibration", "Σpred/Σactual", "one", lambda x: "–" if pd.isna(x) else f"{x:.2f}")]
    best = {}
    for key, _, rule, _f in cols:
        s = r.loc[order, key].dropna()
        if len(s):
            best[key] = s.idxmin() if rule == "min" else s.idxmax() if rule == "max" else (s - 1).abs().idxmin()
    head = "| Model | " + " | ".join(c[1] for c in cols) + (" | Range coverage | Range width | Upper-bound misses |" if ranged else " |")
    lines = [head, "|---|" + "---|" * (len(cols) + (3 if ranged else 0))]
    for name in order:
        cells = []
        for key, _, _, f in cols:
            t = f(r.loc[name, key])
            cells.append(f"**{t}**" if best.get(key) == name and t != "–" else t)
        if ranged:
            x = r.loc[name]
            has = name in RANGED and not pd.isna(x.range_cov)
            cells += [f"{x.range_cov * 100:.0f}% ({int(x.range_k)}/{int(x.range_n)})" if has else "–", f_amt(x.range_width, unit) if has else "–",
                      f"{int(x.range_upper_miss)}" if has else "–"]
        lines.append(f"| {LABEL[name]} | " + " | ".join(cells) + " |")
    rnd = m[m.model == "Random"]
    if len(rnd):
        bc = r.best_capture.dropna()
        lines.append(f"| *Random counties / best possible* | – | – | – | – | *{f_pct(rnd.capture_top20.iloc[0], 1)} / {f_pct(bc.iloc[0], 1) if len(bc) else '–'}* | – | – |" + (" – | – | – |" if ranged else ""))
    return "\n".join(lines)


# ------------------------------------------------------------------ ablation, G experiment
def ablation(train, val, params, use):
    """B with the pre-revision feature list vs the full new list (same hyper-parameters, same nested-calibration decision)."""
    p_old = {**params, "B": {**params["B"], "features": FEATURES_OLD}}
    raw = pd.concat([walk_forward(train, p_old, names=["B"]), fit_predict(train, val, p_old, names=["B"])], ignore_index=True)
    cal = add_z(apply_k(raw, k_table(history(raw)), {k: v for k, v in use.items() if k[0] == "B"}))
    return cal


def g_earlier_run():
    try:
        txt = subprocess.run(["git", "-C", str(REPO), "show", "a5c10b9:app/model/results/validation_results.csv"], capture_output=True, text=True, check=True).stdout
        import io
        g = pd.read_csv(io.StringIO(txt))
        g = g[(g.target == "t1") & (g.model == "G") & (g.calibrated == True) & (g.group == "all")]  # noqa: E712
        return g[["split", "capture_top20", "wape", "auc_any_payout", "calibration"]].reset_index(drop=True)
    except Exception:
        return None


# ------------------------------------------------------------------ report
def write_report(c):
    M, hl, verdict = c["M"], c["headline"], c["verdict"]
    sel = lambda t, split, grp: M[(M.target == t) & (M.split == split) & (M.group == grp)]
    pool = lambda t, grp: sel(t, "pooled", grp)
    names_hl = [hl, "B2a", "B2b"]
    sp_titles = [("pooled", "Pooled 2006-2015 (walk-forward + validation)"), ("walk-forward", "Walk-forward 2006-2012"), ("validation", "Validation 2013-2015")]
    drought_sy = {sp: ", ".join(sorted(f"{s} {y}" for (s, y), v in c["class_of"].items() if v == "drought" and y in c["years"][sp])) for sp in c["years"]}
    out = [f"""# Validation report: nested-calibrated models, walk-forward 2006-2012 and validation 2013-2015

**Headline model: {LABEL[hl]}** ({verdict['reason']}). Everything here comes from out-of-sample years 2006-2015; `testing/` was not read and `final_test.py` has not been run.
Predictions are calibrated with NESTED factors (k for year Y comes only from earlier years' predictions and outcomes; k = 1 in 2006), and calibration is kept for a model-target
only if it lowers statewide absolute $ error (section 4). Preprocessing, B1 bins, look-alike pools and rain/irrigation averages use only earlier years (DECISIONS.md, Entries 3-4).
Wording: **X** = estimated insurance payouts (T1 x liability), **Y** = estimated deductible exposure, **Z** = illustrative relief allocation under a 95% coverage assumption (inspired by
USDA ERP 2022), not a prediction of any program payment. Raw numbers: `validation_results.csv`, `validation_state_years.csv`, `validation_predictions.csv`, `calibration.csv`, `trigger_agreement_*.csv`.

Metric definitions: *Statewide abs. error* = mean over state-years of |Σ predicted - Σ actual|; *Under-budgeted (total)* = Σ over state-years of max(0, actual - predicted); *Worst state-year
shortfall* = the largest single state-year max(0, actual - predicted); *County WAPE* = Σ|error| / Σ actual over county-years (crops summed); *Top-20 capture* = share of actual payouts in the 20
counties (crops summed) with the highest predicted payout, averaged over state-years, ties broken by county FIPS; *AUC* uses each model's own predicted amount; *Σpred/Σactual* is calibration
(<1 under-budgets). AUC inside the drought-only tables is not informative (almost every county pays in a drought year, so few zero-payout rows remain). A drought state-year = actual statewide payout >= 3% of insured $ ({'; '.join(f'{k}: {v}' for k, v in drought_sy.items() if k != 'pooled')}). Bold = best in column.
The historical scenario range is the 10th-90th percentile (A, B, D from whole earlier years' residuals, years < Y and at least 3 of them, so only 2009+; C from its look-alikes' spread); it is a
description of past outcomes, not a probability statement. Tuned on walk-forward only: `{json.dumps(c['params'])}`.
"""]
    out.append(f"## 1. Headline vs current USDA practice (B2a binary trigger, B2b tiered trigger)\n\nSelection rule (fixed in Entry 3): {verdict['reason']}.\n\n{md(c['rule_table'].reset_index().rename(columns={'index': 'candidate'}))}\n")
    for grp, gt in [("all", "all state-years"), ("drought", "drought state-years only")]:
        for sp, st in sp_titles:
            t = sel("t1", sp, grp)
            if len(t):
                out.append(f"**{st}, {gt}** ({int(t.state_years.iloc[0])} state-years)\n\n{summary_md(t, '$', names_hl)}\n")
    out.append("## 2. All models, T1 (X: estimated insurance payouts)\n")
    for grp, gt in [("all", "all state-years"), ("drought", "drought state-years only")]:
        for sp, st in sp_titles:
            t = sel("t1", sp, grp)
            if len(t):
                out.append(f"**{st}, {gt}**\n\n{summary_md(t, '$')}\n")
    out.append("**Quiet state-years only, pooled**\n\n" + summary_md(pool("t1", "quiet"), "$") + "\n")
    out.append("## 3. T2 (damaged acres) and Z (illustrative relief allocation)\n")
    for t, label, unit in [("t2", "T2 damaged acres", "acres"), ("z", "Z illustrative relief allocation, 95% coverage assumption", "$")]:
        for grp, gt in [("all", "all state-years"), ("drought", "drought state-years only")]:
            for sp, st in [sp_titles[0], sp_titles[2]]:
                m = sel(t, sp, grp)
                if len(m):
                    out.append(f"**{label}: {st}, {gt}**\n\n{summary_md(m, unit, ranged=False)}\n")
    cal = c["cal"]
    out.append("## 4. Nested calibration\n\nk for year Y = Σ actual / Σ predicted over earlier out-of-sample years. Calibration is applied to a model-target only if it lowers its statewide absolute error over 2006-2015 "
               "(uncalibrated vs nested-calibrated shown). `k_latest` (all of 2006-2015) is what `budget.py` uses for new years.\n\n" +
               md(cal.assign(raw_stat_abs_err=cal.apply(lambda r: f_amt(r.raw_stat_abs_err, r.unit), axis=1),
                             nested_stat_abs_err=cal.apply(lambda r: f_amt(r.nested_stat_abs_err, r.unit), axis=1))
                  .drop(columns=["unit"]).assign(model=lambda d: d.model.map(LABEL))) + "\n")
    cov = c["cov"]
    rc = []
    for m in RANGED:
        for grp in ("all", "drought", "quiet"):
            x = cov[cov.model == m]
            x = x if grp == "all" else x[x.sy_class == grp]
            rc.append({"model": LABEL[m], "state-years": grp, "n": len(x), "inside": int(x.inside.sum()), "coverage": f_pct(x.inside.mean()) if len(x) else "–",
                       "mean width": f_amt(x.width.mean(), "$") if len(x) else "–", "actual above upper bound": int(x.upper_miss.sum()), "actual below lower bound": int(x.lower_miss.sum())})
    bud = c["bud"]
    out.append(f"## 5. Historical scenario range (10th-90th percentile; rough)\n\nCoverage by state-year type, pooled 2006-2015 (A, B, D have ranges only from 2009):\n\n{md(pd.DataFrame(rc))}\n\n"
               f"Best-covering method (closest to 80% overall): **{c['best_range']}**. The budget range is that method's range widened to contain {LABEL[hl]}'s point estimate: it "
               f"contained the actual statewide payout in {int(bud.inside.sum())} of {len(bud)} state-years; the headline point estimate was inside the raw range in {int(bud.point_inside.sum())} of {len(bud)} "
               f"(widened in {int((~bud.point_inside).sum())}). Upper-bound misses (actual above the range) are the costly ones for a budget: see the column above.\n")
    pts = c["pts"]
    rows = []
    for (s, y), b in bud.sort_index(level=["state", "year"]).iterrows():
        row = {"state": s, "year": y, "type": c["class_of"][(s, y)], "actual X $M": f"{b.actual / 1e6:,.1f}"}
        p = pts[(pts.state_alpha == s) & (pts.year == y)].set_index("model").pred
        for m in [hl, "B2a", "B2b"] + [x for x in CANDIDATES if x != hl]:
            row[LABEL[m] + " $M"] = f"{p[m] / 1e6:,.1f}"
        row["budget range $M"] = f"{b.budget_low / 1e6:,.1f}–{b.budget_high / 1e6:,.1f}"
        row["actual vs range"] = "inside ✓" if b.inside else "outside ✗"
        rows.append(row)
    out.append(f"### Statewide X per state-year ($M): actual, headline, USDA triggers and the other candidates\n\n{md(pd.DataFrame(rows))}\n")
    ab = c["ablation"]
    out.append("## 6. Feature ablation: B with the old features vs the new features\n\n"
               "Old = the pre-revision column list (corrected map cutoff, prior-year normals); new = old + d0/d1 last-map shares, 4-week changes in D1+ and DSCI, 30-day precip ratio. Same hyper-parameters, nested calibration as in B.\n\n" + ab + "\n")
    out.append("## 7. Trigger agreement: B2a vs the headline model\n\nSignificant payout = drought payout share >= 2% of insured value in a county-crop-year. The model flags its top N counties of each state-year by predicted payout, "
               "N = the number of counties B2a makes eligible that state-year (crops summed; ties by FIPS). Precision / recall are over county-crop-years; the 2x2 counts county-years (crops summed) and their actual drought payouts.\n")
    for sp, st in sp_titles:
        tbl, note, pr = c["trigger"][sp]
        out.append(f"**{st}**\n\n{md(pr.reset_index().rename(columns={'index': 'flagging rule'}))}\n\n{md(tbl)}\n\n{note}\n")
    out.append("## 8. Known misses\n\nState-years where B1 and all four candidates (A, B, C, D) were off by more than 50% (statewide X):\n\n" + (md(c["misses"]) if len(c["misses"]) else "None.") + "\n")
    f13 = c["facts"]
    if f13:
        p13 = c["pts"][(c["pts"].state_alpha == "IA") & (c["pts"].year == 2013)].set_index("model").pred
        out.append(f"**Iowa 2013 is a known limitation, not tuned for.** It is an emerging drought: D1+ already covered {f13['d1_aug13']:.0f}% of Iowa on the Aug 13 map (D2+ {f13['d2_aug13']:.0f}%), "
                   f"and it intensified after the forecast date (D2+ {f13['d2_aug27']:.0f}% on Aug 27, {f13['d2_sep10']:.0f}% on Sep 10). Actual X was ${p13.iloc[0] * 0 + c['pts'][(c['pts'].state_alpha == 'IA') & (c['pts'].year == 2013)].actual.iloc[0] / 1e6:,.0f}M; "
                   + ", ".join(f"{LABEL[m]} ${p13[m] / 1e6:,.0f}M" for m in [hl, "B2a", "B2b"] + [x for x in CANDIDATES if x != hl]) + ". No feature, model or setting was changed to catch 2013. Note that B2a / B2b look close here for an unrelated reason: they trigger in {f13['trig_apr']} of {f13['n_ia']} Iowa counties only because the April-May maps still carried 2012's drought; on maps from Jun 1 on, {f13['trig_jun']} counties trigger.\n")
    out.append("The Aug 10, 2020 derecho is not treated as an expected miss: wind is not part of the drought label.\n")
    g = c["g_exp"]
    out.append("## 9. G (TabPFN v2): earlier experiment, not rerun\n\n" + ("G was evaluated once with the pre-revision data and calibration (commit a5c10b9: old map cutoff Aug 14, in-sample k, old normals); it is not a candidate here "
               "(CPU prediction 353 s per year, MPS runs not bit-reproducible). Its T1 results then:\n\n" + md(g) + "\n" if g is not None else "Earlier results are in git history (commit a5c10b9).\n"))
    out.append(f"## Appendix\n\n### Strategy A coefficients\n{md(c['coefs'])}\n\n### Tuning grid (walk-forward WAPE, uncalibrated)\n{md(c['tune'].sort_values(['model', 'wape']))}\n")
    (RESULTS / "validation_report.md").write_text("\n".join(out))


def main():
    RESULTS.mkdir(exist_ok=True)
    train, val = load_usable("training"), load_usable("validation")
    print(f"usable rows: training {len(train)}, validation {len(val)}")
    params, tune_tbl = tune(train)
    tune_tbl.to_csv(RESULTS / "tuning.csv", index=False)
    json.dump(params, open(RESULTS / "params.json", "w"), indent=2)
    print("tuned params:", params)

    oos_raw = pd.concat([walk_forward(train, params), fit_predict(train, val, params)], ignore_index=True)
    oos_raw["split"] = np.where(oos_raw.year <= 2012, "walk-forward", "validation")
    hist = history(oos_raw)
    ktab = k_table(hist)
    use, cal = decide_use(oos_raw, ktab)
    oosc = add_z(apply_k(oos_raw, ktab, use))
    k_latest = hist.groupby(["model", "target"]).apply(lambda g: g.actual.sum() / g.pred.sum() if g.pred.sum() > 0 else 1.0, include_groups=False).rename("k_latest").reset_index()
    cal = cal.merge(k_latest, on=["model", "target"])
    cal["k_applied_to_new_years"] = np.where(cal.use_calibration, cal.k_latest, 1.0)
    cal.to_csv(RESULTS / "calibration.csv", index=False)
    hist.to_csv(RESULTS / "calibration_history.csv", index=False)
    print(cal[cal.target == "t1"][["model", "use_calibration", "k_latest"]].round(3).to_string(index=False))

    years = {"walk-forward": set(range(2006, 2013)), "validation": set(range(2013, 2016)), "pooled": set(range(2006, 2016))}
    cov = range_rows(oosc)
    parts = []
    for t in ("t1", "t2", "z"):
        for sp, ys in years.items():
            f = oosc[oosc.year.isin(ys)]
            m = metrics(f, MODELS, t)
            if t == "t1":
                m = attach_range(m, cov[cov.year.isin(ys)])
            parts.append(m.assign(split=sp))
    M = pd.concat(parts, ignore_index=True)
    M.to_csv(RESULTS / "validation_results.csv", index=False)

    verdict, rule_table = select_headline(M)
    hl = verdict["chosen"]
    pooled_t1 = M[(M.target == "t1") & (M.split == "pooled") & (M.group == "all") & M.model.isin(RANGED) & M.range_n.notna()]
    best_range = pooled_t1.assign(gap=(pooled_t1.range_cov - 0.8).abs()).sort_values(["gap", "model"]).model.iloc[0]
    pts = state_year_points(oosc, "t1")
    bud = budget_range_rows(cov, pts[pts.model == hl].set_index(["state_alpha", "year"]).pred, best_range)
    json.dump({"method": best_range, "label": "historical scenario range (rough)", "pooled_coverage": {r.model: r.range_cov for r in pooled_t1.itertuples()},
               "target": 0.8, "headline_point_inside_range": f"{int(bud.point_inside.sum())}/{len(bud)}", "budget_range_coverage": float(bud.inside.mean())},
              open(RESULTS / "range_method.json", "w"), indent=2)
    json.dump({"chosen": hl, "headline": hl, "rule_met": verdict["rule_met"], "reason": verdict["reason"], "params": params,
               "frozen_models": CANDIDATES, "baselines": BASELINES, "rule": "Entry 3 item 12", "candidates": rule_table.reset_index().to_dict("records")},
              open(RESULTS / "chosen_model.json", "w"), indent=2, default=float)
    print("headline:", hl, "|", verdict["reason"])

    keep = (KEY + CARRY + ["split", "t1_actual", "t2_actual"] + [f"t{i}_{m}" for i in (1, 2) for m in MODELS] + ["t1_C_lo", "t1_C_hi", "t2_C_lo", "t2_C_hi"])
    oosc[keep].to_csv(RESULTS / "oos_predictions.csv", index=False)
    vv = oosc[oosc.year >= 2013]
    vp_rows = []
    for m in MODELS:
        d = vv[["fips", "county_name", "state_alpha", "crop", "year", "liability", "insured_acres"]].copy()
        d.insert(5, "model", m)
        d["pred_share_t1"], d["actual_share_t1"] = vv[f"t1_{m}"], vv.t1_actual
        d["pred_usd"], d["actual_usd"] = vv[f"t1_{m}"] * vv.liability, vv.drought_indemnity.fillna(0)
        d["pred_share_t2"], d["actual_share_t2"] = vv[f"t2_{m}"], vv.t2_actual
        d["pred_damaged_acres"], d["actual_damaged_acres"] = vv[f"t2_{m}"] * vv.insured_acres, vv.drought_loss_acres.fillna(0)
        d["pred_relief_z_usd"], d["actual_relief_z_usd"] = vv[f"z_{m}"], vv.z_actual
        vp_rows.append(d)
    pd.concat(vp_rows, ignore_index=True).to_csv(RESULTS / "validation_predictions.csv", index=False)
    pts.merge(cov[["model", "state", "year", "low", "high", "inside"]].rename(columns={"state": "state_alpha"}), on=["model", "state_alpha", "year"], how="left").to_csv(RESULTS / "validation_state_years.csv", index=False)
    class_of = add_year_class(oosc).drop_duplicates(["state_alpha", "year"]).set_index(["state_alpha", "year"]).sy_class.to_dict()
    misses, facts = known_misses(pts, oosc.groupby(["state_alpha", "year"]).liability.sum())

    # feature ablation
    ab_cal = ablation(train, val, params, use)
    ab_rows = []
    for label, frame in [("B new features", oosc), ("B old features", ab_cal)]:
        for sp, ys in [("pooled", years["pooled"]), ("validation", years["validation"])]:
            for grp in ("all", "drought"):
                f = frame[frame.year.isin(ys)]
                r = metrics(f, ["B"], "t1")
                r = r[r.group == grp]
                if len(r):
                    r = r.iloc[0]
                    ab_rows.append({"features": label, "split": sp, "state-years": grp, "statewide abs. error": f_amt(r.stat_abs_err, "$"), "county WAPE": f"{r.county_wape:.3f}",
                                    "top-20 capture": f_pct(r.capture_top20, 1), "AUC": f"{r.auc:.3f}", "Σpred/Σactual": f"{r.calibration:.2f}"})
    ablation_tbl = md(pd.DataFrame(ab_rows))
    pd.DataFrame(ab_rows).to_csv(RESULTS / "ablation_B_features.csv", index=False)

    # trigger agreement
    trig = {}
    for sp, ys in years.items():
        cd, pr = trigger_agreement(oosc[oosc.year.isin(ys)], hl)
        tbl, note = two_by_two(cd, LABEL[hl])
        trig[sp] = (tbl, note, pr)
        pr.to_csv(RESULTS / f"trigger_agreement_precision_recall_{sp}.csv")
        cd.to_csv(RESULTS / f"trigger_agreement_county_years_{sp}.csv", index=False)

    coef = Hurdle().fit(train, T1).coefficients()
    coef.to_csv(RESULTS / "hurdle_coefficients.csv", index=False)
    coefs = coef.assign(_m=coef.fillna(0).drop(columns="feature").abs().max(axis=1)).sort_values("_m", ascending=False).drop(columns="_m").head(12)
    g = g_earlier_run()
    if g is not None:
        g.to_csv(RESULTS / "experiment_G_earlier_run.csv", index=False)
    write_report(dict(M=M, headline=hl, verdict=verdict, rule_table=rule_table, params=params, class_of=class_of, years=years, cal=cal, cov=cov, bud=bud,
                      best_range=best_range, pts=pts, facts=facts, ablation=ablation_tbl, trigger=trig, misses=misses, g_exp=g, coefs=coefs, tune=tune_tbl))
    print("range method:", best_range, "| report ->", RESULTS / "validation_report.md")


if __name__ == "__main__":
    sys.exit(main())
