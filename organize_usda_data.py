"""Organize repo data (inputs) + USDA RMA files (labels) into training / validation / testing folders.

Usage (from anywhere):
    python organize_usda_data.py \
        --downloads ~/Downloads \
        --repo      ~/path/to/DSU-Hackathon-Team-x \
        --out       ~/ms-cc/app/usda_budget_data

--downloads  folder holding the RMA files: colsom_YYYY.zip / .txt (cause of loss) and
             sobcov_YYYY.zip / .txt (insured dollars by coverage level). Subfolders are searched too.
--repo       your team repo (needs data/master_dataset.parquet and data/processed/...).
--out        the usda_budget_data folder. Existing split folders are replaced.

Output
    usda_budget_data/
        DATA_README.md            what every column means, split years, leakage rules
                                  (separate from your repo's main README.md; never overwrites it)
        manifest.json             row counts, which RMA years were found / missing
        training/   (2000-2012)
            all_inputs.csv        every county stacked (handy for training)
            all_labels.csv
            19169_Story_IA/
                inputs.csv        one row per crop x year, only info known on Aug 15
                labels.csv        what actually happened (RMA payouts, yields)
            ...
        validation/ (2013-2015)   same layout
        testing/    (2016-2025)   same layout, plus a DO_NOT_USE note

Rows: Iowa and Nebraska, corn and soybeans. One row per county x crop x year.
"""
import argparse, io, json, pathlib, re, zipfile
import numpy as np
import pandas as pd

SPLITS = {"training": (2000, 2012), "validation": (2013, 2015), "testing": (2016, 2025)}
TRAIN_END = SPLITS["training"][1]          # training years end (rain normals and irrigation averages now use strictly earlier years instead)
STATES = {"IA": "19", "NE": "31"}
CROPS = ["CORN", "SOYBEANS"]
DECISION_MMDD = "08-15"                    # daily weather uses data before this date (through Aug 14)
MAP_CUTOFF_MMDD = "08-13"                  # drought maps: only maps released by Aug 15 (map_date <= Aug 13; the Thursday release of the Aug 13 map is Aug 15)
FIPS_MERGE = {"19156": "19155"}            # RMA reports Pottawattamie as E (155) + W (156); the repo data has one county, 19155

# ---------------------------------------------------------------- RMA parsing
COLSOM = ["year", "state_code", "state_abbr", "county_code", "county_name", "commodity_code",
          "commodity", "plan_code", "plan", "coverage_category", "stage_code", "cause_code",
          "cause", "month_code", "month", "year_of_loss", "policies_earning", "policies_indemnified",
          "net_planted_qty", "endorsed_acres", "liability", "total_premium", "producer_premium",
          "subsidy", "state_subsidy", "additional_subsidy", "efa_discount", "net_determined_qty",
          "indemnity", "loss_ratio"]
SOBCOV = ["year", "state_code", "state_abbr", "county_code", "county_name", "commodity_code",
          "commodity", "plan_code", "plan", "coverage_category", "delivery_type", "coverage_level",
          "policies_sold", "policies_earning", "policies_indemnified", "units_earning",
          "units_indemnified", "quantity_type", "net_reported_qty", "endorsed_acres", "liability",
          "total_premium", "subsidy", "state_subsidy", "additional_subsidy", "efa_discount",
          "indemnity", "loss_ratio"]
# Area-based / add-on plans pay on county averages or stack on top of a base policy.
# Real names look like "SCO-RP", "ECO-YP", "MP-HPO", so match on the prefix.
EXCLUDE_PLAN = re.compile(r"^(SCO|ECO|STAX|ARP|ARPI|AYP|GRP|GRIP|MP|HIP|PACE)\b")
EXCLUDE_CAUSE_CODES = {"55"}               # "ARPI/SCO/ECO/STAX/MP/HIP-WI/PACE Crops Only"


def _read_text(text, names):
    first = text.split("|", 1)[0].strip()
    df = pd.read_csv(io.StringIO(text), sep="|", header=None if first.isdigit() else 0,
                     dtype=str, keep_default_na=False)
    df = df.iloc[:, :len(names)]
    df.columns = names[:df.shape[1]]
    return df


