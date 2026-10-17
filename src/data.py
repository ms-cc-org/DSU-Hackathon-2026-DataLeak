"""Project-specific reads and filters over the supplied master dataset."""

import pandas as pd

from src.data_loader import load_master as loadMaster


def loadIowaCornHistory() -> pd.DataFrame:
    """Return all Iowa corn county-years, preserving missing-yield records."""
    masterData = loadMaster()
    requiredColumns = {"fips", "state_alpha", "crop", "year", "yield_status", "yield_per_acre"}
    missingColumns = requiredColumns.difference(masterData.columns)
    if missingColumns:
        raise ValueError(f"Master data is missing columns: {sorted(missingColumns)}")

    cornHistory = masterData.loc[
        (masterData["state_alpha"] == "IA") & (masterData["crop"] == "CORN")
    ].copy()
    if cornHistory.empty:
        raise ValueError("No Iowa corn records were found in the master data")

    cornHistory["fips"] = cornHistory["fips"].astype("string").str.zfill(5)
    return cornHistory.sort_values(["year", "fips"]).reset_index(drop=True)
