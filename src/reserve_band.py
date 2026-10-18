"""Planning band for statewide X (exploratory, after the official test; app/model/DECISIONS.md Entry 9).

The constants come from app/model/results/ratio_band.json, built by `python app/model/ratio_band.py` from D's
out-of-sample state-years 2006-2015. The band applies to statewide X only (never Y, Z or a single county) and never changes D.
"""

import json
from functools import lru_cache
from pathlib import Path

_BAND_PATH = Path(__file__).resolve().parents[1] / "app" / "model" / "results" / "ratio_band.json"


@lru_cache(maxsize=1)
def load_ratio_band():
    """Planning-band constants for statewide X (q05, q95, label), read once from ratio_band.json."""
    if not _BAND_PATH.exists():
        raise FileNotFoundError(f"{_BAND_PATH} is missing: run python app/model/ratio_band.py")
    return json.loads(_BAND_PATH.read_text())


def reserve_band_x_usd(plan_usd):
    """The `reserve_band_x_usd` entry for one state's statewide X, to be called AFTER acres_scale x price_scale are applied."""
    band = load_ratio_band()
    return {"plan_usd": plan_usd, "low_usd": plan_usd * band["q05"], "high_usd": plan_usd * band["q95"],
            "label": band["label"], "source_years": "2006-2015"}
