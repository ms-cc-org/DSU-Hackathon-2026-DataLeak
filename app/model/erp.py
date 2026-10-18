"""B2a / B2b inputs: USDA-style drought triggers computed from the weekly Drought Monitor maps (data/processed/drought).

Only maps dated Apr 1 through Aug 13 of the year are used (maps released by Aug 15). "Consecutive" means maps exactly 7 days apart, so a missing map
breaks a run. Only the maps of the requested years are read (parquet filter). The flags are NOT model features; only B2a / B2b use them.

B2a  erp_trigger = 1 if D2+ (D2 + D3 + D4 area share > 0, i.e. any part of the county) on 8 consecutive weekly maps, or D3+ (D3 + D4 > 0) on any map.
B2b  erp_tier = the highest tier met (LFP-style): 1 = D2+ for 8 consecutive maps; 3 = any D3+; 4 = D3+ for 4+ consecutive maps or any D4;
     5 = D4 for 4+ consecutive maps; 0 = none.
"""
import functools

import pandas as pd

from data import REPO

RUN_WEEKS = 8
MAP_CUTOFF_MMDD = "08-13"


def _max_run(flag, d, keys):
    """Longest run of consecutive (7 days apart) True maps per (fips, year)."""
    g = flag.groupby([d.fips, d.year])
    prev = g.shift(1, fill_value=False)
    weekly = (d.map_date - d.groupby(["fips", "year"]).map_date.shift(1)).dt.days == 7
    start = flag & ~(prev & weekly)
    run_id = start.groupby([d.fips, d.year]).cumsum()
    runs = d[flag].groupby(["fips", "year", run_id[flag]]).size()
    return runs.groupby(["fips", "year"]).max()


@functools.lru_cache(maxsize=None)
def erp_trigger(y0, y1):
    f = REPO / "data" / "processed" / "drought" / "drought_weekly.parquet"
    d = pd.read_parquet(f, columns=["fips", "map_date", "D2", "D3", "D4"],
                        filters=[("map_date", ">=", pd.Timestamp(f"{y0}-01-01")), ("map_date", "<=", pd.Timestamp(f"{y1}-12-31"))])
    d["fips"] = d.fips.astype(str).str.zfill(5)
    d["year"] = d.map_date.dt.year
    mmdd = d.map_date.dt.strftime("%m-%d")
    d = d[(mmdd >= "04-01") & (mmdd <= MAP_CUTOFF_MMDD)].sort_values(["fips", "year", "map_date"]).reset_index(drop=True)
    d2, d3, d4 = (d.D2 + d.D3 + d.D4) > 0, (d.D3 + d.D4) > 0, d.D4 > 0
    key = ["fips", "year"]
    out = pd.DataFrame({"d2_max_run": _max_run(d2, d, key), "d3_max_run": _max_run(d3, d, key), "d4_max_run": _max_run(d4, d, key),
                        "d3_any": d3.groupby([d.fips, d.year]).any(), "d4_any": d4.groupby([d.fips, d.year]).any()}).reset_index()
    for c in ["d2_max_run", "d3_max_run", "d4_max_run"]:
        out[c] = out[c].fillna(0).astype(int)
    out["erp_trigger"] = ((out.d2_max_run >= RUN_WEEKS) | out.d3_any).astype(int)
    tier = (out.d2_max_run >= RUN_WEEKS).astype(int)
    tier = tier.where(~out.d3_any, 3)
    tier = tier.where(~((out.d3_max_run >= 4) | out.d4_any), 4)
    tier = tier.where(~(out.d4_max_run >= 4), 5)
    out["erp_tier"] = tier.astype(int)
    return out[["fips", "year", "erp_trigger", "erp_tier"]]
