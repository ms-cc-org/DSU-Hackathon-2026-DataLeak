"""Report the frozen official-test predictions for Iowa corn only."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

resultDir = Path(__file__).resolve().parent / "results"
modelLabels = {"D": "D Tweedie", "B2a": "B2a USDA trigger", "B2b": "B2b tiered trigger"}


def calculateYearRows(predictions: pd.DataFrame) -> pd.DataFrame:
    """Compute dollar error and top-20 actual payout capture by year and model."""
    iowaCorn = predictions.loc[predictions["state_alpha"].eq("IA") &
                                predictions["crop"].eq("CORN")].copy()
    if iowaCorn.empty:
        raise ValueError("Official test predictions contain no Iowa corn rows")
    rows = []
    for year, yearRows in iowaCorn.groupby("year"):
        actualDollars = yearRows["t1_actual"] * yearRows["liability"]
        actualTotal = float(actualDollars.sum())
        for modelName, displayName in modelLabels.items():
            predictedDollars = yearRows[f"t1_{modelName}"] * yearRows["liability"]
            ranking = pd.DataFrame({"fips": yearRows["fips"], "predicted": predictedDollars,
                                    "actual": actualDollars})
            selected = ranking.sort_values(["predicted", "fips"], ascending=[False, True]).head(20)
            predictedTotal = float(predictedDollars.sum())
            rows.append({"year": int(year), "model": displayName, "counties": len(yearRows),
                         "actual_usd": actualTotal, "predicted_usd": predictedTotal,
                         "absolute_error_usd": abs(predictedTotal - actualTotal),
                         "signed_error_usd": predictedTotal - actualTotal,
                         "top20_capture": float(selected["actual"].sum() / actualTotal)
                         if actualTotal > 0 else float("nan")})
    return pd.DataFrame(rows).sort_values(["year", "model"]).reset_index(drop=True)


def renderReport(metrics: pd.DataFrame) -> str:
    """Render one auditable Iowa-corn-only comparison from saved predictions."""
    lines = [
        "# Iowa corn official test slice (2016–2025)",
        "",
        "Source: `results/test_predictions.csv` only. These are existing official-test "
        "predictions; no model was retrained or selected using this slice. "
        "X means estimated drought insurance payouts (predicted T1 share × insured liability).",
        "",
        "Each year contains Iowa corn county-crop rows only. Dollar error is the absolute "
        "difference between statewide predicted and observed drought indemnity. "
        "Top-20 capture is the share of actual Iowa corn drought indemnity in the 20 "
        "counties with the highest predicted dollars; ties use FIPS ascending. "
        "Observed payout can be zero, in which case capture is undefined.",
        "",
        "| Year | Model | Counties | Actual X | Predicted X | Statewide $ error | Top-20 capture |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in metrics.itertuples():
        capture = f"{row.top20_capture:.1%}" if pd.notna(row.top20_capture) else "—"
        lines.append(f"| {row.year} | {row.model} | {row.counties} | "
                     f"${row.actual_usd:,.0f} | ${row.predicted_usd:,.0f} | "
                     f"${row.absolute_error_usd:,.0f} | {capture} |")
    lines += ["", "## Worst statewide miss by model", ""]
    for displayName in modelLabels.values():
        modelRows = metrics.loc[metrics["model"].eq(displayName)]
        worstRow = modelRows.loc[modelRows["absolute_error_usd"].idxmax()]
        direction = "over" if worstRow["signed_error_usd"] > 0 else "under"
        lines.append(f"- **{displayName}:** {int(worstRow['year'])}, "
                     f"${worstRow['absolute_error_usd']:,.0f} {direction} observed X.")
    lines += ["", "The selected headline D was chosen from pooled model evaluation, "
              "not from this Iowa-corn-only slice. This slice should be reviewed before "
              "claiming Iowa corn performance in the app.", ""]
    return "\n".join(lines)


def main() -> None:
    predictionPath = resultDir / "test_predictions.csv"
    if not predictionPath.exists():
        raise FileNotFoundError(predictionPath)
    predictions = pd.read_csv(predictionPath, dtype={"fips": str})
    requiredColumns = {"fips", "crop", "state_alpha", "year", "liability", "t1_actual",
                       "t1_D", "t1_B2a", "t1_B2b"}
    missingColumns = requiredColumns.difference(predictions.columns)
    if missingColumns:
        raise ValueError(f"Missing official test columns: {sorted(missingColumns)}")
    report = renderReport(calculateYearRows(predictions))
    outputPath = resultDir / "iowa_corn_test_slice.md"
    outputPath.write_text(report)
    print(outputPath)


if __name__ == "__main__":
    main()