def read_rma(path, names):
    path = pathlib.Path(path)
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as z:
            parts = [_read_text(z.read(m).decode("latin-1"), names)
                     for m in z.namelist() if m.lower().endswith(".txt")]
        df = pd.concat(parts, ignore_index=True)
    else:
        df = _read_text(path.read_text(encoding="latin-1"), names)
    df = df.apply(lambda s: s.str.strip())
    df = df[df.state_abbr.isin(STATES) & df.commodity.str.upper().isin(CROPS)].copy()
    df["fips"] = (df.state_code.str.zfill(2) + df.county_code.str.zfill(3)).replace(FIPS_MERGE)   # merged before aggregation, so liability/acres/payouts add up
    df["crop"] = df.commodity.str.upper()
    df["year"] = pd.to_numeric(df.year, errors="coerce").astype(int)
    for c in ["liability", "indemnity", "net_determined_qty", "net_reported_qty", "coverage_level"]:
        if c in df:
            df[c] = pd.to_numeric(df[c].replace("", np.nan), errors="coerce")
    df = df[~df.plan.str.upper().str.match(EXCLUDE_PLAN) & (df.county_code != "999")]  # 999 = "All Other Counties"
    return df


def find_files(folder, prefix):
    """Map year -> file for colsom_YYYY / sobcov_YYYY (.zip or .txt), searching subfolders."""
    found = {}
    for p in pathlib.Path(folder).expanduser().rglob(f"{prefix}_*"):
        m = re.match(rf"{prefix}_(\d{{4}})\.(zip|txt)$", p.name, re.I)
        if m and SPLITS["training"][0] <= int(m.group(1)) <= SPLITS["testing"][1]:
            found.setdefault(int(m.group(1)), p)
    return dict(sorted(found.items()))


def build_labels(downloads):
    k = ["fips", "crop", "year"]
    col_files, cov_files = find_files(downloads, "colsom"), find_files(downloads, "sobcov")
    if not col_files:
        raise SystemExit(f"No colsom_YYYY files found under {downloads}")

    col = pd.concat([read_rma(p, COLSOM) for p in col_files.values()], ignore_index=True)
    col = col[~col.cause_code.isin(EXCLUDE_CAUSE_CODES)]
    cause = col.cause.str.upper()
    col["bucket"] = np.select([cause.eq("DROUGHT"), cause.isin(["HEAT", "HOT WIND"])],
                              ["drought", "heat"], "other")
    pay = (col.pivot_table(index=k, columns="bucket", values="indemnity", aggfunc="sum", fill_value=0)
              .reindex(columns=["drought", "heat", "other"], fill_value=0).add_suffix("_indemnity"))
    pay["drought_loss_acres"] = col[col.bucket == "drought"].groupby(k).net_determined_qty.sum()
    lab = pay

    if cov_files:
        cov = pd.concat([read_rma(p, SOBCOV) for p in cov_files.values()], ignore_index=True)
        if "quantity_type" in cov:
            cov = cov[cov.quantity_type.str.upper().str.startswith("ACRE")]
        cov = cov[(cov.liability > 0) & (cov.coverage_level > 0)].copy()
        cov["full_value"] = cov.liability / cov.coverage_level
        expo = cov.groupby(k).agg(liability=("liability", "sum"),
                                  insured_acres=("net_reported_qty", "sum"),
                                  full_value=("full_value", "sum"))
        expo["avg_coverage"] = expo.liability / expo.full_value
        lab = expo.join(pay, how="outer")
        has_cov = lab.liability.notna()
        lab.loc[has_cov, pay.columns] = lab.loc[has_cov, pay.columns].fillna(0)  # insured, no claim = 0
        lab["insured"] = has_cov | (lab[["drought_indemnity", "heat_indemnity", "other_indemnity"]]
                                    .fillna(0).sum(axis=1) > 0)                # any payout => insured
        lab["drought_payout_share"] = lab.drought_indemnity / lab.liability
        bad = lab.drought_payout_share > 1
        if bad.any():
            print(f"WARNING: {int(bad.sum())} rows pay out more than they insure - check parsing:")
            print(lab[bad].head())
        lab["drought_payout_per_acre"] = lab.drought_indemnity / lab.insured_acres
        lab["drought_loss_acre_share"] = lab.drought_loss_acres / lab.insured_acres   # 2nd model target
        lab["out_of_pocket_drought_loss"] = (lab.drought_loss_acres.fillna(0)
                                             * (lab.full_value / lab.insured_acres) * (1 - lab.avg_coverage))
        lab["est_drought_damage"] = lab.drought_indemnity + lab.out_of_pocket_drought_loss
        lab["full_crop_value"] = lab.full_value
        # ERP-style relief gap: loss recomputed as if coverage were 95%, minus what insurance paid.
        # Simplified (county averages, no per-farmer payment limits) -> an upper-end estimate.
        lab["relief_gap_to_95pct"] = (lab.drought_loss_acres.fillna(0) * (lab.full_value / lab.insured_acres)
                                      * (0.95 - lab.avg_coverage).clip(lower=0))
        lab["est_drought_loss_share"] = lab.est_drought_damage / lab.full_value
        lab = lab.drop(columns="full_value")
    lab = lab.reset_index()
    lab["rma_year_available"] = lab.year.isin(col_files)
    return lab, sorted(col_files), sorted(cov_files)


