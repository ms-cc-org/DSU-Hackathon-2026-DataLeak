"""Build drought-severity labels and inputs and organize them into training / validation (and, only for the final test, testing) folders.

Two prediction tasks, each with its own inputs file so nothing leaks:

  A. DROUGHT OUTLOOK  (labels_outlook)
     Label  : y_A = worst Drought Monitor level on maps dated Aug 14 - Sep 30 (0 = none ... 5 = D4);
              worse_A = 1 if y_A is worse than level_last_map (the last map dated <= Aug 13); change_A = y_A - level_last_map.
     Inputs : drought-map state known on Aug 15 (level_last_map, dsci_last, d0plus_pct_last, d1plus_pct_last, dsci_change_4wk, level_apr1,
              prev_fall_level, nbr_level_last), weather windows ending Aug 13, soil, irrigation.

  B. IN-SEASON DROUGHT FROM WEATHER + SOIL  (labels_weather_soil; drives the simulation)
     Label  : y_B = worst level on maps dated Apr 1 - Aug 13; level_apr1 = worst level on maps dated Mar 25 - Apr 7;
              worse_B = 1 if y_B > level_apr1; change_B = y_B - level_apr1.
     Inputs : weather, soil, irrigation, plus level_apr1 and prev_fall_level (worst level Aug 14 - Dec 31 of the previous year).
              NO map dated after Apr 7 of the year is used; the script asserts it.

Level scale (same as the repo's max_drought_severity): 0 = none, 1 = D0, 2 = D1, 3 = D2, 4 = D3, 5 = D4. A level counts on a map when that
category covers MORE than 1% of the county (D0..D4 in the parquet are NON-cumulative percentages of area).

HARD RULE: nothing from 2016-2025 (maps, weather, labels) is loaded unless --include-test AND --i-am-sure are both given (only for the final test).
Every parquet read filters the year at read time and asserts it. The testing/ folder is not written otherwise.

Usage (from anywhere):
    python organize_drought_severity.py --repo ~/path/to/DSU-Hackathon-2026-DataLeak --out ~/path/to/DSU-Hackathon-2026-DataLeak/drought_severity_data

Output (training 2000-2012, validation 2013-2015; testing 2016-2025 only with the flags above)
    drought_severity_data/  DATA_README.md  manifest.json  checks.md
        training/ all_inputs_outlook.csv all_inputs_weather_soil.csv all_labels_outlook.csv all_labels_weather_soil.csv + 19169_Story_IA/ (the same four files per county)
        validation/ same layout
One row = one county x year (drought is the same for corn and soybeans, so there is no crop column).
"""
import argparse
import datetime as dt
import json
import math
import pathlib
import re
import shutil

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------- settings
SPLITS = {"training": (2000, 2012), "validation": (2013, 2015), "testing": (2016, 2025)}
LAST_PRE_TEST_YEAR = 2015
FIRST_YEAR = 2000
WEATHER_FIRST_YEAR = 1999          # weather starts in 1999 (used only for normals and the winter window)
STATES = ("IA", "NE")
LEVEL_THRESHOLD_PCT = 1.0          # a D-level counts when its category covers > 1% of the county
INPUT_WINDOW = ("04-01", "08-13")  # maps used for Task A inputs and the Task B label (released by Aug 15)
OUTLOOK_WINDOW = ("08-14", "09-30")
APR1_WINDOW = ("03-25", "04-07")
PREV_FALL_WINDOW_START = "08-14"   # through Dec 31 of the previous year
CUTOFF_MD = "08-13"
NEIGHBOR_KM = 70.0
SEASON_CHECK_WINDOW = ("05-01", "09-30")  # corn season, only for the cross-check against the master

LEVEL_NAMES = {0: "None", 1: "D0", 2: "D1", 3: "D2", 4: "D3", 5: "D4"}
ID_COLS = ["fips", "county_name", "state_alpha", "year"]
MAP_FEATURES_A = ["level_last_map", "dsci_last", "d0plus_pct_last", "d1plus_pct_last", "dsci_change_4wk", "level_apr1", "prev_fall_level", "nbr_level_last"]
MAP_FEATURES_B = ["level_apr1", "prev_fall_level"]          # the only drought-map-derived inputs allowed in Task B
PRECIP_WINDOWS = ["precip_30d", "precip_60d", "precip_90d", "precip_apr1_to_cutoff", "winter_precip"]
WEATHER_FEATURES = (PRECIP_WINDOWS + ["tmax_mean_30d", "heat32_days_apr1_to_cutoff", "dry_days_30d", "wb_30d", "wb_90d", "wb_apr1"]
                    + [p + "_ratio" for p in PRECIP_WINDOWS])
