"""From predictions to the budget (arithmetic, not learned). Imported by the Streamlit app.

Known on Aug 15 from that year's coverage file: liability, insured_acres, avg_coverage (c), full_crop_value.
V = full_crop_value / insured_acres (full value per acre).
    X  insurance pays        = predicted T1 x liability
    A  damaged acres         = predicted T2 x insured_acres
    Y  farmers' out-of-pocket = A x V x (1 - c)
    Z  estimated relief need  = A x V x max(0, 0.95 - c)      # ERP-style, upper-end estimate
"""
import json

import numpy as np
import pandas as pd

from data import NUMERIC, RESULTS

ERP_COVERAGE = 0.95


def budget_components(df, t1_pred, t2_pred):
    """Per-row X, damaged acres, Y, Z from predicted shares. df needs liability, insured_acres,
    avg_coverage, full_crop_value."""
    t1, t2 = np.clip(np.asarray(t1_pred, float), 0, 1), np.clip(np.asarray(t2_pred, float), 0, 1)
    v = df.full_crop_value.to_numpy(float) / df.insured_acres.to_numpy(float)
    c = df.avg_coverage.to_numpy(float)
    acres = t2 * df.insured_acres.to_numpy(float)
    return pd.DataFrame({"insurance_pays": t1 * df.liability.to_numpy(float), "damaged_acres": acres,
                         "out_of_pocket": acres * v * (1 - c),
                         "relief_need": acres * v * np.maximum(0.0, ERP_COVERAGE - c)}, index=df.index)


def rollup(df, comp, by=("state_alpha",)):
    """Sum components over counties (default: statewide)."""
    return comp.groupby([df[b] for b in by]).sum()


# ------------------------------------------------------------------ ranges (section 6)
RANGE_LABEL = "rough 80% range (10th-90th percentile)"


def residual_pool(oos, model, target="t1"):
    """Out-of-sample share residuals (actual - predicted) for `target` ('t1' or 't2'), kept per year so that a
    whole year's pattern (all counties hit together) is resampled as one unit, never row by row.
    oos needs fips, crop, year, state_alpha, <target>_actual, <target>_<model>."""
    r = oos[["fips", "crop", "year", "state_alpha"]].copy()
    r["resid"] = oos[f"{target}_actual"] - oos[f"{target}_{model}"]
    return r


def resampled_totals(df, pred, pool, weight="liability", exclude_year=None):
    """Statewide totals if each past year's residual pattern were repeated, whole-year at a time, on this
    scenario. One row per pool year, one column per state (weight = liability -> dollars, insured_acres -> acres).
    Scenario rows with no residual that year get that year's state x crop mean residual."""
    p = pd.DataFrame({"fips": df.fips.to_numpy(), "crop": df.crop.to_numpy(), "state_alpha": df.state_alpha.to_numpy(),
                      "w": df[weight].to_numpy(float), "p": np.asarray(pred, float)})
    rows = {}
    for y, g in pool.groupby("year"):
        if y == exclude_year:
            continue
        m = p.merge(g[["fips", "crop", "resid"]], on=["fips", "crop"], how="left")
        fill = m.groupby(["state_alpha", "crop"]).resid.transform("mean").fillna(0.0)
        m["resid"] = m.resid.fillna(fill)
        m["amt"] = np.clip(m.p + m.resid, 0, 1) * m.w
        rows[y] = m.groupby("state_alpha").amt.sum()
    return pd.DataFrame(rows).T


def total_range(df, pred, pool, weight="liability", exclude_year=None, lo=0.1, hi=0.9):
    """{state: (low, high)}: 10th-90th percentile of the whole-year-resampled statewide totals."""
    t = resampled_totals(df, pred, pool, weight, exclude_year)
    return {s: (float(t[s].quantile(lo)), float(t[s].quantile(hi))) for s in t.columns}


def neighbor_total_range(df, analog, weight="liability", lo=0.1, hi=0.9, k=1.0):
    """{state: (low, high)} from Strategy C's neighbour spread: every county at the same (10th / 90th) quantile of
    its look-alikes' liability-weighted shares, i.e. counties assumed to be hit together. `analog` is a fitted Analog;
    k is C's calibration factor (the quantiles are scaled like C's point predictions)."""
    q_lo, q_hi = analog.quantiles(df, lo, hi)
    w = df[weight].to_numpy(float)
    out = {}
    for s in sorted(df.state_alpha.unique()):
        m = (df.state_alpha == s).to_numpy()
        out[s] = (float((k * q_lo * w)[m].sum()), float((k * q_hi * w)[m].sum()))
    return out


