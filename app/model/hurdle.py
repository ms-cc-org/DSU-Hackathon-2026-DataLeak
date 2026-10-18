"""Strategy A: two-part ("hurdle") model.

1. P(cost > 0): LogisticRegression, balanced class weights (intercept shifted back to the real base rate
   afterwards so the probability is usable as a probability; the ranking / AUC is unchanged).
2. E[share | cost > 0]: linear model on log(share) using only rows with share > 0, plus two interactions
   (d2_weeks_50pct x irr_share_train_mean, d2_weeks_50pct x aws_100cm_mm). A tiny ridge penalty (alpha=1 on
   standardised features, ~OLS at this sample size) keeps the collinear drought columns stable.
3. Expected share = P x E[share | cost > 0] x smearing factor (Duan, weighted mean of exp(residual)).
Scaler / imputer are fitted on the training rows passed to fit() only.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge

from data import FEATURES, Preprocessor, norm_weights, y_train

INTERACTIONS = [("d2_weeks_50pct", "irr_share_train_mean"), ("d2_weeks_50pct", "aws_100cm_mm")]


class Hurdle:
    name = "A"

    def __init__(self, C=1.0, ridge_alpha=1.0):
        self.C, self.ridge_alpha = C, ridge_alpha

    def _design(self, df, interactions):
        x = self.pre_.transform(df)
        if interactions:
            for a, b in INTERACTIONS:
                x[f"{a} x {b}"] = x[a] * x[b]
        return x

    def fit(self, train, target):
        self.pre_ = Preprocessor(FEATURES).fit(train)
        y = y_train(train, target)
        w = norm_weights(train)
        pos = y > 0
        # part 1
        x1 = self._design(train, False)
        self.cols1_ = list(x1.columns)
        if pos.all() or (~pos).all():
            self.logit_ = None
            self.const_p_ = float(pos.all())
        else:
            self.logit_ = LogisticRegression(C=self.C, class_weight="balanced", max_iter=5000)
            self.logit_.fit(x1, pos, sample_weight=w)
            prior = np.average(pos, weights=w)
            self.shift_ = np.log(prior / (1 - prior))        # balanced weights imply a 50% prior
        # part 2
        x2 = self._design(train[pos], True)
        self.cols2_ = list(x2.columns)
        self.reg_ = Ridge(alpha=self.ridge_alpha).fit(x2, np.log(y[pos]), sample_weight=w[pos])
        resid = np.log(y[pos]) - self.reg_.predict(x2)
        self.smear_ = float(np.average(np.exp(resid), weights=w[pos]))
        return self

    def p_any(self, df):
        if self.logit_ is None:
            return np.full(len(df), self.const_p_)
        z = self.logit_.decision_function(self._design(df, False)) + self.shift_
        return 1 / (1 + np.exp(-z))

    def conditional(self, df):
        return np.exp(self.reg_.predict(self._design(df, True))) * self.smear_

    def predict(self, df):
        return np.clip(self.p_any(df) * self.conditional(df), 0, 1)

    def score(self, df):
        """Ranking score for 'will drought cost anything?' (part 1)."""
        return self.p_any(df)

    def coefficients(self):
        """Standardised coefficients: the 'why' for the dashboard."""
        c1 = pd.Series(self.logit_.coef_[0], index=self.cols1_, name="p_any_logit") if self.logit_ is not None else None
        c2 = pd.Series(self.reg_.coef_, index=self.cols2_, name="log_share_if_cost")
        return pd.concat([c1, c2], axis=1).rename_axis("feature").reset_index()
