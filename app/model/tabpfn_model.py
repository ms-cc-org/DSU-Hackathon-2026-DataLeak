"""Strategy G (optional): TabPFN v2 regressor, a pretrained tabular foundation model.

Built with PriorLabs-TabPFN. Only the TabPFN-v2 weights are used (Prior Labs License 1.1 = Apache 2.0 + an attribution clause);
the newer v2.5 / v2.6 weights are non-commercial only and are NOT used. The weights download from Hugging Face needs no login.
TabPFNRegressor.fit() takes no sample weights, so liability weighting is NOT applied (unlike A, B, C, D); it also needs no scaling
or imputation (it handles NaN itself). Installed only if `pip install tabpfn` was run; evaluate.py skips G otherwise.
"""
import importlib.util

import numpy as np

from data import FEATURES, y_train

AVAILABLE = importlib.util.find_spec("tabpfn") is not None


def _device():
    import torch
    if torch.cuda.is_available():
        return "cuda"
    return "mps" if torch.backends.mps.is_available() else "cpu"


class TabPFNModel:
    name = "G"

    def __init__(self, n_estimators=8, seed=0, device=None):
        self.n_estimators, self.seed, self.device = n_estimators, seed, device

    def fit(self, train, target):
        from tabpfn import TabPFNRegressor
        from tabpfn.constants import ModelVersion
        self.model_ = TabPFNRegressor.create_default_for_version(
            ModelVersion.V2, device=self.device or _device(), random_state=self.seed, n_estimators=self.n_estimators,
            ignore_pretraining_limits=True)             # lets it run on CPU with > 1000 rows (slow there)
        self.model_.fit(train[FEATURES].astype(float), y_train(train, target))
        return self

    def predict(self, df):
        return np.clip(self.model_.predict(df[FEATURES].astype(float)), 0, 1)

    score = predict
