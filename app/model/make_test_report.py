"""Presentation of the ONE official test run (2016-2025), built only from the saved outputs of that run; no model is fitted and the held-out data folder is not read.

    python app/model/make_test_report.py

Reads the original t1_*/t2_* results/test_predictions.csv, test_budget_range.csv and test_metrics.csv.
Writes only results/test_state_years_extra.csv, results/test_report_extra.png and results/test_report_extra.md.
The frozen official outputs and main's test_state_years.csv are never written.
It asserts that statewide figures recomputed from the predictions equal the saved test_metrics.csv, so the numbers in the report cannot differ from the official run.
"""
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from data import RESULTS, add_year_class                                   # noqa: E402
from evaluate import LABEL                                                  # noqa: E402

ORDER = ["D", "A", "B", "C", "Z0", "B1", "B2a", "B2b", "B3", "B4"]
SHOWN = ["D", "B2a", "B2b", "B1", "B3"]
EXTRA_HEADING = ("Added after the official test. Same frozen predictions, presentation only. "
                 "Nothing here was used to choose or change a model.")
INK, BLUE, ORANGE, SURFACE, GRID = "#0b0b0b", "#2a78d6", "#eb6834", "#fcfcfb", "#e4e3df"


def state_years(p, rng):
    cls = add_year_class(p).drop_duplicates(["state_alpha", "year"]).set_index(["state_alpha", "year"]).sy_class
    g = p.assign(actual=p.drought_indemnity.fillna(0), **{f"u_{m}": p[f"t1_{m}"] * p.liability for m in ORDER}).groupby(["state_alpha", "year"])
    sy = g[["actual"] + [f"u_{m}" for m in ORDER]].sum().reset_index()
    sy.insert(2, "type", [cls[(s, y)] for s, y in zip(sy.state_alpha, sy.year)])
    for m in ORDER:
        sy[f"err_{m}"] = sy[f"u_{m}"] - sy.actual
    r = rng.rename(columns={"state": "state_alpha"})[["state_alpha", "year", "budget_low", "budget_high", "inside"]]
    sy = sy.merge(r, on=["state_alpha", "year"]).rename(columns={"actual": "actual_usd", "budget_low": "D_scenario_range_low_usd", "budget_high": "D_scenario_range_high_usd",
                                                                "inside": "actual_inside_D_range"})
    sy = sy.rename(columns={f"u_{m}": f"pred_usd_{m}" for m in ORDER})
    return sy


def verify(sy, metrics):
    for m in ORDER:
        want = metrics[(metrics.target == "t1") & (metrics.group == "all") & (metrics.model == m)].stat_abs_err.iloc[0]
        got = sy[f"err_{m}"].abs().mean()
        assert abs(want - got) < 1.0, (m, want, got)
    return True


def scoreboard(sy):
    rows = []
    for other in ["B2a", "B2b", "B1"]:
        row = {"comparison": f"D closer to actual than {LABEL[other]}"}
        for name, mask in [("all state-years", sy.type.notna()), ("drought state-years", sy.type == "drought"), ("quiet state-years", sy.type == "quiet")]:
            s = sy[mask]
            wins = int((s.err_D.abs() < s[f"err_{other}"].abs()).sum())
            ties = int((s.err_D.abs() == s[f"err_{other}"].abs()).sum())
            row[f"{name} ({len(s)})"] = f"{wins} of {len(s)}" + (f" ({ties} ties)" if ties else "")
        rows.append(row)
    return pd.DataFrame(rows)