STATIC_FEATURES = ["aws_100cm_mm", "droughty_pct", "irr_share", "is_nebraska"]
TASK_A_FEATURES = MAP_FEATURES_A + WEATHER_FEATURES + STATIC_FEATURES
TASK_B_FEATURES = MAP_FEATURES_B + WEATHER_FEATURES + STATIC_FEATURES
RE_DROUGHT = re.compile(r"^(d[0-4]_|d[0-4]p|d[0-4]plus|dsci|drought_|weeks_since|level_|prev_fall|nbr_level)", re.I)   # not "droughty" (soil)


# ----------------------------------------------------------------------------- helpers
def log(msg):
    print(msg, flush=True)


def safe_name(name):
    return re.sub(r"[^A-Za-z0-9]+", "_", str(name).replace(" County", "")).strip("_")


def md_of(s):
    return s.dt.strftime("%m-%d")


def map_level(df):
    """Highest D-level whose category covers more than LEVEL_THRESHOLD_PCT of the county (0 = none)."""
    cats = df[["D0", "D1", "D2", "D3", "D4"]].to_numpy(dtype=float)
    present = cats > LEVEL_THRESHOLD_PCT
    idx = np.where(present.any(axis=1), 4 - np.argmax(present[:, ::-1], axis=1), -1)
    return idx + 1


class CheckLog:
    def __init__(self):
        self.lines = []

    def ok(self, cond, msg):
        status = "PASS" if cond else "FAIL"
        self.lines.append(f"- **{status}** {msg}")
        log(f"  [{status}] {msg}")
        if not cond:
            raise SystemExit(f"Check failed: {msg}")

    def note(self, msg):
        self.lines.append(f"- {msg}")
        log(f"  [NOTE] {msg}")


def allowed_max_year(include_test, i_am_sure):
    if include_test and not i_am_sure:
        raise SystemExit("Refusing to load 2016-2025: pass --include-test together with --i-am-sure, and only for the final test.")
    return 2025 if include_test else LAST_PRE_TEST_YEAR


# ----------------------------------------------------------------------------- loaders (every one filters the year at read time)
def read_drought(repo, max_year):
    d = pd.read_parquet(repo / "data/processed/drought/drought_weekly.parquet",
                        filters=[("map_date", "<=", pd.Timestamp(f"{max_year}-12-31")), ("state_alpha", "in", list(STATES))])
    assert d.map_date.dt.year.max() <= max_year, "a drought map after the allowed year was loaded"
    d["fips"] = d.fips.astype(str).str.zfill(5)
    d["year"] = d.map_date.dt.year
    d["md"] = md_of(d.map_date)
    d["dlevel"] = map_level(d)
    d["d0p"] = (100 - d.none_pct).clip(lower=0)
    d["d1p"] = d.D1 + d.D2 + d.D3 + d.D4
    return d


def read_weather(repo, max_year):
    w = pd.read_parquet(repo / "data/processed/acis/weather_daily.parquet", columns=["fips", "date", "pcpn_mm", "tmax_c", "tmin_c"],
                        filters=[("date", "<=", pd.Timestamp(f"{max_year}-12-31")), ("state_alpha", "in", list(STATES))])
    assert w.date.dt.year.max() <= max_year, "a weather day after the allowed year was loaded"
    w["fips"] = w.fips.astype(str).str.zfill(5)
    return w


def read_static(repo, max_year):
    soil = pd.read_parquet(repo / "data/processed/soil/soil_county.parquet", columns=["fips", "state_alpha", "aws_100cm_mm", "droughty_pct"])
    soil["fips"] = soil.fips.astype(str).str.zfill(5)
    soil = soil[soil.state_alpha.isin(STATES)].drop(columns="state_alpha").set_index("fips")
    irr = pd.read_parquet(repo / "data/processed/irrigation/nass_irrigation.parquet", columns=["fips", "state_alpha", "year", "irrigated_share"],
                          filters=[("year", "<=", max_year), ("state_alpha", "in", list(STATES))])
    assert irr.year.max() <= max_year
    irr["fips"] = irr.fips.astype(str).str.zfill(5)
    return soil, irr


