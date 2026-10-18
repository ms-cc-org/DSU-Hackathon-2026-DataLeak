"""Strategy B: gradient boosting with Poisson loss (copes with many zeros and a long right tail) and
monotonic constraints so that worse drought can never lower the predicted cost.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import partial_dependence, permutation_importance

from data import FEATURES, norm_weights, y_train

MONOTONE = {+1: ["d2_weeks_50pct", "d3_weeks_50pct", "d2_max_pct", "dsci_mean", "heat35_days"],
            -1: ["precip_ratio_vs_normal", "irr_share_prior_mean", "aws_100cm_mm"]}


def monotone_cst(features):
    return [1 if f in MONOTONE[+1] else -1 if f in MONOTONE[-1] else 0 for f in features]


CST = monotone_cst(FEATURES)


class GBM:
    name = "B"

    def __init__(self, max_iter=200, max_depth=3, learning_rate=0.05, min_samples_leaf=30, seed=0, features=None):
        self.params = dict(max_iter=max_iter, max_depth=max_depth, learning_rate=learning_rate,
                           min_samples_leaf=min_samples_leaf)
        self.seed = seed
        self.features = list(features) if features else list(FEATURES)

    def fit(self, train, target):
        self.model_ = HistGradientBoostingRegressor(loss="poisson", monotonic_cst=monotone_cst(self.features), early_stopping=False,
                                                    random_state=self.seed, **self.params)
        self.model_.fit(train[self.features], y_train(train, target), sample_weight=norm_weights(train))
        return self

    def predict(self, df):
        return np.clip(self.model_.predict(df[self.features]), 0, 1)

    score = predict

    def importance(self, df, target, seed=0):
        """Permutation importance on df (use validation): drop in liability-weighted R^2 when shuffled."""
        r = permutation_importance(self.model_, df[FEATURES], y_train(df, target), sample_weight=norm_weights(df),
                                   n_repeats=10, random_state=seed, scoring="r2")
        return (pd.DataFrame({"feature": FEATURES, "importance": r.importances_mean, "std": r.importances_std})
                .sort_values("importance", ascending=False).reset_index(drop=True))

    def partial_dependence(self, df, features):
        rows = []
        for f in features:
            pd_ = partial_dependence(self.model_, df[FEATURES].astype(float), [f], grid_resolution=20, kind="average",
                                     method="brute")
            rows += [{"feature": f, "value": v, "partial_dependence": p}
                     for v, p in zip(pd_["grid_values"][0], pd_["average"][0])]
        return pd.DataFrame(rows)


class GBMDollars:
    """Side check only (not a candidate model): Poisson boosting on the drought payout in dollars, with `liability` as an
    extra feature instead of share x liability. Same hyper-parameters as B, same monotone constraints (none on liability),
    no sample weights (the dollar target already scales with county size)."""
    name = "BD"
    COLS = FEATURES + ["liability"]

    def __init__(self, max_iter=200, max_depth=4, learning_rate=0.05, min_samples_leaf=30, seed=0):
        self.params = dict(max_iter=max_iter, max_depth=max_depth, learning_rate=learning_rate,
                           min_samples_leaf=min_samples_leaf)
        self.seed = seed

    def fit(self, train):
        self.model_ = HistGradientBoostingRegressor(loss="poisson", monotonic_cst=CST + [0], early_stopping=False,
                                                    random_state=self.seed, **self.params)
        y = np.clip(train.drought_indemnity.to_numpy(float), 0, None) / 1e6      # $M keeps the log link well scaled
        self.model_.fit(train[self.COLS], y)
        return self

    def predict_usd(self, df):
        usd = np.clip(self.model_.predict(df[self.COLS]), 0, None) * 1e6
        return np.minimum(usd, df.liability.to_numpy(float))                    # cannot pay more than is insured
