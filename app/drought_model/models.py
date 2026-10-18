"""Baselines and models for worse_A / worse_B (binary) and y_A / y_B (level 0-5). Every fitted object (imputer, scaler, base rate, county distributions, neighbours)
is fitted in fit() on the rows it is given. Settings are fixed in DECISIONS.md before any result was seen; nothing is tuned."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

PLUS = ["heat32_days_apr1_to_cutoff", "tmax_mean_30d", "dry_days_30d", "level_last_map", "level_apr1", "prev_fall_level", "nbr_level_last", "dsci_last",
        "dsci_change_4wk", "d0plus_pct_last", "d1plus_pct_last"]
MINUS = ["precip_30d", "precip_60d", "precip_90d", "precip_apr1_to_cutoff", "winter_precip", "precip_30d_ratio", "precip_60d_ratio", "precip_90d_ratio",
         "precip_apr1_to_cutoff_ratio", "winter_precip_ratio", "wb_30d", "wb_90d", "wb_apr1", "aws_100cm_mm", "irr_share"]


def monotone(features):
    return [1 if f in PLUS else -1 if f in MINUS else 0 for f in features]


def step_hat(y, start):
    """Training median of the positive steps (y - start among rows that got worse), at least 1."""
    s = (y - start)[y > start]
    return max(1, int(np.median(s))) if len(s) else 1


def level_from_p(start, p, step, threshold=0.5):
    return np.minimum(np.asarray(start, float) + np.where(np.asarray(p) >= threshold, step, 0), 5).astype(int)


# ---------------------------------------------------------------- baselines
class Persistence:
    name = "Persistence"

    def fit(self, tr, t):
        return self

    def proba(self, te, t):
        return np.zeros(len(te))                    # predicts "no worsening": AUC 0.5 by construction

    def level(self, te, t):
        return te[t["start"]].to_numpy().astype(int)


class Climatology:
    """Per-county share of past (training) years at each level of y: P(worse) = share of the county's years above the start level; level = the county's most common level (ties: lower)."""
    name = "Climatology"

    def fit(self, tr, t):
        self.y_ = tr[t["y"]].astype(int)
        self.county_ = {f: g.to_numpy() for f, g in tr.groupby("fips")[t["y"]]}
        self.global_ = tr[t["y"]].astype(int).to_numpy()
        return self

    def _dist(self, f):
        return self.county_.get(f, self.global_).astype(int)

    def proba(self, te, t):
        return np.array([(self._dist(f) > int(s)).mean() for f, s in zip(te.fips, te[t["start"]])])

    def level(self, te, t):
        out = []
        for f in te.fips:
            c = np.bincount(self._dist(f), minlength=6)
            out.append(int(np.argmax(c)))
        return np.array(out)


class MostCommon:
    name = "Most common level"

    def fit(self, tr, t):
        yy = tr[t["y"]].astype(int)
        self.mode_ = int(np.argmax(np.bincount(yy, minlength=6)))
        self.rate_ = float(tr[t["worse"]].astype(float).mean())
        return self

    def proba(self, te, t):
        return np.full(len(te), self.rate_)

    def level(self, te, t):
        return np.full(len(te), self.mode_)


# ---------------------------------------------------------------- models (binary worse + level via start + step)
class _Base:
    def fit(self, tr, t):
        self.feats_ = list(t["feats"])
        yb = tr[t["worse"]].astype(int).to_numpy()
        self.rate_ = float(yb.mean())
        self.step_ = step_hat(tr[t["y"]].to_numpy(float), tr[t["start"]].to_numpy(float))
        self._fit(tr[self.feats_], yb)
        return self

    def level(self, te, t):
        return level_from_p(te[t["start"]].to_numpy(), self.proba(te, t), self.step_)


class M1Logit(_Base):
    name = "M1 logistic"

    def _fit(self, X, y):
        self.imp_ = SimpleImputer(strategy="median", add_indicator=True).fit(X)
        Z = self.imp_.transform(X)
        self.sc_ = StandardScaler().fit(Z)
        self.m_ = LogisticRegression(class_weight="balanced", C=1.0, max_iter=5000).fit(self.sc_.transform(Z), y)
        self.shift_ = np.log(self.rate_ / (1 - self.rate_))              # balanced weights imply a 50% prior: shift back to the base rate

    def proba(self, te, t):
        z = self.m_.decision_function(self.sc_.transform(self.imp_.transform(te[self.feats_]))) + self.shift_
        return 1 / (1 + np.exp(-z))


class M2HGB(_Base):
    name = "M2 gradient boosting"

    def _fit(self, X, y):
        self.m_ = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, min_samples_leaf=30, max_iter=200, early_stopping=False,
                                                 random_state=0, monotonic_cst=monotone(self.feats_)).fit(X, y)

    def proba(self, te, t):
        return self.m_.predict_proba(te[self.feats_])[:, 1]


class M3KNN(_Base):
    name = "M3 look-alike years (kNN)"

    def _fit(self, X, y):
        self.imp_ = SimpleImputer(strategy="median", add_indicator=False).fit(X)
        self.sc_ = StandardScaler().fit(self.imp_.transform(X))
        self.y_ = y
        self.nn_ = NearestNeighbors(n_neighbors=min(25, len(y))).fit(self.sc_.transform(self.imp_.transform(X)))
        self.Xtr_ = X

    def proba(self, te, t):
        idx = self.nn_.kneighbors(self.sc_.transform(self.imp_.transform(te[self.feats_])), return_distance=False)
        return self.y_[idx].mean(axis=1)


BASELINES = {"Persistence": Persistence, "Climatology": Climatology, "Most common level": MostCommon}
MODELS = {"M1": M1Logit, "M2": M2HGB, "M3": M3KNN}
SIMPLEST_FIRST = ["M1", "M3", "M2"]