def per_state_year_md(sy):
    lines = ["| state | year | type | actual $M | " + " | ".join(LABEL[m] + " $M" for m in SHOWN) + " |", "|---|---|---|---|" + "---|" * len(SHOWN)]
    for r in sy.sort_values(["state_alpha", "year"]).itertuples(index=False):
        d = r._asdict()
        best = min(SHOWN, key=lambda m: abs(d[f"err_{m}"]))
        cells = [(f"**{d[f'pred_usd_{m}'] / 1e6:,.1f}**" if m == best else f"{d[f'pred_usd_{m}'] / 1e6:,.1f}") for m in SHOWN]
        lines.append(f"| {d['state_alpha']} | {d['year']} | {d['type']} | {d['actual_usd'] / 1e6:,.1f} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def chart(sy, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4), sharey=True, facecolor=SURFACE)
    for ax, (st, name) in zip(axes, [("IA", "Iowa"), ("NE", "Nebraska")]):
        s = sy[sy.state_alpha == st].sort_values("year")
        ax.set_facecolor(SURFACE)
        for y in s[s.type == "drought"].year:
            ax.axvspan(y - 0.42, y + 0.42, color="#d9d8d3", alpha=0.55, lw=0)
        ax.plot(s.year, s.actual_usd / 1e6, color=INK, lw=2.4, marker="o", ms=6, mec=SURFACE, mew=1.5, label="Actual", zorder=4)
        ax.plot(s.year, s.pred_usd_D / 1e6, color=BLUE, lw=2, marker="o", ms=6, mec=SURFACE, mew=1.5, label="D Tweedie GLM", zorder=3)
        ax.plot(s.year, s.pred_usd_B2a / 1e6, color=ORANGE, lw=2, marker="s", ms=6, mec=SURFACE, mew=1.5, label="B2a USDA binary trigger", zorder=2)
        ax.set_title(name, loc="left", fontsize=12, color=INK, fontweight="bold")
        ax.set_xticks(range(2016, 2026))
        ax.tick_params(axis="x", labelsize=9, colors="#52514e", length=0, rotation=45)
        ax.tick_params(axis="y", labelsize=9, colors="#52514e", length=0)
        ax.grid(axis="y", color=GRID, lw=0.8)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.set_xlim(2015.4, 2025.6)
    axes[0].set_ylabel("Statewide drought payout ($M)", color="#52514e", fontsize=10)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=3, frameon=False, fontsize=10, bbox_to_anchor=(0.5, 1.02), labelcolor="#52514e")
    fig.text(0.01, -0.02, "Official test 2016-2025. Grey bands = drought state-years (actual statewide payout >= 3% of insured $). Same y-scale in both panels.", fontsize=8.5, color="#52514e")
    fig.tight_layout(rect=(0, 0.02, 1, 0.96))
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)


def main():
    raw = pd.read_csv(RESULTS / "test_predictions.csv", dtype={"fips": str})
    rng = pd.read_csv(RESULTS / "test_budget_range.csv")
    metrics = pd.read_csv(RESULTS / "test_metrics.csv")
    sy = state_years(raw, rng)
    verify(sy, metrics)
    sy.to_csv(RESULTS / "test_state_years_extra.csv", index=False)
    chart(sy, RESULTS / "test_report_extra.png")

    sb = scoreboard(sy)
    cols = list(sb.columns)
    sb_md = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n" + "\n".join("| " + " | ".join(str(v) for v in r) + " |" for r in sb.itertuples(index=False))
    extras = f"""# {EXTRA_HEADING}

## 2b. Per state-year table: actual vs D, B2a, B2b, B1, B3 ($M; **bold** = closest to actual of the five shown)
{per_state_year_md(sy)}

## 2c. Scoreboard: how often D was closer to the actual statewide payout
Closer = smaller absolute statewide error in that state-year.

{sb_md}

## 2d. Chart: actual vs D vs B2a, statewide payout by year
![Actual vs D vs B2a, statewide drought payout, Iowa and Nebraska 2016-2025](test_report_extra.png)

*Extended presentation added from the saved outputs of the one official run (no model was re-run; see DECISIONS.md Entry 8). Per-row predicted dollars = `t1_<model>` × liability, acres = `t2_<model>` × insured acres, and Z = `z_<model>` in `test_predictions.csv`;
per state-year errors and D's scenario range: `test_state_years_extra.csv`.*
"""
    (RESULTS / "test_report_extra.md").write_text(extras)
    print(sb_md)
    print("verified against test_metrics.csv; wrote only test_state_years_extra.csv, test_report_extra.png, test_report_extra.md")


if __name__ == "__main__":
    main()
