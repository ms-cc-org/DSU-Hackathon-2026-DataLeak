"""One-time check of the planning band on the 2016-2025 state-years (exploratory, after the official test; DECISIONS_extra.md Entry 9).

Runs AFTER ratio_band.py. Reads results/ratio_band.json (never writes it), the saved test_predictions.csv and
test_budget_range.csv from the one official run, and writes results/ratio_band_eval.md. No model is fitted.

    python app/model/ratio_band_eval.py
"""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
DROUGHT = {("IA", 2023), ("NE", 2022), ("NE", 2023)}
TAG = "exploratory, after the official test"


def m(x):
    return f"${x / 1e6:,.1f}M"


def main():
    band = json.loads((RES / "ratio_band.json").read_text())
    q05, q95 = band["q05"], band["q95"]
    t = pd.read_csv(RES / "test_predictions.csv", dtype={"fips": str})
    t = t.assign(d_usd=t["t1_D"] * t["liability"])
    sy = t.groupby(["state_alpha", "year"]).agg(actual=("drought_indemnity", "sum"), D=("d_usd", "sum")).reset_index()
    rng = pd.read_csv(RES / "test_budget_range.csv").rename(columns={"state": "state_alpha"})
    sy = sy.merge(rng[["state_alpha", "year", "budget_low", "budget_high"]], on=["state_alpha", "year"], validate="1:1")
    assert len(sy) == 20 and sy["year"].between(2016, 2025).all()
    sy["klass"] = ["drought" if (s, y) in DROUGHT else "quiet" for s, y in zip(sy.state_alpha, sy.year)]
    sy["low"], sy["high"] = sy["D"] * q05, sy["D"] * q95
    sy["inside"] = (sy["actual"] >= sy["low"]) & (sy["actual"] <= sy["high"])
    sy["above"] = sy["actual"] > sy["high"]
    sy["below"] = sy["actual"] < sy["low"]
    sy["inside_C"] = (sy["actual"] >= sy["budget_low"]) & (sy["actual"] <= sy["budget_high"])
    sy["le2D"] = sy["actual"] <= 2 * sy["D"]
    sy["w_band"] = sy["high"] - sy["low"]
    sy["w_C"] = sy["budget_high"] - sy["budget_low"]

    def cov(df, col):
        return f"{int(df[col].sum())} of {len(df)}"

    groups = [("All state-years", sy), ("Drought state-years (IA 2023, NE 2022, NE 2023)", sy[sy.klass == "drought"]),
              ("Quiet state-years", sy[sy.klass == "quiet"])]
    L = [f"# Planning band for statewide X on the 2016-2025 state-years ({TAG})", "",
         f"**{TAG}.** The band was proposed after the official test (DECISIONS_extra.md Entry 9) and is a one-time check, not a selection step: D and its test report are unchanged. "
         f"Band = D's statewide estimate x [{q05:.3f}, {q95:.3f}] (5th and 95th percentile of actual / D over the out-of-sample state-years 2006-2015; `results/ratio_band.json`). "
         "'Existing C range' = the saved widened historical scenario range in `results/test_budget_range.csv`. "
         "Coverage uses the unclipped state-year dollars; the 20 test state-years are the same ones as in the official report.", "",
         f"## Coverage and width ({TAG})", "",
         "| State-years | n | Actual inside planning band | Actual inside C range | Mean width, band | Mean width, C | Median width, band | Median width, C |",
         "|---|---|---|---|---|---|---|---|"]
    for name, g in groups:
        L.append(f"| {name} | {len(g)} | {cov(g, 'inside')} | {cov(g, 'inside_C')} | {m(g.w_band.mean())} | {m(g.w_C.mean())} | {m(g.w_band.median())} | {m(g.w_C.median())} |")
    L += ["", f"## Misses and the 2 x D rule of thumb ({TAG})", "",
          "| State-years | n | Actual above the top of the band | Actual below the bottom | Actual <= 2 x D |", "|---|---|---|---|---|"]
    for name, g in groups:
        L.append(f"| {name} | {len(g)} | {cov(g, 'above')} | {cov(g, 'below')} | {cov(g, 'le2D')} |")
    above = sy[sy.above]
    L += ["", f"Years above the top of the band: " + (", ".join(f"{r.state_alpha} {r.year} (actual {m(r.actual)} vs top {m(r.high)}, D {m(r.D)})" for r in above.itertuples()) or "none") + ".", "",
          f"## Per state-year ({TAG})", "",
          "| State-year | Class | Actual | D | Band low | Band high | Inside band | C low | C high | Inside C |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in sy.sort_values(["klass", "state_alpha", "year"], ascending=[False, True, True]).itertuples():
        L.append(f"| {r.state_alpha} {r.year} | {r.klass} | {m(r.actual)} | {m(r.D)} | {m(r.low)} | {m(r.high)} | {'yes' if r.inside else 'NO'} | {m(r.budget_low)} | {m(r.budget_high)} | {'yes' if r.inside_C else 'NO'} |")
    nd, nq = (sy.klass == "drought").sum(), (sy.klass == "quiet").sum()
    L += ["", "## Reading the numbers", "",
          f"- The band contains the actual payout in {cov(sy, 'inside')} state-years ({cov(sy[sy.klass == 'drought'], 'inside')} drought, {cov(sy[sy.klass == 'quiet'], 'inside')} quiet); the existing C range contains it in {cov(sy, 'inside_C')}.",
          f"- Mean width {m(sy.w_band.mean())} vs {m(sy.w_C.mean())} for the C range; median {m(sy.w_band.median())} vs {m(sy.w_C.median())}.",
          f"- Actual payout was at most 2 x D in {cov(sy, 'le2D')} state-years.", ""]
    (RES / "ratio_band_eval.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
