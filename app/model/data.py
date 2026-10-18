"""Load, join, filter and describe the model data (single source of truth for features and targets).

Reads usda_budget_data/{training,validation}/all_inputs.csv + all_labels.csv and joins them on
fips, crop, year. The held-out testing split can only be loaded with allow_test=True, which only
final_test.py does.

Data folder: $USDA_DATA_DIR, else <repo>/usda_budget_data, else <repo>/app/usda_budget_data.
"""
import os
import pathlib

import numpy as np
import pandas as pd

REPO = pathlib.Path(__file__).resolve().parents[2]
RESULTS = pathlib.Path(__file__).resolve().parent / "results"
KEY = ["fips", "crop", "year"]
T1, T2 = "drought_payout_share", "drought_loss_acre_share"
TARGETS = {"T1": T1, "T2": T2}

DROUGHT = ["d2_weeks_50pct", "d3_weeks_50pct", "d2_max_pct", "dsci_mean", "d2_pct_last_map", "d3_pct_last_map"]
WEATHER = ["precip_ratio_vs_normal", "heat32_days", "heat35_days", "tmax_jul_mean", "gdd"]
SOIL = ["aws_100cm_mm", "droughty_pct", "nccpi"]
IRRIGATION = ["irr_share_train_mean", "irr_known"]
HISTORY = ["acres_planted_prev3_mean", "yield_prev5_mean"]
NUMERIC = DROUGHT + WEATHER + SOIL + IRRIGATION + HISTORY
CATEGORY = ["is_soybeans", "is_ne"]            # dummies built from crop and state_alpha
FEATURES = NUMERIC + CATEGORY

# Never features: identifiers, the year, and anything from labels.csv. precip_mm is redundant with the ratio.
FORBIDDEN = {"fips", "year", "county_name", "precip_mm", "decision_date", T1, T2}

# columns carried along for evaluation and the budget arithmetic (never fed to a model)
CARRY = ["county_name", "state_alpha", "liability", "insured_acres", "avg_coverage", "full_crop_value",
         "drought_indemnity", "drought_loss_acres", "out_of_pocket_drought_loss", "relief_gap_to_95pct"]


def data_root():
    cands = [pathlib.Path(os.environ["USDA_DATA_DIR"])] if os.environ.get("USDA_DATA_DIR") else []
    cands += [REPO / "usda_budget_data", REPO / "app" / "usda_budget_data"]
    for c in cands:
        if (c / "training" / "all_inputs.csv").exists():
            return c
    raise FileNotFoundError(f"usda_budget_data not found; tried {[str(c) for c in cands]}")


def assert_no_leak(cols):
    bad = FORBIDDEN & set(cols)
    if bad:
        raise ValueError(f"forbidden feature columns: {sorted(bad)}")


def load_split(split, allow_test=False):
    """Inputs joined to labels for one split, all rows (call usable() to filter)."""
    if split == "testing" and not allow_test:
        raise PermissionError("testing/ is the held-out set: only final_test.py --i-am-sure may load it")
    d = data_root() / split
    x = pd.read_csv(d / "all_inputs.csv", dtype={"fips": str})
    y = pd.read_csv(d / "all_labels.csv", dtype={"fips": str})
    y = y.drop(columns=[c for c in ["county_name", "state_alpha"] if c in y])
    df = x.merge(y, on=KEY, how="left", validate="one_to_one")
    assert df.fips.str.len().eq(5).all(), "fips must stay 5-character text"
    from erp import erp_trigger                      # B2 only; not in FEATURES
    flag = erp_trigger(int(df.year.min()), int(df.year.max()))
    df = df.merge(flag[["fips", "year", "erp_trigger"]], on=["fips", "year"], how="left")
    df["erp_trigger"] = df.erp_trigger.fillna(0).astype(int)
    df["is_soybeans"] = (df.crop == "SOYBEANS").astype(int)
    df["is_ne"] = (df.state_alpha == "NE").astype(int)
    assert_no_leak(FEATURES)
    return df


def usable(df):
    """insured, liability > 0, a label exists (RMA year available). Zero payouts are kept."""
    ok = (df.insured.astype(str) == "True") & (df.liability > 0) & df.rma_year_available.astype(bool)
    ok &= df[T1].notna() & df[T2].notna()
    return df[ok].reset_index(drop=True)


def load_usable(*splits, allow_test=False):
    return pd.concat([usable(load_split(s, allow_test)) for s in splits], ignore_index=True)


def y_train(df, target):
    """Training target with the few tiny negative values (payment reversals, ~0.0005% of dollars) set to 0."""
    return np.clip(df[target].to_numpy(float), 0, None)


def norm_weights(df):
    """Sample weights: insured dollars, scaled to mean 1 so regularisation strengths stay sensible."""
    w = df.liability.to_numpy(float)
    return w / w.mean()


class Preprocessor:
    """Median imputation + missing-flag columns + standardisation. Fit on training rows only."""

    def __init__(self, cols=FEATURES):
        self.cols = list(cols)

    def fit(self, df):
        x = df[self.cols].astype(float)
        self.median_ = x.median().fillna(0.0)
        self.flags_ = [c for c in self.cols if x[c].isna().any()]
        xi = x.fillna(self.median_)
        self.mean_ = xi.mean()
        self.std_ = xi.std(ddof=0).replace(0, 1.0).fillna(1.0)
        return self

    def transform(self, df):
        x = df[self.cols].astype(float)
        out = (x.fillna(self.median_) - self.mean_) / self.std_
        for c in self.flags_:
            out[f"{c}_missing"] = x[c].isna().astype(float)
        return out


def add_year_class(df, threshold=0.03):
    """Label each state-year 'drought' if actual statewide drought payout >= 3% of insured dollars,
    else 'quiet'. Descriptive grouping for reports only; never used by a model."""
    g = df.groupby(["state_alpha", "year"])
    share = g.drought_indemnity.transform("sum") / g.liability.transform("sum")
    out = df.copy()
    out["sy_class"] = np.where(share >= threshold, "drought", "quiet")
    return out