def read_centroids(repo):
    """Area-weighted centroid (outer rings, planar on lon*cos(lat)) of every IA / NE county from counties.geojson."""
    g = json.load(open(repo / "data/counties.geojson"))
    rows = []
    for f in g["features"]:
        p = f["properties"]
        if p["state_alpha"] not in STATES:
            continue
        polys = f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiPolygon" else [f["geometry"]["coordinates"]]
        A = lon_s = lat_s = 0.0
        for poly in polys:
            ring = np.array(poly[0], dtype=float)
            lat0 = ring[:, 1].mean()
            k = math.cos(math.radians(lat0))
            xs, ys = ring[:, 0] * k, ring[:, 1]
            x1, y1 = np.roll(xs, -1), np.roll(ys, -1)
            cross = xs * y1 - x1 * ys
            a = cross.sum() / 2
            if a == 0:
                continue
            cxp, cyp = ((xs + x1) * cross).sum() / (6 * a), ((ys + y1) * cross).sum() / (6 * a)   # polygon centroid (any ring orientation)
            A += abs(a)
            lon_s += abs(a) * cxp / k
            lat_s += abs(a) * cyp
        lon, lat = lon_s / A, lat_s / A
        rows.append({"fips": str(p["fips"]).zfill(5), "county_name": p["county_name"], "state_alpha": p["state_alpha"], "lat": lat, "lon": lon})
    return pd.DataFrame(rows).set_index("fips")


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


# ----------------------------------------------------------------------------- features
def ra_mj(lat_rad, doy):
    """FAO-56 extraterrestrial radiation (MJ m-2 day-1)."""
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    dec = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(lat_rad) * np.tan(dec), -1, 1))
    return (24 * 60 / np.pi) * 0.0820 * dr * (ws * np.sin(lat_rad) * np.sin(dec) + np.cos(lat_rad) * np.cos(dec) * np.sin(ws))


def hargreaves_et0(tmax, tmin, lat_rad, doy):
    """ET0 (mm/day) = 0.0023 * 0.408 * Ra * (Tmean + 17.8) * sqrt(max(Tmax - Tmin, 0))."""
    tmean = (tmax + tmin) / 2
    return np.maximum(0.0023 * 0.408 * ra_mj(lat_rad, doy) * (tmean + 17.8) * np.sqrt(np.maximum(tmax - tmin, 0)), 0)


def weather_windows(w, lat_deg):
    """Raw weather windows per (fips, year); days after Aug 13 of the decision year are never used.
    Returns (features, maxmd) where maxmd is the latest month-day of any day used per feature group (for the date check)."""
    w = w.copy()
    w["year"] = w.date.dt.year
    w["doy"] = w.date.dt.dayofyear
    w["mdn"] = w.date.dt.month * 100 + w.date.dt.day
    w["et0"] = hargreaves_et0(w.tmax_c.to_numpy(), w.tmin_c.to_numpy(), np.radians(w.fips.map(lat_deg).to_numpy(dtype=float)), w.doy.to_numpy())
    cut = pd.to_datetime(dict(year=w.year, month=8, day=13))
    delta = (cut - w.date).dt.days                      # 0 on Aug 13, negative after it
    w["dry"] = (w.pcpn_mm < 1).astype(float).where(w.pcpn_mm.notna())
    w["hot"] = (w.tmax_c >= 32).astype(float).where(w.tmax_c.notna())
    keys = ["fips", "year"]
    masks = {"30d": (delta >= 0) & (delta <= 29), "60d": (delta >= 0) & (delta <= 59), "90d": (delta >= 0) & (delta <= 89),
             "apr1": (w.mdn >= 401) & (w.mdn <= 813)}
    out, maxmd = {}, {}
    for name, m in masks.items():
        sub = w[m]
        out[f"precip_{name}" if name != "apr1" else "precip_apr1_to_cutoff"] = sub.groupby(keys).pcpn_mm.sum(min_count=1)
        maxmd[name] = int(sub.mdn.max())
    out["tmax_mean_30d"] = w[masks["30d"]].groupby(keys).tmax_c.mean()
    out["dry_days_30d"] = w[masks["30d"]].groupby(keys).dry.sum(min_count=1)
    out["heat32_days_apr1_to_cutoff"] = w[masks["apr1"]].groupby(keys).hot.sum(min_count=1)
    for name, key in [("30d", "wb_30d"), ("90d", "wb_90d"), ("apr1", "wb_apr1")]:
        sub = w[masks[name]].groupby(keys)
        out[key] = sub.pcpn_mm.sum(min_count=1) - sub.et0.sum(min_count=1)
    # winter: Oct 1 of the previous year to Mar 31 (target year = year + 1 for Oct-Dec)
    mon = w.date.dt.month
    wt = w[(mon >= 10) | (mon <= 3)].copy()
    wt["target"] = wt.year + (wt.date.dt.month >= 10).astype(int)
    out["winter_precip"] = wt.groupby(["fips", "target"]).pcpn_mm.sum(min_count=1).rename_axis(["fips", "year"])
    maxmd["winter_in_target_year"] = int(wt[wt.date.dt.month <= 3].mdn.max())
    feat = pd.DataFrame(out)
    return feat, maxmd


