"""Pure allocation rules for one state fund shared across all supplied crops."""

from decimal import Decimal, ROUND_HALF_UP, localcontext
import math

import pandas as pd


def validateEstimates(estimates: pd.DataFrame) -> pd.DataFrame:
    """Validate a single state/year table; missing losses remain unavailable."""
    requiredColumns = {"fips", "county", "state", "crop", "year", "estimatedLossUsd"}
    missingColumns = requiredColumns.difference(estimates.columns)
    if missingColumns:
        raise ValueError(f"Missing allocation columns: {sorted(missingColumns)}")
    table = estimates.copy().reset_index(drop=True)
    identityColumns = ["fips", "county", "state", "crop", "year"]
    if table[identityColumns].isna().any().any():
        raise ValueError("County, crop, state and year identifiers cannot be missing.")
    if not table["fips"].map(lambda value: isinstance(value, str)).all() or not table["fips"].str.fullmatch(r"\d{5}").all():
        raise ValueError("FIPS must be five-character text, preserving leading zeros.")
    if table["state"].nunique() > 1 or table["year"].nunique() > 1:
        raise ValueError("A fund covers exactly one state and scenario year.")
    if table.duplicated(["fips", "crop", "year"]).any():
        raise ValueError("Duplicate county/crop/year rows would double-count losses.")
    if (table.groupby("fips")["county"].nunique() > 1).any():
        raise ValueError("Each FIPS must identify one county.")
    table["estimatedLossUsd"] = pd.to_numeric(table["estimatedLossUsd"], errors="raise").astype(float)
    knownLosses = table["estimatedLossUsd"].dropna()
    if not knownLosses.map(math.isfinite).all() or knownLosses.lt(0).any():
        raise ValueError("Estimated losses must be finite, non-negative dollars or missing.")
    return table


def distributeCents(losses: pd.Series, fundCents: int) -> dict[int, int]:
    """Allocate every cent by largest remainder, with deterministic FIPS/crop ties."""
    if losses.empty or fundCents == 0:
        return {rowIndex: 0 for rowIndex in losses.index}
    # Decimal prevents a binary rounding remainder from dropping or creating money.
    with localcontext() as decimalContext:
        decimalContext.prec = 400
        weights = {rowIndex: Decimal(str(loss)) for rowIndex, loss in losses.items()}
        totalWeight = sum(weights.values())
        exactShares = {rowIndex: fundCents * weight / totalWeight for rowIndex, weight in weights.items()}
        cents = {rowIndex: int(share) for rowIndex, share in exactShares.items()}
        remainder = fundCents - sum(cents.values())
        rankedRows = sorted(cents, key=lambda rowIndex: exactShares[rowIndex] - cents[rowIndex], reverse=True)
        for rowIndex in rankedRows[:remainder]:
            cents[rowIndex] += 1
    return cents


def summarizeGroups(table: pd.DataFrame, groupColumns: list[str]) -> pd.DataFrame:
    """Aggregate known losses and integer allocations without turning missing into zero."""
    grouped = table.groupby(groupColumns, sort=True, dropna=False)
    totals = grouped[["estimatedLossUsd", "allocationCents"]].sum(min_count=1)
    totals["estimatedCropRows"] = grouped["eligible"].sum().astype(int)
    totals["unavailableCropRows"] = grouped.size() - totals["estimatedCropRows"]
    totals["allocationUsd"] = totals["allocationCents"] / 100
    totals["coverage"] = "complete"
    totals.loc[totals["unavailableCropRows"].gt(0), "coverage"] = "partial"
    totals.loc[totals["estimatedCropRows"].eq(0), "coverage"] = "unavailable"
    return totals.reset_index()


def allocateFund(estimates: pd.DataFrame, fundUsd: float) -> dict:
    """Share one fund across positive county/crop losses; return details and rollups.

    No additional drought trigger, minimum award, per-crop budget or loss cap is
    applied. All positive estimates share the fund, even when it exceeds loss.
    Missing estimates receive missing allocations; known zero losses receive $0.
    """
    if not math.isfinite(fundUsd) or fundUsd < 0:
        raise ValueError("The fund must be a finite, non-negative dollar amount.")
    with localcontext() as decimalContext:
        decimalContext.prec = 400
        fundCents = int((Decimal(str(fundUsd)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if fundCents > 2**63 - 1:
        raise ValueError("The fund is too large to represent in integer cents.")
    table = validateEstimates(estimates).sort_values(["fips", "crop"]).reset_index(drop=True)
    table["eligible"] = table["estimatedLossUsd"].notna()
    positiveRows = table["estimatedLossUsd"].gt(0)
    table["allocationCents"] = pd.Series(pd.NA, index=table.index, dtype="Int64")
    table.loc[table["eligible"], "allocationCents"] = 0
    cents = distributeCents(table.loc[positiveRows, "estimatedLossUsd"], fundCents)
    for rowIndex, amount in cents.items():
        table.loc[rowIndex, "allocationCents"] = amount
    totalLossUsd = float(table["estimatedLossUsd"].sum())
    if not math.isfinite(totalLossUsd):
        raise ValueError("The combined estimated loss is too large.")
    table["lossShare"] = table["estimatedLossUsd"] / totalLossUsd if totalLossUsd > 0 else 0.0
    table.loc[~table["eligible"], "lossShare"] = float("nan")
    table["allocationUsd"] = table["allocationCents"] / 100
    table["fundUsd"] = fundCents / 100
    table["allocationRule"] = "proportionalCropValueLoss"
    table["allocationSource"] = "Policy arithmetic; not a model prediction"
    table["allocationReason"] = "No estimated loss; no share of the fund."
    table.loc[positiveRows, "allocationReason"] = "Share of positive estimated crop-value loss across all crops in the state."
    table.loc[~table["eligible"], "allocationReason"] = "Unavailable estimate; excluded from the fund weights."
    allocatedCents = int(table["allocationCents"].sum())
    summary = {
        "fundUsd": fundCents / 100,
        "allocatedUsd": allocatedCents / 100,
        "unallocatedUsd": (fundCents - allocatedCents) / 100,
        "estimatedLossUsd": totalLossUsd if table["eligible"].any() else None,
        "fundingGapUsd": max(0.0, totalLossUsd - fundCents / 100) if table["eligible"].any() else None,
        "fundToLossRatio": fundCents / 100 / totalLossUsd if totalLossUsd > 0 else None,
        "estimatedCropRows": int(table["eligible"].sum()),
        "unavailableCropRows": int((~table["eligible"]).sum()),
        "positiveCropRows": int(positiveRows.sum()),
    }
    return {
        "countyCropTable": table,
        "countyTable": summarizeGroups(table, ["fips", "county", "state", "year"]),
        "cropTable": summarizeGroups(table, ["state", "crop", "year"]),
        "summary": summary,
    }