# ---------------------------------------------------------------- inputs from the repo
def build_inputs(repo):
    repo = pathlib.Path(repo).expanduser()
    d = repo / "data"
    master = pd.read_parquet(d / "master_dataset.parquet")
    master = master[master.state_alpha.isin(STATES) & master.crop.isin(CROPS)].copy()
    master["fips"] = master.fips.astype(str).str.zfill(5)
    fips_set = set(master.fips)
    base = master[["fips", "county_name", "state_alpha", "crop", "year",
                   "yield_per_acre", "yield_status", "acres_planted"]].copy()
    base["acres_planted"] = pd.to_numeric(base.acres_planted, errors="coerce")
    base["yield_per_acre"] = pd.to_numeric(base.yield_per_acre, errors="coerce")
    base = base.sort_values("year")
    g = base.groupby(["fips", "crop"])
    base["acres_planted_prev3_mean"] = g.acres_planted.transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    rep = base.yield_per_acre.where(base.yield_status == "reported")
    base["yield_prev5_mean"] = rep.groupby([base.fips, base.crop]).transform(
        lambda s: s.shift(1).rolling(5, min_periods=3).mean())

    # Drought: weekly maps from Apr 1 up to (not including) Aug 15
    dr = pd.read_parquet(d / "processed/drought/drought_weekly.parquet")
    dr["fips"] = dr.fips.astype(str).str.zfill(5)
    dr = dr[dr.fips.isin(fips_set)].copy()
    dr["year"] = dr.map_date.dt.year
    mmdd = dr.map_date.dt.strftime("%m-%d")
    dr = dr[(mmdd >= "04-01") & (mmdd <= MAP_CUTOFF_MMDD)]
    dr["d0p"] = 100 - dr.none_pct                  # D0+ area share
    dr["d1p"] = dr.D1 + dr.D2 + dr.D3 + dr.D4      # D1+ area share
    dr["d2p"] = dr.D2 + dr.D3 + dr.D4
    dr["d3p"] = dr.D3 + dr.D4
    drought = dr.groupby(["fips", "year"]).agg(
        d2_weeks_50pct=("d2p", lambda s: int((s >= 50).sum())),
        d3_weeks_50pct=("d3p", lambda s: int((s >= 50).sum())),
        d2_max_pct=("d2p", "max"), dsci_mean=("dsci", "mean"))
    last = dr.sort_values("map_date").groupby(["fips", "year"]).tail(1).set_index(["fips", "year"])
    drought["d2_pct_last_map"] = last.d2p
    drought["d3_pct_last_map"] = last.d3p
    drought["d0_pct_last_map"] = last.d0p
    drought["d1_pct_last_map"] = last.d1p
    # 4-week change: last map minus the map 28 days earlier (missing if that map is absent)
    key = dr.set_index(["fips", "year", "map_date"])[["d1p", "dsci"]]
    idx = pd.MultiIndex.from_arrays([last.index.get_level_values("fips"), last.index.get_level_values("year"),
                                     (last.map_date - pd.Timedelta(days=28)).to_numpy()])
    prev = key.reindex(idx)
    drought["d1_pct_change_4wk"] = pd.Series(last.d1p.to_numpy() - prev.d1p.to_numpy(), index=last.index)
    drought["dsci_change_4wk"] = pd.Series(last.dsci.to_numpy() - prev.dsci.to_numpy(), index=last.index)

    # Weather: daily, May 1 up to Aug 15 (heat from Jun 1)
    w = pd.read_parquet(d / "processed/acis/weather_daily.parquet")
    w["fips"] = w.fips.astype(str).str.zfill(5)
    w = w[w.fips.isin(fips_set)].copy()
    w["year"] = w.date.dt.year
    mmdd = w.date.dt.strftime("%m-%d")
    w = w[(mmdd >= "05-01") & (mmdd < DECISION_MMDD)].copy()
    w["gdd"] = ((w.tmax_c.clip(upper=30) + w.tmin_c.clip(lower=10)) / 2 - 10).clip(lower=0)
    summer = mmdd.loc[w.index] >= "06-01"
    w["heat32"] = (w.tmax_c >= 32) & summer
    w["heat35"] = (w.tmax_c >= 35) & summer
    w["tmax_jul"] = w.tmax_c.where(w.date.dt.month == 7)
    w["precip_30d"] = w.pcpn_mm.where(w.date.dt.strftime("%m-%d") >= "07-16")      # Jul 16 - Aug 14
    weather = w.groupby(["fips", "year"]).agg(
        precip_mm=("pcpn_mm", "sum"), heat32_days=("heat32", "sum"), heat35_days=("heat35", "sum"),
        tmax_jul_mean=("tmax_jul", "mean"), gdd=("gdd", "sum"), precip_30d_mm=("precip_30d", "sum"))
    # rain normals use strictly EARLIER years only (weather data start in 1999), at least 3 of them: fold-safe for every split
    weather = weather.sort_index()
    for col, name in [("precip_mm", "precip_normal_prior"), ("precip_30d_mm", "precip_30d_normal_prior")]:
        weather[name] = weather.groupby(level="fips")[col].transform(lambda s: s.shift(1).expanding(min_periods=3).mean())
    weather["precip_ratio_vs_normal"] = weather.precip_mm / weather.precip_normal_prior
    weather["precip_30d_ratio"] = weather.precip_30d_mm / weather.precip_30d_normal_prior

    # Soil (static) and irrigation (training-years average, Nebraska mostly)
    soil = pd.read_parquet(d / "processed/soil/soil_county.parquet")
    soil["fips"] = soil.fips.astype(str).str.zfill(5)
    soil = soil.set_index("fips")
    irr = pd.read_parquet(d / "processed/irrigation/nass_irrigation.parquet")
    irr["fips"] = irr.fips.astype(str).str.zfill(5)
    irr = irr.sort_values(["fips", "crop", "year"])
    irr["irr_share_prior_mean"] = irr.groupby(["fips", "crop"]).irrigated_share.transform(lambda s: s.shift(1).expanding(min_periods=1).mean())
    irr = irr.rename(columns={"irrigated_share": "irr_share_year"})[["fips", "crop", "year", "irr_share_year", "irr_share_prior_mean"]]

    x = base.join(drought, on=["fips", "year"]).join(weather, on=["fips", "year"])
    x["aws_100cm_mm"] = x.fips.map(soil.aws_100cm_mm)
    x["droughty_pct"] = x.fips.map(soil.droughty_pct)
    x["nccpi"] = np.where(x.crop == "CORN", x.fips.map(soil.nccpi_corn), x.fips.map(soil.nccpi_soy))
    n_rows = len(x)
    x = x.merge(irr, on=["fips", "crop", "year"], how="left")
    assert len(x) == n_rows
    x["irr_known"] = x.irr_share_prior_mean.notna().astype(int)
    x["irr_share_prior_mean"] = x.irr_share_prior_mean.fillna(0.0)
    x["decision_date"] = x.year.astype(str) + "-" + DECISION_MMDD
    return x