def add_ratios(feat, first_year, last_year):
    """*_ratio = window / mean of the same window over STRICTLY EARLIER years (at least 3), per county. Fold-safe for every fold."""
    fips = feat.index.get_level_values("fips").unique()
    full = pd.MultiIndex.from_product([fips, range(WEATHER_FIRST_YEAR, last_year + 1)], names=["fips", "year"])
    f = feat.reindex(full).sort_index()
    f.loc[(slice(None), WEATHER_FIRST_YEAR), "winter_precip"] = np.nan        # Oct-Dec 1998 are not in the weather file: the 1999 winter window is incomplete
    for c in PRECIP_WINDOWS:
        normal = f.groupby(level="fips")[c].transform(lambda s: s.shift(1).expanding(min_periods=3).mean())
        f[c + "_ratio"] = f[c] / normal
    return f[f.index.get_level_values("year") >= first_year]


def map_features(d):
    """Map-derived inputs and labels per (fips, year) from the weekly maps. Also returns the latest map dates used by each group."""
    keys = ["fips", "year"]
    inp = d[(d.md >= INPUT_WINDOW[0]) & (d.md <= INPUT_WINDOW[1])].sort_values("map_date")
    g_in = inp.groupby(keys)
    last = g_in.tail(1).set_index(keys)
    feat = pd.DataFrame({"level_last_map": last.dlevel, "dsci_last": last.dsci, "d0plus_pct_last": last.d0p, "d1plus_pct_last": last.d1p,
                         "last_input_map_date": last.map_date})
    key = inp.set_index(["fips", "year", "map_date"]).dsci
    idx = pd.MultiIndex.from_arrays([last.index.get_level_values("fips"), last.index.get_level_values("year"), (last.map_date - pd.Timedelta(days=28)).to_numpy()])
    prev = key.reindex(idx)
    feat["dsci_change_4wk"] = pd.Series(last.dsci.to_numpy() - prev.to_numpy(), index=last.index)
    apr1 = d[(d.md >= APR1_WINDOW[0]) & (d.md <= APR1_WINDOW[1])]
    feat["level_apr1"] = apr1.groupby(keys).dlevel.max()
    apr1_last_date = apr1.groupby(keys).map_date.max()
    fall = d[d.md >= PREV_FALL_WINDOW_START]                       # Aug 14 - Dec 31 of the year
    pf = fall.groupby(keys).dlevel.max().reset_index()
    pf["year"] += 1                                                 # becomes the previous-fall level of the NEXT year
    feat["prev_fall_level"] = pf.set_index(keys).dlevel
    fall_last_date = fall.groupby(keys).map_date.max().reset_index()
    fall_last_date["year"] += 1
    feat["n_input_maps"] = g_in.size()
    feat["y_B"] = g_in.dlevel.max()
    feat["weeks_d2plus_to_cutoff"] = g_in.dlevel.agg(lambda s: int((s >= 3).sum()))
    out = d[(d.md >= OUTLOOK_WINDOW[0]) & (d.md <= OUTLOOK_WINDOW[1])]
    g_out = out.groupby(keys)
    feat["y_A"] = g_out.dlevel.max()
    feat["n_outlook_maps"] = g_out.size()
    feat["last_outlook_map_date"] = g_out.map_date.max()
    dates = {"input_last": last.map_date, "apr1_last": apr1_last_date, "prev_fall_last": fall_last_date.set_index(keys).map_date,
             "outlook_first": out.groupby(keys).map_date.min(), "outlook_last": g_out.map_date.max()}
    return feat, dates


def neighbor_level(level_last, cent):
    """Mean level_last_map of the OTHER counties whose centroid is within NEIGHBOR_KM, per year."""
    fips = list(cent.index)
    lat, lon = cent.lat.to_numpy(), cent.lon.to_numpy()
    dist = haversine_km(lat[:, None], lon[:, None], lat[None, :], lon[None, :])
    adj = (dist <= NEIGHBOR_KM) & ~np.eye(len(fips), dtype=bool)
    wide = level_last.unstack("fips").reindex(columns=fips)
    num = wide.fillna(0).to_numpy() @ adj.astype(float)
    den = wide.notna().to_numpy().astype(float) @ adj.astype(float)
    nbr = pd.DataFrame(np.where(den > 0, num / np.where(den > 0, den, 1), np.nan), index=wide.index, columns=fips)
    return nbr.stack(dropna=False).rename("nbr_level_last").rename_axis(["year", "fips"]).swaplevel().sort_index(), adj


