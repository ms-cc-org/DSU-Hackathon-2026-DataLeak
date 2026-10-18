"""B2 input: the USDA ERP-style drought trigger, computed from the weekly Drought Monitor maps (data/processed/drought).

A county-year triggers if, on maps dated Apr 1 through Aug 14 of that year (the window the models' inputs use), it had D2+ (D2 + D3 + D4 area
share > 0, i.e. on any part of the county) on 8 consecutive weekly maps, or reached D3+ (D3 + D4 area share > 0) on any map. Consecutive means
maps exactly 7 days apart, so a missing map breaks a run. Only the maps of the requested years are read (parquet filter), so evaluation never
touches 2016+ maps. The flag is NOT a model feature; only B2 uses it.
"""
import functools

import pandas as pd

from data import REPO

RUN_WEEKS = 8


@functools.lru_cache(maxsize=None)
def erp_trigger(y0, y1):
    f = REPO / "data" / "processed" / "drought" / "drought_weekly.parquet"
    d = pd.read_parquet(f, columns=["fips", "map_date", "D2", "D3", "D4"],
                        filters=[("map_date", ">=", pd.Timestamp(f"{y0}-01-01")), ("map_date", "<=", pd.Timestamp(f"{y1}-12-31"))])
    d["fips"] = d.fips.astype(str).str.zfill(5)
    d["year"] = d.map_date.dt.year
    mmdd = d.map_date.dt.strftime("%m-%d")
    d = d[(mmdd >= "04-01") & (mmdd < "08-15")].sort_values(["fips", "year", "map_date"]).reset_index(drop=True)
    d["d2"] = (d.D2 + d.D3 + d.D4) > 0
    d["d3"] = (d.D3 + d.D4) > 0
    g = d.groupby(["fips", "year"])
    prev_d2 = g.d2.shift(1, fill_value=False)
    weekly = (d.map_date - g.map_date.shift(1)).dt.days == 7
    run_start = d.d2 & ~(prev_d2 & weekly)
    d["run_id"] = run_start.groupby([d.fips, d.year]).cumsum()
    runs = d[d.d2].groupby(["fips", "year", "run_id"]).size()
    out = pd.DataFrame({"d2_max_run": runs.groupby(["fips", "year"]).max(), "d3_any": g.d3.any()}).reset_index()
    out["d2_max_run"] = out.d2_max_run.fillna(0).astype(int)
    out["erp_trigger"] = ((out.d2_max_run >= RUN_WEEKS) | out.d3_any).astype(int)
    return out[["fips", "year", "d2_max_run", "d3_any", "erp_trigger"]]
