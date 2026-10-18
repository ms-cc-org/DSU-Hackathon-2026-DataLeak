"""EXPLORATORY, post-test: does training on more recent years help on the same later years? Not part of the official result.

    python app/model/exploratory_more_years.py

Reads official saved outputs (read-only) and retrains frozen-setting models (results/params.json, no retuning, all uncalibrated) on 2000-2021 and 2000-2023.
Writes only results/exploratory_more_years.md.
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from baselines import B0                                            # noqa: E402
from data import KEY, CARRY, RESULTS, T1, load_usable              # noqa: E402
from evaluate import _top, county_year, make_model                  # noqa: E402

MODELS = ["D", "A", "B", "C", "B0", "B1", "B2a", "B4", "Z0"]
NAMES = {"D": "D Tweedie GLM (headline)", "A": "A hurdle", "B": "B boosting", "C": "C look-alikes", "B0": "B0 state x crop mean", "B1": "B1 drought-bin average",
         "B2a": "B2a USDA binary trigger", "B4": "B4 liability x D2+ last map", "Z0": "Z0 predict zero"}
params = json.load(open(RESULTS / "params.json"))


def fit_predict_t1(train, test, names):
    out = test[KEY + CARRY].reset_index(drop=True).copy()
    for n in names:
        m = (B0() if n == "B0" else make_model(n, params)).fit(train, T1)
        out[f"t1_{n}"] = m.predict(test)
    return out


def official(all_rows):
    """Saved official predictions for 2016-2025 (A and B4 un-calibrated again with the saved nested k, so every column is uncalibrated); B0 was not part of the official run -> fitted on 2000-2015."""
    p = pd.read_csv(RESULTS / "test_predictions.csv", dtype={"fips": str})
    k = pd.read_csv(RESULTS / "test_nested_k.csv")
    for m in ("A", "B4"):
        km = k[(k.model == m) & (k.target == "t1")].set_index("year").k
        p[f"t1_{m}"] = p[f"t1_{m}"] / p.year.map(km)
    train = all_rows[all_rows.year <= 2015]
    p["t1_B0"] = B0().fit(train, T1).predict(p)
    return p


def table_metrics(frame, years, state):
    f = frame[frame.year.isin(years) & (frame.state_alpha == state)]
    res = {}
    for m in MODELS:
        cy = county_year(f, f"t1_{m}", "t1")
        miss, caps, act = [], [], []
        for y, g in cy.groupby("year"):
            a = g.actual.sum()
            miss.append(abs(g.pred.sum() - a))
            act.append(a)
            caps.append(_top(g, "pred").actual.sum() / a if a > 0 else np.nan)
        res[m] = {"avg_miss": np.mean(miss), "pct_miss": np.sum(miss) / np.sum(act), "capture": np.nanmean(caps)}
    return res


def fmt_table(runs, years, title):
    """runs: {label: frame}. Rows = state x model; columns = per run: avg $ miss per state-year ($M), total miss / total actual (%), top-20 capture."""
    labels = list(runs)
    head = "| State | Model | " + " | ".join(f"{l}: avg miss/state-yr | {l}: miss ÷ actual | {l}: top-20 capture" for l in labels) + " |"
    lines = [f"### {title}", "", head, "|---|---|" + "---|" * (3 * len(labels))]
    for st, stname in [("IA", "Iowa"), ("NE", "Nebraska")]:
        mets = {l: table_metrics(runs[l], years, st) for l in labels}
        for m in MODELS:
            cells = []
            for l in labels:
                r = mets[l][m]
                cells += [f"${r['avg_miss'] / 1e6:,.1f}M", f"{r['pct_miss'] * 100:,.0f}%", f"{r['capture'] * 100:.1f}%"]
            bold = "**" if m in ("D", "B2a") else ""
            lines.append(f"| {stname} | {bold}{NAMES[m]}{bold} | " + " | ".join(f"{bold}{c}{bold}" for c in cells) + " |")
    return "\n".join(lines), {l: {st: table_metrics(runs[l], years, st) for st in ("IA", "NE")} for l in labels}


def main():
    all_rows = load_usable("training", "validation", "testing", allow_test=True)      # post-test exploratory use of the 2016-2025 labels, as requested
    print("rows by year range:", all_rows.year.min(), all_rows.year.max(), len(all_rows))
    off = official(all_rows)
    mid = fit_predict_t1(all_rows[all_rows.year <= 2021], all_rows[all_rows.year.between(2022, 2025)], MODELS)
    you = fit_predict_t1(all_rows[all_rows.year <= 2023], all_rows[all_rows.year.between(2024, 2025)], MODELS)
    t1, r1 = fmt_table({"Official (2000-2015)": off, "Middle (2000-2021)": mid}, [2022, 2023, 2024, 2025], "Table 1. Test years 2022-2025: Official vs Middle")
    t2, r2 = fmt_table({"Official (2000-2015)": off, "Middle (2000-2021)": mid, "Yours (2000-2023)": you}, [2024, 2025], "Table 2. Test years 2024-2025: Official vs Middle vs Yours")
    drought = ", ".join(sorted(f"{s} {y}" for s, y in [("NE", 2022), ("IA", 2023), ("NE", 2023)]))

    def d_vs_b2a(res, label, st):
        d, b = res[label][st]["D"], res[label][st]["B2a"]
        return d, b
    text = f"""# EXPLORATORY – post-test. These years were already seen in the official 2016–2025 test; this is not an independent test and doesn't replace the official result.

**Question.** Does training on more recent years improve predictions on the same later years? Nothing in the official results files, models, settings or features was changed.

**Runs.** *Official*: models trained on 2000-2015; their saved official predictions for 2022-2025 (and the 2024-2025 subset), no retraining. *Middle*: retrained on 2000-2021, predict 2022-2025. *Yours*: retrained on 2000-2023, predict 2024-2025.
Models D (alpha 0.001), A, B, C with the frozen `results/params.json` settings, no retuning; baselines B0, B1, B2a, B4, Z0. Preprocessing is the existing fold-safe pipeline (normals and irrigation averages from earlier years in the data build; imputers, scalers, bins, look-alike pools fitted on the training years of each run).
**All columns are uncalibrated** so the runs are comparable: the official nested calibration (applied to A and B4 only) was divided back out of the saved Official predictions for those two models; D, B, C, B1, B2a and Z0 were uncalibrated in the official run already.
B0 was not part of the official run, so its Official column is B0 fitted on 2000-2015 here.

**Metrics (the only two reported).** *Statewide budget error*: for each state, the average over its state-years of |predicted statewide payout − actual|, in $M, and the total absolute miss ÷ total actual payouts (%). *Top-20 capture*: share of actual drought payouts landing in the 20 counties (crops summed) with the highest predicted payout,
averaged over the state-years, as in the official report. Rows for D and B2a are in bold.

**Read with care.** Each Iowa or Nebraska cell rests on only 4 state-years (2022-2025) or 2 (2024-2025), so differences between runs are mostly noise; the drought state-years in 2022-2025 are {drought}, and 2024-2025 has none. The Middle and Yours runs train on years that include
the test-window neighbours (2016-2023), which the official run never saw.

{t1}

{t2}
"""
    return text, r1, r2


if __name__ == "__main__":
    text, r1, r2 = main()
    (RESULTS / "exploratory_more_years.md").write_text(text)
    print("wrote", RESULTS / "exploratory_more_years.md")