def build_tables(repo, include_test=False, i_am_sure=False, checks=None, drought=None, weather=None):
    """Build features and labels for every county x year up to the allowed year. Returns a dict of DataFrames (never writes anything)."""
    repo = pathlib.Path(repo).expanduser().resolve()
    checks = checks or CheckLog()
    max_year = allowed_max_year(include_test, i_am_sure)
    d = drought if drought is not None else read_drought(repo, max_year)
    cent = read_centroids(repo)
    cent = cent[cent.index.isin(d.fips.unique())]
    names = d.drop_duplicates("fips").set_index("fips")[["county_name", "state_alpha"]]
    sums = d[["none_pct", "D0", "D1", "D2", "D3", "D4"]].sum(axis=1)
    checks.ok(((sums > 99) & (sums < 101)).mean() > 0.99, "weekly drought categories are non-overlapping (none + D0..D4 sum to ~100%)")
    checks.ok(d.year.max() <= max_year and d.year.min() >= FIRST_YEAR, f"drought maps loaded only for {FIRST_YEAR}-{max_year}")

    mf, dates = map_features(d)
    checks.ok(md_of(dates["input_last"]).max() <= CUTOFF_MD, f"every Task A map input (level_last_map, dsci_last, d0/d1 share, dsci_change_4wk) comes from a map dated <= {CUTOFF_MD}")
    checks.ok(md_of(dates["outlook_first"]).min() >= OUTLOOK_WINDOW[0], f"outlook-label maps all start on/after {OUTLOOK_WINDOW[0]} (after every input map)")
    checks.ok(md_of(dates["apr1_last"]).max() <= APR1_WINDOW[1],
              f"level_apr1 uses maps dated <= {APR1_WINDOW[1]} only (latest map date used: {md_of(dates['apr1_last']).max()}), so Task B sees no map after Apr 7")
    pf_last = dates["prev_fall_last"]
    yrs = pf_last.index.get_level_values("year")
    checks.ok(bool((pf_last.dt.year == yrs - 1).all()), "prev_fall_level uses maps from the PREVIOUS calendar year only (all dated before Jan 1 of the decision year)")

    w = weather if weather is not None else read_weather(repo, max_year)
    wf, maxmd = weather_windows(w, cent.lat)
    checks.ok(max(maxmd[k] for k in ("30d", "60d", "90d", "apr1")) <= 813 and maxmd["winter_in_target_year"] <= 331,
              f"every weather window ends <= Aug 13 of its year (latest in-season month-day used: {max(maxmd[k] for k in ('30d','60d','90d','apr1'))}; winter window ends Mar 31)")
    wf = add_ratios(wf, FIRST_YEAR, max_year)

    soil, irr = read_static(repo, max_year)
    irr_cy = irr.groupby(["fips", "year"]).irrigated_share.mean().reset_index().sort_values(["fips", "year"])
    irr_cy["irr_share"] = irr_cy.groupby("fips").irrigated_share.transform(lambda s: s.shift(1).expanding(min_periods=1).mean())
    irr_cy = irr_cy.set_index(["fips", "year"]).irr_share

    grid = pd.MultiIndex.from_product([sorted(names.index), range(FIRST_YEAR, max_year + 1)], names=["fips", "year"])
    feat = pd.DataFrame(index=grid)
    feat = feat.join(mf).join(wf)
    feat["irr_share"] = irr_cy.reindex(grid)
    nbr, adj = neighbor_level(feat.level_last_map, cent.reindex(sorted(names.index)))
    feat = feat.join(nbr)
    feat = feat.reset_index()
    feat = feat.join(names, on="fips")
    feat = feat.join(soil, on="fips")
    feat["is_nebraska"] = (feat.state_alpha == "NE").astype(int)
    checks.note(f"neighbors: {int(adj.sum(axis=1).min())}-{int(adj.sum(axis=1).max())} other counties within {NEIGHBOR_KM:.0f} km per county (median {int(np.median(adj.sum(axis=1)))})")

    feat["worse_A"] = (feat.y_A > feat.level_last_map).astype("Int64").where(feat.y_A.notna() & feat.level_last_map.notna())
    feat["change_A"] = feat.y_A - feat.level_last_map
    feat["worse_B"] = (feat.y_B > feat.level_apr1).astype("Int64").where(feat.y_B.notna() & feat.level_apr1.notna())
    feat["change_B"] = feat.y_B - feat.level_apr1
    for c in ("y_A", "y_B"):
        feat[c + "_name"] = feat[c].map(LEVEL_NAMES)
    for c in ("last_input_map_date", "last_outlook_map_date"):
        feat[c] = feat[c].dt.strftime("%Y-%m-%d")
    feat = feat.sort_values(["fips", "year"]).reset_index(drop=True)
    return {"feat": feat, "names": names, "max_year": max_year, "checks": checks, "drought": d, "dates": dates}