INPUT_COLS = ["fips", "county_name", "state_alpha", "crop", "year", "decision_date",
              "d2_weeks_50pct", "d3_weeks_50pct", "d2_max_pct", "dsci_mean", "d2_pct_last_map",
              "d3_pct_last_map", "d0_pct_last_map", "d1_pct_last_map", "d1_pct_change_4wk", "dsci_change_4wk",
              "precip_mm", "precip_normal_prior", "precip_ratio_vs_normal", "precip_30d_ratio",
              "heat32_days", "heat35_days", "tmax_jul_mean", "gdd", "aws_100cm_mm", "droughty_pct", "nccpi",
              "irr_share_year", "irr_share_prior_mean", "irr_known", "acres_planted_prev3_mean", "yield_prev5_mean"]
LABEL_COLS = ["fips", "county_name", "state_alpha", "crop", "year", "rma_year_available", "insured",
              "liability", "insured_acres", "avg_coverage", "drought_indemnity", "heat_indemnity",
              "other_indemnity", "drought_loss_acres", "drought_payout_share", "drought_payout_per_acre", "drought_loss_acre_share",
              "full_crop_value", "out_of_pocket_drought_loss", "est_drought_damage", "est_drought_loss_share",
              "relief_gap_to_95pct", "yield_per_acre", "yield_status", "yield_drop_vs_prev5_pct",
              "possible_out_of_pocket_loss"]

