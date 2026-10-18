"""Strategy C: historical look-alikes (k nearest training county-years, same crop).

Features are standardised with training statistics; drought features get a higher weight. The
prediction is the liability-weighted mean share of the k most similar training county-years. The spread
of the neighbours gives a range, and the nearest neighbours give a plain-English explanation.
"""
import numpy as np
from sklearn.neighbors import NearestNeighbors

from data import DROUGHT, NUMERIC, Preprocessor, y_train


def _wquantile(y, w, q):
    """Row-wise weighted quantile of y (n, k) with weights w (n, k)."""
    order = np.argsort(y, axis=1)
    ys, ws = np.take_along_axis(y, order, 1), np.take_along_axis(w, order, 1)
    cum = np.cumsum(ws, axis=1) / ws.sum(axis=1, keepdims=True)
    idx = (cum < q - 1e-12).sum(axis=1).clip(max=y.shape[1] - 1)
    return ys[np.arange(len(y)), idx]


class Analog:
    name = "C"

    def __init__(self, k=25, drought_weight=2.0):
        self.k, self.drought_weight = k, drought_weight

    def _z(self, df):
        z = self.pre_.transform(df)[NUMERIC].to_numpy()
        return z * self.fw_

    def fit(self, train, target):
        self.pre_ = Preprocessor(NUMERIC).fit(train)
        self.fw_ = np.array([self.drought_weight if c in DROUGHT else 1.0 for c in NUMERIC])
        self.pool_ = {}
        for crop, g in train.groupby("crop"):
            g = g.reset_index(drop=True)
            k = min(self.k, len(g))
            nn = NearestNeighbors(n_neighbors=k, algorithm="brute").fit(self._z(g))
            self.pool_[crop] = (nn, y_train(g, target), g.liability.to_numpy(float),
                                g[["fips", "county_name", "state_alpha", "year"]].reset_index(drop=True))
        return self

    def _neighbors(self, df):
        """-> {crop: (row positions in df, neighbour index array)}"""
        out = {}
        for crop, nn_pool in self.pool_.items():
            pos = np.flatnonzero((df.crop == crop).to_numpy())
            if len(pos):
                out[crop] = (pos, nn_pool[0].kneighbors(self._z(df.iloc[pos]), return_distance=False))
        return out

    def _apply(self, df, fn):
        res = np.full(len(df), np.nan)
        for crop, (pos, idx) in self._neighbors(df).items():
            _, y, w, _ = self.pool_[crop]
            res[pos] = fn(y[idx], w[idx])
        return res

    def predict(self, df):
        return self._apply(df, lambda y, w: (y * w).sum(axis=1) / w.sum(axis=1))

    score = predict

    def quantiles(self, df, lo=0.1, hi=0.9):
        """Range from the neighbours' spread (liability-weighted quantiles of their shares)."""
        return (self._apply(df, lambda y, w: _wquantile(y, w, lo)),
                self._apply(df, lambda y, w: _wquantile(y, w, hi)))

    def explain(self, df, n=3):
        """Plain-English look-alikes per row, nearest first."""
        text = [""] * len(df)
        for crop, (pos, idx) in self._neighbors(df).items():
            meta = self.pool_[crop][3]
            for p, row in zip(pos, idx):
                text[p] = "looks like " + ", ".join(
                    f"{meta.county_name[j].replace(' County', '')}, {meta.state_alpha[j]} {meta.year[j]}" for j in row[:n])
        return text