# ----------------------------------------------------------------------------- writing
def write_split(df_in_a, df_in_b, df_lab_a, df_lab_b, folder):
    folder.mkdir(parents=True, exist_ok=True)
    df_in_a.to_csv(folder / "all_inputs_outlook.csv", index=False)
    df_in_b.to_csv(folder / "all_inputs_weather_soil.csv", index=False)
    df_lab_a.to_csv(folder / "all_labels_outlook.csv", index=False)
    df_lab_b.to_csv(folder / "all_labels_weather_soil.csv", index=False)
    for (fips, name, st), _ in df_in_a.groupby(["fips", "county_name", "state_alpha"]):
        sub = folder / f"{fips}_{safe_name(name)}_{st}"
        sub.mkdir(exist_ok=True)
        for frame, fname in [(df_in_a, "inputs_outlook.csv"), (df_in_b, "inputs_weather_soil.csv"), (df_lab_a, "labels_outlook.csv"), (df_lab_b, "labels_weather_soil.csv")]:
            frame[frame.fips == fips].sort_values("year").to_csv(sub / fname, index=False)


def persistence_stats(feat):
    out = {}
    for task, y, start, worse in (("A", "y_A", "level_last_map", "worse_A"), ("B", "y_B", "level_apr1", "worse_B")):
        v = feat.dropna(subset=[y, start])
        if v.empty:
            continue
        yy, pp = v[y].astype(int), v[start].astype(int)
        out[f"task_{task}"] = {"rows": int(len(v)), "persistence_exact_accuracy": round(float((yy == pp).mean()), 3),
                               "persistence_within_one_level": round(float(((yy - pp).abs() <= 1).mean()), 3),
                               "worse_rate": round(float(v[worse].astype(float).mean()), 3),
                               "label_distribution": {LEVEL_NAMES[int(k)]: int(n) for k, n in yy.value_counts().sort_index().items()}}
    return out


