"""Strategy D: Tweedie generalised linear model (power 1.5, log link) on the payout share.

One model instead of A's two parts: power 1.5 sits between Poisson and gamma, so it copes with the exact zeros and the long right
tail at once. liability is the sample weight; features are standardised with training medians imputed and missing-flag columns
added, all fitted on the training rows passed to fit() only. alpha (L2 penalty) is tuned with walk-forward in evaluate.py.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import TweedieRegressor

from data import FEATURES, Preprocessor, norm_weights, y_train


class Tweedie:
    name = "D"

    def __init__(self, alpha=0.1, power=1.5):
        self.alpha, self.power = alpha, power

    def fit(self, train, target):
        self.pre_ = Preprocessor(FEATURES).fit(train)
        x = self.pre_.transform(train)
        self.cols_ = list(x.columns)
        self.model_ = TweedieRegressor(power=self.power, link="log", alpha=self.alpha, max_iter=5000)
        self.model_.fit(x, y_train(train, target), sample_weight=norm_weights(train))
        return self

    def predict(self, df):
        return np.clip(self.model_.predict(self.pre_.transform(df)), 0, 1)

    score = predict

    def coefficients(self):
        return pd.Series(self.model_.coef_, index=self.cols_, name="log_link_coef").rename_axis("feature").reset_index()