def range_method():
    """Which range method validated best (results/range_method.json written by evaluate.py); default C."""
    f = RESULTS / "range_method.json"
    return json.load(open(f))["method"] if f.exists() else "C"


def chosen_model():
    f = RESULTS / "chosen_model.json"
    return json.load(open(f))["chosen"] if f.exists() else "B"


# ------------------------------------------------------------------ calibration
def load_calibration():
    """results/calibration.csv: one multiplier k per model x target (t1 = payout share, t2 = damaged-acre share), fitted by
    evaluate.py as sum(actual) / sum(predicted) on walk-forward predictions 2006-2012 only."""
    f = RESULTS / "calibration.csv"
    if not f.exists():
        return {}
    c = pd.read_csv(f)
    return {(r.model, r.target): float(r.k) for r in c.itertuples()}


def get_k(model, target="t1"):
    return load_calibration().get((model, target), 1.0)


def calibrate(pred, model, target="t1"):
    """Predicted share x the model's calibration factor k (not clipped: clip to [0, 1] when turning into amounts)."""
    return np.asarray(pred, float) * get_k(model, target)


def calibrated_components(df, t1_pred, t2_pred, model):
    """budget_components() on raw model predictions after applying that model's calibration factors."""
    return budget_components(df, calibrate(t1_pred, model, "t1"), calibrate(t2_pred, model, "t2"))


def statewide_total(df, share_pred, weight="liability"):
    """{state: amount} = sum of clip(share, 0, 1) x weight over the state's rows."""
    amt = pd.Series(np.clip(np.asarray(share_pred, float), 0, 1) * df[weight].to_numpy(float), index=df.index)
    return amt.groupby(df.state_alpha).sum().to_dict()


def widen_to_include(rng, point):
    """Widen {state: (low, high)} so each state's point estimate lies inside. Returns (new range, {state: widened?})."""
    out, widened = {}, {}
    for s, (lo, hi) in rng.items():
        out[s] = (min(lo, point[s]), max(hi, point[s]))
        widened[s] = out[s] != (lo, hi)
    return out, widened


def statewide_range(df, analog=None, preds=None, pool=None, point_model=None):
    """Statewide payout range for the budget: the best-calibrated validated method (range_method.json), around the chosen
    model's calibrated point estimate, widened if that point falls outside it. Always label it rough.
      preds: {model: RAW T1 share predictions for df} for the chosen model (and the range method's model if A or B);
             k factors are applied here.
      analog: a fitted Analog (needed when the method is C).
      pool: residual_pool(...) built from CALIBRATED walk-forward predictions (needed when the method is A or B)."""
    m, point_model, preds = range_method(), point_model or chosen_model(), preds or {}
    point = statewide_total(df, calibrate(preds[point_model], point_model, "t1"))
    if m == "C":
        rng = neighbor_total_range(df, analog, k=get_k("C", "t1"))
    else:
        rng = total_range(df, calibrate(preds[m], m, "t1"), pool)
    rng, widened = widen_to_include(rng, point)
    return {"method": m, "label": RANGE_LABEL, "point": point, "range": rng, "widened": widened}


# ------------------------------------------------------------------ extrapolation warning (section 7)
def training_bounds(train):
    return train[NUMERIC].agg(["min", "max"])


def extrapolation_flags(df, bounds):
    """True where a feature lies beyond the training min / max ('estimate is extrapolated')."""
    x = df[NUMERIC]
    return (x.lt(bounds.loc["min"], axis=1) | x.gt(bounds.loc["max"], axis=1)).where(x.notna(), False)


def extrapolation_message(flags, years="2000-2015"):
    cols = flags.columns[flags.any()]
    if len(cols) == 0:
        return ""
    return (f"beyond anything in {years} for: {', '.join(cols)}; estimate is extrapolated "
            f"({int(flags.any(axis=1).sum())} county rows affected)")