README = """# drought_severity_data (data guide)

Built by `organize_drought_severity.py` on {built}. One row = one county x year, Iowa + Nebraska (all counties). Drought is the same for corn and soybeans, so there is no crop column.

| Folder | Years | Use |
|---|---|---|
| training | {tr} | fit models |
| validation | {va} | compare / confirm models |
{testing_row}
Always read CSVs with `dtype={{"fips": str}}`. Join inputs to labels on `fips, year`.

## Level scale
0 = none, 1 = D0, 2 = D1, 3 = D2, 4 = D3, 5 = D4. A level counts on a weekly map when its category (D0..D4 are non-cumulative % of area) covers more than {thr}% of the county.

## Task A: drought outlook (does it get worse after the decision date?)
- **Labels** (`labels_outlook.csv`), from maps dated **{ow0}-{ow1}** (all after the cutoff): `y_A` worst level (0-5); `worse_A` = 1 if `y_A` > `level_last_map`; `change_A` = `y_A` - `level_last_map`.
- **Inputs** (`inputs_outlook.csv`): map state on the last map dated by Aug 13 (`level_last_map` is also the persistence baseline, `dsci_last`, `d0plus_pct_last`, `d1plus_pct_last`),
  `dsci_change_4wk` (last map minus the map 28 days earlier), `level_apr1` (worst level on maps dated Mar 25-Apr 7), `prev_fall_level` (worst level Aug 14-Dec 31 of the previous year),
  `nbr_level_last` (mean `level_last_map` of the other counties with a centroid within {nbr} km), plus the weather, soil and irrigation columns below.

## Task B: in-season drought from weather + soil
- **Labels** (`labels_weather_soil.csv`), from maps dated {iw0}-{iw1}: `y_B` worst level; `worse_B` = 1 if `y_B` > `level_apr1`; `change_B` = `y_B` - `level_apr1`; `weeks_d2plus_to_cutoff`.
- **Inputs** (`inputs_weather_soil.csv`): weather, soil and irrigation columns plus `level_apr1` and `prev_fall_level`. NO map dated after Apr 7 of the year is used (asserted in checks.md).

## Weather columns (daily weather, only days <= Aug 13 of the year)
`precip_30d / 60d / 90d` (the 30, 60, 90 days ending Aug 13), `precip_apr1_to_cutoff`, `winter_precip` (Oct 1 of the previous year to Mar 31), `tmax_mean_30d`, `heat32_days_apr1_to_cutoff` (tmax >= 32 C),
`dry_days_30d` (days < 1 mm), `wb_30d / wb_90d / wb_apr1` = precipitation - ET0 (Hargreaves, FAO-56 Ra from the county centroid latitude: ET0 = 0.0023 * 0.408 * Ra * (Tmean + 17.8) * sqrt(max(Tmax - Tmin, 0))),
and `*_ratio` = window / the county's mean of the same window over strictly earlier years (weather starts in 1999; at least 3 earlier years, else blank).
Static: `aws_100cm_mm`, `droughty_pct`, `irr_share` (mean over strictly earlier years of the county's irrigated share, blank for the first year), `is_nebraska`.

## Leakage rules (enforced by the script, see checks.md)
- Label columns never appear in any inputs file; Task A labels only use maps dated after every map the inputs use; Task B inputs use no map dated after Apr 7.
- Normals and irrigation averages use strictly earlier years; imputers and scalers are fitted per fold in the model code.
- Nothing from 2016-2025 is loaded unless `--include-test --i-am-sure` (final test only).
- Not used: MODIS NDVI, the master dataset's season weather/drought columns, same-year yield or harvest.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--include-test", action="store_true", help="also load and write 2016-2025 (final test only; requires --i-am-sure)")
    ap.add_argument("--i-am-sure", action="store_true")
    a = ap.parse_args()
    repo = pathlib.Path(a.repo).expanduser().resolve()
    out = pathlib.Path(a.out).expanduser().resolve()
    if (out / ".git").exists() or out == repo:
        raise SystemExit("--out must be a data folder such as <repo>/drought_severity_data, not the repo itself.")

    checks = CheckLog()
    log("1/4 building features and labels from the raw repo files ...")
    r = build_tables(repo, a.include_test, a.i_am_sure, checks)
    feat, max_year = r["feat"], r["max_year"]

    log("2/4 leakage and sanity checks ...")
    label_cols = {"y_A", "y_B", "worse_A", "worse_B", "change_A", "change_B", "y_A_name", "y_B_name", "weeks_d2plus_to_cutoff", "n_input_maps", "n_outlook_maps",
                  "last_input_map_date", "last_outlook_map_date"}
    in_a, in_b = feat[ID_COLS + TASK_A_FEATURES].copy(), feat[ID_COLS + TASK_B_FEATURES].copy()
    lab_a = feat[ID_COLS + ["y_A", "y_A_name", "worse_A", "change_A", "n_outlook_maps", "last_outlook_map_date"]].copy()
    lab_b = feat[ID_COLS + ["y_B", "y_B_name", "worse_B", "change_B", "weeks_d2plus_to_cutoff", "n_input_maps", "last_input_map_date"]].copy()
    checks.ok(not (label_cols & set(in_a.columns)), "Task A inputs contain no label columns")
    checks.ok(not (label_cols & set(in_b.columns)), "Task B inputs contain no label columns")
    drought_like = [c for c in in_b.columns if RE_DROUGHT.search(c)]
    checks.ok(sorted(drought_like) == sorted(MAP_FEATURES_B),
              f"Task B inputs contain only the two allowed map-derived columns {MAP_FEATURES_B} (found: {sorted(drought_like)}); both use maps dated <= Apr 7 of the year or before Jan 1")
    checks.ok(all(c in in_a.columns for c in MAP_FEATURES_A), "Task A inputs contain the map-state features")
    for name, t in (("Task A inputs", in_a), ("Task B inputs", in_b), ("Task A labels", lab_a), ("Task B labels", lab_b)):
        checks.ok((t[["fips", "year"]].to_numpy() == feat[["fips", "year"]].to_numpy()).all(), f"row alignment: {name} has the same county-year in every row")
    checks.ok(feat.duplicated(["fips", "year"]).sum() == 0, "one row per county x year")
    checks.ok((feat.fips.str.len() == 5).all(), "every fips is a 5-character string")
    checks.ok(feat.year.max() <= max_year and (a.include_test or feat.year.max() <= LAST_PRE_TEST_YEAR), f"no row after {max_year} in any output (2016+ excluded unless the final-test flags were given)")
    checks.ok((feat.n_input_maps.dropna() >= 15).mean() > 0.99, "almost every county-year has >= 15 input maps (Apr 1 - Aug 13)")
    checks.ok((feat.n_outlook_maps.dropna() >= 6).mean() > 0.99, "almost every county-year has >= 6 outlook maps (Aug 14 - Sep 30)")
    miss_a, miss_b = feat.worse_A.isna().mean(), feat.worse_B.isna().mean()
    checks.ok(miss_a < 0.02 and miss_b < 0.02, f"labels exist for almost every row (missing: worse_A {miss_a:.2%}, worse_B {miss_b:.2%})")
    checks.ok(pd.to_datetime(feat.last_input_map_date.dropna()).dt.strftime("%m-%d").max() <= CUTOFF_MD, f"level_last_map always comes from a map dated by {CUTOFF_MD}")
    corr = in_b.select_dtypes("number").drop(columns=["year"], errors="ignore").corrwith(feat.y_B.astype(float)).abs()
    checks.note(f"Task B: strongest single input vs y_B |correlation| = {corr.max():.2f} ({corr.idxmax()}); near 1.0 would suggest a hidden copy of the label")
    checks.ok(corr.max() < 0.95, "no Task B input is a near-copy of the label")
    # cross-check of the level definition against the repo master (read with a year filter; only for this check)
    d = r["drought"]
    season = d[(d.md >= SEASON_CHECK_WINDOW[0]) & (d.md <= SEASON_CHECK_WINDOW[1])]
    mine = season.groupby(["fips", "year"]).dlevel.max().rename("mine")
    m = pd.read_parquet(repo / "data/master_dataset.parquet", columns=["fips", "year", "crop", "state_alpha", "max_drought_severity"],
                        filters=[("year", "<=", max_year), ("crop", "==", "CORN"), ("state_alpha", "in", list(STATES))])
    assert m.year.max() <= max_year
    m["fips"] = m.fips.astype(str).str.zfill(5)
    cmp_ = m.join(mine, on=["fips", "year"]).dropna(subset=["mine", "max_drought_severity"])
    agree = (cmp_.max_drought_severity.astype(float) == cmp_.mine).mean()
    checks.note(f"cross-check vs master max_drought_severity (corn, May 1 - Sep 30): {agree:.1%} of {len(cmp_)} county-years agree exactly (differences come from the master's own season window)")
    checks.ok(agree > 0.80, "level definition matches the repo's master dataset for > 80% of county-years")

    log("3/4 writing folders ...")
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"built": dt.datetime.now().isoformat(timespec="seconds"), "max_year_loaded": max_year, "level_threshold_pct": LEVEL_THRESHOLD_PCT,
                "input_window": INPUT_WINDOW, "outlook_label_window": OUTLOOK_WINDOW, "task_a_input_columns": TASK_A_FEATURES,
                "task_b_input_columns": TASK_B_FEATURES, "splits": {}}
    splits = SPLITS if a.include_test else {k: v for k, v in SPLITS.items() if k != "testing"}
    for split, (y0, y1) in splits.items():
        folder = out / split
        if folder.exists():
            shutil.rmtree(folder)
        msk = feat.year.between(y0, y1)
        write_split(in_a[msk], in_b[msk], lab_a[msk], lab_b[msk], folder)
        stats = persistence_stats(feat[msk])
        stats["counties"] = int(feat[msk].fips.nunique())
        manifest["splits"][split] = {"years": [y0, y1], "rows": int(msk.sum()), **stats}
        log(f"  {split:10s} {y0}-{y1}: {int(msk.sum())} rows, {stats['counties']} counties, A persistence exact {stats.get('task_A', {}).get('persistence_exact_accuracy')}, "
            f"worse_A rate {stats.get('task_A', {}).get('worse_rate')}, worse_B rate {stats.get('task_B', {}).get('worse_rate')}")
    if a.include_test:
        (out / "testing" / "DO_NOT_USE_UNTIL_FINAL_TEST.txt").write_text("Held-out years 2016-2025. Do not train, tune or look at results here until the model is final.\n")
    tr, va = (f"{SPLITS[s][0]}-{SPLITS[s][1]}" for s in ("training", "validation"))
    testing_row = "| testing | 2016-2025 | final check, run once at the end |\n" if a.include_test else "| testing | 2016-2025 | NOT BUILT (only with `--include-test --i-am-sure`, for the final test) |\n"
    log("4/4 documentation ...")
    (out / "DATA_README.md").write_text(README.format(built=manifest["built"], tr=tr, va=va, testing_row=testing_row, thr=LEVEL_THRESHOLD_PCT, ow0=OUTLOOK_WINDOW[0],
                                                      ow1=OUTLOOK_WINDOW[1], iw0=INPUT_WINDOW[0], iw1=INPUT_WINDOW[1], nbr=int(NEIGHBOR_KM)))
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    (out / "checks.md").write_text("# Checks\n\n" + "\n".join(checks.lines) + "\n")
    log(f"done -> {out}")


if __name__ == "__main__":
    main()
