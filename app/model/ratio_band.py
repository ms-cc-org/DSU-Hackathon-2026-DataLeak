"""Planning band for statewide X (build time). Exploratory, proposed after the official test (DECISIONS.md Entry 9).

Band = D's statewide estimate x [q05, q95], where q05 / q95 are the 5th / 95th percentile of actual / D over the
out-of-sample state-years 2006-2015 in results/oos_predictions.csv (nothing else is read here: no test file, no testing/ folder).
It never changes D, and it applies to statewide X only (not Y, Z or single counties).

For real future use, re-run this each year after the final RMA claims are in, using only out-of-sample years before the
forecast year (edit LAST_YEAR / FIRST_YEAR and the expected state-year count together, and log the change in DECISIONS.md).

    python app/model/ratio_band.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "results" / "oos_predictions.csv"
OUT = HERE / "results" / "ratio_band.json"
FIRST_YEAR, LAST_YEAR = 2006, 2015
N_STATE_YEARS = 20
FLOOR = 100_000.0
LABEL = ("planning range from D's past misses (5th-95th percentile, 2006-2015); "
         "evaluated after the official test")


def state_year_ratios(df):
    """Per state-year actual, D and r = log(actual / D); both dollar totals clipped to >= FLOOR."""
    years = set(int(y) for y in df["year"].unique())
    assert years and min(years) >= FIRST_YEAR and max(years) <= LAST_YEAR, \
        f"input years {sorted(years)} are outside {FIRST_YEAR}..{LAST_YEAR}; refusing to build the band"
    g = df.assign(d_usd=df["t1_D"] * df["liability"]).groupby(["state_alpha", "year"])
    sy = pd.DataFrame({"actual": g["drought_indemnity"].sum(), "D": g["d_usd"].sum()}).reset_index()
    assert len(sy) == N_STATE_YEARS, f"expected {N_STATE_YEARS} state-years, found {len(sy)}"
    sy["actual"] = sy["actual"].clip(lower=FLOOR)
    sy["D"] = sy["D"].clip(lower=FLOOR)
    sy["r"] = np.log(sy["actual"] / sy["D"])
    return sy


def compute_band(df):
    sy = state_year_ratios(df)
    q05, q95 = (float(np.exp(np.percentile(sy["r"], p))) for p in (5, 95))
    return {"q05": q05, "q95": q95, "source_file": "results/oos_predictions.csv",
            "source_years": list(range(FIRST_YEAR, LAST_YEAR + 1)), "n_state_years": int(len(sy)),
            "applies_to": "statewide X only", "label": LABEL}


def main():
    df = pd.read_csv(SOURCE, dtype={"fips": str})
    band = compute_band(df)
    OUT.write_text(json.dumps(band, indent=2) + "\n")
    print(json.dumps(band, indent=2))


if __name__ == "__main__":
    main()