README = """# usda_budget_data (data guide)

Built by `organize_usda_data.py`. One row = one county x crop x year (Iowa + Nebraska, corn + soybeans).

| Folder | Years | Use |
|---|---|---|
| training | {tr} | fit models |
| validation | {va} | compare / tune models |
| testing | {te} | final check, run once at the end |

Each county folder is named `FIPS_County_ST` (FIPS first, because county names repeat across states).
`all_inputs.csv` / `all_labels.csv` in each split stack every county. Join inputs to labels on
`fips, crop, year` (fips is 5-character text: always read it with `dtype={{"fips": str}}`).

## inputs.csv: only what is known before {dd} of that year
- Drought (weekly maps dated Apr 1 to Aug 13, i.e. only maps released by Aug 15): `d2_weeks_50pct` weeks with D2+ on >=50% of county,
  `d3_weeks_50pct`, `d2_max_pct`, `dsci_mean`, and on the last map `d0_pct_last_map` (D0+ area share), `d1_pct_last_map` (D1+),
  `d2_pct_last_map`, `d3_pct_last_map`, plus `d1_pct_change_4wk` and `dsci_change_4wk` (last map minus the map 28 days earlier).
- Weather (daily, May 1 to Aug 14; heat counted from Jun 1): `precip_mm`, `precip_normal_prior` (mean `precip_mm` of the strictly earlier years,
  weather data start in 1999, at least 3 earlier years, else blank), `precip_ratio_vs_normal` (= precip_mm / precip_normal_prior), `precip_30d_ratio`
  (precipitation Jul 16-Aug 14 over the same window's mean in strictly earlier years), `heat32_days`, `heat35_days`, `tmax_jul_mean`,
  `gdd` (base 10 C, cap 30 C). Because normals only use earlier years, no row's normal contains its own or later years.
- Soil: `aws_100cm_mm`, `droughty_pct`, `nccpi` (crop-specific).
- Irrigation: `irr_share_year` (NASS irrigated share of that year, kept for transparency, not a model input), `irr_share_prior_mean`
  (mean of the strictly earlier years; 0 where unknown), `irr_known` (1 = real value).
- History: `acres_planted_prev3_mean`, `yield_prev5_mean` (previous years only).

## labels.csv: what actually happened (never use as model inputs)
- From RMA cause of loss: `drought_indemnity`, `heat_indemnity` (heat + hot wind), `other_indemnity`,
  `drought_loss_acres` (acres where a drought loss was determined). Add-on/area plans excluded.
- From RMA coverage level (sobcov): `insured`, `liability` (insured $), `insured_acres`, `avg_coverage`.
- `drought_payout_share` = drought_indemnity / liability  <- suggested model target
- `drought_loss_acre_share` = drought_loss_acres / insured_acres  <- second target (needed for out-of-pocket)
- `drought_payout_per_acre`; `full_crop_value` = insured $ / coverage level (insured part + deductible).
- `out_of_pocket_drought_loss` = deductible on the acres with a drought loss (paid by farmers, estimate).
- `est_drought_damage` = drought payout + out_of_pocket_drought_loss = estimated total drought loss on
  insured acres. Slightly low: losses smaller than the deductible never file a claim.
- `est_drought_loss_share` = est_drought_damage / full_crop_value  <- alternative target (total cost)
- `relief_gap_to_95pct` = extra paid if the drought loss were recomputed at 95% coverage (how USDA's
  Emergency Relief Program Track 1 worked for 2022). Simplified, county-level, upper-end estimate.
- Blank = no insurance record or RMA file missing for that year (not zero). 0 = insured, no drought claim.
- `possible_out_of_pocket_loss` = insured, no drought payout, yield >=10% below its 5-year average, and
  some D2+ drought by {dd}: damage likely stayed inside the deductible.
- `rma_year_available` False = that year's colsom file was not found.
"""


