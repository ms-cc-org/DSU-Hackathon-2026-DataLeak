"""Baselines every model must beat.

B0  training-period mean of the target per state x crop (liability-weighted).
B1  training mean per state x crop x d2_weeks_50pct bin (0, 1-3, 4-7, 8+), forced to rise with drought
    (isotonic regression across the bins), i.e. what an officer could do with the Drought Monitor alone.
"""
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

from data import y_train


def _wmean(y, w):
    return float(np.average(y, weights=w)) if len(y) and np.sum(w) > 0 else 0.0


class B0:
    name = "B0"

    def fit(self, train, target):
        self.target_ = target
        train = train.assign(_y=y_train(train, target))
        self.global_ = _wmean(train._y, train.liability)
        self.table_ = {k: _wmean(g._y, g.liability) for k, g in train.groupby(["state_alpha", "crop"])}
        return self

    def predict(self, df):
        return np.array([self.table_.get(k, self.global_) for k in zip(df.state_alpha, df.crop)])

    score = predict


def d2_bin(weeks):
    w = pd.Series(weeks)
    out = pd.cut(w, [-np.inf, 0, 3, 7, np.inf], labels=False)       # 0 | 1-3 | 4-7 | 8+
    return out.astype(float)                                          # NaN stays NaN


class B1:
    name = "B1"

    def fit(self, train, target):
        self.b0_ = B0().fit(train, target)
        train = train.assign(_y=y_train(train, target))
        bins = d2_bin(train.d2_weeks_50pct).to_numpy()
        self.iso_ = {}
        for (st, cr), g in train.assign(bin=bins).dropna(subset=["bin"]).groupby(["state_alpha", "crop"]):
            agg = g.groupby("bin").apply(lambda h: pd.Series({"m": _wmean(h._y, h.liability),
                                                              "w": h.liability.sum()}), include_groups=False)
            iso = IsotonicRegression(increasing=True, out_of_bounds="clip")
            iso.fit(agg.index.to_numpy(float), agg.m.to_numpy(), sample_weight=agg.w.to_numpy())
            self.iso_[(st, cr)] = iso
        return self

    def predict(self, df):
        base = self.b0_.predict(df)
        bins = d2_bin(df.d2_weeks_50pct).to_numpy()
        out = base.copy()
        for i, (k, b) in enumerate(zip(zip(df.state_alpha, df.crop), bins)):
            if k in self.iso_ and not np.isnan(b):
                out[i] = self.iso_[k].predict([b])[0]
        return out

    score = predict


class B2:
    """USDA ERP trigger rule (see erp.py): a county that triggers gets the training mean share of triggering rows (liability-weighted, per state x
    crop), so its predicted cost is proportional to liability; every other county gets 0. Calibrated afterwards like every model."""
    name = "B2"

    def fit(self, train, target):
        t = train.assign(_y=y_train(train, target))
        q = t[t.erp_trigger == 1]
        self.global_ = _wmean(q._y, q.liability)
        self.table_ = {k: _wmean(g._y, g.liability) for k, g in q.groupby(["state_alpha", "crop"])}
        return self

    def predict(self, df):
        base = np.array([self.table_.get(k, self.global_) for k in zip(df.state_alpha, df.crop)])
        return base * (df.erp_trigger.to_numpy() == 1)

    score = predict