def write_split(df, folder):
    folder.mkdir(parents=True, exist_ok=True)
    df[INPUT_COLS].to_csv(folder / "all_inputs.csv", index=False)
    df[LABEL_COLS].to_csv(folder / "all_labels.csv", index=False)
    for (fips, name, st), g in df.groupby(["fips", "county_name", "state_alpha"]):
        safe = re.sub(r"[^A-Za-z0-9]+", "_", str(name).replace(" County", "")).strip("_")
        sub = folder / f"{fips}_{safe}_{st}"
        sub.mkdir(exist_ok=True)
        g.sort_values(["crop", "year"])[INPUT_COLS].to_csv(sub / "inputs.csv", index=False)
        g.sort_values(["crop", "year"])[LABEL_COLS].to_csv(sub / "labels.csv", index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--downloads", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    print("building inputs from repo ...")
    x = build_inputs(a.repo)
    print("reading RMA files ...")
    lab, col_years, cov_years = build_labels(a.downloads)
    df = x.merge(lab, on=["fips", "crop", "year"], how="left")
    df["rma_year_available"] = df.year.isin(col_years)
    for c in LABEL_COLS:
        if c not in df:
            df[c] = np.nan
    df["yield_drop_vs_prev5_pct"] = 100 * (1 - df.yield_per_acre / df.yield_prev5_mean)
    df["possible_out_of_pocket_loss"] = ((df.insured == True) & (df.drought_indemnity == 0)
                                         & (df.yield_drop_vs_prev5_pct >= 10)
                                         & ((df.d2_weeks_50pct >= 1) | (df.d2_max_pct >= 25)))

    out = pathlib.Path(a.out).expanduser().resolve()
    if (out / ".git").exists() or out == pathlib.Path(a.repo).expanduser().resolve():
        raise SystemExit("--out must be a data folder such as <repo>/app/usda_budget_data, not the repo itself.")
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"rma_colsom_years_found": col_years, "rma_sobcov_years_found": cov_years,
                "rma_colsom_years_missing": [y for y in range(2000, 2026) if y not in col_years],
                "rma_sobcov_years_missing": [y for y in range(2000, 2026) if y not in cov_years],
                "decision_date": DECISION_MMDD, "splits": {}}
    for split, (y0, y1) in SPLITS.items():
        part = df[df.year.between(y0, y1)]
        folder = out / split
        if folder.exists():
            for f in sorted(folder.rglob("*"), reverse=True):
                f.unlink() if f.is_file() else f.rmdir()
        write_split(part, folder)
        manifest["splits"][split] = {"years": [y0, y1], "rows": int(len(part)),
                                     "counties": int(part.fips.nunique()),
                                     "rows_with_label": int(part.drought_indemnity.notna().sum())}
        print(f"{split:10s} {y0}-{y1}: {len(part)} rows, {part.fips.nunique()} counties, "
              f"{int(part.drought_indemnity.notna().sum())} with RMA labels")
    (out / "testing" / "DO_NOT_USE_UNTIL_FINAL_TEST.txt").write_text(
        "Held-out years 2016-2025. Do not train, tune or look at results here until the model is final.\n")
    tr, va, te = (f"{SPLITS[s][0]}-{SPLITS[s][1]}" for s in SPLITS)
    (out / "DATA_README.md").write_text(README.format(tr=tr, va=va, te=te, dd=DECISION_MMDD))
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    if manifest["rma_sobcov_years_missing"]:
        print("NOTE: sobcov files missing for", manifest["rma_sobcov_years_missing"],
              "-> no insured $, payout share or zeros for those years.")
    print("done ->", out)


if __name__ == "__main__":
    main()
